#!/usr/bin/env python3
"""
Ocean Motion Analytics -- one style for every time series in the decks.

make_water_levels.py and make_model_chain.py both draw time series (tide,
surge residual, SST, turbidity calibration) and used to style them separately,
which is how they drifted: a teal model here, a grey satellite there, minor
rules on some panels and none on others. Both now take their colours, axes and
legends from here.

  observations   black    gauge, satellite, in-situ -- the reference
  CROCO          blue     our circulation model (and the models built on it)
  MERCATOR       red      the second, external model

The blue and red pass the dataviz palette validator against white (CVD dE
23.5, normal-vision 32.4); black is ink, the reference the colours are read
against, not a third hue.

Rules are drawn at the major ticks only, in both directions, dashed and pale:
enough to read a peak off the slide, not enough to compete with the data.
Figures are saved at DPI -- 300, so an 11-inch figure is 3300 px across, well
past what a projector or a 4K screen shows of a 13.3-inch slide.

Needs matplotlib only, so it imports in the somisana_croco env alongside the
figure scripts.
"""

OBS   = "#0b1420"   # observations: the deck's ink, reads as black
CROCO = "#1f5fbf"   # CROCO, and model output generally
MERC  = "#c62828"   # MERCATOR
CROCO_BAND = "#9dbbe6"  # CROCO spread / ensemble range fills

INK_2 = "#4a5665"
INK_3 = "#8a94a2"
RULE  = "#d5dbe2"   # axis spines
GRID  = "#b3bcc7"   # the dashed major-tick rules
GRID_LW, GRID_LS = 0.6, (0, (4, 3))

F_BODY, F_MONO = "IBM Plex Sans", "IBM Plex Mono"

DPI = 300

# the three lines every model-vs-observation panel draws, in this order
LW = 0.9


def style_axes(ax, ylabel=None, grid=True):
    """Bare deck axes: left and bottom spines only, mono tick labels, dashed
    rules at the major ticks. Call after the locators are set -- rules follow
    the major ticks, and tick fonts are applied to the labels that exist."""
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    for sp in ("left", "bottom"):
        ax.spines[sp].set_color(RULE)
        ax.spines[sp].set_linewidth(0.8)
    ax.tick_params(labelsize=8, colors=INK_3, length=2.5, width=0.7)
    ax.tick_params(which="minor", length=0)
    if grid:
        ax.grid(True, which="major", axis="both", color=GRID, lw=GRID_LW,
                ls=GRID_LS)
        ax.grid(False, which="minor")
        ax.set_axisbelow(True)
    if ylabel:
        ax.set_ylabel(ylabel, fontsize=8.5, color=INK_2, fontfamily=F_BODY)
    fonts(ax)


def fonts(ax):
    """Re-apply tick fonts after locators or limits have made new labels."""
    for lb in list(ax.get_xticklabels()) + list(ax.get_yticklabels()):
        lb.set_fontfamily(F_MONO)
        lb.set_color(INK_2)


def legend_above(ax, ncol=3, **kw):
    """Legend in a row above the axes, left-aligned, no frame. A long record
    fills its frame edge to edge, so any in-axes legend lands on the data."""
    leg = ax.legend(loc="lower left", bbox_to_anchor=(0.0, 1.005),
                    frameon=False, fontsize=8, ncol=ncol, handlelength=1.8,
                    columnspacing=1.6, borderaxespad=0.0, **kw)
    for t in leg.get_texts():
        t.set_color(INK_2)
        t.set_fontfamily(F_MONO)
    for h in leg.legend_handles:
        if hasattr(h, "set_linewidth"):
            h.set_linewidth(1.6)
    return leg


def panel_title(ax, text, x=1.0, ha="right"):
    """A small mono caption naming what a panel shows, set above its top-right
    corner so it never collides with the legend on the left."""
    ax.text(x, 1.02, text, transform=ax.transAxes, fontsize=7.5,
            color=INK_3, fontfamily=F_MONO, ha=ha, va="bottom")


def side(ax, text, y=0.98, size=8, color=INK_2):
    """Statistics in the right margin, beside the axes they describe."""
    ax.text(1.012, y, text, transform=ax.transAxes, fontsize=size,
            color=color, fontfamily=F_MONO, ha="left", va="top",
            linespacing=1.55)
