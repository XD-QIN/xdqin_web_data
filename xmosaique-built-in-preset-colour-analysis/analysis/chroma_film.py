#!/usr/bin/env python3
"""The chromatic questions the first two harnesses did not ask.

Real colour film differs from a digital grade in ways that are specifically
about colour, not tone:

  A. Hue rotation VARIES WITH EXPOSURE. Dye layers have different gammas, so a
     red in the highlights is not rotated the same way as the same red in the
     shadows. A preset built from HSL bands rotates a hue by a fixed amount
     wherever it sits, which is the flat, "stickered" look.
  B. Hues CONVERGE as they approach white. Film's dye density saturates, so
     bright colours lose their identity toward a common point. Digital clips
     channels independently, which does the opposite: it distorts hues TOWARD
     the primaries and secondaries.
  C. Shadows and highlights lean OPPOSITE ways (crossover). Scanned negative
     typically runs cool in the toe and warm in the shoulder.
"""
import colorsys
import json

import numpy as np

D = json.load(open("measured_lightness.json"))
IN, LEV, HUES = D["_input"], D["_levels"], D["_hues"]
ORDER = ["Pierrot le Fou", "Green Ray 1986", "Autumn Sonata", "Hero 2002",
         "Natural", "Cool Slide", "Vivid Daylight", "Green Accent", "Golden",
         "Tungsten"]


def hsl(c):
    h, l, s = colorsys.rgb_to_hls(*[min(1, max(0, x)) for x in c])
    return h * 360, s, l


def sd(a, b):
    return (a - b + 180.0) % 360.0 - 180.0


def rot_at(n, L):
    """Mean signed rotation, and the per-hue vector, at one lightness."""
    v = [sd(hsl(D[n]["L%02d_h%03d" % (round(L * 100), h)])[0], h) for h in HUES]
    return np.array(v)


def circ_spread(n, L):
    """How much of the hue circle the OUTPUT still occupies at this lightness.

    Sum of the gaps between consecutive sorted output hues gives 360 for a
    fully preserved circle; convergence shrinks the occupied arc. Measured as
    the mean absolute deviation of output hue from a perfect 15-degree spacing.
    """
    out = np.array([hsl(D[n]["L%02d_h%03d" % (round(L * 100), h)])[0] for h in HUES])
    gaps = np.diff(np.sort(out % 360))
    return gaps.std()          # even circle -> low; clumped/converged -> high


print("A. Does hue rotation vary with exposure?  (mean signed rotation, degrees)")
print("%-16s %s   %s" % ("preset", "  ".join("L%.2f" % L for L in LEV), "range"))
for n in ORDER:
    r = [rot_at(n, L).mean() for L in LEV]
    print("%-16s %s   %5.1f" % (n, "  ".join("%+5.1f" % v for v in r),
                                max(r) - min(r)))

print("\nB. Do hues converge toward white?  (std-dev of gaps between output hues;")
print("   even circle = low, clumped = high.  Rising = converging.)")
print("%-16s %s   %s" % ("preset", "  ".join("L%.2f" % L for L in LEV), "hi-mid"))
for n in ORDER:
    c = [circ_spread(n, L) for L in LEV]
    print("%-16s %s   %+5.1f" % (n, "  ".join("%5.1f" % v for v in c), c[-1] - c[2]))
