#!/usr/bin/env python3
# Copyright (c) 2026 Martial Systems LLC. MIT.
"""Equalize Maho clip loudness, then write 48 kHz mono 16-bit PCM.

Spoken clips match the median active RMS. Ellipsis/sigh/exclaim clips are
not boosted up to speech (that pumps noise). Peak cap 0.89.
"""

from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np

SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from maho_clip_script import MISSING, NONSPEECH  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
SRC_DEFAULT = Path.home() / "Documents" / "maho_clips"
OUT_DEFAULT = ROOT / "data" / "maho_voice" / "bank" / "equalized"
GATE = 0.02
PEAK_LIMIT = 0.89
TOLERANCE_DB = 2.0
SR = 48000


def ffmpeg_mono16(src: Path, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    subprocess.check_call(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(src),
            "-ac",
            "1",
            "-ar",
            str(SR),
            "-sample_fmt",
            "s16",
            str(dest),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def load_s16(path: Path) -> np.ndarray:
    with wave.open(str(path), "rb") as w:
        if w.getsampwidth() != 2 or w.getnchannels() != 1:
            raise SystemExit("{0}: need mono 16-bit".format(path))
        raw = w.readframes(w.getnframes())
    return np.frombuffer(raw, dtype="<i2").astype(np.float32) / 32768.0


def write_s16(path: Path, samples: np.ndarray) -> None:
    clipped = np.clip(samples, -1.0, 1.0)
    pcm = np.round(clipped * 32767.0).astype("<i2")
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


def peak(x: np.ndarray) -> float:
    return float(np.max(np.abs(x))) if x.size else 0.0


def active_rms(x: np.ndarray) -> float:
    top = peak(x)
    gate = max(GATE, 0.2 * top)
    act = x[np.abs(x) > gate]
    if act.size == 0:
        return 0.0
    return float(np.sqrt(np.mean(act * act)))


def gain_for(x: np.ndarray, target: float) -> float:
    current = active_rms(x)
    if current <= 1e-8 or target <= 1e-8:
        return 1.0
    gain = target / current
    top = peak(x)
    if top * gain > PEAK_LIMIT and top > 1e-8:
        gain = PEAK_LIMIT / top
    return float(gain)


def list_wavs(src: Path) -> list[Path]:
    return sorted(
        src.glob("*.wav"),
        key=lambda p: (not p.stem.isdigit(), int(p.stem) if p.stem.isdigit() else 0, p.stem),
    )


def equalize(src: Path, dest: Path) -> dict:
    wavs = list_wavs(src)
    if not wavs:
        raise SystemExit("no wavs in {0}".format(src))
    tmp = dest / "_tmp"
    tmp.mkdir(parents=True, exist_ok=True)
    loaded: list[tuple[Path, np.ndarray]] = []
    speech_rms: list[float] = []
    for path in wavs:
        tpath = tmp / (path.stem + ".wav")
        ffmpeg_mono16(path, tpath)
        x = load_s16(tpath)
        loaded.append((path, x))
        if path.stem not in NONSPEECH:
            r = active_rms(x)
            if r > 1e-4:
                speech_rms.append(r)
    if not speech_rms:
        raise SystemExit("no speech RMS")
    target = float(np.median(np.array(speech_rms)))
    report = {"target": target, "n": len(loaded), "missing": sorted(MISSING), "gains": {}}
    dest.mkdir(parents=True, exist_ok=True)
    for path, x in loaded:
        tgt = target
        if path.stem in NONSPEECH:
            # Keep pauses quieter than speech. Cap boost at +3 dB.
            cur = active_rms(x)
            modest = min(target * 0.35, cur * (10 ** (3 / 20)) if cur > 1e-8 else 1.0)
            tgt = max(cur, modest) if cur > 1e-8 else cur
        g = gain_for(x, tgt)
        out = dest / (path.stem + ".wav")
        write_s16(out, x * g)
        report["gains"][path.stem] = {
            "gain": round(g, 4),
            "rms_before": round(active_rms(x), 5),
            "rms_after": round(active_rms(load_s16(out)), 5),
            "nonspeech": path.stem in NONSPEECH,
        }
    for p in tmp.glob("*.wav"):
        p.unlink()
    tmp.rmdir()
    (dest.parent / "equalize_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def assert_matched(dest: Path, tolerance_db: float = TOLERANCE_DB) -> None:
    speech = []
    for path in list_wavs(dest):
        x = load_s16(path)
        r = active_rms(x)
        if path.stem in NONSPEECH:
            continue
        if r <= 1e-8:
            raise SystemExit("silent speech after equalize: {0}".format(path.name))
        speech.append((path.stem, r))
    if len(speech) < 20:
        raise SystemExit("expected at least 20 speech clips, got {0}".format(len(speech)))
    vals = [r for _, r in speech]
    target = float(np.median(np.array(vals)))
    max_ratio = 10 ** (tolerance_db / 20)
    bad = []
    for name, r in speech:
        ratio = max(r / target, target / r)
        if ratio > max_ratio:
            bad.append((name, r, target, 20 * math.log10(ratio)))
    if bad:
        raise SystemExit("speech RMS off by more than {0} dB: {1}".format(tolerance_db, bad[:8]))


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--src", default=str(SRC_DEFAULT))
    p.add_argument("--dest", default=str(OUT_DEFAULT))
    p.add_argument("--check", action="store_true")
    args = p.parse_args()
    src, dest = Path(args.src).expanduser(), Path(args.dest)
    if args.check:
        assert_matched(dest)
        print("[equalize] speech clips within {0} dB of median".format(TOLERANCE_DB))
        return 0
    report = equalize(src, dest)
    print("[equalize] n={0} target={1:.4f} missing={2}".format(report["n"], report["target"], report["missing"]))
    assert_matched(dest)
    print("[equalize] ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
