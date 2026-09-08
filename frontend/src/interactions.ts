/** Hit boxes. Motion names match MahoMotion.play. */
export type Interaction = {
  motion: string;
  label: string;
  speechUrl?: string;
  sfx?: boolean;
  position: { top: string; left: string; width: string; height: string };
};

export const interactions: Record<string, Interaction> = {
  head: {
    motion: "PatReaction",
    label: "Head",
    speechUrl: "/maho/head.wav",
    // Hair crown in the window (~20% to 34%). Mesh zoom 0.9 plus y 0.05;
    // a 12% box sits in click-through empty space above her.
    position: { top: "26%", left: "50%", width: "40%", height: "16%" },
  },
  special: {
    motion: "TapReaction",
    label: "Cat",
    speechUrl: "/maho/grr.wav",
    sfx: true,
    // Tight on the plush only. Mouth and hoodie stay out of this box.
    position: { top: "72%", left: "50%", width: "26%", height: "14%" },
  },
};

export type InteractionName = "head" | "special";
