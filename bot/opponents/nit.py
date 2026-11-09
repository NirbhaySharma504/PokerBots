"""Nit: plays only strong preflop hands, bets made hands, folds to aggression otherwise."""
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _base import *
def act(req, st):
    L = req["legal_actions"]; h = st["hole"]
    if req["street"] == "preflop":
        s = score3(h)
        if s > 22 and "raise" in L: return A("raise", bet(req, 1.0))
        if s > 17: return A("check") if "check" in L else A("call")
        return A("check") if "check" in L else A("fold")
    m = made(h, req["board"])
    if m and "raise" in L and random.random() < 0.7: return A("raise", bet(req, 0.6))
    if "check" in L: return A("check")
    if m or req["to_call"] <= 0.25 * req["pot"]: return A("call")
    return A("fold")
run(act)
