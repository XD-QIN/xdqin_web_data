# Building a Film-Look Preset: The Colour Science, and How to Test It

Presets and code for the post **[Building a Film-Look Preset: The Colour Science,
and How to Test It](https://xdqin.com/blog/photography/building-a-film-look-preset-colour-science)**.

## Contents

### `presets/` — four film-look presets, free to download

| File | Look |
|---|---|
| `Autumn Sonata.xmp` | *Höstsonaten* (1978). Tungsten ochre interiors over dense red-brown blacks, with window light left cool. Deep oxblood reds, muted sage greens, no canary yellow. |
| `Green Ray 1986.xmp` | *Le Rayon vert* (1986). Naturalistic 16 mm summer: warm golden-brown mid-tones that peak and then taper, over near-neutral deep shadows. Olive-khaki yellows, muted forest greens, a teal sea. |
| `Hero 2002.xmp` | *英雄* (2002). Bold saturated wuxia: deep warm-red blacks, blazing crimson and gold, a sapphire counter-story kept vivid, low-key and high-contrast. |
| `Pierrot le Fou.xmp` | *Pierrot le Fou* (1965). Mediterranean daylight: warm low mid-tones cooling into bright, near-neutral highlights, with primary red, yellow and blue kept saturated against uncoloured walls. |

These are plain XMP files using Adobe Camera Raw's `crs:` vocabulary. Each one
carries a full set of adjustments — white balance, HSL, colour grading wheels,
split-toning balance, and master plus per-channel RGB point curves.

**Note on portability.** The values were designed and measured against my own
rendering engine, and several `crs:` parameters have deliberately different
response curves there than in Lightroom — most notably the split-toning balance,
whose sign is inverted, and the shadow/black sliders, which bite considerably
harder. Loading these into Lightroom or Camera Raw will give you something in the
right neighbourhood, but not an identical result. The post explains each of those
differences if you want to adapt the values.

To use them, copy the `.xmp` files into your editor's user-presets folder and
restart it.

### `make_proxy.py` — build neutral proxies from graded stills

The measurement harness in the post needs images resembling what a *neutral
camera* would have captured of the reference scenes. Since every frame you can
obtain already carries the film's grade, this script approximates the missing
input by undoing it: inverse gamma to linear light, gray-world white balance to
strip the cast, back to sRGB, then a mild pull toward mid grey to relax contrast.

```bash
pip install numpy pillow
python make_proxy.py path/to/stills path/to/proxy-out
```

Render those proxies through a preset and compare against the original stills.

The script's docstring documents its two failure modes at length, and they matter:
gray-world neutralisation of a warm source overshoots into cool (worst in the
highlights), and a frame that is nearly all one vivid hue inverts toward its
complementary colour — magenta silk proxies to olive, a red forest to cyan. Use
the output for *direction*, not for absolute equality, and never present the
renders of a colour-blocked frame as evidence of a look.

## Reference frames

The reference stills measured in the post are not redistributed here. They come
from the film pages at [yeguozi.com](https://www.yeguozi.com/) —
[*The Green Ray* (1986)](https://www.yeguozi.com/films/the-green-ray-1986),
[*Hero* (2002)](https://www.yeguozi.com/films/ying-xiong-2002) and
[*Pierrot le Fou* (1965)](https://www.yeguozi.com/films/pierrot-le-fou-1965) —
and remain the property of the films' rights holders.

## License

As with the rest of this repository, the presets and code here are released under
[CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/): share and adapt
for non-commercial purposes with attribution.
