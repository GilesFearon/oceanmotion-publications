#!/usr/bin/env python3
"""
Ocean Motion Analytics — "how the models are built" deck module.

Assembles the eight chain slides from the PNGs that make_model_chain.py renders.
All type is native PowerPoint text, not baked into the images, so a headline can
be reworded in the room on a Windows machine without rerunning Python on this
one. The cost is that two systems have to agree on geometry; LAYOUTS below is
the single place that agreement is written down.

Runs in the base environment (needs python-pptx). The figures run in
somisana_croco (needs cartopy + cmocean). The two never share an interpreter.

Usage:   python3 make_chain_deck.py [--layout wide|sidebar|both]
Output:  chain-module.pptx
"""

import argparse
import os

from pptx import Presentation
from pptx.util import Inches, Pt

import deckkit as dk
from deckkit import (ACCENT, CYAN, INK, INK_2, INK_3, PAPER, RULE,
                     F_BODY, F_DISPLAY, F_MONO, EMU_W, EMU_H, MARGIN)

ASSET = dk.ASSET_DIR

# The six links, in order. The rail is a "you are here", not a schematic: no
# arrows, no boxes. The real topology -- ERA5 feeding CROCO and WW3 in parallel,
# and the sediment model running offline after both -- is drawn once, properly,
# on the overview slide. A six-node graph does not survive reduction to 40 px.
RAIL = ["atmosphere", "boundaries", "grid", "circulation", "waves", "output"]


def rail(s, active, clock=None, on_light=True):
    """Progress rail across the top of every link slide."""
    x0, y = MARGIN, Inches(0.42)
    tick_w, gap = Inches(0.92), Inches(0.22)
    for i, label in enumerate(RAIL):
        x = x0 + i * (tick_w + gap)
        live = (i == active)
        dk.rect(s, x, y, tick_w, Pt(2.2), ACCENT if live else RULE)
        tf = dk.box(s, x, y + Inches(0.13), tick_w + gap, Inches(0.3))
        dk.run(tf.paragraphs[0], label, font=F_MONO, size=8,
               color=INK if live else INK_3, track=70, caps=True)
    if clock:
        tf = dk.box(s, EMU_W - MARGIN - Inches(3.2), y - Inches(0.02),
                    Inches(3.2), Inches(0.32))
        p = tf.paragraphs[0]
        p.alignment = 2  # right
        dk.run(p, clock, font=F_MONO, size=10, color=INK_2, track=60)


def specs(s, left, top, width, rows, head):
    """The technical column. Small, dense and unapologetic -- a modeller can read
    only these across the eight slides and know exactly what was built, while a
    non-technical reader's eye skips them without feeling talked down to."""
    dk.eyebrow(s, left, top, head, color=INK_2, w=width)
    tf = dk.box(s, left, top + Inches(0.42), width, Inches(3.0))
    for i, (k, v) in enumerate(rows):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_before = Pt(0 if i == 0 else 5)
        if k:
            dk.run(p, f"{k}  ", font=F_MONO, size=9, color=INK_3,
                   track=60, caps=True)
        dk.run(p, v, font=F_MONO, size=10, color=INK_2)
    return tf


def headline(s, left, top, width, lead, tail=None, size=38):
    tf = dk.box(s, left, top, width, Inches(1.9))
    p = tf.paragraphs[0]
    p.line_spacing = 1.02
    dk.run(p, lead, font=F_DISPLAY, size=size, color=INK)
    if tail:
        dk.run(p, tail, font=F_DISPLAY, size=size, color=ACCENT, italic=True)


def caption(s, left, top, width, text):
    tf = dk.box(s, left, top, width, Inches(0.6))
    dk.run(tf.paragraphs[0], text, font=F_BODY, size=13, color=INK_2,
           italic=True)


# ------------------------------------------------------------------ slides
def slide_waves(prs, layout):
    """Slide 6. Built first and in both layouts, because it is the plainest of
    the six link slides -- one map, one colorbar, one spec block. Whatever reads
    well here sets the pattern the other five inherit."""
    s = prs.slides.add_slide(prs.slide_layouts[6])

    spec_rows = [
        ("model", "WAVEWATCH III v6.07.1"),
        ("grid", "291 x 131, the CROCO mesh"),
        ("spectrum", "32 frequencies x 24 directions"),
        ("", ""),
        ("forced by", "ERA5 wind, 0.25 deg hourly"),
        ("", "CROCO surface currents + level"),
        ("", "25 CMEMS spectra at Hormuz"),
    ]
    cap = ("waves ride the currents we just solved — one-way, "
           "CROCO into WW3, never back")

    if layout == "wide":
        # No bg() here: bg and full_bleed both insert at spTree index 2, so
        # painting a ground first would bury the map under it. The 16:9 image
        # covers the slide, so it *is* the ground.
        dk.full_bleed(s, os.path.join(ASSET, "chain-6-waves-wide.png"))
        rail(s, 4, "21 Jan 2022  ·  14:00 UTC")
        headline(s, MARGIN, Inches(1.15), Inches(4.7),
                 "Waves ride the currents\nwe just ", "solved.")
        specs(s, MARGIN, Inches(3.05), Inches(4.4), spec_rows, "wave model")
        caption(s, MARGIN, Inches(6.82), Inches(8.0), cap)
    else:
        dk.bg(s, PAPER)
        img = os.path.join(ASSET, "chain-6-waves.png")
        h = Inches(6.15)
        w = int(h * 1.195)
        dk.picture(s, img, EMU_W - Inches(0.62) - w, Inches(1.02), height=h)
        rail(s, 4, "21 Jan 2022  ·  14:00 UTC")
        headline(s, MARGIN, Inches(1.35), Inches(3.6),
                 "Waves ride the\ncurrents we\njust ", "solved.", size=34)
        specs(s, MARGIN, Inches(4.15), Inches(3.7), spec_rows, "wave model")
        caption(s, MARGIN, Inches(6.82), Inches(11.5), cap)
    return s


def build(layouts):
    prs = Presentation()
    prs.slide_width, prs.slide_height = EMU_W, EMU_H
    dk.set_theme_fonts(prs)
    for lay in layouts:
        slide_waves(prs, lay)
    dk.embed_fonts(prs)
    out = os.path.join(dk.HERE, "chain-module.pptx")
    prs.save(out)
    print(f"wrote {out} — {len(prs.slides._sldIdLst)} slide(s): {', '.join(layouts)}")
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--layout", default="both",
                    choices=["wide", "sidebar", "both"])
    a = ap.parse_args()
    build(["wide", "sidebar"] if a.layout == "both" else [a.layout])
