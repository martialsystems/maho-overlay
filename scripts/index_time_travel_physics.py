#!/usr/bin/env python3
# Copyright (c) 2026 Martial Systems LLC. MIT.
"""Chunk docs/maho_science.md into retriever rows (kind=notes)."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "docs" / "maho_science.md"
OUT = ROOT / "data" / "maho_voice" / "maho_science.jsonl"
HEAD = re.compile(r"^## (.+)$", re.M)


def chunk_kind(title: str) -> str:
    low = title.lower()
    if "amadeus" in low or "ai" in low:
        return "notes-ai"
    if "brain" in low:
        return "notes-brain"
    if "time travel" in low or "worldline" in low:
        return "notes-physics"
    return "notes"


def chunk_markdown(text: str) -> list[dict]:
    parts = HEAD.split(text)
    rows: list[dict] = []
    body0 = parts[0].strip()
    if body0:
        rows.append(
            {
                "id": "notes_preamble",
                "scene": "maho_science",
                "cue_speaker": "Notes",
                "cue": "brain science graduate researcher Leskinen Amadeus AI time travel skeptic",
                "response": body0,
                "response_ja": "",
                "kind": "notes",
            }
        )
    n = 0
    for i in range(1, len(parts), 2):
        title = parts[i].strip()
        body = parts[i + 1].strip() if i + 1 < len(parts) else ""
        if not body:
            continue
        n += 1
        kind = chunk_kind(title)
        cue = title
        if kind == "notes-physics":
            cue = (
                title
                + " wormhole closed timelike curve CTC time travel past future"
                + " Hawking Novikov Gödel Tipler exotic matter chronology protection"
            )
        elif kind == "notes-ai":
            cue = title + " Amadeus AI memory traces generative model Leskinen"
        elif kind == "notes-brain":
            cue = title + " hippocampus episodic memory reconstructive identity"
        rows.append(
            {
                "id": "notes_{0:02d}".format(n),
                "scene": "maho_science",
                "cue_speaker": "Notes",
                "cue": cue,
                "response": body,
                "response_ja": "",
                "kind": kind,
            }
        )
    return rows


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--src", default=str(SRC))
    p.add_argument("--out", default=str(OUT))
    args = p.parse_args()
    text = Path(args.src).read_text(encoding="utf-8")
    rows = chunk_markdown(text)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
    print("notes chunks {0} -> {1}".format(len(rows), out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
