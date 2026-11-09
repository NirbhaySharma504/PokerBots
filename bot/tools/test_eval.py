"""Cross-check bot.evaluate against the starter kit's best_hand on random deals."""
import sys, os, random, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "../../Starter_Kit"))
import engine as E
sys.path.insert(0, os.path.join(HERE, ".."))
sys.modules.pop("bot", None)
import numpy as np
import bot as B
import engine as E

random.seed(1)
deck = list(B.CARD_ID)
for k in (5, 6, 7):
    n = 20000
    hands = [random.sample(deck, k) for _ in range(n)]
    ours = [int(x) for x in B.evaluate(np.array([[B.CARD_ID[c] for c in h] for h in hands]))]
    ref = [E.best_hand([], h) if k == 5 else max(E.rank5(c) for c in __import__("itertools").combinations(h, 5)) for h in hands]
    # pairwise ordering must agree
    bad = 0
    for _ in range(50000):
        i, j = random.randrange(n), random.randrange(n)
        a = (ours[i] > ours[j]) - (ours[i] < ours[j])
        b = (ref[i] > ref[j]) - (ref[i] < ref[j])
        if a != b:
            bad += 1
            if bad < 5: print("MISMATCH", hands[i], hands[j], ref[i], ref[j])
    print(f"k={k}: mismatches {bad}/50000")
x = np.random.randint(0, 52, (5000, 7))
t = time.perf_counter(); B.evaluate(x); print(f"eval 5000x7: {(time.perf_counter()-t)*1000:.1f} ms")
