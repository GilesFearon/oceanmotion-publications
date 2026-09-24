#!/usr/bin/env python3
"""
Ocean Motion Analytics — water level figures for the ports deck.

All drawn from work that already exists in the model repo and rebuilt here so
it carries the deck's typography:

  tide       the predicted tide, CROCO against the gauge, at Salmiya and Majis:
             August 2023 shown, statistics over each gauge's whole record.
             Context rather than the pitch -- operationally the local forecast
             takes its tide from the gauge's own harmonics, and the residual is
             what the model brings.
  residual   the non-tidal residual at the same two gauges, gauge against CROCO
             and MERCATOR, whole record plus a two-month zoom. Same inputs as
             postprocess_water_levels/plot_residuals_MERCATOR_pres.py.
  abudhabi   nine years of modelled residual at Khalifa Port, where there is no
             gauge to hold it to, extracted with tidal_analysis.py's recipe.
  tidetable  a week of spring lows at Khalifa Port with a persistent set-down on
             top: total water level against the tide table.
  dashboard  the same week as a stand-in for the client view, with the limit on
             total water level as the live site draws it.

Gauge, CROCO and MERCATOR residuals are the operational ones, read from the
models repo rather than refitted here: each series minus its own utide fit over
the gauge record period, trend=False (see gauge()). The numbers that decide
what the deck may claim, as --all prints them, over each gauge's whole record
(Jun 2023 - Mar 2024 at Salmiya, Feb 2023 - Mar 2024 at Majis):

              predicted tide       residual r (RMSE)
              r      RMSE          CROCO        MERCATOR     mean of the two
  Salmiya     0.87   38 cm         0.88 (9 cm)  0.93 (7)     0.94 (6.5)
  Majis       0.98   14 cm         0.60 (6 cm)  0.77 (4)     0.74 (5)

MERCATOR includes the inverse barometer (it is not forced by air pressure);
without it Salmiya drops to 0.77, missing most of the annual cycle.

The annual constituent: Majis's 14-month record resolves SA, so the annual
cycle is in the gauge tide and removed from both model residuals. Salmiya's 9
months do not, so the annual cycle is in all three residuals, and the models
have to carry it (the monthly-mean residual runs +23 cm in June to -18 cm in
February). Method, in full: oceanmotion-models/ops/postprocess/
water_level_method.md

That is the slide 12 argument in one table: the surge is made inside the Gulf,
so it is large and well captured at Salmiya and small and hard to pick out at
Majis -- while the tide, which comes in through Hormuz, is reproduced almost
exactly at Majis and accumulates phase error (1 - 1.5 h) by the head of the
Gulf. At Majis the model lags the gauge by the same ~25 min on every
constituent, which looks like a timestamp convention on the hourly averages
rather than physics; unverified.

Runs in the somisana_croco environment (needs utide, and crocotools_py for the
extraction). The deck builder runs in base.

Usage:   python make_water_levels.py --extract     # ~108 monthly files, once
         python make_water_levels.py --all
Output:  assets/wl-abudhabi.nc   (gitignored)
         assets/wl-<name>.png
"""

import argparse
import os
import warnings

import numpy as np

warnings.filterwarnings("ignore", category=RuntimeWarning)

# ------------------------------------------------------------------ paths
HERE = os.path.dirname(os.path.abspath(__file__))
ASSET_DIR = os.path.join(HERE, "assets")
FONT_DIR = os.path.join(HERE, "fonts")

MODELS = os.path.expanduser("~/code/oceanmotion-models")
CROCO_H = os.path.join(MODELS, "configs/gulf_01/croco_v1.3.1/hindcast")
TIDAL = os.path.join(CROCO_H, "tidal_analysis")
SURF = os.path.join(CROCO_H, "C04_I01_GLORYS_ERA5/output/croco_avg_surf*")
GRD = os.path.join(CROCO_H, "GRID/croco_grd.nc")
OBS = os.path.join(MODELS, "datasets/water_level_obs/from_Chris_2024-03-30/"
                           "postprocess")
# hourly zos, Feb 2023 - Jun 2024, demeaned with the CMEMS MDT
MERCATOR = os.path.join(MODELS, "datasets/MERCATOR/gulf_ssh")

CACHE = os.path.join(ASSET_DIR, "wl-abudhabi.nc")

# The same window tidal_analysis.py fits over: nine full years, long enough to
# separate SA from SSA and K1 from P1 without inference.
PERIOD = slice("2016-01-01", "2024-12-31")

# Abu Dhabi. The parent grid is ~3 km, so this is the nearest wet cell to the
# terminal rather than the terminal itself -- ~6 m deep and within 2 km,
# checked against mask_rho. (Zayed Port was extracted alongside it once and
# tracked it at r = 0.99; a cache built before it was dropped still carries
# its series, unused.)
PORTS = {
    "Khalifa Port": dict(lon=54.655, lat=24.805),
}

GAUGE_LAT = {"Salmiya": 29.356870, "Majis": 24.512053}
GAUGE_NAME = {"Salmiya": "Salmiya, Kuwait", "Majis": "Majis, Oman"}

# The month shown on the tide slide.
TIDE_MONTH = ("2023-08-01", "2023-09-01")

# The residual zoom: Nov-Dec 2023, the stretch the original figure zooms on.
# At Salmiya it holds the largest set-down (-0.72 m, 15 Dec) and a +0.48 m
# set-up (20 Nov).
ZOOM = ("2023-11-01", "2024-01-01")

# One vertical scale for both gauges' residuals, so the slides show the
# difference in size rather than each filling its own frame. Covers every
# gauge value at both: Salmiya -0.72 to +0.48, Majis -0.24 to +0.83.
RES_YLIM = (-0.8, 0.9)

# The Khalifa Port week: spring lows from 21 to 25 January 2023 with the
# residual between -0.1 and -0.2 m throughout. Daily low water falls below
# -1.0 m on five successive days where the tide table alone gets there on three,
# and on 22 Jan reaches -1.17 m -- the lowest water in the nine-year record,
# 0.11 m below the lowest tide the table predicts in all nine years.
LOW_WEEK = ("2023-01-18 12:00", "2023-01-27 12:00")
LOW_NOW = "2023-01-20 06:00"     # the dashboard's issue time
LOW_LIMIT = -1.0                 # placeholder client limit, m about MSL

# ------------------------------------------------------------------ tokens
# Mirrored from deckkit; duplicated because deckkit needs python-pptx, which
# this environment does not have.
NAVY    = "#091c33"
CYAN    = "#4fc3d7"
MODEL   = "#1f7f92"   # the model line on every validation panel in the deck
MERC    = "#8c6bb1"   # MERCATOR: second model, never the accent
ACCENT  = "#ff6a2b"
PAPER   = "#f4efe3"
INK     = "#0b1420"
INK_2   = "#4a5665"
INK_3   = "#8a94a2"
RULE    = "#d6cdb6"
GRID    = "#e2d9c3"

F_DISPLAY, F_BODY, F_MONO = "Instrument Serif", "IBM Plex Sans", "IBM Plex Mono"


# ------------------------------------------------------------------ data
def extract():
    """Model residual at the Abu Dhabi port, tidal_analysis.py's recipe."""
    import utide
    import xarray as xr
    import crocotools_py.postprocess as post
    from datetime import datetime

    out = {}
    for name, p in PORTS.items():
        print(f"--- {name}")
        ds = post.get_ts(SURF, "zeta", p["lon"], p["lat"], Yorig=1993,
                         grdname=GRD, time=PERIOD)
        zeta = ds.zeta.values
        time = ds.time.values
        tdt = time.astype("datetime64[s]").astype(datetime)
        coef = utide.solve(tdt, zeta, lat=p["lat"], trend=False,
                           verbose=False)
        tide = utide.reconstruct(tdt, coef, verbose=False).h
        key = name.split()[0].lower()
        out[f"{key}_zeta"] = ("time", zeta)
        out[f"{key}_tide"] = ("time", tide)
        out[f"{key}_residual"] = ("time", zeta - tide)
        print(f"    {len(time)} steps, residual {np.nanmin(zeta - tide):+.2f}"
              f" to {np.nanmax(zeta - tide):+.2f} m, "
              f"M2 {coef.A[list(coef.name).index('M2')]:.3f} m")
    os.makedirs(ASSET_DIR, exist_ok=True)
    xr.Dataset(out, coords={"time": time},
               attrs={"source": SURF, "period": "2016-2024",
                      "method": "utide.solve(trend=False), residual = zeta - "
                                "reconstruct; same as tidal_analysis.py",
                      "ports": str(PORTS)}).to_netcdf(CACHE)
    print(f"wrote {CACHE}")


def gauge(name):
    """Gauge, CROCO and MERCATOR residuals exactly as the operational system
    defines them -- read from the same files, not refitted here, so the deck
    cannot drift from what ops/postprocess/handlers/water_level.py does.

      gauge     water level minus the gauge constituents
                ({name}_utide_coef.pkl, the forecast's predicted tide)
      CROCO     zeta minus the model constituents (utide_coef_{name}.pkl),
                which tidal_analysis.py fits exactly as the gauge is fitted:
                over the gauge's own record period, utide trend=False
      MERCATOR  sea level minus the CMEMS MDT, plus the inverse barometer
                from ERA5 pressure, minus its own harmonic fit over the gauge
                period (mercator_tidal_{name}.nc) -- no tide to remove, but the
                fit takes out the seasonal constituents the gauge tide already
                carries, so they are not counted twice

    trend=False because the records are too short to fit a trend: at Salmiya a
    trend fit gives -54 cm/yr, which puts a 2026 predicted tide 1.5 m low. The
    statistics this produces are the ones in croco_residual_stats.nc and
    mercator_residual_stats.nc, which set the forecast's confidence bands."""
    import pickle
    import utide
    import xarray as xr

    obs = xr.open_dataset(os.path.join(OBS, f"{name}.nc"))
    t = obs.time.values
    wl = obs.water_level.values.astype("f8")
    with open(os.path.join(OBS, f"{name}_utide_coef.pkl"), "rb") as fh:
        c_obs = pickle.load(fh)["coef"]
    with open(os.path.join(TIDAL, f"utide_coef_{name}.pkl"), "rb") as fh:
        c_mod = pickle.load(fh)["coef"]
    mod = xr.open_dataset(os.path.join(TIDAL, f"croco_tidal_{name}.nc"))
    merc = xr.open_dataset(os.path.join(MERCATOR, f"mercator_tidal_{name}.nc"))

    def tide(c):
        # about zero: the gauge is on chart datum, the model on its own MSL
        return utide.reconstruct(t, c, verbose=False).h - c.mean

    g = dict(t=t, c_obs=c_obs, c_mod=c_mod,
             tide_obs=tide(c_obs), tide_mod=tide(c_mod),
             res_obs=wl - utide.reconstruct(t, c_obs, verbose=False).h,
             res_mod=mod.residuals.interp(time=t).values,
             res_merc=merc.residuals.interp(time=t).values)
    g["res_mean"] = (g["res_mod"] + g["res_merc"]) / 2
    return g


def _stats(mod, obs, mask=None):
    mod, obs = np.asarray(mod, "f8"), np.asarray(obs, "f8")
    ok = np.isfinite(mod) & np.isfinite(obs)
    if mask is not None:
        ok &= mask
    m, o = mod[ok], obs[ok]
    return dict(n=int(ok.sum()), bias=float((m - o).mean()),
                rmse=float(np.sqrt(((m - o) ** 2).mean())),
                r=float(np.corrcoef(m, o)[0, 1]))


def residual_stats(g):
    """CROCO, MERCATOR and their mean against the gauge, over the hours all
    three exist -- so the three rows are scored on the same record."""
    common = (np.isfinite(g["res_obs"]) & np.isfinite(g["res_mod"])
              & np.isfinite(g["res_merc"]))
    return {k: _stats(g[f"res_{k}"], g["res_obs"], common)
            for k in ("mod", "merc", "mean")}, common


def constituents(g, names=("M2", "S2", "N2", "K1", "O1")):
    """Amplitude (m) and phase lag (minutes, model behind gauge) per constituent."""
    rows = []
    for c in names:
        io, im = list(g["c_obs"].name).index(c), list(g["c_mod"].name).index(c)
        dg = (g["c_mod"].g[im] - g["c_obs"].g[io] + 180) % 360 - 180
        speed = g["c_obs"].aux.frq[io] * 360          # deg per hour
        rows.append(dict(name=c, a_obs=float(g["c_obs"].A[io]),
                         a_mod=float(g["c_mod"].A[im]),
                         lag_min=float(dg / speed * 60)))
    return rows


def span(t):
    """'15 Jun 2023 – 26 Mar 2024  ·  9 months' for a time axis."""
    import pandas as pd
    t0, t1 = pd.Timestamp(t[0]), pd.Timestamp(t[-1])
    months = round((t1 - t0).days / 30.44)
    return f"{t0:%-d %b %Y} – {t1:%-d %b %Y}  ·  {months} months"


# ------------------------------------------------------------------ style
def register_fonts():
    from matplotlib import font_manager
    if not os.path.isdir(FONT_DIR):
        return
    for f in sorted(os.listdir(FONT_DIR)):
        if f.endswith(".ttf"):
            try:
                font_manager.fontManager.addfont(os.path.join(FONT_DIR, f))
            except Exception:
                pass


def _axes(ax, ylabel=None, step=None, minor=None):
    """Deck axes. With `step`, a labelled tick every `step` m and a horizontal
    rule at every tick (and at every `minor`, fainter), so peaks and troughs
    can be read straight off the slide."""
    from matplotlib.ticker import MultipleLocator
    ax.set_facecolor(PAPER)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    for sp in ("left", "bottom"):
        ax.spines[sp].set_color(RULE); ax.spines[sp].set_linewidth(0.8)
    ax.tick_params(labelsize=8, colors=INK_3, length=2.5, width=0.7)
    for lb in list(ax.get_xticklabels()) + list(ax.get_yticklabels()):
        lb.set_fontfamily(F_MONO); lb.set_color(INK_2)
    if step:
        ax.yaxis.set_major_locator(MultipleLocator(step))
        ax.grid(True, axis="y", which="major", color=GRID, lw=0.8)
        if minor:
            ax.yaxis.set_minor_locator(MultipleLocator(minor))
            ax.grid(True, axis="y", which="minor", color=GRID, lw=0.4)
            ax.tick_params(axis="y", which="minor", length=0)
        ax.set_axisbelow(True)
    ax.axhline(0, color=RULE, lw=0.9, zorder=1)
    if ylabel:
        ax.set_ylabel(ylabel, fontsize=8.5, color=INK_2, fontfamily=F_BODY)


def _fonts(ax):
    """Re-apply tick fonts after the locators have made new labels."""
    for lb in list(ax.get_xticklabels()) + list(ax.get_yticklabels()):
        lb.set_fontfamily(F_MONO); lb.set_color(INK_2)


def _legend(ax, ncol=2, **kw):
    leg = ax.legend(loc="lower left", bbox_to_anchor=(0.0, 1.005),
                    frameon=False, fontsize=8, ncol=ncol, handlelength=1.6,
                    columnspacing=1.4, **kw)
    for t in leg.get_texts():
        t.set_color(INK_2); t.set_fontfamily(F_MONO)


def _side(ax, text, y=0.98, size=8.5, color=INK_2):
    ax.text(1.015, y, text, transform=ax.transAxes, fontsize=size,
            color=color, fontfamily=F_MONO, ha="left", va="top",
            linespacing=1.55)


def _ylim(*series, step=0.25, pad=0.05):
    """Limits that cover every value, rounded out to the tick step."""
    lo = min(np.nanmin(s) for s in series) - pad
    hi = max(np.nanmax(s) for s in series) + pad
    return np.floor(lo / step) * step, np.ceil(hi / step) * step


def save(fig, name, dpi=200):
    os.makedirs(ASSET_DIR, exist_ok=True)
    out = os.path.join(ASSET_DIR, f"wl-{name}.png")
    fig.savefig(out, dpi=dpi, transparent=True, facecolor="none")
    print(f"wrote {out} ({os.path.getsize(out) / 1e3:.0f} kB)")
    return out


# ------------------------------------------------------------------ figures
def fig_tide(g, name):
    """A month of predicted tide, gauge under model, statistics over the whole
    gauge record. The pale-under-thin convention is the SST panel's: where the
    two agree the model line hides the gauge."""
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    import pandas as pd

    t = pd.to_datetime(g["t"])
    w = (t >= TIDE_MONTH[0]) & (t < TIDE_MONTH[1])
    fig = plt.figure(figsize=(11.0, 2.05), facecolor="none")
    ax = fig.add_axes([0.058, 0.13, 0.815, 0.72])
    ax.plot(t[w], g["tide_obs"][w], color=INK_3, lw=2.4, alpha=0.55,
            label="gauge harmonics")
    ax.plot(t[w], g["tide_mod"][w], color=MODEL, lw=0.9,
            label="model harmonics  (CROCO)")
    ax.set_xlim(pd.Timestamp(TIDE_MONTH[0]),
                pd.Timestamp(TIDE_MONTH[1]) - pd.Timedelta(hours=1))
    ax.set_ylim(*_ylim(g["tide_obs"][w], g["tide_mod"][w], step=0.5))
    ax.xaxis.set_major_locator(mdates.DayLocator(bymonthday=range(1, 32, 3)))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%-d %b"))
    _axes(ax, "predicted tide  (m)", step=0.5, minor=0.25)
    _fonts(ax)
    _legend(ax)
    st = _stats(g["tide_mod"], g["tide_obs"])
    _side(ax, f"r     {st['r']:.2f}\nRMSE  {st['rmse'] * 100:.0f} cm")
    _side(ax, "whole gauge\nrecord", y=0.42, size=7.5, color=INK_3)
    print(f"    {name} tide stats: r {st['r']:.3f} RMSE {st['rmse']:.3f} m")
    return save(fig, f"tide-{name.lower()}")


def fig_residual(g, name):
    """The residual at one gauge: the whole record above, Nov-Dec 2023 below,
    gauge against CROCO and MERCATOR.

    Both models are drawn because neither wins every event -- some set-downs
    are CROCO's, some MERCATOR's -- and their mean beats either, which is the
    argument for running an ensemble operationally. Statistics are over the
    hours all three exist, which is now each gauge's whole record."""
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    import pandas as pd

    t = pd.to_datetime(g["t"])
    st, common = residual_stats(g)
    fig = plt.figure(figsize=(11.0, 3.6), facecolor="none")
    a1 = fig.add_axes([0.058, 0.575, 0.775, 0.36])
    a2 = fig.add_axes([0.058, 0.085, 0.775, 0.40])
    lines = (("res_obs", INK, 1.0, 1.0, "tide gauge"),
             ("res_mod", MODEL, 1.0, 0.9, "CROCO"),
             ("res_merc", MERC, 1.0, 0.85, "MERCATOR + air pressure"))

    for ax, lo, hi, loc, fmt in (
            (a1, t[0], t[-1], mdates.MonthLocator(), "%b %Y"),
            (a2, pd.Timestamp(ZOOM[0]), pd.Timestamp(ZOOM[1]),
             mdates.WeekdayLocator(byweekday=mdates.MO), "%-d %b")):
        for key, c, lw, alpha, lab in lines:
            ax.plot(t, g[key], color=c, lw=lw * (0.6 if ax is a1 else 1.0),
                    alpha=alpha, label=lab)
        ax.set_xlim(lo, hi)
        ax.set_ylim(*RES_YLIM)
        ax.xaxis.set_major_locator(loc)
        ax.xaxis.set_major_formatter(mdates.DateFormatter(fmt))
        _axes(ax, "residual  (m)", step=0.2, minor=0.1)
        _fonts(ax)
    # the zoom window as an outline, as the original figure drew it
    from matplotlib.patches import Rectangle
    from matplotlib.dates import date2num
    x0, x1 = date2num(pd.Timestamp(ZOOM[0])), date2num(pd.Timestamp(ZOOM[1]))
    a1.add_patch(Rectangle((x0, RES_YLIM[0]), x1 - x0,
                           RES_YLIM[1] - RES_YLIM[0], fill=False,
                           edgecolor=ACCENT, lw=1.4, zorder=6, clip_on=False))
    _legend(a1, ncol=3)

    _side(a1, "          r     RMSE\n"
              f"CROCO     {st['mod']['r']:.2f}  {st['mod']['rmse'] * 100:.0f} cm\n"
              f"MERCATOR  {st['merc']['r']:.2f}  {st['merc']['rmse'] * 100:.0f} cm\n"
              f"mean      {st['mean']['r']:.2f}  {st['mean']['rmse'] * 100:.0f} cm",
          size=8)
    _side(a1, f"residual only\n{common.sum():,} hours".replace(",", " "),
          y=0.22, size=7.5, color=INK_3)
    for k, v in st.items():
        print(f"    {name} residual {k:5s} r {v['r']:.3f} RMSE "
              f"{v['rmse']:.3f} m n {v['n']}")
    return save(fig, f"residual-{name.lower()}")


def fig_abudhabi(d):
    """Nine years of modelled residual at Khalifa Port, and one event.

    Top: 2016-2024 as a pale band of hourly values under its 30-day mean, so
    the seasonal cycle and the scale of the excursions are both visible.
    Bottom: the largest set-down in the record, a fortnight either side,
    marked on the top panel."""
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    import pandas as pd

    t = pd.to_datetime(d.time.values)
    kh = pd.Series(d.khalifa_residual.values, index=t)
    i_min = kh.idxmin()
    w0, w1 = i_min - pd.Timedelta(days=12), i_min + pd.Timedelta(days=12)

    fig = plt.figure(figsize=(11.0, 4.6), facecolor="none")
    a1 = fig.add_axes([0.058, 0.60, 0.815, 0.33])
    a2 = fig.add_axes([0.058, 0.085, 0.815, 0.37])

    a1.plot(kh.index, kh.values, color=CYAN, lw=0.35, alpha=0.55,
            label="hourly")
    a1.plot(kh.index, kh.rolling("30D", center=True).mean().values,
            color=NAVY, lw=1.1, label="30-day mean")
    a1.axvspan(w0, w1, color=ACCENT, alpha=0.25, lw=0)
    a1.set_xlim(kh.index[0], kh.index[-1])
    a1.set_ylim(-0.6, 0.8)
    a1.xaxis.set_major_locator(mdates.YearLocator())
    a1.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    _axes(a1, "residual  (m)", step=0.2)
    _fonts(a1)
    _legend(a1)
    lo, hi = kh.quantile(0.001), kh.quantile(0.999)
    _side(a1, f"Khalifa Port\n2016 – 2024\n\n"
              f"min   {kh.min():+.2f} m\nmax   {kh.max():+.2f} m\n"
              f"0.1%  {lo:+.2f} m\n99.9% {hi:+.2f} m", size=8)

    s = slice(w0, w1)
    a2.plot(kh[s].index, kh[s].values, color=NAVY, lw=1.2)
    a2.set_xlim(w0, w1)
    a2.set_ylim(-0.6, 0.6)
    a2.xaxis.set_major_locator(mdates.DayLocator(interval=4))
    a2.xaxis.set_major_formatter(mdates.DateFormatter("%-d %b %Y"))
    _axes(a2, "residual  (m)", step=0.2)
    _fonts(a2)
    _side(a2, f"largest set-down\n{i_min:%-d %b %Y %H:%M}\n\n"
              f"{kh[i_min]:+.2f} m", size=8)
    print(f"    Abu Dhabi: min {kh.min():+.3f} at {i_min}, "
          f"max {kh.max():+.3f} at {kh.idxmax()}")
    return save(fig, "abudhabi")


def _khalifa_week(d):
    """Total water level, tide and residual at Khalifa Port over LOW_WEEK,
    about the model's mean sea level, plus the lowest predicted tide in the
    whole nine-year record -- the level a tide table would call its floor."""
    import pandas as pd
    t = pd.to_datetime(d.time.values)
    z = pd.Series(d.khalifa_zeta.values, index=t)
    tide = pd.Series(d.khalifa_tide.values, index=t)
    z0 = float(tide.mean())
    z, tide = z - z0, tide - z0
    floor = float(tide.min())
    s = slice(*LOW_WEEK)
    return z[s], tide[s], (z - tide)[s], floor


def fig_tidetable(d):
    """The UKC argument in one picture: a week of spring lows at Khalifa Port
    with a persistent set-down on top, total water level against the table.

    Shaded where the water is lower than the table, because that is the
    direction that eats clearance. The dashed floor is the lowest tide the
    table predicts in all of 2016-2024; on 22 Jan the water goes under it.
    Drawn from the hindcast -- what the model says happened, not a forecast
    issued at the time; the slide labels it that way."""
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates

    z, tide, res, floor = _khalifa_week(d)
    fig = plt.figure(figsize=(7.0, 3.9), facecolor="none")
    ax = fig.add_axes([0.095, 0.10, 0.885, 0.76])
    ax.fill_between(tide.index, tide.values, z.values,
                    where=(z.values < tide.values), color=ACCENT,
                    alpha=0.30, lw=0, interpolate=True,
                    label="below the tide table")
    ax.plot(tide.index, tide.values, color=INK_3, lw=1.3, ls=(0, (4, 2)),
            label="tide table  (astronomical tide)")
    ax.plot(z.index, z.values, color=NAVY, lw=1.5,
            label="modelled water level")
    ax.axhline(floor, color=ACCENT, lw=1.0, ls=(0, (1, 2)))
    # under the line on the left: nothing crosses it before 22 Jan
    ax.text(z.index[0], floor - 0.03,
            f"  lowest predicted tide, 2016–24  ({floor:+.2f} m)",
            color=ACCENT, fontsize=7.5, fontfamily=F_MONO, ha="left",
            va="top")
    ax.set_xlim(z.index[0], z.index[-1])
    lo, hi = _ylim(z, tide, step=0.25)
    ax.set_ylim(lo - 0.25, hi)
    ax.xaxis.set_major_locator(mdates.DayLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%-d %b"))
    _axes(ax, "water level about MSL  (m)", step=0.25)
    _fonts(ax)
    _legend(ax, ncol=2)
    lw = z.idxmin()
    ax.annotate(f"{z[lw]:+.2f} m  ·  table {tide[lw]:+.2f} m",
                xy=(lw, z[lw]), xytext=(lw + (z.index[1] - z.index[0]) * 10,
                                        lo - 0.13),
                fontsize=8, color=NAVY, fontfamily=F_MONO, va="center",
                arrowprops=dict(arrowstyle="-", color=NAVY, lw=0.8,
                                shrinkA=2, shrinkB=3))
    days = z.resample("1D").min()
    print(f"    low week: lowest {z.min():+.2f} m at {lw} (table "
          f"{tide[lw]:+.2f}, residual {res[lw]:+.2f}); floor {floor:+.2f}; "
          f"days below {LOW_LIMIT}: water "
          f"{int((days < LOW_LIMIT).sum())}, table "
          f"{int((tide.resample('1D').min() < LOW_LIMIT).sum())}")
    return save(fig, "tidetable-khalifa")


def fig_dashboard(d):
    """A stand-in for the client dashboard, in the public site's idiom (flat
    PAPER panels, cyan traces, mono panel titles, a NOW rule), with the client's
    limit on total water level -- the number a berth is actually planned
    against -- as the live site draws a threshold on its own variable.

    The January 2023 week replayed as if issued on the morning of the 20th:
    hindcast values on both sides of NOW, so it shows what the view would look
    like, not what a forecast would have said. The limit is a placeholder."""
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    import pandas as pd

    z, tide, res, _ = _khalifa_week(d)
    now = pd.Timestamp(LOW_NOW)

    fig = plt.figure(figsize=(7.0, 3.9), facecolor=PAPER)
    axes = [fig.add_axes([0.075, 0.43, 0.905, 0.50]),
            fig.add_axes([0.075, 0.085, 0.905, 0.22])]
    for ax, title in zip(axes, ("TOTAL WATER LEVEL", "NON-TIDAL RESIDUAL")):
        ax.set_facecolor(PAPER)
        for sp in ax.spines.values():
            sp.set_visible(False)
        ax.grid(True, color="#dcd3bd", lw=0.7)
        ax.set_axisbelow(True)
        ax.tick_params(labelsize=7.5, colors=INK_2, length=0)
        ax.set_ylabel("m", fontsize=7.5, color=INK_2, fontfamily=F_MONO)
        ax.text(0.0, 1.03, title, transform=ax.transAxes, fontsize=8,
                color=INK_2, fontfamily=F_MONO, va="bottom")
        ax.axvline(now, color=INK, lw=1.4, zorder=5)
        ax.set_xlim(z.index[0], z.index[-1])
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=2))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%-d %b"))
    top, bot = axes
    top.text(now, 0.97, "  NOW", transform=top.get_xaxis_transform(),
             fontsize=7.5, color=INK, fontfamily=F_MONO, va="top")
    top.plot(tide.index, tide.values, color=INK_3, lw=1.0, ls=(0, (3, 2)))
    top.plot(z.index, z.values, color=CYAN, lw=1.4)
    top.axhline(LOW_LIMIT, color=ACCENT, lw=1.0, ls=(0, (3, 2)))
    # label the limit where the line runs clear of the traces
    # under the line at the left, where the trace stays above it until 21 Jan
    top.text(0.012, (LOW_LIMIT - (-1.4)) / (1.1 - (-1.4)) - 0.03,
             "YOUR LIMIT", transform=top.transAxes, fontsize=7,
             color=ACCENT, fontfamily=F_MONO, ha="left", va="top")
    top.text(1.0, 1.03, "TIDE TABLE  - -", transform=top.transAxes,
             fontsize=7, color=INK_3, fontfamily=F_MONO, ha="right",
             va="bottom")
    top.set_ylim(-1.4, 1.1)
    top.tick_params(axis="x", labelbottom=False)
    bot.plot(res.index, res.values, color=CYAN, lw=1.4)
    bot.set_ylim(-0.3, 0.2)
    for ax in axes:
        _fonts(ax)
    os.makedirs(ASSET_DIR, exist_ok=True)
    out = os.path.join(ASSET_DIR, "wl-dashboard.png")
    fig.savefig(out, dpi=200, facecolor=PAPER)
    print(f"wrote {out}")
    return out


def summary(gs):
    """Print the numbers the deck quotes, so the slides can be checked against
    what the data actually says."""
    for name, g in gs.items():
        print(f"--- {name}  ({span(g['t'])})")
        for row in constituents(g):
            print(f"    {row['name']}  gauge {row['a_obs']:.3f}  model "
                  f"{row['a_mod']:.3f}  d {100 * (row['a_mod'] - row['a_obs']):+.1f}"
                  f" cm  lag {row['lag_min']:+.0f} min")
        ro = g["res_obs"]
        print(f"    gauge residual  min {np.nanmin(ro):+.2f}  max "
              f"{np.nanmax(ro):+.2f}  std {np.nanstd(ro):.3f}  model std "
              f"{np.nanstd(g['res_mod']):.3f}")


# ------------------------------------------------------------------ main
if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("--extract", action="store_true",
                    help="extract the Abu Dhabi residual from the hindcast")
    ap.add_argument("--all", action="store_true", help="render every figure")
    args = ap.parse_args()

    if args.extract:
        extract()
    if args.all:
        import matplotlib
        matplotlib.use("Agg")
        import xarray as xr
        register_fonts()
        gs = {n: gauge(n) for n in ("Salmiya", "Majis")}
        summary(gs)
        for n, g in gs.items():
            fig_tide(g, n)
            fig_residual(g, n)
        if os.path.exists(CACHE):
            d = xr.open_dataset(CACHE)
            fig_abudhabi(d)
            fig_tidetable(d)
            fig_dashboard(d)
        else:
            print(f"  ({CACHE} missing — run --extract for the Abu Dhabi figures)")
