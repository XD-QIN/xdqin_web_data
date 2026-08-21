#!/usr/bin/env python3
"""Revision 2 of the proposal, after peer review.

The review's central finding reframed everything: the six stock presets ARE the
files in the app's sample library  (byte-identical bar name and UUID), and that
library already ships styled variants — a 'lifted blacks' variant,
`a 'cool' variant`. So a "make the base more film-like" edit that lifts the reference look's toe
does not improve the base; it converts it into an existing variant and destroys
the base/variant structure. Two of my headline changes were withdrawn on that
basis alone.

Verified independently before acting: the six base/sample matches, the two
house variants' construction, and that apply_mask_groups (pipeline.rs:531) runs
AFTER grayscale.apply() (:499) — which is what makes the two changes I had
called impossible actually possible.
"""
import os
import os, re

SRC = os.environ.get("XMP_PRESETS", "./presets"); OUT="proposed2"
CURVE={"master":"ToneCurvePV2012","red":"ToneCurvePV2012Red",
       "green":"ToneCurvePV2012Green","blue":"ToneCurvePV2012Blue"}

def mask_group(name, sync, lum_range, **locals_):
    base=dict(LocalExposure=0,LocalHue=0,LocalSaturation=0,LocalContrast=0,
              LocalClarity=0,LocalSharpness=0,LocalBrightness=0,LocalToningHue=0,
              LocalToningSaturation=0,LocalExposure2012=0,LocalContrast2012=0,
              LocalHighlights2012=0,LocalShadows2012=0,LocalWhites2012=0,
              LocalBlacks2012=0,LocalClarity2012=0,LocalDehaze=0,
              LocalLuminanceNoise=0,LocalMoire=0,LocalDefringe=0,
              LocalTemperature=0,LocalTint=0,LocalTexture=0,LocalGrain=0)
    base.update(locals_)
    attrs="\n".join('       crs:%s="%s"'%(k,v) for k,v in base.items())
    return '''     <rdf:li>
      <rdf:Description
       crs:What="Correction"
       crs:CorrectionAmount="1"
       crs:CorrectionActive="true"
       crs:CorrectionName="%s"
       crs:CorrectionSyncID="%s"
%s
       crs:LocalCurveRefineSaturation="100">
      <crs:CorrectionMasks>
       <rdf:Seq>
        <rdf:li>
         <rdf:Description
          crs:What="Mask/RangeMask"
          crs:MaskActive="true"
          crs:MaskName="Luminance Range %s"
          crs:MaskBlendMode="0"
          crs:MaskInverted="false"
          crs:MaskSyncID="%s"
          crs:MaskValue="1">
         <crs:CorrectionRangeMask
          crs:Version="3"
          crs:Type="2"
          crs:Invert="false"
          crs:SampleType="0"
          crs:LumRange="%s"
          crs:LuminanceDepthSampleInfo="0 0.331378 0.207031"/>
         </rdf:Description>
        </rdf:li>
       </rdf:Seq>
      </crs:CorrectionMasks>
      </rdf:Description>
     </rdf:li>
'''%(name,sync,attrs,name,sync[::-1],lum_range)

SPEC={
 "Natural": dict(attrs={},curves={},masks=[],
   why="REVERTED to shipped. This file IS the source library's base file, and the "
       "library already ships a 'lifted blacks' variant as a separate "
       "variant. My lift would have collapsed base into variant. The review "
       "also showed my magenta cut was 74%, not the 'halving' claimed "
       "(+16.7deg -> +4.3deg; a real halving is sliders ~+34), that it moved "
       "the magenta patch by dE 24.9, and that my curve pair produced a "
       "yellow-green shoulder (Lab hue 119deg) - the opposite of the reference look's "
       "warm-neutral skin rendering."),

 "Vivid Daylight": dict(attrs={},curves={},masks=[],
   why="REVERTED to shipped. I had treated the reference look's exposure-invariance as a "
       "defect. It is the stock's defining property - the negative that "
       "behaves like a transparency - and the source library's base file holds a·b "
       "at exactly 0.000 across all 65 grey steps deliberately. My change was "
       "the largest relative shift in the set and blued deep skin shadows "
       "(dE 6.98)."),

 "Golden": dict(
   attrs={"SplitToningHighlightSaturation":"10",
          "ColorGradeMidtoneHue":"40","ColorGradeMidtoneSat":"12"},
   curves={},masks=[],
   why="Diagnosis kept, remedy rebuilt. The shipped blue highlight wheel does "
       "not merely cut the warmth, it REVERSES it (mean b* over codes 64-224: "
       "+1.51 with the wheel off, -0.36 as shipped). But real the look this preset is named for pairs "
       "warm mids with cool-cyan skies, so flipping that wheel warm was wrong: "
       "it made the frame monolithically warm and pushed neutral b* to +5.3 "
       "against reference Gold's +1.3. Instead: keep the wheel's hue (cool sky "
       "separation) and drop its saturation 30 -> 10, then put the warmth where "
       "the name means it, in the mid-tone wheel. No toe lift."),

 "Green Accent": dict(
   attrs={"SaturationAdjustmentGreen":"-6","SaturationAdjustmentYellow":"-10",
          "SplitToningShadowHue":"135"},
   curves={},masks=[],
   why="Same intent, correct arithmetic. My rationale quoted the MEASURED band "
       "output (-2) as if it were the slider, which is -18, so my '+12' was "
       "really a +28 move. Green goes -18 -> -6 (the +12 actually intended) "
       "and yellow -16 -> -10. Shadow hue 107 -> 135 keeps the reference look's green-leaning "
       "toe rather than replacing it with the blue-violet one my curve pair "
       "produced. Curve pair dropped entirely."),

 "Cool Slide": dict(
   attrs={},
   curves={"master":[(0,0),(199,201),(249,246),(255,250)]},masks=[],
   why="Narrowed to the one real fault. The shipped preset drives 31 of 360 "
       "channels to 255; the new white point removes all of them. Everything "
       "else is withdrawn: the (0,4) toe lift contradicted my own 'transparency "
       "keeps its blacks' rule, SaturationAdjustmentBlue was already -4 (a "
       "no-op), and the chroma trim rested on an artefact - HSL S rises toward "
       "white by construction, while Lab C* was already falling monotonically."),

 "Tungsten": dict(
   attrs={"IncrementalTemperature":"-14","SplitToningShadowHue":"205",
          "SplitToningShadowSaturation":"30","SaturationAdjustmentRed":"+31",
          "LuminanceAdjustmentRed":"-3","LuminanceAdjustmentOrange":"-3"},
   curves={},masks=[],
   why="Cold, but not at the cost of faces. My -20 with no compensation cost "
       "every skin patch 8-9 units of C*ab (mean skin dE 8.39) - ill and grey "
       "rather than cool - and quadrupled highlight hue distortion. The house's "
       "own a 'cool' variant solves this: -14 PLUS SaturationAdjustmentRed +31 and "
       "red/orange luminance to -3, which is exactly the compensation that "
       "keeps skin alive, with the shadow split moved to 205 for the cyan-teal "
       "a tungsten-balanced stock signature. Adopted wholesale. NOTE: this makes the base preset "
       "close to a variant the library already ships."),

 "Autumn Sonata": dict(
   attrs={"Blacks2012":"-3","ColorGradeHighlightSat":"40"},curves={},masks=[],
   why="Right target, wrong lever. My extra curve knot made the crush HARDER "
       "(max toe slope 1.88 -> 1.87, codes 24-48 darker). The wall is "
       "Blacks2012=-7, which runs in linear space BEFORE the tone curve, so no "
       "point-curve knot can undo it; -3 takes max slope to 1.43. And the blue "
       "highlight wheel at 18 bought only 0.86 b* - the window light needs ~40-50."),

 "Hero 2002": dict(attrs={},curves={},
   masks=[mask_group("Shadow chroma","A1B2C3D4E5F6470899AABBCCDDEEFF01",
                     "0.000000 0.000000 0.100000 0.400000",LocalSaturation=-40)],
   why="No longer 'unachievable'. I had concluded that tapering shadow chroma "
       "needed PointColors because HSL is lightness-blind. But mask groups "
       "carry LocalSaturation under a luminance range mask and run at "
       "pipeline.rs:531, after everything else. One group takes shadow "
       "saturation from +29.5 to about -0.6 at L=0.15 with nothing above "
       "L=0.60 touched."),

 "Mono Tone": dict(attrs={},curves={},
   masks=[mask_group("Cool shadows","B1C2D3E4F5A6470899AABBCCDDEEFF02",
                     "0.000000 0.000000 0.320000 0.620000",
                     LocalTemperature=-12,LocalTint=-3),
          mask_group("Warm highlights","C1D2E3F4A5B6470899AABBCCDDEEFF03",
                     "0.380000 0.680000 1.000000 1.000000",
                     LocalTemperature=8)],
   why="No longer 'engine change required'. I had verified that split toning "
       "dies because grayscale runs after colour grading - true - and stopped "
       "there. But apply_mask_groups runs after grayscale, and mask groups "
       "carry LocalTemperature/LocalTint. Two luminance-range groups give a "
       "silver/selenium split with a crossover near middle grey, in the "
       "viewfinder as well as the save."),

 "Pierrot le Fou": dict(attrs={},curves={},masks=[],why="Unchanged. No measured fault."),
 "Green Ray 1986": dict(attrs={},curves={},masks=[],why="Unchanged. No measured fault."),
}

def set_curve(t,tag,pts):
    body="".join("     <rdf:li>%d, %d</rdf:li>\n"%p for p in pts)
    pat=r"(<crs:%s>\s*<rdf:Seq>).*?(</rdf:Seq>)"%tag
    return re.sub(pat,lambda m:m.group(1)+"\n"+body+"    "+m.group(2),t,flags=re.S) \
           if re.search(pat,t,re.S) else t

os.makedirs(OUT,exist_ok=True)
for name,spec in SPEC.items():
    t=open(os.path.join(SRC,name+".xmp"),encoding="utf-8").read()
    for k,v in spec["attrs"].items():
        if re.search(r'crs:%s="[^"]*"'%k,t):
            t=re.sub(r'crs:%s="[^"]*"'%k,'crs:%s="%s"'%(k,v),t)
        else:
            t=t.replace('crs:HasSettings="True"',
                        'crs:%s="%s"\n   crs:HasSettings="True"'%(k,v))
    for ch,pts in spec["curves"].items():
        t=set_curve(t,CURVE[ch],pts)
    if spec["masks"]:
        blocks="".join(spec["masks"])
        if "<crs:MaskGroupBasedCorrections>" in t:      # append to existing Seq
            t=re.sub(r"(<crs:MaskGroupBasedCorrections>\s*<rdf:Seq>)",
                     lambda m:m.group(1)+"\n"+blocks, t, flags=re.S)
        else:                                            # create the block
            t=t.replace("  </rdf:Description>\n </rdf:RDF>",
                "   <crs:MaskGroupBasedCorrections>\n    <rdf:Seq>\n"+blocks+
                "    </rdf:Seq>\n   </crs:MaskGroupBasedCorrections>\n"
                "  </rdf:Description>\n </rdf:RDF>")
    open(os.path.join(OUT,name+".xmp"),"w").write(t)
print("wrote %d presets to %s/"%(len(SPEC),OUT))
