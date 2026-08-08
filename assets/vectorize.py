"""Posterized vector portraits: quantize tones -> trace each band with potrace -> stacked SVG.

Usage:
    python vectorize.py [OUT_DIR] [PHOTO_DIR]

Every entry in SOURCES is rendered in every ramp it lists. Output names follow
`<slug>-<ramp>.svg`; the first source keeps the `portrait-<ramp>.svg` names the
READMEs already point at.
"""
import os
import sys

import numpy as np
import potrace
from PIL import Image, ImageEnhance, ImageFilter, ImageOps

OUT_DIR = sys.argv[1] if len(sys.argv) > 1 else "."
PHOTO_DIR = sys.argv[2] if len(sys.argv) > 2 else "."
SIZE = 1000

# tonal ramp: index 0 = lightest (background), last = darkest
RAMPS = {
    "neon": ["#FFE9C9", "#F7A8C4", "#D946A6", "#8B3FCF", "#4C1D95", "#160B2E"],
    "mono": ["#F5F3FF", "#C4B5FD", "#8B5CF6", "#5B21B6", "#2E1065", "#0D0620"],
    "noir": ["#F7F3F1", "#D3ADA6", "#A63A3C", "#6E1017", "#3A0A11", "#0B0708"],
    "amber": ["#FFF6DF", "#FBD87F", "#F0A72A", "#C4700D", "#7A4205", "#1A1206"],
}

# (output slug, source filename, crop box on that source, ramps to render)
SOURCES = [
    ("portrait", "portrait.jpg", (20, 0, 820, 800), ["neon", "mono", "noir", "amber"]),
    ("portrait2", "portrait2.png", (0, 30, 491, 521), ["neon", "noir", "amber"]),
    ("portrait3", "portrait3.png", (60, 90, 960, 990), ["neon", "noir", "amber"]),
    ("portrait4", "portrait4.jpg", (170, 0, 1130, 960), ["neon", "noir", "amber"]),
]


def load(filename, crop):
    im = Image.open(os.path.join(PHOTO_DIR, filename))
    # cut-outs arrive as RGBA; flatten onto white so the subject reads light-on-light
    # instead of dumping the whole background into the darkest band
    if im.mode in ("RGBA", "LA", "P"):
        im = im.convert("RGBA")
        flat = Image.new("RGB", im.size, (255, 255, 255))
        flat.paste(im, mask=im.split()[-1])
        im = flat
    else:
        im = im.convert("RGB")

    im = im.crop(crop).resize((SIZE, SIZE), Image.LANCZOS)
    g = ImageOps.grayscale(im)
    g = ImageEnhance.Contrast(g).enhance(1.25)
    g = g.filter(ImageFilter.MedianFilter(5))
    g = g.filter(ImageFilter.GaussianBlur(1.2))
    return np.asarray(g, dtype=np.float32)


def thresholds(gray, n_bands):
    """Percentile cuts so each tonal band carries a comparable share of pixels."""
    qs = np.linspace(0, 100, n_bands + 1)[1:-1]
    return list(np.percentile(gray, qs))


def curves_to_d(path, scale):
    out = []
    for curve in path:
        pts = curve.start_point
        x, y = (pts.x, pts.y) if hasattr(pts, "x") else (pts[0], pts[1])
        d = [f"M{x * scale:.1f},{y * scale:.1f}"]
        for seg in curve:
            e = seg.end_point
            ex, ey = (e.x, e.y) if hasattr(e, "x") else (e[0], e[1])
            if seg.is_corner:
                c = seg.c
                cx, cy = (c.x, c.y) if hasattr(c, "x") else (c[0], c[1])
                d.append(f"L{cx * scale:.1f},{cy * scale:.1f}L{ex * scale:.1f},{ey * scale:.1f}")
            else:
                a, b = seg.c1, seg.c2
                ax, ay = (a.x, a.y) if hasattr(a, "x") else (a[0], a[1])
                bx, by = (b.x, b.y) if hasattr(b, "x") else (b[0], b[1])
                d.append(
                    f"C{ax * scale:.1f},{ay * scale:.1f} {bx * scale:.1f},{by * scale:.1f} "
                    f"{ex * scale:.1f},{ey * scale:.1f}"
                )
        d.append("Z")
        out.append("".join(d))
    return " ".join(out)


def trace_band(mask):
    # potracer's Bitmap inverts on construction, so hand it the complement to
    # get the mask's True region traced.
    bmp = potrace.Bitmap(np.logical_not(mask))
    return bmp.trace(turdsize=40, alphamax=1.0, opticurve=True, opttolerance=0.3)


def build(ramp_name, gray, cuts):
    """Stack tonal bands lightest-first: each mask is a subset of the previous one,
    so painting darkest last keeps every band visible."""
    ramp = RAMPS[ramp_name]
    layers = []
    for i, cut in enumerate(sorted(cuts, reverse=True)):
        d = curves_to_d(trace_band(gray < cut), 1.0)
        if d:
            layers.append((ramp[i + 1], d))
    return layers


def svg(layers, ramp_name, circular=True):
    ramp = RAMPS[ramp_name]
    clip = ' clip-path="url(#c)"' if circular else ""
    body = "\n".join(
        f'    <path fill="{color}" fill-rule="evenodd" d="{d}"/>' for color, d in layers
    )
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {SIZE} {SIZE}" width="{SIZE}" height="{SIZE}" role="img" aria-label="Vector portrait">
  <defs>
    <clipPath id="c"><circle cx="{SIZE // 2}" cy="{SIZE // 2}" r="{SIZE // 2 - 6}"/></clipPath>
    <linearGradient id="ring" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="{ramp[1]}"/>
      <stop offset="0.5" stop-color="{ramp[2]}"/>
      <stop offset="1" stop-color="{ramp[3]}"/>
    </linearGradient>
  </defs>
  <g{clip}>
    <rect width="{SIZE}" height="{SIZE}" fill="{ramp[0]}"/>
{body}
  </g>
  <circle cx="{SIZE // 2}" cy="{SIZE // 2}" r="{SIZE // 2 - 6}" fill="none" stroke="url(#ring)" stroke-width="10"/>
</svg>
"""


if __name__ == "__main__":
    for slug, filename, crop, ramps in SOURCES:
        try:
            gray = load(filename, crop)
        except FileNotFoundError:
            print(f"skip {slug}: {filename} not found in {PHOTO_DIR}")
            continue

        cuts = thresholds(gray, 6)
        for ramp_name in ramps:
            layers = build(ramp_name, gray, cuts)
            path = f"{OUT_DIR}/{slug}-{ramp_name}.svg"
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(svg(layers, ramp_name))
            print(f"wrote {path} ({len(layers)} bands)")
