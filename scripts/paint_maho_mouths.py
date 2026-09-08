#!/usr/bin/env python3
# Copyright (c) 2026 Martial Systems LLC. MIT.
"""Paint talk visemes onto the overlay still.

Idle closed lips are about 53px wide. Talk mouths are wider than that.
The nose mark is copied 10px up so the bigger opening does not cover it.
Lip stroke is 2px, uniform. Face fill uses the still, not a flat patch.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "frontend/public/maho/maho.png"
OUT = ROOT / "frontend/public/maho"

STROKE = (110, 70, 64, 255)
INNER_HALF = (198, 112, 108, 255)
INNER_OPEN = (56, 26, 28, 255)
TONGUE = (188, 90, 86, 255)
BOX = (580, 728, 710, 812)
NOSE_BOX = (628, 708, 656, 734)
NOSE_SHIFT = 10
SCALE = 4
HALF_RX, HALF_RY = 36, 13
OPEN_RX, OPEN_RY = 38, 24


def shift_nose(img: Image.Image) -> None:
    left, top, right, bottom = NOSE_BOX
    crop = img.crop((left, top, right, bottom))
    for y in range(top, bottom):
        for x in range(left, right):
            img.putpixel((x, y), img.getpixel((x, top - 1)))
    img.paste(crop, (left, top - NOSE_SHIFT))


def paint(kind: str, base: Image.Image) -> Image.Image:
    out = base.copy()
    shift_nose(out)
    left, top, right, bottom = BOX
    skin = out.getpixel((644, 748))
    ImageDraw.Draw(out).ellipse([608, 754, 680, 774], fill=skin)
    face = out.crop((left, top, right, bottom))
    hi = face.resize((face.width * SCALE, face.height * SCALE), Image.Resampling.NEAREST)
    draw = ImageDraw.Draw(hi)
    cx = (644 - left) * SCALE
    cy = (768 - top) * SCALE
    if kind == "half":
        rx, ry = HALF_RX * SCALE, HALF_RY * SCALE
        draw.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=INNER_HALF)
    else:
        rx, ry = OPEN_RX * SCALE, OPEN_RY * SCALE
        draw.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=INNER_OPEN)
        draw.ellipse(
            [cx - rx + 4 * SCALE, cy - ry // 8, cx + rx - 4 * SCALE, cy + ry - 2 * SCALE],
            fill=TONGUE,
        )
    draw.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], outline=STROKE, width=2 * SCALE)
    lo = hi.resize(face.size, Image.Resampling.LANCZOS)
    mask = Image.new("L", face.size, 0)
    ImageDraw.Draw(mask).ellipse(
        [
            644 - left - rx // SCALE - 3,
            768 - top - ry // SCALE - 3,
            644 - left + rx // SCALE + 3,
            768 - top + ry // SCALE + 3,
        ],
        fill=255,
    )
    out.paste(lo, (left, top), mask)
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
