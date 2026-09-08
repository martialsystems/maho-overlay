#!/usr/bin/env python3
# Copyright (c) 2026 Martial Systems LLC. MIT.
"""Hiyajou Maho Japanese register for EN→JA script translation.

Names and forbidden patterns only. Full line translations stay in gitignored
data. Reverse-check: JA back to EN must keep meaning and this register.
"""

from __future__ import annotations

import re

# Official EN loc names → how Maho addresses them in Japanese.
NAME_JA = {
    "Okabe": "岡部",
    "Okarin": "オカリン",
    "Rintaro": "倫太郎",
    "Kurisu": "クリス",
    "Makise": "牧瀬",
    "Christina": "クリスティーナ",
    "Daru": "ダル",
    "Hashida": "橋田",
    "Itaru": "至",
    "Mayuri": "まゆり",
    "Suzuha": "鈴羽",
    "Suzu": "鈴",
    "Kagari": "かがり",
    "Leskinen": "レスキネン",
    "Reyes": "レイエス",
    "Moeka": "萌郁",
    "Kiryu": "桐生",
    "Amadeus": "アマデウス",
    "Faris": "フェイリス",
    "Luka": "ルカ",
    "Lukako": "ルカ子",
    "Fubuki": "フブキ",
    "Kaede": "カエデ",
    "Nae": "なえ",
    "Tennouji": "天王寺",
    "Yuki": "由季",
    "Hiyajo": "比屋定",
    "Maho": "真帆",
}

# JA that is not Maho (cutesy, male, ojousama). Reverse-check fails on these.
FORBIDDEN_JA = (
    "あたし",
    "あたい",
    "俺",
    "僕",
    "わたくし",
    "ですわ",
    "だわよ",
    "かしら",
    "のよん",
    "にゃ",
    "オカリンくん",
)

# First person she uses.
SELF_JA = "私"


def apply_names_en_to_ja(text: str) -> str:
    out = text
    for en, ja in sorted(NAME_JA.items(), key=lambda kv: -len(kv[0])):
        out = re.sub(r"\b" + re.escape(en) + r"\b", ja, out)
    return out


def ja_register_flags(ja: str) -> list[str]:
    hits = [tok for tok in FORBIDDEN_JA if tok in ja]
    if "私" not in ja and re.search(r"(あたし|俺|僕)", ja):
        hits.append("wrong_first_person")
    return hits


def is_ellipsis(text: str) -> bool:
    stripped = re.sub(r"[.\s…・\-—–\(\)（）「」『』]", "", text)
    return stripped == ""


def ellipsis_ja(text: str) -> str:
    if "…" in text or "..." in text or ".." in text:
        return "……"
    return "……"
