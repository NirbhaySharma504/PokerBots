"""v16 exploit probe: raises our bets very often"""
import os, runpy
os.environ["PB_PARAMS"] = '{"raise_t":0.5,"bluff_raise":1.0}'
runpy.run_path(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "ab", "v16.py"), run_name="__main__")
