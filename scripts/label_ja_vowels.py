#!/usr/bin/env python3
# Copyright (c) 2026 Martial Systems LLC. MIT.
"""Label mora vowels on the slow set, copy the same sequence onto normal.

Times are scaled per clip after a simple RMS trim. Labels are not
re-derived on the normal take.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from ja_vowels import OVERLAY_VISEME, vowel_labels  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "ja_speech"
MANIFEST = DATA / "manifest.jsonl"
OUT = DATA / "labels.jsonl"


def load_wav(path: Path) -> tuple[int, np.ndarray]:
    import wave

    with wave.open(str(path), "rb") as w:
        nch, sw, sr, n = w.getnchannels(), w.getsampwidth(), w.getframerate(), w.getnframes()
        raw = w.readframes(n)
    if sw != 2:
        raise SystemExit("{0}: need 16-bit PCM, got sampwidth={1}".format(path, sw))
    samples = np.frombuffer(raw, dtype="<i2").astype(np.float32) / 32768.0
    if nch == 2:
        samples = samples[0::2]
    return sr, samples


def speech_span(samples: np.ndarray, sr: int, hop: int = 256) -> tuple[float, float]:
    if samples.size < hop:
        return 0.0, max(samples.size / sr, 0.05)
    n = 1 + (samples.size - hop) // hop
    windows = np.lib.stride_tricks.as_strided(
        samples,
        shape=(n, hop),
        strides=(samples.strides[0] * hop, samples.strides[0]),
    )
    rms = np.sqrt(np.mean(windows * windows, axis=1))
    thresh = max(0.02, float(rms.mean()) * 0.4)
    voiced = np.flatnonzero(rms >= thresh)
    if voiced.size == 0:
        return 0.0, samples.size / sr
    t0 = float(voiced[0] * hop / sr)
    t1 = min(samples.size / sr, float((voiced[-1] * hop + hop) / sr))
    if t1 <= t0:
        t1 = t0 + 0.05
    return t0, t1


def timed_labels(path: Path, labels: list[str]) -> list[dict]:
    sr, samples = load_wav(path)
    t0, t1 = speech_span(samples, sr)
    n = max(1, len(labels))
    dur = (t1 - t0) / n
    out = []
    for i, lab in enumerate(labels):
        out.append(
            {
                "i": i,
                "label": lab,
                "viseme": OVERLAY_VISEME[lab],
                "t0": round(t0 + i * dur, 4),
                "t1": round(t0 + (i + 1) * dur, 4),
            }
        )
    return out


def label_pool(manifest_path: Path, data_root: Path, out_path: Path) -> list[dict]:
    rows = [json.loads(line) for line in manifest_path.read_text(encoding="utf-8").splitlines() if line]
    by_id: dict[str, dict[str, dict]] = {}
    for row in rows:
        by_id.setdefault(row["id"], {})[row["speed"]] = row

    out_rows = []
    for uid, speeds in sorted(by_id.items()):
        slow = speeds.get("slow")
        normal = speeds.get("normal")
        if not slow or not normal:
            continue
        labels = vowel_labels(slow["text"])
        if not labels:
            continue
        slow_timed = timed_labels(data_root / slow["path"], labels)
        normal_timed = timed_labels(data_root / normal["path"], labels)
        if [m["label"] for m in slow_timed] != [m["label"] for m in normal_timed]:
            raise SystemExit("label sequence drifted on {0}".format(uid))
        for speed, timed, src in (
            ("slow", slow_timed, slow),
            ("normal", normal_timed, normal),
        ):
            out_rows.append(
                {
                    "id": uid,
                    "speed": speed,
                    "speed_rate": src["speed_rate"],
                    "speaker": src["speaker"],
                    "path": src["path"],
                    "text": src["text"],
                    "source": src.get("source", ""),
                    "vowels": timed,
                }
            )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in out_rows), encoding="utf-8")
    return out_rows


def main() -> None:
    out = label_pool(MANIFEST, DATA, OUT)
    print("wrote {0} labeled clips -> {1}".format(len(out), OUT))


if __name__ == "__main__":
    main()
