#!/usr/bin/env python3
"""Grey axis: what each preset does to a neutral ramp.

Left  — tone transfer, measured. The diagonal is identity.
Right — R minus B along that same ramp: the warm/cool *shape* of the look.
        A grade is rarely a uniform cast; where it peaks is the character.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from common import BG, INK, MUTED_INK, CINEMA, STOCKS, ORDER, grey_axis

# One colour per preset, warm-to-cool by eye, stable across every figure.
COLORS = {
    "Pierrot le Fou": "#c0392b", "Green Ray 1986": "#b8860b",
    "Autumn Sonata": "#8e5a2b", "Hero 2002": "#a01d2e",
    "Natural": "#7a8b57", "Cool Slide": "#3d7ea6",
    "Vivid Daylight": "#2f9e6f", "Green Accent": "#5f8c3a",
    "Golden": "#d19226", "Tungsten": "#c2571a", "Mono Tone": "#555250",
}


def main():
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(15.4, 5.6))
    fig.patch.set_facecolor(BG)

    for ax in (a1, a2):
        ax.set_facecolor(BG)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
        for s in ("left", "bottom"):
            ax.spines[s].set_color(MUTED_INK)
            ax.spines[s].set_linewidth(0.7)
        ax.tick_params(colors=MUTED_INK, labelsize=9)

    a1.axhline(0, color=MUTED_INK, lw=0.8, ls=(0, (4, 3)), alpha=0.7, zorder=1)
    for n in ORDER:
        x, y, w = grey_axis(n)
        ls = "-" if n in CINEMA else (0, (5, 2))
        a1.plot(x, (y - x) * 255, color=COLORS[n], lw=1.8, ls=ls, label=n,
                zorder=3, solid_capstyle="round")
        a2.plot(x, w * 255, color=COLORS[n], lw=1.8, ls=ls, zorder=3,
                solid_capstyle="round")

    a1.set_xlabel("input (sRGB, 0–1)", fontsize=10, color=INK)
    a1.set_ylabel("output − input  (8-bit code)", fontsize=10, color=INK)
    a1.set_title("Tone transfer on neutrals, as departure from identity",
                 fontsize=12.5, color=INK, pad=10)
    a1.set_xlim(0, 1)
    a1.text(0.985, 0.955, "lifted", transform=a1.transAxes, ha="right",
            fontsize=9, color=MUTED_INK, style="italic")
    a1.text(0.985, 0.03, "crushed", transform=a1.transAxes, ha="right",
            fontsize=9, color=MUTED_INK, style="italic")

    a2.axhline(0, color=MUTED_INK, lw=0.8, ls=(0, (4, 3)), alpha=0.7, zorder=1)
    a2.set_xlabel("input (sRGB, 0–1)", fontsize=10, color=INK)
    a2.set_ylabel("R − B  (8-bit code)", fontsize=10, color=INK)
    a2.set_title("Warm / cool shape along the same ramp", fontsize=12.5,
                 color=INK, pad=10)
    a2.set_xlim(0, 1)
    a2.text(0.985, 0.955, "warmer", transform=a2.transAxes, ha="right",
            fontsize=9, color=MUTED_INK, style="italic")
    a2.text(0.985, 0.03, "cooler", transform=a2.transAxes, ha="right",
            fontsize=9, color=MUTED_INK, style="italic")

    h, l = a1.get_legend_handles_labels()
    leg = fig.legend(h, l, loc="lower center", ncol=6, frameon=False,
                     fontsize=9.4, bbox_to_anchor=(0.5, -0.015),
                     handlelength=2.4, columnspacing=1.9)
    for t in leg.get_texts():
        t.set_color(INK)

    fig.subplots_adjust(left=0.052, right=0.985, top=0.92, bottom=0.20,
                        wspace=0.19)
    fig.savefig("out_grey.png", dpi=132, facecolor=BG)
    print("wrote out_grey.png")


if __name__ == "__main__":
    main()
