#!/usr/bin/env python3
# Copyright (c) 2026 Martial Systems LLC. MIT.
"""Paint talk visemes onto the overlay still.

The raised nose lives on the rest stills (idle, eyes-closed, angry), not on
talk frames. Talking uses a skin-only mouth with no lip line, then half/open
on that blank. Lip stroke is 2px, uniform.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "frontend/public/maho"
IDLE = OUT / "maho.png"

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
REST = ("maho.png", "maho-eyes-closed.png", "maho-angry.png")


def shift_nose(img: Image.Image) -> None:
    left, top, right, bottom = NOSE_BOX
    crop = img.crop((left, top, right, bottom))
    for y in range(top, bottom):
        for x in range(left, right):
            img.putpixel((x, y), img.getpixel((x, top - 1)))
    img.paste(crop, (left, top - NOSE_SHIFT))


def erase_lips(img: Image.Image) -> None:
    skin = img.getpixel((644, 748))
    ImageDraw.Draw(img).ellipse([600, 750, 688, 778], fill=skin)


def paint_mouth(kind: str, blank: Image.Image) -> Image.Image:
    out = blank.copy()
    left, top, right, bottom = BOX
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


def write_png(im: Image.Image, name: str) -> None:
    if im.size != (1264, 1568):
        raise SystemExit("size {0} for {1}".format(im.size, name))
    im.save(OUT / name, "PNG")


def bake_rest_noses() -> None:
    for name in REST:
        path = OUT / name
        im = Image.open(path).convert("RGBA")
        shift_nose(im)
        write_png(im, name)


def paint_talk() -> None:
    idle = Image.open(IDLE).convert("RGBA")
    blank = idle.copy()
    erase_lips(blank)
    write_png(blank, "maho-mouth-blank.png")
    write_png(paint_mouth("half", blank), "maho-mouth-half.png")
    write_png(paint_mouth("open", blank), "maho-mouth-open.png")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--rest-nose",
        action="store_true",
        help="Shift the nose up on idle, eyes-closed, and angry. Run once.",
    )
    args = parser.parse_args()
    if args.rest_nose:
        bake_rest_noses()
    paint_talk()


if __name__ == "__main__":
    main()
