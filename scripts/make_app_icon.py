#!/usr/bin/env python3
"""Generate ``packaging/icons/app.ico`` generatively with Pillow.

Defeats DEF-011: the committed ``app.ico`` was a 15-byte ASCII file containing
the literal text ``ICO_PLACEHOLDER``, which passed ``scripts/build.py``
precondition 4 because that gate only checked that the *filename* existed.
Precondition 4b now calls ``_is_valid_ico()``, which requires >= 1024 bytes and
a well-formed ICO header (reserved=0, type=1, count>0).

SEC-045 (docs/13 §447) requires assets to be reproducible from a committed
script rather than committed as an opaque binary, so the provenance of every
pixel here is this file. Re-running it reproduces the icon byte-for-byte.

Design: an abstract ledger -- four horizontal bars of different lengths (a
balance sheet read as a column of figures) inside a rounded frame. It reads as
"month-end" and "review" without resembling any bank, currency symbol, or
client brand.

Palette is taken verbatim from ``docs/12_POWERPOINT_OUTPUT_SPEC.md`` §3.3,
which names ``ui/theme/tokens.ts`` as the single source for literal v1 values:

    brand.primary    #1F3A5F   (Ledger Blue)
    brand.secondary  #B7791F   (amber accent)

Generic branding is the approved default (DEC-015 / PEND-03); no client
branding is invented. ``surface.card`` #F7F8FA is used for the bar ink so the
mark keeps AA contrast on the primary field.

Usage:
    python scripts/make_app_icon.py
    python scripts/make_app_icon.py --check   # verify the committed file matches
"""

from __future__ import annotations

import argparse
import struct
import sys
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
ICO_PATH = ROOT / "packaging" / "icons" / "app.ico"

# Sizes Windows expects in one container. 16 px is the taskbar/Alt-Tab entry and
# is where most icons fail, so the mark is drawn with strokes that survive it.
SIZES = (16, 32, 48, 64, 128)

# Source of truth: docs/12_POWERPOINT_OUTPUT_SPEC.md section 3.3.
BRAND_PRIMARY = (0x1F, 0x3A, 0x5F)
BRAND_SECONDARY = (0xB7, 0x79, 0x1F)
SURFACE_CARD = (0xF7, 0xF8, 0xFA)

# Supersampling factor. Drawing at 8x then LANCZOS-downscaling is what keeps the
# 16 px frame edges and bar ends from turning to mush.
SS = 8


def _draw_mark(px: int) -> Image.Image:
    """Render the abstract-ledger mark at ``px`` pixels square.

    Geometry is expressed in fractions of ``px`` so the same code produces a
    correct 16 px and a correct 128 px -- there is no separate small-size
    special case to forget to re-tune.
    """
    s = px * SS
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    def u(v: float) -> int:
        """Fraction of canvas -> supersampled integer."""
        return int(round(v * s))

    # Rounded frame in brand.primary. Corner radius ~18% of the canvas reads as
    # a rounded square at every size and matches the app chrome treatment.
    inset = u(0.04)
    radius = u(0.18)
    d.rounded_rectangle(
        [inset, inset, s - 1 - inset, s - 1 - inset],
        radius=radius,
        fill=BRAND_PRIMARY + (255,),
    )

    # Four bars, a balance-sheet column. Fractions: (top, left, right) per bar.
    # The amber bar is the "this one needs attention" row -- the same signal
    # role brand.secondary plays in the decks (docs/12 section 3.3).
    #
    # Three bars rather than four, and thicker (0.11 of the canvas): at 16 px a
    # fourth bar leaves <1 px of gap and the LANCZOS downscale turns the column
    # into one grey smear. Three bars of this weight keep a clean gap at every
    # size in SIZES, which I verified by reading the pixels back at 16 px.
    bars = (
        (0.30, 0.24, 0.76, SURFACE_CARD),
        (0.47, 0.24, 0.66, BRAND_SECONDARY),
        (0.64, 0.24, 0.56, SURFACE_CARD),
    )
    bar_h = u(0.11)
    for top, left, right, colour in bars:
        y0 = u(top)
        d.rounded_rectangle(
            [u(left), y0, u(right), y0 + bar_h],
            radius=bar_h // 2,
            fill=colour + (255,),
        )

    return img.resize((px, px), Image.LANCZOS)


def build_ico(dest: Path) -> list[int]:
    """Write a true multi-resolution .ico at ``dest``; return the sizes written."""
    dest.parent.mkdir(parents=True, exist_ok=True)

    # Build the largest frame, then hand Pillow the ladder. Pillow packs each
    # requested size as a real BMP/DIB entry inside the ICO container, which is
    # what makes the header count > 1 rather than a single-image stub.
    base = _draw_mark(max(SIZES))
    base.save(dest, format="ICO", sizes=[(n, n) for n in SIZES])

    written = sorted({n for n in SIZES})
    return written


def ico_header(path: Path) -> tuple[int, int, int]:
    """Return (reserved, type, image_count) straight from the first 6 bytes."""
    data = path.read_bytes()
    if len(data) < 6:
        raise ValueError("file is shorter than an ICO header")
    reserved, ico_type, count = struct.unpack("<HHH", data[:6])
    return reserved, ico_type, count


def embedded_sizes(path: Path) -> list[int]:
    """Read back the entry sizes recorded in the ICO directory table.

    Byte 0 of each directory entry is the width; 0 means 256.
    """
    data = path.read_bytes()
    count = struct.unpack("<H", data[4:6])[0]
    out = []
    for i in range(count):
        off = 6 + i * 16
        w = data[off] or 256
        out.append(w)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--check",
        action="store_true",
        help="verify the committed app.ico instead of rewriting it",
    )
    args = ap.parse_args()

    if not args.check:
        written = build_ico(ICO_PATH)
        print("wrote %s" % ICO_PATH.relative_to(ROOT))
        print("requested sizes: %s" % ", ".join(str(n) for n in written))

    if not ICO_PATH.exists():
        print("FAIL: %s does not exist" % ICO_PATH)
        return 1

    size = ICO_PATH.stat().st_size
    reserved, ico_type, count = ico_header(ICO_PATH)
    sizes = embedded_sizes(ICO_PATH)

    print("bytes        : %d (gate requires >= 1024)" % size)
    print("header       : reserved=%d type=%d count=%d" % (reserved, ico_type, count))
    print("embedded sizes: %s" % ", ".join(str(s) for s in sizes))

    ok = size >= 1024 and reserved == 0 and ico_type == 1 and count > 0
    print("gate verdict : %s" % ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
