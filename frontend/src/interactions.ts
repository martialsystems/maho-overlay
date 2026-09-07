/** Hit boxes. Motion names match MahoMotion.play. */
export const interactions = {
  special: {
    backendId: 1,
    motion: "TapReaction",
    label: "Cat",
    // Tight on the plush only. Mouth and hoodie stay out of this box.
    position: { top: "72%", left: "50%", width: "26%", height: "14%" },
  },
};

export type InteractionName = keyof typeof interactions;
