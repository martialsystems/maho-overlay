# Maho chat (Grok subagent)

Standalone chat surface. No overlay window. No local LLM: this machine has 8 GB RAM, so Llama stays off.

Training is a TF-IDF nearest-neighbour fit on SG0 cue→Maho pairs (CPU, small). Runtime in this Grok session: retrieve those pairs, then spawn a `maho` subagent. The child is Grok with her register plus the retrieved lines.

## Train (once, after the SG0 extract)

```bash
backend/.venv/bin/python scripts/build_maho_chat_pairs.py \
  --src ~/Documents/SG0\ Transcript
backend/.venv/bin/python scripts/index_time_travel_physics.py
backend/.venv/bin/python scripts/train_maho_retriever.py
```

Pairs and the pickle stay under gitignored `data/maho_voice/`. The convention opener where Okabe takes her for a middle-schooler is dropped and is not in the fit. Audio chops: wait until they are ready; do not scan for them.

## Talk

In Grok: `/maho-chat` or say you want to talk to Maho. The parent runs `retrieve_maho.py` on your line, then `spawn_subagent` with `subagent_type: maho`. Follow-up turns use `resume_from` on that child.

```bash
backend/.venv/bin/python scripts/retrieve_maho.py \
  --query "how does Amadeus store memory" --k 8
```

SG0 lab talk surfaces `kind: science`. Coffee surfaces `kind: chat`. Real time travel, memory, or Amadeus-as-AI should surface `kind` starting with `notes` from `docs/maho_science.md` (brain science first, GR as a skeptic).

She is 21, Leskinen’s graduate researcher. The user already knows that; she does not introduce the persona. Memory and AI are home turf. Time travel she knows and doubts. Lewd lines get a blush and a snap. Height or childlike-look jokes get `...` until an apology.

Llama / GGUF is a later swap when the box has RAM. Do not load one here.
