import sys, json, random
RANKS = "23456789TJQKA"
def rv(c): return RANKS.index(c[0])
def score3(cards):
    """Crude preflop score for archetype bots: pairs, high cards, suits."""
    r = sorted((rv(c) for c in cards), reverse=True)
    v = r[0] + 0.6 * r[1] + 0.3 * r[2]
    if len(set(r)) < 3: v += 10
    if len({c[1] for c in cards}) < 3: v += 2
    return v
def made(hole, board):
    """1 if any hole card pairs the board or hole is a pair, else 0; 2 for trips+."""
    br = [c[0] for c in board]; hr = [c[0] for c in hole]
    n = max([br.count(x) + hr.count(x) for x in hr] + [0])
    return 2 if n >= 3 else (1 if n == 2 else 0)
def run(choose_action, choose_discard=None):
    st = {}
    for line in sys.stdin:
        line = line.strip()
        if not line: continue
        try: msg = json.loads(line)
        except ValueError: continue
        t = msg.get("type")
        if t == "new_hand": st["hole"] = msg["hole_cards"]
        elif t == "discard_result": st["hole"] = msg["hole_cards"]
        elif t == "match_end": break
        if t == "action_request":
            print(json.dumps(choose_action(msg, st)), flush=True)
        elif t == "discard_request":
            if choose_discard: card = choose_discard(msg, st)
            else:
                b = msg["board"]; h = msg["hole_cards"]
                card = max(h, key=lambda c: (-sum(c[0] == x[0] for x in b + h if x != c) * 20 - sum(c[1] == x[1] for x in b) * 3 - rv(c)))
            print(json.dumps({"type": "discard", "card": card}), flush=True)
def A(a, amt=None):
    d = {"type": "action", "action": a}
    if amt is not None: d["amount"] = int(amt)
    return d
def bet(req, frac):
    t = req["opp_bet"] + frac * (req["pot"] + req["to_call"])
    return max(req["min_raise"], min(req["max_raise"], int(t)))
