"""Raises our flop/turn bets ~75% of the time regardless of hand (the exploit an outside bot ran on v18)"""
import os, sys, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _base import run, A, bet, score3, made

RAISE_P = float(os.environ.get("PUN_P", "0.75"))


def act(req, st):
    legal, tc, street = req["legal_actions"], req["to_call"], req["street"]
    h, b = st["hole"], req["board"]
    if street == "preflop":
        if "raise" in legal and score3(h) > 22:
            return A("raise", bet(req, 1.0))
        if tc > 0 and "call" in legal and (tc <= 6 or score3(h) > 17):
            return A("call")
        return A("check") if "check" in legal else A("fold")
    m = made(h, b)
    if tc > 0:
        if req["my_bet"] == 0 and street != "river" and "raise" in legal and (m >= 1 or random.random() < RAISE_P):
            return A("raise", bet(req, 0.8))
        if m >= 1 and "call" in legal:
            return A("call")
        return A("fold") if "fold" in legal else A("check")
    if "raise" in legal and m >= 1:
        return A("raise", bet(req, 0.5))
    return A("check")


run(act)
