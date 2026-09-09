"""Overlay-matching Japanese viseme curriculum."""
from __future__ import annotations

import json
import pickle
import sys
import tempfile
import unittest
import wave
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

try:
    import numpy as np
except ImportError:
    np = None

try:
    import pykakasi  # noqa: F401

    HAS_KAKASI = True
except ImportError:
    HAS_KAKASI = False

try:
    from sklearn.pipeline import Pipeline

    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False

from ja_vowels import (  # noqa: E402
    OVERLAY_VISEME,
    VOWEL_TO_LABEL,
    mora_vowels_from_kana,
    vowel_labels_from_vowels,
)


def write_sine(path: Path, seconds: float, freq: float, sr: int = 16000, amp: float = 0.25) -> None:
    n = int(seconds * sr)
    t = np.arange(n, dtype=np.float32) / sr
    y = (np.clip(amp * np.sin(2 * np.pi * freq * t), -1, 1) * 32767).astype("<i2")
    with wave.open(str(path), "w") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(y.tobytes())


class VowelMapTests(unittest.TestCase):
    def test_overlay_vowels(self):
        self.assertEqual(VOWEL_TO_LABEL["a"], "open")
        self.assertEqual(VOWEL_TO_LABEL["i"], "half")
        self.assertEqual(VOWEL_TO_LABEL["e"], "half")
        self.assertEqual(VOWEL_TO_LABEL["u"], "small")
        self.assertEqual(VOWEL_TO_LABEL["o"], "open")
        self.assertEqual(VOWEL_TO_LABEL["N"], "closed")
        self.assertEqual(OVERLAY_VISEME["open"], "mouth-open")
        self.assertEqual(OVERLAY_VISEME["half"], "mouth-half")
        self.assertEqual(OVERLAY_VISEME["small"], "mouth-half")
        self.assertEqual(OVERLAY_VISEME["closed"], "mouth-open")

    def test_kana_parser(self):
        self.assertEqual(mora_vowels_from_kana("あいうえおん"), ["a", "i", "u", "e", "o", "N"])
        self.assertEqual(
            vowel_labels_from_vowels(["a", "i", "u", "e", "o", "N"]),
            ["open", "half", "small", "half", "open", "closed"],
        )
        self.assertEqual(mora_vowels_from_kana("きゃ"), ["a"])
        self.assertEqual(mora_vowels_from_kana("しょう"), ["o", "u"])
        self.assertEqual(mora_vowels_from_kana("あー"), ["a", "a"])
        self.assertEqual(mora_vowels_from_kana("マレーシア"), ["a", "e", "e", "i", "a"])

    @unittest.skipUnless(HAS_KAKASI, "pykakasi missing")
    def test_kanji_sentence(self):
        from ja_vowels import vowel_labels

        labels = vowel_labels("水をマレーシアから買わなくてはならないのです。")
        self.assertEqual(
            labels,
            [
                "half",
                "small",
                "open",
                "open",
                "half",
                "half",
                "half",
                "open",
                "open",
                "open",
                "open",
                "open",
                "open",
                "small",
                "half",
                "open",
                "open",
                "open",
                "open",
                "half",
                "open",
                "half",
                "small",
            ],
        )


class PairAndTrainTests(unittest.TestCase):
    @unittest.skipUnless(np is not None and HAS_KAKASI and HAS_SKLEARN, "numpy, pykakasi, or sklearn missing")
    def test_same_labels_one_pool_runtime_no_fit(self):
        from label_ja_vowels import label_pool
        from predict_ja_viseme import predict_track
        from train_ja_viseme import train_pool

        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "normal").mkdir()
            (root / "slow").mkdir()
            text = "あいうえお"
            rows = []
            for i in range(8):
                uid = "utt_{0:02d}".format(i)
                write_sine(root / "normal" / (uid + ".wav"), 0.80, 220 + i * 40)
                write_sine(root / "slow" / (uid + ".wav"), 1.05, 220 + i * 40)
                for speed, rate, folder in (
                    ("normal", 1.0, "normal"),
                    ("slow", 0.7917, "slow"),
                ):
                    rows.append(
                        {
                            "id": uid,
                            "path": "{0}/{1}.wav".format(folder, uid),
                            "speed": speed,
                            "speed_rate": rate,
                            "speaker": "jsut_female",
                            "text": text,
                            "source": "test",
                        }
                    )
            manifest = root / "manifest.jsonl"
            manifest.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
            labels_path = root / "labels.jsonl"
            labeled = label_pool(manifest, root, labels_path)
            self.assertEqual(len(labeled), 16)
            by_id = {}
            by_span = {}
            for row in labeled:
                seq = [m["label"] for m in row["vowels"]]
                by_id.setdefault(row["id"], {})[row["speed"]] = seq
                by_span.setdefault(row["id"], {})[row["speed"]] = row["vowels"][-1]["t1"] - row["vowels"][0]["t0"]
                self.assertEqual(seq, ["open", "half", "small", "half", "open"])
            for uid, speeds in by_id.items():
                self.assertEqual(speeds["slow"], speeds["normal"])
                self.assertGreater(by_span[uid]["slow"], by_span[uid]["normal"])

            model_path = root / "viseme_logreg.pkl"
            summary = train_pool(labels_path, root, model_path, root / "viseme_report.json")
            self.assertEqual(summary["stages"], 1)
            self.assertEqual(summary["n_clips"], 16)
            self.assertIn(summary["chosen"], ("with_rate", "without_rate"))
            hold = set(summary["holdout_id_list"])
            self.assertTrue(hold)
            speeds_by_id = {}
            for row in labeled:
                speeds_by_id.setdefault(row["id"], set()).add(row["speed"])
            for uid in hold:
                self.assertEqual(speeds_by_id[uid], {"slow", "normal"})

            pickle.loads(model_path.read_bytes())
            wav = root / "maho_line.wav"
            write_sine(wav, 0.6, 300)
            with patch.object(Pipeline, "fit", side_effect=AssertionError("runtime must not fit")):
                track = predict_track(wav, model_path, speed_rate=1.0, hop=0.1)
            self.assertTrue(track)
            self.assertIn(track[0]["viseme"], ("mouth-open", "mouth-half"))
            self.assertIn(track[0]["label"], ("open", "half", "small", "closed"))


class SourceContractTests(unittest.TestCase):
    def test_live_talk_stays_rms(self):
        viseme = (ROOT / "frontend" / "src" / "maho" / "viseme.ts").read_text(encoding="utf-8")
        interactions = (ROOT / "frontend" / "src" / "interactions.ts").read_text(encoding="utf-8")
        self.assertIn("Relative RMS", viseme)
        self.assertNotIn("predict_ja_viseme", viseme)
        self.assertNotIn("viseme_logreg", viseme)
        self.assertIn('url: "/maho/head.wav"', interactions)
        self.assertNotIn("talk.wav", interactions)
        self.assertNotIn('label: "Talk"', interactions)

    def test_train_is_one_pool_not_two_stages(self):
        train = (SCRIPTS / "train_ja_viseme.py").read_text(encoding="utf-8")
        predict = (SCRIPTS / "predict_ja_viseme.py").read_text(encoding="utf-8")
        fetch = (SCRIPTS / "fetch_ja_speech.py").read_text(encoding="utf-8")
        self.assertIn("No second stage", train)
        self.assertEqual(train.count("clf.fit("), 1)
        self.assertIn("with_rate", train)
        self.assertNotIn(".fit(", predict)
        self.assertIn("default=1.0", predict)
        self.assertIn("LOCKED_KIDS", fetch)
        self.assertIn("NINJAL CEJC-Child", fetch)
        self.assertNotIn("reaction_audio", fetch)

    def test_docs_and_gitignore(self):
        docs = (ROOT / "docs" / "ja_speech.md").read_text(encoding="utf-8")
        gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
        self.assertNotIn("\u2014", docs)
        self.assertNotIn("\u2013", docs)
        self.assertNotIn("What it is not", docs)
        self.assertIn("SpeedSpeech-JA-2022", docs)
        self.assertIn("speed_rate=1.0", docs)
        self.assertIn("/data/", gitignore)

    def test_kana_table_lengths(self):
        from ja_vowels import _HIRA, _KATA

        self.assertEqual(len(_HIRA), len(_KATA))


if __name__ == "__main__":
    unittest.main()
