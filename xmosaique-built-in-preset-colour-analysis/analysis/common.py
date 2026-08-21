"""Shared loading + colour helpers for the preset figures."""
import colorsys
import json

import numpy as np

BG = "#FCFCFB"
INK = "#1c1b1a"
MUTED_INK = "#6b6864"

M = json.load(open("measured.json"))
P = {p["name"]: p for p in json.load(open("presets.json"))}
IN = M["_input"]

# Presentation order: the four cinema looks, then the seven stock emulations,
# each group ordered cool -> warm so the figures read left to right.
CINEMA = ["Pierrot le Fou", "Green Ray 1986", "Autumn Sonata", "Hero 2002"]
STOCKS = ["Natural", "Cool Slide", "Vivid Daylight", "Green Accent",
          "Golden", "Tungsten", "Mono Tone"]
ORDER = CINEMA + STOCKS

BANDS = [("Red", 345, 15), ("Orange", 15, 45), ("Yellow", 45, 75),
         ("Green", 75, 150), ("Aqua", 150, 195), ("Blue", 195, 255),
         ("Purple", 255, 285), ("Magenta", 285, 345)]


def to_hsl(rgb):
    h, l, s = colorsys.rgb_to_hls(*[min(1.0, max(0.0, c)) for c in rgb])
    return h * 360.0, s, l


def sdiff(a, b):
    return (a - b + 180.0) % 360.0 - 180.0


def sweep(name, tag="vivid"):
    """Per-hue response: arrays of input hue, output hue, out sat, out lum, out rgb."""
    hs, ho, so, lo, rgb = [], [], [], [], []
    for h in range(0, 360, 5):
        k = "hue_%s_%03d" % (tag, h)
        c = M[name][k]
        oh, os_, ol = to_hsl(c)
        hs.append(h); ho.append(oh); so.append(os_); lo.append(ol)
        rgb.append([min(1, max(0, x)) for x in c])
    return (np.array(hs), np.array(ho), np.array(so), np.array(lo), np.array(rgb))


def grey_axis(name):
    """Neutral ramp -> (input, out luma, R-B). The warm/cool shape of the look."""
    xs, ys, wb = [], [], []
    for i in range(33):
        v = round(i * 255.0 / 32.0)
        k = "grey_%03d" % v
        if k not in M[name]:
            continue
        r, g, b = M[name][k]
        xs.append(v / 255.0)
        ys.append(0.2126 * r + 0.7152 * g + 0.0722 * b)
        wb.append(r - b)
    return np.array(xs), np.array(ys), np.array(wb)


def is_mono(name):
    return P[name]["monochrome"]


def band_of(h):
    for b, lo, hi in BANDS:
        if (lo <= h < hi) if lo < hi else (h >= lo or h < hi):
            return b
    return "Red"
