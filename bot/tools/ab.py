"""A/B test: bot.py with param overrides vs a fixed opponent, over many seeds.
usage: python3.11 tools/ab.py '{"bet_t":0.55}' --opp ab/v1.py --seeds 1-20 -j 6"""
import argparse, json, os, re, subprocess, sys, statistics, tempfile
from concurrent.futures import ThreadPoolExecutor
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, ".."))
ENGINE = os.path.join(ROOT, "../Starter_Kit/engine.py")
ap = argparse.ArgumentParser()
ap.add_argument("params", nargs="?", default="{}")
ap.add_argument("--bot", default=os.path.join(ROOT, "bot.py"))
ap.add_argument("--opp", default=os.path.join(ROOT, "ab/v1.py"))
ap.add_argument("--seeds", default="1-12"); ap.add_argument("-j", type=int, default=6)
ap.add_argument("--hands", type=int, default=400)
a = ap.parse_args()
lo, hi = map(int, a.seeds.split("-"))
tmp = tempfile.mkdtemp(prefix="pbab_")
wrapper = os.path.join(tmp, "variant.py")
open(wrapper, "w").write(
    "import os, runpy\nos.environ['PB_PARAMS'] = %r\nrunpy.run_path(%r, run_name='__main__')\n"
    % (a.params, os.path.abspath(a.bot)))
opp = a.opp if os.path.isabs(a.opp) or a.opp.startswith("ab/") is False else os.path.join(ROOT, a.opp)
opp = os.path.abspath(opp if os.path.exists(opp) else os.path.join(ROOT, "opponents", a.opp + ".py"))
def one(seed):
    r = subprocess.run([sys.executable, ENGINE, wrapper, opp, "--seed", str(seed), "--hands", str(a.hands),
                        "--log-dir", ""], capture_output=True, text=True)
    m = re.search(r"A\s+\S+\s+net\s+([+-]?\d+)\s+time used\s+([\d.]+)", r.stdout)
    if not m:
        return seed, None, r.stdout[-500:] + r.stderr[-500:]
    return seed, (int(m.group(1)), float(m.group(2))), ""
with ThreadPoolExecutor(a.j) as ex:
    res = list(ex.map(one, range(lo, hi + 1)))
nets = [r[1][0] for r in res if r[1]]
for s, r, err in res:
    if not r: print("seed", s, "FAILED", err)
if nets:
    mu = statistics.mean(nets); se = statistics.stdev(nets) / len(nets) ** 0.5 if len(nets) > 1 else 0
    wins = sum(n > 0 for n in nets); maxt = max(r[1][1] for r in res if r[1])
    print(f"{a.params} vs {os.path.basename(opp)}: mean {mu:+.0f} ± {se:.0f}  W/L {wins}/{len(nets)-wins}  max time {maxt:.1f}s  nets {nets}")
