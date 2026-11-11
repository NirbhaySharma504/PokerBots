"""Flop jammer: limps/calls preflop, then goes all-in on the flop with any pair or
four-flush/straight-ish draw, else check/fold. Tests our all-in calling ranges."""
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _base import *
def draw(h, b):
    suits = [c[1] for c in h + b]; return max(suits.count(s) for s in set(suits)) >= 4
def act(req, st):
    L = req["legal_actions"]; h = st["hole"]
    if req["street"] == "preflop":
        if score3(h) > 10 or req["to_call"] <= 2: return A("check") if "check" in L else A("call")
        return A("fold")
    if made(h, req["board"]) or draw(h, req["board"]):
        if "raise" in L: return A("raise", req["max_raise"])
        return A("call")
    return A("check") if "check" in L else A("fold")
run(act)
