# A Colour Analysis of xMosaique's Eleven Built-In Presets

Presets and measurement code for the post **[A Colour Analysis of xMosaique's Eleven
Built-In Presets: Reading a Look Off the Colour
Wheel](https://xdqin.com/blog/photography/xmosaique-built-in-preset-colour-analysis)**.

> **Not affiliated with Adobe.** These are independently authored XMP files. *Adobe*,
> *Adobe Lightroom* and *Adobe Camera Raw* are trademarks of Adobe Inc., used here
> only to identify the software these files are meant to be read by. See
> [Disclaimer](#disclaimer) below.

## Contents

### `presets/` — all eleven built-in presets, free to download

These are the eleven looks that ship inside
[xMosaique](https://github.com/XD-QIN/xMosaique_iOS), copied verbatim from the app's
`Presets/` folder. Four are cinema looks; seven are stock emulations.

| File | Group | What it does, in one line |
|---|---|---|
| [`Pierrot le Fou.xmp`](presets/Pierrot%20le%20Fou.xmp) | Cinema | Uniform +26 saturation over lifted, near-neutral blacks — an amplifier, not a cast. |
| [`Green Ray 1986.xmp`](presets/Green%20Ray%201986.xmp) | Cinema | Warmth that peaks at mid-grey (+17.5 code R−B) and tapers toward both ends. |
| [`Autumn Sonata.xmp`](presets/Autumn%20Sonata.xmp) | Cinema | The only preset that darkens overall: −19 code at the toe, greens down 20 code. |
| [`Hero 2002.xmp`](presets/Hero%202002.xmp) | Cinema | +35 saturation on every band equally, deep blacks, heaviest vignette. |
| [`Natural.xmp`](presets/Natural.xmp) | Kodak Portra 400 | Skin left almost exactly alone; the work happens in purple and magenta. |
| [`Cool Slide.xmp`](presets/Cool%20Slide.xmp) | Provia 100F | The only cool preset: −6.4 code R−B at mid, greens pulled down. |
| [`Vivid Daylight.xmp`](presets/Vivid%20Daylight.xmp) | Kodak Ektar 100 | Chroma with no cast at all — R−B is 0.0 at every point on the grey ramp. |
| [`Green Accent.xmp`](presets/Green%20Accent.xmp) | Fuji C200 | Warmth that climbs monotonically into the highlights; yellows pulled down 10. |
| [`Golden.xmp`](presets/Golden.xmp) | Kodak Gold | Hue rotation rather than saturation: everything warm swung +7 to +10°. |
| [`Tungsten.xmp`](presets/Tungsten.xmp) | CineStill 800T | Orange rotated +13° and yellows +32 saturation — the sodium-vapour look. |
| [`Mono Tone.xmp`](presets/Mono%20Tone.xmp) | Monochrome | Neutral black-and-white with a yellow-filter mixer: 160 code of warm-cool separation. |

Every claim in that table is a measurement, not a description of intent; the post
shows the figures they come from.

These are plain XMP files using Adobe Camera Raw's `crs:` vocabulary. Each carries a
full set of adjustments — white balance, HSL, colour-grading wheels, split-toning
balance, and master plus per-channel RGB point curves.

To use them, copy the `.xmp` files into your editor's user-presets folder and restart
it. In xMosaique itself they are already installed.

**Note on portability.** The values were designed and measured against my own
rendering engine, and several `crs:` parameters have deliberately different response
curves there than in Lightroom — most notably the split-toning balance, whose sign is
inverted, and the shadow/black sliders, which bite considerably harder. Loading these
into Lightroom or Camera Raw gives you something in the right neighbourhood, but not
an identical result.

**Relationship to the earlier four.** *Autumn Sonata*, *Green Ray 1986*, *Hero 2002*
and *Pierrot le Fou* also appear in
[`building-film-look-lightroom-presets/`](../building-film-look-lightroom-presets),
the data folder for the post that built them. The files here are the versions that
ship in the app and differ in exactly two attributes —
`PostCropVignetteMidpoint` and `PostCropVignetteFeather`, which change the geometry
of the vignette and nothing about its colour. Every colour measurement in this post
applies unchanged to both copies.

### `analysis/` — the measurement harness

Reproduces every figure in the post.

```bash
pip install numpy matplotlib pillow

# 1. Build the rendering engine (from the xMosaique_iOS checkout)
cd xmp-preset-engine && cargo build --release --bin xmp-engine-cli

# 2. Extract the slider values from the XMP files
python3 parse_presets.py path/to/presets      # -> presets.json

# 3. Render the probes through every preset  (edit CLI at the top of measure.py)
python3 measure.py path/to/presets            # -> measured.json

# 4. Report and figures
python3 analyze.py                            # per-preset numbers
python3 summary.py                            # the table the post quotes
python3 fig_wheels.py fig_grey.py ...         # one PNG each
```

`measured.json` and `presets.json` are committed, so steps 3 and 4 run without
building the engine if you only want to re-plot.

**How the measurement works, and why it is set up that way.** Every test colour is
rendered as its own *uniform* field and sampled at the exact centre. That detail
matters. Four of the presets carry a negative `PostCropVignetteAmount`, which is
radial, so a conventional patch-grid chart would report a different luminance for the
same colour depending on where in the frame the patch sat. At the centre the vignette
is identity. On a uniform field the spatial adjustments — clarity, texture,
sharpening, halation — have no gradient to act on and are likewise no-ops, and
averaging the centre 8×8 suppresses grain, which is zero-mean. What is left is
exactly the colour transform.

The probe set is 187 colours per preset: 72 hues at S=0.65 and again at S=0.30 (both
at L=0.50), a 33-step neutral ramp, and ten memory colours. Rendering all eleven
presets takes about fourteen seconds.

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
files are intended to be read by — nominative use, not a claim of association.

The `.xmp` files are plain text I authored myself. They contain adjustment values
written against Adobe's published `crs:` Camera Raw settings namespace; they include
no Adobe software, no Adobe source code, no Adobe profiles or presets, and nothing
else originating from Adobe. Adobe retains all rights in Lightroom, Camera Raw, the
XMP specification and the `crs:` schema. Using these files requires a license for
whichever Adobe product you load them into, which is a matter between you and Adobe.

The names *Kodak Portra*, *Kodak Gold*, *Kodak Ektar*, *Fujichrome Provia*, *Fuji
C200* and *CineStill 800T* are trademarks of their respective owners — Eastman Kodak
Company, FUJIFILM Corporation and CineStill Film. They appear here only to name the
film each preset was designed to evoke. None of these presets is made, licensed or
endorsed by those companies, and none reproduces any measured characterisation of the
films themselves.

The presets are offered free, as-is and without warranty of any kind, under
[CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/).
