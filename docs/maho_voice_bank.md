# Maho Japanese voice bank

Source: `~/Documents/maho_clips` plus `script.rtf`. Japanese audio only. English in the rtf is the cue sheet. Note on the rtf: she is talking to Okabe (岡部さん), serious register, `……` interchangeable.

Clip 57 is the personality-disintegrate line. Equalize first, then train.

Amadeus English was a single 10 s XTTS clone and picked up artifacts. After equalize, clips split into loud and quiet banks by punch (p90 / median of voiced frames). Clip 10, the kid-call take, is forced loud. Each band gets its own reference WAV, filelist, and speaker encoder. Overlay cat/head lines clone the loud bank only.

```bash
backend/.venv/bin/python scripts/equalize_maho_clips.py
backend/.venv/bin/python scripts/equalize_maho_clips.py --check
backend/.venv/bin/python scripts/build_maho_voice_dataset.py
backend/.venv/bin/python scripts/train_maho_voice_bank.py
# optional XTTS ja check (needs Coqui):
backend/.venv/bin/python scripts/train_maho_voice_bank.py --synth --retrain-synth
# cat/head overlay lines (clip 10 is copied; other lines need Coqui):
.venv-xtts/bin/python scripts/bake_maho_reactions.py --synth
backend/.venv/bin/python scripts/bake_maho_reactions.py --check
```

Writes gitignored `data/maho_voice/bank/` (equalized wavs, manifest, refs, pickle). Do not commit that bank. Overlay cat/head lines go in `backend/assets/reaction_audio/` and are committed.

Current run: 71 clips including 57, speech RMS within 2 dB of median 0.253. Two banks after that: loud (clip 10 first) and quiet (even lecture takes). Overlay clicks synth from loud refs as one utterance, with mid-line holes joined, then a 4 kHz shelf toward clip 10. Clip 10 itself is copied, not cloned.
