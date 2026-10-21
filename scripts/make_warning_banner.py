#!/usr/bin/env python3
"""Render the "do not recalibrate the arms" banner used at the top of the README.

Markdown cannot do red text on GitHub (inline styles are stripped), and the
failure this banner warns about -- the pose gate failing, or six servos
lunging against gravity -- presents as a flaky cable rather than as a bug, so
it needs to be impossible to miss. A PNG is the only thing that renders red.

Usage:
    python scripts/make_warning_banner.py
    python scripts/make_warning_banner.py --out /tmp/banner.png
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

TITLE = "DO NOT RECALIBRATE THE ARMS"
SUBTITLE = (
    "The calibration in robots/so101/calibration/ is verified for this rig. "
    "Recalibrating moves a zero point,\nthe arms stop agreeing in degrees, and the "
    "servos lunge against gravity on the first frame."
)

RED = (176, 0, 32)  # warning red, readable on white
INK = (60, 60, 60)
BORDER = 10

FONT_DIR = Path("/usr/share/fonts/truetype/dejavu")


def _font(size: int, bold: bool = False):
    from PIL import ImageFont

    name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    path = FONT_DIR / name
    if path.exists():
        return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def render(out_path: Path) -> None:
    from PIL import Image, ImageDraw

    title_font = _font(76, bold=True)
    sub_font = _font(32)

    probe = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    title_w = int(probe.textlength(TITLE, font=title_font))
    sub_w = max(int(probe.textlength(line, font=sub_font)) for line in SUBTITLE.split("\n"))

    width = max(title_w, sub_w) + 2 * 60
    height = 60 + title_font.size + 40 + 2 * int(sub_font.size * 1.5) + 50

    img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img)

    draw.rectangle([0, 0, width - 1, height - 1], outline=RED, width=BORDER)

    # The warning sign is in DejaVu Sans Bold (U+26A0); fall back to plain
    # text if the font on hand does not have it.
    sign = "\u26a0"
    try:
        sign_w = int(probe.textlength(sign, font=title_font))
    except Exception:  # pragma: no cover - defensive
        sign_w = 0

    x = (width - title_w) // 2
    y = 60
    draw.text((x, y), TITLE, font=title_font, fill=RED)
    if sign_w:
        draw.text((x - sign_w - 18, y), sign, font=title_font, fill=RED)
        draw.text((x + title_w + 18, y), sign, font=title_font, fill=RED)

    y += title_font.size + 40
    for line in SUBTITLE.split("\n"):
        draw.text(((width - int(probe.textlength(line, font=sub_font))) // 2, y), line, font=sub_font, fill=INK)
        y += int(sub_font.size * 1.5)

    img.save(out_path)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=str(REPO_ROOT / "images" / "do_not_recalibrate.png"))
    args = ap.parse_args()

    try:
        from PIL import Image, ImageDraw  # noqa: F401
    except ImportError:
        print("needs `pillow`: pip install pillow", file=sys.stderr)
        return 1

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    render(out_path)
    print(f"{out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
