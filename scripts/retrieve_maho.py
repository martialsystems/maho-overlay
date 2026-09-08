#!/usr/bin/env python3
# Copyright (c) 2026 Martial Systems LLC. MIT.
"""Retrieve nearest Maho cue→reply pairs for a user query.

Grok subagent context. No local LLM. No network.
"""

from __future__ import annotations

import argparse
import json
import pickle
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "maho_voice"
MODEL = DATA / "maho_retriever.pkl"


def retrieve(query: str, k: int = 8, model_path: Path = MODEL) -> list[dict]:
    if not query.strip():
        return []
    blob = pickle.loads(model_path.read_bytes())
    vec = blob["vectorizer"].transform([query])
    n = min(k, blob["n"])
    dist, idx = blob["nn"].kneighbors(vec, n_neighbors=n)
    out = []
    for d, i in zip(dist[0], idx[0]):
        row = dict(blob["rows"][int(i)])
        row["distance"] = round(float(d), 4)
        out.append(row)
    return out


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--query", required=True)
    p.add_argument("--k", type=int, default=8)
    p.add_argument("--model", default=str(MODEL))
    p.add_argument("--out", default="-")
    args = p.parse_args()
    hits = retrieve(args.query, k=args.k, model_path=Path(args.model))
    text = json.dumps(hits, ensure_ascii=False, indent=2)
    if args.out == "-":
        sys.stdout.write(text + "\n")
    else:
        Path(args.out).write_text(text + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
