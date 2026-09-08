# ---------- SPECIAL INTERACTIONS ----------

INTERACTION_EVENTS = {
    1: "[Interaction event: The user touched your chest.]",
    2: "[Interaction event: The user patted your head.]",
    3: "[Interaction event: The user tapped your arm.]",
}

# Japanese overlay copy. Cat (1) and head (2) share 失礼なことを言わないで。
INTERACTION_RESPONSES = {
    1: [
        {"text": "やめて！離してってば！", "audio_url": "assets/reaction_audio/maho_cat_1.wav"},
        {"text": "失礼なことを言わないで。", "audio_url": "assets/reaction_audio/maho_rude.wav"},
        {"text": "私有地侵害で訴えてあげようか。", "audio_url": "assets/reaction_audio/maho_cat_3.wav"},
        {"text": "良心ってものはないの！？", "audio_url": "assets/reaction_audio/maho_cat_4.wav"},
    ],
    2: [
        {"text": "失礼なことを言わないで。", "audio_url": "assets/reaction_audio/maho_rude.wav"},
        {"text": "やめて。子供じゃないんだから。", "audio_url": "assets/reaction_audio/maho_head_2.wav"},
        {"text": "侮辱されてる気がします。", "audio_url": "assets/reaction_audio/maho_head_3.wav"},
        {"text": "馬鹿にしないで。本気なんだから。", "audio_url": "assets/reaction_audio/maho_head_4.wav"},
    ],
    3: [
        {"text": "名前を呼べばいいでしょう。", "audio_url": None},
        {"text": "ちょっと、ここにいるんだけど。", "audio_url": None},
        {"text": "なに？", "audio_url": None},
    ],
}
