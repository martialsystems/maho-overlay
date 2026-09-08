"""Japanese cat/head reaction lines are paired with live WAVs."""
from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
SCRIPTS = REPO / "scripts"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(SCRIPTS))

JA = re.compile(r"[\u3040-\u30ff\u4e00-\u9fff]")


class ReactionAudioTests(unittest.TestCase):
    def test_cat_and_head_are_japanese_with_wavs(self):
        from chat_interactions import INTERACTION_RESPONSES
        from bake_maho_reactions import reaction_jobs

        jobs = reaction_jobs()
        self.assertEqual(len(jobs), 7)
        named = set()
        for iid in (1, 2):
            variants = INTERACTION_RESPONSES[iid]
            self.assertEqual(len(variants), 4)
            for variant in variants:
                text = variant["text"]
                self.assertTrue(JA.search(text), text)
                self.assertNotIn("kurisu", str(variant["audio_url"]))
                path = ROOT / variant["audio_url"]
                self.assertTrue(path.is_file(), path)
                self.assertEqual(path.read_bytes()[:4], b"RIFF", path)
                named.add(path)
        self.assertEqual(named, {path for path, _text in jobs})
        cat = [v["text"] for v in INTERACTION_RESPONSES[1]]
        head = [v["text"] for v in INTERACTION_RESPONSES[2]]
        self.assertTrue(any("離して" in t for t in cat))
        self.assertTrue(any("良心" in t for t in cat))
        self.assertTrue(any("子供" in t for t in head))
        self.assertTrue(any("馬鹿にしないで" in t for t in head))
        self.assertIn("失礼なことを言わないで。", cat)
        self.assertIn("失礼なことを言わないで。", head)

        blob = (ROOT / "chat_interactions.py").read_text(encoding="utf-8")
        self.assertNotIn("kurisu_", blob)
        self.assertNotIn("Hey!", blob)
        self.assertNotIn("\u2014", blob)
        from bake_maho_reactions import check_jobs

        check_jobs(jobs)

    def test_spectral_match_cuts_hiss(self):
        from bake_maho_reactions import SR, hf_ratio, spectral_match
        import numpy as np

        n = int(0.4 * SR)
        t = np.arange(n, dtype=np.float32) / SR
        clean = (0.2 * np.sin(2 * np.pi * 400 * t)).astype(np.float32)
        hiss = clean + 0.08 * np.random.default_rng(0).standard_normal(n).astype(np.float32)
        out = spectral_match(hiss, clean)
        self.assertLess(hf_ratio(out), hf_ratio(hiss) * 0.85)
        self.assertGreater(float(np.sqrt(np.mean(out * out))), 0.05)

        bake = (SCRIPTS / "bake_maho_reactions.py").read_text(encoding="utf-8")
        self.assertIn("CLEAN_REF_STEMS", bake)
        self.assertIn("temperature", bake)
        self.assertIn("spectral_match", bake)
        self.assertNotIn('EMOTION_CLIPS = ("10", "6", "8", "13", "38")', bake)
        docs = (REPO / "docs" / "maho_voice_bank.md").read_text(encoding="utf-8")
        self.assertNotIn("\u2014", docs)

    def test_xtts_not_loaded_by_check(self):
        src = (SCRIPTS / "bake_maho_reactions.py").read_text(encoding="utf-8")
        self.assertIn("from TTS.api import TTS", src)
        self.assertIn("class XttsJa", src)


if __name__ == "__main__":
    unittest.main()
