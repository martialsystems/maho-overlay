import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

const timerSrc = await readFile(new URL("../src/sleepTimer.ts", import.meta.url), "utf8");
const app = await readFile(new URL("../src/App.tsx", import.meta.url), "utf8");
const css = await readFile(new URL("../src/styles.css", import.meta.url), "utf8");
const main = await readFile(new URL("../electron/main.cjs", import.meta.url), "utf8");

assert.doesNotMatch(app, /Live2DCharacter/);
assert.doesNotMatch(app, /sendInteraction/);
assert.match(app, /className="overlay"/);
assert.match(app, /MahoPuppet/);
assert.match(await readFile(new URL("../src/interactions.ts", import.meta.url), "utf8"), /label: "Cat"/);
assert.match(app, /ZzzLayer/);
assert.match(css, /\.anger-mark/);
assert.match(css, /top: 28%/);
assert.match(timerSrc, /IDLE_SLEEP_MS = 45_000/);
assert.match(css, /\.overlay\s*\{/);
assert.match(css, /\.zzz-layer/);
assert.match(main, /transparent:\s*true/);
assert.match(main, /hasShadow:\s*false/);
assert.match(main, /alwaysOnTop:\s*true/);
assert.match(css, /box-shadow:\s*none/);
assert.match(main, /WINDOW_WIDTH = 520/);
assert.match(main, /WINDOW_HEIGHT = 720/);
assert.match(main, /Maho Overlay/);

const rootReadme = await readFile(new URL("../../README.md", import.meta.url), "utf8");
assert.match(rootReadme, /# maho-overlay/);
assert.match(rootReadme, /start_local\.bat/);
assert.match(rootReadme, /py -3\.12/);
assert.match(rootReadme, /martialsystems\/maho-overlay/);
assert.doesNotMatch(rootReadme, /\u2014/);
assert.doesNotMatch(rootReadme, /What it is not/);

const winBat = await readFile(new URL("../../start_local.bat", import.meta.url), "utf8");
assert.match(winBat, /launcher\.py" --no-ai/);
assert.match(winBat, /backend\\\.venv\\Scripts\\python\.exe/);

const license = await readFile(new URL("../../LICENSE", import.meta.url), "utf8");
const notice = await readFile(new URL("../../NOTICE", import.meta.url), "utf8");
assert.match(license, /MIT License/);
assert.match(license, /Martial Systems LLC/);
assert.match(notice, /frontend\/public\/maho/);
assert.doesNotMatch(notice, /Live2D Cubism Core/);
