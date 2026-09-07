#!/usr/bin/env python3
"""Rebuild Maho neck, collar, bangs, and side-bangs from maho.png."""

from __future__ import annotations

from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
MAHO = ROOT / "frontend" / "public" / "maho"
SRC_PATH = MAHO / "maho.png"
LAYER_DIR = MAHO / "layers"

W = 1264
H = 1568


def bbox(mask: np.ndarray) -> tuple[int, int, int, int, int] | None:
    ys, xs = np.where(mask)
    if len(xs) == 0:
        return None
    return int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max()), int(len(xs))


def dilate(mask: np.ndarray, radius: int) -> np.ndarray:
    if radius <= 0:
        return mask
    im = Image.fromarray(mask.astype(np.uint8) * 255)
    return np.array(im.filter(ImageFilter.MaxFilter(radius * 2 + 1))) > 127


def close_mask(mask: np.ndarray, radius: int) -> np.ndarray:
    im = Image.fromarray(mask.astype(np.uint8) * 255)
    im = im.filter(ImageFilter.MaxFilter(radius * 2 + 1))
    im = im.filter(ImageFilter.MinFilter(radius * 2 + 1))
    return np.array(im) > 127


def flood(h: int, w: int, seed: tuple[int, int], pred) -> np.ndarray:
    seen = np.zeros((h, w), dtype=bool)
    sx, sy = seed
    if not (0 <= sx < w and 0 <= sy < h) or not pred(sy, sx):
        return seen
    q: deque[tuple[int, int]] = deque([(sx, sy)])
    seen[sy, sx] = True
    while q:
        x, y = q.popleft()
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if 0 <= nx < w and 0 <= ny < h and not seen[ny, nx] and pred(ny, nx):
                seen[ny, nx] = True
                q.append((nx, ny))
    return seen


def save_rgba(path: Path, arr: np.ndarray) -> None:
    Image.fromarray(arr).save(path, optimize=True)


def copy_src(src: np.ndarray, mask: np.ndarray) -> np.ndarray:
    out = np.zeros_like(src)
    out[mask] = src[mask]
    return out


def punch_dark(arr: np.ndarray, mask: np.ndarray) -> np.ndarray:
    out = arr.copy()
    lum = out[:, :, 0].astype(np.int16) + out[:, :, 1].astype(np.int16) + out[:, :, 2].astype(np.int16)
    drop = mask & (out[:, :, 3] > 8) & (lum < 280)
    out[drop] = (0, 0, 0, 0)
    return out


def main() -> None:
    src = np.array(Image.open(SRC_PATH).convert("RGBA"))
    assert src.shape[0] == H and src.shape[1] == W
    body = np.array(Image.open(LAYER_DIR / "body.png").convert("RGBA"))
    face = np.array(Image.open(LAYER_DIR / "face.png").convert("RGBA"))
    face_angry = np.array(Image.open(LAYER_DIR / "face-angry.png").convert("RGBA"))
    face_closed = np.array(Image.open(LAYER_DIR / "face-eyes-closed.png").convert("RGBA"))

    r = src[:, :, 0].astype(np.int16)
    g = src[:, :, 1].astype(np.int16)
    b = src[:, :, 2].astype(np.int16)
    a = src[:, :, 3]
    opaque = a > 8
    lum = r + g + b
    dark = opaque & (lum < 280)
    skin = (
        opaque
        & (r > 130)
        & (g > 100)
        & (b > 90)
        & (r > g - 5)
        & (r - b > 15)
        & (lum > 350)
    )
    hoodie = opaque & (g > r + 12) & (g > 85) & (g > b)
    gray = opaque & (np.abs(r - g) < 18) & (np.abs(g - b) < 18) & (r > 140) & (r < 235)
    white = opaque & (r > 210) & (g > 210) & (b > 210)
    pink = opaque & (r > 180) & (g > 90) & (b > 90) & (r > g + 15)

    yy, xx = np.ogrid[:H, :W]

    def cat_pred(y: int, x: int) -> bool:
        if y < 905 or y > 1480 or x < 400 or x > 870:
            return False
        if hoodie[y, x] or skin[y, x]:
            return False
        return bool(white[y, x] or pink[y, x] or lum[y, x] > 520)

    cat_head = flood(H, W, (632, 1040), cat_pred)
    left_ear = ((xx - 500) / 58) ** 2 + ((yy - 922) / 48) ** 2 <= 1
    right_ear = ((xx - 790) / 58) ** 2 + ((yy - 922) / 48) ** 2 <= 1
    cat = cat_head | ((left_ear | right_ear) & (white | (lum > 500)) & (yy >= 860) & ~hoodie & ~skin)
    cat = dilate(cat, 3) & ~hoodie
    cat_head = dilate(cat_head, 2)
    print("cat", bbox(cat), "cat_head", bbox(cat_head))

    neck_core = skin & (yy >= 768) & (yy <= 922) & (xx >= 500) & (xx <= 770) & ~cat
    neck_mask = dilate(neck_core, 6) & ~hoodie & ~cat
    neck_out = np.zeros_like(src)
    # Original skin first, then dilate fill from the nearest core pixel on that row.
    neck_out[neck_core] = src[neck_core]
    for y in range(H):
        xs = np.where(neck_core[y])[0]
        extra = np.where(neck_mask[y] & ~neck_core[y])[0]
        if len(xs) == 0 or len(extra) == 0:
            continue
        left, right = int(xs.min()), int(xs.max())
        for x in extra:
            neck_out[y, x] = src[y, left] if x < left else src[y, right]
    print("neck", bbox(neck_mask))

    in_collar = (yy >= 760) & (yy <= 960) & (xx >= 360) & (xx <= 920)
    lining = in_collar & (gray | (white & ~cat_head) | hoodie) & ~cat_head
    body_hole = in_collar & (body[:, :, 3] < 8) & opaque & ~cat_head
    near_lining = dilate(lining | body_hole, 3)
    outline = in_collar & dark & near_lining & ~cat_head
    collar_mask = close_mask(lining | body_hole | outline, 2)
    collar_mask = dilate(collar_mask, 2) & in_collar & ~cat_head & ~neck_core
    print("collar", bbox(collar_mask))

    # Hanging fringe only. Roots stay in the static crown / side-bangs so a
    # head turn does not open the hair hole above the forehead.
    center_box = (xx >= 515) & (xx <= 755) & (yy >= 468) & (yy <= 528)
    bangs_mask = dark & center_box & ~skin

    dist = ((xx - 650) / 205) ** 2 + ((yy - 640) / 220) ** 2
    annulus = dark & (dist > 0.62) & (dist < 1.78) & (yy >= 380) & (yy <= 875)
    crown = dark & (yy >= 350) & (yy <= 475) & (xx >= 420) & (xx <= 860)
    frame = dark & (
        ((yy >= 400) & (yy <= 545) & (xx >= 420) & (xx <= 535))
        | ((yy >= 400) & (yy <= 545) & (xx >= 735) & (xx <= 860))
    )
    side_mask = (annulus | crown | frame) & ~skin & ~cat
    bangs_mask &= ~side_mask
    print("bangs", bbox(bangs_mask))
    print("side-bangs", bbox(side_mask))

    save_rgba(LAYER_DIR / "neck.png", neck_out)
    save_rgba(LAYER_DIR / "collar.png", copy_src(src, collar_mask))
    save_rgba(LAYER_DIR / "bangs.png", copy_src(src, bangs_mask))
    save_rgba(LAYER_DIR / "side-bangs.png", copy_src(src, side_mask))
    save_rgba(LAYER_DIR / "cat.png", copy_src(src, cat))
    save_rgba(LAYER_DIR / "face.png", punch_dark(face, side_mask))
    save_rgba(LAYER_DIR / "face-angry.png", punch_dark(face_angry, side_mask))
    save_rgba(LAYER_DIR / "face-eyes-closed.png", punch_dark(face_closed, side_mask))

    for name in (
        "neck.png",
        "collar.png",
        "bangs.png",
        "side-bangs.png",
        "cat.png",
        "face.png",
        "face-angry.png",
        "face-eyes-closed.png",
    ):
        im = np.array(Image.open(LAYER_DIR / name).convert("RGBA"))
        zero_rgb = int(((im[:, :, 3] == 0) & (im[:, :, :3].sum(axis=2) > 0)).sum())
        print(name, bbox(im[:, :, 3] > 8), "zeroRGB", zero_rgb)
        assert im.shape[0] == H and im.shape[1] == W
        assert zero_rgb == 0

    neck_n = int((np.array(Image.open(LAYER_DIR / "neck.png"))[:, :, 3] > 8).sum())
    collar_n = int((np.array(Image.open(LAYER_DIR / "collar.png"))[:, :, 3] > 8).sum())
    assert neck_n >= 15000, neck_n
    assert collar_n >= 30000, collar_n
    neck_bb = bbox(np.array(Image.open(LAYER_DIR / "neck.png"))[:, :, 3] > 8)
    assert neck_bb is not None and neck_bb[3] >= 890, neck_bb


if __name__ == "__main__":
    main()
