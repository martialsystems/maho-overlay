#!/usr/bin/env python3
# Copyright (c) 2026 Martial Systems LLC. MIT.
"""Build cue → Maho reply pairs from the SG0 transcript dump.

A cue is the previous named speaker. Narration is skipped. Solo Maho only.
Does not call an LLM. Does not extract audio.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from compile_sg0_maho import DEFAULT_SRC, SKIP, SOLO, iter_named_lines, unwrap_thought  # noqa: E402
from maho_ja_style import is_ellipsis  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "maho_voice"
JA_MAP = DATA / "sg0_maho_en_to_ja.json"

SCIENCE = (
    "amadeus",
    "memory",
    "memories",
    "brain",
    "neuron",
    "cortex",
    "hippocamp",
    "data",
    "digital",
    "backup",
    "server",
    "password",
    "ai",
    "artificial",
    "research",
    "theory",
    "experiment",
    "lab",
    "system",
    "neural",
    "cognitive",
    "science",
    "physics",
    "time machine",
    "world line",
)


def is_science(text: str) -> bool:
    low = text.lower()
    return any(tok in low for tok in SCIENCE)


def build_pairs(src: Path, ja_map: dict[str, str]) -> list[dict]:
    rows: list[dict] = []
    seen_files = set()
    files = sorted(src.glob("*.txt"))
    for path in files:
        if path in seen_files:
            continue
        seen_files.add(path)
        scene = path.name.replace(".scx.txt", "").replace(".txt", "")
        prev: tuple[str, str] | None = None
        n = 0
        for name, text in iter_named_lines(path):
            if name in SKIP:
                prev = None
                continue
            body = unwrap_thought(text)
            if name in SOLO:
                if prev is not None and prev[0] not in SOLO and body and not is_ellipsis(body):
                    n += 1
                    cue, speaker = prev[1], prev[0]
                    rows.append(
                        {
                            "id": "{0}_p{1:04d}".format(scene, n),
                            "scene": scene,
                            "cue_speaker": speaker,
                            "cue": cue,
                            "response": body,
                            "response_ja": ja_map.get(body, ""),
                            "kind": "science" if is_science(cue + " " + body) else "chat",
                        }
                    )
                prev = (name, body)
            else:
                prev = (name, body)
    return rows


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--src", default=str(DEFAULT_SRC))
    p.add_argument("--out", default=str(DATA / "sg0_maho_pairs.jsonl"))
    args = p.parse_args()
    src = Path(args.src).expanduser()
    ja_map = {}
    if JA_MAP.is_file():
        ja_map = json.loads(JA_MAP.read_text(encoding="utf-8"))
    rows = build_pairs(src, ja_map)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
    sci = sum(1 for r in rows if r["kind"] == "science")
    print("pairs {0} science {1} chat {2} -> {3}".format(len(rows), sci, len(rows) - sci, out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
