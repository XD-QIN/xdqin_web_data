#!/usr/bin/env python3
"""Grey axis: what each preset does to plain grey, in plain language.

Accessibility pass: the presets the post narrates are drawn heavy and labelled
directly on the chart; the rest stay as faint context. The warmth panel is
tinted so "+ means warm, - means cool" is visible without reading an axis.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D

from common import BG, INK, MUTED_INK, CINEMA, ORDER, grey_axis

COLORS = {
    "Pierrot le Fou": "#c0392b", "Green Ray 1986": "#b8860b",
    "Autumn Sonata": "#8e5a2b", "Hero 2002": "#a01d2e",
    "Natural": "#7a8b57", "Cool Slide": "#3d7ea6",
    "Vivid Daylight": "#2f9e6f", "Green Accent": "#5f8c3a",
    "Golden": "#d19226", "Tungsten": "#c2571a", "Mono Tone": "#555250",
}
HERO = ["Green Ray 1986", "Tungsten", "Cool Slide", "Vivid Daylight",
        "Mono Tone", "Autumn Sonata"]


def main():
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(15.4, 6.2))
    fig.patch.set_facecolor(BG)

    for ax in (a1, a2):
        ax.set_facecolor(BG)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
        for s in ("left", "bottom"):
            ax.spines[s].set_color(MUTED_INK)
            ax.spines[s].set_linewidth(0.7)
        ax.tick_params(colors=MUTED_INK, labelsize=9)
        ax.axhline(0, color=MUTED_INK, lw=0.8, ls=(0, (4, 3)), alpha=0.7,
                   zorder=1)
        ax.set_xlim(0, 1)

    # Warmth panel: tint the halves so the sign needs no decoding.
    a2.axhspan(0, 22, color="#c2571a", alpha=0.045, zorder=0)
    a2.axhspan(-22, 0, color="#3d7ea6", alpha=0.045, zorder=0)
    a2.set_ylim(-20, 20)

    for n in ORDER:
        x, y, w = grey_axis(n)
        ls = "-" if n in CINEMA else (0, (5, 2))
        hot = n in HERO
        kw = dict(color=COLORS[n], ls=ls, solid_capstyle="round",
                  lw=(2.3 if hot else 1.0), alpha=(1.0 if hot else 0.38),
                  zorder=(4 if hot else 2))
        a1.plot(x, (y - x) * 255, label=n, **kw)
        a2.plot(x, w * 255, **kw)

    a1.set_title("Brightness: what each preset does to every tone",
                 fontsize=12.6, color=INK, pad=20)
    a1.text(0.5, 1.023, "0 = unchanged   ·   above = brighter   ·   below = darker",
            transform=a1.transAxes, ha="center", fontsize=9, color=MUTED_INK,
            style="italic")
    a1.set_xlabel("input tone  (0 = black, 1 = white)", fontsize=10, color=INK)
    a1.set_ylabel("change in brightness  (levels)", fontsize=10, color=INK)

    a2.set_title("Warmth: does it make greys warm or cool?",
                 fontsize=12.6, color=INK, pad=20)
    a2.text(0.5, 1.023, "orange zone = warmer than before   ·   blue zone = cooler",
            transform=a2.transAxes, ha="center", fontsize=9, color=MUTED_INK,
            style="italic")
    a2.set_xlabel("input tone  (0 = black, 1 = white)", fontsize=10, color=INK)
    a2.set_ylabel("warmth score R−B  (levels)", fontsize=10, color=INK)

    a1.set_ylim(-21, 9)

    # Direct labels where each narrated line is most itself.
    lbl = dict(fontsize=8.8, color=INK)
    a2.text(0.535, 18.3, "Green Ray: warm hump\npeaks at mid-grey",
            ha="center", va="bottom", **lbl)
    a2.text(0.47, -18.6, "Tungsten: coldest in the set", ha="center",
            va="top", **lbl)
    a2.text(0.665, -4.1, "Cool Slide", ha="left", va="bottom", **lbl)
    a2.text(0.79, 1.2, "Vivid Daylight: exactly 0", ha="center",
            va="bottom", **lbl)
    a2.text(0.965, 9.6, "Mono Tone:\ncool shadows,\nwarm highlights",
            ha="right", va="bottom", **lbl)

    xa, ya, _ = grey_axis("Autumn Sonata")
    da = (ya - xa) * 255
    j = int(np.argmin(np.where(xa < 0.2, da, 99)))
    a1.annotate("Autumn Sonata darkens\nthe deep shadows",
                xy=(xa[j], da[j]), xytext=(0.135, -18.5), fontsize=8.8,
                color=INK, va="center",
                arrowprops=dict(arrowstyle="->", color=MUTED_INK, lw=0.9,
                                shrinkB=3))
    a1.annotate("Tungsten and Mono Tone keep black\noff the floor (the matte film toe)",
                xy=(0.012, 7.6), xytext=(0.24, 6.4), fontsize=8.8, color=INK,
                va="center",
                arrowprops=dict(arrowstyle="->", color=MUTED_INK, lw=0.9,
                                shrinkB=3))

    handles = [Line2D([], [], color=COLORS[n],
                      ls=("-" if n in CINEMA else (0, (5, 2))),
                      lw=(2.3 if n in HERO else 1.2), label=n) for n in ORDER]
    leg = fig.legend(handles=handles, loc="lower center", ncol=6, frameon=False,
                     fontsize=9.2, bbox_to_anchor=(0.5, -0.018),
                     handlelength=2.3, columnspacing=1.7)
    for t in leg.get_texts():
        t.set_color(INK)

    fig.subplots_adjust(left=0.052, right=0.985, top=0.885, bottom=0.20,
                        wspace=0.21)
    fig.savefig("out_grey.png", dpi=132, facecolor=BG)
    print("wrote out_grey.png")


if __name__ == "__main__":
    main()
