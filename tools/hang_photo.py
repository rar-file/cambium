"""One instrument for a leafless birch against the sky.  It runs unchanged on a photo and on a picture of the model
drawn leafless from a level side view (tools/hang_render.py), so the two can be compared number by number.

    python tools/hang_photo.py photos [--out reference/betula_pendula/hang_photo_numbers.json]   # the reference photos, on the owner's PC only
    python tools/hang_photo.py table                  # those numbers as a table, photo by photo and by kind
    python tools/hang_photo.py picture FILE [--base-y 0.97 --top-y 0.03]

The same part of the tree.  A photo is read only inside boxes set by eye, which leave out the ground and whatever is
not birch; they often cut the lower crown.  window_of() restates those boxes in tree heights from the foot of the stem,
and window_mask() lays them on any other picture of a tree, so a model tree is read over the same part of itself, drawn
as many pixels tall as the photo's tree (tools/hang_run.py).  A photo is read through the very same function.

What it reads.  Fine lines: anything up to about 3 pixels across that stands out from what is beside it, darker or
lighter.  It finds them by the curvature of the picture's brightness at a scale of 1 pixel (Steger 1998, IEEE PAMI
20:113: a line is where the curvature across it is strong, its centre lies within the pixel, and the brightness turns
round across it), thins them to their centre lines, and reads each centre pixel's direction.  It never asks what
colour a twig or the sky is, or which of them is the brighter, and every strength is taken as a share of the
picture's own contrast, so light and exposure cancel.

What it reports.
  near_vertical_share   share of fine-line length within 20 degrees of vertical (the audit's H5).  Lines pointing
                        every way alike would give 0.22
  near_level_share      the same within 20 degrees of level
  tips                  twig ends whose direction can be told: a traced line with one end free in the sky and the other
                        joined to other wood.  Shares pointing down (over 30 degrees below level), up, or sideways
  hanging_run           from each tip that points down, the traced length back to where the line stops pointing over 30
                        degrees below level, as a share of tree height: mean, 90th percentile, longest
  outline               crown width over tree height, and the height of the widest tenth over tree height
  fringe_low_at         how far down the near-vertical fine twigs reach: the height under which 5 % of them sit, as a
                        share of tree height (0 the ground, 1 the top)

What it cannot tell.  Depth: a twig pointing at the camera looks short and steep.  Scale: every length is a share of
the tree's height in the frame, so a photo whose top or base is out of frame gives directions only.  Up from down
along a line: only at a told tip.  Wood thinner than about a tenth of a pixel, or hidden behind other wood.  Whose
twig it is, where trees overlap.  It needs the tree's base and top (by eye on a photo, known for the model).
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np
from scipy import ndimage

ROOT = Path(__file__).resolve().parent.parent
FRAMES = ROOT / "reference" / "betula_pendula" / "hang_photo_frames.json"     # beside the species' other reference numbers, so the server has them too
NUMBERS = ROOT / "reference" / "betula_pendula" / "hang_photo_numbers.json"

SIGMA_PX = 1.0        # the scale of a fine line
LINE_MIN = 0.04       # a line's strength, as a share of the picture's contrast: about a tenth of a pixel of wood at full contrast
LINE_STRICT = 0.08    # the same, twice as strict: reported beside the first to show what the threshold does
CENTRE_PX = 0.7       # a line's centre must lie within this of the pixel: a hairline half a pixel off reads 0.67, the edge of thick wood more
THICK_EDGE = 0.12     # slope, as a share of contrast, that marks the edge of thick wood
THICK_MIN_PX = 12     # ... where at least this many such pixels join up
NEAR_DEG = 20.0
HANG_DEG = 30.0       # the same 30 degrees below level as tools/hang_measure.py
MIN_LINE_PX = 6       # fewer joined-up centre pixels than this is not a line
MIN_CHAIN_PX = 8      # shorter traced lines carry no tip
TIP_SPAN_PX = 10      # a tip's direction is read over its last pixels
FREE_PX = 8           # a free end has no other wood ahead of it within this
JOIN_PX = 4           # a joined end has other wood ahead of it within this
SEEN_PX = LINE_MIN * SIGMA_PX / 0.399   # the narrowest wood it sees at full contrast, about 0.1 px (a hairline's strength is 0.399 x its width)
BANDS = 10
BAND_MIN_PX = 20
EVEN_SHARE = 2.0 * NEAR_DEG / 180.0   # what lines pointing every way alike would give
# how soft a picture is, read at the edges of its thick wood (sharpness)
EDGE_REACH_PX = 5.0       # brightness is read this far to each side of an edge
EDGE_FLAT_PX = 3.0        # ... and from this far out each side must be flat: wood and sky both wide enough
EDGE_STEP_PX = 0.25
EDGE_MIN = 0.25           # the step from wood to sky, as a share of the picture's contrast
EDGE_SLOPE_MIN = 0.02     # the slope that makes a pixel worth looking at, the same way
EDGE_FLAT = 0.10          # how much each side may vary, as a share of the step
TEN_TO_NINETY = 2.563     # a Gaussian blur of 1 px spreads a sharp edge's rise from 10 % to 90 % over this many pixels
QUIET_SLOPE = 0.004       # open sky: the smoothest tenth of the picture changes by less than this share of its contrast per pixel


def load(path) -> np.ndarray:
    """A picture as grey levels 0-1, three channels."""
    from PIL import Image

    with Image.open(path) as im:
        return np.asarray(im.convert("RGB"), dtype=np.float64) / 255.0


def _shift(m: np.ndarray, dy: int, dx: int) -> np.ndarray:
    """out[y, x] = m[y + dy, x + dx], False past the edge."""
    out = np.zeros_like(m)
    h, w = m.shape
    out[max(-dy, 0): h + min(-dy, 0), max(-dx, 0): w + min(-dx, 0)] = m[max(dy, 0): h + min(dy, 0), max(dx, 0): w + min(dx, 0)]
    return out


def brightness(img: np.ndarray) -> np.ndarray:
    """A picture's brightness alone, 0-1 (ITU-R BT.601 weights).  Colour is dropped on purpose: a JPEG keeps colour at
    half the detail of brightness, often in one direction only, which would tilt the directions read from it."""
    if img.ndim == 2:
        return img.astype(np.float64)
    if img.shape[2] == 1:
        return img[:, :, 0].astype(np.float64)
    return img[:, :, :3] @ np.array([0.299, 0.587, 0.114])


def _curvature(ch: np.ndarray):
    """Per pixel of a brightness picture: line strength, the signed curvature across the line, the across direction
    (radians; x right, y down), and the slope along x and along y."""
    s = SIGMA_PX
    gxx = ndimage.gaussian_filter(ch, s, order=(0, 2)) * s * s
    gyy = ndimage.gaussian_filter(ch, s, order=(2, 0)) * s * s
    gxy = ndimage.gaussian_filter(ch, s, order=(1, 1)) * s * s
    gx = ndimage.gaussian_filter(ch, s, order=(0, 1)) * s
    gy = ndimage.gaussian_filter(ch, s, order=(1, 0)) * s
    half = np.hypot(0.5 * (gxx - gyy), gxy)
    mean = 0.5 * (gxx + gyy)
    la, lb = mean + half, mean - half
    first = np.abs(la) >= np.abs(lb)
    big = np.where(first, la, lb)
    strength = np.abs(big) - np.abs(np.where(first, lb, la))
    phi = 0.5 * np.arctan2(2.0 * gxy, gxx - gyy)   # the direction of la's own axis
    across = np.where(first, phi, phi + 0.5 * math.pi)
    return strength, big, across, gx, gy


def _thin(mask: np.ndarray) -> np.ndarray:
    """Thin every line to one pixel wide, so a pixel with three neighbours is a real meeting: Zhang & Suen 1984
    (Comm. ACM 27:236) takes off pixels at a line's side that aren't its end and don't hold it together, then the
    corner pixel comes out of every stair step."""
    m = mask.copy()
    ring = ((-1, 0), (-1, 1), (0, 1), (1, 1), (1, 0), (1, -1), (0, -1), (-1, -1))     # N, NE, E, SE, S, SW, W, NW
    for _ in range(4):
        gone = 0
        for first in (True, False):
            p = [_shift(m, dy, dx) for dy, dx in ring]
            count = sum(q.astype(np.int8) for q in p)
            turns = sum((~p[k] & p[(k + 1) % 8]).astype(np.int8) for k in range(8))
            n, e, s, w = p[0], p[2], p[4], p[6]
            side = (~(n & e & s) & ~(e & s & w)) if first else (~(n & e & w) & ~(n & s & w))
            off = m & (count >= 2) & (count <= 6) & (turns == 1) & side
            gone += int(off.sum())
            m &= ~off
        if not gone:
            break
    for dy, dx in ((-1, 1), (1, 1), (1, -1), (-1, -1)):
        corner = m & _shift(m, dy, 0) & _shift(m, 0, dx) & ~_shift(m, -dy, 0) & ~_shift(m, 0, -dx) & ~_shift(m, -dy, -dx)
        m &= ~corner
    return m


def _neighbours(m: np.ndarray) -> np.ndarray:
    return sum(_shift(m, dy, dx).astype(np.int8) for dy in (-1, 0, 1) for dx in (-1, 0, 1) if (dy, dx) != (0, 0))


def _centres(img: np.ndarray, roi: np.ndarray | None = None) -> dict:
    """Where a line's centre may lie, before any strength is asked of it, with each pixel's strength, its angle from
    vertical (degrees, 0-90), the length it stands for, the slope's size there, and the picture's contrast inside `roi`."""
    grey = brightness(img)
    strength, big, across, gx, gy = _curvature(grey)
    inside = np.ones(grey.shape, bool) if roi is None else roi
    lo, hi = np.percentile(grey[inside], [0.1, 99.9])
    contrast = float(max(hi - lo, 1e-6))
    h, w = strength.shape
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float64)
    ax, ay = np.cos(across), np.sin(across)
    ahead = ndimage.map_coordinates(strength, [yy + ay, xx + ax], order=1, mode="nearest")
    behind = ndimage.map_coordinates(strength, [yy - ay, xx - ax], order=1, mode="nearest")
    # a line, not the edge of thick wood: its centre lies within this pixel (Steger's test) ...
    offset = np.abs(SIGMA_PX * (gx * ax + gy * ay) / np.where(big == 0.0, 1.0, big))
    may = inside & (strength > ahead) & (strength >= behind) & (offset <= CENTRE_PX)
    # ... and the brightness turns round across it: the slope a pixel to either side has opposite signs.  Beside an edge it has one sign
    cy, cx = np.nonzero(may)
    if cy.size:
        sy, sx = ay[cy, cx], ax[cy, cx]
        slope = [ndimage.map_coordinates(gx, [cy + k * sy, cx + k * sx], order=1, mode="nearest") * sx
                 + ndimage.map_coordinates(gy, [cy + k * sy, cx + k * sx], order=1, mode="nearest") * sy for k in (-1.0, 1.0)]
        may[cy, cx] = slope[0] * slope[1] < 0.0
    # the line runs square to `across`: (-sin, cos); its angle from vertical, and the length one centre pixel stands for
    lx, ly = np.abs(np.sin(across)), np.abs(np.cos(across))
    return {"may": may, "strength": strength, "angle": np.degrees(np.arctan2(lx, ly)), "length": 1.0 / np.maximum(lx, ly),
            "edge": np.hypot(gx, gy), "contrast": contrast, "inside": inside}


def fine_lines(img: np.ndarray, roi: np.ndarray | None = None, line_min: float = LINE_MIN, centres: dict | None = None):
    """The centre lines of the fine lines in the picture: a mask, each pixel's angle from vertical (degrees, 0-90), the
    length each pixel stands for, the edges of thick wood, and the picture's contrast."""
    c = _centres(img, roi) if centres is None else centres
    mask = _thin(c["may"] & (c["strength"] >= line_min * c["contrast"]))
    # a line is at least MIN_LINE_PX centre pixels joined up: shorter scraps are buds, catkins and grain, not twigs
    label, count = ndimage.label(mask, structure=np.ones((3, 3), int))
    if count:
        size = np.bincount(label.ravel(), minlength=count + 1)
        mask &= size[label] >= MIN_LINE_PX
    thick = c["inside"] & (c["edge"] >= THICK_EDGE * c["contrast"]) & ~ndimage.binary_dilation(mask, iterations=2)
    # an edge of thick wood is long; the few steep pixels past the end of a fine line are not one
    label, count = ndimage.label(thick, structure=np.ones((3, 3), int))
    if count:
        size = np.bincount(label.ravel(), minlength=count + 1)
        thick &= size[label] >= THICK_MIN_PX
    return mask, c["angle"], c["length"], thick, c["contrast"]


def _paths(chain: np.ndarray) -> list:
    """Every traced line of the mask as its pixels in order, end to end: [(ys, xs), ...].  Rings have no end and are left out."""
    h, w = chain.shape
    W = w + 2
    pad = np.zeros((h + 2, W), np.uint8)
    pad[1:-1, 1:-1] = chain
    count = _neighbours(pad.astype(bool))
    starts = np.flatnonzero((pad == 1) & (count <= 1))
    buf = bytearray(pad.tobytes())
    steps = (-W, -1, 1, W, -W - 1, -W + 1, W - 1, W + 1)
    out = []
    for s in starts.tolist():
        if buf[s] != 1:
            continue
        path, cur = [s], s
        buf[s] = 2
        while True:
            for d in steps:
                if buf[cur + d] == 1:
                    cur += d
                    buf[cur] = 2
                    path.append(cur)
                    break
            else:
                break
        p = np.asarray(path, dtype=np.int64)
        out.append((p // W - 1, p % W - 1))
    return out


def _below_level(dy: float, dx: float) -> float:
    """Degrees below level of a direction in the picture (y grows downward)."""
    return math.degrees(math.atan2(dy, abs(dx)))


def tips(mask: np.ndarray, thick: np.ndarray) -> dict:
    """Twig ends whose direction can be told, and the hanging run behind each that points down (pixels)."""
    meet = mask & (_neighbours(mask) >= 3)
    chain = mask & ~meet
    paths = _paths(chain)
    owner = np.zeros(mask.shape, np.int32)
    for k, (ys, xs) in enumerate(paths):
        owner[ys, xs] = k + 1
    other = meet | thick
    h, w = mask.shape
    reach = max(FREE_PX, JOIN_PX)
    oy, ox = np.mgrid[-reach: reach + 1, -reach: reach + 1]
    dist = np.hypot(oy, ox)

    def wood_ahead(ys, xs, k: int) -> float:
        """How near other wood lies ahead of a traced line's last pixel, within 60 degrees of the way it is heading."""
        y, x = int(ys[-1]), int(xs[-1])
        j = max(len(ys) - 1 - TIP_SPAN_PX, 0)
        uy, ux = float(y - ys[j]), float(x - xs[j])
        norm = math.hypot(uy, ux)
        y0, y1, x0, x1 = max(y - reach, 0), min(y + reach + 1, h), max(x - reach, 0), min(x + reach + 1, w)
        win = (slice(y0 - y + reach, y1 - y + reach), slice(x0 - x + reach, x1 - x + reach))
        own = owner[y0:y1, x0:x1]
        hit = (other[y0:y1, x0:x1] | ((own != 0) & (own != k))) & ((oy[win] * uy + ox[win] * ux) >= 0.5 * norm * dist[win]) & (dist[win] > 0)
        d = dist[win][hit]
        return float(d.min()) if d.size else float("inf")

    down, up, side, run_px, tip_y = 0, 0, 0, [], []
    for k, (ys, xs) in enumerate(paths, start=1):
        n = len(ys)
        if n < MIN_CHAIN_PX:
            continue
        a = wood_ahead(ys[::-1], xs[::-1], k)          # ahead of the path's first pixel
        b = wood_ahead(ys, xs, k)                      # ahead of its last
        if a <= JOIN_PX and b > FREE_PX:
            pass                                       # the tip is the path's last pixel
        elif b <= JOIN_PX and a > FREE_PX:
            ys, xs = ys[::-1], xs[::-1]
        else:
            continue                                   # both ends free (a scrap) or both joined (a crossing): can't be told
        j = max(n - 1 - TIP_SPAN_PX, 0)
        below = _below_level(float(ys[-1] - ys[j]), float(xs[-1] - xs[j]))
        if below > HANG_DEG:
            down += 1
            run = 0.0
            for i in range(n - 1, 0, -1):
                j = max(i - 5, 0)
                if _below_level(float(ys[i] - ys[j]), float(xs[i] - xs[j])) <= HANG_DEG:
                    break
                run += math.hypot(float(ys[i] - ys[i - 1]), float(xs[i] - xs[i - 1]))
            run_px.append(run)
            tip_y.append(int(ys[-1]))
        elif below < -HANG_DEG:
            up += 1
        else:
            side += 1
    told = down + up + side
    return {"told": told, "down_share": down / told if told else None, "up_share": up / told if told else None,
            "side_share": side / told if told else None, "run_px": run_px, "tip_y": tip_y}


def measure(img: np.ndarray, roi: np.ndarray | None = None, base_y: float | None = None, top_y: float | None = None, full: bool = True) -> dict:
    """Every number the instrument gives for one picture.  roi: the part of the picture to read (all of it if None).
    base_y, top_y: the pixel rows of the tree's base and top; without them only directions are given.  full=False stops
    after the directions (the same numbers, with no tips, runs or outline), for the many side readings of one tree."""
    centres = _centres(img, roi)
    mask, angle, length, thick, contrast = fine_lines(img, roi, LINE_MIN, centres)
    ys, xs = np.nonzero(mask)
    a, wt = angle[ys, xs], length[ys, xs]
    total = float(wt.sum())
    out = {"picture_px": [int(mask.shape[1]), int(mask.shape[0])], "contrast": round(contrast, 4), "fine_line_px": round(total, 1)}
    if total <= 0.0:
        return {**out, "near_vertical_share": None}
    out["near_vertical_share"] = float(wt[a <= NEAR_DEG].sum()) / total
    out["near_level_share"] = float(wt[a >= 90.0 - NEAR_DEG].sum()) / total
    out["angle_from_vertical_shares_by_10deg"] = [round(float(wt[(a >= lo) & (a < lo + 10.0 + (1e-9 if lo == 80.0 else 0.0))].sum()) / total, 4) for lo in np.arange(0.0, 90.0, 10.0)]
    strict, s_angle, s_length, _, _ = fine_lines(img, roi, LINE_STRICT, centres)
    sy, sx = np.nonzero(strict)
    s_total = float(s_length[sy, sx].sum())
    out["near_vertical_share_strict"] = float(s_length[sy, sx][s_angle[sy, sx] <= NEAR_DEG].sum()) / s_total if s_total > 0.0 else None
    out["fine_line_px_strict"] = round(s_total, 1)
    if not full:
        return out
    t = tips(mask, thick)
    out["tips"] = {k: t[k] for k in ("told", "down_share", "up_share", "side_share")}
    if base_y is None or top_y is None or base_y <= top_y:
        return {**out, "tree_height_px": None, "hanging_run": None, "outline": None, "fringe_low_at": None}
    height = float(base_y - top_y)
    out["tree_height_px"] = round(height, 1)
    # hanging runs behind the tips that point down, on the tree only; a run under 1 % of tree height isn't counted
    runs = np.asarray([r for r, y in zip(t["run_px"], t["tip_y"]) if top_y <= y <= base_y], dtype=float) / height
    runs = runs[runs >= 0.01]
    out["hanging_run"] = {"runs": int(runs.size), "mean_over_height": float(runs.mean()) if runs.size else None,
                          "p90_over_height": float(np.percentile(runs, 90)) if runs.size else None,
                          "longest_over_height": float(runs.max()) if runs.size else None}
    rel = (base_y - ys) / height
    on = (rel >= 0.0) & (rel <= 1.0)
    band = np.clip((rel * BANDS).astype(int), 0, BANDS - 1)
    widths = np.zeros(BANDS)
    for b in range(BANDS):
        hit = on & (band == b)
        if int(hit.sum()) >= BAND_MIN_PX:
            widths[b] = np.percentile(xs[hit], 98) - np.percentile(xs[hit], 2)
    out["outline"] = {"width_over_height": float(widths.max()) / height if widths.max() > 0.0 else None,
                      "widest_at": (int(np.argmax(widths)) + 0.5) / BANDS if widths.max() > 0.0 else None,
                      "width_by_tenth_over_height": [round(float(x) / height, 3) for x in widths]}
    upright = on & (a <= NEAR_DEG)
    out["fringe_low_at"] = float(np.percentile(rel[upright], 5)) if int(upright.sum()) >= BAND_MIN_PX else None
    return out


def frame_mask(shape, frame: dict) -> np.ndarray:
    """The part of a photo to read, from boxes [x0, y0, x1, y1] in shares of its width and height: inside any
    `include` box and outside every `exclude` box."""
    h, w = shape[:2]
    m = np.zeros((h, w), bool)
    for x0, y0, x1, y1 in frame.get("include") or [[0.0, 0.0, 1.0, 1.0]]:
        m[int(round(y0 * h)): int(round(y1 * h)), int(round(x0 * w)): int(round(x1 * w))] = True
    for x0, y0, x1, y1 in frame.get("exclude") or []:
        m[int(round(y0 * h)): int(round(y1 * h)), int(round(x0 * w)): int(round(x1 * w))] = False
    return m


def window_of(frame: dict) -> dict | None:
    """A photo's boxes restated in tree heights, so the same part of any other tree can be read (window_mask).  Each box
    becomes [a0, v0, a1, v1]: a is sideways from the foot of the stem (left is negative) and v is height above it, both
    in tree heights, foot to top as the picture shows them.  `lean` is how far the top stands to the side of the foot,
    the same way: on another picture the boxes are laid along that tree's own stem line, foot to top.  None where the
    photo's foot or top is out of frame, or its size isn't given."""
    px = frame.get("picture_px")
    need = [frame.get(k) for k in ("base_x", "base_y", "top_x", "top_y")]
    if px is None or any(v is None for v in need):
        return None
    w, h = px
    bx, by, tx, ty = need
    tall = (by - ty) * h
    if tall <= 0.0:
        return None

    def box(b) -> list:
        # the same whole pixels frame_mask cuts at
        x0, y0, x1, y1 = b
        return [round((int(round(x0 * w)) - bx * w) / tall, 6), round((by * h - int(round(y1 * h))) / tall, 6),
                round((int(round(x1 * w)) - bx * w) / tall, 6), round((by * h - int(round(y0 * h))) / tall, 6)]

    return {"tree_height_px": round(tall, 2), "lean": round((tx - bx) * w / tall, 6),
            "include": [box(b) for b in frame.get("include") or [[0.0, 0.0, 1.0, 1.0]]], "exclude": [box(b) for b in frame.get("exclude") or []]}


def window_mask(shape, window: dict, base_xy, top_xy, mirror: bool = False) -> np.ndarray:
    """The part of a picture inside a window (window_of), for a tree whose stem meets the ground at base_xy and whose
    highest twig is at top_xy (pixels: x to the right, y downward).  mirror lays the window on the tree's other side:
    which side of a model tree stands for a photo's left is anyone's choice."""
    h, w = shape[:2]
    tall = float(base_xy[1] - top_xy[1])
    y, x = np.mgrid[0:h, 0:w]
    v = (base_xy[1] - (y + 0.5)) / tall                                         # each pixel's centre, in tree heights above the foot
    u = ((x + 0.5) - base_xy[0] - (top_xy[0] - base_xy[0]) * v) / tall          # ... and to the side of the stem line
    a = (-u if mirror else u) + window["lean"] * v
    m = np.zeros((h, w), bool)
    for a0, v0, a1, v1 in window["include"]:
        m |= (a >= a0) & (a < a1) & (v > v0) & (v <= v1)
    for a0, v0, a1, v1 in window["exclude"]:
        m &= ~((a >= a0) & (a < a1) & (v > v0) & (v <= v1))
    return m


def window_span(window: dict) -> dict:
    """What a window covers, for a table, in tree heights: its lowest and highest edge, the height from which it is as
    wide as it gets, and how far it reaches to each side of the foot of the stem."""
    boxes = window["include"]
    widest = max(b[2] - b[0] for b in boxes)
    return {"from": min(b[1] for b in boxes), "to": min(max(b[3] for b in boxes), 1.0), "left": min(b[0] for b in boxes), "right": max(b[2] for b in boxes),
            "full_width_from": min(b[1] for b in boxes if b[2] - b[0] >= 0.75 * widest)}


def frame_roi(shape, frame: dict) -> np.ndarray:
    """The part of a photo to read.  Where the photo has a window it is read through window_mask, the function that lays
    the window on a model picture, so the two can't drift apart; it gives frame_mask's own pixels (a test holds that)."""
    window = window_of(frame)
    if window is None:
        return frame_mask(shape, frame)
    h, w = shape[:2]
    if [w, h] != list(frame["picture_px"]):
        raise ValueError(f"the frame says the picture is {frame['picture_px']} px, but it is {[w, h]}")
    return window_mask(shape, window, (frame["base_x"] * w, frame["base_y"] * h), (frame["top_x"] * w, frame["top_y"] * h))


def measure_framed(img: np.ndarray, frame: dict) -> dict:
    """A photo's numbers, read inside its frame."""
    h = img.shape[0]
    base, top = frame.get("base_y"), frame.get("top_y")
    roi = frame_roi(img.shape, frame)
    out = measure(img, roi, None if base is None else base * h, None if top is None else top * h)
    if not frame.get("outline", True):
        out["outline"] = out["fringe_low_at"] = None       # crowns overlap, or the frame cuts the crown: no width to read
    # how far down the frame itself goes, as a share of tree height: a fringe read at about this height is cut off by the frame, not by the tree
    out["frame_low_at"] = None if out.get("tree_height_px") is None else max(0.0, float(base * h - (np.nonzero(roi.any(axis=1))[0].max() + 1)) / out["tree_height_px"])
    return {"kind": frame.get("kind"), "young": bool(frame.get("young")), "whole_tree": base is not None and top is not None, **out,
            "window": window_of(frame), "camera": sharpness(img, roi)}


def sharpness(img: np.ndarray, roi: np.ndarray | None = None, most: int = 20000) -> dict:
    """How soft and how grainy a picture is, so a model picture can be given the same (tools/hang_render.py, like_a_photo).

    Soft: at the edges of thick wood against the sky (the stem and big limbs, where both sides are flat from
    EDGE_FLAT_PX out), the brightness is read across the edge and the distance over which it rises from 10 % to 90 % of
    the step is taken.  Divided by 2.563 it is the Gaussian blur that would spread a sharp edge as much.  Every edge
    gives an upper bound on the camera's blur, since a round stem's edge is not a sharp step: blur_sigma_px is from the
    median edge (the heavier figure, used for the model's copy), blur_sigma_sharp_px from the sharpest quarter.  A
    perfectly sharp edge on a pixel grid still reads about 0.3 px.
    Grainy: in the smoothest tenth of the picture, if that is open sky, how far the brightness stands from its own
    2-pixel blur, as a share of the picture's contrast."""
    grey = brightness(img)
    inside = np.ones(grey.shape, bool) if roi is None else roi
    lo, hi = np.percentile(grey[inside], [0.1, 99.9])
    contrast = float(max(hi - lo, 1e-6))
    gx = ndimage.gaussian_filter(grey, SIGMA_PX, order=(0, 1))
    gy = ndimage.gaussian_filter(grey, SIGMA_PX, order=(1, 0))
    mag = np.hypot(gx, gy)
    out = {"edges": 0, "edge_rise_10_90_px": None, "edge_rise_quartiles_px": None, "blur_sigma_px": None, "blur_sigma_sharp_px": None,
           "grain_share_of_contrast": None}
    # grain: where the picture is smoothest, at a scale grain doesn't reach
    smooth = ndimage.maximum_filter(np.hypot(ndimage.gaussian_filter(grey, 2.0, order=(0, 1)), ndimage.gaussian_filter(grey, 2.0, order=(1, 0))), size=9)
    if int(inside.sum()) >= 1000:
        tenth = float(np.percentile(smooth[inside], 10))
        d = (grey - ndimage.gaussian_filter(grey, 2.0))[inside & (smooth <= tenth)]
        if tenth <= QUIET_SLOPE * contrast and d.size >= 100:
            # white grain less its own 2-pixel blur keeps 0.97 of its size; the median deviation shrugs off a stray twig
            out["grain_share_of_contrast"] = float(1.4826 * np.median(np.abs(d - np.median(d))) / 0.97 / contrast)
    # edges: the steepest pixel across each edge
    cy, cx = np.nonzero(inside & (mag >= EDGE_SLOPE_MIN * contrast))
    if not cy.size:
        return out
    nx, ny = gx[cy, cx] / mag[cy, cx], gy[cy, cx] / mag[cy, cx]                  # across the edge, from dark to light
    ahead = ndimage.map_coordinates(mag, [cy + ny, cx + nx], order=1, mode="nearest")
    behind = ndimage.map_coordinates(mag, [cy - ny, cx - nx], order=1, mode="nearest")
    top = (mag[cy, cx] > ahead) & (mag[cy, cx] >= behind)
    cy, cx, nx, ny = cy[top], cx[top], nx[top], ny[top]
    if cy.size > most:
        pick = np.linspace(0, cy.size - 1, most).astype(np.int64)
        cy, cx, nx, ny = cy[pick], cx[pick], nx[pick], ny[pick]
    t = np.arange(-EDGE_REACH_PX, EDGE_REACH_PX + 0.5 * EDGE_STEP_PX, EDGE_STEP_PX)
    prof = ndimage.map_coordinates(grey, [cy[:, None] + ny[:, None] * t[None, :], cx[:, None] + nx[:, None] * t[None, :]], order=3, mode="nearest")
    dark, light = prof[:, t <= -EDGE_FLAT_PX], prof[:, t >= EDGE_FLAT_PX]
    low, high = np.median(dark, axis=1), np.median(light, axis=1)
    step = high - low
    ok = (step >= EDGE_MIN * contrast) & (dark.std(axis=1) <= EDGE_FLAT * step) & (light.std(axis=1) <= EDGE_FLAT * step)
    if not ok.any():
        return out
    n = (prof[ok] - low[ok, None]) / step[ok, None]
    i90 = np.argmax(n >= 0.9, axis=1)                                            # the first reading at 90 % or over
    under = (n <= 0.1) & (np.arange(n.shape[1])[None, :] < i90[:, None])
    i10 = n.shape[1] - 1 - np.argmax(under[:, ::-1], axis=1)                     # the last at 10 % or under before it
    rows = np.nonzero((i90 > 0) & under.any(axis=1))[0]
    if not rows.size:
        return out
    i10, i90 = i10[rows], i90[rows]
    t10 = t[i10] + EDGE_STEP_PX * (0.1 - n[rows, i10]) / np.maximum(n[rows, i10 + 1] - n[rows, i10], 1e-9)
    t90 = t[i90 - 1] + EDGE_STEP_PX * (0.9 - n[rows, i90 - 1]) / np.maximum(n[rows, i90] - n[rows, i90 - 1], 1e-9)
    rise = t90 - t10
    rise = rise[rise > 0.0]
    if not rise.size:
        return out
    q = np.percentile(rise, [25, 50, 75])
    out.update({"edges": int(rise.size), "edge_rise_10_90_px": float(q[1]), "edge_rise_quartiles_px": [float(q[0]), float(q[2])],
                "blur_sigma_px": float(q[1] / TEN_TO_NINETY), "blur_sigma_sharp_px": float(q[0] / TEN_TO_NINETY)})
    return out


def jpeg_quality(path) -> int | None:
    """The quality a JPEG was saved at, estimated from its brightness table against the standard one (the Independent
    JPEG Group's scaling); None if the file has no such table."""
    from PIL import Image

    standard = (16, 11, 10, 16, 24, 40, 51, 61, 12, 12, 14, 19, 26, 58, 60, 55, 14, 13, 16, 24, 40, 57, 69, 56, 14, 17, 22, 29, 51, 87, 80, 62,
                18, 22, 37, 56, 68, 109, 103, 77, 24, 35, 55, 64, 81, 104, 113, 92, 49, 64, 78, 87, 103, 121, 120, 101, 72, 92, 95, 98, 112, 100, 103, 99)
    with Image.open(path) as im:
        tables = getattr(im, "quantization", None)
    if not tables or 0 not in tables:
        return None
    scale = 100.0 * sum(tables[0]) / sum(standard)                               # a sum doesn't care which order the table is kept in
    return int(round(max(1.0, min(100.0, (200.0 - scale) / 2.0 if scale <= 100.0 else 5000.0 / scale))))


def measure_photo(path: Path, frame: dict) -> dict:
    out = measure_framed(load(path), frame)
    out["camera"]["jpeg_quality"] = jpeg_quality(path)
    return out


def lines_picture(img: np.ndarray, roi: np.ndarray | None, path: Path) -> None:
    """The traced centre lines alone, black on white, for checking the instrument by eye.  Made from a reference photo it is
    a tracing of that photo: keep it on this PC, out of the repository and out of every report."""
    from PIL import Image

    mask, angle, _, thick, _ = fine_lines(img, roi)
    out = np.full(mask.shape + (3,), 255, np.uint8)
    out[thick] = (200, 200, 200)
    out[mask & (angle <= NEAR_DEG)] = (200, 0, 0)
    out[mask & (angle > NEAR_DEG)] = (0, 0, 0)
    if roi is not None:
        out[~roi] = (235, 240, 255)
    Image.fromarray(out).save(path)


def table(numbers: Path) -> None:
    """The photos' numbers as a table: one row a photo, then the mean and the range of each kind."""
    rows = json.loads(numbers.read_text(encoding="utf-8"))["photos"]

    def cells(r: dict) -> list:
        t, run, o = r.get("tips") or {}, r.get("hanging_run") or {}, r.get("outline") or {}
        return [r.get("near_vertical_share"), r.get("near_vertical_share_strict"), r.get("near_level_share"), t.get("told"), t.get("down_share"), t.get("up_share"),
                run.get("mean_over_height"), run.get("p90_over_height"), run.get("longest_over_height"), o.get("width_over_height"), o.get("widest_at"),
                r.get("fringe_low_at"), r.get("frame_low_at"), r.get("tree_height_px"), r.get("fine_line_px"),
                (r.get("camera") or {}).get("blur_sigma_px"), (r.get("camera") or {}).get("blur_sigma_sharp_px"), (r.get("camera") or {}).get("edges"),
                (r.get("camera") or {}).get("grain_share_of_contrast"), (r.get("camera") or {}).get("jpeg_quality")]

    places = (3, 3, 3, 0, 2, 2, 3, 3, 3, 2, 2, 2, 2, 0, 0, 2, 2, 0, 4, 0)
    print("| Photo | Kind | Near vertical | strict | Near level | Tips told | down | up | Run over height, mean | p90 | longest | Width over height | widest at | Fringe reaches down to | Frame ends at | Tree (px) | Fine line (px) | Blur, median edge (px) | sharpest quarter | Edges | Grain | JPEG quality |")
    print("|---" * 22 + "|")
    for name, r in rows.items():
        kind = r["kind"] + (", young" if r["young"] else "")
        print(f"| {Path(name).stem} | {kind} | " + " | ".join("-" if v is None else f"{v:.{p}f}" for v, p in zip(cells(r), places)) + " |")
    for kind in dict.fromkeys(r["kind"] for r in rows.values()):
        group = [cells(r) for r in rows.values() if r["kind"] == kind]
        line = []
        for k, p in enumerate(places):
            v = [g[k] for g in group if g[k] is not None]
            line.append("-" if not v else f"{sum(v) / len(v):.{p}f} ({min(v):.{p}f}-{max(v):.{p}f})")
        print(f"| mean of {len(group)} | {kind} | " + " | ".join(line) + " |")


def main(argv=None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("what", choices=("photos", "picture", "table"))
    ap.add_argument("file", nargs="?")
    ap.add_argument("--base-y", type=float, help="the tree's base, as a share of the picture's height from its top edge")
    ap.add_argument("--top-y", type=float, help="the tree's top, the same way")
    ap.add_argument("--frames", default=str(FRAMES), help="the boxes to read on each reference photo")
    ap.add_argument("--out", help="photos: write the numbers here as JSON (numbers only)")
    ap.add_argument("--lines-dir", help="also save each picture's traced lines there; from a reference photo, keep them on this PC")
    a = ap.parse_args(argv)
    if a.what == "table":
        table(Path(a.file or NUMBERS))
        return 0
    if a.what == "picture":
        img = load(a.file)
        h = img.shape[0]
        print(json.dumps(measure(img, None, None if a.base_y is None else a.base_y * h, None if a.top_y is None else a.top_y * h), indent=1))
        if a.lines_dir:
            lines_picture(img, None, Path(a.lines_dir) / (Path(a.file).stem + "_lines.png"))
        return 0
    frames = json.loads(Path(a.frames).read_text(encoding="utf-8"))["photos"]
    rows = {}
    for name, frame in frames.items():
        rows[name] = measure_photo(ROOT / "reference" / name, frame)
        if a.lines_dir:
            img = load(ROOT / "reference" / name)
            lines_picture(img, frame_mask(img.shape, frame), Path(a.lines_dir) / (Path(name).stem + "_lines.png"))
        r = rows[name]
        t = r["tips"]
        print(f"{name}: near vertical {r['near_vertical_share']:.3f} (strict {r['near_vertical_share_strict'] or 0:.3f}), near level {r['near_level_share']:.3f}, "
              f"tips told {t['told']}, down {t['down_share'] or 0:.2f}, up {t['up_share'] or 0:.2f}", flush=True)
    if a.out:
        settings = {k: globals()[k] for k in ("SIGMA_PX", "LINE_MIN", "LINE_STRICT", "CENTRE_PX", "THICK_EDGE", "THICK_MIN_PX", "NEAR_DEG", "HANG_DEG",
                                              "MIN_LINE_PX", "MIN_CHAIN_PX", "TIP_SPAN_PX", "FREE_PX", "JOIN_PX",
                                              "EDGE_REACH_PX", "EDGE_FLAT_PX", "EDGE_MIN", "EDGE_SLOPE_MIN", "EDGE_FLAT", "QUIET_SLOPE")}
        note = ("Numbers read from the reference photos by tools/hang_photo.py, inside the boxes of reference/betula_pendula/hang_photo_frames.json. "
                "window: those boxes in tree heights from the foot of the stem (window_of), which tools/hang_run.py lays on the model's picture. "
                "camera: how soft and grainy the photo is (sharpness) and the quality its JPEG was saved at. "
                "Numbers only: the photos stay on the owner's PC (reference/CREDITS.md).")
        Path(a.out).write_text(json.dumps({"note": note, "instrument": "tools/hang_photo.py", "settings": settings, "photos": rows}, indent=1) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
