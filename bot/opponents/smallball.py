"""Small-ball aggressor: opens every button, bets 1/3 pot whenever checked to with any
hand, continues only with a pair+ when facing a bet. Punishes bots that over-fold to small bets."""
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _base import *
def act(req, st):
    L = req["legal_actions"]; b = req["board"]; h = st["hole"]
    if req["street"] == "preflop":
        if "raise" in L and req["to_call"] <= 1: return A("raise", bet(req, 0.75))
        if req["to_call"] <= 4 or score3(h) > 16: return A("call") if "call" in L else A("check")
        return A("fold")
    m = made(h, b)
    if req["to_call"] == 0:
        return A("raise", bet(req, 0.33 if m < 2 else 0.7)) if "raise" in L else A("check")
    if m >= 2 and "raise" in L: return A("raise", bet(req, 0.8))
    if m >= 1 or req["to_call"] <= 0.25 * req["pot"]: return A("call")
    return A("fold")
run(act)
