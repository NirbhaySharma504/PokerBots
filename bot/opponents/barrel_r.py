"""v11 that bets whenever checked to (bet_t 0) and raises often: probes how much
our flop/turn folding can be exploited by a sound bot that just keeps betting."""
import os, runpy
os.environ["PB_PARAMS"] = '{"bet_t":0.0,"bet_slope":0.5,"trap_p":0,"raise_t":0.45}'
runpy.run_path(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "ab", "v11.py"), run_name="__main__")
