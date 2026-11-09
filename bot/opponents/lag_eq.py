"""Loose-aggressive equity bot, written separately from bot.py on purpose.

Pure python 7-card eval, MC equity vs a *random* hand (no range model),
bets/raises a lot and bluffs often. Meant to punish over-folding.
LAG_BLUFF (env) scales how often it bluffs, default 1.0.
"""
import os, sys, json, random
from collections import Counter

R = {r: i for i, r in enumerate("23456789TJQKA", 2)}
DECK = [r + s for r in "23456789TJQKA" for s in "shdc"]
BLUFF = float(os.environ.get("LAG_BLUFF", "1.0"))


def score(cards):
    """Best 5 of n cards as a comparable tuple."""
    vals = sorted((R[c[0]] for c in cards), reverse=True)
    suits = Counter(c[1] for c in cards)
    fs = next((s for s, n in suits.items() if n >= 5), None)

    def straight(vs):
        u = sorted(set(vs), reverse=True)
        if 14 in u:
            u.append(1)
        run = 1
        for i in range(1, len(u)):
            run = run + 1 if u[i] == u[i - 1] - 1 else 1
            if run == 5:
                return u[i] + 4
        return 0

    if fs:
        fv = sorted((R[c[0]] for c in cards if c[1] == fs), reverse=True)
        sf = straight(fv)
        if sf:
            return (8, sf)
    cnt = Counter(vals)
    g = sorted(cnt.items(), key=lambda kv: (kv[1], kv[0]), reverse=True)
    if g[0][1] == 4:
        return (7, g[0][0], max(v for v in vals if v != g[0][0]))
    if g[0][1] == 3 and len(g) > 1 and g[1][1] >= 2:
        return (6, g[0][0], g[1][0])
    if fs:
        return (5,) + tuple(fv[:5])
    st = straight(vals)
    if st:
        return (4, st)
    if g[0][1] == 3:
        return (3, g[0][0]) + tuple(v for v in vals if v != g[0][0])[:2]
    if g[0][1] == 2 and g[1][1] == 2:
        return (2, g[0][0], g[1][0], max(v for v in vals if v not in (g[0][0], g[1][0])))
    if g[0][1] == 2:
        return (1, g[0][0]) + tuple(v for v in vals if v != g[0][0])[:3]
    return (0,) + tuple(vals[:5])


def best_keep(hole, board):
    """Index of card to discard (keep best 2 by board strength, tie -> keep higher cards)."""
    return max(range(3), key=lambda i: (score([c for j, c in enumerate(hole) if j != i] + board),
                                        -R[hole[i][0]]))


def equity(hole, board, dead, n):
    deck = [c for c in DECK if c not in hole and c not in board and c not in dead]
    win = 0.0
    for _ in range(n):
        need = 5 - len(board)
        opp_n = 3 if len(hole) == 3 or len(board) < 3 else 2
        s = random.sample(deck, opp_n + need)
        opp, full = s[:opp_n], board + s[opp_n:]
        h = hole
        if len(h) == 3:
            h = [c for j, c in enumerate(h) if j != best_keep(h, full[:3])]
        if len(opp) == 3:
            opp = [c for j, c in enumerate(opp) if j != best_keep(opp, full[:3])]
        a, b = score(h + full), score(opp + full)
        win += 1.0 if a > b else 0.5 if a == b else 0.0
    return win / n


def act(a, amt=None):
    d = {"type": "action", "action": a}
    if amt is not None:
        d["amount"] = int(amt)
    return d


def sized(req, frac):
    t = req["opp_bet"] + frac * (req["pot"] + req["to_call"])
    return max(req["min_raise"], min(req["max_raise"], int(t)))


def decide(req, st):
    L, pot, tc = req["legal_actions"], req["pot"], req["to_call"]
    n = 50 if len(st["hole"]) == 3 else 150
    if req.get("time_left_ms", 30000) < 10000:
        n //= 4
    E = equity(st["hole"], req["board"], st["dead"], n)
    r = random.random()
    can = "raise" in L
    if req["street"] == "preflop":
        if can and (E > 0.55 or (E > 0.42 and r < 0.6 * BLUFF)):
            return act("raise", sized(req, 1.0 if tc <= 1 else 1.2))
        if tc == 0:
            return act("check")
        if E > tc / (pot + tc) - 0.05 or tc <= 2:
            return act("call")
        return act("fold")
    if tc == 0:
        if can and (E > 0.6 or r < 0.45 * BLUFF):
            return act("raise", sized(req, 0.75 if E > 0.6 else 0.6))
        return act("check")
    if can and (E > 0.75 or (E > 0.35 and r < 0.15 * BLUFF)):
        return act("raise", sized(req, 0.9))
    if E > tc / (pot + tc) - 0.03:
        return act("call")
    return act("fold") if "fold" in L else act("check")


def main():
    st = {"hole": [], "dead": []}
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            m = json.loads(line)
        except ValueError:
            continue
        t = m.get("type")
        if t == "new_hand":
            st = {"hole": m["hole_cards"], "dead": []}
        elif t == "discard_result":
            st["hole"] = m["hole_cards"]
            st["dead"] = [m.get("my_discard"), m.get("opp_discard")]
        elif t == "match_end":
            break
        elif t == "action_request":
            try:
                out = decide(m, st)
            except Exception:
                out = act("check") if "check" in m["legal_actions"] else act("fold")
            print(json.dumps(out), flush=True)
        elif t == "discard_request":
            h = m["hole_cards"]
            print(json.dumps({"type": "discard", "card": h[best_keep(h, m["board"])]}), flush=True)


if __name__ == "__main__":
    main()
