from __future__ import annotations
from pathlib import Path
import runpy
import sys
import os

def main():
    # run_gptsovits.py is inside Amadeus/, so project root is one level up
    PROJECT_ROOT = Path(__file__).resolve().parent.parent
    GPT_ROOT = PROJECT_ROOT / "GPT-SoVITS"
    GPT_PKG = GPT_ROOT / "GPT_SoVITS"

    if not GPT_ROOT.exists():
        raise RuntimeError(f"GPT-SoVITS not found at: {GPT_ROOT}")
    if not (GPT_ROOT / "config.py").exists():
        raise RuntimeError(f"config.py not found at: {GPT_ROOT / 'config.py'}")
    if not (GPT_ROOT / "api_v2.py").exists():
        raise RuntimeError(f"api_v2.py not found at: {GPT_ROOT / 'api_v2.py'}")

    # Ensure BOTH import roots are visible:
    # - GPT_ROOT: allows `import config`
    # - GPT_PKG : allows `import text.*` and other package-relative imports
    sys.path.insert(0, str(GPT_ROOT))
    sys.path.insert(0, str(GPT_PKG))

    # GPT-SoVITS expects to run from repo root
    os.chdir(GPT_ROOT)

    print("[Amadeus] Starting GPT-SoVITS native API...")

    # Run script
    runpy.run_path(str(GPT_ROOT / "api_v2.py"), run_name="__main__")

if __name__ == "__main__":
    main()
