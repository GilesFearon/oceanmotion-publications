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
import json
import os

from pptx import Presentation
from pptx.util import Inches, Pt

import deckkit as dk
from deckkit import (ACCENT, CYAN, INK, INK_2, INK_3, NAVY, PAPER, RULE,
                     F_BODY, F_DISPLAY, F_MONO, EMU_W, EMU_H, MARGIN)

ASSET = dk.ASSET_DIR


def anchors(name):
    """Feature positions a figure reported, in image fractions.

    Labels are slide text so they stay editable, but they still have to land on
    the right feature. The figure writes where things ended up; this reads it,
    so the two cannot drift apart when a figure is retuned."""
    path = os.path.join(ASSET, f"chain-{name}.anchors.json")
    with open(path) as fh:
        return json.load(fh)


def at(img_left, img_top, img_w, img_h, ax, ay):
    """Image-fraction anchor -> slide EMU."""
    return dk._emu(img_left + ax * img_w), dk._emu(img_top + ay * img_h)


def label(s, x, y, text, size=10.5, color=INK, font=F_BODY, align=2,
          w=Inches(3.0), bold=False):
    """A centred one-line label placed by its centre point."""
    tf = dk.box(s, x - w / 2, y, w, Inches(0.30))
    p = tf.paragraphs[0]
    p.alignment = align
    dk.run(p, text, font=font, size=size, color=color, bold=bold)
    return tf

# The six links, in order. The rail is a "you are here", not a schematic: no
# arrows, no boxes. The real topology -- ERA5 feeding CROCO and WW3 in parallel,
# and the sediment model running offline after both -- is drawn once, properly,
# on the overview slide. A six-node graph does not survive reduction to 40 px.
RAIL = ["atmosphere", "boundaries", "grid", "circulation", "waves",
        "turbidity"]


def rail(s, active, clock=None, on_light=True):
    """Progress rail across the top of every link slide.

    active=-1 lights every tick, for the closing reprise where the whole chain
    has been walked. active=None lights none, for the opener."""
    x0, y = MARGIN, Inches(0.42)
    tick_w, gap = Inches(0.92), Inches(0.22)
    for i, label in enumerate(RAIL):
        x = x0 + i * (tick_w + gap)
        live = (active == -1) or (i == active)
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


# ------------------------------------------------------------------ content
# One entry per link slide. Everything a slide says lives here, so rewording is
# a one-line edit rather than a hunt through layout code -- which is the point
# of keeping the type native rather than baking it into the PNGs.
SLIDES = [
    dict(n=2, rail=0, img="chain-2-atmosphere.png",
         clock="21 Jan 2022  ·  08:00 UTC",
         lead="We start with weather\nanyone can ", tail="audit.",
         head="atmospheric forcing",
         # Both chains, side by side: the same four forcing slots, different
         # products. A buyer asking "and what about tomorrow?" is answered on
         # the slide rather than in the room.
         specs=[("", "hindcast          forecast"),
                ("wind", "ERA5              GFS"),
                ("", "0.25 deg hourly   0.25 deg 3-hourly"),
                ("", ""),
                ("ocean", "GLORYS            MERCATOR"),
                ("tide", "TPXO10            TPXO10"),
                ("waves", "CMEMS spectra     CMEMS WAV")],
         cap="public, global, and honestly coarse — the same four inputs drive "
             "the hindcast and the daily forecast"),

    dict(n=6, rail=4, img="chain-6-waves.png", side="chain-6a-hs.png",
         clock="21 Jan 2022  ·  14:00 UTC",
         lead="Waves ride the currents\nwe just ", tail="solved.",
         head="wave model",
         specs=[("model", "WAVEWATCH III v6.07.1"),
                ("grid", "291 x 131, the CROCO mesh"),
                ("spectrum", "32 frequencies x 24 dir"),
                ("forced by", "ERA5 wind + CROCO currents"),
                ("", "25 CMEMS spectra at Hormuz")],
         cap="one-way, CROCO into WW3, never back — and checked against 26 000 "
             "altimeter passes"),
]

BOOKENDS = dict(
    closer=dict(rail=-1, img="chain-8-cascade.gif", aspect=2.26,
                lead="One storm, all\nthe way ", tail="through.",
                clock=None,
                cap="the traces are the marked site: wind at midday, waves "
                    "within the hour, the plume at the surface by eleven"),
)


# ------------------------------------------------------------------ slides
def overview(prs):
    """Slide 1, built as native shapes rather than one flat image.

    Boxes, arrows and labels are all separate PowerPoint objects, so the diagram
    can be nudged, relabelled or re-coloured in the room; only the thumbnails
    inside the boxes come from the figure module. The topology is the real one:
    ERA5 forces CROCO and WW3 in parallel, CROCO feeds WW3 one way, and the
    sediment model runs offline after both -- drawn across a dashed seam,
    because it is a post-process, not a coupled component."""
    s = prs.slides.add_slide(prs.slide_layouts[6])
    dk.bg(s, PAPER)
    headline(s, MARGIN, Inches(0.72), Inches(5.2), "Five models,\none ", "chain.")

    # --- inputs, as a plain list down the left
    ix = MARGIN
    dk.eyebrow(s, ix, Inches(2.62), "inputs", color=INK_2, w=Inches(3))
    inputs = [("ERA5  /  GFS", "0.25 deg  ·  hourly", 3.16),
              ("GLORYS  /  MERCATOR", "1/12 deg  ·  daily", 3.78),
              ("TPXO10", "10 tidal constituents", 4.40),
              ("CMEMS spectra", "25 points at Hormuz", 5.02),
              ("grid 291 x 131", "3.5 km  ·  15 levels  ·  shared", 5.64)]
    for name, sub, y in inputs:
        tf = dk.box(s, ix, Inches(y), Inches(3.3), Inches(0.26))
        dk.run(tf.paragraphs[0], name, font=F_BODY, size=11, color=INK)
        tf = dk.box(s, ix, Inches(y + 0.235), Inches(3.3), Inches(0.24))
        dk.run(tf.paragraphs[0], sub, font=F_MONO, size=8, color=INK_3)

    # --- the two models, and the offline step
    # No per-node captions: at this width a box is narrower than its own name,
    # and a second label collides with the title of the box below it. The specs
    # live on the link slides.
    bw, bh = Inches(2.05), Inches(1.52)
    cx, wx, tx = Inches(4.95), Inches(4.95), Inches(9.55)
    cy, wy, ty = Inches(2.86), Inches(5.14), Inches(4.00)
    dk.node_box(s, cx, cy, bw, bh, os.path.join(ASSET, "chain-5-circulation.png"),
                "CROCO")
    dk.node_box(s, wx, wy, bw, bh, os.path.join(ASSET, "chain-6-waves.png"),
                "WAVEWATCH III")
    dk.node_box(s, tx, ty, bw, bh, os.path.join(ASSET, "chain-7-turbidity.png"),
                "sediment model")

    # ERA5 is the only input that forces both models, and drawing that is the
    # whole reason this slide is a graph rather than a chain.
    ex = ix + Inches(3.45)
    dk.arrow(s, ex, Inches(3.28), cx - Inches(0.06), Inches(3.34))
    dk.arrow(s, ex, Inches(3.34), wx - Inches(0.06), Inches(5.62))
    dk.arrow(s, ex, Inches(3.90), cx - Inches(0.06), Inches(3.68))
    dk.arrow(s, ex, Inches(4.52), cx - Inches(0.06), Inches(4.02))
    dk.arrow(s, ex, Inches(5.14), wx - Inches(0.06), Inches(5.94))

    # CROCO -> WW3, one way
    mid = dk._emu(cx + bw / 2)
    dk.arrow(s, mid, cy + bh + Inches(0.06), mid, wy - Inches(0.32),
             color=INK_2, width=Pt(1.8))
    tf = dk.box(s, mid + Inches(0.16), Inches(4.58), Inches(3.6), Inches(0.26))
    dk.run(tf.paragraphs[0], "surface currents + water level", font=F_MONO,
           size=8.5, color=INK_2)

    # the offline seam
    sx = Inches(8.62)
    for k in range(12):
        dk.rect(s, sx, Inches(2.60) + k * Inches(0.36), Pt(1.4), Inches(0.20),
                RULE)
    tf = dk.box(s, sx + Inches(0.14), Inches(2.42), Inches(4.4), Inches(0.26))
    dk.run(tf.paragraphs[0], "run offline, after both have finished",
           font=F_MONO, size=8.5, color=INK_3)

    dk.arrow(s, cx + bw + Inches(0.06), Inches(3.90), tx - Inches(0.06),
             Inches(4.46), color=INK_2)
    dk.arrow(s, wx + bw + Inches(0.06), Inches(5.70), tx - Inches(0.06),
             Inches(5.20), color=INK_2)
    for txt, x, y in (("bottom currents", 7.22, 3.84),
                      ("orbital velocity", 7.22, 5.50)):
        tf = dk.box(s, Inches(x), Inches(y), Inches(2.0), Inches(0.26))
        dk.run(tf.paragraphs[0], txt, font=F_MONO, size=8.5, color=INK_2)

    caption(s, MARGIN, Inches(7.02), Inches(11.5),
            "every arrow is a file on disk — there is no step here you cannot "
            "ask to see")
    return s


def link_slide(prs, spec):
    """One link in the chain: rail, headline, spec column, map, caption.

    Geometry is identical on all the map slides so that advancing the deck moves
    only the map and the lit rail tick -- nothing else shifts, which is what
    makes the sequence read as one thing being walked through."""
    s = prs.slides.add_slide(prs.slide_layouts[6])
    dk.bg(s, PAPER)
    h = Inches(5.52)
    w = int(h * 1.195)
    if spec.get("side"):
        # a second figure beside the map: the map shrinks rather than the
        # text column, which stays in the same place on every slide
        dk.picture(s, os.path.join(ASSET, spec["img"]), Inches(7.82),
                   Inches(0.98), height=Inches(4.45))
        dk.picture(s, os.path.join(ASSET, spec["side"]), Inches(4.15),
                   Inches(1.42), height=Inches(3.85))
    else:
        dk.picture(s, os.path.join(ASSET, spec["img"]),
                   EMU_W - Inches(0.60) - w, Inches(1.06), height=h)
    rail(s, spec["rail"], spec["clock"])
    headline(s, MARGIN, Inches(1.45), Inches(4.55), spec["lead"], spec["tail"])
    specs(s, MARGIN, Inches(3.95), Inches(4.55), spec["specs"], spec["head"])
    caption(s, MARGIN, Inches(6.86), Inches(11.5), spec["cap"])
    return s


def boundaries_slide(prs):
    """Slide 3. Four separate images -- the map and the three inputs -- placed
    independently rather than composed into one figure, so each can be moved."""
    s = prs.slides.add_slide(prs.slide_layouts[6])
    dk.bg(s, PAPER)
    rail(s, 1, "21 Jan 2022")
    headline(s, MARGIN, Inches(1.15), Inches(4.6), "The Gulf has\none ", "door.")
    specs(s, MARGIN, Inches(3.05), Inches(4.5),
          [("boundary", "east only  ·  26 wet cells"),
           ("depth", "27 to 1518 m"),
           ("ocean", "GLORYS 1/12 deg  ·  50 z-levels"),
           ("tide", "TPXO10, 10 constituents"),
           ("waves", "25 CMEMS spectra")],
          "open boundary")
    dk.picture(s, os.path.join(ASSET, "chain-3a-door.png"), Inches(5.30),
               Inches(1.10), height=Inches(3.05))
    dk.picture(s, os.path.join(ASSET, "chain-3b-ocean.png"), Inches(8.95),
               Inches(1.18), width=Inches(3.90))
    dk.picture(s, os.path.join(ASSET, "chain-3c-tide.png"), Inches(8.95),
               Inches(3.62), width=Inches(3.90))
    dk.picture(s, os.path.join(ASSET, "chain-3d-waves.png"), Inches(5.35),
               Inches(4.20), height=Inches(2.35))
    caption(s, MARGIN, Inches(6.90), Inches(11.5),
            "everything else is coastline — which is what makes a Gulf hindcast "
            "a tractable problem")
    return s


def grid_slide(prs):
    """Slide 4. Three panels zooming into a nest, with every word of type held
    in PowerPoint so titles and resolutions can be reworded in the room."""
    s = prs.slides.add_slide(prs.slide_layouts[6])
    dk.bg(s, PAPER)
    rail(s, 2, None)
    headline(s, MARGIN, Inches(1.02), Inches(4.8),
             "We refine until the site\nis ", "resolved.")
    specs(s, Inches(6.60), Inches(1.10), Inches(5.9),
          [("parent", "291 x 131  ·  3.5 km  ·  15 levels"),
           ("nest", "140 x 128  ·  1.2 km  ·  3x refinement"),
           ("method", "AGRIF two-way nesting"),
           ("", "further nests wherever a site needs one")],
          "model grid")

    left, top, wd = MARGIN, Inches(3.44), Inches(11.5)
    hgt = dk._emu(wd / 3.38)
    dk.picture(s, os.path.join(ASSET, "chain-4-grid.png"), left, top, width=wd)

    a = anchors("4-grid")
    titles = [("the whole Gulf", "3.5 km  ·  every 4th line"),
              ("the southern shelf", "3.5 km  ·  every cell"),
              ("a nested grid", "1.2 km  ·  every cell")]
    for k, (title, note) in enumerate(titles):
        cx, _ = at(left, top, wd, hgt, a[f"panel{k}"][0], 0.0)
        label(s, cx, Inches(2.92), title, size=11.5)
        label(s, cx, Inches(3.16), note, size=9, color=INK_3, font=F_MONO)

    caption(s, MARGIN, Inches(7.02), Inches(11.5),
            "the nest outline is the grid's own edge, not a box — and the same "
            "machinery refines again wherever a client needs it")
    return s


def circulation_slide(prs):
    """Slide 5. Surface currents plus the 3D cutaway they are the top layer of;
    the ACCENT box on the map is the block drawn beside it."""
    s = prs.slides.add_slide(prs.slide_layouts[6])
    dk.bg(s, PAPER)
    # no clock: the block and the map beside it are an indicative summer
    # snapshot, not part of the January storm the rest of the deck follows
    rail(s, 3, None)
    headline(s, MARGIN, Inches(1.05), Inches(3.4), "Then we solve\nfor the ",
             "water.")
    specs(s, MARGIN, Inches(2.86), Inches(3.4),
          [("model", "CROCO v1.3.1"),
           ("solves", "u, v, w, T, S, turbulence"),
           ("levels", "15, terrain-following"),
           ("mixing", "GLS + KPP"),
           ("output", "hourly, every level")],
          "circulation model")
    dk.picture(s, os.path.join(ASSET, "chain-5-circulation.png"),
               Inches(4.30), Inches(0.94), height=Inches(2.92))
    dk.picture(s, os.path.join(ASSET, "chain-5-block.png"),
               Inches(7.70), Inches(1.02), width=Inches(5.30))
    # clear of the spec column: the legend now sits above the axes, so the
    # figure's top edge is live rather than margin
    dk.picture(s, os.path.join(ASSET, "chain-5a-sst.png"),
               MARGIN, Inches(4.72), width=Inches(11.4))
    caption(s, MARGIN, Inches(7.06), Inches(11.5),
            "solved on 15 layers, not one — and held to ten years of satellite "
            "SST, not just the week we are talking about")
    return s


# Where each label sits relative to the feature it names, in inches, and how it
# is anchored. Read alongside the anchors file the figure writes: the figure
# says where the feature is, this says where its words go.
PROCESS_LABELS = [
    ("waves", "waves", (0.00, -0.30), "c", CYAN, 13, None),
    ("orbital", "orbital motion\nflattens onto the bed", (-1.45, 0.10), "r",
     CYAN, 10.5, None),
    ("current", "current\nstrongest at the surface,\nslowed by friction "
     "at the bed", (0.30, -0.15), "l", None, 10.5, "navy"),
    # both bed-stress labels in the stress colour, not their source's
    ("wave_bed", "wave-driven\nbed stress", (-0.25, 0.55), "r", ACCENT, 10.5,
     None),
    ("current_bed", "current-driven\nbed stress", (-0.15, 0.52), "c", ACCENT,
     10.5, None),
]


def process_labels(s, left, top, wd, hgt, name, extra=()):
    """Place a schematic's labels from the anchors the figure reported."""
    a = anchors(name)
    for key, text, (dx, dy), align, colour, size, special in (
            list(PROCESS_LABELS) + list(extra)):
        if key not in a:
            continue
        col = {"navy": dk.NAVY,
               "sed": dk.RGBColor(0x8a, 0x6a, 0x1c)}.get(
                   special, colour if colour is not None else INK_2)
        x, y = at(left, top, wd, hgt, *a[key])
        w = Inches(2.6)
        if align == "r":
            bx, al = x + Inches(dx) - w, 3
        elif align == "l":
            bx, al = x + Inches(dx), 1
        else:
            bx, al = x + Inches(dx) - w / 2, 2
        tf = dk.box(s, bx, y + Inches(dy), w, Inches(0.9))
        for i, line in enumerate(text.split("\n")):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.alignment = al
            dk.run(p, line, font=F_BODY, size=size, color=col, bold=True)


def process_slide(prs):
    """What acts on the bed, before what it produces.

    Water left plain here so nothing competes with the three mechanisms; the
    next slide repeats the identical geometry with the water coloured. All the
    labels are slide text, placed from the anchors the figure reports."""
    s = prs.slides.add_slide(prs.slide_layouts[6])
    dk.bg(s, PAPER)
    rail(s, 5, None)
    headline(s, MARGIN, Inches(0.98), Inches(5.0),
             "The seabed does nothing\nuntil it does ", "everything.")
    left, top, wd = Inches(1.37), Inches(2.18), Inches(10.60)
    hgt = dk._emu(wd / 2.20)
    dk.picture(s, os.path.join(ASSET, "chain-7b-process.png"), left, top,
               width=wd)
    process_labels(s, left, top, wd, hgt, "7b-process")
    caption(s, MARGIN, Inches(7.02), Inches(11.5),
            "waves and currents rarely line up — the model combines them "
            "non-linearly, so the pair bites harder than either alone")
    return s


def erosion_slide(prs):
    """The second half of the mechanism: what the stress produces.

    Same schematic as the slide before, with the water coloured. Advancing the
    deck changes only the water, which is the whole argument -- stress on the
    left, sediment on the right, nothing else moved."""
    s = prs.slides.add_slide(prs.slide_layouts[6])
    dk.bg(s, PAPER)
    rail(s, 5, None)
    headline(s, MARGIN, Inches(0.98), Inches(5.4),
             "Past a threshold, the bed\nlets ", "go.")
    left, top, wd = Inches(1.37), Inches(2.18), Inches(10.60)
    hgt = dk._emu(wd / 2.20)
    dk.picture(s, os.path.join(ASSET, "chain-7d-erosion.png"), left, top,
               width=wd)
    # The knobs behind the threshold this slide describes. Values are the
    # calib_02 central member -- the one plotted on the next slide -- read from
    # configs/gulf_01/turbidity/hindcast/calib_02/my_env.sh. Fine / coarse.
    # Two SIZE classes, solved together in every run -- not to be confused with
    # the five ensemble members on the next slide, which are five runs of this
    # same two-class model. Listing single values without saying which member
    # they belong to also implied the parameters were fixed, when erosion rate
    # is precisely the one the ensemble sweeps.
    specs(s, Inches(8.30), Inches(1.02), Inches(4.6),
          [("classes", "two, solved together"),
           ("", "fine ≈ 22 µm  ·  coarse ≈ 64 µm"),
           ("critical stress", "0.10 / 0.25 N/m²"),
           ("settling", "2e-4 / 2e-3 m/s"),
           ("erosion rate", "3e-4 / 3e-3 NTU·m/s"),
           ("background", "3 NTU"),
           ("", "central member — the ensemble"),
           ("", "sweeps erosion rate only")],
          "calibration parameters")
    process_labels(s, left, top, wd, hgt, "7d-erosion", extra=[
        ("sediment", "suspended sediment —\nmost of it near the bed",
         (0.18, -1.38), "l", None, 10.5, "sed")])
    caption(s, MARGIN, Inches(7.02), Inches(11.5),
            "erosion begins once the combined stress exceeds the bed's critical "
            "value; settling never stops, so what you see is the difference")
    return s


def turbidity_slide(prs):
    """Slide 8. The result, the observation point it was held to, and the
    calibration itself underneath."""
    s = prs.slides.add_slide(prs.slide_layouts[6])
    dk.bg(s, PAPER)
    # the clock follows the MODIS pass, since that is what is on the slide
    rail(s, 5, "7 Feb 2022  ·  09:30 UTC")
    headline(s, MARGIN, Inches(1.05), Inches(3.4), "All of it lands\non one ",
             "number.")
    specs(s, MARGIN, Inches(2.60), Inches(3.6),
          [("sediment", "two size classes"),
           ("stress", "Soulsby (1997)"),
           ("erosion", "Partheniades (1965)"),
           ("ensemble", "5 runs of that model"),
           ("", "erosion rate x0.5 to x2"),
           ("held to", "in-situ NTU, 6 m depth"),
           ("checked", "MODIS Aqua, qualitative")],
          "sediment model")
    # The MODIS pair replaces the standalone turbidity map: its right-hand
    # panel is that map, at the hour the satellite saw, with the calibration
    # site on it. Two of the same thing on one slide was one too many.
    dk.picture(s, os.path.join(ASSET, "chain-7c-modis.png"),
               Inches(4.45), Inches(0.92), width=Inches(8.45))
    dk.picture(s, os.path.join(ASSET, "chain-7a-calibration.png"),
               Inches(0.95), Inches(4.94), width=Inches(11.45))
    caption(s, MARGIN, Inches(7.06), Inches(11.5),
            "a February event, not January: cloud and dust sit over most of the "
            "storms worth looking at, and clean scenes are rare")
    return s


def bookend(prs, spec):
    """The closing loop. Its figure leaves its own top-left quadrant empty, so
    the headline and the explanatory text sit inside the image's footprint
    rather than above it."""
    s = prs.slides.add_slide(prs.slide_layouts[6])
    dk.bg(s, PAPER)
    if spec["rail"] is not None:
        rail(s, spec["rail"], spec["clock"])
    wd = Inches(12.0)
    dk.picture(s, os.path.join(ASSET, spec["img"]), Inches(0.68), Inches(1.18),
               width=wd)
    # The figure's clear quadrant is roughly x < 7.4 in, y < 3.5 in; the maps
    # start below that and the traces to the right of it, so the text has to
    # finish inside it rather than merely start there.
    headline(s, MARGIN, Inches(1.46), Inches(5.4), spec["lead"], spec["tail"])
    tf = dk.box(s, MARGIN, Inches(2.86), Inches(5.6), Inches(0.9))
    for i, line in enumerate([
            "Wind first, then waves within the hour, then the bed,",
            "then the plume at the surface — twelve hours from the",
            "shamal peaking to the water going brown."]):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_before = Pt(0 if i == 0 else 4)
        dk.run(p, line, font=F_BODY, size=13, color=INK_2)
    caption(s, MARGIN, Inches(6.96), Inches(11.5), spec["cap"])
    return s


def build():
    prs = Presentation()
    prs.slide_width, prs.slide_height = EMU_W, EMU_H
    dk.set_theme_fonts(prs)

    overview(prs)
    link_slide(prs, SLIDES[0])            # 2  atmosphere
    boundaries_slide(prs)                 # 3  boundaries
    grid_slide(prs)                       # 4  grid + nesting
    circulation_slide(prs)                # 5  circulation + 3D block
    link_slide(prs, SLIDES[1])            # 6  waves
    process_slide(prs)                    # 7  what acts on the bed
    erosion_slide(prs)                    # 8  what it produces
    turbidity_slide(prs)                  # 9  result + calibration
    if os.path.exists(os.path.join(ASSET, BOOKENDS["closer"]["img"])):
        bookend(prs, BOOKENDS["closer"])  # 10 cascade reprise
    else:
        print("  (no cascade GIF yet — run make_model_chain.py --gif)")

    dk.embed_fonts(prs)
    out = os.path.join(dk.HERE, "chain-module.pptx")
    prs.save(out)
    check_coordinates(out)
    print(f"wrote {out} — {len(prs.slides._sldIdLst)} slides")
    return out


def check_coordinates(path):
    """Fail loudly on non-integer EMU before the file reaches PowerPoint.

    A float coordinate produces a .pptx that LibreOffice opens happily and that
    PowerPoint and Google Slides both refuse with no useful error -- so the only
    cheap place to catch it is here."""
    import re
    import zipfile
    bad = []
    with zipfile.ZipFile(path) as z:
        for name in z.namelist():
            if not (name.startswith("ppt/slides/slide") and name.endswith(".xml")):
                continue
            body = z.read(name).decode("utf-8")
            for m in re.finditer(r'\b(x|y|cx|cy)="(-?\d+\.\d+)"', body):
                bad.append(f"{name}: {m.group(1)}={m.group(2)}")
    if bad:
        raise SystemExit("non-integer EMU coordinates — PowerPoint will refuse "
                         "this file:\n  " + "\n  ".join(bad[:20]))


if __name__ == "__main__":
    argparse.ArgumentParser().parse_args()
    build()
