#!/usr/bin/env python3
# Copyright (c) 2026 Martial Systems LLC. MIT.
"""Train a TF-IDF nearest-neighbour retriever on cue→Maho pairs.

This is the chat training step. It fits on CPU with a few megabytes of RAM.
It does not load a local LLM.
"""

from __future__ import annotations

import argparse
import json
import pickle
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import NearestNeighbors

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "maho_voice"
PAIRS = DATA / "sg0_maho_pairs.jsonl"
PHYSICS = DATA / "maho_science.jsonl"
MODEL = DATA / "maho_retriever.pkl"


def docs_for(rows: list[dict]) -> list[str]:
    return ["{0}: {1}\nMaho: {2}".format(r["cue_speaker"], r["cue"], r["response"]) for r in rows]


def train(rows: list[dict]) -> dict:
    if len(rows) < 2:
        raise SystemExit("need at least 2 pairs")
    vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1, max_features=50000)
    matrix = vectorizer.fit_transform(docs_for(rows))
    nn = NearestNeighbors(metric="cosine", algorithm="brute")
    nn.fit(matrix)
    return {"vectorizer": vectorizer, "nn": nn, "rows": rows, "n": len(rows)}


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--pairs", default=str(PAIRS))
    p.add_argument("--physics", default=str(PHYSICS))
    p.add_argument("--out", default=str(MODEL))
    args = p.parse_args()
    path = Path(args.pairs)
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
    extra = Path(args.physics)
    if extra.is_file():
        rows.extend(json.loads(line) for line in extra.read_text(encoding="utf-8").splitlines() if line)
    blob = train(rows)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(pickle.dumps(blob))
    kinds: dict[str, int] = {}
    for r in rows:
        kinds[r.get("kind", "")] = kinds.get(r.get("kind", ""), 0) + 1
    print("trained n={0} kinds={1} -> {2}".format(len(rows), kinds, out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
