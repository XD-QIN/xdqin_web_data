#!/usr/bin/env python3
"""Mono Tone: the one preset the colour wheel cannot describe.

Left  — where each hue lands on the grey scale, against what a plain Rec.709
        desaturation of the same colour would have given. The gap is the
        channel mixer doing the work of a coloured filter on the lens.
Right — the measured tone transfer, which is where the 'matte' comes from.
"""
import colorsys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from common import BG, INK, MUTED_INK, M, IN, grey_axis

NAME = "Mono Tone"


def main():
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(15.4, 5.5),
                                 gridspec_kw={"width_ratios": [1.42, 1]})
    fig.patch.set_facecolor(BG)
    for ax in (a1, a2):
        ax.set_facecolor(BG)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
        for s in ("left", "bottom"):
            ax.spines[s].set_color(MUTED_INK); ax.spines[s].set_linewidth(0.7)
        ax.tick_params(colors=MUTED_INK, labelsize=9)

    hues = np.arange(0, 360, 5)
    out, ref = [], []
    for h in hues:
        k = "hue_vivid_%03d" % h
        r, g, b = M[NAME][k]
        out.append(0.2126 * r + 0.7152 * g + 0.0722 * b)
        ri, gi, bi = IN[k]
        ref.append(0.2126 * ri + 0.7152 * gi + 0.0722 * bi)
    out, ref = np.array(out), np.array(ref)

    a1.plot(hues, ref * 255, color=MUTED_INK, lw=1.5, ls=(0, (5, 3)),
            label="plain Rec.709 desaturation", zorder=3)
    a1.plot(hues, out * 255, color=INK, lw=2.1, label="Mono Tone", zorder=4)
    a1.fill_between(hues, ref * 255, out * 255,
                    where=(out >= ref), color="#c8a13a", alpha=0.30,
                    zorder=2, label="lifted (warm side)")
    a1.fill_between(hues, ref * 255, out * 255,
                    where=(out < ref), color="#3d6ea6", alpha=0.30,
                    zorder=2, label="darkened (cool side)")

    # Hue strip under the axis, so the reader can see which colour is which.
    for h in hues:
        a1.axvspan(h, h + 5, ymin=0, ymax=0.030,
                   color=colorsys.hls_to_rgb(h / 360.0, 0.5, 0.65), lw=0)

    a1.set_xlim(0, 355)
    a1.set_xticks([0, 60, 120, 180, 240, 300, 355])
    a1.set_xlabel("input hue (degrees)", fontsize=10, color=INK)
    a1.set_ylabel("output grey (8-bit code)", fontsize=10, color=INK)
    a1.set_title("Where each hue lands on the grey scale",
                 fontsize=12.5, color=INK, pad=10)
    leg = a1.legend(frameon=False, fontsize=9.2, loc="upper right")
    for t in leg.get_texts():
        t.set_color(INK)

    x, y, _ = grey_axis(NAME)
    a2.plot([0, 255], [0, 255], color=MUTED_INK, lw=0.9, ls=(0, (4, 3)),
            alpha=0.75, zorder=1)
    a2.plot(x * 255, y * 255, color=INK, lw=2.1, zorder=3)
    a2.set_xlim(0, 255); a2.set_ylim(0, 255)
    a2.set_xlabel("input (8-bit code)", fontsize=10, color=INK)
    a2.set_ylabel("output (8-bit code)", fontsize=10, color=INK)
    a2.set_title("Tone transfer: a lifted toe and a held shoulder",
                 fontsize=12.5, color=INK, pad=10)
    a2.annotate("black lifted to code %d" % round(y[0] * 255),
                xy=(3, y[0] * 255), xytext=(52, 12), fontsize=9.2,
                color=MUTED_INK, va="center",
                arrowprops=dict(arrowstyle="->", color=MUTED_INK, lw=0.9,
                                shrinkA=2, shrinkB=3))
    a2.annotate("white held to code %d" % round(y[-1] * 255),
                xy=(250, y[-1] * 255), xytext=(150, 246), fontsize=9.2,
                color=MUTED_INK, ha="right", va="center",
                arrowprops=dict(arrowstyle="->", color=MUTED_INK, lw=0.9,
                                shrinkA=2, shrinkB=3))

    fig.subplots_adjust(left=0.055, right=0.985, top=0.90, bottom=0.115,
                        wspace=0.20)
    fig.savefig("out_mono.png", dpi=132, facecolor=BG)
    print("wrote out_mono.png")
    sep = (out.max() - out.min()) * 255
    print("  warm-to-cool separation: %.0f code (max %.0f at %d deg, min %.0f at %d deg)"
          % (sep, out.max()*255, hues[out.argmax()], out.min()*255, hues[out.argmin()]))


if __name__ == "__main__":
    main()
