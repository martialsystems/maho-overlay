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
```

Writes gitignored `data/maho_voice/bank/` (equalized wavs, manifest, refs, pickle). Do not commit audio.

Current run: 71 clips including 57, speech RMS within 2 dB of median 0.253. Speaker encoder on 63 speech clips. XTTS Japanese synth on the 45 s multi-clip ref still tripped the artifact gate (spectral drift vs the recordings; one retry added dropouts). Those synths are not the bank. The bank is the equalized Japanese corpus plus the encoder pickle and GPT-SoVITS filelist.
