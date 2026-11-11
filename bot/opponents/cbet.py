"""Continuation bettor: raises most buttons, bets nearly every flop, then only keeps
betting with a made hand. Bets ~2/3 pot, calls down with any pair."""
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _base import *
def act(req, st):
    L = req["legal_actions"]; h = st["hole"]; r = random.random(); street = req["street"]
    if street == "preflop":
        s = score3(h)
        if "raise" in L and (s > 13 or req["to_call"] <= 1 and r < 0.7): return A("raise", bet(req, 0.75))
        if s > 11 or req["to_call"] <= 1: return A("check") if "check" in L else A("call")
        return A("check") if "check" in L else A("fold")
    m = made(h, req["board"])
    if "check" in L:
        want = r < 0.85 if street == "flop" else (m > 0 or r < 0.1)
        if want and "raise" in L: return A("raise", bet(req, 0.66))
        return A("check")
    if m == 2 and "raise" in L: return A("raise", bet(req, 0.8))
    if m or (street == "flop" and req["to_call"] < 0.5 * req["pot"]): return A("call")
    return A("fold")
run(act)
