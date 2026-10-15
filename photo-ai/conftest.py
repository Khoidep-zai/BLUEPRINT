"""Root conftest: make all source trees importable in tests."""
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))

for path in [
    ROOT,  # providers/, recipes/
    os.path.join(ROOT, "apps", "api", "src"),  # photoai_api
    os.path.join(ROOT, "workers", "src"),  # photoai_worker
]:
    if path not in sys.path:
        sys.path.insert(0, path)
