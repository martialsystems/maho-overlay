#!/usr/bin/env python3
# Copyright (c) 2026 Martial Systems LLC. MIT.
"""Fetch a pooled Japanese slow+normal speech set.

Does not train sequentially. Writes wavs plus a manifest with speaker id and
speed_rate. Prefers SpeedSpeech-JA-2022 (same sentences at 3.8 and 4.8 mora/s).
Falls back to JSUT basic5000 (first parquet shard) with atempo slow copies.

Amadeus Overlay's 21 JA clips are extra style, not this rate pair. NINJAL
CEJC-Child, ELRA Japanese Kids Speech, and NTT INFANT stay locked.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "ja_speech"
HF_DS = "japanese-asr/ja_asr.jsut_basic5000"
HF_SHARD = "data/test-00000-of-00004.parquet"
NICT_ZIPS = (
    "https://ast-astrec.nict.go.jp/release/speedspeech_ja_2022/speedspeech_ja_2022_v1.0.0.zip",
    "https://ast-astrec.nict.go.jp/en/release/speedspeech_ja_2022/speedspeech_ja_2022_v1.0.0.zip",
)
# Female SpeedSpeech: slow 3.8 mora/s, normal 4.8 mora/s.
SLOW_RATE = 3.8 / 4.8
SPEAKER = "jsut_female"
LIMIT = 400
LOCKED_KIDS = (
    "NINJAL CEJC-Child",
    "ELRA Japanese Kids Speech",
    "NTT INFANT",
)


def run(argv: list[str], **kw) -> subprocess.CompletedProcess:
    return subprocess.run(argv, check=True, **kw)


def nict_zip_ok(url: str) -> bool:
    req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "maho-overlay/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            ctype = (resp.headers.get("Content-Type") or "").lower()
            length = int(resp.headers.get("Content-Length") or "0")
            return "zip" in ctype or length > 10_000_000
    except OSError:
        return False


def write_row(rows: list[dict], **row: object) -> None:
    rows.append(row)


def find_parquet(root: Path) -> Path | None:
    hits = list(root.rglob("test-00000-of-00004.parquet"))
    for hit in hits:
        if hit.stat().st_size > 1_000_000:
            return hit
    return None


def fetch_jsut_shard(dest: Path) -> Path:
    dest.mkdir(parents=True, exist_ok=True)
    existing = find_parquet(dest)
    if existing is not None:
        return existing
    hf = shutil.which("hf")
    if not hf:
        raise SystemExit("hf CLI missing; install huggingface_hub")
    run(
        [
            hf,
            "download",
            HF_DS,
            "--repo-type",
            "dataset",
            "--include",
            HF_SHARD,
            "--local-dir",
            str(dest),
        ]
    )
    found = find_parquet(dest)
    if found is None:
        raise SystemExit("JSUT parquet missing after hf download")
    return found


def extract_wavs(parquet: Path, normal_dir: Path, limit: int) -> list[tuple[str, Path]]:
    import pyarrow.parquet as pq

    normal_dir.mkdir(parents=True, exist_ok=True)
    table = pq.read_table(parquet, columns=["audio", "transcription"])
    n = min(limit, table.num_rows)
    out: list[tuple[str, Path]] = []
    for i in range(n):
        audio = table.column("audio")[i].as_py()
        text = table.column("transcription")[i].as_py() or ""
        raw = audio["bytes"] if isinstance(audio, dict) else None
        if not raw:
            continue
        name = audio.get("path") if isinstance(audio, dict) else None
        uid = Path(name).stem if name else "jsut_{0:04d}".format(i)
        ext = ".wav" if raw[:4] == b"RIFF" else ".flac" if raw[:4] == b"fLaC" else ".bin"
        path = normal_dir / (uid + ext)
        path.write_bytes(raw)
        (normal_dir / (uid + ".txt")).write_text(text, encoding="utf-8")
        out.append((uid, path))
    return out


def make_slow(src: Path, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(src),
            "-filter:a",
            "atempo={0:.6f}".format(SLOW_RATE),
            "-acodec",
            "pcm_s16le",
            str(dest),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def speedspeech_dirs() -> tuple[Path, Path] | None:
    root = DATA / "speedspeech"
    normal = root / "female" / "01_normal"
    slow = root / "female" / "03_slow"
    if normal.is_dir() and slow.is_dir() and any(normal.glob("*.wav")) and any(slow.glob("*.wav")):
        return normal, slow
    return None


def main() -> int:
    DATA.mkdir(parents=True, exist_ok=True)
    print("locked kids corpora stay out: {0}".format(", ".join(LOCKED_KIDS)))
    print("Amadeus JA reaction clips stay out of this pool (extra style, not the rate pair).")
    py = sys.executable
    try:
        import pyarrow.parquet  # noqa: F401
    except ImportError:
        run([py, "-m", "pip", "install", "pyarrow"])

    ss = speedspeech_dirs()
    if ss is not None:
        print("SpeedSpeech dirs present at data/ja_speech/speedspeech/female/{01_normal,03_slow}.")
        print("Re-run labeling from those paired takes instead of JSUT atempo.")
        return 0

    source = "jsut_atempo"
    for url in NICT_ZIPS:
        if nict_zip_ok(url):
            print("NICT SpeedSpeech is up: {0}".format(url))
            print("Unpack female/01_normal and female/03_slow into data/ja_speech/speedspeech/.")
            source = "speedspeech_pending"
            break

    cache = DATA / "_cache"
    parquet = fetch_jsut_shard(cache)
    normal_dir = DATA / "normal"
    slow_dir = DATA / "slow"
    pairs = extract_wavs(parquet, normal_dir, LIMIT)
    rows: list[dict] = []
    for uid, path in pairs:
        slow_path = slow_dir / (uid + ".wav")
        if not slow_path.is_file():
            make_slow(path, slow_path)
        text = (normal_dir / (uid + ".txt")).read_text(encoding="utf-8")
        write_row(
            rows,
            id=uid,
            path=str(path.relative_to(DATA)),
            speed="normal",
            speed_rate=1.0,
            mora_per_sec=4.8,
            speaker=SPEAKER,
            text=text,
            source=source,
        )
        write_row(
            rows,
            id=uid,
            path=str(slow_path.relative_to(DATA)),
            speed="slow",
            speed_rate=round(SLOW_RATE, 4),
            mora_per_sec=3.8,
            speaker=SPEAKER,
            text=text,
            source=source,
        )
    man = DATA / "manifest.jsonl"
    man.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
    print("wrote {0} rows ({1} utterances x 2 speeds) -> {2}".format(len(rows), len(pairs), man))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
