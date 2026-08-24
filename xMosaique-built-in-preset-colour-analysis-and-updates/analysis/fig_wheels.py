#!/usr/bin/env python3
"""The colour wheel figure: how each preset deforms the hue circle.

Accessibility pass: every wheel carries a one-line plain-language verdict
under its name, the first two wheels carry direct annotations showing how to
read a spoke (outward = more vivid, sideways = renamed), and the legend cell
explains the encoding in ordinary words.
"""
import colorsys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from common import BG, INK, MUTED_INK, ORDER, is_mono, sweep, sdiff

RIN = 0.65          # radius of the input ring == probe saturation
RMAX = 1.02

VERDICT = {
    "Pierrot le Fou": "everything gets more vivid",
    "Green Ray 1986": "the warm side grows",
    "Autumn Sonata": "colours are muted, especially cool ones",
    "Hero 2002": "the strongest boost of all",
    "Natural": "purples and magentas swing toward red",
    "Cool Slide": "gently cooler, reds kept",
    "Vivid Daylight": "more vivid, nothing renamed",
    "Green Accent": "quiet; yellows eased",
    "Golden": "warm colours renamed, not boosted",
    "Tungsten": "yellows and oranges surge",
    "Mono Tone": "all colour removed",
}


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
        d = np.deg2rad(sdiff(ho[i], hs[i]))
        t = np.linspace(0, 1, 24)
        arc = a0 + d * t
        rad = RIN + (so[i] - RIN) * t
        ax.plot(arc, rad, color=rgb[i], lw=1.05, alpha=0.85, zorder=3,
                solid_capstyle="round")
        ax.scatter([a1], [so[i]], c=[rgb[i]], s=13, zorder=4, edgecolors="none")

    if label_bands:
        for lbl, ang in [("red", 0), ("yellow", 60), ("green", 120),
                         ("cyan", 180), ("blue", 240), ("magenta", 300)]:
            ax.text(np.deg2rad(ang), RMAX + 0.16, lbl, ha="center", va="center",
                    fontsize=7.6, color=MUTED_INK)


def main():
    fig, axes = plt.subplots(3, 4, figsize=(15.2, 12.6),
                             subplot_kw={"projection": "polar"})
    fig.patch.set_facecolor(BG)
    axes = axes.ravel()

    for i, name in enumerate(ORDER):
        ax = axes[i]
        draw_wheel(ax, name, label_bands=(i == 0))
        ax.set_title(name, fontsize=12.5, color=INK, pad=26)
        ax.text(0.5, 1.055, VERDICT[name], transform=ax.transAxes, ha="center",
                fontsize=8.6, color=MUTED_INK, style="italic")

    # Direct reading hints on the first two wheels the eye meets.
    ax = axes[0]      # Pierrot: spokes reach outward
    ax.annotate("spokes reach outward\n= colour gets more vivid",
                xy=(np.deg2rad(238), 0.96), xycoords="data",
                xytext=(0.00, -0.06), textcoords="axes fraction",
                ha="left", va="top", fontsize=8.2, color=MUTED_INK,
                arrowprops=dict(arrowstyle="->", color=MUTED_INK, lw=0.9,
                                shrinkA=2, shrinkB=2))
    ax = axes[4]      # Natural: magenta spokes swing sideways
    ax.annotate("spokes swing sideways\n= colour renamed",
                xy=(np.deg2rad(322), 0.80), xycoords="data",
                xytext=(1.00, -0.06), textcoords="axes fraction",
                ha="right", va="top", fontsize=8.2, color=MUTED_INK,
                arrowprops=dict(arrowstyle="->", color=MUTED_INK, lw=0.9,
                                shrinkA=2, shrinkB=2))

    # Twelfth cell: how to read, in plain words.
    ax = axes[11]
    ax.axis("off")
    ax.set_facecolor(BG)
    ax.text(0.5, 0.96, "How to read these wheels", transform=ax.transAxes,
            ha="center", va="top", fontsize=12.5, color=INK)
    ax.text(0.5, 0.84,
            "Around the circle: which colour (hue).\n"
            "Distance from centre: how vivid.\n\n"
            "The faint ring is where 72 test colours\n"
            "started. Each spoke runs to where the\n"
            "preset actually moved that colour,\n"
            "painted in the colour that came out.\n\n"
            "outward = more vivid\n"
            "inward = muted\n"
            "sideways = renamed",
            transform=ax.transAxes, ha="center", va="top", fontsize=9.4,
            color=MUTED_INK, linespacing=1.65)

    fig.subplots_adjust(left=0.02, right=0.98, top=0.935, bottom=0.045,
                        wspace=0.16, hspace=0.38)
    fig.savefig("out_wheels.png", dpi=132, facecolor=BG)
    print("wrote out_wheels.png")


if __name__ == "__main__":
    main()
