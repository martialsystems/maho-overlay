#!/usr/bin/env python3
# Copyright (c) 2026 Martial Systems LLC. MIT.
"""Merge ja_chunks/ja_*.json into sg0_maho_en_to_ja.json and recompile."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "maho_voice"
CHUNKS = DATA / "ja_chunks"


def main() -> int:
    merged: dict[str, str] = {}
    files = sorted(CHUNKS.glob("ja_*.json"))
    if not files:
        raise SystemExit("no ja_*.json chunks")
    for path in files:
        blob = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(blob, dict):
            raise SystemExit("{0} is not an object".format(path))
        for k, v in blob.items():
            if not isinstance(k, str) or not isinstance(v, str) or not v.strip():
                raise SystemExit("bad pair in {0}: {1!r}".format(path.name, k))
            merged[k] = v
    dest = DATA / "sg0_maho_en_to_ja.json"
    dest.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")
    print("merged {0} strings from {1} chunks -> {2}".format(len(merged), len(files), dest))
    py = ROOT / "backend" / ".venv" / "bin" / "python"
    cmd = [
        str(py if py.is_file() else sys.executable),
        str(ROOT / "scripts" / "compile_sg0_maho.py"),
        "--src",
        str(Path.home() / "Documents" / "SG0 Transcript"),
        "--ja-map",
        str(dest),
    ]
    subprocess.check_call(cmd)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
