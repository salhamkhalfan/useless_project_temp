import os
import sys

# Root launcher: makes "python threshold_test.py" work from C:\UP3.0
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main.vein_graph import process_all

if __name__ == "__main__":
    process_all()