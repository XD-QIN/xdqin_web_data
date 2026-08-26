#!/usr/bin/env python3
"""Cover: six of the eleven wheels, chosen to span the range of behaviours."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from common import BG, INK
from fig_wheels import draw_wheel, VERDICT

PICK = ["Hero 2002", "Autumn Sonata", "Tungsten", "Natural",
        "Vivid Daylight", "Mono Tone"]


def main():
    fig, axes = plt.subplots(1, 6, figsize=(18.4, 3.8),
                             subplot_kw={"projection": "polar"})
    fig.patch.set_facecolor(BG)
    for ax, name in zip(axes, PICK):
        draw_wheel(ax, name)
        ax.set_title(name, fontsize=11.4, color=INK, pad=22)
        ax.text(0.5, 1.075, VERDICT[name], transform=ax.transAxes, ha="center",
                fontsize=7.6, color="#6b6864", style="italic")
    fig.subplots_adjust(left=0.008, right=0.992, top=0.83, bottom=0.02,
                        wspace=0.14)
    fig.savefig("out_cover.png", dpi=132, facecolor=BG)
    print("wrote out_cover.png")


if __name__ == "__main__":
    main()
