#!/usr/bin/env python3
# Copyright (c) 2026 Martial Systems LLC. MIT.
"""Retrieve nearest Maho cue→reply pairs for a user query.

Grok subagent context. No local LLM. No network.
"""

from __future__ import annotations

import argparse
import json
import pickle
import re
import sys
from pathlib import Path

from sklearn.metrics.pairwise import cosine_distances

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "maho_voice"
MODEL = DATA / "maho_retriever.pkl"
PHYSICS_Q = re.compile(
    r"\b(wormhole|time[\s-]?travel|timelike|ctc|chronology|g[oö]del|tipler|kerr|"
    r"exotic matter|novikov|hawking|time machine)\b",
    re.I,
)


def _doc(row: dict) -> str:
    return "{0}: {1}\nMaho: {2}".format(row.get("cue_speaker", ""), row.get("cue", ""), row.get("response", ""))


def _boost_notes(blob: dict, query_vec, hits: list[dict], k_notes: int = 3) -> list[dict]:
    notes = [r for r in blob["rows"] if str(r.get("kind", "")).startswith("notes")]
    if not notes:
        return hits
    mat = blob["vectorizer"].transform([_doc(r) for r in notes])
    dist = cosine_distances(query_vec, mat)[0]
    order = dist.argsort()[: min(k_notes, len(notes))]
    boost = []
    for j in order:
        row = dict(notes[int(j)])
        row["distance"] = round(float(dist[int(j)]), 4)
        boost.append(row)
    seen = {h["id"] for h in boost}
    rest = [h for h in hits if h.get("id") not in seen]
    return boost + rest


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
    if PHYSICS_Q.search(query):
        out = _boost_notes(blob, vec, out)
    return out[:k]


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
