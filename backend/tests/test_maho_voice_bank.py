"""Maho clip script + loudness equalize. No overlay. No Llama."""
from __future__ import annotations

import math
import sys
import tempfile
import unittest
import wave
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from equalize_maho_clips import SR, active_rms, equalize, write_s16  # noqa: E402
from maho_clip_script import LINES, MISSING, NONSPEECH  # noqa: E402


def sine(path: Path, seconds: float, amp: float, freq: float = 220.0) -> None:
    n = int(seconds * SR)
    t = np.arange(n, dtype=np.float32) / SR
    y = (amp * np.sin(2 * np.pi * freq * t)).astype(np.float32)
    write_s16(path, y)


class ScriptTests(unittest.TestCase):
    def test_57_is_disintegrate_and_present(self):
        self.assertEqual(MISSING, frozenset())
        en, ja = LINES["57"]
        self.assertIn("disintegrate", en.lower())
        self.assertIn("崩壊", ja)
        self.assertIn("58", LINES)
        self.assertIn("remove Kurisu", LINES["58"][0])
        self.assertEqual(len([k for k in LINES if k.isdigit()]), 67)
        self.assertTrue(NONSPEECH <= set(LINES))


class EqualizeTests(unittest.TestCase):
    def test_speech_rms_matches_and_pauses_stay_quiet(self):
        with tempfile.TemporaryDirectory() as raw:
            src = Path(raw) / "src"
            dest = Path(raw) / "eq"
            src.mkdir()
            sine(src / "1.wav", 0.4, 0.15)
            sine(src / "2.wav", 0.4, 0.45)
            sine(src / "3.wav", 0.4, 0.30)
            sine(src / "7.wav", 0.4, 0.04)
            report = equalize(src, dest)
            from equalize_maho_clips import load_s16

            a = active_rms(load_s16(dest / "1.wav"))
            b = active_rms(load_s16(dest / "2.wav"))
            c = active_rms(load_s16(dest / "3.wav"))
            q = active_rms(load_s16(dest / "7.wav"))
            med = float(np.median([a, b, c]))
            for r in (a, b, c):
                ratio = max(r / med, med / r)
                self.assertLessEqual(20 * math.log10(ratio), 2.05)
            self.assertLess(q, med * 0.6)
            self.assertEqual(report["n"], 4)
            self.assertEqual(report["missing"], [])


class TrainTests(unittest.TestCase):
    def test_encoder_from_multiple_clips(self):
        from train_maho_voice_bank import train_encoder

        with tempfile.TemporaryDirectory() as raw:
            d = Path(raw)
            sine(d / "a.wav", 0.3, 0.2, 180)
            sine(d / "b.wav", 0.3, 0.2, 240)
            sine(d / "c.wav", 0.3, 0.2, 300)
            blob = train_encoder([d / "a.wav", d / "b.wav", d / "c.wav"])
            self.assertEqual(blob["n_speech"], 3)
            self.assertEqual(blob["lang"], "ja")
            self.assertGreaterEqual(blob["basis"].shape[1], 1)
            self.assertIn("a", blob["embeddings"])


class SourceContractTests(unittest.TestCase):
    def test_no_xtts_single_clip_default(self):
        eq = (SCRIPTS / "equalize_maho_clips.py").read_text(encoding="utf-8")
        self.assertIn("PEAK_LIMIT", eq)
        self.assertNotIn("llama", eq.lower())
        train = (SCRIPTS / "train_maho_voice_bank.py").read_text(encoding="utf-8")
        self.assertIn("multi-clip", train)
        self.assertNotIn("kurisu10s", train)
        docs = (ROOT / "docs" / "maho_voice_bank.md").read_text(encoding="utf-8")
        self.assertNotIn("\u2014", docs)
        self.assertNotIn("What it is not", docs)


if __name__ == "__main__":
    unittest.main()
