import os
import sys

# Make the project root importable no matter where this script is run from.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main.vein_graph import process_all

if __name__ == "__main__":
    process_all()