export {};

declare global {
  interface Window {
    overlay?: {
      setClickThrough: (ignore: boolean) => void;
      moveBy: (dx: number, dy: number) => void;
      quit: () => void;
    };
  }
}
