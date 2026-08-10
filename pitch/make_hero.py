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
NUM = 180                     # particles
TAIL_LEN = 40
ACCENT_TAIL_LEN = 80
GRID_N = 64                   # coarse SSH grid
NUM_EDDIES = 4
SPEED_SCALE = 1.2             # velocity scale in blendAndDeriveVelocity
STEP = 1.1                    # px per frame multiplier
BURN_IN = 220                 # frames to advance before freezing the frame
MIN_TAIL = 10                 # drop stubs: a just-respawned particle reads as motion
                              # while animating, but as a speck of dust in a still
MIN_SPAN = 9.0                # ...likewise a particle stalled in a low-velocity core,
                              # whose whole trail collapses into a few px

COLORS = {
    "faint":  (30, 70, 120),
    "white":  (220, 232, 240),
    "cyan":   (120, 210, 230),
    "accent": (255, 140, 70),
}
ALPHAS = {"faint": 0.35, "white": 0.55, "cyan": 0.75, "accent": 0.95}
WIDTHS = {"faint": 0.55, "white": 0.7, "cyan": 1.0, "accent": 1.8}

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "assets", "hero-streamlines.png")


# ---------------------------------------------------------------- field
def random_eddies(rng):
    """Eddies biased to the right half so the left (where the title sits) stays calm."""
    eddies = [(0.7 + rng.random() * 0.2,          # guaranteed warm eddy, top-right
               0.1 + rng.random() * 0.25,
               0.12 + rng.random() * 0.14,
               0.6 + rng.random() * 0.4)]
    for _ in range(NUM_EDDIES - 1):
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


def background(ssh, w=960, h=540):
    """SSH shaded dark navy (low) to warm orange (high), suppressed quadratically
    toward the left edge so the title area stays near-black. Same ramp as hero.js."""
    nx, ny = np.meshgrid(np.linspace(0, 1, w), np.linspace(0, 1, h))
    t = sample(ssh, nx, ny)
    t = (t - t.min()) / (np.ptp(t) or 1.0)
    s = t * nx ** 2                       # quadratic suppression, 0 at left
    img = np.empty((h, w, 3), dtype=np.uint8)
    img[..., 0] = (5 + s * 102).astype(np.uint8)     # R:  5 -> 107
    img[..., 1] = (15 + s * 27).astype(np.uint8)     # G: 15 -> 42
    img[..., 2] = (28 - s * 8).astype(np.uint8)      # B: 28 -> 20
    return img


# ---------------------------------------------------------------- particles
def simulate(rng, gu, gv):
    """Advect particles and return their trails, frozen after BURN_IN frames."""
    def spawn(idx, aged):
        if idx == 0:                                  # the single accent streamline
            key = "accent"
            x = W * 0.55 + rng.random() * (W * 0.35)
            y = H * 0.1 + rng.random() * (H * 0.5)
            life = 600 + rng.random() * 400
        else:
            r = rng.random()
            key = "cyan" if r < 0.14 else "white" if r < 0.48 else "faint"
            x, y = rng.random() * W, rng.random() * H
            life = 160 + rng.random() * 260
        return {"x": x, "y": y, "trail": [(x, y)], "key": key, "life": life,
                # stagger initial ages so the frozen frame shows a natural mix
                # of fresh and fading streamlines rather than a synchronised flush
                "age": rng.random() * life if aged else 0.0,
                "maxtail": ACCENT_TAIL_LEN if idx == 0 else TAIL_LEN}

    ps = [spawn(i, aged=True) for i in range(NUM)]

    for _ in range(BURN_IN):
        for i, p in enumerate(ps):
            u = float(sample(gu, np.array(p["x"] / W), np.array(p["y"] / H)))
            v = float(sample(gv, np.array(p["x"] / W), np.array(p["y"] / H)))
            p["x"] += u * STEP
            p["y"] += v * STEP
            p["age"] += 1.0                # dt * 0.06 at ~60fps ~= 1 age unit/frame
            p["trail"].append((p["x"], p["y"]))
            if len(p["trail"]) > p["maxtail"]:
                p["trail"].pop(0)
            if (p["x"] < -30 or p["x"] > W + 30 or p["y"] < -30 or p["y"] > H + 30
                    or p["age"] > p["life"]):
                ps[i] = spawn(i, aged=False)
    return ps


def draw(ps, ax):
    """Each trail is a run of segments whose alpha ramps quadratically to the head."""
    segs, cols, widths = [], [], []
    accent = []
    for p in ps:
        tr = p["trail"]
        if len(tr) < MIN_TAIL:
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
            col = (r, g, b, base * frac * frac)
            lw = w * 0.72          # CSS px -> points at the 100-dpi logical scale
            if p["key"] == "accent":
                accent.append((seg, col, lw))
            else:
                segs.append(seg); cols.append(col); widths.append(lw)

    ax.add_collection(LineCollection(segs, colors=cols, linewidths=widths,
                                     capstyle="round", antialiaseds=True))

    # the accent streamline carries a soft glow on the site (shadowBlur); approximate
    # it with a few progressively wider, fainter passes underneath the core stroke
    if accent:
        for mult, fade in ((6.0, 0.05), (3.5, 0.09), (2.0, 0.16)):
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
    ap.add_argument("--out", default=OUT)
    args = ap.parse_args()

    rng = np.random.default_rng(args.seed)
    ssh = compute_ssh(random_eddies(rng))
    gu, gv = derive_velocity(ssh)
    ps = simulate(rng, gu, gv)

    fig = plt.figure(figsize=(W / 100.0, H / 100.0), dpi=100)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, W); ax.set_ylim(H, 0)   # y down, as in canvas coords
    ax.axis("off")
    ax.imshow(background(ssh), extent=(0, W, H, 0), interpolation="bilinear",
              aspect="auto", zorder=0)
    draw(ps, ax)

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    fig.savefig(args.out, dpi=args.dpi, facecolor="#050f1c")
    plt.close(fig)
    print("wrote %s (seed %d, %d px wide)"
          % (args.out, args.seed, int(W / 100.0 * args.dpi)))


if __name__ == "__main__":
    main()
