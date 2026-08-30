#!/usr/bin/env python3
"""
Ocean Motion Analytics — turbidity process schematic for the desal pitch deck.

Three build stages of one figure, exported as flat PNGs so a live call has nothing
to mis-click and a PDF export still reads:

  stage 1  cross-section: waves and currents loading the bed with a combined stress
  stage 2  + the bed-stress strip, tau_max against the erosion threshold
  stage 3  + plume and intake; the strip morphs from stress to concentration,
           surface against bed, with tau ghosted behind on the same clock

The section is an idealised cartoon — reality is 3D and a "realistic" section would
be less legible, not more. The strip is real model output. That split is deliberate:
the cartoon carries the general claim (both drivers, combined), the data carries the
site-specific one (the bed only responds above a threshold). The strip shows tau_max
only and stays silent on which driver dominates, because that varies by site and this
figure is shown to operators at many of them.

Data comes from a small cached extract so the figure regenerates anywhere, offline,
long after the 12 GB model files have been rotated away by the streaming pipeline.

Regenerate:  python3 make_turbidity_schematic.py --extract     (needs the model volume)
             python3 make_turbidity_schematic.py               (all three stages)
             python3 make_turbidity_schematic.py --stage 2 --obs
Output:      assets/tau-jan2022.npz
             assets/turbidity-schematic-{1,2,3}.png
Requires:    numpy, matplotlib (+ xarray, pandas for --extract only)

The in-situ NTU overlay is behind --obs and OFF by default: provenance of the record
is unresolved (see gulf-turbidity-skill-assessment/v1.0-plan.md), and a pitch slide
discloses sooner and more widely than the report does. Turn it on once that clears.
"""

import argparse
import os

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse, Polygon
import matplotlib.dates as mdates

# ---------------------------------------------------------------- tokens
# Mirrors build_template.py, which mirrors the website's styles.css.
ABYSS    = "#050f1c"
NAVY     = "#091c33"
NAVY_MID = "#13294a"
CYAN     = "#4fc3d7"
CYAN_LT  = "#a8e0ea"
ACCENT   = "#ff6a2b"
PAPER    = "#f4efe3"
PAPER_2  = "#efe9d9"
INK      = "#0b1420"
INK_2    = "#4a5665"
INK_3    = "#8a94a2"
RULE     = "#d6cdb6"

F_DISPLAY = "Instrument Serif"
F_BODY    = "IBM Plex Sans"
F_MONO    = "IBM Plex Mono"

HERE      = os.path.dirname(os.path.abspath(__file__))
ASSET_DIR = os.path.join(HERE, "assets")
FONT_DIR  = os.path.join(HERE, "fonts")
CACHE     = os.path.join(ASSET_DIR, "tau-jan2022.npz")

# Source paths for --extract only. Everything downstream reads the cache.
MODELS   = os.path.expanduser("~/code/oceanmotion-models")
TURB_NC  = os.path.join(MODELS, "configs/gulf_01/turbidity/hindcast/calib_02/"
                                "output/turbidity_3d_Y2022M01_mem03.nc")
OBS_CSV  = os.path.join(MODELS, "datasets/ntu_obs/NTU_obs.csv")
SITE_LON, SITE_LAT = 54.0723, 24.3689

# Two themes so the Asset 2 report figure is a flag rather than a rewrite. Only
# "deck" is built today; "report" is a stub carrying the palette inversion.
THEME = {
    "deck": dict(ground=PAPER, water=NAVY, water_edge=NAVY_MID, bed=PAPER_2,
                 ink=INK, ink_2=INK_2, ink_3=INK_3, on_water=PAPER,
                 on_water_2=CYAN_LT, figsize=(11.5, 4.6)),
    "report": dict(ground="white", water="#dceaf0", water_edge=CYAN,
                   bed=PAPER_2, ink=INK, ink_2=INK_2, ink_3=INK_3,
                   on_water=INK, on_water_2=INK_2, figsize=(6.5, 4.2)),
}


def register_fonts():
    """Use the deck's vendored faces so the figure sets in the same type as the
    slide it lands on. Silently falls back to matplotlib defaults if absent."""
    from matplotlib import font_manager
    if not os.path.isdir(FONT_DIR):
        return
    for f in os.listdir(FONT_DIR):
        if f.endswith(".ttf"):
            try:
                font_manager.fontManager.addfont(os.path.join(FONT_DIR, f))
            except Exception:
                pass


# ---------------------------------------------------------------- extract
def extract():
    """Pull the three traces and the obs at the site into a small committed cache.

    tau_max, C_surface and C_bottom are all already in the turbidity output, so this
    needs neither CROCO nor WW3 and no Soulsby recompute — one file, one grid point.
    """
    import xarray as xr
    import pandas as pd

    ds = xr.open_dataset(TURB_NC)
    lon, lat = ds.lon_rho.values, ds.lat_rho.values
    j, i = np.unravel_index(np.argmin((lon - SITE_LON) ** 2
                                      + (lat - SITE_LAT) ** 2), lon.shape)

    time = pd.to_datetime(ds.time.values)
    out = dict(
        time=time.values.astype("datetime64[s]").astype(np.int64),
        tau_max=ds.tau_max[:, j, i].values.astype(np.float32),
        C_surface=ds.C_surface[:, j, i].values.astype(np.float32),
        C_bottom=ds.C_bottom[:, j, i].values.astype(np.float32),
        tau_cr_fine=np.float32(ds.attrs["tau_cr_0"]),
        tau_cr_coarse=np.float32(ds.attrs["tau_cr_1"]),
        C_bg=np.float32(3.0),
        depth_m=np.float32(6.4),
        site=np.array([lon[j, i], lat[j, i]], dtype=np.float64),
    )

    if os.path.exists(OBS_CSV):
        obs = pd.read_csv(OBS_CSV, header=None, usecols=[0, 1],
                          names=["t", "ntu"], parse_dates=["t"])
        obs = obs.dropna()
        out["obs_time"] = obs["t"].values.astype("datetime64[s]").astype(np.int64)
        out["obs_ntu"] = obs["ntu"].values.astype(np.float32)

    os.makedirs(ASSET_DIR, exist_ok=True)
    np.savez_compressed(CACHE, **out)
    print(f"wrote {CACHE}")
    print(f"  site grid point {j},{i} — {out['site'][0]:.4f}E {out['site'][1]:.4f}N, "
          f"{out['depth_m']:.1f} m")
    print(f"  {len(time)} hourly steps, tau_max max {out['tau_max'].max():.2f} N/m²")


def load():
    if not os.path.exists(CACHE):
        raise SystemExit(f"missing {CACHE} — run with --extract first "
                         "(needs the model volume mounted)")
    d = np.load(CACHE)
    return {k: d[k] for k in d.files}


# ---------------------------------------------------------------- section
# Idealised cross-shore section. Shore right, deepening left, waves in from the
# left. The alongshore current is drawn in-plane: a known simplification, taken
# because an into-page symbol costs the reader more than the rigour is worth in
# a cartoon. Vertical is exaggerated ~7x and says so on the figure.
X0, X1 = 0.0, 100.0
Y0, Y1 = -8.8, 2.9
BED_FLAT, BED_TOP = -7.0, 0.9
BED_TONE, BED_EDGE = "#e2d8c0", "#b9ad8e"   # carbonate: pale, but not PAPER-pale
INTAKE_X = 68.0


def bed_profile(x):
    """Gentle shelf holding ~6 m across most of the frame, steepening to a beach
    only in the last fifth. A steeper shelf would spend the picture on sand."""
    t = np.clip((x - 10.0) / 85.0, 0.0, 1.0)
    return BED_FLAT + (BED_TOP - BED_FLAT) * t ** 3.2


def surface_profile(x, amp=0.24, wl=12.5):
    taper = np.clip((92.0 - x) / 12.0, 0.0, 1.0)
    return amp * taper * np.sin(2 * np.pi * x / wl)


def plume_thickness(x):
    """Resuspension is strongest where the bed is most worked and tapers both
    ways — a uniform band would imply the whole shelf lifts equally."""
    return 2.0 * np.exp(-((x - 44.0) / 30.0) ** 2)


def draw_section(ax, th, stage):
    ax.set_xlim(X0, X1); ax.set_ylim(Y0, Y1); ax.axis("off")

    x = np.linspace(X0, X1, 900)
    bed, surf = bed_profile(x), surface_profile(x)
    wet = bed < surf

    ax.fill_between(x, bed, surf, where=wet, color=th["water"], zorder=1, lw=0)
    ax.fill_between(x, Y0, bed, color=BED_TONE, zorder=2, lw=0)
    ax.plot(x, bed, color=BED_EDGE, lw=1.3, zorder=6)
    ax.plot(x[wet], surf[wet], color=CYAN, lw=1.7, zorder=4)

    # ---- stage 3: near-bed plume, densest at the bed and fading upward
    if stage >= 3:
        xp = np.linspace(2.0, 84.0, 500)
        bp, tp = bed_profile(xp), plume_thickness(xp)
        for k in range(8):
            ax.fill_between(xp, bp, bp + tp * (k + 1) / 8.0, color=CYAN_LT,
                            alpha=0.105, lw=0, zorder=3)

    # ---- driver 1: waves
    ax.annotate("", xy=(21.0, 1.35), xytext=(6.0, 1.35), zorder=8,
                arrowprops=dict(arrowstyle="-|>", color=CYAN, lw=1.5,
                                shrinkA=0, shrinkB=0))
    ax.text(6.0, 1.80, "waves", color=CYAN, fontsize=13, fontfamily=F_BODY,
            fontstyle="italic", zorder=8)
    # orbital ellipses flattening with depth — why waves matter at all in 6 m
    for yc, w, h in ((-1.10, 6.2, 1.85), (-3.00, 5.4, 1.05),
                     (-4.75, 4.7, 0.48), (-6.25, 4.2, 0.14)):
        ax.add_patch(Ellipse((32.0, yc), w, h, fill=False, ec=CYAN_LT, lw=1.1,
                             alpha=0.9, zorder=7))

    # ---- driver 2: currents
    ax.annotate("", xy=(22.0, -5.45), xytext=(4.0, -5.45), zorder=8,
                arrowprops=dict(arrowstyle="-|>", color=th["on_water"], lw=1.5,
                                alpha=0.9, shrinkA=0, shrinkB=0))
    ax.text(4.0, -5.02, "tidal + wind-driven current", color=th["on_water"],
            fontsize=10, fontfamily=F_BODY, fontstyle="italic", alpha=0.92,
            zorder=8)

    # ---- both, converging on one stress at the bed. The label sits below the
    # bed, otherwise dead space, and gives dark-on-pale contrast.
    bx0, bx1 = 26.0, 50.0
    xb = np.linspace(bx0, bx1, 100)
    ax.plot(xb, bed_profile(xb) + 0.09, color=ACCENT, lw=3.2,
            solid_capstyle="round", zorder=9)
    ax.text(bx0 + 1.0, bed_profile(np.array([bx0 + 1.0]))[0] - 0.55,
            "combined bed stress", color=ACCENT, fontsize=11.5,
            fontfamily=F_BODY, va="top", zorder=9)

    # ---- stage 3: the intake, and the two depths that differ
    if stage >= 3:
        iy = bed_profile(np.array([INTAKE_X]))[0]
        ax.add_patch(Polygon([[INTAKE_X - 1.5, iy], [INTAKE_X + 1.5, iy],
                              [INTAKE_X + 1.0, iy + 1.15],
                              [INTAKE_X - 1.0, iy + 1.15]], closed=True,
                             fc=th["on_water"], ec=INK_3, lw=1.0, zorder=12))
        px = np.linspace(INTAKE_X, 99.0, 200)
        ax.plot(px, bed_profile(px) + 0.18, color=INK_3, lw=3.4, zorder=10)
        ax.plot(px, bed_profile(px) + 0.18, color=th["on_water"], lw=1.7,
                zorder=11)
        ax.text(INTAKE_X - 2.8, iy + 1.15, "open intake", color=th["on_water"],
                fontsize=10.5, fontfamily=F_BODY, va="center", ha="right",
                zorder=10)

        # surface label above the waterline on paper; intake label below the bed
        # on carbonate — both on pale ground, both dark ink, neither in the water
        ax.annotate("what a satellite sees", xy=(80.0, 0.10), xytext=(64.0, 2.05),
                    color=th["ink_2"], fontsize=10.5, fontfamily=F_BODY, zorder=11,
                    arrowprops=dict(arrowstyle="-", color=th["ink_3"], lw=0.9,
                                    connectionstyle="arc3,rad=-0.3"))
        ax.annotate("what the plant pumps", xy=(INTAKE_X + 0.4, iy - 0.05),
                    xytext=(71.0, -6.85), color=th["ink_2"], fontsize=10.5,
                    fontfamily=F_BODY, zorder=11,
                    arrowprops=dict(arrowstyle="-", color=th["ink_3"], lw=0.9,
                                    connectionstyle="arc3,rad=-0.25"))

    ax.text(1.5, Y0 + 0.20, "6 m water depth · vertical exaggerated",
            color=INK_3, fontsize=8.5, fontfamily=F_MONO, va="bottom", zorder=8)


# ---------------------------------------------------------------- strip
def draw_strip(ax, th, stage, d, show_obs):
    """Real model output at the site. Stage 2 is bed stress against the erosion
    threshold; stage 3 morphs to concentration on the same clock, with stress
    ghosted behind on a faint right axis so the ghost stays readable as data.

    tau_max only — no wave/current decomposition. Which driver dominates is a
    property of the site, and this figure is shown to operators at many of them.
    """
    t = d["time"].astype("datetime64[s]")
    tau, cs, cb = d["tau_max"], d["C_surface"], d["C_bottom"]
    tau_cr = float(d["tau_cr_fine"])

    ax.set_xlim(t[0], t[-1])
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(RULE); ax.spines[s].set_linewidth(0.9)
    ax.tick_params(colors=th["ink_3"], labelsize=8.5, length=3, width=0.8)
    ax.xaxis.set_major_locator(mdates.DayLocator(bymonthday=(1, 6, 11, 16, 21, 26, 31)))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d %b"))
    for lb in ax.get_xticklabels() + ax.get_yticklabels():
        lb.set_fontfamily(F_MONO)

    if stage <= 2:
        ax.set_ylim(0, max(1.15, float(tau.max()) * 1.12))
        if stage == 2:
            ax.fill_between(t, tau_cr, tau, where=tau > tau_cr, color=ACCENT,
                            alpha=0.17, lw=0, zorder=2)
            ax.plot(t, tau, color=th["ink"], lw=1.3, zorder=4)
        ax.axhline(tau_cr, color=ACCENT, lw=1.2, ls=(0, (5, 3)), zorder=3)
        ax.text(t[-1], tau_cr, "  erosion\n  threshold", color=ACCENT, fontsize=9,
                fontfamily=F_BODY, va="center", ha="left", linespacing=1.25,
                zorder=5)
        ax.set_ylabel("bed stress  N/m²", color=th["ink_2"], fontsize=9.5,
                      fontfamily=F_BODY, labelpad=6)
    else:
        gh = ax.twinx()
        gh.set_xlim(t[0], t[-1]); gh.set_ylim(0, max(1.15, float(tau.max()) * 1.12))
        gh.fill_between(t, 0, tau, color=th["ink"], alpha=0.06, lw=0, zorder=1)
        gh.plot(t, tau, color=th["ink"], lw=0.9, alpha=0.18, zorder=1)
        gh.axhline(tau_cr, color=ACCENT, lw=0.9, ls=(0, (5, 3)), alpha=0.30, zorder=1)
        for s in ("top", "left", "bottom", "right"):
            gh.spines[s].set_visible(False)
        gh.set_yticks([])
        gh.text(t[-1], float(tau.max()) * 0.14, "  bed stress,\n  ghosted",
                color=th["ink_3"], fontsize=8.5, fontfamily=F_BODY, va="center",
                linespacing=1.25, zorder=2)

        ax.set_zorder(gh.get_zorder() + 1); ax.patch.set_visible(False)
        top = float(max(cb.max(), cs.max())) * 1.20
        ax.set_ylim(0, top)
        if show_obs and "obs_ntu" in d:
            ax.plot(d["obs_time"].astype("datetime64[s]"), d["obs_ntu"], "o",
                    ms=3.4, mfc="none", mec=th["ink_2"], mew=0.9, alpha=0.8,
                    zorder=6)
        ax.plot(t, cs, color=CYAN, lw=2.0, zorder=4)
        ax.plot(t, cb, color=NAVY, lw=2.0, zorder=5)
        ax.text(t[-1], top * 0.86, "  at the bed", color=NAVY, fontsize=9.5,
                fontfamily=F_BODY, va="center", zorder=6)
        ax.text(t[-1], top * 0.66, "  at the surface", color=CYAN, fontsize=9.5,
                fontfamily=F_BODY, va="center", zorder=6)
        ax.set_ylabel("turbidity  NTU", color=th["ink_2"], fontsize=9.5,
                      fontfamily=F_BODY, labelpad=6)


# ---------------------------------------------------------------- compose
CAPTION = ("which dominates depends on depth, exposure and tide — "
           "the model doesn't assume")
FOOTER = ("Soulsby (1997) combined wave–current bed stress · "
          "Partheniades (1965) excess-stress erosion · "
          "southern Arabian Gulf coast, 6 m depth · January 2022")


def build(stage, theme="deck", show_obs=False, dpi=200):
    th = THEME[theme]
    d = load()

    fig = plt.figure(figsize=th["figsize"], dpi=dpi)
    fig.patch.set_facecolor(th["ground"])

    # Axes geometry is identical at every stage so nothing shifts during the
    # build — the whole reason for exporting stages rather than animating.
    ax_sec = fig.add_axes([0.050, 0.410, 0.845, 0.560])
    ax_str = fig.add_axes([0.050, 0.150, 0.845, 0.210])
    for a in (ax_sec, ax_str):
        a.set_facecolor(th["ground"])

    draw_section(ax_sec, th, stage)
    draw_strip(ax_str, th, stage, d, show_obs)

    fig.text(0.050, 0.374, CAPTION, color=th["ink_2"], fontsize=9.5,
             fontfamily=F_BODY, fontstyle="italic", va="bottom")
    fig.text(0.050, 0.020, FOOTER, color=th["ink_3"], fontsize=7.4,
             fontfamily=F_MONO, va="bottom")

    suffix = "" if theme == "deck" else f"-{theme}"
    out = os.path.join(ASSET_DIR, f"turbidity-schematic-{stage}{suffix}.png")
    fig.savefig(out, dpi=dpi, facecolor=th["ground"])
    plt.close(fig)
    print(f"wrote {out}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--extract", action="store_true",
                    help="rebuild assets/tau-jan2022.npz from the model volume")
    ap.add_argument("--stage", type=int, choices=(1, 2, 3),
                    help="build one stage (default: all three)")
    ap.add_argument("--theme", default="deck", choices=tuple(THEME),
                    help="deck (16:9 slide graphic) or report (Asset 2, stub)")
    ap.add_argument("--obs", action="store_true",
                    help="overlay in-situ NTU — off until provenance clears")
    ap.add_argument("--dpi", type=int, default=200)
    a = ap.parse_args()

    if a.extract:
        extract()
        return

    register_fonts()
    for stage in ([a.stage] if a.stage else (1, 2, 3)):
        build(stage, theme=a.theme, show_obs=a.obs, dpi=a.dpi)


if __name__ == "__main__":
    main()
