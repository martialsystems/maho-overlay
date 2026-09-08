# Maho Japanese voice bank

Source: `~/Documents/maho_clips` plus `script.rtf`. Japanese audio only. English in the rtf is the cue sheet. Note on the rtf: she is talking to Okabe (岡部さん), serious register, `……` interchangeable.

Clip 57 is the personality-disintegrate line. Equalize first, then train.

Amadeus English was a single 10 s XTTS clone and picked up artifacts. This bank fits a speaker encoder on every equalized speech clip and conditions synth on a 45 s multi-clip reference. A second reference mix is used if the first synth fails the artifact gate (clipping, dropouts, spectral drift).

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

Current run: 71 clips including 57, speech RMS within 2 dB of median 0.253. Speaker encoder on 63 speech clips. Overlay cat/head synths clone from the cleanest recorded takes (clips 2, 8, 10, 11, 18, 51, 64) at low XTTS temperature, then match clip 10's spectrum so vocoder hiss stays down. Clip 10 itself is copied, not cloned. The bank pickle is still the equalized Japanese corpus, not a one-shot 10 s clone.
