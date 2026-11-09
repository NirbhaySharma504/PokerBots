import sys, os, random, itertools
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "../../Starter_Kit")); import engine as E
sys.path.insert(0, os.path.join(HERE, "..")); sys.modules.pop("bot", None); import bot as B
import numpy as np
random.seed(2)
small = [r + s for r in "A2345TJQK" for s in "shdc"][:20] + [r+'s' for r in "6789"]  # dense ranks -> many pairs/trips/straights/flushes
bad = 0; n = 0
for _ in range(3000):
    hs = [random.sample(small, 7) for _ in range(20)]
    ours = [int(x) for x in B.evaluate(np.array([[B.CARD_ID[c] for c in h] for h in hs]))]
    ref = [max(E.rank5(c) for c in itertools.combinations(h, 5)) for h in hs]
    for i, j in itertools.combinations(range(20), 2):
        n += 1
        a = (ours[i] > ours[j]) - (ours[i] < ours[j]); b = (ref[i] > ref[j]) - (ref[i] < ref[j])
        if a != b:
            bad += 1
            if bad < 5: print(hs[i], hs[j], ref[i], ref[j])
print("mismatches", bad, "of", n)
