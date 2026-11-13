"""Two-street (turn + river) CFR+ on equity buckets.

Private state: turn buckets (i, j) for OOP / IP, river buckets (i2, j2). Turn buckets are
percentiles of turn equity vs a random hand, river buckets are percentiles of river hand
strength; their joint distribution and the river showdown result come from simulation on
real boards (Discard Hold'em: 2 hole cards after the discard, 4-card turn board).
Tree per street: OOP check / bet s; IP vs check: check / bet s; vs bet: fold / call / pot raise;
vs raise: fold / call. Pot = 1 at the start of the turn.
usage: python turn_cfr.py ITERS OUT.npy"""
import sys, os, itertools
import numpy as np

N = 10
SIZES = [0.33, 0.75]
BOT = "/Users/aaryan/Downloads/PokerBots_Synergy/PokerBots/bot/bot.py"


def simulate(n_boards=150, pairs=3000, seed=1):
    """Return P[i,j,i2,j2] (sums to 1) and W[i2,j2] = E[sign(OOP - IP) at showdown]."""
    ns = {"__name__": "sim"}
    src = open(BOT).read().split("\nif __name__")[0]
    exec(compile(src, BOT, "exec"), ns)
    evaluate = ns["evaluate"]
    rng = np.random.default_rng(seed)
    cnt = np.zeros((N, N, N, N))
    wsum = np.zeros((N, N)); wn = np.zeros((N, N))
    for _ in range(n_boards):
        board = rng.choice(52, 4, replace=False)
        rest = np.setdiff1d(np.arange(52), board)          # 48 cards
        hands = np.array(list(itertools.combinations(rest, 2)))  # 1128 hands
        H = len(hands)
        rank = np.zeros((len(rest), H))                     # river strength per river card
        valid = np.zeros((len(rest), H), bool)
        for k, r in enumerate(rest):
            ok = (hands[:, 0] != r) & (hands[:, 1] != r)
            cards = np.concatenate([hands, np.tile(np.append(board, r), (H, 1))], 1)
            s = evaluate(cards).astype(float)
            s[~ok] = np.nan
            v = s[ok]
            order = np.sort(v)
            lo = np.searchsorted(order, v, "left"); hi = np.searchsorted(order, v, "right")
            pct = np.full(H, np.nan); pct[ok] = (lo + 0.5 * (hi - lo)) / len(v)
            rank[k], valid[k] = pct, ok
            rank[k][~ok] = np.nan
        raw = np.zeros((len(rest), H)); raw[:] = np.nan
        # keep raw strengths for showdown comparison
        for k, r in enumerate(rest):
            ok = valid[k]
            cards = np.concatenate([hands, np.tile(np.append(board, r), (H, 1))], 1)
            raw[k, ok] = evaluate(cards[ok])
        teq = np.nanmean(rank, 0)                           # turn equity vs random
        tb = np.minimum(N - 1, (np.argsort(np.argsort(teq)) * N) // H)  # turn percentile bucket
        rb = np.minimum(N - 1, np.nan_to_num(rank * N).astype(int))
        for _ in range(pairs):
            a, b = rng.choice(H, 2, replace=False)
            if len({*hands[a], *hands[b]}) < 4:
                continue
            ks = np.flatnonzero(valid[:, a] & valid[:, b])
            k = rng.choice(ks)
            i, j, i2, j2 = tb[a], tb[b], rb[k, a], rb[k, b]
            cnt[i, j, i2, j2] += 1
            wsum[i2, j2] += np.sign(raw[k, a] - raw[k, b]); wn[i2, j2] += 1
    P = cnt / cnt.sum()
    W = np.where(wn > 0, wsum / np.maximum(wn, 1), np.sign(np.subtract.outer(np.arange(N), np.arange(N))))
    return P, W


def build():
    """nodes: name -> (player, street, {action: child}); terminals are tuples
    ('sd', inv0, inv1) or ('fold', folder, inv0, inv1) or ('next', inv) (turn closed -> river)."""
    T = {}

    def street(prefix, st, base):
        """add one street's tree; base = per-player investment before this street (equal)."""
        end = ("next", base) if st == "t" else ("sd", base, base)
        def facing(name, player, inv_me, inv_opp, depth):
            inv = (inv_me, inv_opp) if player == 0 else (inv_opp, inv_me)
            acts = {"fold": ("fold", player, *inv)}
            acts["call"] = ("next", inv_opp) if st == "t" else ("sd", inv_opp, inv_opp)
            if depth == 0:
                pot_now = 1 + 2 * base + (inv_me - base) + (inv_opp - base)
                to = inv_opp + (pot_now + (inv_opp - inv_me))
                child = name + "r"
                acts["raise"] = child
                other = 1 - player
                inv2 = (to, inv_opp) if player == 0 else (inv_opp, to)
                T[child] = (other, st, {"fold": ("fold", other, *inv2),
                                        "call": ("next", to) if st == "t" else ("sd", to, to)})
            T[name] = (player, st, acts)
        pot = 1 + 2 * base
        root = {}
        for s in SIZES:
            facing(prefix + "b%.2f" % s, 1, base, base + s * pot, 0)
            root["bet%.2f" % s] = prefix + "b%.2f" % s
        xs = {"check": end}
        for s in SIZES:
            facing(prefix + "xb%.2f" % s, 0, base, base + s * pot, 0)
            xs["bet%.2f" % s] = prefix + "xb%.2f" % s
        T[prefix + "x"] = (1, st, xs)
        root["check"] = prefix + "x"
        T[prefix + "root"] = (0, st, root)
    street("t", "t", 0.0)
    return T, street


T, _street = build()
RIVER_CACHE = {}


def river_root(base):
    key = round(base, 4)
    if key not in RIVER_CACHE:
        pre = "r%.4f_" % base
        _street(pre, "r", base)
        RIVER_CACHE[key] = pre + "root"
    return RIVER_CACHE[key]


# resolve 'next' terminals into river subtrees
for name, (pl, st, acts) in list(T.items()):
    if st == "t":
        for a, c in acts.items():
            if isinstance(c, tuple) and c[0] == "next":
                acts[a] = river_root(c[1])
# raise-child nodes created inside facing() for the turn also hold 'next'
for name, (pl, st, acts) in list(T.items()):
    for a, c in acts.items():
        if isinstance(c, tuple) and c[0] == "next":
            acts[a] = river_root(c[1])

AX = {(0, "t"): (1, 2, 3), (0, "r"): (1, 3), (1, "t"): (0, 2, 3), (1, "r"): (0, 2)}
SHAPE = {(0, "t"): (N, 1, 1, 1), (0, "r"): (N, 1, N, 1), (1, "t"): (1, N, 1, 1), (1, "r"): (1, N, 1, N)}


def info_shape(pl, st):
    return (N,) if st == "t" else (N, N)


regret = {k: np.zeros(info_shape(v[0], v[1]) + (len(v[2]),)) for k, v in T.items()}
ssum = {k: np.zeros_like(r) for k, r in regret.items()}


def strat(k):
    r = np.maximum(regret[k], 0); s = r.sum(-1, keepdims=True)
    return np.where(s > 0, r / np.where(s > 0, s, 1), 1.0 / r.shape[-1])


def bshape(k, x):
    """broadcast an infoset array (N,) or (N,N) to the joint state shape."""
    pl, st, _ = T[k]
    if st == "t":
        return x.reshape(SHAPE[(pl, st)])
    if pl == 0:
        return x[:, None, :, None]
    return x[None, :, None, :]


def term(t, p):
    """payoff for player p per joint state."""
    if t[0] == "sd":
        inv = t[1]
        u0 = W4 * (0.5 + inv)
        return u0 if p == 0 else -u0
    _, folder, inv0, inv1 = t
    amt = 0.5 + (inv0 if folder == 0 else inv1)
    return (amt if folder != p else -amt) * np.ones((N, N, N, N))


def cfr(k, p, reach_p, reach_o, it):
    if isinstance(k, tuple):
        return term(k, p)
    pl, st, acts = T[k]
    s = strat(k)
    names = list(acts)
    if pl == p:
        us = []
        for a_i, a in enumerate(names):
            us.append(cfr(acts[a], p, reach_p * bshape(k, s[..., a_i]), reach_o, it))
        us = np.stack(us, -1)
        sb = np.stack([bshape(k, s[..., a_i]) * np.ones((N, N, N, N)) for a_i in range(len(names))], -1)
        ev = (sb * us).sum(-1)
        w = (PJ * reach_o)[..., None]
        cf = (w * (us - ev[..., None])).sum(AX[(pl, st)])
        regret[k] = np.maximum(regret[k] + cf, 0)
        rp = (reach_p * np.ones((N, N, N, N)))
        rsum = rp.max(AX[(pl, st)])  # reach of own infoset (identical across other axes)
        ssum[k] += it * rsum[..., None] * s
        return ev
    ev = 0
    for a_i, a in enumerate(names):
        ev = ev + cfr(acts[a], p, reach_p, reach_o * bshape(k, s[..., a_i]), it)
    return ev


def avg(k):
    s = ssum[k]; t = s.sum(-1, keepdims=True)
    return np.where(t > 0, s / np.where(t > 0, t, 1), 1.0 / s.shape[-1])


if __name__ == "__main__":
    iters = int(sys.argv[1]) if len(sys.argv) > 1 else 300
    out = sys.argv[2] if len(sys.argv) > 2 else "turn_strat.npy"
    cache = os.path.splitext(out)[0] + "_sim.npz"
    if os.path.exists(cache):
        z = np.load(cache); PJ, W = z["P"], z["W"]
    else:
        PJ, W = simulate()
        np.savez(cache, P=PJ, W=W)
    W4 = W[None, None, :, :] * np.ones((N, N, N, N))
    one = np.ones((N, N, N, N))
    for it in range(1, iters + 1):
        for p in (0, 1):
            cfr("troot", p, one.copy(), one.copy(), it)
    np.set_printoptions(linewidth=200)
    for k in ("troot", "tx"):
        print(k, list(T[k][2])); print((avg(k).T * 100).round().astype(int))
    np.save(out, {k: avg(k) for k in ("troot", "tx")}, allow_pickle=True)
