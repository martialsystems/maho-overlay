#!/usr/bin/env python3
# Copyright (c) 2026 Martial Systems LLC. MIT.
"""Japanese mora vowels to overlay viseme labels.

あ open, い/え half, う small, お open. ん closed. Runtime overlay currently
maps small to mouth-half until a small mouth frame exists. closed maps to
mouth-open while speaking (same contract as MouthDriver silence-during-speech).
"""

from __future__ import annotations

from typing import List

try:
    import pykakasi
except ImportError:  # pragma: no cover
    pykakasi = None

_KKS = pykakasi.kakasi() if pykakasi is not None else None

# Gojuon + dakuten/handakuten: character -> nucleus vowel or N.
_KANA_VOWEL: dict[str, str] = {}
for _row, _v in (
    ("あかさたなはまやらわがざだばぱぁゃゎ", "a"),
    ("いきしちにひみりぎじぢびぴぃゐ", "i"),
    ("うくすつぬふむゆるぐずづぶぷぅゅゔ", "u"),
    ("えけせてねへめれげぜでべぺぇゑ", "e"),
    ("おこそとのほもよろをごぞどぼぽぉょ", "o"),
):
    for _ch in _row:
        _KANA_VOWEL[_ch] = _v
_KANA_VOWEL["ん"] = "N"
_KANA_VOWEL["を"] = "o"

_YOON = {"ゃ": "a", "ゅ": "u", "ょ": "o"}
_SKIP = set("。、・「」『』（）()！？!? 　\n\t.,;:[]{}…―")

_HIRA = (
    "ぁあぃいぅうぇえぉおかがきぎくぐけげこごさざしじすずせぜそぞ"
    "ただちぢっつづてでとどなにぬねのはばぱひびぴふぶぷへべぺほぼぽ"
    "まみむめもゃやゅゆょよらりるれろゎわゐゑをんゔゝゞー"
)
_KATA = (
    "ァアィイゥウェエォオカガキギクグケゲコゴサザシジスズセゼソゾ"
    "タダチヂッツヅテデトドナニヌネノハバパヒビピフブプヘベペホボポ"
    "マミムメモャヤュユョヨラリルレロヮワヰヱヲンヴヽヾー"
)
KATA_TO_HIRA = str.maketrans(_KATA, _HIRA)

# Training labels. Overlay runtime: small -> half until that PNG exists.
VOWEL_TO_LABEL = {
    "a": "open",
    "o": "open",
    "i": "half",
    "e": "half",
    "u": "small",
    "N": "closed",
}

OVERLAY_VISEME = {
    "open": "mouth-open",
    "half": "mouth-half",
    "small": "mouth-half",
    "closed": "mouth-open",
}


def to_hiragana(text: str) -> str:
    if _KKS is None:
        raise SystemExit("pykakasi is required for kanji text")
    parts = _KKS.convert(text)
    return "".join(p.get("hira") or p.get("orig") or "" for p in parts)


def mora_vowels_from_kana(kana: str) -> List[str]:
    hira = kana.translate(KATA_TO_HIRA)
    vowels: List[str] = []
    i = 0
    while i < len(hira):
        ch = hira[i]
        if ch in _SKIP:
            i += 1
            continue
        if ch == "ー":
            if vowels:
                vowels.append(vowels[-1])
            i += 1
            continue
        if ch == "っ":
            i += 1
            continue
        if i + 1 < len(hira) and hira[i + 1] in _YOON:
            vowels.append(_YOON[hira[i + 1]])
            i += 2
            continue
        v = _KANA_VOWEL.get(ch)
        if v:
            vowels.append(v)
        i += 1
    return vowels


def mora_vowels(text: str) -> List[str]:
    return mora_vowels_from_kana(to_hiragana(text))


def vowel_labels_from_vowels(vowels: List[str]) -> List[str]:
    return [VOWEL_TO_LABEL[v] for v in vowels]


def vowel_labels(text: str) -> List[str]:
    return vowel_labels_from_vowels(mora_vowels(text))


def overlay_visemes(text: str) -> List[str]:
    return [OVERLAY_VISEME[lab] for lab in vowel_labels(text)]
