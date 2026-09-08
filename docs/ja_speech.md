# Japanese speech pool (slow + normal)

Curriculum that matches the overlay mouth set.

## Labels

Japanese vowels on the slow set:

| vowel | training label | overlay viseme |
|-------|----------------|----------------|
| あ | open | mouth-open |
| い | half | mouth-half |
| え | half | mouth-half |
| う | small | mouth-half (until a small PNG exists) |
| お | open | mouth-open |
| ん | closed | mouth-open while speaking |

The closed overlay mapping is the same contract as MouthDriver silence during a line: keep the mouth open until the clip ends.

## Pair

The vowel sequence is taken from the slow take's text. The paired normal take of that sentence gets the same label sequence. Times are scaled per clip after an RMS trim. Labels are not re-derived on the normal take.

## Train

One model on the pool. Two classifiers are fit from scratch on the same rows (with and without `speed_rate`). The holdout winner is kept. Holdout is by utterance id, both speeds together.

That is model selection, not a second stage. Do not fine-tune a slow model on normal takes. Sequential Child then Adult wipes the slow weights.

Runtime always passes `speed_rate=1.0` (Maho's normal line). If the winner used the rate feature, that value is the condition. If the two speeds did not confuse the holdout, the feature is dropped.

## Runtime

```bash
backend/.venv/bin/python scripts/predict_ja_viseme.py \
  --wav frontend/public/maho/talk.wav \
  --speed-rate 1.0
```

Predict only. No `fit`. The current Talk line is English (`talk.wav`, staff room). Live overlay Talk still uses MouthDriver relative RMS. Wire this track when a Japanese Maho line exists.

## Data

SpeedSpeech-JA-2022 female `03_slow` (3.8 mora/s) plus `01_normal` (4.8 mora/s) is the paired set this architecture is built for. Same 324 ITA sentences at two true rates, CC BY 4.0. NICT currently serves an HTML maintenance page, not the zip.

Until that zip unpacks into `data/ja_speech/speedspeech/female/{01_normal,03_slow}/`, the pool is JSUT BASIC5000 (first parquet shard, 400 utterances) with `atempo=3.8/4.8` slow copies. That stretch is a rate pair, not SlowSpeech articulation.

| speed | mora/s | `speed_rate` | source |
|-------|--------|--------------|--------|
| slow | 3.8 | 0.792 | SpeedSpeech female `03_slow` when present; else JSUT atempo |
| normal | 4.8 | 1.0 | SpeedSpeech female `01_normal` when present; else JSUT as recorded |

Amadeus Overlay's 21 JA reaction clips are extra style. They are not the rate pair and they stay out of this pool.

NINJAL CEJC-Child, ELRA Japanese Kids Speech, and NTT INFANT stay locked. This fetch does not download them.

Audio lives under `data/ja_speech/` (gitignored). Do not commit wavs, parquet, labels, or the pickle.

## Current results (JSUT atempo, 400 pairs)

800 labeled clips, 0 label-sequence mismatches between slow and normal. First sentence (`BASIC5000_0001`) is 23 mora; slow speech span 0.3787 to 3.4293 s, normal 0.304 to 2.72 s.

Holdout (60 utterance ids, both speeds): without `speed_rate` macro-F1 0.2487, with `speed_rate` macro-F1 0.2488. Winner: with_rate, one stage. The two speeds barely separate on stretched JSUT, which is why SpeedSpeech's true slow takes are the swap-in.

## How to run

```bash
backend/.venv/bin/pip install -r scripts/requirements-ja-speech.txt
backend/.venv/bin/python scripts/fetch_ja_speech.py
backend/.venv/bin/python scripts/label_ja_vowels.py
backend/.venv/bin/python scripts/train_ja_viseme.py
backend/.venv/bin/python scripts/predict_ja_viseme.py --wav frontend/public/maho/talk.wav --speed-rate 1.0
```

Cite the corpus you actually unpacked. JSUT is research/non-commercial. SpeedSpeech-JA-2022 is CC BY 4.0.
