"""Calling station: never folds, rarely raises."""
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _base import *
def act(req, st):
    L = req["legal_actions"]
    if "raise" in L and req["street"] != "preflop" and made(st["hole"], req["board"]) == 2 and random.random() < 0.5:
        return A("raise", bet(req, 0.7))
    return A("check") if "check" in L else A("call")
run(act)
