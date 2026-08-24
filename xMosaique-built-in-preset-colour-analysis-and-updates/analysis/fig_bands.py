#!/usr/bin/env python3
"""Per-band response as heatmaps, made readable without prior knowledge.

Accessibility pass: each column carries an actual colour swatch so the family
is visible rather than named only; titles state the takeaway; the cells the
post discusses are outlined.
"""
import colorsys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Rectangle

from common import BANDS, BG, INK, MUTED_INK, ORDER, is_mono, sdiff, sweep

BAND_HUE = {"Red": 0, "Orange": 30, "Yellow": 60, "Green": 120,
            "Aqua": 180, "Blue": 240, "Purple": 270, "Magenta": 300}


def band_stats(name, tag="vivid"):
    hs, ho, so, lo, _ = sweep(name, tag)
    S_IN = 0.65 if tag == "vivid" else 0.30
    rot, dsat = [], []
    for b, lo_, hi in BANDS:
        sel = [i for i, h in enumerate(hs)
               if ((lo_ <= h < hi) if lo_ < hi else (h >= lo_ or h < hi))]
        rot.append(np.mean([sdiff(ho[i], hs[i]) for i in sel]))
        dsat.append(np.mean([so[i] - S_IN for i in sel]) * 100)
    return np.array(rot), np.array(dsat)


def heat(ax, data, rows, title, subtitle, vlim, cmap, unit, outline):
    im = ax.imshow(data, cmap=cmap, vmin=-vlim, vmax=vlim, aspect="auto")
    ax.set_xticks(range(len(BANDS)))
    ax.set_xticklabels([b for b, _, _ in BANDS], fontsize=9.4, color=INK)
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels(rows, fontsize=9.8, color=INK)
    ax.set_title(title, fontsize=12.6, color=INK, pad=30)
    ax.text(0.5, -0.105, subtitle, transform=ax.transAxes, ha="center",
            fontsize=9, color=MUTED_INK, style="italic")
    ax.tick_params(length=0)
    for s in ax.spines.values():
        s.set_visible(False)
    # A real swatch above each column, so the family needs no decoding.
    for j, (b, _, _) in enumerate(BANDS):
        c = colorsys.hls_to_rgb(BAND_HUE[b] / 360.0, 0.5, 0.65)
        ax.add_patch(Rectangle((j - 0.34, -1.22), 0.68, 0.52, color=c, lw=0,
                               clip_on=False))
    for i in range(data.shape[0]):
        for j in range(data.shape[1]):
            v = data[i, j]
            ax.text(j, i, "%+.0f" % v, ha="center", va="center", fontsize=8.3,
                    color=("#ffffff" if abs(v) > vlim * 0.58 else INK))
    for (ri, ci) in outline:
        ax.add_patch(Rectangle((ci - 0.5, ri - 0.5), 1, 1, fill=False,
                               edgecolor=INK, lw=1.6, zorder=5))
    cb = ax.figure.colorbar(im, ax=ax, fraction=0.030, pad=0.015)
    cb.set_label(unit, fontsize=9, color=MUTED_INK)
    cb.ax.tick_params(labelsize=8, colors=MUTED_INK)
    cb.outline.set_visible(False)


def main():
    rot_rows = [n for n in ORDER if not is_mono(n)]
    rot = np.array([band_stats(n)[0] for n in rot_rows])
    sat = np.array([band_stats(n)[1] for n in ORDER])

    fig, (a1, a2) = plt.subplots(1, 2, figsize=(15.6, 6.4))
    fig.patch.set_facecolor(BG)
    for ax in (a1, a2):
        ax.set_facecolor(BG)

    bidx = {b: j for j, (b, _, _) in enumerate(BANDS)}
    rot_marks = [(rot_rows.index("Natural"), bidx["Purple"]),
                 (rot_rows.index("Natural"), bidx["Magenta"]),
                 (rot_rows.index("Tungsten"), bidx["Orange"])]
    sat_marks = [(ORDER.index("Hero 2002"), bidx["Yellow"]),
                 (ORDER.index("Autumn Sonata"), bidx["Yellow"]),
                 (ORDER.index("Mono Tone"), bidx["Blue"])]

    heat(a1, rot, rot_rows,
         "Which colour families get renamed",
         "numbers are degrees around the wheel  ·  outlined = discussed in the text",
         14, "PuOr_r", "degrees of renaming", rot_marks)
    heat(a2, sat, ORDER,
         "Which get more vivid, which get muted",
         "+ = more vivid   ·   − = muted   ·   Mono Tone removes colour entirely",
         40, "RdBu_r", "vividness change (points)", sat_marks)

    fig.subplots_adjust(left=0.088, right=0.975, top=0.86, bottom=0.105,
                        wspace=0.42)
    fig.savefig("out_bands.png", dpi=132, facecolor=BG)
    print("wrote out_bands.png")


if __name__ == "__main__":
    main()
