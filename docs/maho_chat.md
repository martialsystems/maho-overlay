# Maho chat (Grok subagent)

Standalone chat surface. No overlay window. No local LLM: this machine has 8 GB RAM, so Llama stays off.

Training is a TF-IDF nearest-neighbour fit on SG0 cue→Maho pairs (CPU, small). Runtime in this Grok session: retrieve those pairs, then spawn a `maho` subagent. The child is Grok with her register plus the retrieved lines.

## Train (once, after the SG0 extract)

```bash
backend/.venv/bin/python scripts/build_maho_chat_pairs.py \
  --src ~/Documents/SG0\ Transcript
backend/.venv/bin/python scripts/train_maho_retriever.py
```

Pairs and the pickle stay under gitignored `data/maho_voice/`. Current fit: 1,366 pairs (328 science, 1,038 chat).

## Talk

In Grok: `/maho-chat` or say you want to talk to Maho. The parent runs `retrieve_maho.py` on your line, then `spawn_subagent` with `subagent_type: maho`. Follow-up turns use `resume_from` on that child.

```bash
backend/.venv/bin/python scripts/retrieve_maho.py \
  --query "how does Amadeus store memory" --k 8
```

Science questions should surface `kind: science` pairs. Coffee and small talk should surface `kind: chat`.

Llama / GGUF is a later swap when the box has RAM. Do not load one here.
