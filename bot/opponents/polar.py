"""Polarized bot: overbets 1.5x pot with strong hands AND with bluffs, checks/calls
medium hands. Stress test for bet-size-aware range reading."""
import os, sys, json, random
import numpy as np
import importlib.util
spec = importlib.util.spec_from_file_location("v2", os.path.join(os.path.dirname(os.path.abspath(__file__)), "../ab/v2.py"))
B = importlib.util.module_from_spec(spec); spec.loader.exec_module(B)

def equity(hole, board):
    h = np.array([B.CARD_ID[c] for c in hole]); b = np.array([B.CARD_ID[c] for c in board], dtype=int)
    if not len(b):
        return float(B.EQ3[h[0], h[1], h[2]])
    deck = np.setdiff1d(np.arange(52), np.concatenate([h, b]))
    N = 800; s = B.sample_cards(deck, N, 2 + 5 - len(b))
    full = np.concatenate([np.tile(b, (N, 1)), s[:, 2:]], 1)
    vs = B.evaluate(np.concatenate([s[:, :2], full], 1))
    keeps = [list(k) for k in B.KEEPS] if len(h) == 3 else [[0, 1]]
    best = 0
    for k in keeps:
        hs = B.evaluate(np.concatenate([np.tile(h[k], (N, 1)), full], 1))
        best = max(best, float(((hs > vs) + 0.5 * (hs == vs)).mean()))
    return best

def A(a, amt=None):
    d = {"type": "action", "action": a}
    if amt is not None: d["amount"] = int(amt)
    return d

def act(req, hole):
    L = req["legal_actions"]; e = equity(hole, req["board"])
    pot, tc = req["pot"], req["to_call"]
    pre = req["street"] == "preflop"
    big = lambda: A("raise", max(req["min_raise"], min(req["max_raise"], int(req["opp_bet"] + 1.5 * (pot + tc)))))
    if pre:
        if "raise" in L and e > 0.6: return A("raise", max(req["min_raise"], min(req["max_raise"], 3 * req["opp_bet"])))
        if tc == 0: return A("check")
        return A("call") if e > 0.4 or tc <= 2 else A("fold")
    if "raise" in L and (e > 0.75 or (e < 0.25 and random.random() < 0.45)):
        return big()
    if tc == 0: return A("check")
    return A("call") if e >= tc / (pot + tc) else A("fold")

def discard(req):
    h = req["hole_cards"]; best, card = -1, h[0]
    for i, k in enumerate(B.KEEPS):
        e = equity([h[j] for j in k], req["board"])
        if e > best: best, card = e, h[i]
    return card

hole = []
for line in sys.stdin:
    line = line.strip()
    if not line: continue
    try: msg = json.loads(line)
    except ValueError: continue
    t = msg.get("type")
    if t == "new_hand": hole = msg["hole_cards"]
    elif t == "discard_result": hole = msg["hole_cards"]
    elif t == "match_end": break
    elif t == "action_request": print(json.dumps(act(msg, hole)), flush=True)
    elif t == "discard_request": print(json.dumps({"type": "discard", "card": discard(msg)}), flush=True)
