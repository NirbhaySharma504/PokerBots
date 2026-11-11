"""v11 exploit probe: 3-bets / BB-raises very wide preflop"""
import os, runpy
os.environ["PB_PARAMS"] = '{"pf_reraise_t":0.42,"bb_raise_t":0.42,"pf_call_margin":0.0}'
runpy.run_path(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "ab", "v11.py"), run_name="__main__")
