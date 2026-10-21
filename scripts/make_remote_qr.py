#!/usr/bin/env python3
"""Print the repo's git remotes as QR codes.

GitHub SSH keys are per-machine, and not everyone has a working one. The
remotes are printed on the lab wall, so scanning the QR is faster than typing
a URL, and the HTTPS form works with no key at all.

The card carries the URL *and* the ready-to-paste command, so it works for
someone who scans it with a phone and for someone who just reads it.

Usage:
    python scripts/make_remote_qr.py                 # -> docs/qr/*.png
    python scripts/make_remote_qr.py --out-dir /tmp
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# HTTPS on purpose: an SSH clone needs a GitHub key on the machine doing the
# clone, and a public repo does not need one over HTTPS.
REMOTES = {
    "umn": "https://github.com/umn-cse-mnri/so101_mnri.git",
    "origin": "https://github.com/thdhyan/so101_mnri.git",
}

# DejaVu ships with most Linux images and is the only font guaranteed to
# render the box-drawing/ASCII we use.
FONT_DIR = Path("/usr/share/fonts/truetype/dejavu")


def _font(size: int, bold: bool = False):
    from PIL import ImageFont

    name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    path = FONT_DIR / name
    if path.exists():
        return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def _card(name: str, url: str, out_path: Path, scale: int) -> None:
    """Write a QR code for `url` with the remote name and command under it."""
    import qrcode
    from PIL import Image, ImageDraw

    qr = qrcode.make(url, box_size=scale, border=2).convert("RGB")

    pad = 20
    title_font = _font(30, bold=True)
    body_font = _font(22)
    cmd_font = _font(20)

    title = f"git remote add {name}"
    cmd = f"git remote add {name} {url}"
    lines = [title, url, cmd]

    widths = []
    for line, font in zip(lines, (title_font, body_font, cmd_font)):
        widths.append(int(ImageDraw.Draw(Image.new("RGB", (1, 1))).textlength(line, font=font)))

    text_w = max(max(widths), qr.width)
    text_h = sum(
        int(font.size * 1.45)
        for font in (title_font, body_font, cmd_font)
    )

    img = Image.new("RGB", (text_w + 2 * pad, qr.height + text_h + 3 * pad), "white")
    draw = ImageDraw.Draw(img)

    # QR, centred over the text block.
    img.paste(qr, ((img.width - qr.width) // 2, pad))

    y = pad + qr.height + pad
    for line, font, colour in zip(
        lines,
        (title_font, body_font, cmd_font),
        ("black", "black", "#b00020"),
    ):
        draw.text((pad, y), line, font=font, fill=colour)
        y += int(font.size * 1.45)

    img.save(out_path)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out-dir", default=str(REPO_ROOT / "docs" / "qr"), help="where to write the PNGs")
    ap.add_argument("--scale", type=int, default=8, help="QR module size in pixels (print scale)")
    args = ap.parse_args()

    try:
        import qrcode  # noqa: F401
        from PIL import Image  # noqa: F401
    except ImportError:
        print("needs `qrcode` and `pillow`: pip install 'qrcode[pil]'", file=sys.stderr)
        return 1

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    for name, url in REMOTES.items():
        out_path = out_dir / f"remote_{name}.png"
        _card(name, url, out_path, args.scale)
        print(f"{out_path}  <-  {url}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
