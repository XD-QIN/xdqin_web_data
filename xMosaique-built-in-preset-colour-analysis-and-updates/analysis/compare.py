#!/usr/bin/env python3
"""Measure original vs proposed on every film-realism axis established so far."""
import os
import colorsys, os, subprocess, sys
import numpy as np
from PIL import Image

CLI = os.environ.get("XMP_ENGINE_CLI", "./xmp-engine-cli")
SRC = os.environ.get("XMP_PRESETS", "./presets"); NEW="proposed2"
ORDER=["Pierrot le Fou","Green Ray 1986","Autumn Sonata","Hero 2002","Natural",
       "Cool Slide","Vivid Daylight","Green Accent","Golden","Tungsten","Mono Tone"]
LEV=[0.15,0.30,0.45,0.60,0.75,0.88]; HUES=list(range(0,360,15))

def shoot(p,rgb):
    Image.fromarray(np.tile(np.array(np.round(np.clip(rgb,0,255)),dtype=np.uint8),(48,48,1))).save("ci.png")
    subprocess.run([CLI,"ci.png",p,"co.png"],capture_output=True,check=True)
    o=np.asarray(Image.open("co.png").convert("RGB"),dtype=float)/255.0
    return np.clip(o[20:28,20:28].reshape(-1,3).mean(0),0,1)

def hsl(c):
    h,l,s=colorsys.rgb_to_hls(*c); return h*360,s,l
def sd(a,b): return (a-b+180.0)%360.0-180.0

def dossier(p):
    ramp=[shoot(p,(v,)*3) for v in [round(i*255/32) for i in range(33)]]
    rb=np.array([(c[0]-c[2])*255 for c in ramp])
    lum=np.array([0.2126*c[0]+0.7152*c[1]+0.0722*c[2] for c in ramp])*255
    # chroma-weighted cast hue at each end
    def cast(sl):
        X=[]
        for c in ramp[sl]:
            ch=(max(c)-min(c))*255
            if ch<0.4: continue
            h=colorsys.rgb_to_hls(*c)[0]*2*np.pi
            X.append((ch*np.cos(h),ch*np.sin(h)))
        if not X: return None
        X=np.array(X); return np.degrees(np.arctan2(X[:,1].sum(),X[:,0].sum()))%360
    t,s_=cast(slice(2,10)),cast(slice(24,32))
    swing=None if (t is None or s_ is None) else abs((s_-t+180)%360-180)
    # per-hue rotation band across exposure + saturation vs lightness
    per=[];satL=[]
    for L in LEV:
        row=[]
        for h in HUES:
            c=colorsys.hls_to_rgb(h/360.0,L,0.60)
            o=shoot(p,tuple(x*255 for x in c)); oh,os_,ol=hsl(o)
            row.append((sd(oh,h),os_-0.60))
        per.append([r[0] for r in row]); satL.append(np.mean([r[1] for r in row])*100)
    per=np.array(per)
    band=float(np.mean(per.max(0)-per.min(0)))
    return dict(black=lum[0],white=lum[-1],toeRB=rb[1],midRB=rb[16],shRB=rb[-2],
                swing=swing,band=band,satShadow=satL[0],satHi=satL[-1],
                satMid=satL[2])

print("%-16s %-5s %6s %7s %7s %7s %7s %7s %7s %7s" %
      ("preset","","black","white","toeR-B","midR-B","shR-B","swing","hueBand","satSh"))
for n in ORDER:
    a=dossier(os.path.join(SRC,n+".xmp")); b=dossier(os.path.join(NEW,n+".xmp"))
    for tag,d in (("old",a),("NEW",b)):
        sw="  -  " if d["swing"] is None else "%5.0f"%d["swing"]
        print("%-16s %-5s %6.1f %7.1f %+7.1f %+7.1f %+7.1f %7s %7.1f %+7.1f" %
              (n if tag=="old" else "", tag, d["black"], d["white"], d["toeRB"],
               d["midRB"], d["shRB"], sw, d["band"], d["satShadow"]))
