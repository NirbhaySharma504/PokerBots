"""CFR+ on a one-street [0,1]-style river game: both players hold a strength bucket
(uniform, independent), higher wins. Pot = 1. OOP: check / bet s; IP vs check: check / bet s;
vs bet: fold / call / raise (pot-size); vs raise: fold / call.
Prints the solved strategy per bucket for each node."""
import numpy as np, sys

N = 20
SIZES = [0.33, 0.75]
x = (np.arange(N) + 0.5) / N
SD = np.sign(x[:, None] - x[None, :])  # OOP-row vs IP-col showdown result


def build():
    """nodes: (name, player, actions); action -> child name or terminal ('sd', inv_oop, inv_ip) / ('fold', folder, inv_oop, inv_ip)."""
    T = {}
    def facing(name, player, inv_me, inv_opp, depth):
        # player faces a bet: invested amounts (beyond the pot of 1)
        other = 1 - player
        acts = {"fold": ("fold", player, *(inv_me, inv_opp)[::(1 if player == 0 else -1)])}
        acts["call"] = ("sd", *((inv_opp, inv_opp)))
        if depth == 0:
            pot_now = 1 + inv_me + inv_opp
            to = inv_opp + (pot_now + (inv_opp - inv_me))  # pot-size raise
            child = name + "r"
            acts["raise"] = child
            facing(child, other, inv_opp, to, 1) if False else None
            inv = (to, inv_opp) if player == 0 else (inv_opp, to)
            T[child] = (other, {"fold": ("fold", other, *inv), "call": ("sd", to, to)})
        T[name] = (player, acts)
    root = {}
    for s in SIZES:
        facing("b%.2f" % s, 1, 0.0, s, 0)          # IP faces OOP bet
        root["bet%.2f" % s] = "b%.2f" % s
    xs = {"check": ("sd", 0.0, 0.0)}
    for s in SIZES:
        facing("xb%.2f" % s, 0, 0.0, s, 0)         # OOP faces IP bet after check
        xs["bet%.2f" % s] = "xb%.2f" % s
    T["x"] = (1, xs)
    root["check"] = "x"
    T["root"] = (0, root)
    return T


T = build()
# fix fold terminals: store (folder, inv_oop, inv_ip)
regret = {k: np.zeros((N, len(v[1]))) for k, v in T.items()}
ssum = {k: np.zeros((N, len(v[1]))) for k, v in T.items()}


def strat(k):
    r = np.maximum(regret[k], 0)
    s = r.sum(1, keepdims=True)
    n = r.shape[1]
    return np.where(s > 0, r / np.where(s > 0, s, 1), 1.0 / n)


def term_util(t, reach_opp, player):
    """utility vector for `player` (per own bucket) at terminal t given opponent reach."""
    if t[0] == "sd":
        inv = t[1]  # equal investment
        M = SD if player == 0 else -SD.T
        return (M * (0.5 + inv)) @ reach_opp
    _, folder, inv_oop, inv_ip = t
    win_amt = 0.5 + (inv_ip if folder == 1 else inv_oop)  # winner gets half pot + loser's inv (net)
    sign = 1 if folder != player else -1
    amt = win_amt if folder != player else 0.5 + (inv_oop if player == 0 else inv_ip)
    return sign * amt * reach_opp.sum() * np.ones(N)


def cfr(k, player, reach_me, reach_opp, it):
    """returns utility vector for `player` at node k (or terminal)."""
    if isinstance(k, tuple):
        return term_util(k, reach_opp, player)
    owner, acts = T[k]
    s = strat(k)
    names = list(acts)
    if owner == player:
        u = np.zeros((N, len(names)))
        for i, a in enumerate(names):
            u[:, i] = cfr(acts[a], player, reach_me * s[:, i], reach_opp, it)
        ev = (s * u).sum(1)
        regret[k] = np.maximum(regret[k] + (u - ev[:, None]), 0)
        ssum[k] += it * reach_me[:, None] * s
        return ev
    ev = np.zeros(N)
    for i, a in enumerate(names):
        ev += cfr(acts[a], player, reach_me, reach_opp * s[:, i], it)
    return ev


def avg(k):
    s = ssum[k]
    t = s.sum(1, keepdims=True)
    return np.where(t > 0, s / np.where(t > 0, t, 1), 1.0 / s.shape[1])


if __name__ == "__main__":
    iters = int(sys.argv[1]) if len(sys.argv) > 1 else 3000
    u = np.ones(N) / N
    for it in range(1, iters + 1):
        for p in (0, 1):
            cfr("root", p, u.copy(), u.copy(), it)
    np.set_printoptions(precision=2, suppress=True, linewidth=200)
    out = {}
    for k in T:
        out[k] = (list(T[k][1]), avg(k))
        print(k, list(T[k][1]))
        print((avg(k).T * 100).round().astype(int))
    np.save(sys.argv[2] if len(sys.argv) > 2 else "river_strat.npy", {k: v[1] for k, v in out.items()}, allow_pickle=True)


def br(k, player, reach_opp):
    if isinstance(k, tuple):
        return term_util(k, reach_opp, player)
    owner, acts = T[k]
    s = avg(k)
    vals = [None] * len(acts)
    if owner == player:
        return np.max([br(acts[a], player, reach_opp) for a in acts], 0)
    return sum(br(acts[a], player, reach_opp * s[:, i]) for i, a in enumerate(acts))


def exploit():
    u = np.ones(N) / N
    return (br("root", 0, u) @ u + br("root", 1, u) @ u) / 2
