"""Run bot vs each opponent through the official local engine (timed), in parallel.
usage: python3.11 tools/gauntlet.py [BOT] [--seeds 1 2] [--opps a b] [--stage 1]"""
import argparse, os, re, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
ENGINE = os.path.join(ROOT, "../Starter_Kit/engine.py")
ap = argparse.ArgumentParser()
ap.add_argument("bot", nargs="?", default=os.path.join(ROOT, "bot.py"))
ap.add_argument("--seeds", nargs="+", type=int, default=[1, 2])
ap.add_argument("--opps", nargs="+", default=["random_bot", "checkcall", "station", "maniac", "nit", "tag"])
ap.add_argument("--stage", default="1"); ap.add_argument("-j", type=int, default=3)
a = ap.parse_args()
def one(opp, seed):
    p = opp if opp.endswith(".py") else os.path.join(ROOT, "opponents", opp + ".py")
    logd = os.path.join("/tmp", f"pb_{os.getpid()}_{os.path.basename(p)}_{seed}")
    r = subprocess.run([sys.executable, ENGINE, a.bot, p, "--seed", str(seed), "--stage", a.stage,
                        "--log-dir", logd], capture_output=True, text=True)
    return opp, seed, r.stdout + r.stderr, logd
jobs = [(o, s) for o in a.opps for s in a.seeds]
with ThreadPoolExecutor(a.j) as ex:
    res = list(ex.map(lambda x: one(*x), jobs))
tot = {}
for opp, seed, out, logd in res:
    m = re.findall(r"(-?\d+)", out)
    print(f"=== {opp} seed {seed} ({logd})\n" + "\n".join(l for l in out.splitlines() if l.strip())[-900:])
