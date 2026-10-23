#!/usr/bin/env python3
"""Print the repo's git remotes as QR codes.

GitHub SSH keys are per-machine, and not everyone has a working one. The
remotes are printed on the lab wall, so scanning the QR is faster than typing
a URL, and the HTTPS form works with no key at all.

Two outputs per remote:

* a small card (``docs/qr/remote_<name>.png``) -- the QR plus the URL and the
  ready-to-paste command, for the README and for chat;
* an A4 poster (``docs/qr/remote_<name>_poster.png``) -- the same thing at
  poster size, with the command and the SSH-key caveat spelled out, for the
  one that goes on the table.

Usage:
    python scripts/make_remote_qr.py                  # cards
    python scripts/make_remote_qr.py --poster         # cards + A4 posters
    python scripts/make_remote_qr.py --poster --remotes umn
    python scripts/make_remote_qr.py --out-dir /tmp
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# HTTPS on purpose: the umn-cse-mnri organization enforces SAML SSO, so an SSH
# key that is not authorized for the org is refused on it. A public repo needs
# no key at all over HTTPS.
REMOTES = {
    "umn": "https://github.com/umn-cse-mnri/so101_mnri.git",
    "origin": "https://github.com/thdhyan/so101_mnri.git",
}

# DejaVu ships with most Linux images and is the only font guaranteed to
# render the box-drawing/ASCII we use.
FONT_DIR = Path("/usr/share/fonts/truetype/dejavu")

GREY = (90, 90, 90)
LIGHT = (243, 243, 243)
INK = (20, 20, 20)
RED = (176, 0, 32)

# A4 portrait at 300 dpi.
POSTER_SIZE = (2480, 3508)
POSTER_DPI = 300


def _font(size: int, bold: bool = False):
    from PIL import ImageFont

    name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    path = FONT_DIR / name
    if path.exists():
        return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def _mono(size: int, bold: bool = False):
    from PIL import ImageFont

    name = "DejaVuSansMono-Bold.ttf" if bold else "DejaVuSansMono.ttf"
    path = FONT_DIR / name
    if path.exists():
        return ImageFont.truetype(str(path), size)
    return _font(size, bold)


def _wrap(draw, text: str, font, max_width: int) -> list[str]:
    """Greedy word wrap to `max_width` pixels."""
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if draw.textlength(candidate, font=font) <= max_width or not current:
            current = candidate
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


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


def _poster(name: str, url: str, out_path: Path) -> None:
    """Write an A4 poster for `url` -- this is the one that goes on the table."""
    import qrcode
    from PIL import Image, ImageDraw

    width, height = POSTER_SIZE
    margin = 220
    inner = width - 2 * margin

    title_font = _font(130, bold=True)
    sub_font = _font(58)
    url_font = _mono(62, bold=True)
    cmd_font = _mono(54)
    note_font = _font(46)
    foot_font = _font(42)

    # Draw onto a scratch canvas, then centre the whole block vertically so
    # the poster is not a strip of content with half a page of white below.
    scratch = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(scratch)

    def centre(text: str, font, y: int, fill=INK) -> int:
        draw.text(((width - int(draw.textlength(text, font=font))) // 2, y), text, font=font, fill=fill)
        return y + int(font.size * 1.35)

    top = 0
    y = top
    y = centre("SO-101 MNRI", title_font, y)
    y = centre("the organization repo - scan to clone", sub_font, y, GREY)
    y += 80

    qr = qrcode.make(url, box_size=24, border=4).convert("RGB")
    img_qr_x = (width - qr.width) // 2
    scratch.paste(qr, (img_qr_x, y))
    y += qr.height + 110

    y = centre(url, url_font, y, RED)
    y += 50

    cmd = f"git remote add {name} {url}"
    cmd_w = int(draw.textlength(cmd, font=cmd_font)) + 140
    box_h = int(cmd_font.size * 2.4)
    draw.rounded_rectangle(
        [(width - cmd_w) // 2, y, (width + cmd_w) // 2, y + box_h],
        radius=24,
        fill=LIGHT,
        outline=INK,
        width=3,
    )
    draw.text(((width - int(draw.textlength(cmd, font=cmd_font))) // 2, y + 40), cmd, font=cmd_font, fill=INK)
    y += box_h + 110

    note = (
        "HTTPS on purpose: the umn-cse-mnri organization enforces SAML SSO, so a GitHub "
        "SSH key is refused on it unless the key has been authorized for the organization. "
        "Over HTTPS a public repo needs no key at all - the URL is the whole credential for "
        "reading. Pushing still needs a token: use gh auth setup-git, or a PAT authorized "
        "for the organization."
    )
    for line in _wrap(draw, note, note_font, inner):
        draw.text((margin, y), line, font=note_font, fill=GREY)
        y += int(note_font.size * 1.4)

    footer = "umn-cse-mnri/so101_mnri"
    footer_y = y + 90
    draw.text(
        ((width - int(draw.textlength(footer, font=foot_font))) // 2, footer_y),
        footer,
        font=foot_font,
        fill=GREY,
    )
    content_bottom = footer_y + int(foot_font.size * 1.4)

    # Centre the block vertically so the poster is not a strip of content with
    # half a page of white below it.
    block = scratch.crop((0, 0, width, content_bottom))
    offset = max(0, (height - content_bottom) // 2)
    poster = Image.new("RGB", (width, height), "white")
    poster.paste(block, (0, offset))

    poster.save(out_path, dpi=(POSTER_DPI, POSTER_DPI))
    poster.save(out_path.with_suffix(".pdf"), "PDF", resolution=POSTER_DPI)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out-dir", default=str(REPO_ROOT / "docs" / "qr"), help="where to write the images")
    ap.add_argument("--scale", type=int, default=8, help="QR module size in pixels (card)")
    ap.add_argument("--poster", action="store_true", help="also write A4 posters (and their PDFs)")
    ap.add_argument("--remotes", nargs="*", choices=sorted(REMOTES), help="which remotes to render")
    args = ap.parse_args()

    try:
        import qrcode  # noqa: F401
        from PIL import Image  # noqa: F401
    except ImportError:
        print("needs `qrcode` and `pillow`: pip install 'qrcode[pil]'", file=sys.stderr)
        return 1

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    names = args.remotes or list(REMOTES)
    for name in names:
        url = REMOTES[name]
        card_path = out_dir / f"remote_{name}.png"
        _card(name, url, card_path, args.scale)
        print(f"{card_path}  <-  {url}")
        if args.poster:
            poster_path = out_dir / f"remote_{name}_poster.png"
            _poster(name, url, poster_path)
            print(f"{poster_path}  (A4 poster, {POSTER_DPI} dpi)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
