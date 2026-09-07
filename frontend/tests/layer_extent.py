#!/usr/bin/env python3
"""Opaque-count and bbox gates for Maho layer PNGs."""

from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1] / "public" / "maho" / "layers"


def bbox(im: Image.Image) -> tuple[int, int, int, int, int]:
    alpha = im.split()[-1]
    box = alpha.getbbox()
    if box is None:
        raise SystemExit("layer PNG is empty")
    count = sum(1 for p in alpha.getdata() if p > 8)
    return box[0], box[1], box[2], box[3], count


def main() -> None:
    neck = Image.open(ROOT / "neck.png").convert("RGBA")
    collar = Image.open(ROOT / "collar.png").convert("RGBA")
    bangs = Image.open(ROOT / "bangs.png").convert("RGBA")
    side = Image.open(ROOT / "side-bangs.png").convert("RGBA")
    cat = Image.open(ROOT / "cat.png").convert("RGBA")
    for name, im in (
        ("neck", neck),
        ("collar", collar),
        ("bangs", bangs),
        ("side-bangs", side),
        ("cat", cat),
    ):
        assert im.size == (1264, 1568), (name, im.size)

    nx0, ny0, nx1, ny1, n_neck = bbox(neck)
    cx0, cy0, cx1, cy1, n_collar = bbox(collar)
    _, by0, _, by1, n_bangs = bbox(bangs)
    _, _, _, sy1, n_side = bbox(side)
    _, _, _, _, n_cat = bbox(cat)

    assert n_neck >= 15000, n_neck
    assert ny1 >= 890, ny1
    assert n_collar >= 50000, n_collar
    assert cy1 >= 940, cy1
    assert n_bangs >= 4000, n_bangs
    assert by1 <= 540, by1
    assert n_side >= 80000, n_side
    assert sy1 >= 800, sy1
    assert n_cat >= 80000, n_cat
    print("layer_extent ok", n_neck, n_collar, n_bangs, n_side, n_cat)


if __name__ == "__main__":
    main()
