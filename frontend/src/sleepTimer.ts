export const IDLE_SLEEP_MS = 45_000;

type TimeoutFn = (callback: () => void, delay: number) => unknown;
type ClearFn = (id: unknown) => void;

export function startSleepTimer(options: {
  onSleep: () => void;
  onWake?: () => void;
  delayMs?: number;
  setTimeoutFn?: TimeoutFn;
  clearTimeoutFn?: ClearFn;
}): { poke: () => void; stop: () => void } {
  const delay = options.delayMs ?? IDLE_SLEEP_MS;
  const schedule = options.setTimeoutFn ?? ((callback, ms) => setTimeout(callback, ms));
  const cancel = options.clearTimeoutFn ?? ((id) => clearTimeout(id as ReturnType<typeof setTimeout>));
  let asleep = false;
  let timer: unknown;

  function arm() {
    cancel(timer);
    timer = schedule(() => {
      if (asleep) return;
      asleep = true;
      options.onSleep();
    }, delay);
  }

  arm();

  return {
    poke() {
      const wasAsleep = asleep;
      asleep = false;
      arm();
      if (wasAsleep) options.onWake?.();
    },
    stop() {
      cancel(timer);
    },
  };
}
