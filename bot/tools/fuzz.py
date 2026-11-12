"""Protocol robustness check: start-up time, then feed bot.py odd / malformed messages
mixed with valid requests and check every request gets exactly one legal reply.
usage: python3.11 tools/fuzz.py [path/to/bot.py]"""
import json, os, subprocess, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
BOT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "bot.py")

def run(lines, timeout=20):
    p = subprocess.Popen([sys.executable, BOT], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True)
    out, _ = p.communicate("\n".join(lines) + "\n", timeout=timeout)
    return [l for l in out.splitlines() if l.strip()], p.returncode

hist = [{"street": "preflop", "actor": "opp", "action": "raise", "amount": 6}]
act = {"type": "action_request", "hand_id": 1, "street": "preflop", "board": [], "pot": 8,
       "to_call": 4, "my_bet": 2, "opp_bet": 6, "my_stack": 198, "opp_stack": 194,
       "min_raise": 10, "max_raise": 200, "raises_left": 3, "time_left_ms": 30000,
       "legal_actions": ["fold", "call", "raise"], "history": hist}
init = {"type": "init", "protocol_version": "1.0", "total_hands": 200, "time_bank_ms": 30000}
hand = {"type": "new_hand", "hand_id": 1, "seat": "big_blind", "hole_cards": ["As", "Kd", "7c"],
        "stack": 200, "opp_stack": 200}
flop = dict(act, street="flop", board=["Ah", "7d", "2s"], to_call=0, my_bet=0, opp_bet=0, pot=12,
            min_raise=2, legal_actions=["check", "raise"], history=hist + [
                {"street": "preflop", "actor": "me", "action": "call"}])
disc = {"type": "discard_request", "hand_id": 1, "board": ["Ah", "7d", "2s"],
        "hole_cards": ["As", "Kd", "7c"], "time_left_ms": 29000}
end = {"type": "match_end"}
D = json.dumps
fails = 0

t = time.time()
out, rc = run([D(init), D(hand), D(act), D(end)])
print(f"start-up + first reply: {time.time() - t:.2f}s, exit {rc}")

cases = {
    "valid sequence": ([D(init), D(hand), D(act), D(disc), D(flop), D(end)], 3),
    "garbage lines": ([D(init), "not json", "{", "[]", "42", D(hand), D(act), D(end)], 1),
    "unknown type / extra fields": ([D(init), D({"type": "weird", "x": 1}), D(dict(hand, extra=[1, 2])),
                                     D(dict(act, foo="bar")), D(end)], 1),
    "notice + missing optional fields": ([D(init), D({"type": "notice", "code": "illegal_action",
                                          "applied": "fold"}), D(hand),
                                          D({k: v for k, v in act.items() if k not in ("history", "time_left_ms")}),
                                          D(end)], 1),
    "no init, action first": ([D(act), D(end)], 1),
    "tiny time bank": ([D(init), D(hand), D(dict(act, time_left_ms=300)), D(end)], 1),
    "all-in only (max=min)": ([D(init), D(hand), D(dict(act, min_raise=200, max_raise=200)), D(end)], 1),
    "check-only": ([D(init), D(hand), D(dict(flop, legal_actions=["check"])), D(end)], 1),
}
for name, (lines, expect) in cases.items():
    try:
        out, rc = run(lines)
    except subprocess.TimeoutExpired:
        print(f"FAIL {name}: timeout"); fails += 1; continue
    ok = len(out) == expect
    for l in out:
        try:
            m = json.loads(l)
            ok &= m.get("type") in ("action", "discard")
        except ValueError:
            ok = False
    print(("ok  " if ok and rc == 0 else "FAIL") + f" {name}: {len(out)} replies, exit {rc}  {out[:3]}")
    fails += not (ok and rc == 0)
print("FAILED" if fails else "all passed")
sys.exit(1 if fails else 0)
