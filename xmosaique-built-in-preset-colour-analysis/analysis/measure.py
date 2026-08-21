#!/usr/bin/env python3
"""Measure what each built-in preset actually does, by rendering through the engine.

Method. Every test colour is rendered as its own *uniform* field and sampled at
the exact centre. That matters: four of the presets carry a negative
PostCropVignetteAmount, which is radial, so a patch-grid chart would report a
different luminance for the same colour depending on where it sat in the frame.
At the centre of the frame the vignette is identity. On a uniform field the
spatial adjustments (clarity, texture, sharpening, halation) have no gradient to
act on and are likewise no-ops, and averaging the centre 8x8 suppresses grain,
which is zero-mean. What is left is exactly the colour transform.

Note this is the *preview* path. The capture path additionally re-normalises
median luma to 0.42 (CaptureRenderPipeline.swift), which is not modelled here.
"""
import colorsys
import json
import os
import subprocess
import sys

import numpy as np
from PIL import Image

CLI = "/home/user/xMosaique_iOS/xmp-preset-engine/target/release/xmp-engine-cli"
TILE = 48          # rendered field size
CORE = 8           # centre region averaged

# --- test colours -----------------------------------------------------------
HUE_STEP = 5
VIVID_S, MUTED_S = 0.65, 0.30
MID_L = 0.50

# Memory colours: the surfaces people actually judge a preset on. Values are
# sRGB 0-255 for representative light/mid skin, foliage, sky, and a warm wall.
MEMORY = {
    "skin_light": (233, 190, 166), "skin_mid": (198, 145, 112),
    "skin_deep": (126, 84, 62), "foliage": (94, 122, 60),
    "sky_blue": (110, 155, 200), "sky_pale": (186, 209, 230),
    "wall_warm": (206, 184, 152), "denim": (72, 96, 132),
    "brick": (150, 78, 58), "gold_hour": (222, 168, 104),
}


def test_colors():
    """(key, (r,g,b) 0-255) for every probe, in a stable order."""
    out = []
    for h in range(0, 360, HUE_STEP):
        for tag, s in (("vivid", VIVID_S), ("muted", MUTED_S)):
            r, g, b = colorsys.hls_to_rgb(h / 360.0, MID_L, s)
            out.append(("hue_%s_%03d" % (tag, h), (r * 255, g * 255, b * 255)))
    for i in range(33):                       # neutral ramp, 0..255
        v = i * 255.0 / 32.0
        out.append(("grey_%03d" % round(v), (v, v, v)))
    for k, v in MEMORY.items():
        out.append(("mem_" + k, v))
    return out


def render_batch(preset_path, colors, work):
    """Render every probe through one preset; return {key: (r,g,b) float 0-1}."""
    os.makedirs(work, exist_ok=True)
    res = {}
    for key, rgb in colors:
        src = os.path.join(work, key + "_in.png")
        dst = os.path.join(work, key + "_out.png")
        arr = np.zeros((TILE, TILE, 3), dtype=np.uint8)
        arr[:, :] = np.round(np.clip(rgb, 0, 255)).astype(np.uint8)
        Image.fromarray(arr).save(src)
        r = subprocess.run([CLI, src, preset_path, dst],
                           capture_output=True)
        if r.returncode != 0:
            raise SystemExit("render failed for %s: %s" % (key, r.stderr.decode()[:400]))
        o = np.asarray(Image.open(dst).convert("RGB"), dtype=np.float64) / 255.0
        c = TILE // 2
        h = CORE // 2
        res[key] = o[c - h:c + h, c - h:c + h].reshape(-1, 3).mean(0).tolist()
        os.remove(src)
        os.remove(dst)
    return res


if __name__ == "__main__":
    preset_dir = sys.argv[1]
    colors = test_colors()
    print("probes per preset: %d" % len(colors))
    out = {"_input": {k: [c / 255.0 for c in v] for k, v in colors}}
    import glob
    for p in sorted(glob.glob(os.path.join(preset_dir, "*.xmp"))):
        name = os.path.splitext(os.path.basename(p))[0]
        sys.stdout.write("  rendering %-16s ... " % name)
        sys.stdout.flush()
        out[name] = render_batch(p, colors, "work_" + name.replace(" ", "_"))
        print("ok")
    json.dump(out, open("measured.json", "w"))
    print("wrote measured.json")
