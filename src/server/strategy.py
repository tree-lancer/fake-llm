import importlib.util
import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STRATEGY_DIR = ROOT / "reply-strategy"


def load_strategy(name=None):
    name = name or os.environ.get("REPLY_STRATEGY", "hello")
    path = STRATEGY_DIR / f"{name}.py"
    if not path.exists():
        name = "hello"
        path = STRATEGY_DIR / "hello.py"
    common_path = str(STRATEGY_DIR)
    if common_path not in sys.path:
        sys.path.insert(0, common_path)
    spec = importlib.util.spec_from_file_location(f"reply_strategy_{name}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.Strategy()
