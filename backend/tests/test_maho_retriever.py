"""Cue→Maho retriever: science vs chit-chat, no LLM."""
from __future__ import annotations

import json
import pickle
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from build_maho_chat_pairs import build_pairs, is_science  # noqa: E402
from retrieve_maho import retrieve  # noqa: E402
from train_maho_retriever import train  # noqa: E402

FIXTURE = """\
[name]Rintaro[line]“Want some coffee?”[%p]
[name]Maho[line]“Thanks. I’ll take it.”[%p]
[name]Mayuri[line]“How was your morning?”[%p]
[name]Maho[line]“Busy. I slept late.”[%p]
[name]Rintaro[line]“How does Amadeus store cortical memory as digital data?”[%p]
[name]Maho[line]“We map firing patterns onto stored memory traces on the server.”[%p]
[name]Amadeus Maho[line]“I am a copy.”[%p]
[name]Maho[line]“Ignore that.”[%p]
"""


class PairTests(unittest.TestCase):
    def test_pairs_skip_amadeus_and_tag_science(self):
        with tempfile.TemporaryDirectory() as raw:
            src = Path(raw)
            (src / "SG0_X.scx.txt").write_text(FIXTURE, encoding="utf-8")
            rows = build_pairs(src, {})
            cues = [(r["cue"], r["response"], r["kind"]) for r in rows]
            self.assertEqual(
                cues,
                [
                    ("Want some coffee?", "Thanks. I’ll take it.", "chat"),
                    ("How was your morning?", "Busy. I slept late.", "chat"),
                    (
                        "How does Amadeus store cortical memory as digital data?",
                        "We map firing patterns onto stored memory traces on the server.",
                        "science",
                    ),
                ],
            )
            self.assertTrue(is_science("cortical memory digital data"))
            self.assertFalse(is_science("Want some coffee?"))


class TrainRetrieveTests(unittest.TestCase):
    def test_science_and_chat_retrieve(self):
        rows = [
            {
                "id": "a",
                "scene": "s",
                "cue_speaker": "Rintaro",
                "cue": "Want some coffee?",
                "response": "Thanks. I’ll take it.",
                "response_ja": "ありがとう。もらっとく。",
                "kind": "chat",
            },
            {
                "id": "b",
                "scene": "s",
                "cue_speaker": "Mayuri",
                "cue": "How was your morning?",
                "response": "Busy. I slept late.",
                "response_ja": "",
                "kind": "chat",
            },
            {
                "id": "c",
                "scene": "s",
                "cue_speaker": "Rintaro",
                "cue": "How does Amadeus store cortical memory as digital data?",
                "response": "We map firing patterns onto stored memory traces on the server.",
                "response_ja": "",
                "kind": "science",
            },
        ]
        blob = train(rows)
        with tempfile.TemporaryDirectory() as raw:
            model = Path(raw) / "maho_retriever.pkl"
            model.write_bytes(pickle.dumps(blob))
            sci = retrieve("explain digital memory storage in the cortex", k=1, model_path=model)
            chat = retrieve("do you want coffee", k=1, model_path=model)
            self.assertEqual(sci[0]["kind"], "science")
            self.assertIn("server", sci[0]["response"])
            self.assertEqual(chat[0]["kind"], "chat")
            self.assertIn("coffee", chat[0]["cue"].lower())


class SourceContractTests(unittest.TestCase):
    def test_no_llama_in_retriever(self):
        for name in ("train_maho_retriever.py", "retrieve_maho.py", "build_maho_chat_pairs.py"):
            src = (SCRIPTS / name).read_text(encoding="utf-8")
            self.assertNotIn("llama", src.lower())
            self.assertNotIn("demucs", src.lower())

    def test_docs(self):
        docs = (ROOT / "docs" / "maho_chat.md").read_text(encoding="utf-8")
        self.assertNotIn("\u2014", docs)
        self.assertNotIn("What it is not", docs)
        self.assertIn("Grok subagent", docs)


if __name__ == "__main__":
    unittest.main()
