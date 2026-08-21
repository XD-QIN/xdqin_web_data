#!/usr/bin/env python3
"""The eight HSL bands rendered through each preset.

Systematic probes, not invented surfaces: each row is an Adobe HSL band centre
at L=0.50, rendered at three saturations, with the resulting sRGB hex printed
under every swatch so the numbers can be checked by hand.
"""
import colorsys, os, subprocess, sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Rectangle
from PIL import Image

from common import BG, INK, MUTED_INK

CLI="/home/user/xMosaique_iOS/xmp-preset-engine/target/release/xmp-engine-cli"
BANDS=[("Red",0),("Orange",30),("Yellow",60),("Green",120),
       ("Aqua",180),("Blue",240),("Purple",270),("Magenta",300)]
SATS=[0.85,0.45,0.20]
ABBR={"Pierrot le Fou":"PLF","Green Ray 1986":"GR","Autumn Sonata":"AS",
      "Hero 2002":"H2","Natural":"NAT","Cool Slide":"CS","Vivid Daylight":"VD",
      "Green Accent":"GA","Golden":"GLD","Tungsten":"TUN","Mono Tone":"MT"}
_cache={}

def shoot(preset,rgb):
    k=(preset,rgb)
    if k in _cache: return _cache[k]
    Image.fromarray(np.tile(np.array(np.round(np.clip(rgb,0,255)),dtype=np.uint8),
                            (48,48,1))).save("hb_i.png")
    subprocess.run([CLI,"hb_i.png",preset,"hb_o.png"],capture_output=True,check=True)
    o=np.asarray(Image.open("hb_o.png").convert("RGB"),dtype=float)/255.0
    v=np.clip(o[20:28,20:28].reshape(-1,3).mean(0),0,1)
    _cache[k]=v; return v

def hexs(c): return "#%02X%02X%02X"%tuple(int(round(x*255)) for x in c)

def chart(cols, out, title, width, note=""):
    """cols = [(header, preset_path_or_None)] ; None means unmodified input."""
    nR=len(BANDS); nC=len(cols); gap=0.55
    fig_w=width; fig_h=1.05+0.62*nR
    fig,ax=plt.subplots(figsize=(fig_w,fig_h))
    fig.patch.set_facecolor(BG); ax.set_facecolor(BG)
    total=len(SATS)*nC+(len(SATS)-1)*gap
    for gi,S in enumerate(SATS):
        x0=gi*(nC+gap)
        ax.text(x0,nR+0.72,"saturation %.2f"%S,fontsize=9.4,color=INK,
                ha="left",va="bottom")
        for ci,(hdr,path) in enumerate(cols):
            ax.text(x0+ci+0.46,nR+0.30,hdr,fontsize=7.8,color=MUTED_INK,
                    ha="center",va="bottom")
        for ri,(bname,hue) in enumerate(BANDS):
            r,g,b=colorsys.hls_to_rgb(hue/360.0,0.50,S)
            src=(r*255,g*255,b*255)
            y=nR-1-ri
            for ci,(hdr,path) in enumerate(cols):
                c=np.array([r,g,b]) if path is None else shoot(path,src)
                ax.add_patch(Rectangle((x0+ci,y+0.16),0.92,0.68,color=c,lw=0))
                ax.text(x0+ci+0.46,y+0.02,hexs(c),fontsize=5.6,color=MUTED_INK,
                        ha="center",va="bottom",family="monospace")
            if gi==0:
                ax.text(-0.30,y+0.50,bname,fontsize=9.2,color=INK,
                        ha="right",va="center")
    ax.set_xlim(-2.35,total+0.05); ax.set_ylim(-0.55,nR+1.35)
    ax.axis("off")
    ax.text(-2.30,nR+1.15,title,fontsize=11.6,color=INK,ha="left",va="bottom",
            fontweight="bold")
    if note:
        ax.text(-2.30,-0.42,note,fontsize=7.6,color=MUTED_INK,ha="left",va="bottom")
    fig.subplots_adjust(left=0.012,right=0.995,top=0.985,bottom=0.02)
    fig.savefig(out,dpi=150,facecolor=BG); print(out)

P="/home/user/xMosaique_iOS/Presets/%s.xmp"
if __name__=="__main__":
    cinema=["Pierrot le Fou","Green Ray 1986","Autumn Sonata","Hero 2002"]
    stocks=["Natural","Cool Slide","Vivid Daylight","Green Accent","Golden",
            "Tungsten","Mono Tone"]
    chart([("orig",None)]+[(ABBR[n],P%n) for n in cinema],
          "out_hsl_cinema.png",
          "The eight HSL bands, rendered through the four cinema presets",
          13.4,
          "orig = unmodified   ·   AS = Autumn Sonata   ·   GR = Green Ray 1986   "
          "·   H2 = Hero 2002   ·   PLF = Pierrot le Fou   ·   probes are L=0.50 at "
          "each band centre; hex is the rendered sRGB output")
    chart([("orig",None)]+[(ABBR[n],P%n) for n in stocks],
          "out_hsl_stocks.png",
          "The eight HSL bands, rendered through the seven film-inspired presets",
          19.6,
          "orig = unmodified   ·   NAT = Natural   ·   CS = Cool Slide   ·   "
          "VD = Vivid Daylight   ·   GA = Green Accent   ·   GLD = Golden   ·   "
          "TUN = Tungsten   ·   MT = Mono Tone   ·   probes are L=0.50 at each band "
          "centre; hex is the rendered sRGB output")
