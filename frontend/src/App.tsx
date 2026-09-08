import { useEffect, useRef, useState } from "react";
import MahoPuppet from "./components/MahoPuppet";
import ZzzLayer from "./components/ZzzLayer";
import { sendInteraction } from "./api";
import { startOverlayPointer } from "./overlayPointer";
import { useKurisuSleep } from "./useKurisuSleep";
import { interactions } from "./interactions";
import type { OverlayCharacterHandle } from "./overlayCharacter";
import type { InteractionName } from "./interactions";

export default function App() {
  const [busy, setBusy] = useState(false);
  const characterRef = useRef<OverlayCharacterHandle>(null);
  const { sleeping, noteActivity } = useKurisuSleep(characterRef);

  useEffect(() => {
    return startOverlayPointer({
      hitTest: (x, y) => characterRef.current?.hitTest(x, y) ?? false,
      onActivity: noteActivity,
    });
  }, [noteActivity]);

  async function handleInteraction(name: InteractionName) {
    if (busy) return;
    noteActivity();
    const interaction = interactions[name];
    if (interaction.speechUrl) {
      const url = interaction.speechUrl;
      void characterRef.current?.prepareSpeech().then(() =>
        characterRef.current?.playSpeech(url),
      );
      return;
    }
    if (!interaction.backendId || !interaction.motion) return;
    const result = characterRef.current?.playMotion(interaction.motion) ?? "not-ready";
    if (result !== "started") return;
    const speechReady = characterRef.current?.prepareSpeech().then(
      () => true,
      () => false,
    );
    setBusy(true);
    try {
      const reply = await sendInteraction(interaction.backendId);
      if (reply.speechUrl && (await speechReady)) {
        await characterRef.current?.playSpeech(reply.speechUrl);
      }
    } catch (error) {
      console.error("Interaction failed:", error);
      characterRef.current?.stopSpeech();
      setBusy(false);
    }
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
              className="touch-button"
              style={interaction.position}
              aria-label={interaction.label}
              disabled={busy}
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
