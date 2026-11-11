"""Check-raiser: out of position it checks, then raises any bet pot-size (any pair or
40% of air); in position it bets 60% when checked to. Calls raises with a pair."""
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _base import *
def act(req, st):
    L = req["legal_actions"]; h = st["hole"]; r = random.random()
    if req["street"] == "preflop":
        if "raise" in L and score3(h) > 18: return A("raise", bet(req, 1.0))
        return A("check") if "check" in L else A("call")
    m = made(h, req["board"])
    if "check" in L:
        if req.get("my_bet", 0) == 0 and r < 0.6 and "raise" in L and st.get("ip"): return A("raise", bet(req, 0.6))
        return A("check")
    if "raise" in L and (m or r < 0.4) and req["to_call"] < req["pot"]: return A("raise", bet(req, 1.0))
    if m or req["to_call"] < 0.3 * req["pot"]: return A("call")
    return A("fold")
def run2():
    st = {}
    for line in sys.stdin:
        line = line.strip()
        if not line: continue
        try: msg = json.loads(line)
        except ValueError: continue
        t = msg.get("type")
        if t == "new_hand": st["hole"] = msg["hole_cards"]; st["ip"] = msg.get("seat") == "button"
        elif t == "discard_result": st["hole"] = msg["hole_cards"]
        elif t == "match_end": break
        if t == "action_request": print(json.dumps(act(msg, st)), flush=True)
        elif t == "discard_request":
            b = msg["board"]; hh = msg["hole_cards"]
            card = max(hh, key=lambda c: (-sum(c[0] == x[0] for x in b + hh if x != c) * 20 - rv(c)))
            print(json.dumps({"type": "discard", "card": card}), flush=True)
run2()
