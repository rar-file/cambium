"""A leafless picture of a model tree from the side, drawn the way a photo holds a bare tree against the sky, for
tools/hang_photo.py to read.

It is the preview renderer's drawing (treegen/preview.py: one line per internode, as wide as its wood), with three
changes so the picture's fine twigs behave as a photo's do:

- the tree is drawn a set number of pixels tall (TREE_PX, or the height of a reference photo's own tree);
- no line is drawn wider than its wood.  The previews' floor of 0.3 pt is left out, so wood narrower than a pixel only
  darkens it by the share it covers, as in a photo scaled down from a larger one;
- nothing is snapped to the pixel grid.

Black wood on a white sky, no leaves, no ground.  By default the view is level and from far away (no perspective).
With `camera` it is a person's view from the ground: an eye 1.6 m up, that many tree heights from the stem, looking up
at the middle of the tree, with perspective.  Every reference photo was taken that way, from an unknown distance.
"""
from __future__ import annotations

import math

import matplotlib

matplotlib.use("Agg")
import numpy as np  # noqa: E402
from matplotlib.backends.backend_agg import FigureCanvasAgg  # noqa: E402
from matplotlib.collections import LineCollection  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402

TREE_PX = 1200     # the tree's height in the picture; the four reference photos with a whole tree are 830-1470 px tall
MARGIN_PX = 24
DPI = 100
VIEWS = {"east": 0, "north": 1}   # the sideways axis of each view
EYE_M = 1.6        # a ground camera's height
RENDER_SIGMA_PX = 0.3   # how soft this drawing's own edges read by tools/hang_photo.py's sharpness(); a test holds it


def segments(g):
    """The living internodes of a tools/hang_measure.py Geometry: near ends, far ends, radii (m)."""
    idx = np.nonzero(g.alive & (g.parent >= 0))[0]
    return g.pos[g.parent[idx]].astype(float), g.pos[idx].astype(float), g.radius[idx].astype(float)


def _from_the_ground(p0: np.ndarray, p1: np.ndarray, r: np.ndarray, axis: int, distance_heights: float, foot: np.ndarray):
    """Both ends of every internode and its width as a ground camera sees them, restated so that the foot of the stem is
    at height 0 and the highest twig in the picture at the tree's own height: the units are then metres at the stem."""
    top = float(max(p0[:, 2].max(), p1[:, 2].max()))
    depth = 1 - axis
    away = distance_heights * top
    pitch = math.atan2(0.5 * top - EYE_M, away)             # looking at the middle of the tree
    cos, sin = math.cos(pitch), math.sin(pitch)

    def seen(p):
        s, t, z = p[:, axis] - foot[axis], p[:, depth] - foot[depth] + away, p[:, 2] - EYE_M
        ahead = t * cos + z * sin
        return s / ahead, (z * cos - t * sin) / ahead, ahead

    x0, y0, d0 = seen(p0)
    x1, y1, d1 = seen(p1)
    _, y_foot, _ = seen(np.array([[foot[0], foot[1], 0.0]]))
    k = top / (float(max(y0.max(), y1.max())) - float(y_foot[0]))
    a = np.stack([foot[axis] + k * x0, k * (y0 - y_foot[0])], axis=1)
    b = np.stack([foot[axis] + k * x1, k * (y1 - y_foot[0])], axis=1)
    return a, b, r * k / (0.5 * (d0 + d1))


def draw(p0: np.ndarray, p1: np.ndarray, r: np.ndarray, view: str = "east", tree_px: int = TREE_PX, camera: float | None = None, foot=None):
    """The picture, as grey levels 0-255 (rows from the top), and where the tree sits in it: the pixel rows of its base and
    its top, the pixel columns of the foot of its stem and of its highest twig, and the scale.
    camera: None for the level view from far away; else a ground camera's distance from the stem, in tree heights.
    foot: where the stem meets the ground (m); the origin if not given."""
    axis = VIEWS[view]
    foot = np.zeros(3) if foot is None else np.asarray(foot, dtype=float)
    top = float(max(p0[:, 2].max(), p1[:, 2].max()))
    ppm = tree_px / top
    if camera is None:
        a, b, wide = p0[:, [axis, 2]], p1[:, [axis, 2]], r
        below_px = 0
    else:
        a, b, wide = _from_the_ground(p0, p1, r, axis, float(camera), foot)
        # wood nearer than the stem can show below its foot
        below_px = int(math.ceil(max(0.0, -float(min(a[:, 1].min(), b[:, 1].min()))) * ppm))
    lo = float(min(a[:, 0].min(), b[:, 0].min()))
    hi = float(max(a[:, 0].max(), b[:, 0].max()))
    w_px = int(math.ceil((hi - lo) * ppm)) + 2 * MARGIN_PX
    h_px = int(tree_px) + 2 * MARGIN_PX + below_px
    # a hair over, so rounding can never cost the picture a row or a column
    fig = Figure(figsize=((w_px + 0.01) / DPI, (h_px + 0.01) / DPI), dpi=DPI, facecolor="white")
    canvas = FigureCanvasAgg(fig)
    ax = fig.add_axes([0.0, 0.0, 1.0, 1.0])
    ax.set_xlim(lo - MARGIN_PX / ppm, lo - MARGIN_PX / ppm + w_px / ppm)
    ax.set_ylim(-(MARGIN_PX + below_px) / ppm, (h_px - MARGIN_PX - below_px) / ppm)
    ax.axis("off")
    seg = np.stack([a, b], axis=1)
    wide_px = 2.0 * wide * ppm
    points = wide_px * 72.0 / DPI
    order = np.argsort(-wide)
    # wood a pixel wide or more gets round ends, so a limb drawn as many short pieces has no seams; finer wood gets
    # square ends, so overlapping ends don't darken it
    for part, cap in ((order[wide_px[order] >= 1.0], "round"), (order[wide_px[order] < 1.0], "butt")):
        if part.size:
            lc = LineCollection(seg[part], linewidths=points[part], colors="black", capstyle=cap, antialiaseds=True)
            lc.set_snap(False)
            ax.add_collection(lc)
    canvas.draw()
    grey = np.asarray(canvas.buffer_rgba())[:, :, 0].copy()
    ends = np.concatenate([a, b])
    highest = ends[int(np.argmax(ends[:, 1]))]
    base_y = float(h_px - MARGIN_PX - below_px)
    return grey, {"base_y": base_y, "top_y": base_y - top * ppm, "px_per_m": ppm,
                  "base_x": MARGIN_PX + (float(foot[axis]) - lo) * ppm, "top_x": MARGIN_PX + (float(highest[0]) - lo) * ppm}


def like_a_photo(grey: np.ndarray, seed: int = 0, blur_px: float = 0.7, contrast: float = 0.65, grain: float = 0.01, quality: int = 85) -> np.ndarray:
    """The picture as a camera might hand it over: softened (a Gaussian blur of blur_px), at this share of its contrast,
    with grain (this share of full range), saved as a JPEG of this quality and read back.  The defaults are guesses, a
    check that the reading survives what a photo does to fine twigs.  as_photo() uses a reference photo's own measured
    figures instead."""
    import io

    from PIL import Image
    from scipy import ndimage

    soft = grey.astype(np.float64) / 255.0
    if blur_px > 0.0:
        soft = ndimage.gaussian_filter(soft, blur_px)
    soft = 0.2 + contrast * soft + np.random.default_rng(seed).normal(0.0, grain, soft.shape)
    buf = io.BytesIO()
    Image.fromarray(np.clip(np.rint(soft * 255.0), 0, 255).astype(np.uint8)).save(buf, format="JPEG", quality=quality)
    buf.seek(0)
    with Image.open(buf) as im:
        return np.asarray(im.convert("L")).copy()


def as_photo(grey: np.ndarray, camera: dict, seed: int = 0) -> np.ndarray:
    """The picture made as soft and as grainy as one reference photo was measured to be (tools/hang_photo.py, sharpness:
    the photo's `camera` numbers), and saved at that photo's JPEG quality.  The blur added is what the photo's median
    edge shows beyond this drawing's own softness; that is the heavier of the two figures measured, so it errs towards
    losing twigs."""
    sigma = float(camera.get("blur_sigma_px") or 0.0)
    contrast = 0.65
    return like_a_photo(grey, seed, math.sqrt(max(sigma * sigma - RENDER_SIGMA_PX ** 2, 0.0)), contrast,
                        contrast * float(camera.get("grain_share_of_contrast") or 0.0), int(camera.get("jpeg_quality") or 85))


def save(grey: np.ndarray, path) -> None:
    from PIL import Image

    Image.fromarray(np.ascontiguousarray(grey, dtype=np.uint8)).save(path)
