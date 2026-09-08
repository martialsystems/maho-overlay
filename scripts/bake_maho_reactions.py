#!/usr/bin/env python3
# Copyright (c) 2026 Martial Systems LLC. MIT.
"""Bake Japanese cat/head reaction WAVs from the loud Maho bank.

Uses the equalized clip for the one line that is already in the bank
(馬鹿にしないで). Other lines are XTTS ja on the loud band (clip 10 first),
one utterance, gaps joined, then hiss-shelved toward clip 10.
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
from maho_energy_bands import join_gaps, loud_ref_wavs, max_interior_gap, synth_text  # noqa: E402
from train_maho_voice_bank import artifacted, clip_stats  # noqa: E402

BANK = ROOT / "data" / "maho_voice" / "bank"
EQ = BANK / "equalized"
AUDIO_DIR = BACKEND / "assets" / "reaction_audio"
# Clip 10 is the recorded take of this exact line.
CLIP_COPY = {
    "馬鹿にしないで。本気なんだから。": EQ / "10.wav",
}
N_FFT = 1024
HOP = 256
TEMPERATURES = (0.28, 0.4)


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


def hf_ratio(x: np.ndarray, sr: int = SR) -> float:
    """Voiced-frame 4-8 kHz energy over 0.3-2.5 kHz. Raspy clones score high."""
    n = 2048
    hop = 512
    if x.size < n:
        x = np.pad(x, (0, n - x.size))
    w = np.hanning(n)
    freqs = np.fft.rfftfreq(n, 1.0 / sr)
    lows: list[float] = []
    highs: list[float] = []
    for i in range(0, x.size - n + 1, hop):
        sl = x[i : i + n]
        if float(np.sqrt(np.mean(sl * sl))) < 0.02:
            continue
        mag = np.abs(np.fft.rfft(sl * w)) + 1e-12
        lows.append(float(mag[(freqs >= 300) & (freqs < 2500)].mean()))
        highs.append(float(mag[(freqs >= 4000) & (freqs < 8000)].mean()))
    if not lows:
        return 0.0
    return float(np.median(highs) / np.median(lows))


def voiced_frac(x: np.ndarray) -> float:
    hop = int(0.02 * SR)
    if x.size < hop:
        return 0.0
    n = 0
    v = 0
    for i in range(0, x.size - hop, hop):
        n += 1
        if float(np.sqrt(np.mean(x[i : i + hop] ** 2))) > 0.02:
            v += 1
    return v / max(1, n)


def spectral_match(x: np.ndarray, ref: np.ndarray) -> np.ndarray:
    """Cut excess 4 kHz+ grain toward the recorded clip. Midrange stays put."""
    rx = hf_ratio(x)
    rr = hf_ratio(ref)
    if rx <= rr * 1.15:
        return x
    scale = float(np.clip(max(rr, 1e-6) / rx, 0.25, 1.0))
    w = np.hanning(N_FFT).astype(np.float32)
    freqs = np.fft.rfftfreq(N_FFT, 1.0 / SR)
    gain = np.ones(freqs.shape[0], dtype=np.float32)
    t = np.clip((freqs - 3500.0) / 1500.0, 0.0, 1.0)
    gain = 1.0 - t * (1.0 - scale)
    y = np.zeros(x.size + N_FFT, dtype=np.float32)
    wsum = np.zeros_like(y)
    for i in range(0, max(1, x.size - N_FFT), HOP):
        sl = x[i : i + N_FFT]
        if sl.size < N_FFT:
            sl = np.pad(sl, (0, N_FFT - sl.size))
        spec = np.fft.rfft(sl * w) * gain
        out = np.fft.irfft(spec, n=N_FFT).real.astype(np.float32)
        y[i : i + N_FFT] += out * w
        wsum[i : i + N_FFT] += w * w
    wsum = np.maximum(wsum, 1e-8)
    return (y[: x.size] / wsum[: x.size]).astype(np.float32)


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


def rasp_score(x: np.ndarray, ref_hf: float) -> float:
    hf = hf_ratio(x)
    over = max(0.0, hf / max(ref_hf, 1e-6) - 1.0)
    long = max(0.0, x.size / SR - 4.2)
    short = max(0.0, 1.5 - x.size / SR)
    thin = max(0.0, 0.35 - voiced_frac(x))
    return over + 0.2 * long + 4.0 * short + 6.0 * thin


class XttsJa:
    def __init__(self, refs: list[Path]) -> None:
        from TTS.api import TTS  # type: ignore

        self.tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2")
        self.refs = [str(p) for p in refs]

    def synth(self, text: str, dest: Path, temperature: float) -> None:
        dest.parent.mkdir(parents=True, exist_ok=True)
        self.tts.tts_to_file(
            text=text,
            speaker_wav=self.refs,
            language="ja",
            file_path=str(dest),
            temperature=temperature,
            top_p=0.65,
            top_k=20,
            repetition_penalty=5.0,
            gpt_cond_len=8,
            gpt_cond_chunk_len=4,
            sound_norm_refs=True,
            split_sentences=False,
        )


def finish(y: np.ndarray, ref: np.ndarray, target: float) -> np.ndarray:
    y = trim_pad(y)
    y = join_gaps(y, target)
    if y.size / SR > 6.5:
        y = first_cluster(y, max_gap_s=0.85)
    y = spectral_match(trim_pad(y), ref)
    return match_loudness(trim_pad(y), target)


def bake(jobs: list[tuple[Path, str]], synth: bool) -> dict:
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    src10 = CLIP_COPY["馬鹿にしないで。本気なんだから。"]
    if not src10.is_file():
        raise SystemExit("missing equalized clip 10")
    ref = load_s16(src10)
    target = active_rms(ref)
    ref_hf = hf_ratio(ref)
    src_centroid = clip_stats(ref)["centroid"]
    report: dict = {"target_rms": target, "ref_hf": ref_hf, "files": []}
    xtts = None
    if synth and any(CLIP_COPY.get(text) is None for _p, text in jobs):
        xtts = XttsJa(loud_ref_wavs(EQ))

    for path, text in jobs:
        src = CLIP_COPY.get(text)
        if src is not None:
            y = match_loudness(trim_pad(load_s16(src)), target)
            write_s16(path, y)
            st = clip_stats(y)
            report["files"].append(
                {"name": path.name, "source": "clip", "text": text, "hf": hf_ratio(y), **st}
            )
            print("[bake] copy", path.name, text)
            continue
        if xtts is None:
            raise SystemExit("missing {0}; run with --synth".format(path.name))
        best = None
        best_score = 1e9
        best_temp = TEMPERATURES[0]
        for temperature in TEMPERATURES:
            raw = path.with_suffix(".xtts-raw.wav")
            tmp = path.with_suffix(".xtts.wav")
            spoken = synth_text(text)
            print("[bake] synth", path.name, "t={0}".format(temperature), spoken)
            xtts.synth(spoken, raw, temperature=temperature)
            ffmpeg_mono16(raw, tmp)
            y = finish(load_s16(tmp), ref, target)
            score = rasp_score(y, ref_hf)
            reasons = artifacted(clip_stats(y), src_centroid)
            print("[bake]", path.name, "t={0}".format(temperature), "hf={0:.3f}".format(hf_ratio(y)), "score={0:.3f}".format(score), reasons or "none")
            if voiced_frac(y) < 0.25 or y.size / SR < 1.2:
                score += 20.0
            if score < best_score:
                best, best_score, best_temp = y, score, temperature
            raw.unlink(missing_ok=True)
            tmp.unlink(missing_ok=True)
        assert best is not None
        write_s16(path, best)
        st = clip_stats(best)
        hf = hf_ratio(best)
        report["files"].append(
            {
                "name": path.name,
                "source": "xtts",
                "text": text,
                "hf": hf,
                "temperature": best_temp,
                "rasp_score": best_score,
                **st,
            }
        )
        print("[bake] pick", path.name, "t={0}".format(best_temp), "hf={0:.3f}".format(hf))
    return report


def check_jobs(jobs: list[tuple[Path, str]]) -> None:
    missing = [path.name for path, _ in jobs if not path.is_file()]
    if missing:
        raise SystemExit("missing " + ", ".join(missing))
    copy_names = set()
    ref_wav = None
    for path, text in jobs:
        raw = path.read_bytes()[:12]
        if raw[:4] != b"RIFF":
            raise SystemExit("{0} is not a WAV".format(path.name))
        if text in CLIP_COPY:
            copy_names.add(path)
            ref_wav = path
    if ref_wav is None:
        raise SystemExit("clip-copy wav missing")
    ref_hf = hf_ratio(load_s16(ref_wav))
    cap = max(2.2, 3.0 * ref_hf)
    for path, text in jobs:
        if path in copy_names:
            continue
        x = load_s16(path)
        hf = hf_ratio(x)
        if hf > cap:
            raise SystemExit("{0} too raspy hf={1:.3f} cap={2:.3f}".format(path.name, hf, cap))
        if x.size / SR < 1.2 or voiced_frac(x) < 0.25:
            raise SystemExit("{0} too thin dur={1:.2f} voiced={2:.2f}".format(path.name, x.size / SR, voiced_frac(x)))
        gap = max_interior_gap(x)
        if gap > 0.45:
            raise SystemExit("{0} two takes gap={1:.2f}s".format(path.name, gap))
    print("ok", len(jobs), "reaction wavs", "ref_hf={0:.3f}".format(ref_hf))


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--synth", action="store_true", help="XTTS ja for lines not in the clip bank")
    p.add_argument("--check", action="store_true")
    args = p.parse_args()
    jobs = reaction_jobs()
    if args.check:
        check_jobs(jobs)
        return 0
    bake(jobs, synth=args.synth)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
