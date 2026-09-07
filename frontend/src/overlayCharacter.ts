export type PlayMotionResult = "started" | "busy" | "not-ready" | "missing";

/** Overlay handle for the Maho mesh puppet. */
export type OverlayCharacterHandle = {
  playMotion: (group: string) => PlayMotionResult;
  hitTest: (clientX: number, clientY: number) => boolean;
  setSleeping: (sleeping: boolean) => void;
  prepareSpeech: () => Promise<void>;
  playSpeech: (url: string) => Promise<void>;
  stopSpeech: () => void;
};
