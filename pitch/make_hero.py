#!/usr/bin/env python3
"""
Ocean Motion Analytics — static hero streamline still for the pitch deck.

A faithful port of the website's animated hero (oceanmotion-web/hero.js): particles
trace geostrophic streamlines over a sea surface height field built from Gaussian
eddies, with velocity from u = -dn/dy, v = dn/dx. Physics, colours, tail lengths and
the left-side suppression all mirror the JS so the deck's title slide reads as the
same artwork, frozen mid-motion.

The sim runs in the website's logical pixel space (1600x900 CSS px) and is rendered
at higher dpi, so trail lengths stay in the same proportion to the frame as they are
on the site — resolution changes the sharpness, not the composition.

Regenerate:  python3 make_hero.py [--seed N] [--dpi N]
Output:      assets/hero-streamlines.png
Requires:    numpy, matplotlib
"""

import argparse
import os

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection

# ---------------------------------------------------------------- config
# Mirrors the constants at the top of hero.js.
W, H = 1600.0, 900.0          # logical CSS pixel space the sim runs in
NUM = 51                      # particles; the site's 180 spread over a full-width
                              # canvas, so packing them into a narrow band crowds it
TAIL_LEN = 80                 # 2x the site's 40: longer trails give the still the
                              # sense of sweep that motion supplies on the web
ACCENT_TAIL_LEN = 80
GRID_N = 64                   # coarse SSH grid
NUM_EDDIES = 1                # the site uses 4, but a still wants a much calmer
                              # field: with nothing moving to carry the eye, several
                              # eddies read as competing blobs behind the title
SPEED_SCALE = 1.2             # velocity scale in blendAndDeriveVelocity
STEP = 1.1                    # px per frame multiplier
BURN_IN = 220                 # frames to advance before freezing the frame

# --- still-image quality -------------------------------------------------
# The browser redraws 60x a second, so a thin, roughly-integrated, softly-beaded
# stroke reads fine there. Frozen and enlarged onto a 13" slide it does not, so
# the still is integrated more accurately and stroked more heavily than the site.
SUBSTEPS = 3                  # RK4 sub-steps per frame: kills the outward drift
                              # forward Euler produces on curved streamlines, and
                              # shortens each segment so strokes read as continuous
LINE_SCALE = 2.6              # the site's widths are ~1px hairlines at this output
                              # size, which alias into dashes; thicken them

# --- horizontal confinement ---------------------------------------------
# The field is faded out by a purely horizontal mask that reaches zero at mid-frame.
# Crucially the mask plateaus at 1 by the eddy's centre: any mask still rising as it
# crosses the SSH peak multiplies the peak down on its left flank and not its right,
# which walks the apparent warm centroid off-centre from the circulation.
FIELD_X0 = 0.5                # mask reaches zero here — left half is flat ground

# --- SSH shading ---------------------------------------------------------
GROUND = (5, 15, 28)          # --color-abyss, the low-SSH end of the ramp
WARM_GAIN = 0.5               # fraction of the site's excursion toward #6b2a14;
                              # at full strength the eddy reads far hotter frozen
                              # on a slide than it does moving behind a web page
WARM = tuple(int(round(g + WARM_GAIN * (hi - g)))
             for g, hi in zip(GROUND, (107, 42, 20)))
MIN_TAIL = 10                 # drop stubs: a just-respawned particle reads as motion
                              # while animating, but as a speck of dust in a still
MIN_SPAN = 14.0               # ...likewise a particle stalled in a low-velocity core,
                              # whose whole trail collapses into a few px

# Radial cutoff, in eddy radii, measured from the SSH peak. Far outside the eddy the
# gradient is nearly flat, so particles there barely move: they contribute stubby
# fragments that read as dirt on the slide rather than as circulation.
RADIAL_R0 = 1.5               # full opacity within this many radii of the centre
RADIAL_R1 = 2.3               # faded to nothing beyond this

# The site mixes faint blue, white and cyan streamlines. The deck uses cyan only,
# keeping the three tiers purely as an alpha/width hierarchy so the field still has
# depth, plus the site's single orange accent streamline.
CYAN = (120, 210, 230)        # --color-cyan
COLORS = {"dim": CYAN, "mid": CYAN, "bright": CYAN, "accent": (255, 140, 70)}
ALPHAS = {"dim": 0.35, "mid": 0.55, "bright": 0.75, "accent": 0.95}
WIDTHS = {"dim": 0.55, "mid": 0.7, "bright": 1.0, "accent": 1.8}

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "assets", "hero-streamlines.png")


# ---------------------------------------------------------------- field
def random_eddies(rng, n_eddies=NUM_EDDIES):
    """Eddies sit inside the right-hand band so the title area stays black."""
    # One broad eddy, its SSH peak sitting inside the visible band and its radius
    # scaled so the circulation fills the band's width.
    eddies = [(0.80 + rng.random() * 0.07,        # peak toward the top right
               0.13 + rng.random() * 0.13,
               0.19 + rng.random() * 0.06,
               0.6 + rng.random() * 0.4)]
    for _ in range(n_eddies - 1):
        eddies.append((0.45 + rng.random() * 0.47,
                       0.08 + rng.random() * 0.84,
                       0.08 + rng.random() * 0.18,
                       (-1 if rng.random() < 0.5 else 1) * (0.4 + rng.random() * 0.6)))
    return eddies


def compute_ssh(eddies):
    n = GRID_N
    ax = np.linspace(0.0, 1.0, n)
    x, y = np.meshgrid(ax, ax)            # x varies along axis 1, y along axis 0
    ssh = np.zeros((n, n), dtype=np.float64)
    for cx, cy, r, amp in eddies:
        ssh += amp * np.exp(-(((x - cx) ** 2 + (y - cy) ** 2) / (r * r)))
    return ssh


def derive_velocity(ssh):
    """Geostrophic balance: u = -dn/dy, v = dn/dx, central differences with
    boundary clamping — matching the finite differences used in hero.js."""
    n = GRID_N
    ip = np.minimum(np.arange(n) + 1, n - 1)
    im = np.maximum(np.arange(n) - 1, 0)
    dhdx = (ssh[:, ip] - ssh[:, im]) / np.where(ip == im, 1, 2)
    dhdy = (ssh[ip, :] - ssh[im, :]) / np.where(ip == im, 1, 2)[:, None]
    return -dhdy * n * SPEED_SCALE, dhdx * n * SPEED_SCALE


def sample(grid, nx, ny):
    """Bilinear sample of a GRID_N x GRID_N field at normalised coords."""
    n = GRID_N
    gx = np.clip(nx, 0.0, 1.0) * (n - 1)
    gy = np.clip(ny, 0.0, 1.0) * (n - 1)
    i0 = np.clip(gx.astype(int), 0, n - 2)
    j0 = np.clip(gy.astype(int), 0, n - 2)
    fx, fy = gx - i0, gy - j0
    return (grid[j0, i0] * (1 - fx) * (1 - fy) +
            grid[j0, i0 + 1] * fx * (1 - fy) +
            grid[j0 + 1, i0] * (1 - fx) * fy +
            grid[j0 + 1, i0 + 1] * fx * fy)


def mask_profile(nx, x1):
    """Horizontal visibility: 0 at FIELD_X0, smoothstepping to 1 at x1 (the eddy
    centre) and flat at 1 beyond it, so the masked field peaks where the SSH does."""
    t = np.clip((nx - FIELD_X0) / max(x1 - FIELD_X0, 1e-6), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def background(ssh, eddy, w=960, h=540):
    """SSH shaded from the abyss ground (low) toward warm orange (high), faded out
    to the left by mask_profile so the title area stays flat black."""
    x1 = eddy[0]
    nx, ny = np.meshgrid(np.linspace(0, 1, w), np.linspace(0, 1, h))
    t = sample(ssh, nx, ny)
    t = (t - t.min()) / (np.ptp(t) or 1.0)
    s = t * mask_profile(nx, x1)
    img = np.empty((h, w, 3), dtype=np.uint8)
    for c in range(3):
        img[..., c] = (GROUND[c] + s * (WARM[c] - GROUND[c])).astype(np.uint8)
    return img


# ---------------------------------------------------------------- particles
ASPECT = H / W


def velocity(gu, gv, x, y):
    """Velocity in pixels/frame at a pixel position.

    gu/gv are derivatives with respect to *normalised* coordinates, but particles
    step through *pixel* space. On a non-square canvas that mismatch means
        dn/dt = dn/dx (-dn/dy H) + dn/dy (dn/dx W) = (W - H) dn/dx dn/dy != 0
    so particles drift across SSH contours instead of following them — the flow
    stops being geostrophic, and the circulation sits offset from the SSH peak.
    (hero.js has the same issue; it is invisible while everything is moving.)
    Scaling the y-component by H/W makes the two terms cancel exactly, so n is
    conserved along a trajectory and streamlines follow the contours."""
    return (float(sample(gu, np.array(x / W), np.array(y / H))),
            float(sample(gv, np.array(x / W), np.array(y / H))) * ASPECT)


def rk4(gu, gv, x, y, h):
    """Classical RK4 on the (steady) velocity field. Forward Euler, as used in the
    browser, systematically throws particles outward on curved streamlines — an
    error invisible at 60fps but obvious in a still, where it turns what should be
    closed contours around an eddy into loose spirals."""
    k1x, k1y = velocity(gu, gv, x, y)
    k2x, k2y = velocity(gu, gv, x + 0.5 * h * k1x, y + 0.5 * h * k1y)
    k3x, k3y = velocity(gu, gv, x + 0.5 * h * k2x, y + 0.5 * h * k2y)
    k4x, k4y = velocity(gu, gv, x + h * k3x, y + h * k3y)
    return (x + h * (k1x + 2 * k2x + 2 * k3x + k4x) / 6.0,
            y + h * (k1y + 2 * k2y + 2 * k3y + k4y) / 6.0)


def simulate(rng, gu, gv):
    """Advect particles and return their trails, frozen after BURN_IN frames."""
    x0 = FIELD_X0 * W

    def spawn(idx, aged):
        # seeded only in the right-hand band; the flow may carry them left,
        # where the edge ramp fades them out
        x = x0 + rng.random() * (W - x0)
        if idx == 0:                                  # the single accent streamline
            key = "accent"
            y = H * 0.1 + rng.random() * (H * 0.5)
            life = 600 + rng.random() * 400
        else:
            r = rng.random()
            key = "bright" if r < 0.14 else "mid" if r < 0.48 else "dim"
            y = rng.random() * H
            life = 160 + rng.random() * 260
        return {"x": x, "y": y, "trail": [(x, y)], "key": key, "life": life,
                # stagger initial ages so the frozen frame shows a natural mix
                # of fresh and fading streamlines rather than a synchronised flush
                "age": rng.random() * life if aged else 0.0,
                "maxtail": (ACCENT_TAIL_LEN if idx == 0 else TAIL_LEN) * SUBSTEPS}

    ps = [spawn(i, aged=True) for i in range(NUM)]
    h = STEP / SUBSTEPS

    for _ in range(BURN_IN):
        for i, p in enumerate(ps):
            for _ in range(SUBSTEPS):
                p["x"], p["y"] = rk4(gu, gv, p["x"], p["y"], h)
                p["trail"].append((p["x"], p["y"]))
            p["age"] += 1.0                # dt * 0.06 at ~60fps ~= 1 age unit/frame
            del p["trail"][:-p["maxtail"]]
            if (p["x"] < -30 or p["x"] > W + 30 or p["y"] < -30 or p["y"] > H + 30
                    or p["age"] > p["life"]):
                ps[i] = spawn(i, aged=False)
    return ps


def draw(ps, ax, eddy):
    """Each trail is a run of segments whose alpha ramps quadratically to the head."""
    cx, cy, er, _ = eddy
    x1 = cx
    segs, cols, widths = [], [], []
    accent = []
    for p in ps:
        tr = p["trail"]
        if len(tr) < MIN_TAIL * SUBSTEPS:
            continue
        xs = [q[0] for q in tr]; ys = [q[1] for q in tr]
        if max(max(xs) - min(xs), max(ys) - min(ys)) < MIN_SPAN:
            continue
        r, g, b = (c / 255.0 for c in COLORS[p["key"]])
        base, w = ALPHAS[p["key"]], WIDTHS[p["key"]]
        n = len(tr)
        for j in range(1, n):
            frac = j / n
            seg = [tr[j - 1], tr[j]]
            mx = (seg[0][0] + seg[1][0]) * 0.5
            my = (seg[0][1] + seg[1][1]) * 0.5
            # streamlines fade on the same horizontal profile as the SSH shading...
            edge = float(mask_profile(np.array(mx / W), x1))
            if edge <= 0.0:
                continue
            # ...and again radially, so the field ends where the eddy's influence does
            d = np.hypot(mx / W - cx, my / H - cy) / er
            q = min(1.0, max(0.0, (RADIAL_R1 - d) / (RADIAL_R1 - RADIAL_R0)))
            radial = q * q * (3.0 - 2.0 * q)
            if radial <= 0.0:
                continue
            col = (r, g, b, base * frac * frac * edge * radial)
            lw = w * 0.72 * LINE_SCALE   # CSS px -> pt at the 100-dpi scale
            if p["key"] == "accent":
                accent.append((seg, col, lw))
            else:
                segs.append(seg); cols.append(col); widths.append(lw)

    ax.add_collection(LineCollection(segs, colors=cols, linewidths=widths,
                                     capstyle="round", antialiaseds=True))

    # the accent streamline carries a soft glow on the site (shadowBlur); approximate
    # it with a few progressively wider, fainter passes underneath the core stroke
    if accent:
        # multipliers are modest because LINE_SCALE has already thickened the core
        # stroke; the site's wider ratios turn the accent into an orange blob here
        for mult, fade in ((3.2, 0.05), (2.1, 0.09), (1.5, 0.14)):
            ax.add_collection(LineCollection(
                [s for s, _, _ in accent],
                colors=[(c[0], c[1], c[2], c[3] * fade) for _, c, _ in accent],
                linewidths=[w * mult for _, _, w in accent],
                capstyle="round", antialiaseds=True))
        ax.add_collection(LineCollection(
            [s for s, _, _ in accent], colors=[c for _, c, _ in accent],
            linewidths=[w for _, _, w in accent], capstyle="round", antialiaseds=True))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=7, help="field/particle RNG seed")
    ap.add_argument("--dpi", type=int, default=180, help="output dpi (180 -> 2880px wide)")
    ap.add_argument("--eddies", type=int, default=NUM_EDDIES,
                    help="eddies in the field; fewer = simpler background")
    ap.add_argument("--out", default=OUT)
    args = ap.parse_args()

    rng = np.random.default_rng(args.seed)
    eddies = random_eddies(rng, args.eddies)
    eddy = eddies[0]                       # mask plateaus at the main eddy's centre
    ssh = compute_ssh(eddies)
    gu, gv = derive_velocity(ssh)
    ps = simulate(rng, gu, gv)

    fig = plt.figure(figsize=(W / 100.0, H / 100.0), dpi=100)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, W); ax.set_ylim(H, 0)   # y down, as in canvas coords
    ax.axis("off")
    ax.imshow(background(ssh, eddy), extent=(0, W, H, 0), interpolation="bilinear",
              aspect="auto", zorder=0)
    draw(ps, ax, eddy)

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    fig.savefig(args.out, dpi=args.dpi, facecolor="#050f1c")
    plt.close(fig)
    print("wrote %s (seed %d, %d px wide)"
          % (args.out, args.seed, int(W / 100.0 * args.dpi)))


if __name__ == "__main__":
    main()
