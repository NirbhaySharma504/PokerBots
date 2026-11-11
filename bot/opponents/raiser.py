"""v11 exploit probe: raises our postflop bets very often"""
import os, runpy
os.environ["PB_PARAMS"] = '{"raise_t":0.45,"bluff_raise":1.0}'
runpy.run_path(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "ab", "v11.py"), run_name="__main__")
