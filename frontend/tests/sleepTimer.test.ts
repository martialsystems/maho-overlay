import assert from "node:assert/strict";
import { IDLE_SLEEP_MS, startSleepTimer } from "../src/sleepTimer.ts";

assert.equal(IDLE_SLEEP_MS, 45_000);

const events: string[] = [];
let pending: { callback: () => void; delay: number } | null = null;
const timer = startSleepTimer({
  delayMs: IDLE_SLEEP_MS,
  onSleep: () => events.push("sleep"),
  onWake: () => events.push("wake"),
  setTimeoutFn: (callback, delay) => {
    pending = { callback, delay };
    return 1;
  },
  clearTimeoutFn: () => {
    pending = null;
  },
});

assert.equal(pending?.delay, 45_000);
pending?.callback();
assert.deepEqual(events, ["sleep"]);
timer.poke();
assert.deepEqual(events, ["sleep", "wake"]);
assert.equal(pending?.delay, 45_000);
pending?.callback();
assert.deepEqual(events, ["sleep", "wake", "sleep"]);
timer.stop();
