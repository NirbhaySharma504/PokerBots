"""v18 that min-raises every button open (open_size 0, opens 100%): probes size-blind preflop range reading with tiny opens"""
import os, runpy
os.environ["PB_PARAMS"] = '{"open_size":0.0,"open_t":0.0,"limp_t":0.0}'
runpy.run_path(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "ab", "v18.py"), run_name="__main__")
