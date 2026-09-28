#!/usr/bin/env python3
"""
Ocean Motion Analytics — supplier deck for a UAE coastal engineering
consultancy (ADEC).

The audience is a consultancy, not an asset owner: they run their own
nearshore models and deliver the client's study. So the deck sells what sits
behind their work -- regional design data, turbidity, climate horizons -- and
never port-scale downscaling, which is their business.

It is also a discovery deck. The 40-year design-conditions dataset is built in
H1 2027 (see oceanmotion-company/business-plan/); today there is a 10-year
circulation hindcast and one year of waves. Slides say so. The ask is a
founding-partner commitment -- a letter of intent and validation data -- not
a purchase.

Built the same way as make_ports_deck.py, and reusing its helpers: open the
desal deck as sent (it carries hand edits the generators don't know about),
keep the model and turbidity slides, retext the offering slides as the dataset,
climate and ways-of-working slides, and add the surge evidence and new slides
with deckkit. Shape ids are the base file's; every lookup fails loudly.

Story:
  --  what has changed since we last worked together
  01  how the model works         inputs, grid, circulation, waves, turbidity
  02  tested against tide gauges  Salmiya and Majis surge; nine years at
                                 Khalifa Port
  03  a design dataset            the dataset (status stated); climate horizons
  04  working together            three ways; founding partner

Prices are deliberately not on the slides or in the notes (a sent .pptx
carries its notes). They live in adec-meeting-prep.md.

Runs in the base environment (needs python-pptx):
    python3 make_adec_deck.py
Output: oma-pitch-adec.pptx
"""

import argparse
import os
from datetime import date

from pptx.util import Inches

import deckkit as dk
from deckkit import ACCENT, MARGIN
import make_desal_deck as desal
import make_ports_deck as ports
from make_ports_deck import (shape, set_paras, dash_item, spec_item, retext,
                             drop_slide, reorder, new_slide, notes, divider)

BASE = ports.BASE
CLIENT = "ADEC"


# ------------------------------------------------------------------ new
def since_slide(prs):
    s = new_slide(prs)
    dk.eyebrow(s, MARGIN, Inches(0.95), "Since we last worked together")
    desal.headline(s, MARGIN, Inches(1.35), Inches(11.4),
                   "A model of the whole Gulf, ", "running every day.", size=40)
    desal.cards(s, [
        ("Operational", "A daily Gulf forecast",
         "Circulation, water level and waves across the whole Gulf, seven "
         "days ahead, every day, on a fully automated chain."),
        ("Tested", "A decade of hindcast",
         "2015 to 2025, hourly, checked against tide gauges, satellite "
         "temperature and satellite wave heights. The surge is the standout."),
        ("Unique", "Sediment turbidity",
         "Shamal-driven turbidity from waves and currents at the bed, tuned "
         "to in-situ measurements. We know of no one else modelling it for "
         "the Gulf."),
    ], top=Inches(2.85))
    notes(s, "Open with the relationship, then this slide. The point: the "
             "regional model they would otherwise have to build or buy "
             "already exists, runs daily, and is tested. Everything later in "
             "the deck is built on it.")
    return s


def evidence_rail(s, active):
    """The validation slides sit outside the chain's progress rail, so they
    carry a section eyebrow where the rail would be."""
    dk.eyebrow(s, MARGIN, Inches(0.42), "Section 02  ·  Tested against tide "
                                        "gauges")


def salmiya_slide(prs):
    """The surge evidence with CROCO alone. The ports deck draws MERCATOR
    beside it to argue for the operational ensemble; for design data the
    argument is the model's own long record, and MERCATOR's long-record
    counterpart (GLORYS) keeps only daily means, so it is left off."""
    s = new_slide(prs)
    evidence_rail(s, None)
    desal.headline(s, MARGIN, Inches(1.00), Inches(5.6),
                   "Salmiya, Kuwait: the surge,\nevent by event.", size=30)
    for k, (big, lbl) in enumerate([
            ("0.88", "correlation\nhourly, 9 months"),
            ("8.7 cm", "RMSE"),
            ("±18 cm", "typical surge\nat the gauge")]):
        ports.stat(s, Inches(6.75) + k * Inches(2.0), Inches(0.95), big, lbl,
                   width=Inches(1.9), size=40)
    dk.picture(s, ports.asset("wl-gauge-salmiya-croco.png"), MARGIN,
               Inches(2.15), width=Inches(11.0))
    desal.caption(s, MARGIN, Inches(6.40), Inches(11.5),
                  "predicted tide, then the non-tidal residual: gauge and "
                  "model put through the same harmonic analysis over the "
                  "gauge record, 15 Jun 2023 – 26 Mar 2024")
    notes(s, ports.TIDE_NOTES["Salmiya"] + "Salmiya: 6 834 hourly pairs (6 gauge spikes removed). CROCO "
             "r 0.88, RMSE 8.7 cm. Gauge residual -0.72 to +0.48 m, std "
             "18.4 cm. Residual = series minus its own utide fit over the "
             "gauge record period, trend=False. The surge is generated inside "
             "the Gulf by wind over a shallow enclosed sea, so it is largest "
             "at the head of the Gulf and along the southern shelf.")
    return s


def majis_slide(prs):
    """The contrast to Salmiya, CROCO alone as on that slide. Outside Hormuz
    the surge is a third the size, so the same few-cm errors weigh more: this
    is the weakest residual score in the deck, and the slide says what it
    is rather than leaving it out. Same layout as Salmiya, so the two read as
    a pair."""
    s = new_slide(prs)
    evidence_rail(s, None)
    desal.headline(s, MARGIN, Inches(1.00), Inches(5.6),
                   "Majis, Oman: outside the Gulf,\nthe surge is small.",
                   size=30)
    for k, (big, lbl) in enumerate([
            ("0.65", "correlation\nhourly, 14 months"),
            ("5.3 cm", "RMSE"),
            ("±6 cm", "typical surge\nat the gauge")]):
        ports.stat(s, Inches(6.75) + k * Inches(2.0), Inches(0.95), big, lbl,
                   width=Inches(1.9), size=40)
    dk.picture(s, ports.asset("wl-gauge-majis-croco.png"), MARGIN,
               Inches(2.15), width=Inches(11.0))
    desal.caption(s, MARGIN, Inches(6.40), Inches(11.5),
                  "predicted tide, then the non-tidal residual, as at "
                  "Salmiya; 6 Feb 2023 – 24 Mar 2024, unphysical gauge spikes "
                  "removed (1.6% of readings). The tide here is near exact: "
                  "correlation 0.98.")
    notes(s, ports.TIDE_NOTES["Majis"] + "Majis: 8 482 hourly pairs after the spike QC (155 readings, "
             "1.6%, flagged by an iterated 5-h running-median test at "
             "0.10 m). CROCO r 0.65, RMSE 5.3 cm. Residual std: gauge 6.0 cm, "
             "CROCO 6.4 cm; at Salmiya the gauge std is 18.4 cm. The surge is "
             "made inside the Gulf by wind over a shallow enclosed sea, while "
             "the tide comes in through Hormuz: at Majis the tide is near "
             "exact (r 0.98, amplitudes within 2 cm on the main constituents, "
             "a uniform ~25 min lag still to be checked) and the surge is a "
             "third of Salmiya's, so a few cm of error costs more "
             "correlation. If pressed: the operational forecast runs an "
             "ensemble with MERCATOR, which scores r 0.85 here.")
    return s


def abudhabi_slide(prs):
    s = new_slide(prs)
    dk.eyebrow(s, MARGIN, Inches(0.95), "Section 02  ·  Abu Dhabi")
    desal.headline(s, MARGIN, Inches(1.30), Inches(11.4),
                   "Nine years of surge at Khalifa Port.", size=34)
    dk.picture(s, ports.asset("wl-abudhabi.png"), MARGIN, Inches(2.08),
               width=Inches(11.0))
    desal.caption(s, MARGIN, Inches(6.88), Inches(11.5),
                  "model only — there is no UAE gauge in this comparison yet. "
                  "Your records are what would change that.")
    notes(s, "CROCO C04_I01 hindcast, 2016-2024 hourly, nearest wet cell to "
             "Khalifa Port (~3 km grid, ~6 m deep). Residual -0.37 to +0.60 m; "
             "0.1 / 99.9 percentiles -0.27 / +0.47 m. Set-downs below -0.25 m "
             "about four a year. Zayed Port, 40 km along the coast, tracks it "
             "at r 0.99. This is the lead-in to the data-sharing ask: the gap "
             "in the evidence is a UAE gauge, and they may hold one.")
    return s


def partner_slide(prs):
    s = new_slide(prs)
    dk.eyebrow(s, MARGIN, Inches(0.95), "Section 04")
    desal.headline(s, MARGIN, Inches(1.30), Inches(11.4),
                   "Founding partner, ", "2027.", size=40)
    col_w = Inches(5.5)
    right = MARGIN + col_w + Inches(0.5)
    dk.eyebrow(s, MARGIN, Inches(2.55), f"What {CLIENT} gets", color=ACCENT)
    desal.bullets(s, MARGIN, Inches(3.00), col_w, [
        "A first-year regional licence at a founding rate.",
        "A say in what the dataset covers: your sites, your variables, your "
        "design horizons.",
        "Early access to each release as it is validated.",
        "Validation at your own stations, published as ours to stand behind.",
    ], size=13)
    dk.eyebrow(s, right, Inches(2.55), "What we'd ask", color=ACCENT)
    desal.bullets(s, right, Inches(3.00), col_w, [
        "A letter of intent: the licence, if the validation clears the bar "
        "we agree now.",
        "Access to gauge, ADCP or buoy records for validating extremes. They "
        "stay yours and are never redistributed.",
        "A reference, once delivered.",
    ], size=13)
    desal.note(s, MARGIN, Inches(5.52), Inches(11.5), "Where it stands",
               "Today: a tested 10-year circulation hindcast and one year of "
               "waves. In build, first half of 2027: the 40-year record, "
               "validated extremes, turbidity climatology and climate "
               "horizons. Founding partners shape it before it is fixed.")
    notes(s, "The ask. A letter of intent conditional on validation is easy "
             "to sign and is the evidence the funding case needs. The data "
             "access matters as much as the money: UAE gauge extremes are the "
             "missing piece of the validation.")
    return s


def lead_items(sh, items, top=None, width=None, size=None,
               aside_last=False):
    """Dash bullets with a bold lead word, in the base deck's own bullet
    formatting. aside_last mutes the final item, for the thing worth saying
    but not worth selling on this slide."""
    set_paras(sh, [[("—  ", 0), (lead + "  ", 1), (body, 1)]
                   for lead, body in items])
    from pptx.util import Pt
    paras = sh.text_frame.paragraphs
    for p in paras:
        p.runs[1].font.bold = True
        if size is not None:
            p.line_spacing = 1.22
            p.space_after = Pt(7)
            for r in p.runs:
                r.font.size = Pt(size)
    if aside_last:
        for r in paras[-1].runs:
            r.font.color.rgb = dk.INK_3
    if top is not None:
        sh.height = sh.height + (sh.top - top)
        sh.top = top
    if width is not None:
        sh.width = width


def gauge_sites(s, sid=247):
    """Swap the circulation map for the render with the gauges marked, and set
    their names as native text beside the markers. Positions come from the
    anchors file the figure writes, so the names follow the map. Salmiya's
    name goes to the right, over Kuwait; Majis sits near the map's right
    edge, beside the 3D block, so its name goes underneath."""
    import json
    from pptx.enum.text import PP_ALIGN
    pic = dk.swap_picture(s, sid, ports.asset("chain-5-circulation-sites.png"))
    with open(ports.asset("chain-5-circulation-sites.anchors.json")) as fh:
        anchors = json.load(fh)
    w = Inches(0.9)
    place = {"Salmiya": (Inches(0.15), -Inches(0.13), PP_ALIGN.LEFT),
             "Majis": (-w / 2, Inches(0.08), PP_ALIGN.CENTER)}
    if set(anchors) != set(place):
        raise SystemExit(f"sites on the map {sorted(anchors)} != labelled "
                         f"{sorted(place)}")
    for name, a in anchors.items():
        dx, dy, align = place[name]
        x = pic.left + a["x"] * pic.width
        y = pic.top + a["y"] * pic.height
        tf = ports.label(s, x + dx, y + dy, w, name, color=dk.INK, size=9,
                         align=align)
        if name == "Salmiya":
            # it sits on the densest arrows in the map: a white chip, cut to
            # the word, keeps it legible without hiding more than it must
            box = tf._parent
            box.fill.solid()
            box.fill.fore_color.rgb = dk.GROUND
            box.width = Inches(0.78)
            tf.word_wrap = False
            tf.margin_left = tf.margin_right = Inches(0.04)
    notes(s, "The two dots are the tide gauges section 02 tests against: "
             "Salmiya at the head of the Gulf, Majis outside Hormuz.")


# ------------------------------------------------------------------ kept
def retext_kept(k):
    """k maps the base deck's 1-based slide numbers to slides."""
    # 1. title
    s = k[1]
    set_paras(shape(s, 163), [[("Regional ocean data\n"
                                "for your Gulf projects", 1)]])
    set_paras(shape(s, 164), [[("PITCH DECK", 0)],
                              [(f"Prepared for {CLIENT}  ·  "
                                f"{date.today():%B %Y}", 0)]])

    # 2. contents
    set_paras(shape(k[2], 173), [
        [(f"{i + 1:02d}", 0), (f"    {t}", -1)] for i, t in enumerate([
            "How the model works",
            "Tested against tide gauges",
            "A design dataset for the Gulf",
            "Working together"])])

    # 6. circulation: the map carries the two tide gauges of section 02
    gauge_sites(k[6])

    # 8, 10. turbidity: same slides, the consultancy's reasons in notes
    notes(k[8], "For a consultancy the turbidity story is dredging and "
                "reclamation compliance and EIA baselines as much as intakes: "
                "what background turbidity looks like through a shamal "
                "season, and how often a limit is exceeded with no works at "
                "all.")
    notes(k[10], "Calibrated at one station over one month; a multi-year "
                 "climatology validated against satellite turbidity is part "
                 "of the 2027 build. Say so if asked.")

    # 13. three offerings -> three ways to work together
    s = k[13]
    retext(s, 381, "SECTION 04")
    set_paras(shape(s, 382), [[("Three ways to ", 0), ("work together.", 1)]])
    for tag, head, body, t, h, b in (
            (385, 386, 387, "PER PROJECT", "Project data",
             "Design conditions and boundary data at the offshore edge of "
             "your project, with a skill appendix, delivered in days for "
             "your own nearshore models."),
            (390, 391, 392, "ANNUAL", "A regional licence",
             "Unlimited point extractions across the Gulf for your projects "
             "for a year, under one agreement. Your team pulls what each "
             "study needs."),
            (395, 396, 397, "SUBCONTRACT", "Specialist modelling",
             "What most consultancies don't run in-house: sediment turbidity "
             "and dredge plumes, and climate horizons for a design basis.")):
        retext(s, tag, t)
        retext(s, head, h)
        retext(s, body, b)
    notes(s, "We supply what sits behind your study; the nearshore modelling "
             "and design stay with you.")

    # 14. offering 01 -> the dataset. The selling point is the joint record:
    # waves and water level hour by hour over decades, so a designer no
    # longer has to assume how the two co-occur. One bullet per product,
    # co-occurrence given its own, turbidity last and muted as an aside.
    s = k[14]
    retext(s, 404, "SECTION 03")
    retext(s, 405, "Waves and water level together,\n"
                   "hour by hour, for 40+ years.")
    head = shape(s, 405)
    head.height = Inches(1.15)
    lead_items(shape(s, 406), [
        ("Waves.", "Hourly parameters and full directional spectra at any "
                   "point, in the format your models take: MIKE, SWAN or "
                   "WW3. Each output point can be bias-corrected against "
                   "satellite altimetry."),
        ("Surge.", "Tide and surge separated, hourly, across the whole Gulf, "
                   "checked against tide gauges as in Section 02."),
        ("Co-occurrence.", "One modelling chain, one set of winds: every "
                           "hour carries both waves and water level. Joint "
                           "extremes for EVA, and berth availability and "
                           "throughput from the real sequence of conditions, "
                           "not an assumed dependence."),
        ("Nested models.", "Boundary conditions for your nearshore models: "
                           "spectral waves, water level and currents along "
                           "any open boundary, over the same period."),
        ("Also turbidity.", "From the same run, a climatology of how often, "
                            "how high and for how long, for dredging and EIA "
                            "baselines."),
    ], top=Inches(2.88), width=Inches(6.9), size=12, aside_last=True)
    retext(s, 408, "WHAT IT WILL COVER")
    set_paras(shape(s, 409), [spec_item(*r) for r in [
        ("period", "40+ years, hourly"),
        ("waves", "Hs, Tp, direction + 2D spectra"),
        ("water level", "total, tide and surge"),
        ("also", "currents, T, S, turbidity"),
        ("resolution", "~3 km regional"),
        ("formats", "MIKE, SWAN, WW3, NetCDF, CSV"),
        ("deliverable", "point series, spectra, boundaries"),
        ("", "at any coordinates, with a skill appendix")]])
    retext(s, 412, "STATUS AND SCOPE")
    retext(s, 413, "In build, first half of 2027; today's record is ten years "
                   "of circulation and one of waves. Regional, not nearshore: "
                   "transformation to your structures stays in your models.")
    notes(s, "The point of this slide is the joint record. Designers normally "
             "take waves and water level from separate sources and assume how "
             "they co-occur (a dependence factor, as in the Defra/EA FD2308 "
             "joint probability approach), for both EVA and operational "
             "studies. Here the two are simulated together, hour by hour, so "
             "joint exceedance and downtime come straight from the record. "
             "Waves: WW3 forced by the same ERA5 winds and by CROCO's water "
             "levels and currents; spectra can be written at any output point "
             "and converted to MIKE 21 SW or SWAN boundary formats; per-point "
             "bias correction against CMEMS altimetry. Be exact about status. Today: 10-year CROCO hindcast "
             "(2015-2025) and one year of coupled waves (2016). The 40-year "
             "record, extremes validation, turbidity climatology and climate "
             "horizons are the 2027 build.")

    # 17. climate
    s = k[17]
    retext(s, 443, "SECTION 03")
    retext(s, 444, "Design conditions at 2050 and 2100,\n"
                   "ready to cite.")
    set_paras(shape(s, 445), [dash_item(t) for t in [
        "Structures designed now will work through the 2070s, but climate "
        "allowances in the Gulf are mostly desk estimates.",
        "Sea level rise lets larger waves reach shallow structures, and "
        "surge rides on a higher mean. The future record keeps waves and "
        "water level together, so joint extremes move consistently.",
        "The same rise reduces bed stress, so turbidity can fall at deeper "
        "sites while waves at the structure grow. One consistent set of "
        "runs answers both."]])
    set_paras(shape(s, 448), [spec_item(*r) for r in [
        ("method", "delta (pseudo-global-warming) downscaling"),
        ("scenarios", "SSP2-4.5 and SSP5-8.5"),
        ("horizons", "2050 and 2100"),
        ("sea level", "projected rise, built into the model"),
        ("answers", "joint water level and waves, turbidity"),
        ("built on", "the same validated models")]])
    notes(s, "The method keeps the observed sequence of shamals and adds the "
             "projected change on top; wind changes are handled as a response "
             "curve rather than a claim about how shamals will change.")


# ------------------------------------------------------------------ build
# 11, the storm-cascade GIF, is left out: 8 MB for one slide, and the chain
# slides before it already walk the storm through.
KEEP = [1, 2, 3, 4, 5, 6, 7, 8, 10, 13, 14, 17, 18]


def build(out="oma-pitch-adec.pptx"):
    prs, base = ports.load_base()
    k = {n: base[n - 1] for n in KEEP}
    for n, s in enumerate(base, 1):
        if n not in KEEP:
            drop_slide(prs, s)
    retext_kept(k)

    since = since_slide(prs)
    d02 = divider(prs, "Section 02", "Tested against tide gauges")
    sal = salmiya_slide(prs)
    maj = majis_slide(prs)
    ad = abudhabi_slide(prs)
    d03 = divider(prs, "Section 03", "A design dataset for the Gulf")
    d04 = divider(prs, "Section 04", "Working together")
    partner = partner_slide(prs)

    reorder(prs, [k[1], since, k[2],
                  k[3], k[4], k[5], k[6], k[7], k[8], k[10],         # 01
                  d02, sal, maj, ad,                                     # 02
                  d03, k[14], k[17],                                  # 03
                  d04, k[13], partner,                                # 04
                  k[18]])

    from pptx.opc.packuri import PackURI
    for i, s in enumerate(prs.slides, 1):
        s.part.partname = PackURI(f"/ppt/slides/slide{i}.xml")
        if s.has_notes_slide:
            s.notes_slide.part.partname = PackURI(
                f"/ppt/notesSlides/notesSlide{i}.xml")

    path = os.path.join(dk.HERE, out)
    prs.save(path)
    ports.chain.check_coordinates(path)
    print(f"wrote {path} — {len(prs.slides._sldIdLst)} slides")
    return path


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("-o", "--out", default="oma-pitch-adec.pptx")
    build(ap.parse_args().out)
