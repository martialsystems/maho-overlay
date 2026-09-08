/** Hit boxes. Motion names match MahoMotion.play. */
export type Interaction = {
  backendId?: number;
  motion: string;
  label: string;
  speechUrl?: string;
  position: { top: string; left: string; width: string; height: string };
};

export const interactions: Record<string, Interaction> = {
  head: {
    backendId: 2,
    motion: "PatReaction",
    label: "Head",
    // Hair and crown. Mouth and eyes stay out of this box.
    position: { top: "14%", left: "50%", width: "28%", height: "12%" },
  },
  talk: {
    motion: "",
    label: "Talk",
    speechUrl: "/maho/talk.wav",
    // Mouth only. Sits above the cat, below the nose.
    position: { top: "48%", left: "50%", width: "16%", height: "7%" },
  },
  special: {
    backendId: 1,
    motion: "TapReaction",
    label: "Cat",
    // Tight on the plush only. Mouth and hoodie stay out of this box.
    position: { top: "72%", left: "50%", width: "26%", height: "14%" },
  },
};

export type InteractionName = "head" | "talk" | "special";
