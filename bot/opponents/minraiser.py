"""Min-raises whenever possible (hits the raise cap a lot), otherwise calls."""
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _base import *
def act(req, st):
    L = req["legal_actions"]
    if "raise" in L: return A("raise", req["min_raise"])
    return A("call") if "call" in L else A("check")
run(act)
