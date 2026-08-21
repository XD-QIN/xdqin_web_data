#!/usr/bin/env python3
"""The colour wheel figure: how each preset deforms the hue circle.

Each panel is a polar plot of the measured response. Angle is hue, radius is
saturation. The faint ring is where the 72 input probes started (S=0.65, L=0.50);
each spoke runs from that starting point to where the preset actually put that
colour, and the dot at the end is painted in the rendered output RGB. A spoke
that swings anticlockwise is a hue rotated toward yellow-green; one that reaches
further out is a colour the preset saturated.
"""
import colorsys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D

from common import BG, INK, MUTED_INK, ORDER, is_mono, sweep, sdiff

RIN = 0.65          # radius of the input ring == probe saturation
RMAX = 1.02


def draw_wheel(ax, name, tag="vivid", label_bands=False):
    hs, ho, so, lo, rgb = sweep(name, tag)

    ax.set_theta_zero_location("E")
    ax.set_theta_direction(1)
    ax.set_ylim(0, RMAX)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.spines["polar"].set_visible(False)
    ax.set_facecolor(BG)

    # Reference ring: true input hues at their untouched positions.
    th = np.deg2rad(np.arange(0, 360, 2))
    ring = [colorsys.hls_to_rgb(t / 360.0, 0.5, 0.65) for t in np.arange(0, 360, 2)]
    ax.scatter(th, np.full_like(th, RIN), c=ring, s=7, zorder=2, alpha=0.35,
               edgecolors="none")
    ax.plot(np.linspace(0, 2 * np.pi, 400), np.full(400, RIN), color=MUTED_INK,
            lw=0.5, alpha=0.30, zorder=1)

    # The deformation: input position -> measured output position.
    for i in range(len(hs)):
        a0, a1 = np.deg2rad(hs[i]), np.deg2rad(ho[i])
        # Interpolate along the shorter arc so the spoke shows the rotation.
        d = np.deg2rad(sdiff(ho[i], hs[i]))
        t = np.linspace(0, 1, 24)
        arc = a0 + d * t
        rad = RIN + (so[i] - RIN) * t
        ax.plot(arc, rad, color=rgb[i], lw=1.05, alpha=0.85, zorder=3,
                solid_capstyle="round")
        ax.scatter([a1], [so[i]], c=[rgb[i]], s=13, zorder=4, edgecolors="none")

    if label_bands:
        for lbl, ang in [("R", 0), ("Y", 60), ("G", 120), ("C", 180),
                         ("B", 240), ("M", 300)]:
            ax.text(np.deg2rad(ang), RMAX + 0.13, lbl, ha="center", va="center",
                    fontsize=8.5, color=MUTED_INK)


def main():
    n = len(ORDER)
    cols, rows = 4, 3
    fig, axes = plt.subplots(rows, cols, figsize=(15.2, 11.8),
                             subplot_kw={"projection": "polar"})
    fig.patch.set_facecolor(BG)
    axes = axes.ravel()

    for i, name in enumerate(ORDER):
        ax = axes[i]
        draw_wheel(ax, name, label_bands=(i == 0))
        sub = "monochrome — the wheel collapses" if is_mono(name) else ""
        ax.set_title(name, fontsize=12.5, color=INK, pad=14)
        if sub:
            ax.text(0.5, -0.055, sub, transform=ax.transAxes, ha="center",
                    fontsize=8.4, color=MUTED_INK, style="italic")

    # Twelfth cell: how to read the figure.
    ax = axes[11]
    ax.axis("off")
    ax.set_facecolor(BG)
    ax.text(0.5, 0.97, "How to read these", transform=ax.transAxes,
            ha="center", va="top", fontsize=12.5, color=INK)
    ax.text(0.5, 0.855,
            "Angle is hue, radius is saturation.\n\n"
            "The faint ring is where the 72 probe colours\n"
            "started: S = 0.65, L = 0.50. Each spoke runs\n"
            "to where the preset actually put that colour,\n"
            "painted in the rendered output.\n\n"
            "Anticlockwise swing → hue pushed toward\n"
            "yellow-green. Outward → saturated.\n"
            "Inward → desaturated.",
            transform=ax.transAxes, ha="center", va="top", fontsize=9.4,
            color=MUTED_INK, linespacing=1.6)

    fig.subplots_adjust(left=0.02, right=0.98, top=0.945, bottom=0.035,
                        wspace=0.16, hspace=0.26)
    fig.savefig("out_wheels.png", dpi=132, facecolor=BG)
    print("wrote out_wheels.png")


if __name__ == "__main__":
    main()
