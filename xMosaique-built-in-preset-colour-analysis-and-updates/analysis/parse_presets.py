#!/usr/bin/env python3
"""Extract every crs: parameter from the built-in xMosaique presets.

Emits presets.json: one record per preset with white balance, the eight HSL
bands, the colour-grading wheels, split toning, tone curves and point colours.
Values are taken verbatim from the XMP; interpretation happens downstream.
"""
import glob
import json
import os
import re
import sys

# Adobe's HSL band order, which is also the order the engine stores them in.
BANDS = ["Red", "Orange", "Yellow", "Green", "Aqua", "Blue", "Purple", "Magenta"]

ATTR = re.compile(r'crs:([A-Za-z0-9_]+)="([^"]*)"')


def parse(path):
    src = open(path, encoding="utf-8").read()
    attrs = dict(ATTR.findall(src))

    def num(key, default=0.0):
        v = attrs.get(key)
        if v is None:
            return default
        try:
            return float(v)
        except ValueError:
            return default

    def seq(tag):
        """Pull an rdf:Seq of 'x, y' points for a named tone curve tag."""
        m = re.search(r"<crs:%s>\s*<rdf:Seq>(.*?)</rdf:Seq>" % tag, src, re.S)
        if not m:
            return []
        return [tuple(float(x) for x in li.split(","))
                for li in re.findall(r"<rdf:li>([^<]*)</rdf:li>", m.group(1))]

    name = re.search(r"<crs:Name>\s*<rdf:Alt>\s*<rdf:li[^>]*>([^<]*)<", src, re.S)
    group = re.search(r"<crs:Group>\s*<rdf:Alt>\s*<rdf:li[^>]*>([^<]*)<", src, re.S)

    # Point colours: 19 floats each. The first four are hue, sat, lum, and the
    # amount of the correction; the rest describe the range mask.
    pc = re.search(r"<crs:PointColors>\s*<rdf:Seq>(.*?)</rdf:Seq>", src, re.S)
    point_colors = []
    if pc:
        for li in re.findall(r"<rdf:li>([^<]*)</rdf:li>", pc.group(1)):
            vals = [float(x) for x in li.split(",")]
            if len(vals) >= 5:
                point_colors.append(vals)

    # Grain rides in a mask-based local correction, not the global GrainAmount.
    lg = re.search(r'crs:LocalGrain="([-\d.]+)"', src)

    return {
        "file": os.path.basename(path),
        "name": (name.group(1).strip() if name else os.path.basename(path)),
        "group": (group.group(1).strip() if group else ""),
        "monochrome": attrs.get("ConvertToGrayscale", "False") == "True",
        "wb": {
            "temperature": num("IncrementalTemperature"),
            "tint": num("IncrementalTint"),
            "mode": attrs.get("WhiteBalance", ""),
        },
        "basic": {k: num(k) for k in [
            "Exposure2012", "Contrast2012", "Highlights2012", "Shadows2012",
            "Whites2012", "Blacks2012", "Texture", "Clarity2012", "Dehaze",
            "Vibrance", "Saturation"]},
        "hsl": {
            "hue": {b: num("HueAdjustment" + b) for b in BANDS},
            "sat": {b: num("SaturationAdjustment" + b) for b in BANDS},
            "lum": {b: num("LuminanceAdjustment" + b) for b in BANDS},
        },
        "gray_mixer": {b: num("GrayMixer" + b) for b in BANDS},
        "split": {
            "shadow_hue": num("SplitToningShadowHue"),
            "shadow_sat": num("SplitToningShadowSaturation"),
            "highlight_hue": num("SplitToningHighlightHue"),
            "highlight_sat": num("SplitToningHighlightSaturation"),
            "balance": num("SplitToningBalance"),
        },
        "grade": {
            "shadow": (num("ColorGradeShadowHue"), num("ColorGradeShadowSat"),
                       num("ColorGradeShadowLum")),
            "midtone": (num("ColorGradeMidtoneHue"), num("ColorGradeMidtoneSat"),
                        num("ColorGradeMidtoneLum")),
            "highlight": (num("ColorGradeHighlightHue"), num("ColorGradeHighlightSat"),
                          num("ColorGradeHighlightLum")),
            "global": (num("ColorGradeGlobalHue"), num("ColorGradeGlobalSat"),
                       num("ColorGradeGlobalLum")),
            "blending": num("ColorGradeBlending", 50.0),
        },
        "calibration": {
            "shadow_tint": num("ShadowTint"),
            "red_hue": num("RedHue"), "red_sat": num("RedSaturation"),
            "green_hue": num("GreenHue"), "green_sat": num("GreenSaturation"),
            "blue_hue": num("BlueHue"), "blue_sat": num("BlueSaturation"),
        },
        "curves": {
            "master": seq("ToneCurvePV2012"),
            "red": seq("ToneCurvePV2012Red"),
            "green": seq("ToneCurvePV2012Green"),
            "blue": seq("ToneCurvePV2012Blue"),
        },
        "point_colors": point_colors,
        "grain": float(lg.group(1)) if lg else 0.0,
        "vignette": num("PostCropVignetteAmount"),
    }


if __name__ == "__main__":
    d = sys.argv[1] if len(sys.argv) > 1 else "."
    out = [parse(p) for p in sorted(glob.glob(os.path.join(d, "*.xmp")))]
    json.dump(out, open("presets.json", "w"), indent=1)
    print("parsed %d presets -> presets.json" % len(out))
    for p in out:
        hm = sum(p["hsl"]["lum"].values()) / 8.0
        print("  %-16s mono=%-5s temp=%+5.0f tint=%+4.0f  HSLlumMean=%+6.2f  grain=%.2f  group=%s"
              % (p["name"], p["monochrome"], p["wb"]["temperature"], p["wb"]["tint"],
                 hm, p["grain"], p["group"]))
