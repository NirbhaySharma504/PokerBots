"""v18 that bets tiny postflop: bluffs at ~0.1 pot and value-bets 0.15-0.35 pot, probing v18's cm_size margin shrink (v18 calls tiny bets with almost anything)"""
import os, runpy
os.environ["PB_PARAMS"] = '{"bluff_size":0.1,"bet_base":0.15,"bet_slope":0.5,"bet_t":0.5}'
runpy.run_path(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "ab", "v18.py"), run_name="__main__")
