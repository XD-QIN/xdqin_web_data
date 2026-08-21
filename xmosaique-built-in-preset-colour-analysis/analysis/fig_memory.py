#!/usr/bin/env python3
"""Memory colours: the surfaces people actually judge a preset on.

Ten reference surfaces rendered through every preset. The top row is the
untouched input. Skin is the unforgiving one — the eye has a hard prior for it,
and a look that is merely 'warm' on a grey ramp can still turn skin orange.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Rectangle

from common import BG, INK, MUTED_INK, ORDER, M, IN

KEYS = ["skin_light", "skin_mid", "skin_deep", "wall_warm", "gold_hour",
        "brick", "foliage", "sky_pale", "sky_blue", "denim"]
LABELS = ["skin\nlight", "skin\nmid", "skin\ndeep", "warm\nwall", "golden\nhour",
          "brick", "foliage", "pale\nsky", "blue\nsky", "denim"]


def main():
    rows = ["_input"] + ORDER
    nR, nC = len(rows), len(KEYS)
    fig, ax = plt.subplots(figsize=(12.6, 8.4))
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)

    for i, r in enumerate(rows):
        src = IN if r == "_input" else M[r]
        for j, k in enumerate(KEYS):
            c = np.clip(src["mem_" + k], 0, 1)
            ax.add_patch(Rectangle((j, nR - 1 - i), 0.93, 0.90, color=c,
                                   lw=0))
        label = "input (untouched)" if r == "_input" else r
        ax.text(-0.22, nR - 1 - i + 0.45, label, ha="right", va="center",
                fontsize=10.2, color=(MUTED_INK if r == "_input" else INK),
                style=("italic" if r == "_input" else "normal"))

    for j, l in enumerate(LABELS):
        ax.text(j + 0.465, nR + 0.10, l, ha="center", va="bottom",
                fontsize=9.2, color=MUTED_INK, linespacing=1.35)

    # Separate the untouched row from the graded ones.
    ax.plot([-0.06, nC - 0.02], [nR - 1.06, nR - 1.06], color=MUTED_INK,
            lw=0.8, alpha=0.55)

    ax.set_xlim(-3.05, nC + 0.05)
    ax.set_ylim(-0.15, nR + 0.72)
    ax.axis("off")
    fig.subplots_adjust(left=0.005, right=0.995, top=0.985, bottom=0.008)
    fig.savefig("out_memory.png", dpi=132, facecolor=BG)
    print("wrote out_memory.png")


if __name__ == "__main__":
    main()
