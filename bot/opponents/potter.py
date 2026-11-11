"""Pot-bettor / caller: calls most preflop, bets pot every time it is checked to,
calls any bet with a pair or 50% of the time, never folds the river with a pair."""
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _base import *
def act(req, st):
    L = req["legal_actions"]; h = st["hole"]; r = random.random()
    if req["street"] == "preflop":
        if "raise" in L and score3(h) > 20: return A("raise", bet(req, 1.0))
        return A("check") if "check" in L else A("call")
    m = made(h, req["board"])
    if "check" in L:
        return A("raise", bet(req, 1.0)) if "raise" in L else A("check")
    if m == 2 and "raise" in L: return A("raise", bet(req, 1.0))
    if m or r < 0.5: return A("call")
    return A("fold")
run(act)
