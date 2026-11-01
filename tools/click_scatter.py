"""Click scatter from re-clicked trunks: reference/stem_traces_reclick.json
against reference/stem_traces.json.  Each new trace is matched to the old
trace on the same photo with the nearest base.  For every click of one trace,
the horizontal offset from the other trace's polyline at the same image
height (only where both traces cover that height), both ways.  With
independent click error sigma, the other line (linear between its own noisy
clicks) carries 2/3 sigma^2 on average, so RMS offset ~ sigma sqrt(5/3);
real trunk wobble between the other trace's clicks adds to it, so this sigma
is an upper bound.  Stem metrics (tools/stem_metrics.py, unchanged) of both
traces, for repeatability.

    python tools/click_scatter.py
"""
import json
import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import stem_metrics as sm  # noqa: E402

old = json.load(open(ROOT / "reference" / "stem_traces.json"))
new = json.load(open(ROOT / "reference" / "stem_traces_reclick.json"))
HGT = 1802   # height (px) of the photo-matched stand render the model traces use
oldims = {v["name"]: v for v in old["images"].values()}


def base(pts):
    return max(pts, key=lambda p: p[1])


def offsets(a, b):
    """x offsets of a's clicks from b's polyline at the same y."""
    b = sorted(b, key=lambda p: p[1])
    by = np.array([p[1] for p in b]); bx = np.array([p[0] for p in b])
    out = []
    for x, y in a:
        if by[0] <= y <= by[-1]:
            out.append(x - np.interp(y, by, bx))
    return out


pairs, allo = [], []
print("| photo | trunk (old id) | base distance (px) | clicks old / new | overlap, % of height | RMS offset (px) | off-line % old / new | turning deg old / new | lean deg old / new |")
print("|---|---|---|---|---|---|---|---|---|")
for v in new["images"].values():
    for t in v["trunks"]:
        o_im = oldims.get(v["name"])
        if not o_im or not o_im["trunks"]:
            continue
        bn = base(t["pts"])
        best = min(o_im["trunks"], key=lambda u: math.dist(base(u["pts"]), bn))
        dist = math.dist(base(best["pts"]), bn)
        if dist > 60:
            print(f"| {v['name']} | no old trace within 60 px (nearest {dist:.0f} px) | | | | | | | |")
            continue
        off = offsets(t["pts"], best["pts"]) + offsets(best["pts"], t["pts"])
        H = v["h"]
        ys_o = [p[1] for p in best["pts"]]; ys_n = [p[1] for p in t["pts"]]
        ov = max(0.0, min(max(ys_o), max(ys_n)) - max(min(ys_o), min(ys_n))) / H * 100
        mo, mn = sm.metrics(best["pts"], 4), sm.metrics(t["pts"], 4)
        rms = float(np.sqrt(np.mean(np.square(off)))) if off else float("nan")
        allo += [x / H for x in off]
        pairs.append((mo, mn, H, len(best["pts"]), len(t["pts"])))
        print(f"| {v['name'].replace('.jpg', '')} | {best['id']} | {dist:.0f} | {len(best['pts'])} / {len(t['pts'])} | {ov:.0f} | {rms:.1f} | "
              f"{mo['max_offline_pct']:.2f} / {mn['max_offline_pct']:.2f} | {mo['total_turning_deg']:.1f} / {mn['total_turning_deg']:.1f} | {mo['lean_deg']:+.1f} / {mn['lean_deg']:+.1f} |")
allo = np.array(allo)
rms = float(np.sqrt(np.mean(allo ** 2)))
mad = float(np.median(np.abs(allo - np.median(allo)))) * 1.4826
sig = rms / math.sqrt(5 / 3)
sig_r = mad / math.sqrt(5 / 3)
print(f"\npairs {len(pairs)}, offsets {len(allo)}")
print(f"RMS offset {rms * 100:.3f} % of image height; click scatter sigma <= {sig * 100:.3f} % ({sig * HGT:.1f} px on the {HGT}-px render)")
print(f"robust (MAD) version: sigma <= {sig_r * 100:.3f} % ({sig_r * HGT:.1f} px)")
print(f"earlier: upper bound 0.505 % (9.1 px); assumed 0.5x = 4.6 px  ->  measured scale {sig / 0.005054772259887635:.2f}x (robust {sig_r / 0.005054772259887635:.2f}x)")
d = lambda k: np.array([abs(a[k] - b[k]) for a, b, *_ in pairs])
print(f"repeatability, median |old - new|: off-line {np.median(d('max_offline_pct')):.2f} %, turning {np.median(d('total_turning_deg')):.1f} deg, "
      f"lean {np.median(np.array([abs(a['lean_deg'] - b['lean_deg']) for a, b, *_ in pairs])):.1f} deg, bends {np.median(d('bends')):.1f}")
