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

The chain schematic that opens the deck is NOT built here: it is drawn as native
PowerPoint shapes in make_chain_deck.py, so its boxes and arrows stay editable.
Only the thumbnails inside its boxes come from this module.
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
AVG = os.path.join(CROCO_H, "C04_I02_GLORYS_ERA5/output/croco_avg_Y2022M01.nc")
# Boreal summer, for the 3D block only. January in the Gulf is nearly mixed, so
# a winter block is a slab of one colour and says nothing about being 3D. This
# is indicative -- it deliberately does not correspond to the January storm.
AVG_SUMMER = os.path.join(CROCO_H,
                          "C04_I01_GLORYS_ERA5/output/croco_avg_Y2022M08.nc")
AVG_SUMMER_STEP = 58          # 6-hourly output; mid-August, local afternoon
WW3 = os.path.join(MODELS, "ww3_v6.07.1/hindcast/RUN_02/output/ww3.202201.nc")
SPEC_DIR = os.path.join(MODELS, "ww3_v6.07.1/hindcast/SPEC_CMEMS/2022_01")
TURB = os.path.join(MODELS, "turbidity/hindcast/calib_02/output/"
                            "turbidity_3d_Y2022M01_mem03.nc")
ERA5 = os.path.expanduser("~/code/somisana-croco/DATASETS_CROCOTOOLS/ERA5/"
                          "gulf_for_croco")
# Raw GLORYS, 1/12 deg on 50 z-levels. The boundary section is drawn from this
# rather than from croco_bry_*.nc: the bry file has already been squeezed onto
# 15 terrain-following layers, which is fine inside the Gulf but badly stretched
# over the 1500 m of the Gulf of Oman, where the section actually goes.
GLORYS_RAW = os.path.expanduser("~/code/somisana-croco/DATASETS_CROCOTOOLS/"
                                "GLORYS/gulf/2022_01.nc")

OBS_CSV = os.path.expanduser("~/code/oceanmotion-models/datasets/ntu_obs/"
                             "NTU_obs.csv")

# Validation. Both are model-vs-satellite, both already exist in the model repo;
# rebuilt here only so they carry the deck's typography.
#   SST : 2015-2025 surface output from the long C04_I01 hindcast against OSTIA
#         L4 at one Gulf point.
#   Hs  : WW3 RUN_02 co-located with CMEMS L3 altimetry, 26 347 pairs.
LONG_SURF = os.path.expanduser(
    "~/code/oceanmotion-models/configs/gulf_01/croco_v1.3.1/hindcast/"
    "C04_I01_GLORYS_ERA5/output")
OSTIA_CSV = os.path.expanduser(
    "~/projects/foresea/data/CMEMS_GLO_OSTIA_L4/gulf/"
    "ts_OSTIA_temp_54.12E_24.31N.csv")
OSTIA_LONLAT = (54.12, 24.31)
# MODIS Aqua surface reflectance, h22v06 tile. Aqua passes the Gulf around
# 10:00 UTC, and the 21 January plume does not reach the surface until about
# 21:30 -- so the honest comparison is the morning after the storm, not the
# storm day. 22 Jan is 93% cloud-free over the box (21 Jan is 100%, but too
# early to show anything).
MODIS_DIR = "/media/external_1/MODIS/gulf/"
MODIS_TOOLS = os.path.expanduser(
    "~/code/oceanmotion-models/configs/gulf_01/turbidity/hindcast/calib_02/"
    "postprocess")
# 7 February 2022: a different event from the January storm the rest of the
# module follows, chosen because it is a far cleaner scene. Cloud and dust sit
# over the Gulf through most of the events worth looking at, which is itself
# worth saying out loud on the slide.
MODIS_DATE = (2022, 2, 7)
MODIS_HOUR = 10
MODIS_EXTENT = [49.3, 56.6, 22.8, 28.0]
# The h22v06 tile runs out at about 55.4 E, which shows as a hard vertical edge.
# Cached wide, plotted narrow.
# East limit set by the swath, not by taste: coverage on 7 Feb is 58% at 55.1
# and nil by 55.5. 55.35 keeps Dubai in frame without a wedge of empty tile.
MODIS_PLOT_EXTENT = [49.9, 55.35, 23.2, 27.4]

HS_COLOC = os.path.expanduser(
    "~/code/oceanmotion-models/configs/gulf_01/ww3_v6.07.1/hindcast/RUN_02/"
    "postprocess/colocated_hs.nc")

CACHE = os.path.join(ASSET_DIR, "chain-stills.npz")
ANIM = os.path.join(ASSET_DIR, "chain-frames.npz")

# The cascade window, chosen by searching January for the pair of hours that
# minimises the loop seam: 17 Jan 14:00 to 25 Jan 12:00. Domain-mean wind is
# 2.88 and 2.86 m/s at the two ends and site turbidity is at the 3 NTU
# background at both, so the loop returns to its own start state. A storm
# animation otherwise cannot do this -- the hero GIF only manages it because its
# field is stationary and the seam can be built out by construction.
# Picked over a longer, even cleaner 220 h window because that one spent a third
# of its length on nothing happening.
ANIM_H0, ANIM_H1 = 398, 588

# Sampled, never drawn. The strip on the closing loop plots point series because
# the cascade is local: a domain maximum hops between locations and peaks in the
# wrong order (turbidity before wind), which would contradict the story the rest
# of the module tells. Labelled by depth only -- no marker, no coordinates.
SITE_LON, SITE_LAT = 54.0723, 24.3689

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
# Kept small on purpose: at 1.8 deg across, 50-odd cells render as grey hatching
# rather than as a mesh. 0.8 x 0.63 deg is ~23 x 20 cells, big enough that a
# single cell is legible and a 0.25 deg ERA5 box visibly swallows about fifty.
ZOOM = [53.15, 53.95, 24.15, 24.78]

# The block cut out for the 3D view on slide 5: the southern Gulf, viewed from
# the north-east so the shelf climbs away from the camera toward the Abu Dhabi
# coast. Outlined in ACCENT on the surface map so the two figures on that slide
# are visibly the same water.
# The 3D block's true footprint, not a nominal box: the trimmed index window
# spans this, and it contains the AGRIF nest almost exactly. One region shared
# by slide 4's inset and slide 5's cutaway, so the two are visibly the same
# water rather than approximately so.
BLOCK_EXT = [51.75, 55.25, 23.35, 26.35]

# The refined grid: 140 x 128 at ~1.2 km, a 3x AGRIF nest on the southern
# shelf. Its point on slide 4 is not this particular nest but that nesting is
# available at all -- resolution is a choice per site, not a property of the
# system.
NEST_GRD = os.path.join(CROCO_H, "GRID.1/croco_grd.nc.1")
NEST_RED = "#c62828"
BLOCK_ETA = slice(11, 79)      # index window covering BLOCK_EXT
BLOCK_XI = slice(198, 269)     # 68 x 71 cells, 3.2 to 82 m

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
    import pandas as pd

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

    # --- the same boundary, sampled from raw GLORYS on its own z-levels
    gl = xr.open_dataset(GLORYS_RAW)
    blon = xr.DataArray(out["lon"][east, -1].astype("f8"), dims="pt")
    blat = xr.DataArray(out["lat"][east, -1].astype("f8"), dims="pt")
    sec = gl.isel(time=D_BRY).interp(longitude=blon, latitude=blat)
    out["g_depth"] = gl.depth.values.astype("f4")
    out["g_temp"] = sec.thetao.values.astype("f4")
    out["g_salt"] = sec.so.values.astype("f4")
    out["g_lat"] = out["lat"][east, -1]
    out["g_lon"] = out["lon"][east, -1]

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

    # --- the AGRIF nest, for slide 4's second inset
    with xr.open_dataset(NEST_GRD) as ng:
        out["n_lon"] = ng.lon_rho.values.astype("f4")
        out["n_lat"] = ng.lat_rho.values.astype("f4")
        out["n_h"] = ng.h.values.astype("f4")
        out["n_mask"] = ng.mask_rho.values.astype("i1")
        out["n_dx"] = np.float64(np.mean(1.0 / ng.pm.values))

    # --- 3D block for slide 5. The only read from the 12 GB full-depth file,
    # and only a 68 x 71 x 15 window of one hour of it.
    av = xr.open_dataset(AVG, decode_times=False)
    blk = dict(eta_rho=BLOCK_ETA, xi_rho=BLOCK_XI)
    out["b_h"] = av.h.isel(**blk).values.astype("f4")
    out["b_mask"] = av.mask_rho.isel(**blk).values.astype("i1")
    out["b_lon"] = av.lon_rho.isel(**blk).values.astype("f4")
    out["b_lat"] = av.lat_rho.isel(**blk).values.astype("f4")
    out["b_pm"] = av.pm.isel(**blk).values.astype("f4")
    out["b_pn"] = av.pn.isel(**blk).values.astype("f4")
    out["b_temp"] = av.temp.isel(time=H_CURR, **blk).values.astype("f4")
    out["b_salt"] = av.salt.isel(time=H_CURR, **blk).values.astype("f4")
    bu = av.u.isel(time=H_CURR, eta_rho=BLOCK_ETA).values
    bv = av.v.isel(time=H_CURR, xi_rho=BLOCK_XI).values
    out["b_u"] = bu[:, :, BLOCK_XI.start - 1:BLOCK_XI.stop].astype("f4")
    out["b_v"] = bv[:, BLOCK_ETA.start - 1:BLOCK_ETA.stop, :].astype("f4")
    # The avg file carries sc/Cs directly rather than theta_s/theta_b, which is
    # all _z_rho needs: Vtransform 2 is z = zeta + (zeta+h)(hc*s + h*Cs)/(hc+h).
    out["b_sc_w"] = av.sc_w.values.astype("f8")
    out["b_Cs_w"] = av.Cs_w.values.astype("f8")
    out["b_hc"] = np.float64(np.ravel(av.hc.values)[0])

    # nearest wet grid cell to the observation point
    dist = np.where(out["mask"].astype(bool),
                    (out["lon"] - SITE_LON) ** 2 + (out["lat"] - SITE_LAT) ** 2,
                    np.inf)
    sj, si = np.unravel_index(np.argmin(dist), dist.shape)
    out["site_ji"] = np.array([sj, si])
    out["site_lonlat"] = np.array([out["lon"][sj, si], out["lat"][sj, si]])
    out["site_depth"] = np.float64(out["h"][sj, si])

    # August: the 3D block, and the surface currents for the same hour, so the
    # map beside the block shows the same water moving the same way.
    with xr.open_dataset(AVG_SUMMER, decode_times=False) as av2:
        out["b_temp_aug"] = av2.temp.isel(time=AVG_SUMMER_STEP,
                                          **blk).values.astype("f4")
        out["b_sc_w_aug"] = av2.sc_w.values.astype("f8")
        out["b_Cs_w_aug"] = av2.Cs_w.values.astype("f8")
        out["b_hc_aug"] = np.float64(np.ravel(av2.hc.values)[0])
        ua = av2.u.isel(time=AVG_SUMMER_STEP, s_rho=-1).values
        va = av2.v.isel(time=AVG_SUMMER_STEP, s_rho=-1).values
        ur, vr = _rho(ua, va)
        out["croco_u_aug"] = (ur * cos_a - vr * sin_a).astype("f4")
        out["croco_v_aug"] = (vr * cos_a + ur * sin_a).astype("f4")
        # The 3D block is drawn in grid axes, not compass axes, so it needs the
        # unrotated xi/eta components -- rotating them to east/north and back
        # would just be a round trip.
        out["b_u_aug"] = ur[BLOCK_ETA, BLOCK_XI].astype("f4")
        out["b_v_aug"] = vr[BLOCK_ETA, BLOCK_XI].astype("f4")
        out["aug_time"] = np.int64(
            (pd.Timestamp("1993-01-01")
             + pd.to_timedelta(float(av2.time.values[AVG_SUMMER_STEP]), "s")
             - pd.Timestamp("1970-01-01")).total_seconds())

    # --- 7a. the five ensemble members at the observation point, for the
    # calibration panel. LABELS L/ML/M/MH/H follow calib_02's own naming.
    # January and February together. The in-situ record stops on 31 January, so
    # February carries model spread and no observations -- which is the point:
    # the moorings pin the first month, the satellite gives an independent look
    # at the second.
    ens, ctime = [], None
    for k in range(1, 6):
        member = []
        for mon in ("Y2022M01", "Y2022M02"):
            f = TURB.replace("Y2022M01", mon).replace("mem03", f"mem{k:02d}")
            with xr.open_dataset(f) as t5:
                member.append(t5.C_surface.values[:, sj, si].astype("f4"))
                if ctime is None or k == 1:
                    pass
        ens.append(np.concatenate(member))
    tt = []
    for mon in ("Y2022M01", "Y2022M02"):
        with xr.open_dataset(TURB.replace("Y2022M01", mon)) as t5:
            tt.append(pd.to_datetime(t5.time.values))
    ctime = tt[0].append(tt[1])
    out["cal_ens"] = np.stack(ens)
    out["cal_t"] = ((ctime - pd.Timestamp("1970-01-01")).total_seconds()
                    .values.astype("f8"))

    obs = pd.read_csv(OBS_CSV, header=None, usecols=[0, 1],
                      names=["time", "ntu"]).dropna()
    ot = pd.to_datetime(obs["time"])
    out["cal_obs_t"] = ((ot - pd.Timestamp("1970-01-01")).dt.total_seconds()
                        .values.astype("f8"))
    out["cal_obs"] = obs["ntu"].values.astype("f4")

    # --- 7. turbidity
    t = xr.open_dataset(TURB)
    out["turb"] = t.C_surface.isel(time=H_TURB).values.astype("f4")

    # --- validation: SST against OSTIA, Hs against altimetry
    out.update(_extract_validation(out, xr, pd))

    # Merge onto whatever is already cached rather than replacing it. The
    # extract composes from half a dozen sources and some live on an external
    # drive; if one is offline this run, its keys should survive from the last
    # run instead of silently vanishing and breaking a figure three steps later.
    os.makedirs(ASSET_DIR, exist_ok=True)
    if os.path.exists(CACHE):
        prev = dict(np.load(CACHE, allow_pickle=True))
        kept = [k for k in prev if k not in out]
        if kept:
            print(f"  carried forward {len(kept)} key(s) from the previous "
                  f"cache: {', '.join(sorted(kept)[:6])}"
                  f"{' …' if len(kept) > 6 else ''}")
        prev.update(out)
        out = prev
    np.savez_compressed(CACHE, **out)
    mb = os.path.getsize(CACHE) / 1e6
    print(f"wrote {CACHE} ({mb:.1f} MB)")
    for k, v in sorted(out.items()):
        print(f"  {k:12s} {np.shape(v)}")


def extract_anim():
    """168 hourly frames x 4 fields for the cascade loop.

    uint8, quantised to the display levels. That is lossless here -- the GIF
    palette forces the same quantisation anyway -- and it turns a 102 MB float32
    array into 20 MB. Gitignored: it is a binary that changes whenever a colour
    level is retuned, which is exactly what should not enter git history. The
    rendered GIF is the artefact worth keeping.
    """
    import xarray as xr

    h0, h1 = ANIM_H0, ANIM_H1
    out = {"h0": h0, "h1": h1}

    def q(a, levels):
        """Bucket into the display levels: index of the band each value falls in."""
        return np.digitize(np.asarray(a, "f8"), np.array(levels[1:-1])).astype("u1")

    g = xr.open_dataset(GRD)
    ang = g.angle.values
    cos_a, sin_a = np.cos(ang), np.sin(ang)

    u10 = xr.open_dataset(f"{ERA5}/U10M_Y2022M1.nc").U10M
    v10 = xr.open_dataset(f"{ERA5}/V10M_Y2022M1.nc").V10M
    sub = dict(lon=slice(46.5, 59.0), lat=slice(31.8, 22.0))
    if float(u10.lat[0]) < float(u10.lat[-1]):
        sub["lat"] = slice(22.0, 31.8)
    uu = u10.sel(**sub).isel(time=slice(h0, h1)).values
    vv = v10.sel(**sub).isel(time=slice(h0, h1)).values
    wspd = np.hypot(uu, vv)
    out["f_wind"] = q(wspd, LEVELS["wind"])
    elon = u10.sel(**sub).lon.values
    elat = u10.sel(**sub).lat.values
    ej = int(np.argmin(np.abs(elat - SITE_LAT)))
    ei = int(np.argmin(np.abs(elon - SITE_LON)))
    out["s_wind"] = wspd[:, ej, ei].astype("f4")

    sf = xr.open_dataset(SURF, decode_times=False)
    u = sf.u.isel(time=slice(h0, h1)).values
    v = sf.v.isel(time=slice(h0, h1)).values
    nt = u.shape[0]
    spd = np.empty((nt, 131, 291), "f4")
    for t in range(nt):
        ur, vr = _rho(u[t], v[t])
        spd[t] = np.hypot(ur * cos_a - vr * sin_a, vr * cos_a + ur * sin_a)
    out["f_curr"] = q(spd, LEVELS["curr"])
    dist = ((g.lon_rho.values - SITE_LON) ** 2 +
            (g.lat_rho.values - SITE_LAT) ** 2)
    dist = np.where(g.mask_rho.values.astype(bool), dist, np.inf)
    sj, si = np.unravel_index(np.argmin(dist), dist.shape)
    out["site_ji"] = np.array([sj, si])
    out["s_curr"] = spd[:, sj, si].astype("f4")

    w = xr.open_dataset(WW3)
    hs = w.hs.isel(time=slice(h0, h1)).values
    out["f_hs"] = q(np.nan_to_num(hs), LEVELS["hs"])
    out["s_hs"] = np.nan_to_num(hs[:, sj, si]).astype("f4")

    t = xr.open_dataset(TURB)
    c = t.C_surface.isel(time=slice(h0, h1)).values
    out["f_turb"] = q(np.nan_to_num(c, nan=3.0), LEVELS["turb"])
    out["s_turb"] = np.nan_to_num(c[:, sj, si], nan=3.0).astype("f4")

    np.savez_compressed(ANIM, **out)
    print(f"wrote {ANIM} ({os.path.getsize(ANIM) / 1e6:.1f} MB), {nt} frames")


def _extract_modis(xr, pd):
    """MODIS turbidity index for the morning after the storm, and the model
    snapshot to set beside it.

    The CI itself is Shanableh et al. (2025) Eq. 2, reused verbatim from
    calib_02/postprocess/compare_modis.py rather than reimplemented -- the two
    figures should not be able to drift apart. Cropped to the Gulf and taken
    every second pixel: the native tile is 2400 x 2400 at 500 m, which is far
    more than a slide can show and 23 MB of cache to carry it."""
    import sys
    from datetime import datetime

    # The model half needs no external drive, so it is computed first and
    # unconditionally: the calibration panel marks the satellite hour on its
    # time axis and must not depend on whether a USB disk is plugged in.
    v = {}
    turb_file = TURB.replace("Y2022M01", "Y2022M%02d" % MODIS_DATE[1])
    with xr.open_dataset(turb_file) as t:
        target = np.datetime64(datetime(*MODIS_DATE, MODIS_HOUR))
        k = int(np.argmin(np.abs(t.time.values - target)))
        v["modis_model"] = t.C_surface.isel(time=k).values.astype("f4")
        v["modis_time"] = (np.datetime64(t.time.values[k])
                           .astype("datetime64[s]").astype("int64"))

    if not os.path.isdir(MODIS_DIR):
        print(f"  (skipping the MODIS scene: {MODIS_DIR} not mounted — "
              "the model panel and the scene timestamp are still current)")
        return v
    sys.path.insert(0, MODIS_TOOLS)
    from compare_modis import (modis_lonlat_h22v06, load_land_mask,
                               find_myd09_file, compute_ci)

    lon, lat = modis_lonlat_h22v06()
    land = load_land_mask(MODIS_DIR)
    date = datetime(*MODIS_DATE)
    ci = compute_ci(find_myd09_file(MODIS_DIR, date), land)

    x0, x1, y0, y1 = MODIS_EXTENT
    inside = (lon >= x0) & (lon <= x1) & (lat >= y0) & (lat <= y1)
    jj, ii = np.where(inside)
    sl = (slice(jj.min(), jj.max() + 1, 2), slice(ii.min(), ii.max() + 1, 2))
    v["modis_lon"] = lon[sl].astype("f4")
    v["modis_lat"] = lat[sl].astype("f4")
    v["modis_ci"] = ci[sl].astype("f4")
    return v


def _extract_validation(out, xr, pd):
    """Point SST series and the co-located Hs pairs.

    The SST point is read one hyperslab per monthly file rather than by opening
    all 126 at once: only a single cell is wanted, and open_mfdataset would pull
    whole surface fields to get it."""
    import glob
    v = {}

    lon0, lat0 = OSTIA_LONLAT
    dist = np.where(out["mask"].astype(bool),
                    (out["lon"] - lon0) ** 2 + (out["lat"] - lat0) ** 2, np.inf)
    oj, oi = np.unravel_index(np.argmin(dist), dist.shape)

    times, vals = [], []
    for f in sorted(glob.glob(os.path.join(LONG_SURF, "croco_avg_surf_Y*.nc"))):
        with xr.open_dataset(f, decode_times=False) as ds:
            t = ds.time.values.astype("f8")
            times.append(t)
            vals.append(ds.temp.isel(eta_rho=oj, xi_rho=oi).values.astype("f4"))
    t = np.concatenate(times)
    y = np.concatenate(vals)
    # YORIG for this run is 1993, not the ops default of 2000: croco_avg_surf
    # carries "time since initialization" in seconds with no epoch, and 1993 is
    # the value that puts croco_avg_surf_Y2015M01 on 1 January 2015.
    stamp = pd.Timestamp("1993-01-01") + pd.to_timedelta(t, "s")
    ser = pd.Series(y, index=stamp).sort_index().resample("D").mean()
    v["sst_t"] = (ser.index - pd.Timestamp("1970-01-01")).total_seconds().values
    v["sst_model"] = ser.values.astype("f4")

    o = pd.read_csv(OSTIA_CSV, parse_dates=["time"]).set_index("time")
    o = o["temperature_deg_C"].resample("D").mean()
    v["sat_t"] = (o.index - pd.Timestamp("1970-01-01")).total_seconds().values
    v["sat_sst"] = o.values.astype("f4")

    v.update(_extract_modis(xr, pd))

    with xr.open_dataset(HS_COLOC) as hc:
        ho = hc.hs_obs.values.astype("f8")
        hm = hc.hs_model.values.astype("f8")
    # L3 altimetry carries a little noise through zero; a negative significant
    # wave height is not a measurement, and keeping it would drag the fit.
    ok = np.isfinite(ho) & np.isfinite(hm) & (ho >= 0.0)
    v["hs_obs"] = ho[ok].astype("f4")
    v["hs_mod"] = hm[ok].astype("f4")
    return v


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


def domain_extent(d, pad=0.15, aspect=None):
    """Extent around the model domain: 1103 x 921 km, aspect 1.20:1.

    Near square, so the map is boxed on the right of the slide with a text column
    beside it rather than run full-bleed. `aspect` pads longitude to a wider
    frame instead of cropping the basin -- used on slide 3, where the map takes
    a letterbox strip across the top and the boundary panels sit beneath it."""
    ext = [float(d["lon"].min()) - pad, float(d["lon"].max()) + pad,
           float(d["lat"].min()) - pad, float(d["lat"].max()) + pad]
    if aspect is not None:
        have = _mercator_aspect(ext)
        if aspect > have:
            grow = (ext[1] - ext[0]) * (aspect / have - 1.0) / 2.0
            ext[0] -= grow
            ext[1] += grow
    return ext


def new_map(ext, height=6.0, transparent=True, land_fill=None,
            land_edge=None, rect=(0, 0, 1, 1), fig=None):
    """A bare map: no frame, no graticule, no tick labels. Everything the deck
    needs to say about it is native PowerPoint text sitting on top."""
    import matplotlib.pyplot as plt
    import cartopy.crs as ccrs
    import cartopy.feature as cfeature

    asp = _mercator_aspect(ext)
    ground = "none" if transparent else PAPER
    if fig is None:
        fig = plt.figure(figsize=(height * asp, height), facecolor=ground)
    ax = fig.add_axes(list(rect), projection=ccrs.Mercator())
    ax.set_extent(ext, crs=ccrs.PlateCarree())
    # Transparent lets the slide's own ground show through everywhere the model
    # is not, so the map floats as a shape instead of sitting in a visible box.
    ax.set_facecolor(ground)
    ax.patch.set_alpha(0.0 if transparent else 1.0)
    ax.spines["geo"].set_visible(False)

    # GSHHS full resolution, already cached locally. Same source crocotools_py's
    # plot_land() uses; drawn directly here only to control the colours.
    land = cfeature.GSHHSFeature(scale="f")
    # land_fill="none" leaves the coast as an outline only, for fields that are
    # genuinely defined over land as well -- ERA5 wind being the one that is.
    fill = LAND_FILL if land_fill is None else land_fill
    ax.add_feature(land, facecolor=fill, edgecolor=LAND_EDGE if land_edge is None
                   else land_edge, linewidth=0.6, zorder=3)
    return fig, ax


def mplc_listed(color):
    """A one-colour colormap, for painting the domain footprint as a flat tone."""
    import matplotlib.colors as mplc
    return mplc.ListedColormap([color])


def trunc(cmap, lo=0.0, hi=1.0, n=256):
    """Chop the washed-out end off a colormap.

    cmo.amp and cmo.turbid both start at near-white, which on a PAPER ground is
    indistinguishable from the sea outside the model domain -- a calm northern
    Gulf then reads as "not modelled". Starting the ramp part-way in keeps the
    lowest class visibly a colour."""
    import matplotlib.colors as mplc
    return mplc.LinearSegmentedColormap.from_list(
        f"{cmap.name}_t", cmap(np.linspace(lo, hi, n)))


def shade(ax, d, field, levels, cmap, mask_land=True,
          lon=None, lat=None, edges=False):
    """pcolormesh on non-uniform levels. BoundaryNorm rather than a linear scale
    because most of these fields are strongly skewed -- see LEVELS."""
    import matplotlib.colors as mplc
    import cartopy.crs as ccrs
    v = np.asarray(field, dtype="f8")
    if mask_land:
        v = np.where(d["mask"].astype(bool), v, np.nan)
    lon = d["lon"] if lon is None else lon
    lat = d["lat"] if lat is None else lat
    kw = dict(edgecolors="#00000018", linewidth=0.15) if edges else {}
    return ax.pcolormesh(lon, lat, v, cmap=cmap,
                         norm=mplc.BoundaryNorm(np.array(levels), ncolors=256),
                         transform=ccrs.PlateCarree(), zorder=2, **kw)


def colorbar(fig, art, levels, label, rect=(0.045, 0.115, 0.300, 0.019),
             every=2, backing=False):
    """Horizontal bar tucked into the empty lower-left corner of the frame. The
    Gulf runs diagonally, so that corner is outside the domain on every one of
    these maps -- free space inside the picture rather than a sidebar beside it."""
    import matplotlib.pyplot as plt
    if backing:
        # A field defined over land as well (ERA5) fills the frame, leaving the
        # bar no clear ground of its own.
        pad = (0.022, 0.055)
        fig.patches.append(plt.Rectangle(
            (rect[0] - pad[0], rect[1] - pad[1] * 0.55),
            rect[2] + 2 * pad[0], rect[3] + pad[1] * 1.9,
            transform=fig.transFigure, facecolor=PAPER, alpha=0.88,
            edgecolor="none", zorder=5))
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
    cax.set_zorder(6)
    return cb


# Coloured vectors, following ops/postprocess/publish_web.py::_write_vector_png.
# Magnitude is carried by BOTH arrow colour and arrow length; there is no scalar
# field underneath. A length floor matters as much as the ceiling -- purely
# proportional arrows collapse most of the domain to invisible stubs and the
# direction field, which is the whole point, is lost.
VEC_LEN_MIN, VEC_LEN_MAX = 0.010, 0.040    # fraction of map width


def cvectors(ax, lon, lat, u, v, levels, cmap, skip=6, where=None,
             lmin=None, lmax=None):
    """Arrows coloured and scaled by magnitude, over a flat sea.

    Points are projected to the axes' own coordinates and the arrow components
    built there, rather than handing lon/lat vectors to cartopy with a
    transform: with `scale_units="xy"` cartopy reads the components as projected
    metres, so degree-sized vectors collapse to dots. Mercator is conformal and
    north-up, so east/north unit components carry straight over to +x/+y.

    Lengths are a fraction of the map width, so the same call works on the
    domain maps and on any inset without retuning.
    """
    import matplotlib.colors as mplc
    import cartopy.crs as ccrs

    lmin = VEC_LEN_MIN if lmin is None else lmin
    lmax = VEC_LEN_MAX if lmax is None else lmax

    u = np.asarray(u, "f8")
    v = np.asarray(v, "f8")
    if lon.ndim == 1:
        lon, lat = np.meshgrid(lon, lat)

    pts = ax.projection.transform_points(ccrs.PlateCarree(), lon, lat)
    X, Y = pts[..., 0], pts[..., 1]
    x0, x1 = ax.get_xlim()
    W = abs(x1 - x0)

    mag = np.hypot(u, v)
    with np.errstate(invalid="ignore", divide="ignore"):
        uh, vh = u / mag, v / mag
    vmax = float(levels[-1])
    L = (lmin + (lmax - lmin) * np.clip(mag / vmax, 0, 1)) * W

    uh, vh, mag = uh.copy(), vh.copy(), mag.copy()
    if where is not None:
        uh[~where] = np.nan
        vh[~where] = np.nan
        mag[~where] = np.nan

    sl = (slice(None, None, skip), slice(None, None, skip))
    return ax.quiver(X[sl], Y[sl], (uh * L)[sl], (vh * L)[sl], mag[sl],
                     cmap=cmap, norm=mplc.BoundaryNorm(np.array(levels), 256),
                     angles="xy", scale_units="xy", scale=1.0,
                     width=0.0032, headwidth=3.5, headlength=4.0,
                     headaxislength=3.4, pivot="mid", zorder=4)


def flat_sea(ax, d, color="#e9e3d2"):
    """The model footprint as one inert tone, so the basin still reads as a
    shape under a vector field that carries all the colour itself."""
    import cartopy.crs as ccrs
    v = np.where(d["mask"].astype(bool), 1.0, np.nan)
    return ax.pcolormesh(d["lon"], d["lat"], v, cmap=mplc_listed(color),
                         vmin=0, vmax=1, transform=ccrs.PlateCarree(), zorder=2)


def vectors(ax, d, u, v, lon=None, lat=None, skip=6, scale=14, color=INK_2,
            where=None, unit=True):
    """Sparse direction arrows.

    `unit` normalises every arrow to the same length, so the arrows carry
    direction and the colour carries magnitude. Scaled arrows fight the shading
    for the same job and lose: surface speed spans 0.001 to 1.9 m/s here, which
    draws a handful of enormous arrows over a field of invisible ones.

    `where` drops arrows below a threshold -- an arrow in near-calm water points
    somewhere nobody cares about, and a field of them reads as clutter."""
    import cartopy.crs as ccrs
    lon = d["lon"] if lon is None else lon
    lat = d["lat"] if lat is None else lat
    if lon.ndim == 1:
        lon, lat = np.meshgrid(lon, lat)
    u, v = np.asarray(u, "f8").copy(), np.asarray(v, "f8").copy()
    if unit:
        m = np.hypot(u, v)
        with np.errstate(invalid="ignore", divide="ignore"):
            u, v = u / m, v / m
    if where is not None:
        u[~where] = np.nan
        v[~where] = np.nan
    sl = (slice(None, None, skip), slice(None, None, skip))
    return ax.quiver(lon[sl], lat[sl], u[sl], v[sl],
                     scale=scale, width=0.0022, color=color, alpha=0.42,
                     transform=ccrs.PlateCarree(), zorder=4)


def save_anchors(name, anchors):
    """Write feature positions, in image fractions, beside the PNG.

    Labels live in PowerPoint so they stay editable, but they still have to land
    next to the thing they name. Rather than hand-tuning two sets of coordinates
    that silently drift apart, the figure reports where its features ended up and
    the deck reads that file. x runs left-to-right, y top-to-bottom, both 0-1 of
    the saved image."""
    import json
    out = os.path.join(ASSET_DIR, f"chain-{name}.anchors.json")
    with open(out, "w") as fh:
        json.dump(anchors, fh, indent=2, sort_keys=True)
    print(f"wrote {out} ({len(anchors)} anchors)")


def save(fig, name, dpi=200, transparent=True, tight=False):
    """`tight` crops to the drawn content.

    The axonometric blocks sit inside a lot of dead figure, because the
    silhouette is a rotated diamond in a rectangular frame. Cropping means the
    block itself gets the slide space rather than its own whitespace."""
    os.makedirs(ASSET_DIR, exist_ok=True)
    out = os.path.join(ASSET_DIR, f"chain-{name}.png")
    kw = dict(bbox_inches="tight", pad_inches=0.02) if tight else {}
    fig.savefig(out, dpi=dpi, transparent=transparent,
                facecolor="none" if transparent else PAPER, **kw)
    print(f"wrote {out} ({os.path.getsize(out) / 1e3:.0f} kB)")
    return out


# ------------------------------------------------------------------ slides
def slide_6(d):
    """Waves ride the currents we just solved.

    Coloured arrows rather than black arrows over a scalar field: hs sets both
    the colour and the length, dp sets the direction, and the sea underneath is
    one flat tone. The scalar map was doing the same job as the arrows, and the
    two competed for it.
    """
    import cmocean.cm as cmo
    fig, ax = new_map(domain_extent(d))
    flat_sea(ax, d)
    th = np.deg2rad(np.asarray(d["dp"], dtype="f8"))
    hs = np.asarray(d["hs"], "f8")
    # dp is the direction waves travel FROM, nautical convention
    u, v = -np.sin(th) * hs, -np.cos(th) * hs
    wet = d["mask"].astype(bool) & (hs > 0.05)
    art = cvectors(ax, d["lon"], d["lat"], u, v, LEVELS["hs"],
                   trunc(cmo.amp, 0.14), skip=7, where=wet)
    colorbar(fig, art, LEVELS["hs"], "significant wave height  (m)")
    return save(fig, "6-waves")


def SPEED_CMAP():
    """One ramp for every speed in the module -- wind on slide 2 and current on
    slide 5 -- so the audience reads "same kind of thing" without being told.
    cmo.dense rather than cmo.speed: speed's yellow-green fights the paper
    ground and sits too close to the yellow-brown of cmo.turbid on slide 7."""
    import cmocean.cm as cmo
    return trunc(cmo.dense, 0.06, 0.96)


def slide_2(d):
    """We start with weather anyone can audit.

    ERA5 on its native 0.25 deg grid as coloured arrows, one per cell, no
    interpolation: the coarseness then shows in the arrow spacing itself rather
    than in a blocky scalar field. Land is outline-only because wind is defined
    over it; every other slide fills land, because theirs are not.
    """
    fig, ax = new_map(domain_extent(d), land_fill="none")
    art = cvectors(ax, d["era5_lon"], d["era5_lat"], d["era5_u"], d["era5_v"],
                   LEVELS["wind"], SPEED_CMAP(), skip=1,
                   lmin=0.011, lmax=0.030)
    colorbar(fig, art, LEVELS["wind"], "wind speed at 10 m  (m/s)",
             backing=True)
    return save(fig, "2-atmosphere")


def slide_5(d):
    """Then we solve for the water.

    The same hour as the 3D block beside it, so the arrows on the two figures
    are the same arrows. Gulf currents are tidal -- p50 around 0.2 m/s against
    1.4 in the narrows -- so the levels are deliberately non-uniform. The ACCENT
    box is the block that is cut out; no caption needed, since the block sits
    directly below it on the slide.
    """
    import cartopy.crs as ccrs
    fig, ax = new_map(domain_extent(d))
    flat_sea(ax, d)
    wet = d["mask"].astype(bool)
    art = cvectors(ax, d["lon"], d["lat"], d["croco_u_aug"], d["croco_v_aug"],
                   LEVELS["curr"], SPEED_CMAP(), skip=6, where=wet)
    x0, x1, y0, y1 = BLOCK_EXT
    ax.plot([x0, x1, x1, x0, x0], [y0, y0, y1, y1, y0], color=ACCENT, lw=1.8,
            transform=ccrs.PlateCarree(), zorder=6)
    colorbar(fig, art, LEVELS["curr"], "surface current speed  (m/s)", every=2)
    return save(fig, "5-circulation")


# ------------------------------------------------------------------ 3D block
# Adapted from oceanmotion-web/studies/figures/plot_model_grid_3d.py: an
# axonometric cutaway of real model cells, no decimation and no smoothing. Every
# quad drawn is one cell of the 291x131x15 grid.
VEX = 950.0        # vertical exaggeration. The block spans ~230 km and only 82 m
                   # of depth; at anything less the 15 layers are not legible,
                   # and showing that there ARE layers is the whole point.
CRUST = 4.0        # m of seabed drawn below the deepest cell, so the base
                   # follows the bathymetry instead of being a flat slab
LAND_H = 2.5       # schematic land-slab height (m); carries no topography

# Columns past ~54 of the cached block are almost entirely land, which was
# taking a third of the frame. Trimmed here rather than re-extracting, so the
# cache stays a straight window of the model and the framing stays a plot
# decision.
BLOCK_TRIM = (slice(None), slice(0, 56))
SHADE_F = {"top": 1.00, "x": 0.86, "y": 0.72}


def _camera(azim, elev):
    th, ph = np.radians(azim), np.radians(elev)
    view = np.array([np.cos(ph) * np.cos(th), np.cos(ph) * np.sin(th), np.sin(ph)])
    right = np.array([-np.sin(th), np.cos(th), 0.0])
    up = np.array([-np.cos(th) * np.sin(ph), -np.sin(th) * np.sin(ph), np.cos(ph)])
    return view, right, up


def block3d(d, field="b_temp", cmap=None, levels=None, label="temperature",
            azim=135.0, elev=24.0, name="5-block", extra=None,
            figsize=(11.0, 5.0), trim=None, values=None, vex=None,
            north=True):
    """Axonometric cutaway of a block of the real model grid.

    Two cut walls expose the 15 terrain-following layers; the shelf climbs to a
    schematic land wedge at the coast. The point is not the field but the fact
    that there *are* layers -- everywhere else in the module "3D" is asserted
    over a plan view, which is what a 3D claim does not look like.

    Orientation is geographic, not index-order: X follows xi (which runs ESE
    here) and Y follows eta (NNE), both unreversed. An earlier version mirrored
    both axes, which put the coast on the wrong side and made the view read as
    flipped. Which pair of walls is cut away is then derived from the camera
    rather than fixed, so any azimuth gives a solid block seen from outside.
    """
    import matplotlib.pyplot as plt
    import matplotlib.colors as mplc
    from matplotlib.collections import PolyCollection
    from matplotlib.colors import to_rgb

    view, right, up = _camera(azim, elev)

    def project(p):
        p = np.asarray(p, float)
        return np.column_stack([p @ right, p @ up])

    def depth_of(p):
        return float(np.mean(np.asarray(p, float) @ view))

    def shade(c, f):
        return tuple(np.clip(np.array(to_rgb(c)) * f, 0, 1))

    tj, ti = BLOCK_TRIM if trim is None else trim
    VEXL = VEX if vex is None else vex
    h = np.asarray(d["b_h"], "f8")[tj, ti]
    mask = d["b_mask"].astype(bool)[tj, ti]
    lat = np.asarray(d["b_lat"], "f8")[tj, ti]
    # `values` arrives already trimmed by the caller (it is built from the same
    # window), so it must not be sliced again.
    val = (np.asarray(d[field], "f8")[:, tj, ti] if values is None
           else np.asarray(values, "f8"))
    ny, nx = h.shape
    N = val.shape[0]

    zw = _z_rho(np.asarray(d["b_h"], "f8").ravel(), d["b_Cs_w"], d["b_sc_w"],
                float(d["b_hc"]))
    zw = zw.reshape(N + 1, *np.asarray(d["b_h"]).shape)[:, tj, ti]

    dx = np.mean(1.0 / np.asarray(d["b_pm"])[tj, ti], axis=0) / 1000.0
    dy = np.mean(1.0 / np.asarray(d["b_pn"])[tj, ti], axis=1) / 1000.0
    Xe = np.concatenate([[0.0], np.cumsum(dx)])
    Ye = np.concatenate([[0.0], np.cumsum(dy)])

    def zk(z):
        return np.asarray(z) * VEXL / 1000.0

    if cmap is None:
        import cmocean.cm as cmo
        cmap = cmo.thermal
    if levels is None:
        lo, hi = np.nanpercentile(val[:, mask], [1, 99])
        levels = np.linspace(np.floor(lo), np.ceil(hi), 11)
    norm = mplc.BoundaryNorm(np.asarray(levels), 256)
    val = np.where(mask[None], val, np.nan)

    # Which pair of walls is cut away follows the camera: always the two that
    # face it, so the block reads as solid from any azimuth.
    sx = -1 if view[0] < 0 else 1
    sy = -1 if view[1] < 0 else 1
    xi_w = 0 if sx < 0 else nx - 1
    eta_w = 0 if sy < 0 else ny - 1
    Xw = Xe[0] if sx < 0 else Xe[-1]
    Yw = Ye[0] if sy < 0 else Ye[-1]

    faces = []
    NXv, NYv, NZv = np.array([1., 0, 0]), np.array([0, 1., 0]), np.array([0, 0, 1.])
    OC_EDGE, LD_EDGE = (0.09, 0.13, 0.20, 0.55), "#7d735f"
    LAND_C, SUB_C = "#d8c9a6", "#a89a7d"

    def add(pts3, fc, ec, lw, normal):
        if np.dot(normal, view) <= 0:
            return
        faces.append((depth_of(pts3), project(pts3), fc, ec, lw))

    lh = zk(LAND_H)
    for j in range(ny):
        for i in range(nx):
            x0, x1 = Xe[i], Xe[i + 1]
            y0, y1 = Ye[j], Ye[j + 1]
            if mask[j, i]:
                add([(x0, y0, 0), (x1, y0, 0), (x1, y1, 0), (x0, y1, 0)],
                    cmap(norm(val[-1, j, i])), OC_EDGE, 0.08, NZv)
                continue
            add([(x0, y0, lh), (x1, y0, lh), (x1, y1, lh), (x0, y1, lh)],
                shade(LAND_C, SHADE_F["top"]), LD_EDGE, 0.08, NZv)
            # coastal step: only the camera-facing walls, where water adjoins
            ii = i - 1 if sx < 0 else i + 1
            xf = x0 if sx < 0 else x1
            if 0 <= ii < nx and mask[j, ii]:
                add([(xf, y0, 0), (xf, y1, 0), (xf, y1, lh), (xf, y0, lh)],
                    shade(LAND_C, SHADE_F["x"]), LD_EDGE, 0.08, sx * NXv)
            jj = j - 1 if sy < 0 else j + 1
            yf = y0 if sy < 0 else y1
            if 0 <= jj < ny and mask[jj, i]:
                add([(x0, yf, 0), (x1, yf, 0), (x1, yf, lh), (x0, yf, lh)],
                    shade(LAND_C, SHADE_F["y"]), LD_EDGE, 0.08, sy * NYv)

    def wall_interfaces(cells):
        """Interface depths at the cell *edges*.

        z_levels gives depths at cell centres; drawing each cell from its own
        centres makes neighbours step against each other, which misrepresents a
        terrain-following grid -- the layers are continuous surfaces. Averaging
        onto the shared edge lets the faces slant and the seabed read as one
        line. Land neighbours are not averaged in, so the water ends vertically
        at the coast."""
        n = len(cells)
        zcol = np.stack([zw[:, j, i] for j, i in cells], axis=1)
        wet = np.array([mask[j, i] for j, i in cells])
        ze = np.zeros((N + 1, n + 1))
        for e in range(n + 1):
            src = [c for c in (e - 1, e) if 0 <= c < n and wet[c]]
            if src:
                ze[:, e] = zcol[:, src].mean(axis=1)
        return ze

    def wall(axis):
        if axis == "x":
            const, normal, edges = Xw, sx * NXv, Ye
            cells = [(m, xi_w) for m in range(ny)]
        else:
            const, normal, edges = Yw, sy * NYv, Xe
            cells = [(eta_w, m) for m in range(nx)]
        ze = wall_interfaces(cells)
        base = np.where(ze[0] < 0.0, ze[0] - CRUST, np.nan)
        idx = np.arange(len(base))
        good = ~np.isnan(base)
        if not good.any():
            return base
        base = np.interp(idx, idx[good], base[good])

        def quad(m, zlo, zhi):
            a, b = edges[m], edges[m + 1]
            pts = [(a, zlo[0]), (b, zlo[1]), (b, zhi[1]), (a, zhi[0])]
            if axis == "x":
                return [(const, t, zk(z)) for t, z in pts]
            return [(t, const, zk(z)) for t, z in pts]

        for m, (j, i) in enumerate(cells):
            if not mask[j, i]:
                add(quad(m, base[m:m + 2], (LAND_H, LAND_H)),
                    shade(SUB_C, SHADE_F[axis]), LD_EDGE, 0.08, normal)
                continue
            for k in range(N):
                add(quad(m, ze[k, m:m + 2], ze[k + 1, m:m + 2]),
                    cmap(norm(val[k, j, i])), OC_EDGE, 0.08, normal)
            add(quad(m, base[m:m + 2], ze[0, m:m + 2]),
                shade(SUB_C, SHADE_F[axis]), LD_EDGE, 0.08, normal)
        return base

    wall("x")
    wall("y")
    faces.sort(key=lambda f: f[0])

    fig = plt.figure(figsize=figsize, facecolor="none")
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_facecolor("none")
    ax.add_collection(PolyCollection(
        [f[1] for f in faces], facecolors=[f[2] for f in faces],
        edgecolors=[f[3] for f in faces], linewidths=[f[4] for f in faces]))
    ax.set_aspect("equal")
    ax.autoscale_view()
    (ax0, ax1), (ay0, ay1) = ax.get_xlim(), ax.get_ylim()
    mx, my = 0.10 * (ax1 - ax0), 0.13 * (ay1 - ay0)
    ax.set_xlim(ax0 - mx, ax1 + mx)
    ax.set_ylim(ay0 - my, ay1 + my)
    ax.axis("off")

    # North, derived from the grid rather than assumed: the block is a rotated
    # curvilinear window, so which way is up is not obvious and the figure has
    # to say so.
    dlat_x = np.nanmean(np.gradient(lat, axis=1)) / np.mean(dx)
    dlat_y = np.nanmean(np.gradient(lat, axis=0)) / np.mean(dy)
    nvec = np.array([dlat_x, dlat_y, 0.0])
    nvec /= (np.linalg.norm(nvec) or 1.0)

    ctx = dict(ax=ax, fig=fig, project=project, zk=zk, Xe=Xe, Ye=Ye, zw=zw,
               mask=mask, cmap=cmap, norm=norm, levels=levels, label=label,
               nx=nx, ny=ny, h=h, wall_interfaces=wall_interfaces,
               north=nvec, right=right, up=up, sx=sx, sy=sy,
               xi_w=xi_w, eta_w=eta_w, Xw=Xw, Yw=Yw, trim=(tj, ti))
    if north:
        north_arrow(ctx)
    if extra is not None:
        extra(ctx)
    else:
        _block_furniture(ctx)
    return save(fig, name, tight=True)


def surface_vectors(c, u, v, skip=6, scale=52.0, color="#101b2b"):
    """Surface currents lying in the sea-surface plane of a 3D block.

    The block is drawn in grid axes, so the xi/eta components map straight onto
    its X and Y before projection -- no compass rotation, and the arrows lie
    flat on the surface and foreshorten with it rather than floating above."""
    ax = c["ax"]
    tj, ti = c["trim"]
    u = np.asarray(u, "f8")[tj, ti]
    v = np.asarray(v, "f8")[tj, ti]
    Xe, Ye = c["Xe"], c["Ye"]
    xc = 0.5 * (Xe[:-1] + Xe[1:])
    yc = 0.5 * (Ye[:-1] + Ye[1:])
    right, up = c["right"], c["up"]

    jj, ii = np.mgrid[0:len(yc):skip, 0:len(xc):skip]
    jj, ii = jj.ravel(), ii.ravel()
    ok = c["mask"][jj, ii] & np.isfinite(u[jj, ii]) & np.isfinite(v[jj, ii])
    jj, ii = jj[ok], ii[ok]

    pts = c["project"]([(xc[i], yc[j], 0.0) for j, i in zip(jj, ii)])
    vec = np.stack([u[jj, ii] * scale, v[jj, ii] * scale,
                    np.zeros(len(jj))], axis=-1)
    return ax.quiver(pts[:, 0], pts[:, 1], vec @ right, vec @ up,
                     angles="xy", scale_units="xy", scale=1.0, color=color,
                     width=0.0022, headwidth=3.6, headlength=4.0,
                     headaxislength=3.4, alpha=0.75, zorder=12)


def north_arrow(c, frac=0.085):
    """A compass rose in the corner, projected the same way the block is, so it
    foreshortens with it and reads as lying on the sea surface."""
    ax = c["ax"]
    (x0, x1), (y0, y1) = ax.get_xlim(), ax.get_ylim()
    L = frac * (x1 - x0)
    n2 = np.array([c["north"] @ c["right"], c["north"] @ c["up"]])
    n2 = n2 / (np.linalg.norm(n2) or 1.0)
    base = np.array([x0 + 0.055 * (x1 - x0), y1 - 0.16 * (y1 - y0)])
    tip = base + n2 * L
    ax.annotate("", xy=tip, xytext=base, zorder=10,
                arrowprops=dict(arrowstyle="-|>", color=INK_2, lw=1.6,
                                mutation_scale=15, shrinkA=0, shrinkB=0))
    ax.text(tip[0] + n2[0] * 0.30 * L, tip[1] + n2[1] * 0.30 * L, "N",
            color=INK_2, fontsize=11, fontfamily=F_MONO, ha="center",
            va="center", zorder=10)


def _block_furniture(c):
    """Colourbar, scale bar and depth ruler.

    Everything is hung off the corner where the two cut walls meet -- the one
    corner guaranteed to face the camera whatever the azimuth. Fixed block
    corners were fine while the axes were reversed and the camera was fixed;
    they are not once either can change."""
    from matplotlib.cm import ScalarMappable
    ax, fig = c["ax"], c["fig"]
    Xw, Yw, Xe, Ye = c["Xw"], c["Yw"], c["Xe"], c["Ye"]

    def scr(x, y, z_m):
        return c["project"]([(x, y, c["zk"](z_m))])[0]

    (x0, x1), (y0, y1) = ax.get_xlim(), ax.get_ylim()
    W = x1 - x0

    # deepest point on the near corner's column, so the ruler spans real water
    zmin = float(np.nanmin(np.where(c["mask"], c["zw"][0], np.nan)))
    ticks = [t for t in (0, 20, 40, 60, 80, 120) if t <= -zmin + 12]

    # hung off the left edge of the frame, not off the corner: at some azimuths
    # the near corner is well inside the silhouette and the ruler ends up drawn
    # across the block face
    corner = scr(Xw, Yw, 0.0)
    rx = min(corner[0] - 0.055 * W, x0 + 0.030 * W)
    for dep in ticks:
        p = scr(Xw, Yw, -dep)
        ax.plot([rx, rx + 0.008 * W], [p[1], p[1]], color=INK_2, lw=0.9,
                zorder=10)
        ax.text(rx - 0.005 * W, p[1], f"{dep} m", color=INK_2, fontsize=8.5,
                fontfamily=F_MONO, ha="right", va="center", zorder=10)
    t0, t1 = scr(Xw, Yw, -ticks[0]), scr(Xw, Yw, -ticks[-1])
    ax.plot([rx, rx], [t0[1], t1[1]], color=INK_2, lw=0.9, zorder=10)

    # scale bar along the far end of the near wall, clear of the block
    bar = 50.0
    yo = Ye[-1] if Yw == Ye[0] else Ye[0]
    step = bar if yo > Yw else -bar
    zb = zmin - 18.0
    b0, b1 = scr(Xw, Yw, zb), scr(Xw, Yw + step, zb)
    ax.plot(*zip(b0, b1), color=INK_2, lw=1.3, solid_capstyle="butt", zorder=10)
    for e in (b0, b1):
        ax.plot([e[0], e[0]], [e[1] - 0.006 * W, e[1] + 0.006 * W],
                color=INK_2, lw=1.3, zorder=10)
    mid = (np.asarray(b0) + np.asarray(b1)) / 2
    ax.text(mid[0], mid[1] - 0.012 * W, f"{bar:.0f} km", color=INK_2,
            fontsize=9, fontfamily=F_MONO, ha="center", va="top", zorder=10)

    cax = fig.add_axes([0.560, 0.055, 0.230, 0.022])
    cb = fig.colorbar(ScalarMappable(norm=c["norm"], cmap=c["cmap"]), cax=cax,
                      orientation="horizontal", ticks=c["levels"][::3])
    cb.outline.set_visible(False)
    cb.set_label(c["label"], fontsize=9, color=INK_2, fontfamily=F_BODY)
    cb.ax.xaxis.set_label_position("top")
    cb.ax.tick_params(labelsize=8, colors=INK_2, length=2.5, width=0.7)
    for t in cb.ax.get_xticklabels():
        t.set_fontfamily(F_MONO)


def slide_5_block(d):
    """The 3D cutaway that backs slide 5's claim to be a 3D model.

    Coloured by temperature in mid-August, not in the January storm the rest of
    the module follows. That is deliberate and indicative: the Gulf is close to
    mixed in winter, so a January block is a slab of one colour and demonstrates
    nothing about being three-dimensional. In August the same water carries up
    to 11 degrees between surface and bed, which is what a 3D model is for.

    Viewed from the north-west, so the shelf climbs away from the camera to the
    Abu Dhabi coast."""
    import cmocean.cm as cmo

    def extra(c):
        surface_vectors(c, d["b_u_aug"], d["b_v_aug"])
        _block_furniture(c)

    return block3d(d, field="b_temp_aug", cmap=cmo.thermal,
                   levels=np.arange(22, 36.5, 1.0),
                   label="temperature  (°C)",
                   azim=135.0, elev=24.0, name="5-block", figsize=(11.0, 5.0),
                   north=False, extra=extra)


def _stats(mod, obs):
    """Bias, RMSE and correlation -- the three a modeller looks for first."""
    mod, obs = np.asarray(mod, "f8"), np.asarray(obs, "f8")
    ok = np.isfinite(mod) & np.isfinite(obs)
    m, o = mod[ok], obs[ok]
    return dict(n=int(ok.sum()), bias=float((m - o).mean()),
                rmse=float(np.sqrt(((m - o) ** 2).mean())),
                r=float(np.corrcoef(m, o)[0, 1]))


def _stat_block(ax, st, unit, loc=(0.985, 0.045), ha="right", va="bottom"):
    txt = (f"n {st['n']:,}".replace(",", " ") + "\n"
           f"bias  {st['bias']:+.2f} {unit}\n"
           f"RMSE  {st['rmse']:.2f} {unit}\n"
           f"r     {st['r']:.3f}")
    ax.text(loc[0], loc[1], txt, transform=ax.transAxes, fontsize=8.5,
            color=INK_2, fontfamily=F_MONO, ha=ha, va=va, linespacing=1.55)


def slide_5a_sst(d):
    """Model against satellite SST, ten years of it.

    Not the storm and not the site: this is the whole domain's seasonal cycle
    tested against an independent product over a decade. It is the cheapest
    honest answer to "how do you know the model is right?", and it belongs next
    to the circulation slide because SST is what the circulation is carrying."""
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    import pandas as pd

    mt = pd.to_datetime(np.asarray(d["sst_t"], "f8"), unit="s")
    st = pd.to_datetime(np.asarray(d["sat_t"], "f8"), unit="s")
    mod = pd.Series(np.asarray(d["sst_model"], "f8"), index=mt).dropna()
    sat = pd.Series(np.asarray(d["sat_sst"], "f8"), index=st).dropna()
    both = pd.concat([mod.rename("m"), sat.rename("s")], axis=1).dropna()

    fig = plt.figure(figsize=(11.0, 2.5), facecolor="none")
    # narrowed to leave a clear right margin for the statistics, which have no
    # quiet corner inside a decade of seasonal cycles
    ax = fig.add_axes([0.052, 0.190, 0.800, 0.750])
    ax.set_facecolor(PAPER)
    # satellite as a broad pale line under a thin model line: where the two
    # agree the model hides it, and every disagreement shows as grey.
    ax.plot(sat.index, sat.values, color=INK_3, lw=2.4, alpha=0.55,
            label="satellite  (OSTIA L4)")
    ax.plot(mod.index, mod.values, color="#1f7f92", lw=0.9,
            label="model  (CROCO)")
    ax.set_ylabel("sea surface temperature  (°C)", fontsize=8.5, color=INK_2,
                  fontfamily=F_BODY)
    ax.set_xlim(both.index[0], both.index[-1])
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    for sp in ("left", "bottom"):
        ax.spines[sp].set_color(RULE); ax.spines[sp].set_linewidth(0.8)
    ax.tick_params(labelsize=8, colors=INK_3, length=2.5, width=0.7)
    for lb in list(ax.get_xticklabels()) + list(ax.get_yticklabels()):
        lb.set_fontfamily(F_MONO); lb.set_color(INK_2)
    # above the axes rather than inside: a decade of seasonal cycles fills the
    # frame edge to edge and any in-axes legend lands on the data
    leg = ax.legend(loc="lower left", bbox_to_anchor=(0.0, 1.005), frameon=False,
                    fontsize=8, ncol=2, handlelength=1.6, columnspacing=1.4)
    for t in leg.get_texts():
        t.set_color(INK_2); t.set_fontfamily(F_MONO)
    _stat_block(ax, _stats(both.m, both.s), "°C", loc=(1.022, 0.90),
                ha="left", va="top")
    return save(fig, "5a-sst")


def slide_6a_hs(d):
    """Model against satellite significant wave height.

    26 000 altimeter passes co-located with WW3 output to 0.1 degrees and half
    an hour. Hexbin rather than a scatter because at this count a scatter is a
    solid blob and the density -- which is where the fit lives -- is invisible.
    The bias is negative and stays on the figure: the model runs a little under
    the altimeter, and saying so is worth more than hiding it."""
    import matplotlib.pyplot as plt
    import matplotlib.colors as mplc
    import cmocean.cm as cmo

    o = np.asarray(d["hs_obs"], "f8")
    m = np.asarray(d["hs_mod"], "f8")
    st = _stats(m, o)

    fig = plt.figure(figsize=(3.5, 3.5), facecolor="none")
    ax = fig.add_axes([0.155, 0.145, 0.665, 0.800])
    ax.set_facecolor(PAPER)
    hb = ax.hexbin(o, m, gridsize=44, cmap=trunc(cmo.dense, 0.06, 0.96),
                   norm=mplc.LogNorm(vmin=1, vmax=1200), mincnt=1,
                   linewidths=0)
    hi = 3.6
    ax.plot([0, hi], [0, hi], color=INK_2, lw=1.0, ls=(0, (4, 3)), zorder=4)
    ax.set_xlim(0, hi); ax.set_ylim(0, hi)
    ax.set_aspect("equal")
    ax.set_xlabel("satellite Hs  (m)", fontsize=8.5, color=INK_2,
                  fontfamily=F_BODY)
    ax.set_ylabel("model Hs  (m)", fontsize=8.5, color=INK_2,
                  fontfamily=F_BODY)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    for sp in ("left", "bottom"):
        ax.spines[sp].set_color(RULE); ax.spines[sp].set_linewidth(0.8)
    ax.tick_params(labelsize=8, colors=INK_3, length=2.5, width=0.7)
    for lb in list(ax.get_xticklabels()) + list(ax.get_yticklabels()):
        lb.set_fontfamily(F_MONO); lb.set_color(INK_2)
    _stat_block(ax, st, "m", loc=(0.045, 0.955), ha="left", va="top")

    cax = fig.add_axes([0.848, 0.145, 0.024, 0.340])
    cb = fig.colorbar(hb, cax=cax)
    cb.outline.set_visible(False)
    cax.set_title("pairs", fontsize=8, color=INK_2, fontfamily=F_MONO, pad=5)
    cb.ax.tick_params(labelsize=7.5, colors=INK_2, length=2, width=0.6)
    for t in cb.ax.get_yticklabels():
        t.set_fontfamily(F_MONO)
    return save(fig, "6a-hs")


def slide_7(d):
    """All of it lands on one number.

    Surface turbidity three hours after the bed let go, with the observation
    point that calibrated it marked in ACCENT. The scale starts at the 3 NTU
    background: below it there is nothing to show, and starting at zero would
    spend half the ramp on water that is simply clear."""
    import cmocean.cm as cmo
    import cartopy.crs as ccrs
    fig, ax = new_map(domain_extent(d))
    art = shade(ax, d, d["turb"], LEVELS["turb"], trunc(cmo.turbid, 0.10))
    lo, la = d["site_lonlat"]
    ax.plot([lo], [la], marker="o", ms=7, mfc="none", mec=ACCENT, mew=2.0,
            transform=ccrs.PlateCarree(), zorder=7)
    ax.annotate("calibration site\n6 m depth", xy=(float(lo), float(la)),
                xytext=(-14, -34), textcoords="offset points",
                xycoords=ccrs.PlateCarree()._as_mpl_transform(ax),
                color=ACCENT, fontsize=8.5, fontfamily=F_MONO, ha="right",
                va="top", zorder=7, linespacing=1.5,
                arrowprops=dict(arrowstyle="-", color=ACCENT, lw=1.0,
                                shrinkA=2, shrinkB=5))
    colorbar(fig, art, LEVELS["turb"], "surface turbidity  (NTU)", every=2)
    return save(fig, "7-turbidity")


def slide_7c_modis(d):
    """Qualitative model-vs-satellite check on the plume itself.

    Left, the MODIS Aqua turbidity index -- Shanableh et al. (2025) Eq. 2, a
    green-versus-blue/red reflectance contrast; right, modelled surface NTU at
    the same hour. The two are different quantities on different scales, so this
    is a shape comparison and nothing more: does the model put the plume where
    the satellite sees one. It does, along the whole southern shelf and around
    the Bahrain-Qatar shallows.

    Morning after the storm, not the storm day: Aqua passes around 10:00 and the
    21 January plume does not reach the surface until roughly 21:30."""
    import cmocean.cm as cmo
    import cartopy.crs as ccrs
    import matplotlib.colors as mplc
    import matplotlib.pyplot as plt
    import pandas as pd

    ext = MODIS_PLOT_EXTENT
    fig = plt.figure(figsize=(11.0, 4.0), facecolor="none")

    # Stepped so the open-Gulf background (CI about 90-150) lands in the first
    # band or two, matching how the model panel treats its 3 NTU background.
    # Without that the two panels sit at visibly different overall levels and
    # the eye compares brightness instead of shape.
    ci_lev = np.array([80, 130, 180, 240, 310, 390, 480, 580, 700])
    panels = [
        ("satellite  ·  MODIS Aqua turbidity index",
         d["modis_lon"], d["modis_lat"], d["modis_ci"], ci_lev,
         trunc(cmo.turbid, 0.10), "CI  (unitless)"),
        ("model  ·  surface turbidity",
         d["lon"], d["lat"], np.where(d["mask"].astype(bool),
                                      d["modis_model"], np.nan),
         np.array(LEVELS["turb"]), trunc(cmo.turbid, 0.10),
         "NTU"),
    ]
    for k, (title, lo, la, v, lev, cm, unit) in enumerate(panels):
        ax = fig.add_axes([0.030 + k * 0.492, 0.115, 0.455, 0.800],
                          projection=ccrs.Mercator())
        ax.set_extent(ext, crs=ccrs.PlateCarree())
        ax.set_facecolor(PAPER)
        ax.patch.set_alpha(0.0)
        ax.spines["geo"].set_visible(False)
        art = ax.pcolormesh(lo, la, np.asarray(v, "f8"), cmap=cm,
                            norm=mplc.BoundaryNorm(lev, 256),
                            transform=ccrs.PlateCarree(), zorder=2)
        import cartopy.feature as cfeature
        ax.add_feature(cfeature.GSHHSFeature(scale="i"), facecolor=LAND_FILL,
                       edgecolor=LAND_EDGE, linewidth=0.5, zorder=3)
        # Marked on both panels, and the text sits inland rather than over the
        # plume, where it was disappearing into the dark end of the ramp.
        lo0, la0 = (float(v) for v in d["site_lonlat"])
        ax.plot([lo0], [la0], marker="o", ms=7, mfc="none", mec=ACCENT,
                mew=2.0, transform=ccrs.PlateCarree(), zorder=8)
        ax.annotate("calibration site", xy=(lo0, la0),
                    xytext=(lo0 + 0.30, la0 - 0.62),
                    xycoords=ccrs.PlateCarree()._as_mpl_transform(ax),
                    textcoords=ccrs.PlateCarree()._as_mpl_transform(ax),
                    color=ACCENT, fontsize=8.5, fontfamily=F_MONO, ha="left",
                    va="center", zorder=8,
                    arrowprops=dict(arrowstyle="-", color=ACCENT, lw=0.9,
                                    shrinkA=2, shrinkB=4))
        ax.set_title(title, fontsize=9.5, color=INK, fontfamily=F_BODY,
                     loc="left", pad=5)
        cax = fig.add_axes([0.060 + k * 0.492, 0.075, 0.200, 0.021])
        cb = fig.colorbar(art, cax=cax, orientation="horizontal",
                          ticks=lev[::3])
        cb.outline.set_visible(False)
        cb.set_label(unit, fontsize=8, color=INK_2, fontfamily=F_MONO)
        cb.ax.xaxis.set_label_position("top")
        cb.ax.tick_params(labelsize=7.5, colors=INK_2, length=2, width=0.6)
        for t in cb.ax.get_xticklabels():
            t.set_fontfamily(F_MONO)

    stamp = pd.to_datetime(int(d["modis_time"]), unit="s")
    fig.text(0.985, 0.955, stamp.strftime("%-d %b %Y  ·  %H:%M UTC"),
             fontsize=9, color=INK_2, fontfamily=F_MONO, ha="right", va="top")
    # cropped to content: the panels are near-square, so a fixed 2.75:1 figure
    # letterboxes them and the maps end up smaller than the space allows
    return save(fig, "7c-modis", tight=True)


def slide_7a_calib(d):
    """The calibration itself: five ensemble members against the observations.

    The two free parameters are erosion rate and settling velocity, and they
    trade off against each other, so the honest presentation is a spread rather
    than a single tuned line: L to H spans the plausible range and the
    observations should sit inside it. They do.

    Two months, because the in-situ record covers January and the clean
    satellite scene is in February. The gap after 31 January is real and left
    visible: there is model spread there and nothing to hold it to except the
    satellite, which is exactly what the panels above are for.

    Observations are shown without a source or coordinates -- the point is that
    there were some and the model was held to them."""
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    import pandas as pd

    ens = np.asarray(d["cal_ens"], "f8")
    t = pd.to_datetime(np.asarray(d["cal_t"], "f8"), unit="s")
    ot = pd.to_datetime(np.asarray(d["cal_obs_t"], "f8"), unit="s")
    stamp = pd.to_datetime(int(d["modis_time"]), unit="s")

    fig = plt.figure(figsize=(11.0, 2.05), facecolor="none")
    ax = fig.add_axes([0.055, 0.235, 0.930, 0.640])
    ax.set_facecolor(PAPER)
    ax.fill_between(t, ens.min(axis=0), ens.max(axis=0), color=CYAN,
                    alpha=0.22, lw=0, label="ensemble range  (L–H)")
    ax.fill_between(t, np.percentile(ens, 25, axis=0),
                    np.percentile(ens, 75, axis=0), color=CYAN, alpha=0.40,
                    lw=0, label="ML–MH")
    ax.plot(t, ens[2], color="#1f7f92", lw=1.4, label="median  (M)")
    ax.plot(ot, d["cal_obs"], ls="none", marker="o", ms=3.4, mfc="none",
            mec=INK, mew=0.9, label="observed")

    ax.set_xlim(t[0], t[-1])
    ax.set_ylim(0, 48)
    ax.set_ylabel("surface turbidity  (NTU)", fontsize=8.5, color=INK_2,
                  fontfamily=F_BODY)
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=7))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%-d %b"))
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    for sp in ("left", "bottom"):
        ax.spines[sp].set_color(RULE); ax.spines[sp].set_linewidth(0.8)
    ax.tick_params(labelsize=8, colors=INK_3, length=2.5, width=0.7)
    for lb in list(ax.get_xticklabels()) + list(ax.get_yticklabels()):
        lb.set_fontfamily(F_MONO); lb.set_color(INK_2)
    leg = ax.legend(loc="lower left", bbox_to_anchor=(0.0, 1.005), frameon=False,
                    fontsize=8, ncol=4, handlelength=1.6, columnspacing=1.4)
    for txt in leg.get_texts():
        txt.set_color(INK_2); txt.set_fontfamily(F_MONO)
    # one line, marking the hour the satellite scene above was taken
    ax.axvline(stamp, color=ACCENT, lw=1.6, zorder=6)
    ax.text(stamp, 47.0, "  satellite scene above", color=ACCENT, fontsize=8.5,
            fontfamily=F_MONO, ha="left", va="top")
    return save(fig, "7a-calibration")


# Panel geometry for slide 4, shared with the deck through the anchors file.
GRID_PANELS = [0.020, 0.350, 0.680]
GRID_PANEL_W = 0.300


def slide_4(d):
    """The mesh is shaped to the basin -- and can be refined without limit.

    Three panels, each a zoom into the region outlined on the one before: the
    whole domain at 3.5 km, the southern shelf, and the AGRIF nest at 1.2 km.

    The nest is outlined by its actual grid edge, not by a bounding box, in both
    the panel it sits inside and the panel that shows it -- a rotated
    curvilinear grid is not a rectangle, and drawing it as one misstates what a
    nest is. Titles and resolution notes are slide text, so they stay editable;
    this function only reports where the panels landed.
    """
    import cmocean.cm as cmo
    import cartopy.crs as ccrs
    import cartopy.feature as cfeature
    import matplotlib.pyplot as plt

    nlon, nlat = d["n_lon"], d["n_lat"]
    pad = 0.06
    NEST_EXT = [float(nlon.min()) - pad, float(nlon.max()) + pad,
                float(nlat.min()) - pad, float(nlat.max()) + pad]

    def nest_edge(ax, lw=1.8):
        for lo, la in ((nlon[0], nlat[0]), (nlon[-1], nlat[-1]),
                       (nlon[:, 0], nlat[:, 0]), (nlon[:, -1], nlat[:, -1])):
            ax.plot(lo, la, color=NEST_RED, lw=lw,
                    transform=ccrs.PlateCarree(), zorder=8)

    fig = plt.figure(figsize=(12.0, 3.55), facecolor="none")
    panels = [
        dict(ext=domain_extent(d), frame=None, step=4, box=BLOCK_EXT),
        dict(ext=BLOCK_EXT, frame=ACCENT, step=1, nest_outline=True),
        dict(ext=NEST_EXT, frame=None, step=1, nest=True, nest_outline=True),
    ]

    for k, p in enumerate(panels):
        ax = fig.add_axes([GRID_PANELS[k], 0.020, GRID_PANEL_W, 0.960],
                          projection=ccrs.Mercator())
        ax.set_extent(p["ext"], crs=ccrs.PlateCarree())
        ax.set_facecolor(PAPER)
        if p["frame"] is None:
            ax.spines["geo"].set_color(RULE)
            ax.spines["geo"].set_linewidth(0.8)
        else:
            ax.spines["geo"].set_edgecolor(p["frame"])
            ax.spines["geo"].set_linewidth(2.0)

        art = shade(ax, d, d["h"], LEVELS["depth"], cmo.deep)
        glon, glat = d["lon"], d["lat"]
        if p.get("nest"):
            v = np.where(d["n_mask"].astype(bool), d["n_h"], np.nan)
            shade(ax, d, v, LEVELS["depth"], cmo.deep, mask_land=False,
                  lon=nlon, lat=nlat)
            glon, glat = nlon, nlat

        st = p["step"]
        for j in range(0, glon.shape[0], st):
            ax.plot(glon[j], glat[j], color="#33404e", lw=0.22, alpha=0.55,
                    transform=ccrs.PlateCarree(), zorder=5)
        for i in range(0, glon.shape[1], st):
            ax.plot(glon[:, i], glat[:, i], color="#33404e", lw=0.22,
                    alpha=0.55, transform=ccrs.PlateCarree(), zorder=5)
        if p.get("nest_outline"):
            nest_edge(ax)
        ax.add_feature(cfeature.GSHHSFeature(scale="f"), facecolor="#e4dbc3",
                       edgecolor=INK_2, linewidth=0.6, zorder=6)

        if p.get("box"):
            x0, x1, y0, y1 = p["box"]
            ax.plot([x0, x1, x1, x0, x0], [y0, y0, y1, y1, y0], color=ACCENT,
                    lw=2.0, transform=ccrs.PlateCarree(), zorder=8)

    cax = fig.add_axes([0.033, 0.075, 0.135, 0.030])
    cb = fig.colorbar(art, cax=cax, orientation="horizontal",
                      ticks=np.array(LEVELS["depth"])[::3], spacing="uniform")
    cb.outline.set_visible(False)
    cb.set_label("depth  (m)", fontsize=8.5, color=INK_2, fontfamily=F_BODY)
    cb.ax.xaxis.set_label_position("top")
    cb.ax.tick_params(labelsize=7.5, colors=INK_2, length=2, width=0.6)
    for t in cb.ax.get_xticklabels():
        t.set_fontfamily(F_MONO)

    save_anchors("4-grid", {f"panel{k}": [GRID_PANELS[k] + GRID_PANEL_W / 2,
                                          0.0]
                            for k in range(3)})
    return save(fig, "4-grid")


def _panel(fig, rect, title):
    """A small framed panel for the boundary slide."""
    import matplotlib.pyplot as plt
    ax = fig.add_axes(list(rect))
    ax.set_facecolor(PAPER)
    for k, sp in ax.spines.items():
        sp.set_color(RULE)
        sp.set_linewidth(0.8)
    ax.tick_params(labelsize=7, colors=INK_3, length=2, width=0.6)
    for t in list(ax.get_xticklabels()) + list(ax.get_yticklabels()):
        t.set_fontfamily(F_MONO)
        t.set_color(INK_2)
    ax.set_title(title, fontsize=7.5, color=INK_2, fontfamily=F_MONO,
                 loc="left", pad=4)
    return ax


def slide_3a_door(d):
    """The Gulf has one door -- the map alone.

    Split out as its own image, along with the three input panels, so they can
    be moved independently on the slide instead of being locked into one
    composed figure. The domain is drawn inert -- one flat tone, no colormap --
    because the subject here is the edge, not the interior."""
    import cartopy.crs as ccrs
    fig, ax = new_map(domain_extent(d))
    flat_sea(ax, d, "#e7e1d0")
    east = np.where(d["mask"][:, -1] == 1)[0]
    blon, blat = d["lon"][east, -1], d["lat"][east, -1]
    ax.plot(blon, blat, color=ACCENT, lw=3.6, solid_capstyle="round",
            transform=ccrs.PlateCarree(), zorder=6)
    ax.annotate("one open boundary",
                xy=(float(blon.mean()), float(blat.mean())),
                xytext=(-46, -26), textcoords="offset points",
                xycoords=ccrs.PlateCarree()._as_mpl_transform(ax),
                color=ACCENT, fontsize=10, fontfamily=F_MONO, ha="right",
                va="center", zorder=7,
                arrowprops=dict(arrowstyle="-", color=ACCENT, lw=1.0,
                                shrinkA=2, shrinkB=4))
    return save(fig, "3a-door")


def slide_3b_ocean(d):
    """What the ocean brings, from raw GLORYS on its own 50 z-levels.

    Not from croco_bry_*.nc: that file has already been interpolated onto the
    model's 15 terrain-following layers, which is reasonable inside the Gulf but
    badly stretched across the 1500 m of the Gulf of Oman -- which is exactly
    where this section runs. The raw product shows the thermocline the boundary
    is actually being given."""
    import cmocean.cm as cmo
    import matplotlib.pyplot as plt

    fig = plt.figure(figsize=(5.4, 3.1), facecolor="none")
    ax = fig.add_axes([0.135, 0.185, 0.735, 0.700])
    ax.set_facecolor(PAPER)
    lat = np.asarray(d["g_lat"], "f8")
    dep = np.asarray(d["g_depth"], "f8")
    t = np.asarray(d["g_temp"], "f8")
    lev = np.arange(6, 26, 1.0)
    import matplotlib.colors as mplc
    pc = ax.pcolormesh(lat, dep, t, cmap=cmo.thermal,
                       norm=mplc.BoundaryNorm(lev, 256), shading="nearest")
    ax.set_ylim(500, 0)
    ax.set_xlabel("latitude along the boundary  (°N)", fontsize=8,
                  color=INK_2, fontfamily=F_MONO)
    ax.set_ylabel("depth  (m)", fontsize=8, color=INK_2, fontfamily=F_MONO)
    for sp in ax.spines.values():
        sp.set_color(RULE); sp.set_linewidth(0.8)
    ax.tick_params(labelsize=7.5, colors=INK_3, length=2.5, width=0.7)
    for lb in list(ax.get_xticklabels()) + list(ax.get_yticklabels()):
        lb.set_fontfamily(F_MONO); lb.set_color(INK_2)
    cb = fig.colorbar(pc, ax=ax, pad=0.03, fraction=0.055, ticks=lev[::4])
    cb.outline.set_visible(False)
    cb.set_label("°C", fontsize=8, color=INK_2, fontfamily=F_MONO)
    cb.ax.tick_params(labelsize=7.5, colors=INK_2, length=2, width=0.6)
    for lb in cb.ax.get_yticklabels():
        lb.set_fontfamily(F_MONO)
    return save(fig, "3b-ocean")


def slide_3c_tide(d):
    """What the tide brings.

    The model's own boundary elevation rather than a reconstruction from the
    TPXO10 constituents: the forcing file carries amplitude and phase with no
    phase reference, so an absolute trace would be guesswork. Same tide,
    correctly phased, and a real output."""
    import matplotlib.pyplot as plt
    fig = plt.figure(figsize=(5.4, 2.0), facecolor="none")
    ax = fig.add_axes([0.115, 0.235, 0.860, 0.680])
    ax.set_facecolor(PAPER)
    y = np.asarray(d["tide"], "f8")
    ax.plot(np.arange(len(y)) / 24.0, y, color=CYAN, lw=1.5)
    ax.axhline(0, color=RULE, lw=0.7, zorder=0)
    ax.set_xlim(0, len(y) / 24.0)
    ax.set_xlabel("days", fontsize=8, color=INK_2, fontfamily=F_MONO)
    ax.set_ylabel("m", fontsize=8, color=INK_2, fontfamily=F_MONO)
    for sp in ax.spines.values():
        sp.set_color(RULE); sp.set_linewidth(0.8)
    ax.tick_params(labelsize=7.5, colors=INK_3, length=2.5, width=0.7)
    for lb in list(ax.get_xticklabels()) + list(ax.get_yticklabels()):
        lb.set_fontfamily(F_MONO); lb.set_color(INK_2)
    return save(fig, "3c-tide")


def slide_3d_waves(d):
    """What the waves bring: one of the 25 CMEMS boundary spectra.

    32 frequencies x 24 directions. Unmistakably real -- nobody fakes a
    directional spectrum -- which is why it is worth the space."""
    import cmocean.cm as cmo
    import matplotlib.pyplot as plt
    fig = plt.figure(figsize=(3.0, 3.0), facecolor="none")
    ax = fig.add_axes([0.11, 0.09, 0.78, 0.78], projection="polar")
    ax.set_facecolor(PAPER)
    th = np.deg2rad(np.asarray(d["spec_d"], "f8"))
    order = np.argsort(th)
    ax.pcolormesh(th[order], np.asarray(d["spec_f"], "f8"),
                  np.asarray(d["spec"])[:, order], cmap=cmo.dense,
                  shading="nearest")
    ax.set_theta_zero_location("N")
    ax.set_theta_direction(-1)
    ax.set_ylim(0, 0.35)
    ax.set_yticklabels([])
    ax.set_xticks(np.deg2rad([0, 90, 180, 270]))
    ax.set_xticklabels(["N", "E", "S", "W"], fontsize=8, color=INK_2,
                       fontfamily=F_MONO)
    ax.grid(color=RULE, lw=0.5)
    ax.spines["polar"].set_color(RULE)
    return save(fig, "3d-waves")


# The turbidity schematic block: a 28 x 28 window around the calibration site,
# 3 to 22 m deep. Indices are into the cached b_* block, not the full grid.
TURB_TRIM = (slice(20, 52), slice(28, 56))


def _process_schematic(sediment, name):
    """The turbidity mechanism, as a schematic. Nothing here is model output.

    Drawn twice: once plain, to show what acts on the bed, and once with the
    water coloured, to show what that produces. One builder, so the geometry is
    identical and advancing the slide changes only the water.

    Everything is anchored to the near section (y = 0) and to the sea surface
    itself. The topmost orbit is tangent to the surface at a crest, and the
    current profile's surface vector starts on the surface -- floated even
    slightly off, both read as diagrams laid over a picture rather than as
    things happening in the water.

    No text: the labels are slide text, placed from the anchors file this
    writes, so they stay editable.
    """
    import matplotlib.pyplot as plt
    from matplotlib.collections import PolyCollection
    from matplotlib.colors import to_rgb

    # A deeper column relative to the box. At D = 26 against LX = 175 the wall
    # was about 15% of the block's length on screen, so however strong the
    # sediment ramp was made it stayed a thin band. The mechanism needs a water
    # column you can see into.
    LX, LY, D = 148.0, 58.0, 42.0
    AMP, WAVELEN = 2.8, 33.0
    AZ, EL = -54.0, 15.0
    view, right, up = _camera(AZ, EL)

    def proj(pts):
        p = np.asarray(pts, float)
        return np.column_stack([p @ right, p @ up])

    def dep(pts):
        return float(np.mean(np.asarray(pts, float) @ view))

    def P(x, y, z):
        return proj([(x, y, z)])[0]

    def sea_z(x):
        return AMP * np.sin(2 * np.pi * np.asarray(x) / WAVELEN)

    WATER_TOP, WATER_BED = "#eef6f8", "#5c4310"
    PLAIN = "#dbe8ec"
    BED_C, SUB_C = "#cbb888", "#a8977a"
    WAVE_C, CURR_C = CYAN, NAVY
    # Bed stress gets its own colour, shared by both sources: the point of the
    # figure is that two different things produce the same kind of forcing on
    # the bed, and colouring each arrow after its source says the opposite.
    STRESS_C = ACCENT

    def mix(a, b, t):
        a, b = np.array(to_rgb(a)), np.array(to_rgb(b))
        return tuple(a + (b - a) * np.clip(t, 0, 1))

    def water(z):
        if not sediment:
            return PLAIN
        # Steeper than a physical profile, but confined to the lower column.
        # Saturating the exponent instead (0.42) turned the whole water body
        # brown, which says "all sediment" rather than "most of it near the
        # bed" -- the opposite of the point.
        # A darker floor and a squarer exponent: the mid-column has to read as
        # visibly turbid, and with a pale top and a gentle curve it was landing
        # around 0.3 of the way to brown, which is nearly nothing on screen.
        return mix(WATER_TOP, WATER_BED,
                   float(np.exp(-(z + D) / (0.32 * D))) ** 0.50)

    faces = []

    def add(pts, fc, ec="#00000022", lw=0.4):
        faces.append((dep(pts), proj(pts), fc, ec, lw))

    nb = 26
    xb, yb = np.linspace(0, LX, nb + 1), np.linspace(0, LY, nb + 1)
    for i in range(nb):
        for j in range(nb):
            add([(xb[i], yb[j], -D), (xb[i + 1], yb[j], -D),
                 (xb[i + 1], yb[j + 1], -D), (xb[i], yb[j + 1], -D)],
                BED_C, "#00000010", 0.3)

    nz = 34
    for k in range(nz):
        f0, f1 = k / nz, (k + 1) / nz
        c = water(-D + 0.5 * (f0 + f1) * D)
        xs = np.linspace(0, LX, 90)
        for a, b in zip(xs[:-1], xs[1:]):
            add([(a, 0, -D + f0 * (sea_z(a) + D)),
                 (b, 0, -D + f0 * (sea_z(b) + D)),
                 (b, 0, -D + f1 * (sea_z(b) + D)),
                 (a, 0, -D + f1 * (sea_z(a) + D))], c, "none", 0)
        zt = sea_z(LX)
        ys = np.linspace(0, LY, 40)
        for a, b in zip(ys[:-1], ys[1:]):
            add([(LX, a, -D + f0 * (zt + D)), (LX, b, -D + f0 * (zt + D)),
                 (LX, b, -D + f1 * (zt + D)), (LX, a, -D + f1 * (zt + D))],
                c, "none", 0)

    xs, ys = np.linspace(0, LX, 90), np.linspace(0, LY, 34)
    for i in range(len(xs) - 1):
        za, zb = sea_z(xs[i]), sea_z(xs[i + 1])
        sh = 0.86 + 0.14 * np.cos(2 * np.pi * xs[i] / WAVELEN)
        c = tuple(np.clip(np.array(to_rgb("#8fd3e2")) * sh, 0, 1))
        for j in range(len(ys) - 1):
            add([(xs[i], ys[j], za), (xs[i + 1], ys[j], zb),
                 (xs[i + 1], ys[j + 1], zb), (xs[i], ys[j + 1], za)],
                c, "none", 0)

    for a, b in zip(xb[:-1], xb[1:]):
        add([(a, 0, -D - 4), (b, 0, -D - 4), (b, 0, -D), (a, 0, -D)],
            SUB_C, "#00000018", 0.3)
    for a, b in zip(yb[:-1], yb[1:]):
        add([(LX, a, -D - 4), (LX, b, -D - 4), (LX, b, -D), (LX, a, -D)],
            mix(SUB_C, "#000000", 0.12), "#00000018", 0.3)

    faces.sort(key=lambda f: f[0])

    fig = plt.figure(figsize=(11.0, 5.0), facecolor="none")
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_facecolor("none")
    ax.add_collection(PolyCollection(
        [f[1] for f in faces], facecolors=[f[2] for f in faces],
        edgecolors=[f[3] for f in faces], linewidths=[f[4] for f in faces]))
    ax.set_aspect("equal")
    ax.autoscale_view()
    (a0, a1), (b0_, b1_) = ax.get_xlim(), ax.get_ylim()
    Wf, Hf = a1 - a0, b1_ - b0_
    ax.set_xlim(a0 - 0.055 * Wf, a1 + 0.045 * Wf)
    ax.set_ylim(b0_ - 0.055 * Hf, b1_ + 0.075 * Hf)
    ax.axis("off")

    # --- orbital paths, in the plane the waves travel along. The top orbit is
    # tangent to the surface at a crest: its centre sits one radius below the
    # crest, so the circle touches the water line instead of breaking through.
    crest = WAVELEN * 1.25                      # first crest past x = 0
    xo = crest
    zsurf = sea_z(xo)
    th = np.linspace(0, 2 * np.pi, 160)
    r_top = 6.0
    orbits = [(zsurf - r_top, r_top, r_top)]
    for f, rx, rz in ((0.42, 6.2, 3.9), (0.68, 5.6, 1.9), (0.90, 5.0, 0.5)):
        orbits.append((zsurf - f * (zsurf + D), rx, rz))
    for k, (zc, rx, rz) in enumerate(orbits):
        pts = proj([(xo + rx * np.cos(t), 0.0, zc + rz * np.sin(t))
                    for t in th])
        ax.plot(pts[:, 0], pts[:, 1], color=WAVE_C, lw=1.7, zorder=14)
        # Sense of rotation, at the top of each orbit. Under a progressive wave
        # the water at the crest moves with the wave, so the orbit runs
        # clockwise in this view. Skipped on the lowest orbit -- it is flattened
        # almost to a line and an arrowhead on it just reads as a blob.
        if k < len(orbits) - 1:
            dlt = 0.26
            a = proj([(xo + rx * np.cos(np.pi / 2 + dlt), 0.0,
                       zc + rz * np.sin(np.pi / 2 + dlt))])[0]
            b = proj([(xo + rx * np.cos(np.pi / 2 - dlt), 0.0,
                       zc + rz * np.sin(np.pi / 2 - dlt))])[0]
            ax.annotate("", xy=b, xytext=a, zorder=15,
                        arrowprops=dict(arrowstyle="-|>", color=WAVE_C, lw=1.7,
                                        mutation_scale=12, shrinkA=0,
                                        shrinkB=0))

    # --- current: a logarithmic profile standing on the near section, its top
    # vector starting exactly on the sea surface.
    # 45 degrees from the wave direction in the horizontal plane -- the physical
    # angle, which is what anyone reading an axonometric block actually reads.
    #
    # Be aware the camera flattens it: at this elevation a 45 degree plan angle
    # projects to about 13 degrees on screen, so the two arrow families look
    # closer to parallel than they are. No azimuth fixes that without going
    # nearly edge-on. Raise this toward 75-90 if the screen angle matters more
    # than the physical one (75 -> 22 degrees on screen, 90 -> 30).
    CUR_PLAN = np.radians(45.0)
    cdir = np.array([np.cos(CUR_PLAN), np.sin(CUR_PLAN), 0.0])
    px = 0.66 * LX
    zsurf_c = sea_z(px)
    z0 = 0.0016 * D
    # stops just short of the surface: the current direction rises on screen,
    # so a vector starting exactly at the waterline puts its head above it
    zs = np.linspace(0.045 * D, 0.90 * (zsurf_c + D), 8)
    umax = np.log(zs[-1] / z0)
    tips = []
    for zz in zs:
        L = 10.5 * np.log(zz / z0) / umax
        p0 = P(px, 0.0, -D + zz)
        vec = cdir * L
        p1 = p0 + np.array([vec @ right, vec @ up])
        tips.append(p1)
        ax.annotate("", xy=p1, xytext=p0, zorder=15,
                    arrowprops=dict(arrowstyle="-|>", color=CURR_C, lw=1.7,
                                    mutation_scale=13, shrinkA=0, shrinkB=0))

    # --- one bed-stress vector from each source, lying on the bed
    def bed_arrow(x, y, direction, length, colour):
        p0 = P(x, y, -D + 0.4)
        vec = np.asarray(direction, float) * length
        p1 = p0 + np.array([vec @ right, vec @ up])
        ax.annotate("", xy=p1, xytext=p0, zorder=18,
                    arrowprops=dict(arrowstyle="-|>", color=colour, lw=3.0,
                                    mutation_scale=18, shrinkA=0, shrinkB=0))
        return 0.5 * (p0 + p1)

    wave_bed = bed_arrow(xo - 5.0, 0.16 * LY, (1, 0, 0), 19.0, STRESS_C)
    curr_bed = bed_arrow(px - 4.0, 0.16 * LY, cdir, 30.0, STRESS_C)

    # --- report where everything landed, in image fractions
    (X0, X1), (Y0, Y1) = ax.get_xlim(), ax.get_ylim()

    def frac(pt):
        return [float((pt[0] - X0) / (X1 - X0)),
                float(1.0 - (pt[1] - Y0) / (Y1 - Y0))]

    anchors = {
        "waves": frac(P(0.42 * LX, LY, AMP + 2.0)),
        "orbital": frac(P(xo - r_top, 0, zsurf - 0.55 * (zsurf + D))),
        "current": frac(tips[-1]),
        "wave_bed": frac(wave_bed),
        "current_bed": frac(curr_bed),
        "sediment": frac(P(LX, 0, -D + 0.18 * D)),
    }
    save_anchors(name, anchors)
    return save(fig, name)


def slide_7b_process(d=None):
    """What acts on the bed. Water left plain, so nothing competes with the
    three mechanisms."""
    return _process_schematic(False, "7b-process")


def slide_7d_erosion(d=None):
    """What that produces. Identical geometry, water coloured by suspended
    load, so advancing from the previous slide changes only the water."""
    return _process_schematic(True, "7d-erosion")


def render_gif(d, dpi=100, ms=55):
    """The cascade: four panels playing the same eight days side by side.

    This is the one claim a still cannot make. You watch the colour enter at the
    wind panel and arrive at the turbidity panel most of a day later, and the
    four traces in the strip below step visibly to the right. Everywhere else in
    the module the lag is asserted; here it is simply visible.

    Reprising the opener as the closer: same chain, one storm."""
    import matplotlib.pyplot as plt
    import matplotlib.colors as mplc
    import cartopy.crs as ccrs
    import cartopy.feature as cfeature
    import cmocean.cm as cmo
    from matplotlib.animation import FuncAnimation, PillowWriter
    import pandas as pd

    if not os.path.exists(ANIM):
        raise SystemExit(f"{ANIM} missing — run with --extract-anim first.")
    a = dict(np.load(ANIM))
    nt = a["f_hs"].shape[0]
    t0 = pd.Timestamp("2022-01-01") + pd.Timedelta(hours=int(a["h0"]))
    times = t0 + pd.to_timedelta(np.arange(nt), unit="h")

    def bands(cmap, levels):
        return mplc.ListedColormap(cmap(np.linspace(0, 1, len(levels) - 1)))

    panels = [
        ("wind", "f_wind", "s_wind", LEVELS["wind"], SPEED_CMAP(), "#2a3f74"),
        ("currents", "f_curr", "s_curr", LEVELS["curr"], SPEED_CMAP(), "#4fc3d7"),
        ("waves", "f_hs", "s_hs", LEVELS["hs"], trunc(cmo.amp, 0.14), "#b23a2f"),
        ("turbidity", "f_turb", "s_turb", LEVELS["turb"], trunc(cmo.turbid, 0.10),
         "#8a6a1c"),
    ]

    fig = plt.figure(figsize=(12.0, 5.30), facecolor=PAPER)
    ext = domain_extent(d)
    # Intermediate resolution, not full: cartopy re-renders a feature on every
    # draw, so at 192 frames x 4 panels the "f" coastline costs 768 renders of a
    # polygon set whose extra detail is invisible at 280 px panel width.
    land = cfeature.GSHHSFeature(scale="i")
    arts = []
    for k, (name, fk, _, lev, cmap, _) in enumerate(panels):
        # Maps along the bottom; the traces sit above their right-hand half and
        # the top-left corner is deliberately left empty for the slide's text.
        ax = fig.add_axes([0.014 + k * 0.2470, 0.030, 0.236, 0.520],
                          projection=ccrs.Mercator())
        ax.set_extent(ext, crs=ccrs.PlateCarree())
        ax.set_facecolor(PAPER)
        ax.spines["geo"].set_visible(False)
        lon = d["era5_lon"] if name == "wind" else d["lon"]
        lat = d["era5_lat"] if name == "wind" else d["lat"]
        v = a[fk][0].astype("f8")
        if name != "wind":
            v = np.where(d["mask"].astype(bool), v, np.nan)
        pc = ax.pcolormesh(lon, lat, v, cmap=bands(cmap, lev), vmin=0,
                           vmax=len(lev) - 2, transform=ccrs.PlateCarree(),
                           zorder=2)
        ax.add_feature(land, facecolor="none" if name == "wind" else LAND_FILL,
                       edgecolor=PAPER if name == "wind" else LAND_EDGE,
                       linewidth=0.5, zorder=3)
        ax.set_title(name, fontsize=10.5, color=INK, fontfamily=F_BODY,
                     loc="left", pad=4)
        # the point the traces above are taken from
        lo0, la0 = d["site_lonlat"]
        ax.plot([float(lo0)], [float(la0)], marker="o", ms=5.5, mfc=ACCENT,
                mec=PAPER, mew=1.0, transform=ccrs.PlateCarree(), zorder=8)
        arts.append(pc)

    # the strip: four lanes, each normalised in its own band, so the peaks
    # stepping to the right is the only thing the eye has to read
    # All four traces share one lane rather than stacking into four.
    # Stacked, each lane was about 20 px tall and the cascade read as four flat
    # lines -- the opposite of the point. Overlaid, every trace gets the full
    # height and the horizontal offset between the peaks, which is the whole
    # claim, is directly comparable on one axis.
    st = fig.add_axes([0.560, 0.660, 0.420, 0.290])
    st.set_xlim(0, nt - 1); st.set_ylim(-0.06, 1.12)
    st.axis("off")
    st.plot([0, nt - 1], [0, 0], color=RULE, lw=0.6, zorder=0)
    for k, (name, _, sk, _, _, col) in enumerate(panels):
        y = np.asarray(a[sk], "f8")
        y = (y - y.min()) / max(np.ptp(y), 1e-9)
        st.plot(np.arange(nt), y, color=col, lw=1.5, zorder=3 + k)
        # legend row, top left, in the trace colours
        x = 0.005 + k * 0.180
        st.plot([x, x + 0.030], [1.075, 1.075], color=col, lw=2.4,
                transform=st.transAxes, clip_on=False)
        st.text(x + 0.040, 1.075, name, fontsize=8, color=col,
                fontfamily=F_MONO, ha="left", va="center",
                transform=st.transAxes)
    st.text(0.0, 1.215, "normalised  ·  at the marked site, 6 m depth",
            fontsize=7.5, color=INK_3, fontfamily=F_MONO, ha="left",
            va="center", transform=st.transAxes)
    for day in range(0, nt, 24):
        st.axvline(day, color=RULE, lw=0.6, zorder=0)
        st.text(day + 2, -0.09, times[day].strftime("%-d %b"), fontsize=7.5,
                color=INK_3, fontfamily=F_MONO, va="top")
    cursor = st.axvline(0, color=ACCENT, lw=1.5, zorder=9)
    # between the traces and the maps: the top-right is the trace legend and
    # the top-left is reserved for the slide's own text
    clock = fig.text(0.980, 0.580, "", fontsize=10, color=INK_2,
                     fontfamily=F_MONO, ha="right", va="bottom")

    def frame(i):
        for (name, fk, _, _, _, _), pc in zip(panels, arts):
            v = a[fk][i].astype("f8")
            if name != "wind":
                v = np.where(d["mask"].astype(bool), v, np.nan)
            pc.set_array(v.ravel())
        cursor.set_xdata([i, i])
        clock.set_text(times[i].strftime("%-d %b %Y  ·  %H:%M UTC"))
        return arts + [cursor, clock]

    out = os.path.join(ASSET_DIR, "chain-8-cascade.gif")
    FuncAnimation(fig, frame, frames=nt).save(
        out, writer=PillowWriter(fps=max(1, round(1000 / ms))), dpi=dpi)
    print(f"wrote {out} ({os.path.getsize(out) / 1e6:.1f} MB, {nt} frames)")
    return out


SLIDES = {2: slide_2, 4: slide_4, 5: slide_5, 6: slide_6, 7: slide_7,
          31: slide_3a_door, 32: slide_3b_ocean,
          33: slide_3c_tide, 34: slide_3d_waves, 51: slide_5_block, 52: slide_5a_sst, 61: slide_6a_hs,
          71: slide_7a_calib, 72: slide_7b_process, 73: slide_7c_modis,
          74: slide_7d_erosion}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--extract", action="store_true",
                    help="rebuild assets/chain-stills.npz from the model output")
    ap.add_argument("--extract-anim", action="store_true",
                    help="rebuild assets/chain-frames.npz (~20 MB, gitignored)")
    ap.add_argument("--slide", type=int, choices=sorted(SLIDES))
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--gif", action="store_true", help="render the cascade loop")
    ap.add_argument("--dpi", type=int, default=200)
    args = ap.parse_args()

    if args.extract:
        extract()
    if args.extract_anim:
        extract_anim()
    if (args.extract or args.extract_anim) and not (args.slide or args.all
                                                    or args.gif):
        return

    import matplotlib
    matplotlib.use("Agg")
    register_fonts()
    import matplotlib.pyplot as plt
    plt.rcParams["font.family"] = F_BODY

    d = load()
    if args.gif:
        render_gif(d)
    if not (args.slide or args.all):
        return
    todo = sorted(SLIDES) if args.all else [args.slide]
    for n in todo:
        SLIDES[n](d)


if __name__ == "__main__":
    main()
