"""SG0 Maho transcript compile: solo EN extract, JA map, register."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from compile_sg0_maho import attach_ja, extract_en  # noqa: E402
from maho_ja_style import FORBIDDEN_JA, NAME_JA, ja_register_flags  # noqa: E402


FIXTURE = """\
[name]Mayuri[line]“Maho, have some coffee.”[%p]
[name]Maho[line]“Thanks. I’ll take it.”[%p]
[name]Maho[line]“Okabe, wait.”[%p]
[name]Maho[line](Am I sad about leaving?)[%p]
[name]Maho[line]“...”[%p]
[name]Amadeus Maho[line]“I am a copy.”[%p]
[name]Rintaro&Maho[line]“Together!”[%p]
[name]Rintaro[line]“Hiyajo?”[%p]
"""


class ExtractTests(unittest.TestCase):
    def test_solo_maho_only(self):
        with tempfile.TemporaryDirectory() as raw:
            src = Path(raw)
            (src / "SG0_M01_01.scx.txt").write_text(FIXTURE, encoding="utf-8")
            rows = extract_en(src)
            texts = [r["text"] for r in rows]
            self.assertEqual(
                texts,
                ["Thanks. I’ll take it.", "Okabe, wait.", "Am I sad about leaving?", "..."],
            )
            self.assertEqual(rows[2]["kind"], "thought")
            self.assertEqual(rows[0]["kind"], "spoken")
            self.assertTrue(all(r["speaker"] == "maho" for r in rows))
            joined = " ".join(texts)
            self.assertNotIn("I am a copy", joined)
            self.assertNotIn("Together!", joined)
            self.assertNotIn("have some coffee", joined)

    def test_ja_map_and_ellipsis(self):
        with tempfile.TemporaryDirectory() as raw:
            src = Path(raw)
            (src / "SG0_X.scx.txt").write_text(FIXTURE, encoding="utf-8")
            en = extract_en(src)
            ja_map = {
                "Thanks. I’ll take it.": "ありがとう。もらっとく。",
                "Okabe, wait.": "岡部、待って。",
                "Am I sad about leaving?": "日本を離れるのが寂しいのか？",
            }
            ja_rows, missing, bad = attach_ja(en, ja_map)
            self.assertEqual(missing, 0)
            self.assertEqual(bad, 0)
            by_en = {r["en_text"]: r["text"] for r in ja_rows}
            self.assertEqual(by_en["..."], "……")
            self.assertEqual(by_en["Okabe, wait."], "岡部、待って。")
            self.assertEqual(ja_rows[0]["lang"], "ja")

    def test_register_rejects_cute_and_male(self):
        self.assertTrue(ja_register_flags("あたしは真帆"))
        self.assertTrue(ja_register_flags("俺は研究者だ"))
        self.assertTrue(ja_register_flags("よろしいですわ"))
        self.assertFalse(ja_register_flags("私は比屋定真帆。岡部、待って。"))
        self.assertEqual(NAME_JA["Okabe"], "岡部")
        self.assertIn("あたし", FORBIDDEN_JA)


class SourceContractTests(unittest.TestCase):
    def test_compiler_does_not_train_or_extract_audio(self):
        compile_src = (SCRIPTS / "compile_sg0_maho.py").read_text(encoding="utf-8")
        self.assertIn("Does not extract audio", compile_src)
        self.assertIn("Does not train", compile_src)
        self.assertNotIn("demucs", compile_src)
        self.assertNotIn("clf.fit", compile_src)

    def test_docs(self):
        docs = (ROOT / "docs" / "maho_voice.md").read_text(encoding="utf-8")
        self.assertNotIn("\u2014", docs)
        self.assertNotIn("\u2013", docs)
        self.assertNotIn("What it is not", docs)
        self.assertIn("English", docs)
        self.assertIn("Japanese", docs)


if __name__ == "__main__":
    unittest.main()
