#!/usr/bin/env python3
# Copyright (c) 2026 Martial Systems LLC. MIT.
"""Paint talk visemes onto the overlay still.

Keeps the original nose pixels. Lip stroke is 2px, uniform, not bold.
Face fill is the model skin #f0dacc.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "frontend/public/maho/maho.png"
OUT = ROOT / "frontend/public/maho"

SKIN = (240, 218, 204, 255)
STROKE = (110, 70, 64, 255)
INNER_HALF = (198, 112, 108, 255)
INNER_OPEN = (56, 26, 28, 255)
TONGUE = (188, 90, 86, 255)
BOX = (590, 744, 698, 792)
SCALE = 4


def paint(kind: str, base: Image.Image) -> Image.Image:
    out = base.copy()
    left, top, right, bottom = BOX
    patch = Image.new("RGBA", ((right - left) * SCALE, (bottom - top) * SCALE), SKIN)
    draw = ImageDraw.Draw(patch)
    cx = (644 - left) * SCALE
    cy = (764 - top) * SCALE
    if kind == "half":
        rx, ry = 26 * SCALE, 9 * SCALE
    else:
        rx, ry = 24 * SCALE, 17 * SCALE
    if kind == "half":
        draw.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=INNER_HALF)
    else:
        draw.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=INNER_OPEN)
        # Tongue fills the lower two thirds, like the staff-room still.
        draw.ellipse(
            [cx - rx + 3 * SCALE, cy - ry // 6, cx + rx - 3 * SCALE, cy + ry - 2 * SCALE],
            fill=TONGUE,
        )
    draw.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], outline=STROKE, width=2 * SCALE)
    small = patch.resize((right - left, bottom - top), Image.Resampling.LANCZOS)
    out.paste(small, (left, top))
    return out


def main() -> None:
    base = Image.open(SRC).convert("RGBA")
    for kind, name in (("half", "maho-mouth-half.png"), ("open", "maho-mouth-open.png")):
        im = paint(kind, base)
        if im.size != (1264, 1568):
            raise SystemExit("size {0}".format(im.size))
        im.save(OUT / name, "PNG")


if __name__ == "__main__":
    main()
