# maho-overlay

Maho sits on your desktop. Click her head or the cat. After a while she falls asleep.

MIT for the software. Character art keeps its own terms: see [NOTICE](NOTICE).

## Use it

- Head: her face, chin, and bangs turn. Side hair stays in front of the bangs. Neck and collar stay put.
- Cat: she gets mad, and a vein mark pops on her hair. No sound yet.
- Drag: grab her anywhere and move the window. A short click on the head or cat still fires.
- 45 seconds with no click: eyes close, `z`s over her head
- Click again: she wakes
- Right-click, or the Maho Overlay menu, then Quit: close

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
| [LICENSE](LICENSE) | MIT for our software |
| [NOTICE](NOTICE) | Character art terms |

## Changelog

- Neck and collar fill the hoodie opening (2026-09-07). Bangs turn with the head, under the side hair.
- Maho overlay (2026-09-07): hoodie still as a full-res mesh. Cat click is mad + vein mark, no audio.
