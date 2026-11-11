"""v11 exploit probe: barrel + wide 3-bets + raises our bets"""
import os, runpy
os.environ["PB_PARAMS"] = '{"bet_t":0.0,"bet_slope":0.5,"trap_p":0,"pf_reraise_t":0.42,"bb_raise_t":0.42,"raise_t":0.5,"bluff_raise":1.0}'
runpy.run_path(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "ab", "v11.py"), run_name="__main__")
