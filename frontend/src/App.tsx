import { useEffect, useRef, useState } from "react";
import MahoPuppet from "./components/MahoPuppet";
import ZzzLayer from "./components/ZzzLayer";
import { startOverlayPointer } from "./overlayPointer";
import { useKurisuSleep } from "./useKurisuSleep";
import { interactions, nextStep } from "./interactions";
import type { OverlayCharacterHandle } from "./overlayCharacter";
import type { InteractionName } from "./interactions";

const ZERO_CYCLE: Record<InteractionName, number> = { head: 0, special: 0 };

export default function App() {
  const [busy, setBusy] = useState(false);
  const [cycle, setCycle] = useState(ZERO_CYCLE);
  const characterRef = useRef<OverlayCharacterHandle>(null);
  const { sleeping, noteActivity } = useKurisuSleep(characterRef);

  useEffect(() => {
    return startOverlayPointer({
      hitTest: (x, y) => characterRef.current?.hitTest(x, y) ?? false,
      onActivity: noteActivity,
    });
  }, [noteActivity]);

  useEffect(() => {
    if (sleeping) setCycle(ZERO_CYCLE);
  }, [sleeping]);

  async function handleInteraction(name: InteractionName) {
    if (busy) return;
    noteActivity();
    const interaction = interactions[name];
    const clips = interaction.clips;
    if (!clips.length) return;
    const index = cycle[name] % clips.length;
    const clip = clips[index];
    const motion = clip.motion ?? interaction.motion;
    if (clip.sfx) {
      if (motion) {
        const result = characterRef.current?.playMotion(motion) ?? "not-ready";
        if (result !== "started") return;
      }
      void characterRef.current?.playSfx(clip.url);
      setCycle((current) => ({ ...current, [name]: nextStep(index, clips.length) }));
      return;
    }
    if (motion) {
      const result = characterRef.current?.playMotion(motion) ?? "not-ready";
      if (result !== "started") return;
    }
    const url = clip.url;
    void characterRef.current?.prepareSpeech().then(() =>
      characterRef.current?.playSpeech(url),
    );
    setCycle((current) => ({ ...current, [name]: nextStep(index, clips.length) }));
  }

  return (
    <main className="overlay">
      <div className="character-viewport">
        <MahoPuppet ref={characterRef} onBusyChange={setBusy} />
        {sleeping ? <ZzzLayer /> : null}

        {(Object.keys(interactions) as InteractionName[]).map((name) => {
          const interaction = interactions[name];
          return (
            <button
              key={name}
              type="button"
              className="touch-button touch-point"
              style={interaction.position}
              aria-label={interaction.label}
              onClick={() => handleInteraction(name)}
            >
              {interaction.label}
            </button>
          );
        })}
      </div>
    </main>
  );
}
