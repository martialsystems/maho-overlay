/** Desktop overlay pointer: drag the figure first. Stationary clicks still hit. */

type OverlayHost = NonNullable<Window["overlay"]>;

export const DRAG_THRESHOLD_PX = 5;

export function startOverlayPointer(options: {
  hitTest: (clientX: number, clientY: number) => boolean;
  onActivity?: () => void;
}): () => void {
  const overlay = window.overlay;
  if (overlay === undefined) return () => {};
  return attachOverlayPointer(overlay, options);
}

export function attachOverlayPointer(
  host: OverlayHost,
  options: {
    hitTest: (clientX: number, clientY: number) => boolean;
    onActivity?: () => void;
  },
): () => void {
  let ignoring = true;
  let tracking = false;
  let dragging = false;
  let suppressClick = false;
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

  function onSolid(event: MouseEvent): boolean {
    const overButton =
      event.target instanceof Element &&
      event.target.closest(".touch-button") !== null;
    return overButton || options.hitTest(event.clientX, event.clientY);
  }

  function onMove(event: MouseEvent) {
    if (tracking) {
      const dx = event.screenX - lastX;
      const dy = event.screenY - lastY;
      if (!dragging && dx * dx + dy * dy >= DRAG_THRESHOLD_PX * DRAG_THRESHOLD_PX) {
        dragging = true;
        suppressClick = true;
      }
      if (dragging) {
        host.moveBy(dx, dy);
        lastX = event.screenX;
        lastY = event.screenY;
        event.preventDefault();
      }
      return;
    }

    pending = event;
    if (raf) return;
    raf = requestAnimationFrame(() => {
      raf = 0;
      const current = pending;
      pending = null;
      if (!current || tracking) return;
      applyIgnore(!onSolid(current));
    });
  }

  function onDown(event: MouseEvent) {
    if (event.button !== 0) return;
    if (!onSolid(event)) return;
    options.onActivity?.();
    tracking = true;
    dragging = false;
    suppressClick = false;
    lastX = event.screenX;
    lastY = event.screenY;
  }

  function onUp() {
    tracking = false;
    dragging = false;
  }

  function onMouseUp(event: MouseEvent) {
    if (dragging) event.preventDefault();
    onUp();
  }

  function onClick(event: MouseEvent) {
    if (!suppressClick) return;
    suppressClick = false;
    event.preventDefault();
    event.stopPropagation();
  }

  window.addEventListener("mousemove", onMove);
  window.addEventListener("mousedown", onDown);
  window.addEventListener("mouseup", onMouseUp);
  window.addEventListener("click", onClick, true);
  window.addEventListener("blur", onUp);

  return () => {
    cancelAnimationFrame(raf);
    window.removeEventListener("mousemove", onMove);
    window.removeEventListener("mousedown", onDown);
    window.removeEventListener("mouseup", onMouseUp);
    window.removeEventListener("click", onClick, true);
    window.removeEventListener("blur", onUp);
    host.setClickThrough(true);
  };
}
