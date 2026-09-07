"""Scripted chat replies used when OpenRouter is not in the path."""

import re
from datetime import datetime


def scripted_reply(user_message: str, now: datetime | None = None) -> tuple[str, str]:
    """Return (English UI text, Japanese TTS text) for a local turn."""
    text = (user_message or "").strip()
    lowered = text.lower()
    clock = (now or datetime.now().astimezone()).astimezone()

    if _matches(lowered, ("hello", "hi", "hey", "good morning", "good afternoon", "good evening")):
        english = (
            "Hello. Local Amadeus is running. Live2D, memory, and touch reactions "
            "are up. Chat replies are scripted until an OpenRouter key is saved."
        )
        japanese = "こんにちは。ローカルで起動しています。"
    elif _matches(lowered, ("who are you", "your name", "kurisu", "amadeus", "makise")):
        english = (
            "Amadeus. Makise Kurisu, if you want the lab name. This session is "
            "using scripted replies, so keep the questions short."
        )
        japanese = "アマデウスです。牧瀬紅莉栖、という名前でも呼ばれます。"
    elif _matches(lowered, ("what time", "what is the time", "current time", "what day")):
        english = f"Local clock reads {clock:%H:%M} on {clock:%Y-%m-%d}."
        japanese = f"いまの時刻は{clock:%H:%M}です。"
    elif _matches(lowered, ("help", "what can you do", "how do i", "commands")):
        english = (
            "You can type here, reset memory, edit personality in Settings, and "
            "use the head-pat or special-touch hit areas. Those two play the "
            "prerecorded lines."
        )
        japanese = "会話、記憶のリセット、設定、それに頭なでが使えます。"
    elif not text:
        english = "Say something, even if it is small."
        japanese = "何か言ってください。"
    else:
        english = (
            "Stored. This turn used a local scripted reply. Head pats and the "
            "special touch still play the recorded lines."
        )
        japanese = "覚えました。ローカルの定型返信です。"

    return english, japanese


def _matches(lowered: str, needles: tuple[str, ...]) -> bool:
    for needle in needles:
        if " " in needle:
            if needle in lowered:
                return True
        elif re.search(rf"\b{re.escape(needle)}\b", lowered):
            return True
    return False
