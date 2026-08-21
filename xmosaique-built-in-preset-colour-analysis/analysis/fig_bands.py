#!/usr/bin/env python3
"""Per-band response, measured: rotation and saturation change by hue family.

Mono Tone is omitted from the rotation panel — its output is neutral, so output
hue is undefined and any 'rotation' would be an artefact of reading a hue off a
grey pixel.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from common import BANDS, BG, INK, MUTED_INK, ORDER, is_mono, sdiff, sweep


def band_stats(name, tag="vivid"):
    hs, ho, so, lo, _ = sweep(name, tag)
    _, _, so_in, _, _ = sweep(name, tag)  # placeholder, replaced below
    rot, dsat = [], []
    S_IN = 0.65 if tag == "vivid" else 0.30
    for b, lo_, hi in BANDS:
        sel = [i for i, h in enumerate(hs)
               if ((lo_ <= h < hi) if lo_ < hi else (h >= lo_ or h < hi))]
        rot.append(np.mean([sdiff(ho[i], hs[i]) for i in sel]))
        dsat.append(np.mean([so[i] - S_IN for i in sel]) * 100)
    return np.array(rot), np.array(dsat)


def heat(ax, data, rows, title, vlim, cmap, unit):
    im = ax.imshow(data, cmap=cmap, vmin=-vlim, vmax=vlim, aspect="auto")
    ax.set_xticks(range(len(BANDS)))
    ax.set_xticklabels([b for b, _, _ in BANDS], fontsize=9.4, color=INK)
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels(rows, fontsize=9.8, color=INK)
    ax.set_title(title, fontsize=12.5, color=INK, pad=11)
    ax.tick_params(length=0)
    for s in ax.spines.values():
        s.set_visible(False)
    for i in range(data.shape[0]):
        for j in range(data.shape[1]):
            v = data[i, j]
            ax.text(j, i, "%+.0f" % v, ha="center", va="center", fontsize=8.3,
                    color=("#ffffff" if abs(v) > vlim * 0.58 else INK))
    cb = ax.figure.colorbar(im, ax=ax, fraction=0.030, pad=0.015)
    cb.set_label(unit, fontsize=9, color=MUTED_INK)
    cb.ax.tick_params(labelsize=8, colors=MUTED_INK)
    cb.outline.set_visible(False)


def main():
    rot_rows = [n for n in ORDER if not is_mono(n)]
    rot = np.array([band_stats(n)[0] for n in rot_rows])
    sat = np.array([band_stats(n)[1] for n in ORDER])

    fig, (a1, a2) = plt.subplots(1, 2, figsize=(15.6, 5.9))
    fig.patch.set_facecolor(BG)
    for ax in (a1, a2):
        ax.set_facecolor(BG)

    heat(a1, rot, rot_rows, "Hue rotation by band", 14, "PuOr_r", "degrees")
    heat(a2, sat, ORDER, "Saturation change by band", 40, "RdBu_r",
         "saturation points")

    fig.subplots_adjust(left=0.088, right=0.975, top=0.90, bottom=0.06,
                        wspace=0.42)
    fig.savefig("out_bands.png", dpi=132, facecolor=BG)
    print("wrote out_bands.png")


if __name__ == "__main__":
    main()
