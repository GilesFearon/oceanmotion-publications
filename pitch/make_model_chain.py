#!/usr/bin/env python3
"""
Ocean Motion Analytics — "how the models are built" figure module.

Renders the map figures for an eight-slide story that walks the modelling chain
from atmospheric forcing to a client-facing number. The slides themselves (the
headline, spec block, caption and progress rail) are native PowerPoint text and
live in make_chain_deck.py; this script produces only the pictures.

The chain is one-way and, at the last step, offline:

    ERA5 ------------+--------------------> CROCO ------+
                     +--------------------> WW3 <-------+  surface currents
    GLORYS --------> CROCO                                 + water level
    TPXO10 --------> CROCO
    25 CMEMS spectra -> WW3
    grid 291x131 ---> both
                            CROCO bottom currents -+
                            WW3 orbital velocity --+--> offline sediment model

Every figure is drawn from one storm: the shamal of 21 January 2022, the largest
event of the month at every link in the chain. The clock advances across the
slides because the lag *is* the product --- wind at 08:00, waves by 14:00, bed
stress by 18:30, plume at the surface before midnight. Freezing every panel at
one instant would show a decaying wind next to a plume that has not arrived yet.

Colour follows one rule: the colormap encodes the quantity, not the slide, so
wind and current share cmo.speed and the audience reads "same kind of thing"
across two slides without being told. ACCENT (#ff6a2b) never enters a colormap
-- it marks the thing being pointed at (the open boundary, the zoom box) and
nothing else.

Runs in the somisana_croco environment (needs cartopy + cmocean); the deck
builder runs in base (needs python-pptx). The two never run in one interpreter.

Usage:   python make_model_chain.py --extract          # ~2.4 GB read, once
         python make_model_chain.py --slide 6
         python make_model_chain.py --all
Output:  assets/chain-stills.npz  (gitignored)
         assets/chain-<n>-<name>.png
"""

import argparse
import os

import numpy as np

# ------------------------------------------------------------------ paths
HERE = os.path.dirname(os.path.abspath(__file__))
ASSET_DIR = os.path.join(HERE, "assets")
FONT_DIR = os.path.join(HERE, "fonts")

MODELS = os.path.expanduser("~/code/oceanmotion-models/configs/gulf_01")
CROCO_H = os.path.join(MODELS, "croco_v1.3.1/hindcast")
GRD = os.path.join(CROCO_H, "GRID/croco_grd.nc")
BRY = os.path.join(CROCO_H, "GLORYS/croco_bry_GLORYS_Y2022M01.nc")
SURF = os.path.join(CROCO_H, "C04_I02_GLORYS_ERA5/output/croco_avg_surf_Y2022M01.nc")
WW3 = os.path.join(MODELS, "ww3_v6.07.1/hindcast/RUN_02/output/ww3.202201.nc")
SPEC_DIR = os.path.join(MODELS, "ww3_v6.07.1/hindcast/SPEC_CMEMS/2022_01")
TURB = os.path.join(MODELS, "turbidity/hindcast/calib_02/output/"
                            "turbidity_3d_Y2022M01_mem03.nc")
ERA5 = os.path.expanduser("~/code/somisana-croco/DATASETS_CROCOTOOLS/ERA5/"
                          "gulf_for_croco")

CACHE = os.path.join(ASSET_DIR, "chain-stills.npz")

# ------------------------------------------------------------------ tokens
# Mirrored from build_template.py. Duplicated rather than imported because that
# module builds and saves the template at import time (no __main__ guard).
ABYSS   = "#050f1c"
NAVY    = "#091c33"
CYAN    = "#4fc3d7"
ACCENT  = "#ff6a2b"
PAPER   = "#f4efe3"
INK     = "#0b1420"
INK_2   = "#4a5665"
INK_3   = "#8a94a2"
RULE    = "#d6cdb6"

F_DISPLAY, F_BODY, F_MONO = "Instrument Serif", "IBM Plex Sans", "IBM Plex Mono"

# Land is drawn in the deck's own ground with the coast carried by a line, not
# as a filled tone. GSHHS covers nearly the whole frame at this extent, so a
# tinted land makes the map read as a pasted rectangular panel; matching the
# ground lets it float, and the coastline does the work on its own.
LAND_FILL, LAND_EDGE = "#f4efe3", "#a2957c"

# ------------------------------------------------------------------ the storm
# 21 January 2022. Hours are indices into the January hourly files (0 = 1 Jan
# 00:00). Verified from the output, not chosen by eye:
#   wind   domain-mean 9.1 m/s, gusting 17.6, from the NW      08:00
#   waves  domain max hs 3.81 m                                14:00
#   bed    tau_max 1.04 N/m2 at the site, month's highest      18:30
#   plume  C_bottom 17.8 NTU, C_surface 12.0 against 3 NTU bg  21:30
# Circulation has no storm peak of its own -- Gulf surface currents are tidal,
# and the domain-mean maximum on this day falls at 00:00, before the wind. Using
# it would run the clock backwards, so slide 5 takes the midpoint of the wind ->
# wave interval and its caption concedes the point.
DAY = 20                       # 0-based day index of 21 January
H_WIND = DAY * 24 + 8
H_CURR = DAY * 24 + 12
H_WAVE = DAY * 24 + 14
H_TURB = DAY * 24 + 21
D_BRY = 20                     # daily GLORYS record for 21 Jan

# Slide 4 zooms on the southern shelf, deliberately centred west of the client
# site: same coastline, same argument about resolution, no finger pointed at a
# facility. See go-to-market.md on anonymising Gulf work in Gulf pitches.
ZOOM = [52.8, 54.6, 23.9, 25.3]

# Surface speed is p50 0.08, p95 0.55, max 2.2 m/s -- a linear scale would render
# 95% of the Gulf flat. BoundaryNorm on non-uniform ticks is how plot_bathy.py
# already handles bathymetry; the same trick is load-bearing here.
LEVELS = {
    "wind":  [0, 2, 4, 6, 8, 10, 12, 14, 16, 18],
    "curr":  [0, .05, .1, .15, .2, .3, .4, .6, .8, 1.2],
    "hs":    [0, .5, 1, 1.5, 2, 2.5, 3, 3.5, 4],
    "turb":  [3, 4, 5, 6, 7, 8, 10, 12, 15],
    "depth": [0, 10, 20, 30, 40, 50, 60, 80, 100, 200, 500, 1000],
}


# ------------------------------------------------------------------ extract
def _rho(u, v):
    """CROCO u/v staggered points -> rho points, with NaN at the outer edges."""
    ny, nx = u.shape[0], v.shape[1]
    ur = np.full((ny, nx), np.nan)
    ur[:, 1:-1] = 0.5 * (u[:, :-1] + u[:, 1:])
    vr = np.full((ny, nx), np.nan)
    vr[1:-1, :] = 0.5 * (v[:-1, :] + v[1:, :])
    return ur, vr


def _z_rho(h, Cs, s, hc, zeta=0.0):
    """NEW_S_COORD vertical levels: z = zeta + (zeta+h) * (hc*s + h*Cs)/(hc+h)."""
    S = (hc * s[:, None] + h[None, :] * Cs[:, None]) / (hc + h[None, :])
    return zeta + (zeta + h[None, :]) * S


def extract():
    """Pull the six still frames out of ~2.4 GB of model output into ~3 MB.

    Float32 rather than the quantised uint8 used for the animation: there are
    only six frames, and keeping full precision means contour levels can be
    retuned during design without re-reading the source files.
    """
    import xarray as xr

    out = {}

    g = xr.open_dataset(GRD)
    out["lon"] = g.lon_rho.values.astype("f4")
    out["lat"] = g.lat_rho.values.astype("f4")
    out["mask"] = g.mask_rho.values.astype("i1")
    out["h"] = g.h.values.astype("f4")
    ang = g.angle.values
    cos_a, sin_a = np.cos(ang), np.sin(ang)

    # --- 2. atmosphere: ERA5 on its native 0.25 deg grid, unsmoothed. The
    # blockiness is the point; slide 4 answers it.
    u10 = xr.open_dataset(f"{ERA5}/U10M_Y2022M1.nc").U10M
    v10 = xr.open_dataset(f"{ERA5}/V10M_Y2022M1.nc").V10M
    sub = dict(lon=slice(46.5, 59.0), lat=slice(31.8, 22.0))
    if float(u10.lat[0]) < float(u10.lat[-1]):
        sub["lat"] = slice(22.0, 31.8)
    u10, v10 = u10.sel(**sub), v10.sel(**sub)
    out["era5_lon"] = u10.lon.values.astype("f4")
    out["era5_lat"] = u10.lat.values.astype("f4")
    out["era5_u"] = u10.isel(time=H_WIND).values.astype("f4")
    out["era5_v"] = v10.isel(time=H_WIND).values.astype("f4")

    # --- 3. boundaries: the temperature curtain is the module's only view of
    # the vertical, so it carries the "15 levels" claim on its own.
    b = xr.open_dataset(BRY, decode_times=False)
    east = np.where(out["mask"][:, -1] == 1)[0]
    hb = out["h"][east, -1].astype("f8")
    out["bry_temp"] = b.temp_east.values[D_BRY][:, east].astype("f4")
    out["bry_lat"] = out["lat"][east, -1]
    out["bry_z"] = _z_rho(hb, b.Cs_rho.values, b.s_rho.values,
                          float(np.ravel(b.hc.values)[0])).astype("f4")
    out["bry_h"] = hb.astype("f4")

    # Tides are stored as 10 harmonic constituents with no phase reference in
    # the file, so reconstructing an absolute trace would be guesswork. The
    # model's own boundary elevation is the same tide, correctly phased, and is
    # a real output -- the spec block names the constituents.
    s = xr.open_dataset(SURF, decode_times=False)
    jb = east[len(east) // 2]
    out["tide"] = s.zeta.values[17 * 24:23 * 24, jb, -1].astype("f4")

    # --- 5. circulation: rotated from grid axes to east/north.
    u = s.u.isel(time=H_CURR).values
    v = s.v.isel(time=H_CURR).values
    ur, vr = _rho(u, v)
    out["croco_u"] = (ur * cos_a - vr * sin_a).astype("f4")
    out["croco_v"] = (vr * cos_a + ur * sin_a).astype("f4")

    # --- 6. waves
    w = xr.open_dataset(WW3)
    out["hs"] = w.hs.isel(time=H_WAVE).values.astype("f4")
    out["dp"] = w.dp.isel(time=H_WAVE).values.astype("f4")

    # one directional spectrum, 32 frequencies x 24 directions, at the peak
    sp = xr.open_dataset(os.path.join(SPEC_DIR, "cmems.lon57.00.lat24.60.spec.nc"))
    ef = [k for k in sp.variables if k.lower() in ("efth", "ef", "spectra")]
    if ef:
        e = sp[ef[0]]
        it = min(H_WAVE // 3, e.shape[0] - 1)   # spectra are 3-hourly
        out["spec"] = np.squeeze(e.isel(time=it).values).astype("f4")
        out["spec_f"] = sp.frequency.values.astype("f4")
        out["spec_d"] = sp.direction.values.astype("f4")

    # --- 7. turbidity
    t = xr.open_dataset(TURB)
    out["turb"] = t.C_surface.isel(time=H_TURB).values.astype("f4")

    os.makedirs(ASSET_DIR, exist_ok=True)
    np.savez_compressed(CACHE, **out)
    mb = os.path.getsize(CACHE) / 1e6
    print(f"wrote {CACHE} ({mb:.1f} MB)")
    for k, v in sorted(out.items()):
        print(f"  {k:12s} {np.shape(v)}")


def load():
    if not os.path.exists(CACHE):
        raise SystemExit(f"{CACHE} missing — run with --extract first "
                         "(needs the model output on this machine).")
    return dict(np.load(CACHE))




# ------------------------------------------------------------------ style
def register_fonts():
    """Make the vendored brand faces available to matplotlib in whichever env
    this runs in. Silent fallback: a missing face costs typography, not a plot."""
    from matplotlib import font_manager
    if not os.path.isdir(FONT_DIR):
        return
    for f in sorted(os.listdir(FONT_DIR)):
        if f.endswith(".ttf"):
            try:
                font_manager.fontManager.addfont(os.path.join(FONT_DIR, f))
            except Exception:
                pass


def _mercator_aspect(ext):
    """Width/height of the extent in projected coordinates, so the figure can be
    sized to the map exactly and the axes can fill it edge to edge."""
    import cartopy.crs as ccrs
    p = ccrs.Mercator()
    x0, y0 = p.transform_point(ext[0], ext[2], ccrs.PlateCarree())
    x1, y1 = p.transform_point(ext[1], ext[3], ccrs.PlateCarree())
    return abs(x1 - x0) / abs(y1 - y0)


def domain_extent(d, pad=0.15, aspect=None, bias=0.5, pad_n=0.0):
    """Extent around the model domain, optionally widened to a target aspect.

    The domain is 1103 x 921 km -- 1.20:1, near square -- so it can never fill a
    16:9 slide. `aspect=16/9` pads longitude instead of cropping, which buys a
    full-bleed map whose extra width is flat land: exactly the neutral ground
    headline and spec text want to sit on."""
    # pad_n opens sky above the head of the Gulf so the full-bleed variant does
    # not run the coastline up into the rail. Applied before the aspect fit, so
    # the extra width needed to stay 16:9 is computed from the taller frame.
    ext = [float(d["lon"].min()) - pad, float(d["lon"].max()) + pad,
           float(d["lat"].min()) - pad, float(d["lat"].max()) + pad + pad_n]
    if aspect is None:
        return ext
    have = _mercator_aspect(ext)
    if aspect > have:
        grow = (ext[1] - ext[0]) * (aspect / have - 1.0)
        # bias > 0.5 puts most of the new width on the west side, sliding the
        # Gulf right and leaving the left third as flat land -- the ground the
        # headline and spec column sit on.
        ext[0] -= grow * bias
        ext[1] += grow * (1.0 - bias)
    return ext


def new_map(ext, height=6.0, transparent=False):
    """A bare map: no frame, no graticule, no tick labels. Everything the deck
    needs to say about it is native PowerPoint text sitting on top."""
    import matplotlib.pyplot as plt
    import cartopy.crs as ccrs
    import cartopy.feature as cfeature

    asp = _mercator_aspect(ext)
    ground = "none" if transparent else PAPER
    fig = plt.figure(figsize=(height * asp, height), facecolor=ground)
    ax = fig.add_axes([0, 0, 1, 1], projection=ccrs.Mercator())
    ax.set_extent(ext, crs=ccrs.PlateCarree())
    # Transparent lets the slide's own ground show through everywhere the model
    # is not, so the map floats as a shape instead of sitting in a visible box.
    ax.set_facecolor(ground)
    ax.patch.set_alpha(0.0 if transparent else 1.0)
    ax.spines["geo"].set_visible(False)

    # GSHHS full resolution, already cached locally. Same source crocotools_py's
    # plot_land() uses; drawn directly here only to control the colours.
    land = cfeature.GSHHSFeature(scale="f")
    ax.add_feature(land, facecolor=LAND_FILL, edgecolor=LAND_EDGE,
                   linewidth=0.6, zorder=3)
    return fig, ax


def trunc(cmap, lo=0.0, hi=1.0, n=256):
    """Chop the washed-out end off a colormap.

    cmo.amp and cmo.turbid both start at near-white, which on a PAPER ground is
    indistinguishable from the sea outside the model domain -- a calm northern
    Gulf then reads as "not modelled". Starting the ramp part-way in keeps the
    lowest class visibly a colour."""
    import matplotlib.colors as mplc
    return mplc.LinearSegmentedColormap.from_list(
        f"{cmap.name}_t", cmap(np.linspace(lo, hi, n)))


def shade(ax, d, field, levels, cmap, mask_land=True):
    """pcolormesh on non-uniform levels. BoundaryNorm rather than a linear scale
    because most of these fields are strongly skewed -- see LEVELS."""
    import matplotlib.colors as mplc
    import cartopy.crs as ccrs
    v = np.asarray(field, dtype="f8")
    if mask_land:
        v = np.where(d["mask"].astype(bool), v, np.nan)
    return ax.pcolormesh(d["lon"], d["lat"], v, cmap=cmap,
                         norm=mplc.BoundaryNorm(np.array(levels), ncolors=256),
                         transform=ccrs.PlateCarree(), zorder=2)


def colorbar(fig, art, levels, label, rect=(0.045, 0.115, 0.300, 0.019),
             every=2):
    """Horizontal bar tucked into the empty lower-left corner of the frame. The
    Gulf runs diagonally, so that corner is outside the domain on every one of
    these maps -- free space inside the picture rather than a sidebar beside it."""
    cax = fig.add_axes(rect)
    # Every level gets a colour band, but only every nth gets a label -- nine
    # numbers under a 3 cm bar run into each other.
    cb = fig.colorbar(art, cax=cax, orientation="horizontal",
                      ticks=list(levels)[::every], spacing="uniform")
    cb.outline.set_visible(False)
    cb.ax.tick_params(labelsize=8, length=2.5, width=0.7, color=INK_3,
                      labelcolor=INK_2, pad=2)
    for t in cb.ax.get_xticklabels():
        t.set_fontfamily(F_MONO)
    cb.set_label(label, fontsize=9, color=INK_2, fontfamily=F_BODY, labelpad=6)
    cb.ax.xaxis.set_label_position("top")
    return cb


def vectors(ax, d, u, v, lon=None, lat=None, skip=6, scale=14, color=INK_2,
            where=None):
    """Sparse direction arrows.

    `where` drops arrows below a magnitude threshold: an arrow in near-calm water
    is noise pointing in a direction nobody cares about, and a field of them
    reads as clutter rather than as structure."""
    import cartopy.crs as ccrs
    lon = d["lon"] if lon is None else lon
    lat = d["lat"] if lat is None else lat
    if lon.ndim == 1:
        lon, lat = np.meshgrid(lon, lat)
    u, v = np.asarray(u, "f8").copy(), np.asarray(v, "f8").copy()
    if where is not None:
        u[~where] = np.nan
        v[~where] = np.nan
    sl = (slice(None, None, skip), slice(None, None, skip))
    return ax.quiver(lon[sl], lat[sl], u[sl], v[sl],
                     scale=scale, width=0.0022, color=color, alpha=0.42,
                     transform=ccrs.PlateCarree(), zorder=4)


def save(fig, name, dpi=200, transparent=False):
    os.makedirs(ASSET_DIR, exist_ok=True)
    out = os.path.join(ASSET_DIR, f"chain-{name}.png")
    fig.savefig(out, dpi=dpi, transparent=transparent,
                facecolor="none" if transparent else PAPER)
    print(f"wrote {out} ({os.path.getsize(out) / 1e3:.0f} kB)")
    return out


# ------------------------------------------------------------------ slides
WIDE = 16 / 9


def slide_6(d, wide=False):
    """Waves ride the currents we just solved. WW3 hs at the 21 Jan peak, with
    peak-direction arrows -- the only field in the module with a direction worth
    drawing, since the whole point is that the sea state is organised."""
    import cmocean.cm as cmo
    ext = (domain_extent(d, aspect=WIDE, bias=0.86, pad_n=1.0) if wide
           else domain_extent(d))
    fig, ax = new_map(ext, transparent=not wide)
    art = shade(ax, d, d["hs"], LEVELS["hs"], trunc(cmo.amp, 0.14))
    th = np.deg2rad(np.asarray(d["dp"], dtype="f8"))
    wet = d["mask"].astype(bool) & (np.asarray(d["hs"]) > 0.6)
    # dp is the direction waves travel FROM, nautical convention
    vectors(ax, d, -np.sin(th), -np.cos(th), skip=11, scale=30, where=wet)
    # In the wide layout the left third is reserved for type, so the bar moves
    # to the opposite corner, over the Gulf of Oman.
    colorbar(fig, art, LEVELS["hs"], "significant wave height  (m)",
             rect=(0.700, 0.115, 0.200, 0.019) if wide
             else (0.045, 0.115, 0.300, 0.019))
    return save(fig, "6-waves-wide" if wide else "6-waves",
                transparent=not wide)


SLIDES = {6: slide_6}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--extract", action="store_true",
                    help="rebuild assets/chain-stills.npz from the model output")
    ap.add_argument("--slide", type=int, choices=sorted(SLIDES))
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--dpi", type=int, default=200)
    ap.add_argument("--wide", action="store_true",
                    help="also render the full-bleed 16:9 variant")
    args = ap.parse_args()

    if args.extract:
        extract()
        if not (args.slide or args.all):
            return

    import matplotlib
    matplotlib.use("Agg")
    register_fonts()
    import matplotlib.pyplot as plt
    plt.rcParams["font.family"] = F_BODY

    d = load()
    todo = sorted(SLIDES) if args.all else [args.slide]
    for n in todo:
        SLIDES[n](d)
        if args.wide:
            SLIDES[n](d, wide=True)


if __name__ == "__main__":
    main()
