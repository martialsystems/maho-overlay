import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { buildGridMesh, groupIndexAt, skinVertices } from "../src/maho/buildMesh";
import type { MeshSpec } from "../src/maho/buildMesh";
import { MahoMotion } from "../src/maho/motion";
import { MouthDriver, MOUTH_HALF, MOUTH_OPEN } from "../src/maho/viseme";

function pngSize(bytes: Uint8Array): { width: number; height: number } {
  const view = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
  return { width: view.getUint32(16), height: view.getUint32(20) };
}

const spec = JSON.parse(
  await readFile(new URL("../public/maho/mesh.json", import.meta.url), "utf8"),
) as MeshSpec;
assert.ok(spec.textures["angry-mouth-open"]);
assert.ok(spec.textures["angry-mouth-half"]);

assert.deepEqual(
  Object.keys(spec.groups).sort(),
  ["arms", "body", "eyes", "face", "head", "plush"],
);
assert.equal(spec.width, 1264);
assert.equal(spec.height, 1568);

const mesh = buildGridMesh(spec);
assert.deepEqual(mesh.groupNames, ["eyes", "face", "plush", "arms", "head", "body"]);
assert.equal(mesh.groupNames[groupIndexAt(spec, 0.5, 0.48)], "face");
assert.equal(mesh.groupNames[groupIndexAt(spec, 0.5, 0.62)], "plush");

function nearest(u: number, v: number): number {
  let best = 0;
  let bestD = 9;
  for (let i = 0; i < mesh.group.length; i++) {
    const du = mesh.rest[i * 2] - u;
    const dv = mesh.rest[i * 2 + 1] - v;
    const d = du * du + dv * dv;
    if (d < bestD) {
      bestD = d;
      best = i;
    }
  }
  return best;
}

const chinI = nearest(0.5, 0.48);
const plushI = nearest(0.5, 0.62);
const bodyI = nearest(0.12, 0.7);
const posed = new Float32Array(mesh.rest.length);
const hairI = nearest(0.2, 0.12);
skinVertices(spec, mesh, {
  faceRot: 0.25,
  hairSway: 0,
  torsoBob: 0.02,
  armBob: 0,
  plushBob: 0,
  shakeX: 0,
}, posed);
const chinMove = Math.abs(posed[chinI * 2] - mesh.rest[chinI * 2]);
const hairMove = Math.abs(posed[hairI * 2] - mesh.rest[hairI * 2]);
assert.ok(chinMove > 0.01, `chin should swing, got ${chinMove}`);
assert.equal(hairMove, 0);
assert.equal(posed[plushI * 2 + 1], mesh.rest[plushI * 2 + 1]);
assert.notEqual(posed[bodyI * 2 + 1], mesh.rest[bodyI * 2 + 1]);
assert.equal(mesh.indices.length, spec.cols * spec.rows * 6);
assert.equal(mesh.rest.length, mesh.uv.length);
assert.doesNotMatch(
  await readFile(new URL("../src/maho/meshPlayer.ts", import.meta.url), "utf8"),
  /LINE_STRIP|LINES\b/,
);

for (const name of [
  "maho.png",
  "maho-eyes-closed.png",
  "maho-angry.png",
  "maho-mouth-blank.png",
  "maho-mouth-half.png",
  "maho-mouth-open.png",
  "maho-angry-mouth-blank.png",
  "maho-angry-mouth-half.png",
  "maho-angry-mouth-open.png",
] as const) {
  const bytes = await readFile(new URL(`../public/maho/${name}`, import.meta.url));
  assert.equal(bytes[0], 0x89);
  const size = pngSize(bytes);
  assert.equal(size.width, 1264, name);
  assert.equal(size.height, 1568, name);
}

const idlePng = await readFile(new URL("../public/maho/maho.png", import.meta.url));
const blankPng = await readFile(new URL("../public/maho/maho-mouth-blank.png", import.meta.url));
const halfPng = await readFile(new URL("../public/maho/maho-mouth-half.png", import.meta.url));
const openPng = await readFile(new URL("../public/maho/maho-mouth-open.png", import.meta.url));
assert.notEqual(Buffer.compare(idlePng, blankPng), 0);
assert.notEqual(Buffer.compare(blankPng, halfPng), 0);
assert.notEqual(Buffer.compare(halfPng, openPng), 0);
const angryPng = await readFile(new URL("../public/maho/maho-angry.png", import.meta.url));
const angryOpenPng = await readFile(new URL("../public/maho/maho-angry-mouth-open.png", import.meta.url));
const angryHalfPng = await readFile(new URL("../public/maho/maho-angry-mouth-half.png", import.meta.url));
assert.notEqual(Buffer.compare(angryPng, angryOpenPng), 0);
assert.notEqual(Buffer.compare(angryHalfPng, angryOpenPng), 0);
assert.notEqual(Buffer.compare(openPng, angryOpenPng), 0);

const driver = new MouthDriver();
assert.equal(driver.viseme(0), "idle");
driver.reset();
assert.equal(driver.viseme(1), "mouth-open");
driver.reset();
driver.peak = 1;
assert.equal(driver.viseme(MOUTH_HALF), "mouth-half");
assert.equal(driver.viseme(MOUTH_OPEN), "mouth-open");

const talkWav = await readFile(new URL("../public/maho/talk.wav", import.meta.url));
assert.ok(talkWav.subarray(0, 4).toString("ascii") === "RIFF");
assert.ok(talkWav.byteLength > 50_000);

const talking = new MahoMotion();
talking.setSpeaking(true);
talking.update(0.016);
assert.equal(talking.texture, "mouth-open");
talking.setMouth("idle");
talking.update(0.016);
assert.equal(talking.texture, "mouth-open");
talking.setMouth("mouth-open");
talking.update(0.016);
assert.equal(talking.texture, "mouth-open");
talking.setMouth("mouth-half");
talking.update(0.016);
assert.equal(talking.texture, "mouth-half");
talking.setSpeaking(false);
talking.update(0.016);
assert.equal(talking.texture, "idle");

const motion = new MahoMotion();
assert.equal(motion.play("TapReaction"), "started");
assert.equal(motion.texture, "angry-mouth-open");
assert.equal(motion.angerMark, true);
assert.equal(motion.play("PatReaction"), "busy");
motion.setSpeaking(true);
motion.setMouth("mouth-half");
motion.update(0.016);
assert.equal(motion.texture, "angry-mouth-half");
motion.setMouth("mouth-open");
for (let i = 0; i < 20; i++) motion.update(0.1);
assert.equal(motion.texture, "angry-mouth-open");
assert.equal(motion.angerMark, true);
motion.setSpeaking(false);
motion.update(0.016);
assert.equal(motion.texture, "idle");
assert.equal(motion.angerMark, false);
assert.equal(motion.busy, false);

assert.equal(motion.play("PatReaction"), "started");
assert.equal(motion.angerMark, false);
assert.notEqual(motion.texture, "angry");
for (let i = 0; i < 20; i++) motion.update(0.1);

motion.setSleeping(true);
motion.update(0.05);
assert.equal(motion.texture, "eyes-closed");

const app = await readFile(new URL("../src/App.tsx", import.meta.url), "utf8");
assert.match(app, /MahoPuppet/);
assert.doesNotMatch(app, /Live2DCharacter/);
assert.match(app, /sendInteraction/);

const playerSrc = await readFile(new URL("../src/maho/meshPlayer.ts", import.meta.url), "utf8");
assert.match(playerSrc, /const zoom = 0\.9/);
assert.match(playerSrc, /LINEAR_MIPMAP_LINEAR/);
assert.match(playerSrc, /generateMipmap/);
assert.doesNotMatch(playerSrc, /discard/);
const puppetSrc = await readFile(new URL("../src/components/MahoPuppet.tsx", import.meta.url), "utf8");
assert.match(puppetSrc, /webgl2/);
assert.match(puppetSrc, /antialias:\s*false/);
assert.match(playerSrc, /disable\(gl\.DITHER\)/);
assert.doesNotMatch(
  await readFile(new URL("../src/maho/buildMesh.ts", import.meta.url), "utf8"),
  /torsoScaleY/,
);

const hits = await readFile(new URL("../src/interactions.ts", import.meta.url), "utf8");
assert.match(hits, /top: "72%"/);
assert.match(hits, /label: "Cat"/);
assert.match(hits, /label: "Head"/);
assert.match(hits, /label: "Talk"/);
assert.match(hits, /PatReaction/);
assert.match(hits, /\/maho\/talk\.wav/);
assert.match(puppetSrc, /MahoMeshPlayer/);
assert.doesNotMatch(puppetSrc, /MahoLayerPlayer/);
assert.doesNotMatch(puppetSrc, /layers\.json/);
