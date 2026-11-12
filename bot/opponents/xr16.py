"""v16 exploit probe: traps everything and check-raises a lot"""
import os, runpy
os.environ["PB_PARAMS"] = '{"trap_p":1.0,"raise_t":0.55,"bluff_raise":0.7}'
runpy.run_path(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "ab", "v16.py"), run_name="__main__")
