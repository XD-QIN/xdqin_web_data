#!/usr/bin/env python3
"""Build "neutral" proxy images from already-graded reference stills.

    python make_proxy.py <stills-dir> <proxy-out-dir> [--decontrast 0.80]

WHY THIS EXISTS
---------------
To test whether a preset reproduces a film's look, you need images resembling
what a *neutral camera* would have captured of those scenes. Nobody has those:
every frame you can get hold of already carries the film's grade. So this script
approximates the missing input by undoing the look:

  1. Convert to (approximately) linear light — an inverse gamma of 2.2.
  2. Apply gray-world white balance: scale each channel so all three have the
     same mean. This is the step that removes the colour cast.
  3. Return to gamma-encoded sRGB.
  4. Pull everything a little toward mid grey, relaxing the source's contrast so
     the preset's own tone curve has room to act.

Render the resulting proxy through your preset and compare against the original
still. If the preset reproduces the look, the two should converge.

READ THIS BEFORE TRUSTING THE OUTPUT
------------------------------------
Gray-world neutralisation of a warm source OVERSHOOTS into cool, and it does so
unevenly — worst in the highlights, where a warm image's bright pixels come out
distinctly blue. Therefore:

  * Directional checks are sound. "Did my grade warm the mid-tones?" "Did it
    rotate greens?" "Did it crush the toe?" — all trustworthy.
  * Absolute equality is NOT. If graded-versus-reference disagrees in the
    highlights, suspect the proxy before you re-tune the preset.

A stronger failure mode: gray-world assumes an average-grey scene. A frame that
is nearly all one vivid hue has no grey to anchor to, so neutralisation drives it
toward the COMPLEMENTARY colour. Magenta silk proxies to olive-green; a red
forest proxies to cyan; a yellow wall proxies to bare white. No preset recovers
the original from those, and the failure belongs to the proxy, not to the preset.
Colour-blocked films trip this on most of their signature frames — do not present
those renders as evidence of a look.

Trust named-surface patches and your own eyes on a side-by-side over any single
aggregate number.

Requires: numpy, pillow.
"""
import argparse
import glob
import os

import numpy as np
from PIL import Image

GAMMA = 2.2


def neutralise(rgb01, decontrast=0.80):
    """Undo a colour grade, approximately. Input and output are sRGB in [0,1]."""
    lin = np.power(rgb01, GAMMA)                          # sRGB -> ~linear
    means = lin.reshape(-1, 3).mean(0)
    lin = lin * (means.mean() / np.maximum(means, 1e-6))  # gray-world balance
    out = np.power(np.clip(lin, 0, 1), 1.0 / GAMMA)       # back to sRGB
    return np.clip(0.5 + (out - 0.5) * decontrast, 0, 1)  # relax contrast


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("stills_dir", help="folder of reference stills (any PIL-readable format)")
    ap.add_argument("out_dir", help="folder to write proxy PNGs into")
    ap.add_argument("--decontrast", type=float, default=0.80,
                    help="pull toward mid grey; 1.0 leaves contrast alone (default 0.80)")
    a = ap.parse_args()

    os.makedirs(a.out_dir, exist_ok=True)
    written = 0
    for path in sorted(glob.glob(os.path.join(a.stills_dir, "*"))):
        try:
            im = Image.open(path).convert("RGB")
        except Exception:
            continue                                       # skip non-images quietly
        x = np.asarray(im, dtype=np.float32) / 255.0
        out = neutralise(x, a.decontrast)
        stem = os.path.splitext(os.path.basename(path))[0]
        Image.fromarray((out * 255).astype(np.uint8)).save(
            os.path.join(a.out_dir, "proxy_%s.png" % stem))
        written += 1

    print("wrote %d proxy images to %s" % (written, a.out_dir))


if __name__ == "__main__":
    main()
