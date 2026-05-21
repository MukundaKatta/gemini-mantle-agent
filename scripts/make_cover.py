"""Generate the DoraHacks submission cover image (1200x675, 16:9 thumb).

Reuses the same palette + typography as the intro slide so the cover and
the demo video read as one set.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


W, H = 1200, 675
FG = "#0f172a"
FG_MUTED = "#475569"
ACCENT = "#14b8a6"      # Mantle teal
ACCENT_2 = "#0f766e"
BG = "#ffffff"
PANEL = "#f8fafc"

SF = "/System/Library/Fonts/SFNS.ttf"
SFI = "/System/Library/Fonts/SFNSItalic.ttf"
MONO = "/System/Library/Fonts/SFNSMono.ttf"
if not Path(MONO).exists():
    MONO = "/System/Library/Fonts/Menlo.ttc"


def font(size, mono=False, italic=False):
    path = MONO if mono else (SFI if italic else SF)
    return ImageFont.truetype(path, size)


def main():
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    # Footer band
    d.rectangle([(0, H - 40), (W, H)], fill=PANEL)
    d.text((24, H - 32),
           "github.com/MukundaKatta/gemini-mantle-agent",
           font=font(16), fill=FG_MUTED)
    d.text((W - 200, H - 32), "Apache 2.0", font=font(16), fill=FG_MUTED)

    # Title block
    d.text((60, 100), "gemini-mantle-agent", font=font(72), fill=FG)
    d.rectangle([(60, 200), (220, 208)], fill=ACCENT)

    d.text((60, 240),
           "On-chain queries on Mantle.",
           font=font(28), fill=FG_MUTED)
    d.text((60, 280),
           "Verbatim block state, TVL, and tx hashes.",
           font=font(28), fill=FG_MUTED)

    d.text((60, 380),
           "Gemini 2.5 ADK + Mantle MCP",
           font=font(24, mono=True), fill=ACCENT_2)
    d.text((60, 420),
           "(block height + protocol TVL + contract reads + tx receipts)",
           font=font(20), fill=FG_MUTED)

    d.text((60, 520),
           "DoraHacks Mantle Turing Test 2026",
           font=font(22), fill=FG)
    d.text((60, 552),
           "deadline 2026-06-15 · $100K prize pool",
           font=font(20), fill=FG_MUTED)

    out = Path("/Users/ubl/gemini-mantle-agent/.video-build/cover.png")
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out, "PNG", optimize=True)
    size = out.stat().st_size / 1024
    print(f"DONE: {out} ({size:.1f} KB)")


if __name__ == "__main__":
    main()
