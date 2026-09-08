#!/usr/bin/env python3
# Copyright (c) 2026 Martial Systems LLC. MIT.
"""Bake Japanese cat/head reaction WAVs from the Maho speaker bank.

Uses the equalized clip for the one line that is already in the bank
(馬鹿にしないで). Other lines are XTTS ja on a short emotional reference,
then loudness-matched to clip 10. Artifacted synths retry on the reverse mix.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import numpy as np

os.environ.setdefault("COQUI_TOS_AGREED", "1")

SCRIPTS = Path(__file__).resolve().parent
ROOT = SCRIPTS.parent
BACKEND = ROOT / "backend"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from chat_interactions import INTERACTION_RESPONSES  # noqa: E402
from equalize_maho_clips import (  # noqa: E402
    PEAK_LIMIT,
    SR,
    active_rms,
    ffmpeg_mono16,
    gain_for,
    load_s16,
    write_s16,
)
from train_maho_voice_bank import artifacted, clip_stats, synth_xtts  # noqa: E402

BANK = ROOT / "data" / "maho_voice" / "bank"
EQ = BANK / "equalized"
AUDIO_DIR = BACKEND / "assets" / "reaction_audio"
# Clip 10 is the recorded take of this exact line.
CLIP_COPY = {
    "馬鹿にしないで。本気なんだから。": EQ / "10.wav",
}
EMOTION_CLIPS = ("10", "6", "8", "13", "38")


def spoken_text(raw: str) -> str:
    return " ".join((raw or "").strip().split())


def reaction_jobs() -> list[tuple[Path, str]]:
    jobs: list[tuple[Path, str]] = []
    seen: set[Path] = set()
    for variants in INTERACTION_RESPONSES.values():
        for variant in variants:
            audio_url = variant.get("audio_url")
            text = spoken_text(str(variant.get("text") or ""))
            if not audio_url or not text:
                continue
            path = BACKEND / str(audio_url)
            if path in seen:
                continue
            seen.add(path)
            jobs.append((path, text))
    return jobs


def build_emotion_ref(dest: Path) -> Path:
    chunks: list[np.ndarray] = []
    pad = np.zeros(int(0.12 * SR), dtype=np.float32)
    for stem in EMOTION_CLIPS:
        path = EQ / (stem + ".wav")
        if not path.is_file():
            continue
        chunks.append(load_s16(path))
        chunks.append(pad)
    if not chunks:
        raise SystemExit("need equalized emotion clips")
    write_s16(dest, np.concatenate(chunks))
    return dest


def match_loudness(x: np.ndarray, target: float) -> np.ndarray:
    y = x * gain_for(x, target)
    peak = float(np.max(np.abs(y))) if y.size else 0.0
    if peak > PEAK_LIMIT and peak > 0:
        y = y * (PEAK_LIMIT / peak)
    return y.astype(np.float32)


def trim_pad(x: np.ndarray, pad_s: float = 0.08) -> np.ndarray:
    mag = np.abs(x)
    voiced = mag > 0.02
    if not voiced.any():
        return x
    a = int(np.argmax(voiced))
    b = int(len(x) - np.argmax(voiced[::-1]))
    pad = int(pad_s * SR)
    return x[max(0, a - pad) : min(len(x), b + pad)]


def first_cluster(x: np.ndarray, max_gap_s: float = 0.35) -> np.ndarray:
    """Drop extra XTTS bursts after a long hole. Keep a two-phrase line if the gap is short."""
    hop = int(0.01 * SR)
    rms = np.array(
        [
            float(np.sqrt(np.mean(x[i : i + hop] ** 2))) if i + hop <= len(x) else 0.0
            for i in range(0, len(x), hop)
        ]
    )
    speech = rms > 0.02
    if not speech.any():
        return x
    start = int(np.argmax(speech))
    need_gap = int(max_gap_s / 0.01)
    gap = 0
    end = start
    for i in range(start, len(speech)):
        if speech[i]:
            gap = 0
            end = i
        else:
            gap += 1
            if gap > need_gap and (end - start) >= 20:
                break
    a = max(0, start * hop - int(0.05 * SR))
    b = min(len(x), (end + 1) * hop + int(0.12 * SR))
    return x[a:b]


def bake(jobs: list[tuple[Path, str]], synth: bool) -> dict:
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    src10 = CLIP_COPY["馬鹿にしないで。本気なんだから。"]
    if not src10.is_file():
        raise SystemExit("missing equalized clip 10")
    target = active_rms(load_s16(src10))
    ref = BANK / "maho_reaction_ref.wav"
    build_emotion_ref(ref)
    alt = BANK / "maho_ref_ja_b.wav"
    report: dict = {"target_rms": target, "files": []}
    src_centroid = clip_stats(load_s16(src10))["centroid"]

    for path, text in jobs:
        src = CLIP_COPY.get(text)
        if src is not None:
            y = match_loudness(trim_pad(load_s16(src)), target)
            write_s16(path, y)
            st = clip_stats(y)
            report["files"].append({"name": path.name, "source": "clip", "text": text, **st})
            print("[bake] copy", path.name, text)
            continue
        if not synth:
            raise SystemExit("missing {0}; run with --synth".format(path.name))
        raw = path.with_suffix(".xtts-raw.wav")
        tmp = path.with_suffix(".xtts.wav")
        print("[bake] synth", path.name, text)
        synth_xtts(text, ref, raw, language="ja")
        ffmpeg_mono16(raw, tmp)
        y = load_s16(tmp)
        reasons = artifacted(clip_stats(y), src_centroid)
        if reasons and alt.is_file():
            raw2 = path.with_suffix(".xtts-raw-b.wav")
            tmp2 = path.with_suffix(".xtts_b.wav")
            print("[bake] retry", path.name, reasons)
            synth_xtts(text, alt, raw2, language="ja")
            ffmpeg_mono16(raw2, tmp2)
            y2 = load_s16(tmp2)
            r2 = artifacted(clip_stats(y2), src_centroid)
            if len(r2) <= len(reasons):
                y, reasons = y2, r2
            raw2.unlink(missing_ok=True)
            tmp2.unlink(missing_ok=True)
        if y.size / SR > 4.2 or clip_stats(y)["holes"] >= 3:
            y = first_cluster(y)
        y = match_loudness(trim_pad(y), target)
        write_s16(path, y)
        raw.unlink(missing_ok=True)
        st = clip_stats(y)
        report["files"].append(
            {"name": path.name, "source": "xtts", "text": text, "reasons": reasons, **st}
        )
        print("[bake]", path.name, "artifacts", reasons or "none")
        tmp.unlink(missing_ok=True)
        path.with_suffix(".xtts_b.wav").unlink(missing_ok=True)
    return report


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--synth", action="store_true", help="XTTS ja for lines not in the clip bank")
    p.add_argument("--check", action="store_true")
    args = p.parse_args()
    jobs = reaction_jobs()
    if args.check:
        missing = [path.name for path, _ in jobs if not path.is_file()]
        if missing:
            raise SystemExit("missing " + ", ".join(missing))
        for path, _text in jobs:
            raw = path.read_bytes()[:12]
            if raw[:4] != b"RIFF":
                raise SystemExit("{0} is not a WAV".format(path.name))
        print("ok", len(jobs), "reaction wavs")
        return 0
    bake(jobs, synth=args.synth)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
