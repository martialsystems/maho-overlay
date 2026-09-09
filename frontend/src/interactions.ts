/** Hit boxes. Motion names match MahoMotion.play. */
export type ClipStep = {
  url: string;
  sfx?: boolean;
  motion?: string;
};

export type Interaction = {
  motion: string;
  label: string;
  clips: ClipStep[];
  position: { top: string; left: string; width: string; height: string };
};

export const interactions: Record<string, Interaction> = {
  head: {
    motion: "",
    label: "Head",
    // 39 (no visemes), first phrase of 10, then full 10. Loops. Sleep resets.
    clips: [
      { url: "/maho/clip39.wav", sfx: true },
      { url: "/maho/head10a.wav" },
      { url: "/maho/head.wav" },
    ],
    // Hair crown in the window (~20% to 34%). Mesh zoom 0.9 plus y 0.05;
    // a 12% box sits in click-through empty space above her.
    position: { top: "26%", left: "50%", width: "40%", height: "16%" },
  },
  special: {
    motion: "TapReaction",
    label: "Cat",
    // 39 angry no mark, then grr with the red mark. Loops. Sleep resets.
    clips: [
      { url: "/maho/clip39.wav", sfx: true, motion: "AnnoyedReaction" },
      { url: "/maho/grr.wav", sfx: true, motion: "TapReaction" },
    ],
    // Tight on the plush only. Mouth and hoodie stay out of this box.
    position: { top: "72%", left: "50%", width: "26%", height: "14%" },
  },
};

export type InteractionName = "head" | "special";

export function nextStep(step: number, count: number): number {
  if (count <= 0) return 0;
  return (step + 1) % count;
}
