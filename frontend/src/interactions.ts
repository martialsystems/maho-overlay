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
    // Crown and hair only. Face and mouth stay out.
    position: { top: "12%", left: "50%", width: "38%", height: "16%" },
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
