#!/usr/bin/env python3
# Copyright (c) 2026 Martial Systems LLC. MIT.
"""Write the Japanese voice-bank manifest and a multi-clip reference WAV.

Amadeus English artifacts came from cloning a single 10 s take. This bank
uses every equalized speech clip as the speaker set.
"""

from __future__ import annotations

import json
import sys
import wave
from pathlib import Path

import numpy as np

SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from equalize_maho_clips import SR, load_s16, write_s16  # noqa: E402
from maho_clip_script import LINES, NONSPEECH  # noqa: E402
from maho_energy_bands import write_bands  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
EQ = ROOT / "data" / "maho_voice" / "bank" / "equalized"
BANK = ROOT / "data" / "maho_voice" / "bank"


def rows() -> list[dict]:
    out = []
    missing_wav = []
    for cid, (en, ja) in LINES.items():
        wav = EQ / (cid + ".wav")
        rec = {
            "id": cid,
            "en": en,
            "ja": ja,
            "wav": str(wav.relative_to(BANK)) if wav.is_file() else "",
            "nonspeech": cid in NONSPEECH,
            "missing_wav": not wav.is_file(),
        }
        if not wav.is_file():
            missing_wav.append(cid)
        out.append(rec)
    if missing_wav:
        raise SystemExit("missing equalized wavs: {0}".format(missing_wav))
    return out


def concat_speech(dest: Path, max_seconds: float = 45.0, reverse: bool = False) -> Path:
    speech = []
    for cid, (_en, _ja) in LINES.items():
        if cid in NONSPEECH:
            continue
        path = EQ / (cid + ".wav")
        if path.is_file():
            speech.append((cid, load_s16(path)))
    speech.sort(key=lambda kv: -kv[1].size)
    if reverse:
        speech.reverse()
    chunks = []
    n = 0
    cap = int(max_seconds * SR)
    for _cid, x in speech:
        if n >= cap:
            break
        chunks.append(x)
        n += x.size
        chunks.append(np.zeros(int(0.08 * SR), dtype=np.float32))
        n += int(0.08 * SR)
    write_s16(dest, np.concatenate(chunks) if chunks else np.zeros(SR, dtype=np.float32))
    return dest


def main() -> int:
    recs = rows()
    BANK.mkdir(parents=True, exist_ok=True)
    man = BANK / "manifest.jsonl"
    man.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in recs), encoding="utf-8")
    # GPT-SoVITS style: wav|speaker|lang|text
    filelist = []
    for r in recs:
        if r["nonspeech"]:
            continue
        wav = BANK / r["wav"]
        filelist.append("{0}|maho|ja|{1}".format(wav, r["ja"]))
    (BANK / "filelist_ja.txt").write_text("\n".join(filelist) + "\n", encoding="utf-8")
    ref = concat_speech(BANK / "maho_ref_ja.wav")
    concat_speech(BANK / "maho_ref_ja_b.wav", reverse=True)
    bands = write_bands(EQ, BANK)
    by_id = {r["id"]: r for r in recs}
    for band_name in ("loud", "quiet"):
        lines = []
        for cid in bands[band_name]:
            r = by_id.get(cid)
            if not r or r["nonspeech"] or not r["wav"]:
                continue
            lines.append("{0}|maho_{1}|ja|{2}".format(BANK / r["wav"], band_name, r["ja"]))
        (BANK / "filelist_ja_{0}.txt".format(band_name)).write_text("\n".join(lines) + "\n", encoding="utf-8")
    loud_n = len(bands["loud"])
    quiet_n = len(bands["quiet"])
    with wave.open(str(ref), "rb") as w:
        dur = w.getnframes() / float(w.getframerate())
    print(
        "manifest {0} speech {1} ref {2:.1f}s loud {3} quiet {4} -> {5}".format(
            len(recs),
            sum(1 for r in recs if not r["nonspeech"]),
            dur,
            loud_n,
            quiet_n,
            man,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
