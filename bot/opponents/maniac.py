"""Maniac: raises big almost always, jams often."""
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _base import *
def act(req, st):
    L = req["legal_actions"]
    if "raise" in L and random.random() < 0.75:
        return A("raise", req["max_raise"] if random.random() < 0.3 else bet(req, 1.0))
    return A("check") if "check" in L else A("call")
run(act)
