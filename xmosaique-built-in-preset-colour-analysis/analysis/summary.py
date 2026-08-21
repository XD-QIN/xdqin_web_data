#!/usr/bin/env python3
"""Per-preset summary numbers, so the prose can quote measurements not guesses."""
import json

import numpy as np

from common import (BANDS, IN, M, ORDER, P, grey_axis, is_mono, sdiff, sweep,
                    to_hsl)


def mem_shift(name, key):
    """Hue rotation, saturation delta and luma delta for one memory colour."""
    a = IN["mem_" + key]
    b = M[name]["mem_" + key]
    ha, sa, la = to_hsl(a)
    hb, sb, lb = to_hsl(b)
    lum = lambda c: 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]
    return sdiff(hb, ha), (sb - sa) * 100, (lum(b) - lum(a)) * 255


for n in ORDER:
    p = P[n]
    x, y, w = grey_axis(n)
    hv, hov, sov, _, _ = sweep(n, "vivid")
    hm, hom, som, _, _ = sweep(n, "muted")
    rv = np.mean([abs(sdiff(a, b)) for a, b in zip(hov, hv)])
    rm = np.mean([abs(sdiff(a, b)) for a, b in zip(hom, hm)])
    j = int(np.argmax(abs(w)))
    i10 = int(np.argmin(abs(x - 0.10)))
    i90 = int(np.argmin(abs(x - 0.90)))

    print("\n### %s  [%s]" % (n, p["group"]))
    print("  tone   black(0.10) %+.0f code   white(0.90) %+.0f code   grain %.2f  vign %.0f"
          % ((y[i10] - x[i10]) * 255, (y[i90] - x[i90]) * 255, p["grain"], p["vignette"]))
    print("  warmth peak R-B %+.1f code at input %.2f | black %+.1f | white %+.1f"
          % (w[j] * 255, x[j], w[1] * 255, w[-2] * 255))
    print("  sat    mean %+.1f pts (vivid probes)" % np.mean((sov - 0.65) * 100))
    if not is_mono(n):
        print("  rot    mean|vivid| %.2f  mean|muted| %.2f  ratio %.2f"
              % (rv, rm, rm / max(rv, 1e-9)))
    for k in ("skin_mid", "foliage", "sky_blue", "gold_hour"):
        r, s, l = mem_shift(n, k)
        print("  %-9s rot %+6.1f  dSat %+6.1f  dLum %+6.1f" % (k, r, s, l))
