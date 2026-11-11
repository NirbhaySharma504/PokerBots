"""Evaluate a param variant against a pool of strong opponents and print one line per opponent.
usage: python3.11 tools/pool.py '{"bet_t":0.4}' --seeds 3301-3328 [--bot path]"""
import argparse, subprocess, sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
POOL = ["ab/v11.py", "barrel", "barrel_r", "ab/v6.py", "tag"]
ap = argparse.ArgumentParser(); ap.add_argument("params"); ap.add_argument("--seeds", default="3301-3328")
ap.add_argument("--bot", default=None); ap.add_argument("--pool", default=",".join(POOL)); ap.add_argument("-j", default="7")
a = ap.parse_args()
for opp in a.pool.split(","):
    cmd = [sys.executable, os.path.join(HERE, "ab.py"), a.params, "--opp", opp, "--seeds", a.seeds, "-j", a.j]
    if a.bot: cmd += ["--bot", a.bot]
    out = subprocess.run(cmd, capture_output=True, text=True).stdout.strip().splitlines()
    line = out[-1] if out else "FAILED"
    print(f"{opp:12s} " + line.split(": ", 1)[-1].split("  max")[0], flush=True)
