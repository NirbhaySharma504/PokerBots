"""Switches style every 50 hands: tag-like (bets made hands, folds air) <-> maniac (raises
almost everything). Tests whether a cumulative opponent model lags behind a style change."""
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _base import *
def tag(req, st):
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
def maniac(req, st):
    L = req["legal_actions"]
    if "raise" in L and random.random() < 0.75:
        return A("raise", req["max_raise"] if random.random() < 0.3 else bet(req, 1.0))
    return A("check") if "check" in L else A("call")
def act(req, st):
    return (maniac if (req.get("hand_id", 0) // 50) % 2 else tag)(req, st)
run(act)
