"""Size-reading sparring bot (not built on bot.py, reuses lag_eq's evaluator).

Learns the bet sizes it faces postflop and, when the opponent uses a size
they rarely use, needs a lot more equity to call. Its own value bets grow
with equity (so it leaks size, like our v3 did), bluffs use the small size.
"""
import os, sys, json, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lag_eq import equity, best_keep, act, sized

BUCKETS = (0.55, 1.05)  # small < 0.55 pot <= medium < 1.05 pot <= big


def bucket(frac):
    return sum(frac >= b for b in BUCKETS)


class Reader:
    def __init__(self):
        self.seen = [1, 1, 1]  # faced bets per size bucket (+1 prior)

    def rarity(self, b):
        return self.seen[b] / sum(self.seen)

    def decide(self, req, st):
        L, pot, tc = req["legal_actions"], req["pot"], req["to_call"]
        n = 50 if len(st["hole"]) == 3 else 150
        if req.get("time_left_ms", 30000) < 10000:
            n //= 4
        E = equity(st["hole"], req["board"], st["dead"], n)
        r = random.random()
        can = "raise" in L
        if req["street"] == "preflop":
            if can and (E > 0.56 or (E > 0.46 and r < 0.3)):
                return act("raise", sized(req, 1.0))
            if tc == 0:
                return act("check")
            if E > tc / (pot + tc) - 0.03 or tc <= 2:
                return act("call")
            return act("fold")
        if tc == 0:
            if can and E > 0.58:
                return act("raise", sized(req, min(1.4, 0.4 + 1.5 * (E - 0.58))))
            if can and r < 0.25:
                return act("raise", sized(req, 0.4))
            return act("check")
        b = bucket(tc / max(1, pot - tc))
        f = self.rarity(b)
        self.seen[b] += 1
        need = tc / (pot + tc)
        if b == 2 and f < 0.25:
            need += 0.35 * (0.25 - f) / 0.25 + 0.1  # rare overbet: assume strength
        elif f > 0.5:
            need -= 0.04  # their usual size, so it's capped / mixed
        if can and E > 0.8:
            return act("raise", sized(req, 0.9))
        if E > need:
            return act("call")
        return act("fold") if "fold" in L else act("check")


def main():
    me, st = Reader(), {"hole": [], "dead": []}
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
                out = me.decide(m, st)
            except Exception:
                out = act("check") if "check" in m["legal_actions"] else act("fold")
            print(json.dumps(out), flush=True)
        elif t == "discard_request":
            h = m["hole_cards"]
            print(json.dumps({"type": "discard", "card": h[best_keep(h, m["board"])]}), flush=True)


if __name__ == "__main__":
    main()
