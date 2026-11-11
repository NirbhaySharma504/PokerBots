"""Tiny bettor: plays most hands, bets ~10% pot every time it is checked to, calls any
pair, raises trips+. Probes whether we over-fold to very small bets."""
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _base import *
def act(req, st):
    L = req["legal_actions"]; h = st["hole"]
    if req["street"] == "preflop":
        if "raise" in L and score3(h) > 20: return A("raise", bet(req, 0.75))
        return A("check") if "check" in L else A("call")
    m = made(h, req["board"])
    if "check" in L:
        return A("raise", bet(req, 0.1)) if "raise" in L else A("check")
    if m == 2 and "raise" in L: return A("raise", bet(req, 0.8))
    if m or req["to_call"] < 0.25 * req["pot"]: return A("call")
    return A("fold")
run(act)
