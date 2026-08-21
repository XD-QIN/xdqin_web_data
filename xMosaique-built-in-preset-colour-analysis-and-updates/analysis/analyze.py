#!/usr/bin/env python3
"""Turn measured.json into the numbers the post is built on."""
import colorsys
import json

import numpy as np

M = json.load(open("measured.json"))
IN = M["_input"]
NAMES = [k for k in M if not k.startswith("_")]

BANDS = [("Red", 345, 15), ("Orange", 15, 45), ("Yellow", 45, 75), ("Green", 75, 150),
         ("Aqua", 150, 195), ("Blue", 195, 255), ("Purple", 255, 285),
         ("Magenta", 285, 345)]


def to_hsl(rgb):
    h, l, s = colorsys.rgb_to_hls(*[min(1, max(0, c)) for c in rgb])
    return h * 360.0, s, l


def sdiff(a, b):
    """Signed smallest angular difference a-b, in (-180,180]."""
    return (a - b + 180.0) % 360.0 - 180.0


def in_band(h, lo, hi):
    return (lo <= h < hi) if lo < hi else (h >= lo or h < hi)


def hue_response(name, tag):
    """[(input_hue, rotation, sat_in, sat_out, lum_in, lum_out)] for one sweep."""
    out = []
    for h in range(0, 360, 5):
        k = "hue_%s_%03d" % (tag, h)
        hi_, si, li = to_hsl(IN[k])
        ho, so, lo_ = to_hsl(M[name][k])
        out.append((h, sdiff(ho, hi_), si, so, li, lo_))
    return out


def band_table(name, tag):
    rows = []
    resp = hue_response(name, tag)
    for b, lo, hi in BANDS:
        sel = [r for r in resp if in_band(r[0], lo, hi)]
        if not sel:
            continue
        rot = float(np.mean([r[1] for r in sel]))
        sat = float(np.mean([r[3] - r[2] for r in sel]))
        lum = float(np.mean([r[5] - r[4] for r in sel]))
        rows.append((b, rot, sat * 100, lum * 100))
    return rows


def grey_axis(name):
    """Neutral ramp: (in, out_luma, R-B) — the warm/cool shape of the look."""
    out = []
    for i in range(33):
        v = round(i * 255.0 / 32.0)
        k = "grey_%03d" % v
        if k not in M[name]:
            continue
        r, g, b = M[name][k]
        out.append((v / 255.0, 0.2126 * r + 0.7152 * g + 0.0722 * b, r - b))
    return out


if __name__ == "__main__":
    for n in NAMES:
        print("\n=== %s ===" % n)
        ga = grey_axis(n)
        arr = np.array(ga)
        # Tone transfer at the classic control points.
        for probe in (0.10, 0.25, 0.50, 0.75, 0.90):
            j = int(np.argmin(abs(arr[:, 0] - probe)))
            print("   in %.2f -> out %.3f   R-B %+.3f" % (arr[j, 0], arr[j, 1], arr[j, 2]))
        print("   black R-B %+.3f   white R-B %+.3f   max|R-B| %.3f"
              % (arr[1, 2], arr[-2, 2], np.max(abs(arr[:, 2]))))
        print("   band (vivid S=0.65):  rot      dSat    dLum")
        for b, rot, ds, dl in band_table(n, "vivid"):
            print("     %-8s %+7.1f  %+7.1f %+7.1f" % (b, rot, ds, dl))
        print("   band (muted S=0.30):  rot      dSat    dLum")
        for b, rot, ds, dl in band_table(n, "muted"):
            print("     %-8s %+7.1f  %+7.1f %+7.1f" % (b, rot, ds, dl))
