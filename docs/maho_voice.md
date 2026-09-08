# Maho voice corpus

Local compile of Hiyajou Maho speech for a later voice model and for Japanese viseme labels. Live Talk is still MouthDriver RMS on `talk.wav`.

## Audio chops

About 45 clips, mixed length, from the Part 23 English scene. Maho only. Drop them in `~/Documents/maho_clips` with a matching `.txt` per file. Vocal isolation (Demucs) runs after those files exist. Do not isolate the 27-minute two-speaker mix.

## SG0 transcript (English pack, then Japanese)

Source: `~/Documents/SG0 Transcript` (104 `.scx.txt` files).

1. Extract solo `[name]Maho` lines. Skip Amadeus Maho and joint speakers.
2. Spoken vs thought. Thoughts are parenthetical in the dump; they stay tagged.
3. After the English extract is finished, fill Japanese from an EN→JA map in Maho’s register.
4. Reverse-check: translate a JA sample back to English and compare to the original line. Names and first person have to match her pattern (私, 岡部, クリス), not あたし or ですわ.

```bash
backend/.venv/bin/python scripts/compile_sg0_maho.py \
  --src ~/Documents/SG0\ Transcript
```

Writes gitignored `data/maho_voice/sg0_maho_en.jsonl` and `sg0_maho_ja.jsonl`. The game text does not go in git.

Current extract from the 104-file pack: 2,627 solo Maho lines (2,584 spoken, 43 thought), 2,273 unique English strings. Japanese filled 2,627/2,627. Register scan: no あたし, 俺, ですわ, かしら. Reverse-check sample (campus line, coffee take, phone ID, Amadeus, Okarin thanks) keeps meaning; the campus JA follows her canon 寝ぼける wording rather than the looser English loc.

Japanese viseme labels (あ open, い/え half, う small, お open) apply to the JA spoken rows. English chops clone the voice. Do not fine-tune the slow+normal viseme pool as a second stage.

## How to run

```bash
backend/.venv/bin/python -m unittest backend.tests.test_sg0_maho backend.tests.test_ja_viseme
backend/.venv/bin/python scripts/compile_sg0_maho.py --src ~/Documents/SG0\ Transcript
```
