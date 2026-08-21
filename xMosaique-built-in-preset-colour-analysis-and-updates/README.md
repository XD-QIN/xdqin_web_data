# A Colour Analysis of xMosaique's Eleven Built-In Presets

Presets and measurement code for the post **[A Colour Analysis of xMosaique's Eleven
Built-In Presets: Reading a Look Off the Colour
Wheel](https://xdqin.com/blog/photography/xmosaique-built-in-preset-colour-analysis-and-updates)**.

> **Not affiliated with Adobe.** These are independently authored XMP files. *Adobe*,
> *Adobe Lightroom* and *Adobe Camera Raw* are trademarks of Adobe Inc., used here
> only to identify the software these files are meant to be read by. See
> [Disclaimer](#disclaimer) below.

## Contents

### `presets/`: all eleven built-in presets, free to download

These are the eleven looks that ship inside
[xMosaique](https://xmosaique.com), copied verbatim from the app's
`Presets/` folder. Four are cinema looks, six are film-inspired, one is monochrome.

| File | Group | What it does, in one line |
|---|---|---|
| [`Pierrot le Fou.xmp`](presets/Pierrot%20le%20Fou.xmp) | Cinema | Uniform +25 saturation over near-neutral blacks, an amplifier rather than a cast. |
| [`Green Ray 1986.xmp`](presets/Green%20Ray%201986.xmp) | Cinema | Warmth that peaks at mid-grey (+17.2 code R−B) and tapers toward both ends. |
| [`Autumn Sonata.xmp`](presets/Autumn%20Sonata.xmp) | Cinema | The subtractive one: −5 mean saturation, yellows down 15, cool window light. |
| [`Hero 2002.xmp`](presets/Hero%202002.xmp) | Cinema | +35 saturation on five of eight bands, with shadow chroma tapered to zero. |
| [`Natural.xmp`](presets/Natural.xmp) | Film Inspired | Skin left almost exactly alone; the work happens in purple and magenta. |
| [`Cool Slide.xmp`](presets/Cool%20Slide.xmp) | Film Inspired | Cool daylight: −6.4 code R−B at mid, greens pulled down, no clipped whites. |
| [`Vivid Daylight.xmp`](presets/Vivid%20Daylight.xmp) | Film Inspired | Chroma with no cast at all: R−B is 0.0 at every point on the grey ramp. |
| [`Green Accent.xmp`](presets/Green%20Accent.xmp) | Film Inspired | Warmth climbing into the highlights, with green actually raised. |
| [`Golden.xmp`](presets/Golden.xmp) | Film Inspired | Warm mid-tones (+6.4 code) plus hue rotation of +7 to +10° across the warm bands. |
| [`Tungsten.xmp`](presets/Tungsten.xmp) | Film Inspired | Genuinely tungsten-balanced: −16.3 code at mid, cyan shadows, warm lamp glow. |
| [`Mono Tone.xmp`](presets/Mono%20Tone.xmp) | Monochrome | Yellow-filter mixer, 160 code of warm-cool separation, gentle split tone. |

Every claim in that table is a measurement, not a description of intent; the post
shows the figures they come from.

These are plain XMP files using Adobe Camera Raw's `crs:` vocabulary. Each carries a
full set of adjustments: white balance, HSL, colour-grading wheels, split-toning
balance, master plus per-channel RGB point curves, and in two cases a mask group
with a luminance range mask.

To use them, copy the `.xmp` files into your editor's user-presets folder and restart
it. In xMosaique itself they are already installed.

**Note on portability.** The values were designed and measured against my own
rendering engine, and several `crs:` parameters have deliberately different response
curves there than in Lightroom, most notably the shadow/black sliders, which bite
considerably harder. Loading these into Lightroom or Camera Raw gives you something
in the right neighbourhood, but not an identical result.

**Correction to the earlier folder's note.**
[`building-film-look-lightroom-presets/`](../building-film-look-lightroom-presets)
states that `SplitToningBalance` is inverted relative to Lightroom. That held for the
piecewise implementation it was written against; the colour-grading module has since
been reworked and the current engine follows **Adobe's convention**, where positive
balance emphasises the highlight wheel and negative the shadow wheel
(`adjustments/color_grading.rs`, and the `positive_balance_emphasizes_highlight_wheel`
test). Measured through the CLI, a bright pixel's R−B runs +4 → +16 as balance goes
−100 → +100. Use the Adobe direction when adapting these files.

### `analysis/`: the measurement harness

Reproduces every figure in the post.

```bash
pip install numpy matplotlib pillow

# 1. Build the rendering engine (from the app's engine source, which is not public)
cd xmp-preset-engine && cargo build --release --bin xmp-engine-cli

# 2. Point the harness at that binary and at a folder of presets
export XMP_ENGINE_CLI=/path/to/xmp-engine-cli
export XMP_PRESETS=./presets

# 3. Extract the slider values from the XMP files
python3 parse_presets.py "$XMP_PRESETS"       # -> presets.json

# 4. Render the probes through every preset
python3 measure.py "$XMP_PRESETS"             # -> measured.json

# 5. Report and figures
python3 analyze.py                            # per-preset numbers
python3 summary.py                            # the table the post quotes
python3 fig_wheels.py fig_grey.py ...         # one PNG each
python3 fig_hsl_bands.py                      # the HSL band swatch charts
python3 chroma_film.py                        # exposure-dependence and crossover
python3 compare.py                            # before/after against a revision
```

`measured.json` and `presets.json` are committed, so steps 4 and 5 run without
building the engine if you only want to re-plot. `propose2.py` is the script that
generated the revision documented in §10 of the post, with the rationale for each
change in its `SPEC` block.

**How the measurement works, and why it is set up that way.** Every test colour is
rendered as its own *uniform* field and sampled at the exact centre. That detail
matters. Four of the presets carry a negative `PostCropVignetteAmount`, which is
radial, so a conventional patch-grid chart would report a different luminance for the
same colour depending on where in the frame the patch sat. At the centre the vignette
is identity. On a uniform field the spatial adjustments (clarity, texture,
sharpening, halation) have no gradient to act on and are likewise no-ops, and
averaging the centre 8×8 suppresses grain, which is zero-mean. What is left is
exactly the colour transform.

The probe set is 187 colours per preset: 72 hues at S=0.65 and again at S=0.30 (both
at L=0.50), a 33-step neutral ramp, and the eight HSL band centres at three
saturations. Rendering all eleven presets takes about fourteen seconds.

**One caveat worth stating plainly.** This measures the *preview* path. The app's
capture path additionally re-normalises median luma to 0.42 on save
(`CaptureRenderPipeline.swift`), so absolute brightness in a saved photograph will
differ from the numbers here. Curve *shape*, hue and saturation all survive that
re-normalisation, because it is a monotonic remap.

## Disclaimer

These files are **independent work, not affiliated with, endorsed by, sponsored by,
or otherwise connected to Adobe Inc.**

*Adobe*, *Adobe Lightroom*, *Lightroom Classic*, *Adobe Camera Raw* and *Adobe
Photoshop* are trademarks or registered trademarks of Adobe Inc. in the United States
and other countries. They are used here only to identify the software these preset
files are intended to be read by: nominative use, not a claim of association.

The `.xmp` files are plain text I authored myself. They contain adjustment values
written against Adobe's published `crs:` Camera Raw settings namespace; they include
no Adobe software, no Adobe source code, no Adobe profiles or presets, and nothing
else originating from Adobe. Adobe retains all rights in Lightroom, Camera Raw, the
XMP specification and the `crs:` schema. Using these files requires a license for
whichever Adobe product you load them into, which is a matter between you and Adobe.

The presets grouped as **Film Inspired** are original interpretations. They are not
reproductions, emulations or measured characterisations of any manufacturer's film
stock, they are not made or licensed by any film manufacturer, and no manufacturer's
product is named or referenced in the preset files, in this README, or in the post.
Any resemblance to the look of a particular stock is the result of my own choices
about colour, contrast and grain.

The presets are offered free, as-is and without warranty of any kind, under
[CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/).
