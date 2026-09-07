import type { PlayMotionResult } from "../overlayCharacter";

export type MahoTexture = "idle" | "eyes-closed" | "angry";

const BLINK_EVERY_MS = 3200;
const BLINK_HOLD_MS = 90;
const PAT_MS = 900;
const TAP_MS = 1400;

type Clip = {
  name: "PatReaction" | "TapReaction";
  elapsed: number;
  duration: number;
};

export class MahoMotion {
  texture: MahoTexture = "idle";
  angerMark = false;
  sleeping = false;
  busy = false;
  faceRot = 0;
  hairSway = 0;
  torsoScaleY = 1;
  armSqueeze = 0;
  plushBob = 0;
  shakeX = 0;
  onClipEnd: (() => void) | null = null;

  private time = 0;
  private blinkIn = BLINK_EVERY_MS;
  private blinkHold = 0;
  private clip: Clip | null = null;

  play(group: string): PlayMotionResult {
    if (this.busy) return "busy";
    if (group === "PatReaction") {
      this.busy = true;
      this.clip = { name: "PatReaction", elapsed: 0, duration: PAT_MS };
      return "started";
    }
    if (group === "TapReaction") {
      this.busy = true;
      this.angerMark = true;
      this.texture = "angry";
      this.clip = { name: "TapReaction", elapsed: 0, duration: TAP_MS };
      return "started";
    }
    return "missing";
  }

  setSleeping(sleeping: boolean): void {
    this.sleeping = sleeping;
    if (sleeping && this.clip?.name !== "TapReaction") {
      this.texture = "eyes-closed";
    }
  }

  update(deltaSeconds: number): void {
    const dt = Math.min(deltaSeconds, 0.1);
    this.time += dt;

    const breathe = Math.sin(this.time * 1.7);
    this.torsoScaleY = 1 + breathe * 0.012;
    this.armSqueeze = 0.5 + 0.5 * breathe;
    this.plushBob = Math.sin(this.time * 2.1) * 0.006;

    if (this.clip) {
      this.clip.elapsed += dt * 1000;
      const t = Math.min(1, this.clip.elapsed / this.clip.duration);
      if (this.clip.name === "PatReaction") {
        this.faceRot = Math.sin(t * Math.PI) * 0.16;
        this.hairSway = Math.sin(t * Math.PI) * 0.02;
        this.armSqueeze = 1;
        this.texture = this.sleeping ? "eyes-closed" : "idle";
        this.angerMark = false;
        this.shakeX = 0;
      } else {
        const shake = Math.sin(t * Math.PI * 8) * (1 - t) * 0.008;
        this.shakeX = shake;
        this.faceRot = -0.03;
        this.hairSway = 0.01;
        this.texture = "angry";
        this.angerMark = true;
      }
      if (t >= 1) {
        this.clip = null;
        this.busy = false;
        this.angerMark = false;
        this.faceRot = 0;
        this.hairSway = 0;
        this.shakeX = 0;
        this.texture = this.sleeping ? "eyes-closed" : "idle";
        this.onClipEnd?.();
      }
      return;
    }

    this.faceRot = Math.sin(this.time * 0.7) * 0.012;
    this.hairSway = Math.sin(this.time * 0.45) * 0.01;
    this.shakeX = 0;
    this.angerMark = false;

    if (this.sleeping) {
      this.texture = "eyes-closed";
      return;
    }

    this.blinkIn -= dt * 1000;
    if (this.blinkHold > 0) {
      this.blinkHold -= dt * 1000;
      this.texture = "eyes-closed";
      if (this.blinkHold <= 0) this.texture = "idle";
      return;
    }
    if (this.blinkIn <= 0) {
      this.blinkHold = BLINK_HOLD_MS;
      this.blinkIn = BLINK_EVERY_MS + Math.sin(this.time) * 400;
      this.texture = "eyes-closed";
      return;
    }
    this.texture = "idle";
  }
}
