#!/usr/bin/env python3
"""Mono Tone, explained without jargon.

Left:  which colours become bright greys and which become dark ones, against
       a plain black-and-white conversion. The gap IS the look.
Right: the brightness curve: matte black, held-back white.
"""
import colorsys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from common import BG, INK, MUTED_INK, M, IN, grey_axis

NAME = "Mono Tone"


def main():
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(15.4, 5.9),
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
            label="a plain black & white conversion", zorder=3)
    a1.plot(hues, out * 255, color=INK, lw=2.1, label="Mono Tone", zorder=4)
    a1.fill_between(hues, ref * 255, out * 255, where=(out >= ref),
                    color="#c8a13a", alpha=0.30, zorder=2,
                    label="warm colours pushed brighter")
    a1.fill_between(hues, ref * 255, out * 255, where=(out < ref),
                    color="#3d6ea6", alpha=0.30, zorder=2,
                    label="blues pushed darker")

    # The two ends of the story, pointed at directly.
    iy = int(np.argmax(out)); ib = int(np.argmin(out))
    a1.annotate("yellow becomes the\nbrightest grey (%d)" % round(out[iy]*255),
                xy=(hues[iy] + 3, out[iy]*255), xytext=(122, 200), fontsize=9,
                color=INK, ha="left", va="center",
                arrowprops=dict(arrowstyle="->", color=MUTED_INK, lw=0.9,
                                shrinkB=3))
    a1.annotate("blue becomes the darkest (%d):\nskies gain drama" % round(out[ib]*255),
                xy=(hues[ib], out[ib]*255), xytext=(262, 88), fontsize=9,
                color=INK, va="top",
                arrowprops=dict(arrowstyle="->", color=MUTED_INK, lw=0.9,
                                shrinkB=3))

    # Hue strip under the axis, so the reader can see which colour is which.
    for h in hues:
        a1.axvspan(h, h + 5, ymin=0, ymax=0.030,
                   color=colorsys.hls_to_rgb(h / 360.0, 0.5, 0.65), lw=0)

    a1.set_xlim(0, 355)
    a1.set_xticks([0, 60, 120, 180, 240, 300, 355])
    a1.set_xticklabels(["red", "yellow", "green", "cyan", "blue", "magenta",
                        "red"], fontsize=9, color=MUTED_INK)
    a1.set_xlabel("the colour that went in (strip below shows it)",
                  fontsize=10, color=INK)
    a1.set_ylabel("the grey that came out  (0 = black, 255 = white)",
                  fontsize=10, color=INK)
    a1.set_title("Which colours become bright greys, and which become dark",
                 fontsize=12.5, color=INK, pad=22)
    a1.text(0.5, 1.025, "this is the classic yellow-filter trick from black & white film",
            transform=a1.transAxes, ha="center", fontsize=9, color=MUTED_INK,
            style="italic")
    leg = a1.legend(frameon=False, fontsize=9.0, loc="lower left")
    for t in leg.get_texts():
        t.set_color(INK)

    x, y, _ = grey_axis(NAME)
    a2.plot([0, 255], [0, 255], color=MUTED_INK, lw=0.9, ls=(0, (4, 3)),
            alpha=0.75, zorder=1, label="no change")
    a2.plot(x * 255, y * 255, color=INK, lw=2.1, zorder=3, label="Mono Tone")
    a2.set_xlim(0, 255); a2.set_ylim(0, 255)
    a2.set_xlabel("input tone  (0 = black, 255 = white)", fontsize=10, color=INK)
    a2.set_ylabel("output tone", fontsize=10, color=INK)
    a2.set_title("Brightness: matte black, held-back white",
                 fontsize=12.5, color=INK, pad=22)
    a2.text(0.5, 1.025, "black never reaches the floor; white never burns out",
            transform=a2.transAxes, ha="center", fontsize=9, color=MUTED_INK,
            style="italic")
    a2.annotate("black is lifted to %d,\nnever pure black" % round(y[0] * 255),
                xy=(3, y[0] * 255), xytext=(56, 14), fontsize=9,
                color=INK, va="center",
                arrowprops=dict(arrowstyle="->", color=MUTED_INK, lw=0.9,
                                shrinkA=2, shrinkB=3))
    a2.annotate("white held back to %d,\nlike paper, not glare" % round(y[-1] * 255),
                xy=(250, y[-1] * 255), xytext=(158, 244), fontsize=9,
                color=INK, ha="right", va="center",
                arrowprops=dict(arrowstyle="->", color=MUTED_INK, lw=0.9,
                                shrinkA=2, shrinkB=3))
    leg2 = a2.legend(frameon=False, fontsize=9.0, loc="lower right")
    for t in leg2.get_texts():
        t.set_color(INK)

    fig.subplots_adjust(left=0.055, right=0.985, top=0.875, bottom=0.115,
                        wspace=0.22)
    fig.savefig("out_mono.png", dpi=132, facecolor=BG)
    print("wrote out_mono.png")


if __name__ == "__main__":
    main()
