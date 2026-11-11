"""v11 exploit probe: bets and raises pot-plus sizes"""
import os, runpy
os.environ["PB_PARAMS"] = '{"bet_base":1.0,"bet_slope":1.0,"bluff_size":1.1,"open_size":1.2}'
runpy.run_path(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "ab", "v11.py"), run_name="__main__")
