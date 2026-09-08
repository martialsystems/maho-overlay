#!/usr/bin/env python3
# Copyright (c) 2026 Martial Systems LLC. MIT.
"""Split Maho speech clips into loud and quiet delivery banks.

Equalized RMS is already matched, so the split is punch: p90 / median of
voiced 20 ms frames. Clip 10 (馬鹿にしないで) is forced loud. Interior
gaps in a synth are joined so one line is not two takes.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from equalize_maho_clips import SR, active_rms, gain_for, load_s16, write_s16
from maho_clip_script import LINES, NONSPEECH

CLIP10 = "10"
MIN_BAND = 8
FRAME = int(0.02 * SR)


def frame_rms(x: np.ndarray, hop: int = FRAME) -> np.ndarray:
    if x.size < hop:
        return np.array([float(np.sqrt(np.mean(x * x)))], dtype=np.float32)
    out = []
    for i in range(0, x.size - hop, hop):
        sl = x[i : i + hop]
        out.append(float(np.sqrt(np.mean(sl * sl))))
    return np.asarray(out, dtype=np.float32)


def punch_score(x: np.ndarray) -> float:
    v = frame_rms(x)
    v = v[v > 0.02]
    if v.size < 3:
        return 0.0
    med = float(np.median(v))
    if med <= 1e-8:
        return 0.0
    return float(np.percentile(v, 90) / med)


def synth_text(ja: str) -> str:
    """One utterance. Sentence breaks make XTTS drop energy mid-line."""
    t = (ja or "").strip()
    for src, dst in (("！", "、"), ("？", "、"), ("。", "、"), ("――", "、")):
        t = t.replace(src, dst)
    t = t.strip("、")
    if t:
        t = t + "。"
    return t


def voiced_clusters(x: np.ndarray, hop: int = int(0.01 * SR)) -> list[tuple[int, int]]:
    rms = np.array(
        [
            float(np.sqrt(np.mean(x[i : i + hop] ** 2))) if i + hop <= x.size else 0.0
            for i in range(0, x.size, hop)
        ]
    )
    speech = rms > 0.02
    clusters: list[tuple[int, int]] = []
    i = 0
    while i < len(speech):
        if not speech[i]:
            i += 1
            continue
        j = i
        while j < len(speech) and speech[j]:
            j += 1
        a, b = i * hop, min(x.size, j * hop)
        if (b - a) / SR >= 0.06:
            clusters.append((a, b))
        i = j
    return clusters


def max_interior_gap(x: np.ndarray) -> float:
    clusters = voiced_clusters(x)
    if len(clusters) < 2:
        return 0.0
    return max((clusters[i][0] - clusters[i - 1][1]) / SR for i in range(1, len(clusters)))


def join_gaps(x: np.ndarray, target_rms: float, gap_s: float = 0.08) -> np.ndarray:
    """Keep one take. Shrink long holes and match each burst to the same RMS."""
    clusters = voiced_clusters(x)
    if len(clusters) <= 1:
        return x
    pad = int(0.03 * SR)
    gap = np.zeros(int(gap_s * SR), dtype=np.float32)
    parts: list[np.ndarray] = []
    for n, (a, b) in enumerate(clusters):
        sl = x[max(0, a - pad) : min(x.size, b + pad)].astype(np.float32)
        sl = sl * np.float32(gain_for(sl, target_rms))
        if n:
            parts.append(gap)
        parts.append(sl)
    return np.concatenate(parts)


def split_bands(eq_dir: Path) -> dict[str, list[str]]:
    scored: list[tuple[float, str]] = []
    for cid, (_en, _ja) in LINES.items():
        if cid in NONSPEECH:
            continue
        path = eq_dir / (cid + ".wav")
        if not path.is_file():
            continue
        scored.append((punch_score(load_s16(path)), cid))
    if len(scored) < MIN_BAND * 2:
        raise SystemExit("need at least {0} scored speech clips".format(MIN_BAND * 2))
    scored.sort()
    mid = float(np.median([p for p, _ in scored]))
    quiet = [cid for p, cid in scored if p < mid and cid != CLIP10]
    loud = [cid for p, cid in scored if p >= mid or cid == CLIP10]
    # Keep both sides usable as XTTS refs.
    if CLIP10 not in loud:
        loud.append(CLIP10)
        quiet = [c for c in quiet if c != CLIP10]
    if len(loud) < MIN_BAND:
        take = [cid for _p, cid in reversed(scored) if cid not in loud]
        loud.extend(take[: MIN_BAND - len(loud)])
        quiet = [c for c in quiet if c not in loud]
    if len(quiet) < MIN_BAND:
        take = [cid for _p, cid in scored if cid not in quiet and cid not in loud]
        quiet.extend(take[: MIN_BAND - len(quiet)])
        loud = [c for c in loud if c not in quiet or c == CLIP10]
    return {"loud": loud, "quiet": quiet, "median_punch": mid}


def concat_band(eq_dir: Path, ids: list[str], dest: Path, max_seconds: float = 20.0) -> Path:
    cap = int(max_seconds * SR)
    pad = np.zeros(int(0.08 * SR), dtype=np.float32)
    chunks: list[np.ndarray] = []
    n = 0
    # Clip 10 first on the loud ref so the clone starts from the kid-call take.
    ordered = list(ids)
    if CLIP10 in ordered:
        ordered = [CLIP10] + [c for c in ordered if c != CLIP10]
    for cid in ordered:
        path = eq_dir / (cid + ".wav")
        if not path.is_file():
            continue
        x = load_s16(path)
        if n >= cap:
            break
        chunks.append(x)
        chunks.append(pad)
        n += x.size + pad.size
    if not chunks:
        raise SystemExit("no wavs for {0}".format(dest.name))
    dest.parent.mkdir(parents=True, exist_ok=True)
    write_s16(dest, np.concatenate(chunks))
    return dest


def write_bands(eq_dir: Path, bank: Path) -> dict:
    bands = split_bands(eq_dir)
    bank.mkdir(parents=True, exist_ok=True)
    (bank / "bands.json").write_text(json.dumps(bands, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    concat_band(eq_dir, bands["loud"], bank / "maho_ref_ja_loud.wav")
    concat_band(eq_dir, bands["quiet"], bank / "maho_ref_ja_quiet.wav")
    return bands


def loud_ref_wavs(eq_dir: Path, n: int = 8) -> list[Path]:
    """Clip 10 first, then the loud-band takes closest to its punch."""
    bands = split_bands(eq_dir)
    ten = eq_dir / (CLIP10 + ".wav")
    if not ten.is_file():
        raise SystemExit("missing clip 10")
    target = punch_score(load_s16(ten))
    scored = []
    for cid in bands["loud"]:
        path = eq_dir / (cid + ".wav")
        if path.is_file() and cid != CLIP10:
            scored.append((abs(punch_score(load_s16(path)) - target), path))
    scored.sort()
    out = [ten] + [p for _d, p in scored[: max(0, n - 1)]]
    if len(out) < 3:
        raise SystemExit("loud band too small")
    return out

