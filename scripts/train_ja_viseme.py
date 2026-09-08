#!/usr/bin/env python3
# Copyright (c) 2026 Martial Systems LLC. MIT.
"""Train one viseme classifier on the pooled slow+normal labels.

No second stage. Two models are fit from scratch on the same pool (with and
without speed_rate). The holdout winner is kept. That is model selection, not
fine-tune. Hold out is by utterance id (both speeds together).
"""

from __future__ import annotations

import json
import pickle
import wave
from collections import Counter
from pathlib import Path

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, f1_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "ja_speech"
LABELS = DATA / "labels.jsonl"
MODEL = DATA / "viseme_logreg.pkl"
REPORT = DATA / "viseme_report.json"

LABEL_INDEX = {"closed": 0, "small": 1, "half": 2, "open": 3}
INDEX_LABEL = {v: k for k, v in LABEL_INDEX.items()}
N_SPEC = 16


def load_wav(path: Path) -> tuple[int, np.ndarray]:
    with wave.open(str(path), "rb") as w:
        nch, sw, sr, n = w.getnchannels(), w.getsampwidth(), w.getframerate(), w.getnframes()
        raw = w.readframes(n)
    if sw != 2:
        raise SystemExit("{0}: need 16-bit PCM, got sampwidth={1}".format(path, sw))
    samples = np.frombuffer(raw, dtype="<i2").astype(np.float32) / 32768.0
    if nch == 2:
        samples = samples[0::2]
    return sr, samples


def log_spec(window: np.ndarray, n_fft: int = 512, bins: int = N_SPEC) -> np.ndarray:
    if window.size < 8:
        return np.zeros(bins, dtype=np.float32)
    w = np.hanning(window.size) * window
    spec = np.abs(np.fft.rfft(w, n=n_fft)) + 1e-6
    logp = np.log(spec)
    edges = np.linspace(0, logp.size, bins + 1).astype(int)
    out = np.zeros(bins, dtype=np.float32)
    for i in range(bins):
        a, b = edges[i], max(edges[i] + 1, edges[i + 1])
        out[i] = float(logp[a:b].mean())
    return out


def features_from_samples(
    samples: np.ndarray, sr: int, t0: float, t1: float, speed_rate: float | None
) -> np.ndarray:
    a = int(t0 * sr)
    b = max(a + 1, int(t1 * sr))
    chunk = samples[a:b]
    spec = log_spec(chunk)
    rms = float(np.sqrt(np.mean(chunk * chunk))) if chunk.size else 0.0
    extra = [rms] if speed_rate is None else [rms, float(speed_rate)]
    return np.concatenate([spec, extra]).astype(np.float32)


def features_for(
    path: Path,
    t0: float,
    t1: float,
    speed_rate: float,
    cache: dict[Path, tuple[int, np.ndarray]] | None = None,
    with_rate: bool = True,
) -> np.ndarray:
    if cache is not None and path in cache:
        sr, samples = cache[path]
    else:
        sr, samples = load_wav(path)
        if cache is not None:
            cache[path] = (sr, samples)
    return features_from_samples(samples, sr, t0, t1, speed_rate if with_rate else None)


def _new_clf() -> Pipeline:
    return Pipeline(
        [
            ("scale", StandardScaler()),
            (
                "lr",
                LogisticRegression(
                    max_iter=800,
                    class_weight="balanced",
                    solver="lbfgs",
                ),
            ),
        ]
    )


def _split_ids(ids: list[str]) -> set[str]:
    if len(ids) < 2:
        raise SystemExit("need at least 2 utterance ids for a holdout")
    rng = np.random.default_rng(0)
    order = list(ids)
    rng.shuffle(order)
    cut = max(1, int(len(order) * 0.15))
    if cut >= len(order):
        cut = 1
    return set(order[:cut])


def _xy_with_rate(
    rows: list[dict], data_root: Path, hold: set[str]
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    x_train, y_train, x_test, y_test = [], [], [], []
    for row in rows:
        path = data_root / row["path"]
        sr, samples = load_wav(path)
        rate = float(row["speed_rate"])
        bucket_x = x_test if row["id"] in hold else x_train
        bucket_y = y_test if row["id"] in hold else y_train
        for mora in row["vowels"]:
            bucket_x.append(features_from_samples(samples, sr, mora["t0"], mora["t1"], rate))
            bucket_y.append(LABEL_INDEX[mora["label"]])
    return (
        np.stack(x_train),
        np.array(y_train),
        np.stack(x_test),
        np.array(y_test),
    )


def train_pool(labels_path: Path, data_root: Path, model_path: Path, report_path: Path | None = None) -> dict:
    rows = [json.loads(line) for line in labels_path.read_text(encoding="utf-8").splitlines() if line]
    if not rows:
        raise SystemExit("no labels")
    ids = sorted({r["id"] for r in rows})
    hold = _split_ids(ids)
    x_train_r, y_train, x_test_r, y_test = _xy_with_rate(rows, data_root, hold)
    reports = {}
    models = {}
    for with_rate in (False, True):
        x_train = x_train_r if with_rate else x_train_r[:, :-1]
        x_test = x_test_r if with_rate else x_test_r[:, :-1]
        clf = _new_clf()
        clf.fit(x_train, y_train)
        pred = clf.predict(x_test)
        f1 = float(f1_score(y_test, pred, labels=list(range(4)), average="macro", zero_division=0))
        text = classification_report(
            y_test,
            pred,
            labels=list(range(4)),
            target_names=[INDEX_LABEL[i] for i in range(4)],
            zero_division=0,
        )
        key = "with_rate" if with_rate else "without_rate"
        reports[key] = {"macro_f1": f1, "report": text, "train": dict(Counter(y_train.tolist()))}
        models[key] = clf
        print(key, "macro_f1", round(f1, 4))
        print(text)

    # Condition on rate when it helps or ties. Runtime always wants to pass 1.0.
    chosen = "with_rate" if reports["with_rate"]["macro_f1"] >= reports["without_rate"]["macro_f1"] else "without_rate"
    blob = {
        "clf": models[chosen],
        "labels": INDEX_LABEL,
        "with_rate": chosen == "with_rate",
        "chosen": chosen,
        "stages": 1,
    }
    model_path.parent.mkdir(parents=True, exist_ok=True)
    model_path.write_bytes(pickle.dumps(blob))
    summary = {
        "chosen": chosen,
        "with_rate": chosen == "with_rate",
        "stages": 1,
        "n_ids": len(ids),
        "n_clips": len(rows),
        "holdout_ids": len(hold),
        "holdout_id_list": sorted(hold),
        "without_rate_macro_f1": reports["without_rate"]["macro_f1"],
        "with_rate_macro_f1": reports["with_rate"]["macro_f1"],
        "without_rate_report": reports["without_rate"]["report"],
        "with_rate_report": reports["with_rate"]["report"],
        "source": rows[0].get("source", ""),
    }
    if report_path is not None:
        report_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print("chose", chosen, "stages 1; wrote", model_path)
    return summary


def main() -> None:
    train_pool(LABELS, DATA, MODEL, REPORT)


if __name__ == "__main__":
    main()
