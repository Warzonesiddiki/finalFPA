#!/usr/bin/env python3
"""
Generate the Windows multi-size `app.ico` and a PNG ladder from `logo-mark.svg`.

WHY THIS EXISTS
---------------
The brand master is `logo-mark.svg` (resolution-independent, inspectable, reviewable).
Windows does not consume SVG, so something has to rasterise it. Rather than commit an
opaque binary that nobody can review and nobody can regenerate, the build step is
committed instead. `app.ico` is therefore a BUILD ARTEFACT, not a source file -
which also satisfies `docs/13` `SEC-045` (no unreviewed binaries in the repo) far
better than checking in a hand-made binary would.

USAGE
-----
    pip install cairosvg pillow
    python make_icons.py

OUTPUT
------
    app.ico                 multi-size Windows icon container
    out/app-icon-16.png     ...and the ladder, for HTML <link rel="icon"> and docs
    out/app-icon-24.png
    out/app-icon-32.png
    out/app-icon-48.png
    out/app-icon-64.png
    out/app-icon-128.png
    out/app-icon-256.png
    out/ICON-BUILD.txt      the input SHA-256 and the sizes packed, for the release notes

WHY THESE SIZES
---------------
    16     taskbar, Alt-Tab, title bar. The size most icons fail at.
    24     small Explorer views, some shell surfaces.
    32     Explorer medium icons, Alt-Tab preview.
    48     Explorer large icons, 150% DPI scaling.
    64     high-DPI shell surfaces.
    128    large-icon views, some shortcut stacks.
    256    Explorer icon size (Pillow's maximum ICO entry); what the installer ships.

A single 256px image stuffed into an .ico is the usual cause of a blurry taskbar.
Windows picks the nearest entry, so all seven have to be present.

WIRING (lead's edit - these files are not mine to touch)
------------------------------------------------------
    packaging/pyinstaller.spec    icon='branding/out/app-256.png' on EXE(...)/BINARY(...)
    packaging/installer.iss       [Setup] SetupIconFile=branding\out\app-256.png
    pywebview window              create_window(..., icon='branding/out/app-256.png')
    ui/index.html                 <link rel="icon" href="...app-icon-32.png">

VERIFY AFTER GENERATING
-----------------------
    1. Compare every packed image against logo-mark.svg by eye at 100%.
    2. At 16px, all four bars must still read as four distinct bars. If any merge,
       the strokes in logo-mark.svg are too thin - thicken them there, not here.
    3. Confirm `out/ICON-BUILD.txt` records the input hash; quote that hash in the
       release notes so the shipped icon is traceable to a reviewed SVG.
"""

from __future__ import annotations

import hashlib
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE_SVG = HERE / "logo-mark.svg"
OUT_DIR = HERE / "out"
ICO_PATH = HERE / "app.ico"

# Order matters: Pillow packs them in the order given, and Windows conventionally
# stores the 256px entry last.
SIZES = [16, 24, 32, 48, 64, 128, 256]


def die(msg: str) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def render(svg: Path, size: int, out_png: Path) -> None:
    """Rasterise the SVG master to a PNG of the given square size."""
    try:
        import cairosvg
    except ImportError as exc:
        die(
            "cairosvg is required: pip install cairosvg\n"
            f"(import failed: {exc})"
        )

    # transparent background: Windows icons composite onto whatever is behind them.
    # cairosvg's default background is transparent, so nothing to override here.
    cairosvg.svg2png(
        url=str(svg),
        write_to=str(out_png),
        output_width=size,
        output_height=size,
    )


def main() -> int:
    if not SOURCE_SVG.exists():
        die(f"source master not found: {SOURCE_SVG}")

    try:
        from PIL import Image
    except ImportError as exc:
        die(f"Pillow is required: pip install pillow\n(import failed: {exc})")

    source_hash = sha256(SOURCE_SVG)
    print(f"Source master : {SOURCE_SVG.name}")
    print(f"Source SHA-256: {source_hash}")
    print(f"Sizes         : {', '.join(str(s) for s in SIZES)}")
    print()

    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    OUT_DIR.mkdir(parents=True)

    pngs: list[Path] = []
    for size in SIZES:
        png = OUT_DIR / f"app-icon-{size}.png"
        render(SOURCE_SVG, size, png)
        actual = Image.open(png)
        if actual.size != (size, size):
            die(f"renderer produced {actual.size}, expected ({size}, {size}) for {png.name}")
        # Force RGBA so Pillow does not emit a paletted PNG, which some shell
        # surfaces render with a hard edge instead of antialiasing.
        actual.convert("RGBA").save(png)
        pngs.append(png)
        print(f"  rendered  {png.name:<22} {size}x{size}")

    # Pack every size into ONE .ico container.
    images = [Image.open(p).convert("RGBA") for p in pngs]
    images[0].save(
        ICO_PATH,
        format="ICO",
        sizes=[(s, s) for s in SIZES],
        append_images=images[1:],
    )

    # Verify the container actually carries all seven entries - a silently
    # downsampled .ico is exactly the bug this script exists to prevent.
    with Image.open(ICO_PATH) as ico:
        packed = sorted({s for s in ico.info.get("sizes", [])})
    expected = sorted({(s, s) for s in SIZES})
    if packed != expected:
        die(f"ICO container is incomplete. packed={packed} expected={expected}")
    if ICO_PATH.stat().st_size > 256 * 1024:
        print(
            f"  note: {ICO_PATH.name} is {ICO_PATH.stat().st_size / 1024:.0f} KB. "
            "Pillow stores ICO entries as uncompressed BMP. If the installer payload "
            "budget matters, re-encode the entries as PNG (see note in "
            "packaging/pyinstaller.spec)."
        )

    # Traceability record for the release notes.
    (OUT_DIR / "ICON-BUILD.txt").write_text(
        "FP&A Month-End Copilot - icon build record\n"
        "========================================\n"
        f"source          : {SOURCE_SVG.name}\n"
        f"source SHA-256  : {source_hash}\n"
        f"sizes packed    : {', '.join(str(s) for s in SIZES)}\n"
        f"app.ico bytes   : {ICO_PATH.stat().st_size}\n"
        f"generator       : make_icons.py (cairosvg + Pillow)\n\n"
        "Quote the source SHA-256 above in the release notes so the shipped icon\n"
        "is traceable to a reviewed SVG master.\n",
        encoding="utf-8",
    )

    print()
    print(f"Wrote {ICO_PATH}  ({ICO_PATH.stat().st_size} bytes, {len(expected)} sizes)")
    print(f"Wrote {OUT_DIR}/  ({len(pngs)} PNGs + ICON-BUILD.txt)")
    print()
    print("Now do the visual check described in this file's docstring, then wire the")
    print("icon into packaging/pyinstaller.spec, packaging/installer.iss and the")
    print("pywebview window. See the docstring for the exact settings.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())