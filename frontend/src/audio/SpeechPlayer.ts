export type SpeechPlayerCallbacks = {
  onSpeakingChange: (speaking: boolean) => void;
  onAmplitude: (value: number) => void;
  onError?: (message: string) => void;
};

/**
 * Plays a WAV in the browser and exposes a smoothed 0..1 amplitude
 * for mouth visemes. Same analyser path as Amadeus Overlay.
 */
export class SpeechPlayer {
  private readonly audio = new Audio();
  private readonly callbacks: SpeechPlayerCallbacks;

  private context: AudioContext | null = null;
  private source: MediaElementAudioSourceNode | null = null;
  private analyser: AnalyserNode | null = null;
  private samples: Uint8Array<ArrayBuffer> | null = null;

  private animationFrame = 0;
  private speaking = false;
  private smoothedAmplitude = 0;
  private destroyed = false;
  private generation = 0;
  private lastFrameTime = 0;
  private emitVisemes = true;

  constructor(callbacks: SpeechPlayerCallbacks) {
    this.callbacks = callbacks;
    this.audio.crossOrigin = "anonymous";
    this.audio.preload = "auto";
    this.audio.addEventListener("playing", this.handlePlaying);
    this.audio.addEventListener("ended", this.handleEnded);
    this.audio.addEventListener("error", this.handleError);
    this.audio.addEventListener("pause", this.handleEnded);
    this.audio.addEventListener("waiting", this.handleEnded);
  }

  isSpeaking(): boolean {
    return this.speaking && !this.destroyed;
  }

  async prepare(): Promise<void> {
    if (this.destroyed) return;

    if (!this.context) {
      const context = new AudioContext();
      const analyser = context.createAnalyser();
      analyser.fftSize = 256;
      analyser.smoothingTimeConstant = 0;

      const source = context.createMediaElementSource(this.audio);
      source.connect(analyser);
      analyser.connect(context.destination);

      this.context = context;
      this.source = source;
      this.analyser = analyser;
      this.samples = new Uint8Array(analyser.fftSize);
    }

    if (this.context.state === "suspended") {
      await this.context.resume();
    }
  }

  async play(url: string, opts?: { visemes?: boolean }): Promise<void> {
    if (this.destroyed) return;
    this.stop();
    this.emitVisemes = opts?.visemes !== false;
    const generation = this.generation;
    await this.prepare();
    if (this.destroyed || generation !== this.generation) return;

    this.audio.volume = 1;
    this.audio.src = url;
    this.audio.load();

    try {
      await this.audio.play();
    } catch (error) {
      if (this.destroyed || generation !== this.generation) return;
      this.finishSpeaking();
      throw error;
    }
  }

  stop(): void {
    this.generation++;
    cancelAnimationFrame(this.animationFrame);
    this.animationFrame = 0;

    if (!this.audio.paused) {
      this.audio.pause();
    }

    this.audio.removeAttribute("src");
    this.audio.load();
    this.finishSpeaking();
  }

  private handlePlaying = (): void => {
    if (this.destroyed || this.speaking) return;

    this.speaking = true;
    this.lastFrameTime = performance.now();
    this.smoothedAmplitude = 0;
    if (this.emitVisemes) this.callbacks.onSpeakingChange(true);
    this.updateAmplitude();
  };

  private handleEnded = (): void => {
    this.finishSpeaking();
  };

  private handleError = (): void => {
    this.finishSpeaking();
    if (!this.destroyed && this.audio.error) {
      this.callbacks.onError?.("Speech playback failed.");
    }
  };

  private updateAmplitude = (): void => {
    if (
      this.destroyed ||
      !this.speaking ||
      !this.analyser ||
      !this.samples
    ) {
      return;
    }

    this.analyser.getByteTimeDomainData(this.samples);

    let sumSquares = 0;
    for (const sample of this.samples) {
      const normalized = (sample - 128) / 128;
      sumSquares += normalized * normalized;
    }

    const rms = Math.sqrt(sumSquares / this.samples.length);
    const target = Math.min(1, Math.max(0, rms - 0.012) * 11);
    const now = performance.now();
    const dt = Math.min((now - this.lastFrameTime) / 1000, 0.1);
    this.lastFrameTime = now;
    const smoothing = 1 - Math.exp(-dt / (target > this.smoothedAmplitude ? 0.028 : 0.067));
    this.smoothedAmplitude +=
      (target - this.smoothedAmplitude) * smoothing;

    if (this.emitVisemes) this.callbacks.onAmplitude(this.smoothedAmplitude);
    this.animationFrame = requestAnimationFrame(this.updateAmplitude);
  };

  private finishSpeaking(): void {
    cancelAnimationFrame(this.animationFrame);
    this.animationFrame = 0;
    this.smoothedAmplitude = 0;
    if (this.speaking) {
      this.speaking = false;
      if (this.emitVisemes) this.callbacks.onSpeakingChange(false);
    }
    this.callbacks.onAmplitude(0);
  }

  destroy(): void {
    if (this.destroyed) return;

    this.stop();
    this.destroyed = true;

    this.audio.removeEventListener("playing", this.handlePlaying);
    this.audio.removeEventListener("ended", this.handleEnded);
    this.audio.removeEventListener("error", this.handleError);
    this.audio.removeEventListener("pause", this.handleEnded);
    this.audio.removeEventListener("waiting", this.handleEnded);

    this.source?.disconnect();
    this.analyser?.disconnect();
    this.source = null;
    this.analyser = null;
    this.samples = null;

    if (this.context) {
      void this.context.close();
      this.context = null;
    }
  }
}
