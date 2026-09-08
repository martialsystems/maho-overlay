#!/usr/bin/env python3
# Copyright (c) 2026 Martial Systems LLC. MIT.
"""Train a Japanese Maho speaker bank from equalized clips.

Does not use a single 10 s XTTS clone (that caused Amadeus English
artifacts). Fits a log-mel speaker encoder on all speech clips, writes
the bank pickle, then optionally synthesizes JA test lines with XTTS
conditioned on the multi-clip reference. Artifacted synths trigger a
second pass with a different reference mix.
"""

from __future__ import annotations

import argparse
import json
import pickle
import sys
import wave
from pathlib import Path

import numpy as np

SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from equalize_maho_clips import SR, load_s16  # noqa: E402
from maho_clip_script import NONSPEECH  # noqa: E402
from maho_energy_bands import CLIP10, split_bands  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
BANK = ROOT / "data" / "maho_voice" / "bank"
EQ = BANK / "equalized"
MODEL = BANK / "maho_speaker_bank.pkl"
N_FFT = 1024
N_MELS = 40
HOP = 256


def log_mel(x: np.ndarray) -> np.ndarray:
    if x.size < N_FFT:
        x = np.pad(x, (0, N_FFT - x.size))
    w = np.hanning(N_FFT)
    frames = []
    for i in range(0, x.size - N_FFT + 1, HOP):
        spec = np.abs(np.fft.rfft(x[i : i + N_FFT] * w, n=N_FFT)) + 1e-8
        frames.append(spec)
    if not frames:
        frames = [np.abs(np.fft.rfft(x[:N_FFT] * w, n=N_FFT)) + 1e-8]
    mag = np.stack(frames)
    # triangular mel-ish bins
    edges = np.linspace(0, mag.shape[1], N_MELS + 1).astype(int)
    mel = np.zeros((mag.shape[0], N_MELS), dtype=np.float32)
    for j in range(N_MELS):
        a, b = edges[j], max(edges[j] + 1, edges[j + 1])
        mel[:, j] = mag[:, a:b].mean(axis=1)
    return np.log(mel)


def clip_stats(x: np.ndarray) -> dict:
    peak = float(np.max(np.abs(x))) if x.size else 0.0
    clipped = int(np.sum(np.abs(x) >= 0.99))
    # interior holes: 50 ms of near-zero after speech has started
    gate = 0.02
    mag = np.abs(x)
    voiced = mag > gate
    holes = 0
    if voiced.any():
        a = int(np.argmax(voiced))
        b = int(len(x) - np.argmax(voiced[::-1]))
        z = mag[a:b] < 0.005
        run = 0
        need = int(0.05 * SR)
        for v in z:
            run = run + 1 if v else 0
            if run == need:
                holes += 1
    mel = log_mel(x)
    return {
        "peak": peak,
        "clipped": clipped,
        "holes": holes,
        "centroid": float(np.mean(np.exp(mel) * np.arange(1, N_MELS + 1))),
        "dur": x.size / SR,
    }


def artifacted(stats: dict, src_centroid: float) -> list[str]:
    reasons = []
    if stats["clipped"] > SR * 0.01:
        reasons.append("clipping")
    if stats["holes"] >= 3:
        reasons.append("dropouts")
    if stats["peak"] < 0.05:
        reasons.append("too_quiet")
    if src_centroid > 0 and abs(stats["centroid"] - src_centroid) / src_centroid > 0.55:
        reasons.append("spectral_drift")
    return reasons


def train_encoder(paths: list[Path]) -> dict:
    means = []
    ids = []
    cents = []
    for path in paths:
        x = load_s16(path)
        mel = log_mel(x)
        mu = mel.mean(axis=0)
        means.append(mu)
        ids.append(path.stem)
        st = clip_stats(x)
        cents.append(st["centroid"])
    M = np.stack(means)
    mu = M.mean(axis=0)
    xc = M - mu
    # PCA speaker space (all Maho clips). Keep 12 components or fewer.
    cov = (xc.T @ xc) / max(1, len(M) - 1)
    eigval, eigvec = np.linalg.eigh(cov)
    order = np.argsort(eigval)[::-1]
    k = min(12, eigvec.shape[1])
    basis = eigvec[:, order[:k]]
    embeddings = xc @ basis
    return {
        "mean_mel": mu.astype(np.float32),
        "basis": basis.astype(np.float32),
        "embeddings": {i: embeddings[n].astype(np.float32) for n, i in enumerate(ids)},
        "src_centroid": float(np.median(cents)),
        "n_speech": len(ids),
        "lang": "ja",
        "ref_wav": "maho_ref_ja.wav",
        "note": "multi-clip Japanese bank; not a 10s XTTS one-shot",
        "band": None,
    }


def synth_xtts(text: str, ref: Path, dest: Path, language: str = "ja") -> None:
    from TTS.api import TTS  # type: ignore

    dest.parent.mkdir(parents=True, exist_ok=True)
    tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2")
    tts.tts_to_file(
        text=text,
        speaker_wav=str(ref),
        language=language,
        file_path=str(dest),
    )


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--synth", action="store_true", help="also run XTTS ja on the multi-clip ref")
    p.add_argument("--retrain-synth", action="store_true", help="second synth pass if artifacts")
    args = p.parse_args()
    speech = [
        EQ / (p.stem + ".wav")
        for p in EQ.glob("*.wav")
        if p.stem not in NONSPEECH
    ]
    if len(speech) < 20:
        raise SystemExit("need equalized speech clips first")
    bands = split_bands(EQ)
    by_id = {p.stem: p for p in speech}
    loud_paths = [by_id[i] for i in bands["loud"] if i in by_id]
    quiet_paths = [by_id[i] for i in bands["quiet"] if i in by_id]
    if len(loud_paths) < 8 or len(quiet_paths) < 8:
        raise SystemExit("loud {0} quiet {1}: need 8 each".format(len(loud_paths), len(quiet_paths)))
    loud = train_encoder(loud_paths)
    loud["band"] = "loud"
    loud["ref_wav"] = "maho_ref_ja_loud.wav"
    quiet = train_encoder(quiet_paths)
    quiet["band"] = "quiet"
    quiet["ref_wav"] = "maho_ref_ja_quiet.wav"
    blob = train_encoder(speech)
    blob["bands"] = {"loud": loud, "quiet": quiet}
    blob["clip10_band"] = "loud"
    blob["loud_ids"] = bands["loud"]
    blob["quiet_ids"] = bands["quiet"]
    if CLIP10 not in bands["loud"]:
        raise SystemExit("clip 10 must be in the loud band")
    MODEL.write_bytes(pickle.dumps(blob))
    print(
        "trained speaker bank n={0} loud={1} quiet={2} pca={3} -> {4}".format(
            blob["n_speech"],
            loud["n_speech"],
            quiet["n_speech"],
            blob["basis"].shape[1],
            MODEL,
        )
    )
    report = {
        "encoder": str(MODEL),
        "n_speech": blob["n_speech"],
        "n_loud": loud["n_speech"],
        "n_quiet": quiet["n_speech"],
        "synths": [],
    }
    if args.synth:
        ref = BANK / "maho_ref_ja.wav"
        if not ref.is_file():
            raise SystemExit("run build_maho_voice_dataset.py first")
        tests = [
            ("clip1", "紅莉栖の記憶、なの？"),
            ("clip58", "方法は一つ。かがりから紅莉栖の記憶を取り除くこと。"),
            ("clip57", "何もしなければ、人格そのものが崩壊する。"),
        ]
        outdir = BANK / "synth_ja"
        for name, text in tests:
            dest = outdir / (name + ".wav")
            print("[synth]", name, text)
            try:
                synth_xtts(text, ref, dest)
            except Exception as exc:
                print("[synth] skip (no XTTS):", exc)
                report["synths"].append({"id": name, "error": str(exc)})
                continue
            x = load_s16(dest)
            st = clip_stats(x)
            reasons = artifacted(st, blob["src_centroid"])
            row = {"id": name, "reasons": reasons, **st}
            report["synths"].append(row)
            print("[synth]", name, "artifacts", reasons or "none")
            if reasons and args.retrain_synth:
                # Second pass: shorter, speech-only mid clips as ref.
                alt = BANK / "maho_ref_ja_b.wav"
                if alt.is_file():
                    dest2 = outdir / (name + "_b.wav")
                    synth_xtts(text, alt, dest2)
                    x2 = load_s16(dest2)
                    st2 = clip_stats(x2)
                    r2 = artifacted(st2, blob["src_centroid"])
                    print("[synth] retry", name, "artifacts", r2 or "none")
                    row["retry_reasons"] = r2
        if any(s.get("reasons") for s in report["synths"] if "error" not in s):
            print("[synth] artifacts remain; keep the equalized corpus and speaker pickle, do not ship one-shot XTTS")
    (BANK / "train_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
