"""Sparring partner: frozen v1 with 2.5x bluffing (it crushes plain v1)."""
import os, runpy
os.environ["PB_PARAMS"] = '{"bluff_scale": 2.5}'
runpy.run_path(os.path.join(os.path.dirname(os.path.abspath(__file__)), "v1.py"), run_name="__main__")
