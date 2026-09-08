export type MouthViseme = "idle" | "mouth-half" | "mouth-open";

/**
 * Relative RMS gates. Fit on 42 Amadeus Overlay reaction WAVs (English and
 * Japanese): of active-speech frames, about 19% closed, 28% half, 54% open.
 * Per-clip peak so quiet talk (mahotalk.mp4) and louder future lines share
 * the same mouth set.
 */
export const MOUTH_SILENCE = 0.04;
export const MOUTH_HALF = 0.28;
export const MOUTH_OPEN = 0.5;

export class MouthDriver {
  peak = 0;

  reset(): void {
    this.peak = 0;
  }

  viseme(amplitude: number): MouthViseme {
    if (amplitude < MOUTH_SILENCE) {
      this.peak *= 0.985;
      return "idle";
    }
    this.peak = Math.max(amplitude, this.peak * 0.995);
    const rel = amplitude / Math.max(this.peak, MOUTH_SILENCE);
    if (rel >= MOUTH_OPEN) return "mouth-open";
    if (rel >= MOUTH_HALF) return "mouth-half";
    return "idle";
  }
}
