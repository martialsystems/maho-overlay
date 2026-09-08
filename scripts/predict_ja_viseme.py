#!/usr/bin/env python3
# Copyright (c) 2026 Martial Systems LLC. MIT.
"""Run the pooled viseme model on a normal-rate clip (Maho's line).

Does not fine-tune. Does not call fit. speed_rate defaults to 1.0 (normal).
"""

from __future__ import annotations

import argparse
import json
import pickle
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from ja_vowels import OVERLAY_VISEME  # noqa: E402
from train_ja_viseme import features_for, load_wav  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "ja_speech"
MODEL = DATA / "viseme_logreg.pkl"


def predict_track(wav: Path, model_path: Path, speed_rate: float = 1.0, hop: float = 0.05) -> list[dict]:
    blob = pickle.loads(model_path.read_bytes())
    clf = blob["clf"]
    labels = blob["labels"]
    with_rate = bool(blob.get("with_rate", True))
    sr, samples = load_wav(wav)
    dur = samples.size / float(sr)
    cache = {wav: (sr, samples)}
    track: list[dict] = []
    t = 0.0
    last = ""
    while t < dur:
        t1 = min(dur, t + hop)
        feat = features_for(wav, t, t1, speed_rate, cache=cache, with_rate=with_rate)
        idx = int(clf.predict(feat.reshape(1, -1))[0])
        lab = labels[idx]
        vis = OVERLAY_VISEME[lab]
        if vis != last or not track:
            track.append({"t": round(t, 4), "label": lab, "viseme": vis})
            last = vis
        t = t1
    return track


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--wav", required=True)
    p.add_argument("--speed-rate", type=float, default=1.0)
    p.add_argument("--hop", type=float, default=0.05)
    p.add_argument("--out", default="")
    p.add_argument("--model", default=str(MODEL))
    args = p.parse_args()
    wav = Path(args.wav)
    model_path = Path(args.model)
    track = predict_track(wav, model_path, speed_rate=args.speed_rate, hop=args.hop)
    out = Path(args.out) if args.out else DATA / (wav.stem + "_visemes.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(track, ensure_ascii=False, indent=2), encoding="utf-8")
    print("wrote", out, "n", len(track), "speed_rate", args.speed_rate)


if __name__ == "__main__":
    main()
