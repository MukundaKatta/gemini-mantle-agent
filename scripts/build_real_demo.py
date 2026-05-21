"""Build the final gemini-mantle-agent demo video.

Composition:
  - ~14s intro slide with TTS narration
  - ~32s real Cloud Run footage (already captured at .video-build/real_footage.mp4)
  - ~11s outro slide with TTS narration

Total ~60s, well under the DoraHacks submission limit. Centerpiece is
real footage of the deployed Streamlit dashboard answering "What's TVL
on Agni Finance right now and the most recent deposit to the WMNT
contract?" by walking the Mantle MCP tools (get_block_height +
get_protocol_tvl + query_contract + get_transaction) and citing
verbatim quotes — block height, TVL number, WMNT address, tx hash.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


W, H = 1920, 1080
FG = "#0f172a"
FG_MUTED = "#475569"
ACCENT = "#14b8a6"          # Mantle teal
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


def draw_intro(img, d):
    d.rectangle([(0, 0), (W, H)], fill=BG)
    d.rectangle([(0, H - 56), (W, H)], fill=PANEL)
    d.text((48, H - 44),
           "github.com/MukundaKatta/gemini-mantle-agent",
           font=font(22), fill=FG_MUTED)
    d.text((W - 270, H - 44), "Apache 2.0", font=font(22), fill=FG_MUTED)
    d.text((96, 220), "gemini-mantle-agent", font=font(108), fill=FG)
    d.rectangle([(96, 360), (340, 372)], fill=ACCENT)
    d.text((96, 410),
           "Plain-English questions about Mantle chain state",
           font=font(40), fill=FG_MUTED)
    d.text((96, 470),
           "with verbatim block height, TVL, and tx hashes.",
           font=font(40), fill=FG_MUTED)
    d.text((96, 600),
           "DoraHacks Mantle Turing Test 2026",
           font=font(32), fill=FG)
    d.text((96, 645),
           "· deadline 2026-06-15 · $100K pool ·",
           font=font(32), fill=FG_MUTED)
    d.text((96, 760),
           "What follows is real footage of the deployed",
           font=font(28, italic=True), fill=FG_MUTED)
    d.text((96, 800),
           "Cloud Run dashboard walking a Mantle MCP server.",
           font=font(28, italic=True), fill=FG_MUTED)


def draw_outro(img, d):
    d.rectangle([(0, 0), (W, H)], fill=BG)
    d.text((96, 180), "gemini-mantle-agent", font=font(72), fill=FG)
    d.rectangle([(96, 280), (340, 292)], fill=ACCENT)
    d.text((96, 330),
           "github.com/MukundaKatta/gemini-mantle-agent",
           font=font(30, mono=True), fill=ACCENT_2)
    d.text((96, 410),
           "gemini-mantle-agent-1029931682737.us-central1.run.app",
           font=font(28, mono=True), fill=ACCENT_2)
    d.text((96, 540),
           "Google Cloud Agent Builder (ADK)",
           font=font(32), fill=FG_MUTED)
    d.text((96, 590),
           "+ Gemini 2.5 Flash on Vertex AI",
           font=font(32), fill=FG_MUTED)
    d.text((96, 640),
           "+ Mantle MCP (block height, TVL, contracts, tx)",
           font=font(32), fill=FG_MUTED)
    d.text((96, 760),
           "Every number in this demo is byte-for-byte from",
           font=font(26, italic=True), fill=FG_MUTED)
    d.text((96, 800),
           "a Mantle MCP tool call. No paraphrasing.",
           font=font(26, italic=True), fill=FG_MUTED)
    d.text((96, 870),
           "Apache 2.0. Mukunda Katta, independent.",
           font=font(28, italic=True), fill=FG_MUTED)


INTRO_NARRATION = (
    "Gemini Mantle agent. An on-chain analyst on Google Cloud Agent "
    "Builder, wired to a Mantle M C P server. Submission for the "
    "DoraHacks Mantle Turing Test 2026. What follows is real footage "
    "of the deployed Cloud Run dashboard walking the Mantle tools and "
    "quoting block height, T V L, and transaction hashes byte for byte."
)


OUTRO_NARRATION = (
    "Every number you just saw was copied byte for byte from a Mantle "
    "M C P tool call. The agent never paraphrases on chain values. "
    "Built on the A D K with Gemini two point five Flash, wired to a "
    "Mantle M C P server. Apache two point zero. Thank you."
)


def render_slide(name, draw_fn, outdir):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    draw_fn(img, d)
    p = outdir / f"{name}.png"
    img.save(p, "PNG", optimize=True)
    return p


def say_to_m4a(text, outpath):
    aiff = outpath.with_suffix(".aiff")
    subprocess.run(
        ["say", "-v", "Samantha", "-r", "175", "-o", str(aiff), text],
        check=True,
    )
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-i", str(aiff),
         "-c:a", "aac", "-b:a", "128k", str(outpath)],
        check=True,
    )
    aiff.unlink(missing_ok=True)


def make_slide_segment(png, m4a, out):
    dur = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(m4a)],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    seg_dur = float(dur) + 0.5
    subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error",
        "-loop", "1", "-i", str(png),
        "-i", str(m4a),
        "-af", "apad=pad_dur=0.5",
        "-c:v", "libx264", "-tune", "stillimage", "-pix_fmt", "yuv420p",
        "-r", "30", "-t", f"{seg_dur:.2f}",
        "-c:a", "aac", "-b:a", "128k",
        "-shortest", str(out),
    ], check=True)
    return out, seg_dur


def main():
    outdir = Path("/Users/ubl/gemini-mantle-agent/.video-build")
    outdir.mkdir(parents=True, exist_ok=True)

    real = outdir / "real_footage.mp4"
    if not real.exists():
        sys.exit(f"missing real footage at {real}; run record_real_demo.py first")

    for needed in ("ffmpeg", "ffprobe", "say"):
        if shutil.which(needed) is None:
            sys.exit(f"missing tool: {needed}")

    print("[1/4] slides...")
    intro_png  = render_slide("01_intro",  draw_intro,  outdir)
    outro_png  = render_slide("99_outro",  draw_outro,  outdir)
    print(f"  rendered {intro_png.name}")
    print(f"  rendered {outro_png.name}")

    print("[2/4] audio...")
    intro_m4a = outdir / "01_intro.m4a"
    outro_m4a = outdir / "99_outro.m4a"
    say_to_m4a(INTRO_NARRATION, intro_m4a)
    print(f"  spoke {intro_m4a.name}")
    say_to_m4a(OUTRO_NARRATION, outro_m4a)
    print(f"  spoke {outro_m4a.name}")

    print("[3/4] segments...")
    intro_seg, intro_dur = make_slide_segment(intro_png, intro_m4a, outdir / "seg_01_intro.mp4")
    outro_seg, outro_dur = make_slide_segment(outro_png, outro_m4a, outdir / "seg_99_outro.mp4")
    real_dur = float(subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(real)],
        capture_output=True, text=True, check=True,
    ).stdout.strip())
    print(f"  intro {intro_dur:.1f}s · real {real_dur:.1f}s · outro {outro_dur:.1f}s")

    print("[4/4] concat...")
    list_file = outdir / "concat.txt"
    list_file.write_text("\n".join([
        f"file '{intro_seg.resolve()}'",
        f"file '{real.resolve()}'",
        f"file '{outro_seg.resolve()}'",
    ]) + "\n")

    final = outdir / "demo.mp4"
    subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error",
        "-f", "concat", "-safe", "0", "-i", str(list_file),
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "30",
        "-c:a", "aac", "-b:a", "128k",
        str(final),
    ], check=True)

    size_mb = final.stat().st_size / (1024 * 1024)
    dur = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(final)],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    print(f"\nDONE: {final}  ({size_mb:.1f} MB, {float(dur):.1f}s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
