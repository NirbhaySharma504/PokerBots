"""v13 exploit probe: same small-ball range betting but with tiny sizes (~1/8 pot)."""
import os, runpy
os.environ["PB_PARAMS"] = '{"bluff_size":0.12,"bet_base":0.12,"bet_slope":0.2}'
runpy.run_path(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "ab", "v13.py"), run_name="__main__")
