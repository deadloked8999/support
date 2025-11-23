#!/usr/bin/env python3
import sys
sys.stdout.write("TEST: Script started\n")
sys.stdout.flush()
sys.stderr.write("TEST: Script started (stderr)\n")
sys.stderr.flush()

print("TEST: Print statement works")
print("TEST: Python version:", sys.version)

try:
    import main
    print("TEST: main.py imported successfully")
except Exception as e:
    print(f"TEST: Failed to import main.py: {e}")
    import traceback
    traceback.print_exc()

