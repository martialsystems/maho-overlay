"""Reaction audio layout: Japanese originals archived, live files are WAV."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class EnglishAudioTests(unittest.TestCase):
    def test_japanese_originals_archived_and_live_wavs_exist(self):
        import sys
        sys.path.insert(0, str(ROOT))
        from chat_interactions import INTERACTION_RESPONSES
        from scripts.bake_english_voice import reaction_jobs, spoken_text

        jobs = reaction_jobs()
        self.assertGreaterEqual(len(jobs), 20)
        for path, text in jobs:
            self.assertTrue(text, path)
            self.assertNotIn("“", spoken_text("“Mm… this isn’t bad.”"))
            live = path.read_bytes()[:12]
            archive = (ROOT / "assets" / "reaction_audio" / "ja" / path.name).read_bytes()[:12]
            self.assertEqual(live[:4], b"RIFF", path)
            self.assertEqual(archive[:4], b"RIFF", path.name)

        named = {
            ROOT / variant["audio_url"]
            for variants in INTERACTION_RESPONSES.values()
            for variant in variants
            if variant.get("audio_url")
        }
        self.assertEqual(named, {path for path, _text in jobs})


if __name__ == "__main__":
    unittest.main()
