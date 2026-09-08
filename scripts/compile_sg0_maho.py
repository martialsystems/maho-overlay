#!/usr/bin/env python3
# Copyright (c) 2026 Martial Systems LLC. MIT.
"""Compile Hiyajou Maho lines from a Steins;Gate 0 .scx.txt dump.

English is extracted from the local transcript pack. Japanese is joined from
a gitignored EN→JA map after that extract (not a second speaker dump).
Solo Maho only. Amadeus Maho and joint lines stay out of the voice set.

Does not extract audio. Does not train. Does not fine-tune the viseme pool.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from maho_ja_style import ellipsis_ja, is_ellipsis, ja_register_flags  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "maho_voice"
DEFAULT_SRC = Path.home() / "Documents" / "SG0 Transcript"
LINE_RE = re.compile(r"\[name\](.*?)\[line\](.*?)\[%(?:p|e)\]", re.S)
TAG_RE = re.compile(r"\[[^\]]+\]")

SOLO = frozenset({"Maho", "Maho?"})
SKIP = frozenset(
    {
        "Amadeus Maho",
        "Rintaro&Maho",
        "Moeka&Maho",
        "Itaru&Maho",
        "Amadeus Kurisu&Maho",
    }
)


def clean_line(raw: str) -> str:
    text = TAG_RE.sub("", raw)
    text = text.replace("\u3000", " ")
    text = re.sub(r"\s+", " ", text).strip()
    if (text.startswith("“") and text.endswith("”")) or (text.startswith('"') and text.endswith('"')):
        text = text[1:-1].strip()
    return text


def line_kind(text: str) -> str:
    if (text.startswith("(") and text.endswith(")")) or (text.startswith("（") and text.endswith("）")):
        return "thought"
    return "spoken"


def unwrap_thought(text: str) -> str:
    if line_kind(text) == "thought":
        return text[1:-1].strip()
    return text


def iter_named_lines(path: Path) -> list[tuple[str, str]]:
    blob = path.read_text(encoding="utf-8", errors="replace")
    return [(name.strip(), clean_line(raw)) for name, raw in LINE_RE.findall(blob)]


def extract_en(src: Path) -> list[dict]:
    rows: list[dict] = []
    files = sorted(src.glob("*.txt")) + sorted(src.glob("*.scx.txt"))
    seen = set()
    for path in files:
        if path in seen:
            continue
        seen.add(path)
        scene = path.name.replace(".scx.txt", "").replace(".txt", "")
        n = 0
        for name, text in iter_named_lines(path):
            if name in SKIP:
                continue
            if name not in SOLO:
                continue
            if not text:
                continue
            kind = line_kind(text)
            body = unwrap_thought(text)
            n += 1
            rows.append(
                {
                    "id": "{0}_{1:04d}".format(scene, n),
                    "scene": scene,
                    "i": n,
                    "speaker": "maho",
                    "source_name": name,
                    "kind": kind,
                    "lang": "en",
                    "text": body,
                }
            )
    return rows


def load_ja_map(path: Path) -> dict[str, str]:
    if not path.is_file():
        return {}
    blob = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(blob, dict):
        return {str(k): str(v) for k, v in blob.items()}
    raise SystemExit("ja map must be an object of en_text -> ja_text")


def attach_ja(en_rows: list[dict], ja_map: dict[str, str]) -> list[dict]:
    out = []
    missing = 0
    bad = 0
    for row in en_rows:
        ja_row = dict(row)
        ja_row["lang"] = "ja"
        en = row["text"]
        if is_ellipsis(en):
            ja = ellipsis_ja(en)
        elif en in ja_map:
            ja = ja_map[en]
        else:
            ja = ""
            missing += 1
        flags = ja_register_flags(ja) if ja else []
        if flags:
            bad += 1
        ja_row["text"] = ja
        ja_row["en_text"] = en
        ja_row["register_flags"] = flags
        out.append(ja_row)
    return out, missing, bad


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")


def write_sidecar_txt(dir_path: Path, rows: list[dict], field: str) -> None:
    dir_path.mkdir(parents=True, exist_ok=True)
    for row in rows:
        if row["kind"] != "spoken":
            continue
        if not row.get(field):
            continue
        (dir_path / (row["id"] + ".txt")).write_text(row[field] + "\n", encoding="utf-8")


def unique_en(rows: list[dict]) -> list[str]:
    seen = []
    got = set()
    for row in rows:
        t = row["text"]
        if t not in got:
            got.add(t)
            seen.append(t)
    return seen


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--src", default=str(DEFAULT_SRC))
    p.add_argument("--out", default=str(DATA))
    p.add_argument("--ja-map", default=str(DATA / "sg0_maho_en_to_ja.json"))
    p.add_argument("--sidecars", action="store_true")
    args = p.parse_args()
    src = Path(args.src).expanduser()
    if not src.is_dir():
        raise SystemExit("transcript dir missing: {0}".format(src))
    en_rows = extract_en(src)
    out = Path(args.out)
    write_jsonl(out / "sg0_maho_en.jsonl", en_rows)
    uniq = unique_en(en_rows)
    (out / "sg0_maho_en_unique.json").write_text(
        json.dumps(uniq, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    spoken = [r for r in en_rows if r["kind"] == "spoken"]
    print(
        "en lines {0} spoken {1} thought {2} unique {3} -> {4}".format(
            len(en_rows),
            len(spoken),
            len(en_rows) - len(spoken),
            len(uniq),
            out / "sg0_maho_en.jsonl",
        )
    )
    ja_map = load_ja_map(Path(args.ja_map))
    ja_rows, missing, bad = attach_ja(en_rows, ja_map)
    write_jsonl(out / "sg0_maho_ja.jsonl", ja_rows)
    filled = sum(1 for r in ja_rows if r["text"])
    print("ja filled {0}/{1} missing {2} register_flags {3}".format(filled, len(ja_rows), missing, bad))
    if args.sidecars:
        write_sidecar_txt(out / "en_txt", en_rows, "text")
        write_sidecar_txt(out / "ja_txt", ja_rows, "text")
    report = {
        "en_lines": len(en_rows),
        "en_spoken": len(spoken),
        "en_unique": len(uniq),
        "ja_filled": filled,
        "ja_missing": missing,
        "ja_register_flags": bad,
        "src": str(src),
    }
    (out / "sg0_maho_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return 0 if missing == 0 or not ja_map else 0


if __name__ == "__main__":
    raise SystemExit(main())
