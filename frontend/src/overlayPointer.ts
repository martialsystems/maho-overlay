/** Desktop overlay pointer: click-through on empty pixels, drag the figure. */

type OverlayHost = NonNullable<Window["overlay"]>;

export function startOverlayPointer(options: {
  hitTest: (clientX: number, clientY: number) => boolean;
  onActivity?: () => void;
}): () => void {
  const overlay = window.overlay;
  if (overlay === undefined) return () => {};
  return attachOverlayPointer(overlay, options);
}

function attachOverlayPointer(
  host: OverlayHost,
  options: {
    hitTest: (clientX: number, clientY: number) => boolean;
    onActivity?: () => void;
  },
): () => void {
  let ignoring = true;
  let dragging = false;
  let lastX = 0;
  let lastY = 0;
  let raf = 0;
  let pending: MouseEvent | null = null;

  host.setClickThrough(true);

  function applyIgnore(next: boolean) {
    if (ignoring === next) return;
    ignoring = next;
    host.setClickThrough(next);
  }

  function onMove(event: MouseEvent) {
    if (dragging) {
      host.moveBy(event.screenX - lastX, event.screenY - lastY);
      lastX = event.screenX;
      lastY = event.screenY;
      return;
    }

    pending = event;
    if (raf) return;
    raf = requestAnimationFrame(() => {
      raf = 0;
      const current = pending;
      pending = null;
      if (!current || dragging) return;
      const overButton =
        current.target instanceof Element &&
        current.target.closest(".touch-button") !== null;
      const solid = overButton || options.hitTest(current.clientX, current.clientY);
      applyIgnore(!solid);
    });
  }

  function onDown(event: MouseEvent) {
    if (event.button !== 0) return;
    const overButton =
      event.target instanceof Element &&
      event.target.closest(".touch-button") !== null;
    if (overButton || options.hitTest(event.clientX, event.clientY)) {
      options.onActivity?.();
    }
    if (overButton) return;
    if (!options.hitTest(event.clientX, event.clientY)) return;
    dragging = true;
    lastX = event.screenX;
    lastY = event.screenY;
    event.preventDefault();
  }

  function onUp() {
    dragging = false;
  }

  window.addEventListener("mousemove", onMove);
  window.addEventListener("mousedown", onDown);
  window.addEventListener("mouseup", onUp);
  window.addEventListener("blur", onUp);

  return () => {
    cancelAnimationFrame(raf);
    window.removeEventListener("mousemove", onMove);
    window.removeEventListener("mousedown", onDown);
    window.removeEventListener("mouseup", onUp);
    window.removeEventListener("blur", onUp);
    host.setClickThrough(true);
  };
}
