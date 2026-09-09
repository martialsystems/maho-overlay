# maho-overlay

<p align="right">
  <a href="https://ko-fi.com/martialgames"><img src="https://img.shields.io/badge/Donate-Ko--fi-ff5e5b?style=flat-square&logo=ko-fi&logoColor=white" alt="Donate on Ko-fi" /></a>
</p>

Maho sits on your desktop. Click the cat. After a while she falls asleep.

Speak to Maho now on https://martialgames.net/maho/!

MIT for the software. Character art keeps its own terms: see [NOTICE](NOTICE).

## Use it

- Cat: clip 39 (angry face, no red mark), then grr (angry with the mark). Then that loops. Sleep starts the loop over.
- Head: clip 39 with no mouth move, then the first phrase of clip 10, then all of clip 10. Then that loops. Sleep starts the loop over.
- Drag: grab her anywhere and move the window. A short click on the cat still fires.
- 45 seconds with no click: eyes close, `z`s over her head
- Click again: she wakes
- Right-click, or the Maho Overlay menu: Size (Small, Medium, Large, XL) and Quit. Large is the starting size. The art stays the full 1264×1568 PNG.

Clicks go through empty space around her, so you can still use the apps underneath.

## Run it

You need Node, Python 3.12, and Git LFS.

### macOS

```bash
git clone https://github.com/martialsystems/maho-overlay.git
cd maho-overlay
git lfs install
git lfs pull
python3.12 -m venv backend/.venv
backend/.venv/bin/pip install -r backend/requirements-no-ai.txt
cd frontend && npm install && cd ..
chmod +x start_local.command
./start_local.command
```

Same start later: `./start_local.command`

### Windows

```bat
git clone https://github.com/martialsystems/maho-overlay.git
cd maho-overlay
git lfs install
git lfs pull
py -3.12 -m venv backend\.venv
backend\.venv\Scripts\python -m pip install -r backend\requirements-no-ai.txt
cd frontend
npm install
cd ..
start_local.bat
```

Same start later: double-click `start_local.bat` or `start_windows.bat`.

## Files

| Path | Role |
|------|------|
| `frontend/` | Mesh puppet window and Electron shell |
| `backend/` | Local Flask process the launcher starts |
| `start_local.command` | Starts the overlay on a Mac |
| `start_local.bat` | Starts the overlay on Windows |
| `docs/ja_speech.md` | Slow+normal Japanese viseme pool (offline) |
| `docs/maho_voice.md` | Maho EN+JA script compile (offline) |
| `docs/maho_chat.md` | Maho chat via Grok subagent (no overlay, no Llama) |
| `docs/maho_science.md` | Brain science, Amadeus/AI, skeptical time-travel notes |
| `docs/maho_voice_bank.md` | Japanese Maho voice bank (equalize, then train) |
| [LICENSE](LICENSE) | MIT for our software |
| [NOTICE](NOTICE) | Character art terms |

## Changelog

