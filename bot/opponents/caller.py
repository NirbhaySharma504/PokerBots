"""v11 exploit probe: calls down much wider (punishes our bluffs)"""
import os, runpy
os.environ["PB_PARAMS"] = '{"call_margin":-0.05,"cm_oop":0.0}'
runpy.run_path(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "ab", "v11.py"), run_name="__main__")
