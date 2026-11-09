"""Tight-aggressive heuristic: decent baseline opponent."""
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _base import *
def act(req, st):
    L = req["legal_actions"]; h = st["hole"]; r = random.random()
    if req["street"] == "preflop":
        s = score3(h)
        if s > 21 and "raise" in L: return A("raise", bet(req, 1.0))
        if s > 15 or req["to_call"] <= 1: return A("check") if "check" in L else A("call")
        return A("check") if "check" in L else A("fold")
    m = made(h, req["board"])
    if "check" in L:
        if (m or r < 0.3) and "raise" in L: return A("raise", bet(req, 0.66))
        return A("check")
    if m == 2 and "raise" in L: return A("raise", bet(req, 0.8))
    if m or req["to_call"] < 0.4 * req["pot"] and r < 0.5: return A("call")
    return A("fold")
run(act)
