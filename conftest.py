"""Root conftest: make the ``photoai`` desktop package importable in tests."""
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))

for path in [
    os.path.join(ROOT, "src"),  # photoai desktop package
    ROOT,  # recipes/, prompts/
]:
    if path not in sys.path:
        sys.path.insert(0, path)
