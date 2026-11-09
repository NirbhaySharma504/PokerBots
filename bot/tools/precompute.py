"""Compute PRE3 (3-card preflop equity vs random hand) and splice it into bot.py."""
import sys, os, time, json
from itertools import combinations
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
import numpy as np
import bot as B
from itertools import permutations
RANKS = B.RANKS


def canon3(cards):
    """Canonical class string for 3 card ids."""
    best = None
    cs = sorted(cards, key=lambda c: -(c >> 2))
    for perm in permutations(cs):
        if any((perm[i] >> 2) < (perm[i + 1] >> 2) for i in range(2)):
            continue
        lab = {}
        pat = []
        for c in perm:
            s = c & 3
            if s not in lab:
                lab[s] = len(lab)
            pat.append(lab[s])
        key = "".join(RANKS[c >> 2] for c in perm) + "".join(map(str, pat))
        if best is None or key < best:
            best = key
    return best


N = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
reps = {}
for c in combinations(range(52), 3):
    reps.setdefault(canon3(c), c)
print(len(reps), "classes", file=sys.stderr)
t = time.time()
out = {}
for i, (k, c) in enumerate(sorted(reps.items())):
    h = np.array(c)
    deck = np.setdiff1d(np.arange(52), h)
    s = B.sample_cards(deck, N, 8)
    v3, board = s[:, :3], s[:, 3:]
    hk, _ = B.heuristic_keep(np.tile(h, (N, 1)), board[:, :3])
    vk, _ = B.heuristic_keep(v3, board[:, :3])
    hs = B.evaluate(np.concatenate([hk, board], 1)); vs = B.evaluate(np.concatenate([vk, board], 1))
    out[k] = round(float(((hs > vs) + 0.5 * (hs == vs)).mean()), 4)
    if i % 200 == 0: print(i, k, out[k], f"{time.time()-t:.0f}s", file=sys.stderr)
import base64
eq = np.array([out[canon3(c)] for c in combinations(range(52), 3)])
b64 = base64.b64encode(np.round(eq * 65535).astype("<u2").tobytes()).decode()
src = open(os.path.join(HERE, "../bot.py")).read()
line = 'EQ3_B64 = "' + b64 + '"  # @@PRE3@@'
lines = [line if l.rstrip().endswith("# @@PRE3@@") else l for l in src.split("\n")]
open(os.path.join(HERE, "../bot.py"), "w").write("\n".join(lines))
top = sorted(out.items(), key=lambda kv: -kv[1])
print("best", top[:8]); print("worst", top[-5:])
