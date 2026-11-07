"""Procedural bark and leaf textures, generated from the values in the species file.

No photographs go in.  A bark stage is a tile (periodic both ways, sized in metres) built from a
few generic layers, each with its own values: blotches, fibres, lenticels, plates and furrows,
lifted sheets.  A tree's textures are then baked from those tiles, texel by texel, from the state
of the part underneath (``appearance.part_state``), so a stem goes from one stage to the next
through the tile's own pattern, and cracks open before plates form:

* the stem gets its own texture, once around and once along (``bake_stem``);
* branches share an atlas with one column for each circumference class, a whole turn of the branch
  each and repeating along it (``bake_branch_atlas``);
* leaves and bark strips get small alpha-masked textures (``leaf_blade``, ``leaf_card_atlas``,
  ``strip_texture``).

Other species need other values, not other code.  All arrays are linear light, row 0 is v = 0.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.spatial import cKDTree

from .appearance import smooth, srgb_to_linear


# -- periodic noise -------------------------------------------------------------------------------
def noise(shape, seed: int, scale_px, beta: float = 2.0, low_cut: float | None = None) -> np.ndarray:
    """Periodic Gaussian noise, mean 0, sd 1: white noise through a filter with correlation lengths
    ``scale_px`` (y, x), falling off at frequencies above them with slope ``beta``.  ``low_cut``
    also removes what varies over more than that many of those lengths, so the field keeps
    crossing zero and has no broad plateaus."""
    rng = np.random.default_rng(seed)
    h, w = shape
    fy = np.fft.fftfreq(h)[:, None] * scale_px[0]
    fx = np.fft.rfftfreq(w)[None, :] * scale_px[1]
    q = (2.0 * np.pi) ** 2 * (fx * fx + fy * fy)
    filt = (1.0 + q) ** (-beta / 2.0)
    if low_cut:
        filt = filt * (1.0 - 1.0 / (1.0 + q * float(low_cut) ** 2))
    f = np.fft.rfft2(rng.standard_normal(shape)) * filt
    a = np.fft.irfft2(f, s=shape)
    return ((a - a.mean()) / max(a.std(), 1e-12)).astype(np.float32)


def rank01(a: np.ndarray) -> np.ndarray:
    """Values replaced by their rank, 0-1: the share of the field below each point, so a threshold
    at 1 - c marks a share c of the surface."""
    out = np.empty(a.size, np.float32)
    out[np.argsort(a, axis=None)] = np.linspace(0.0, 1.0, a.size, dtype=np.float32)
    return out.reshape(a.shape)


def _lenticels(shape, tile_m: float, seed: int, cfg: dict):
    """Lens-shaped horizontal dashes: (mask, rim).  Clustered in rows, more small than large."""
    h, w = shape
    px = tile_m / w
    rng = np.random.default_rng(seed)
    n = int(float(cfg["per_m2"]) * tile_m * tile_m)
    mask = np.zeros(shape, np.float32)
    rim = np.zeros(shape, np.float32)
    bands = rank01(noise((h, 1), seed + 1, (0.02 / px, 1.0), 1.5))[:, 0]
    rough_edge = rank01(noise((1, w), seed + 2, (1.0, 0.004 / px), 1.8))[0]
    placed = 0
    while placed < n:
        y0 = rng.uniform(0, h)
        if rng.random() > 0.25 + 0.75 * float(bands[int(y0) % h]):
            continue
        placed += 1
        x0 = rng.uniform(0, w)
        u = rng.random()
        L = cfg["length_m"][0] * (cfg["length_m"][1] / cfg["length_m"][0]) ** (u * u) / px
        H = (cfg["height_m"][0] + (cfg["height_m"][1] - cfg["height_m"][0]) * u) / px * rng.uniform(0.8, 1.2)
        tilt = rng.normal(0.0, 0.05)
        ri = int(L / 2 + 3)
        rj = int(H + abs(tilt) * L + 3)
        xs = np.arange(-ri, ri + 1)
        ys = np.arange(-rj, rj + 1)
        X, Y = np.meshgrid(xs + (int(x0) - x0), ys + (int(y0) - y0))
        Y = Y - tilt * X
        t = np.clip(2.0 * np.abs(X) / max(L, 1.0), 0.0, 1.0)
        half = 0.5 * H * (1.0 - t * t) ** 0.7 * (0.75 + 0.5 * rough_edge[(xs + int(x0)) % w, None].reshape(1, -1)) + 1e-3
        d = np.abs(Y) / half
        m = np.clip(1.5 - d * 1.5, 0.0, 1.0) * (t < 1.0)
        r = np.exp(-((d - 1.35) / 0.55) ** 2) * (t < 1.0)
        iy = (ys + int(y0)) % h
        ix = (xs + int(x0)) % w
        mask[np.ix_(iy, ix)] = np.maximum(mask[np.ix_(iy, ix)], m.astype(np.float32))
        rim[np.ix_(iy, ix)] = np.maximum(rim[np.ix_(iy, ix)], r.astype(np.float32))
    return mask, rim


def _plates(shape, tile_m: float, seed: int, cfg: dict):
    """Plates split by furrows.  Furrows are the zero lines of noise stretched along the stem, which
    join and part as fissures do; a finer set makes shallower ones, and breaks across the plates
    make blocks.  Returns (height 0 furrow floor .. 1 plate top, furrow share 1 in a furrow)."""
    px = tile_m / shape[1]
    sx, sy = cfg["size_m"]
    fw = float(cfg["furrow_width"])
    main = np.abs(noise(shape, seed, (sy / px, sx / px), 2.6, low_cut=2.5))
    fine = np.abs(noise(shape, seed + 1, (0.5 * sy / px, 0.4 * sx / px), 2.3, low_cut=2.5))
    cross = np.abs(noise(shape, seed + 2, (0.12 * sy / px, 0.35 * sy / px), 2.2))
    grit = noise(shape, seed + 3, (0.006 / px, 0.004 / px), 1.5)
    tall = 0.72 + 0.28 * rank01(noise(shape, seed + 4, (0.25 * sy / px, 0.9 * sx / px), 2.4))
    deep = smooth(0.05, fw, main)
    mid = smooth(0.0, 0.8 * fw, fine)
    blocks = smooth(0.0, 0.4 * fw, cross)
    k = float(cfg["cross_crack"])
    height = tall * deep * (0.35 + 0.65 * mid) * (1.0 - k * (1.0 - blocks) * 0.6)
    height = height + 0.05 * grit * deep
    height = np.clip(height, 0.0, 1.0)
    return height.astype(np.float32), (1.0 - np.minimum(height / np.maximum(tall, 1e-3), 1.0)).astype(np.float32)


# -- one stage's tile -----------------------------------------------------------------------------
# channels of a tile
ALB = slice(0, 3)
H_ABS, H_REL, ROUGH, REVEAL, PEEL, GRIME, PATCH = 3, 4, 5, 6, 7, 8, 9
N_CHANNELS = 10


@dataclass
class Tile:
    name: str
    px: float                  # m per texel
    mips: list                 # arrays (H, W, channels), each half the size of the last
    under: np.ndarray          # peeled layers, colours (layers x 3) linear; may be empty
    layer_m: float
    soft: float = 0.1          # how gradually this stage comes through its pattern, 0-1

    @property
    def mean_colour(self) -> np.ndarray:
        return self.mips[-1].reshape(-1, N_CHANNELS)[:, ALB].mean(0)


def _mip_chain(a: np.ndarray) -> list:
    out = [a]
    while min(out[-1].shape[:2]) > 4:
        b = out[-1]
        out.append(0.25 * (b + np.roll(b, -1, 0) + np.roll(b, -1, 1) + np.roll(np.roll(b, -1, 0), -1, 1))[::2, ::2])
    return out


def make_tile(stage: dict, tile_m: float, px_count: int, seed: int) -> Tile:
    """A stage's tile from its values: every layer is optional, so any species fits."""
    shape = (px_count, px_count)
    px = tile_m / px_count
    a = np.zeros(shape + (N_CHANNELS,), np.float32)
    c0, c1 = srgb_to_linear(stage["colour"]), srgb_to_linear(stage["colour_variation"])
    bl = stage["blotch_m"]
    blotch = noise(shape, seed, (bl[1] / px, bl[0] / px), 2.4)
    fine = noise(shape, seed + 1, (0.004 / px, 0.012 / px), 1.6)
    t = np.clip(0.5 + 0.38 * blotch + 0.14 * fine, 0.0, 1.0)[..., None]
    a[..., ALB] = c0 + (c1 - c0) * t
    a[..., ROUGH] = float(stage["roughness"]) + 0.05 * fine
    # fibres: long and fine, across the stem, as paper layers and stretch marks are; they wander a
    # little up and down, as rings of paper do, and vary in strength
    fibre = noise(shape, seed + 2, (0.0016 / px, 0.05 / px), 1.1)
    drift = noise(shape, seed + 12, (0.05 / px, 0.1 / px), 2.4) * (0.006 / px)
    rows = (np.arange(shape[0])[:, None] + drift).astype(np.int64) % shape[0]
    fibre = fibre[rows, np.arange(shape[1])[None, :]]
    strength = 0.45 + 0.55 * rank01(noise(shape, seed + 13, (0.03 / px, 0.14 / px), 2.2))
    a[..., H_ABS] = float(stage["fibre_depth_m"]) * fibre * strength
    a[..., ALB] *= (1.0 + 0.016 * fibre * strength)[..., None]
    if stage.get("lenticels"):
        cfg = stage["lenticels"]
        m, r = _lenticels(shape, tile_m, seed + 3, cfg)
        col = srgb_to_linear(cfg["colour"])
        # the rim of a dark lenticel is lighter and its core varies a little
        vary = 0.8 + 0.4 * rank01(noise(shape, seed + 4, (0.004 / px, 0.012 / px), 1.2))[..., None]
        a[..., ALB] = a[..., ALB] * (1.0 - m[..., None]) + np.minimum(col * vary, 1.0) * m[..., None]
        a[..., H_ABS] += float(cfg["rim_m"]) * r - float(cfg["inset_m"]) * m
        a[..., ROUGH] += 0.15 * m
    a[..., REVEAL] = 0.0
    a[..., H_REL] = 0.0
    if stage.get("plates"):
        cfg = stage["plates"]
        plate, furrow = _plates(shape, tile_m, seed + 5, cfg)
        fc = srgb_to_linear(cfg["furrow_colour"])
        lit = (0.6 + 0.55 * plate)[..., None]
        a[..., ALB] = a[..., ALB] * lit
        dark = (furrow ** 1.6)[..., None]
        a[..., ALB] = a[..., ALB] * (1.0 - dark) + fc * dark
        a[..., H_REL] = plate - 1.0                # 0 on plate tops, -1 at furrow floors
        patchy = rank01(noise(shape, seed + 6, (0.09 / px, 0.03 / px), 2.2))
        # furrows open first, plates cover last
        fine_edge = noise(shape, seed + 15, (0.004 / px, 0.003 / px), 1.4)
        a[..., REVEAL] = np.clip(0.8 * plate ** 1.3 + 0.2 * patchy + 0.035 * fine_edge, 0.0, 1.0)
    elif stage.get("reveal_patch_m"):
        rp = stage["reveal_patch_m"]
        a[..., REVEAL] = rank01(noise(shape, seed + 7, (rp[1] / px, rp[0] / px), 2.2))
    under = np.zeros((0, 3))
    layer_m = 0.0
    if stage.get("peel"):
        cfg = stage["peel"]
        sm = cfg["sheet_m"]
        base = noise(shape, seed + 8, (sm[1] / px, sm[0] / px), 2.6)
        torn = noise(shape, seed + 9, (0.003 / px, 0.02 / px), 1.4)
        a[..., PEEL] = rank01(base + 0.22 * torn)
        under = np.array([srgb_to_linear(c) for c in cfg["under_colours"]])
        layer_m = float(cfg["layer_m"])
    # grime: vertical runs of grey, from rain down the stem
    a[..., GRIME] = rank01(noise(shape, seed + 11, (0.09 / px, 0.012 / px), 2.0))
    a[..., PATCH] = rank01(noise(shape, seed + 14, (0.05 / px, 0.03 / px), 2.2))
    a[..., ALB] = np.clip(a[..., ALB], 0.0, 1.0)
    return Tile(stage["name"], px, _mip_chain(a), under, layer_m, float(stage.get("reveal_softness", 0.1)))


def make_tiles(look: dict) -> list:
    bark = look["bark"]
    seed = int(look["game"]["texture_seed"])
    return [make_tile(st, float(bark["tile_size_m"]), int(bark["tile_px"]), seed + 100 * i) for i, st in enumerate(bark["stages"])]


def _sample(mip: np.ndarray, px: float, x_m: np.ndarray, y_m: np.ndarray) -> np.ndarray:
    """Bilinear, wrapping both ways."""
    h, w = mip.shape[:2]
    x = np.asarray(x_m) / px - 0.5
    y = np.asarray(y_m) / px - 0.5
    x0 = np.floor(x).astype(np.int64)
    y0 = np.floor(y).astype(np.int64)
    fx = (x - x0)[..., None].astype(np.float32)
    fy = (y - y0)[..., None].astype(np.float32)
    x0 %= w
    y0 %= h
    x1 = (x0 + 1) % w
    y1 = (y0 + 1) % h
    return (mip[y0, x0] * (1 - fx) + mip[y0, x1] * fx) * (1 - fy) + (mip[y1, x0] * (1 - fx) + mip[y1, x1] * fx) * fy


def sample_tile(tile: Tile, x_m, y_m, texel_m: np.ndarray) -> np.ndarray:
    """A tile at world positions, from the mip level matching the size a texture's texel covers
    there, so a coarse bake averages its pattern and doesn't alias it.  ``texel_m``: per row."""
    lvl = np.clip(np.round(np.log2(np.maximum(texel_m, 1e-9) / tile.px)).astype(np.int64), 0, len(tile.mips) - 1)
    out = np.zeros(np.shape(x_m) + (N_CHANNELS,), np.float32)
    for k in np.unique(lvl):
        rows = np.nonzero(lvl == k)[0]
        out[rows] = _sample(tile.mips[int(k)], tile.px * 2 ** int(k), x_m[rows], y_m[rows])
    return out


def _wrapped(tile: Tile, x_m, y_m, circ, texel_m, seam=0.14):
    """A tile around a tube of circumference ``circ`` (per row): x runs 0 to circ, and the last part
    of the way cross-fades into the pattern at the start, so the seam doesn't show and the tile
    keeps its true size in metres at any radius."""
    a = sample_tile(tile, x_m, y_m, texel_m)
    frac = x_m / np.maximum(circ, 1e-9)
    f = np.clip((frac - (1.0 - seam)) / seam, 0.0, 1.0)
    idx = f > 0
    if idx.any():
        b = sample_tile(tile, x_m - circ, y_m, texel_m)
        a[idx] = a[idx] * (1 - f[idx, None]) + b[idx] * f[idx, None]
    return a


def compose(tiles: list, samples: list, state: dict, shape) -> dict:
    """Lay the stages over each other, texel by texel.  ``samples``: each stage's tile sampled at
    this texture's texels.  ``state``: from part_state, per row or per texel."""
    def field(x):
        x = np.asarray(x, np.float32)
        return x if x.ndim == 2 else np.broadcast_to(x[:, None] if x.ndim == 1 else x, shape)

    S = samples[0]
    alb = S[..., ALB].copy()
    rough = S[..., ROUGH].copy()
    height = S[..., H_ABS].copy()
    W = state["weights"]
    fissure = field(state["fissure_m"])
    peel = field(state["peel"])
    grime = field(state["grime"])
    for i in range(1, len(tiles)):
        S = samples[i]
        w = field(W[i])
        a_i = S[..., ALB].copy()
        h_i = S[..., H_ABS] + S[..., H_REL] * fissure
        r_i = S[..., ROUGH]
        if len(tiles[i].under):
            # sheets lift in layers: the deeper the layer the smaller its share
            total = 0.0
            for k, col in enumerate(tiles[i].under):
                share = peel * 0.42 ** k
                m = smooth(1.0 - share - 0.012, 1.0 - share + 0.012, S[..., PEEL]) * (share > 0)
                a_i = a_i + (col.astype(np.float32) - a_i) * m[..., None]
                total = total + m
            h_i = h_i - tiles[i].layer_m * total
        reveal = S[..., REVEAL]
        soft = tiles[i].soft
        cover = smooth(reveal * (1.0 - soft), reveal * (1.0 - soft) + soft, w)
        alb = alb + (a_i - alb) * cover[..., None]
        rough = rough + (r_i - rough) * cover
        height = height + (h_i - height) * cover
    g = (grime * (0.35 + 0.9 * samples[min(1, len(samples) - 1)][..., GRIME]))[..., None]
    alb = alb * (1.0 - g) + alb * np.array([0.42, 0.40, 0.38], np.float32) * g
    return {"albedo": np.clip(alb, 0.0, 1.0), "rough": np.clip(rough, 0.03, 1.0), "height": height}


def _box_u(a, r):
    """Moving average, wrapping across columns and clamped across rows, width 2 r + 1."""
    c = np.cumsum(np.concatenate([a[:, -r - 1:], a, a[:, :r]], axis=1), axis=1, dtype=np.float64)
    return ((c[:, 2 * r + 1:] - c[:, :-2 * r - 1]) / (2 * r + 1)).astype(np.float32)


def _box_v(a, r):
    p = np.concatenate([np.repeat(a[:1], r + 1, 0), a, np.repeat(a[-1:], r, 0)], axis=0)
    c = np.cumsum(p, axis=0, dtype=np.float64)
    return ((c[2 * r + 1:] - c[:-2 * r - 1]) / (2 * r + 1)).astype(np.float32)


def finish(maps: dict, dx_m: np.ndarray, dy_m: np.ndarray, wrap_v: bool = False) -> dict:
    """Normal, occlusion and height maps from a surface in metres.  dx_m and dy_m: the size of a
    texel across and along, by row.  Normal map: +x along u, +y towards v = 0 (the glTF convention)."""
    h = maps["height"]
    dx = np.broadcast_to(np.asarray(dx_m, np.float32)[:, None], h.shape)
    dy = np.broadcast_to(np.asarray(dy_m, np.float32)[:, None], h.shape)
    if wrap_v:
        dhdr = 0.5 * (np.roll(h, -1, 0) - np.roll(h, 1, 0))
    else:
        dhdr = np.gradient(h, axis=0)
    dhdc = 0.5 * (np.roll(h, -1, 1) - np.roll(h, 1, 1))
    nx = -dhdc / np.maximum(dx, 1e-6)
    ny = dhdr / np.maximum(dy, 1e-6)
    # a steep crack edge shouldn't flip the normal; it's detail, not geometry
    nx, ny = np.clip(nx, -2.5, 2.5), np.clip(ny, -2.5, 2.5)
    nz = np.ones_like(nx)
    ln = np.sqrt(nx * nx + ny * ny + nz * nz)
    normal = np.stack([nx / ln, ny / ln, nz / ln], -1)
    # cavities: lower than the area around them
    r = 6
    blur = _box_v(_box_u(h, r), r) if not wrap_v else np.roll(_box_v(_box_u(np.roll(h, h.shape[0] // 2, 0), r), r), -h.shape[0] // 2, 0)
    cav = blur - h
    scale = max(float(np.percentile(np.abs(cav), 99.0)), 2e-4)
    ao = np.clip(1.0 - 0.8 * cav / scale, 0.35, 1.0).astype(np.float32)
    out = dict(maps)
    out["normal"] = normal.astype(np.float32)
    out["ao"] = ao
    return out


# -- stem and branch bakes ------------------------------------------------------------------------
@dataclass
class StemProfile:
    """The stem, read from its mesh: stem position s (m from the ground) and what's at each."""
    s: np.ndarray
    radius: np.ndarray       # over bark, m
    part_age: np.ndarray
    d_wood: np.ndarray
    z: np.ndarray


def _stem_rows(look: dict, length: float):
    """Heights and the share of texture rows below each: more rows near the ground, the same rows
    for the same place at any age once the stem has passed them."""
    z = [0.0]
    v = [0.0]
    for height, share in look["bark"]["stem_rows"]:
        if height < length:
            z.append(float(height))
            v.append(float(share))
    z.append(float(length))
    v.append(1.0)
    return np.asarray(z), np.asarray(v)


def stem_v(look: dict, s, length: float):
    """Texture row (0-1) for a position up the stem."""
    z, v = _stem_rows(look, length)
    return np.interp(s, z, v)


def stem_s(look: dict, v, length: float):
    """The inverse of stem_v."""
    z, vv = _stem_rows(look, length)
    return np.interp(v, vv, z)


def bake_stem(look: dict, tiles: list, profile: StemProfile, part_state_fn, marks: list, px=None, block: int = 512) -> dict:
    """The stem's own texture, baked from the state at every row.  ``marks``: (around 0-1, s, branch
    radius) of each branch that leaves the stem, living or shed, for the dark chevrons.

    A tile goes around the stem a whole number of times, so it meets itself at the seam.  The count
    depends only on the circumference: 1 turn in a tile's width on any stem up to one tile around,
    then 2 turns' worth, 4, and so on.  So a pattern stays where it is on the stem as it thickens
    and widens with it, as lenticels and plates do, and patch by patch the stem takes up the next,
    finer count as it grows.  That is what keeps one age in line with the next."""
    bark = look["bark"]
    W, H = px or bark["stem_texture_px"]
    tile_m = float(bark["tile_size_m"])
    length = float(profile.s[-1])
    v = (np.arange(H) + 0.5) / H
    s = stem_s(look, v, length)
    r = np.interp(s, profile.s, profile.radius)
    circ = 2.0 * np.pi * np.maximum(r, 1e-4)
    state = part_state_fn(np.interp(s, profile.s, profile.part_age), np.interp(s, profile.s, profile.d_wood), np.interp(s, profile.s, profile.z))
    dy = np.gradient(s)
    dx = circ / W
    u = (np.arange(W) + 0.5) / W
    level = np.log2(np.maximum(circ, tile_m) / tile_m)
    low = np.floor(level)
    share = (level - low).astype(np.float32)
    ka = tile_m * 2.0 ** low
    alb = np.zeros((H, W, 3), np.float32)
    rough = np.zeros((H, W), np.float32)
    height = np.zeros((H, W), np.float32)
    edge = 0.3
    # each tile's height of stem takes the tile from its own random offset, handed over patch by patch
    # at the end of the band, so nothing repeats up the stem
    from .appearance import hash01
    seed = int(look["game"]["texture_seed"])
    band = np.floor(s / tile_m).astype(np.int64)
    frac = s / tile_m - band
    ox, oy = hash01(band + seed, 61) * tile_m, hash01(band + seed, 62) * tile_m
    ox2, oy2 = hash01(band + 1 + seed, 61) * tile_m, hash01(band + 1 + seed, 62) * tile_m
    hand_over = 0.82
    for start in range(0, H, block):
        rows = np.arange(start, min(start + block, H))
        n = len(rows)
        y = np.broadcast_to(s[rows, None], (n, W))
        patch = sample_tile(tiles[0], np.broadcast_to(u[None, :] * tile_m, (n, W)), y, np.maximum(tile_m / W, dy[rows]))[..., PATCH]
        mix = smooth(patch, patch + edge, share[rows, None] * (1.0 + edge))[..., None]
        xa = u[None, :] * ka[rows, None]
        near = np.nonzero(frac[rows] > hand_over)[0]
        over = smooth(patch[near], patch[near] + edge, ((frac[rows][near, None] - hand_over) / (1.0 - hand_over)) * (1.0 + edge))[..., None]

        def fetch(t, rr, ox_, oy_):
            sa = sample_tile(t, xa[rr] + ox_[rows][rr, None], y[rr] + oy_[rows][rr, None], np.maximum(ka[rows][rr] / W, dy[rows][rr]))
            if share[rows][rr].max(initial=0.0) > 0.0:
                sb = sample_tile(t, 2.0 * xa[rr] + ox_[rows][rr, None], y[rr] + oy_[rows][rr, None], np.maximum(2.0 * ka[rows][rr] / W, dy[rows][rr]))
                sa = sa + (sb - sa) * mix[rr]
            return sa

        everyone = np.arange(n)
        samples = []
        for t in tiles:
            sa = fetch(t, everyone, ox, oy)
            if near.size:
                sa[near] = sa[near] + (fetch(t, near, ox2, oy2) - sa[near]) * over
            samples.append(sa)
        st = {"weights": state["weights"][:, rows], "fissure_m": state["fissure_m"][rows], "peel": state["peel"][rows], "grime": state["grime"][rows]}
        m = compose(tiles, samples, st, (n, W))
        alb[rows] = m["albedo"]
        rough[rows] = m["rough"]
        height[rows] = m["height"]
    maps = {"albedo": alb, "rough": rough, "height": height}
    _paint_marks(look, maps, marks, length, circ, dy, W, H)
    out = finish(maps, dx, dy)
    out["texel_m"] = (dx, dy)
    out["height_range_m"] = (float(out["height"].min()), float(out["height"].max()))
    out["length_m"] = length
    return out


def _paint_marks(look: dict, maps: dict, marks: list, length: float, circ: np.ndarray, dy: np.ndarray, W: int, H: int):
    """A dark mark at each branch: two arms that rise from the sides to a peak above it, like a
    drooping moustache, and a collar round the branch, raised, rough and dark.  Never thinner than the
    texture can hold, so a mark on the coarse part of the stem stays a clean line."""
    cfg = look["bark"].get("marks")
    if not cfg:
        return
    col = srgb_to_linear(cfg["colour"]).astype(np.float32)
    rmin = float(cfg["min_branch_radius_m"])
    wid, tall = float(cfg["chevron_width"]), float(cfg["chevron_height"])
    s_row = np.cumsum(dy) - dy[0] * 0.5
    for around, s0, rb in marks:
        if rb < rmin or s0 >= length:
            continue
        v0 = float(stem_v(look, s0, length))
        row0 = int(v0 * H)
        if not 0 <= row0 < H:
            continue
        c = float(circ[row0])
        half_w = min(wid * rb, 0.35 * c)
        drop = tall * 2.0 * rb
        peak = 1.3 * rb
        stroke = max(0.38 * rb, 1.4 * float(dy[row0]))
        lo = max(int(np.searchsorted(s_row, s0 + peak - drop - 2.0 * stroke)), 0)
        hi = min(int(np.searchsorted(s_row, s0 + peak + 2.0 * stroke)) + 1, H)
        if hi <= lo:
            continue
        col_half = min(int(half_w / c * W) + 2, W // 2)
        cols = np.arange(int(around * W) - col_half, int(around * W) + col_half + 1)
        rr = np.arange(lo, hi)
        X = ((cols + 0.5) / W - around)[None, :] * c
        Y = (s_row[rr] - s0)[:, None]
        t = np.clip(np.abs(X) / max(half_w, 1e-6), 0.0, 1.0)
        # the arm's line: from the peak, down and out, curving away
        line = peak - drop * t ** 1.4
        band = np.exp(-((Y - line) / stroke) ** 2) * (1.0 - t ** 3)
        ring = np.exp(-((np.hypot(X, Y) - 1.05 * rb) / max(0.35 * rb, 1.4 * float(dy[row0]))) ** 2)
        m = np.clip(np.maximum(band, 0.8 * ring), 0.0, 1.0).astype(np.float32)
        ix = np.ix_(rr, cols % W)
        maps["albedo"][ix] = maps["albedo"][ix] + (col - maps["albedo"][ix]) * m[..., None]
        maps["rough"][ix] = maps["rough"][ix] + (0.88 - maps["rough"][ix]) * m
        maps["height"][ix] = maps["height"][ix] + 0.0015 * m


def atlas_layout(look: dict, px=None) -> list:
    """Branch atlas columns: (left, right, top) texel positions and circumference for each class."""
    bark = look["bark"]
    W, H = px or bark["atlas_px"]
    tile_px = float(bark["tile_size_m"]) / float(H)
    pad = 4
    out = []
    x = pad
    total = sum(c / tile_px for c in bark["branch_circumference_m"]) + 2 * pad * len(bark["branch_circumference_m"])
    shrink = min(1.0, (W - 1.0) / total)
    for c in bark["branch_circumference_m"]:
        w = max(int(c / tile_px * shrink), 8)
        out.append((x, x + w, float(c)))
        x += w + 2 * pad
    return out


def bake_branch_atlas(look: dict, tiles: list, states: list, px=None) -> dict:
    """One column per circumference class, from ``states``: the mean state of the parts in the class
    (or None).  Each column is a whole turn of a branch and repeats along it."""
    bark = look["bark"]
    W, H = px or bark["atlas_px"]
    layout = atlas_layout(look, (W, H))
    alb = np.zeros((H, W, 3), np.float32)
    rough = np.ones((H, W), np.float32) * 0.6
    height = np.zeros((H, W), np.float32)
    tile_m = float(bark["tile_size_m"])
    means = []
    dy = tile_m / H
    y = (np.arange(H) + 0.5) * dy
    for (x0, x1, c), st in zip(layout, states):
        w = x1 - x0
        dx = c / w
        X = np.broadcast_to(((np.arange(w) + 0.5) * dx)[None, :], (H, w))
        Y = np.broadcast_to(y[:, None], (H, w))
        circ = np.full((H, w), c)
        texel = np.full(H, max(dx, dy))
        samples = [_wrapped(t, X, Y, circ, texel) for t in tiles]
        state = st or {"weights": np.array([1.0] + [0.0] * (len(tiles) - 1)), "fissure_m": 0.0, "peel": 0.0, "grime": 0.0}
        fields = {"weights": [np.full((H, w), float(a), np.float32) for a in np.ravel(state["weights"])],
                  "fissure_m": np.full((H, w), float(state["fissure_m"]), np.float32),
                  "peel": np.full((H, w), float(state["peel"]), np.float32),
                  "grime": np.full((H, w), float(state["grime"]), np.float32)}
        m = compose(tiles, samples, fields, (H, w))
        alb[:, x0:x1] = m["albedo"]
        rough[:, x0:x1] = m["rough"]
        height[:, x0:x1] = m["height"]
        for p in range(1, 5):                # bleed each column's edge into its padding
            if x0 - p >= 0:
                alb[:, x0 - p] = m["albedo"][:, 0]
                rough[:, x0 - p] = m["rough"][:, 0]
                height[:, x0 - p] = m["height"][:, 0]
            if x1 - 1 + p < W:
                alb[:, x1 - 1 + p] = m["albedo"][:, -1]
                rough[:, x1 - 1 + p] = m["rough"][:, -1]
                height[:, x1 - 1 + p] = m["height"][:, -1]
        means.append(m["albedo"].reshape(-1, 3).mean(0))
    out = finish({"albedo": alb, "rough": rough, "height": height}, np.full(H, dy * 1.0), np.full(H, dy), wrap_v=True)
    # the normal map's x slope above used a single texel size; columns are close enough to it
    out["layout"] = layout
    out["column_mean"] = np.array(means)
    return out


# -- leaves and strips ----------------------------------------------------------------------------
def leaf_half_width(look: dict, t) -> np.ndarray:
    """The blade's half width at t (0 base, 1 tip), 1 at its widest, before its teeth: the same curve
    as ``_leaf_outline``, for meshes that cut the leaf's real outline."""
    w0 = float(look["leaves"]["shape"]["widest_at"])
    t = np.asarray(t, float)
    up = np.clip(t / w0, 0.0, 1.0)
    down = np.clip(1.0 - (t - w0) / (1.0 - w0), 0.0, 1.0)
    k = 0.32
    d_ = np.clip(k - np.abs(up - down), 0.0, k) / k
    rounded = np.minimum(up, down) - d_ * d_ * k * 0.25
    half = rounded * (1.0 - 0.34 * smooth(0.55, 1.0, t) * (1.0 - smooth(0.9, 1.0, t)))
    return np.where(t <= 0, 0.0, half)


def push_pull_fill(rgb: np.ndarray, weight: np.ndarray) -> np.ndarray:
    """Colour flooded into the texels of zero weight from their nearest weighted neighbours, coarse to
    fine, so mips of a cut-out never average in what lies under the cut (the game's bleed_foliage.py
    does this to its leaf textures, or distant crowns frost)."""
    levels = []
    colour, total = rgb * weight[..., None], weight
    while min(colour.shape[:2]) > 1:
        levels.append((colour, total))
        h, w = colour.shape[0] // 2, colour.shape[1] // 2
        colour = colour[:h * 2, :w * 2].reshape(h, 2, w, 2, 3).sum((1, 3))
        total = total[:h * 2, :w * 2].reshape(h, 2, w, 2).sum((1, 3))
    fill = colour / np.maximum(total, 1e-6)[..., None]
    for colour, total in reversed(levels):
        coarse = np.repeat(np.repeat(fill, 2, 0), 2, 1)
        coarse = np.pad(coarse, ((0, colour.shape[0] - coarse.shape[0]), (0, colour.shape[1] - coarse.shape[1]), (0, 0)), mode="edge")
        own = colour / np.maximum(total, 1e-6)[..., None]
        have = np.minimum(total, 1.0)[..., None]
        fill = own * have + coarse * (1.0 - have)
    return fill.astype(np.float32)


def _leaf_outline(look: dict, n: int) -> np.ndarray:
    """A birch blade in a square, base at the bottom row, tip at the top: mask 0-1.  The outline
    is triangular with a truncate base and double teeth, and sits inside the diamond the mesh uses
    (corners at bottom middle, top middle, and at widest_at along the sides)."""
    sh = look["leaves"]["shape"]
    w0 = float(sh["widest_at"])
    teeth = float(sh["teeth"])
    Y, X = np.meshgrid((np.arange(n) + 0.5) / n, (np.arange(n) + 0.5) / n, indexing="ij")
    t = 1.0 - Y                 # 0 at the base, 1 at the tip
    x = np.abs(2.0 * X - 1.0)   # 0 on the midrib, 1 at the side corners
    up = np.clip(t / w0, 0.0, 1.0)
    down = np.clip(1.0 - (t - w0) / (1.0 - w0), 0.0, 1.0)
    # shoulders rounded where the two edges meet, the last part drawn out to a point
    k = 0.32
    d_ = np.clip(k - np.abs(up - down), 0.0, k) / k
    rounded = np.minimum(up, down) - d_ * d_ * k * 0.25
    half = rounded * (1.0 - 0.34 * smooth(0.55, 1.0, t) * (1.0 - smooth(0.9, 1.0, t)))
    half = np.where(t <= 0, 0.0, half)
    # double teeth along the edge, nothing at the base or the very tip
    tooth = 0.045 * np.abs(((t * teeth) % 1.0) - 0.5) * 2.0 + 0.025 * np.abs(((t * teeth * 2.0) % 1.0) - 0.5) * 2.0
    edge = half - tooth * smooth(0.02, 0.2, t) * (1.0 - smooth(0.8, 1.0, t)) - x
    aa = 2.0 / n * 2.0
    mask = np.clip(edge / aa + 0.5, 0.0, 1.0)
    # nothing outside the diamond the mesh has, so the visible area is known
    diamond = np.minimum(t / w0, (1.0 - t) / (1.0 - w0))
    return (mask * (x <= diamond)).astype(np.float32)


def leaf_blade(look: dict, seed: int, state_lead: float = 0.0) -> dict:
    """The blade: a soft, near-white detail map (COLOR_0 gives each leaf its colour), with an alpha
    mask; lighter veins, a little mottling.  ``state_lead``: how yellow between the veins, 0-1;
    with it the map's own hue shifts from green at the veins to yellow between them."""
    n = int(look["leaves"]["texture_size_px"])
    sh = look["leaves"]["shape"]
    mask = _leaf_outline(look, n)
    Y, X = np.meshgrid((np.arange(n) + 0.5) / n, (np.arange(n) + 0.5) / n, indexing="ij")
    t = 1.0 - Y
    x = 2.0 * X - 1.0
    vein_light = float(sh["vein_lightness"])
    mid = np.exp(-(x / 0.018) ** 2)
    nv = int(sh["secondary_veins"])
    # secondary veins leave the midrib at a slant and run straight to the teeth
    phase = (t - 0.55 * np.abs(x)) * nv
    side = np.exp(-(((phase % 1.0) - 0.5) / 0.055) ** 2) * (t > 0.02)
    veins = np.clip(mid + 0.6 * side, 0.0, 1.0)
    grain = noise((n, n), seed, (n / 40.0, n / 40.0), 1.8)
    cell = noise((n, n), seed + 1, (n / 170.0, n / 170.0), 1.0)
    base = 0.86 + 0.045 * grain + 0.03 * cell
    # chlorophyll goes first between the veins: yellow there, green by the veins
    v_near = np.exp(-(((phase % 1.0) - 0.5) / 0.22) ** 2)
    between = np.clip(1.0 - np.maximum(v_near, np.exp(-(x / 0.09) ** 2)), 0.0, 1.0)
    lead = float(state_lead) * between * (0.6 + 0.4 * rank01(grain))
    rgb = np.stack([base + 0.20 * lead, base + 0.06 * lead, base * (1.0 - 0.45 * lead)], -1)
    rgb = rgb + vein_light * veins[..., None] * np.array([1.0, 1.1, 0.7])
    # slope for a normal map: veins sunken on top
    hgt = -0.6 * veins + 0.06 * grain
    gy, gx = np.gradient(hgt)
    nrm = np.stack([-gx * 2.5, gy * 2.5, np.ones_like(gx)], -1)
    nrm /= np.linalg.norm(nrm, axis=-1, keepdims=True)
    # bleed colour past the outline so mips don't pick up a dark edge
    return {"rgb": np.clip(rgb, 0.0, 1.0).astype(np.float32), "alpha": mask, "normal": nrm.astype(np.float32),
            "fill": float(mask.mean() / 0.5)}


def leaf_card_atlas(look: dict, blade: dict, seed: int) -> dict:
    """Leaf cards for distant levels: a grid of variants, each a spray of blades on transparent.
    Returns rgb, alpha and the share of each variant that's opaque, to keep leaf area when sizing."""
    cfg = look["game"]["leaf_card"]
    from PIL import Image

    N = int(cfg["texture_px"])
    grid = int(np.ceil(np.sqrt(int(cfg["variants"]))))
    cell = N // grid
    rng = np.random.default_rng(seed)
    src = np.concatenate([np.clip(blade["rgb"], 0, 1), blade["alpha"][..., None]], -1)
    sprite = Image.fromarray((src * 255).astype(np.uint8), "RGBA")
    sheet = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    covered = []
    k = int(cfg["leaves_per_variant"])
    aspect = float(look["leaves"]["shape"]["aspect"])
    for gy in range(grid):
        for gx in range(grid):
            tile = Image.new("RGBA", (cell, cell), (0, 0, 0, 0))
            for _ in range(k):
                ln = int(cell * rng.uniform(0.26, 0.36))
                wd = int(ln / aspect)
                im = sprite.resize((max(wd, 2), max(ln, 2)), Image.LANCZOS)
                shade = rng.uniform(0.72, 1.0)
                a = np.asarray(im, np.float32)
                a[..., :3] *= shade
                im = Image.fromarray(a.astype(np.uint8), "RGBA").rotate(rng.uniform(0, 360), expand=True, resample=Image.BICUBIC)
                # spray from a central point, blades pointing out
                r = cell * 0.5 * rng.uniform(0.0, 0.62)
                ang = rng.uniform(0, 2 * np.pi)
                cx, cy = cell / 2 + r * np.cos(ang), cell / 2 + r * np.sin(ang)
                tile.alpha_composite(im, (int(np.clip(cx - im.width / 2, 0, cell - im.width)), int(np.clip(cy - im.height / 2, 0, cell - im.height))))
            sheet.paste(tile, (gx * cell, gy * cell))
            covered.append(float(np.asarray(tile, np.float32)[..., 3].mean() / 255.0))
    a = np.asarray(sheet, np.float32) / 255.0
    rgb = a[..., :3].copy()
    alpha = a[..., 3].copy()
    # colour past the edges: nearest opaque colour, so mips stay leaf-coloured
    mean = rgb[alpha > 0.5].mean(0) if (alpha > 0.5).any() else np.array([0.8, 0.8, 0.8])
    rgb = np.where((alpha < 0.05)[..., None], mean, rgb)
    return {"rgb": rgb, "alpha": alpha, "grid": grid, "coverage": covered}


def strip_texture(look: dict, seed: int, size: int = 512) -> dict:
    """Free bark strips: four rows of strips; the left half is the outside (white), the right the
    inside (orange).  Alpha has torn edges and holes, so a lower vertex alpha opens more of them."""
    cfg = look["bark"]["peel"]
    H = size
    W = size * 2
    out_c, in_c = srgb_to_linear(cfg["outer_colour"]), srgb_to_linear(cfg["inner_colour"])
    rgb = np.zeros((H, W, 3), np.float32)
    alpha = np.zeros((H, W), np.float32)
    row_h = H // 4
    for i in range(4):
        y = (np.arange(row_h) + 0.5) / row_h
        x = (np.arange(size) + 0.5) / size
        tear_t = noise((1, size), seed + i, (1.0, size / 30.0), 1.6)[0]
        tear_b = noise((1, size), seed + 10 + i, (1.0, size / 30.0), 1.6)[0]
        # a sheet that tapers to both ends, more to the free one, with torn edges
        width = smooth(0.0, 0.12, x) * (1.0 - smooth(0.35, 1.0, x)) ** 0.7
        top = 0.5 + 0.44 * width + 0.05 * tear_t * width
        bot = 0.5 - 0.44 * width + 0.05 * tear_b * width
        m = (y[:, None] < top[None, :]) & (y[:, None] > bot[None, :])
        holes = rank01(noise((row_h, size), seed + 20 + i, (row_h / 26.0, size / 12.0), 1.5))
        # opacity falls off towards holes: 1 where solid, under the cutoff where worn through
        a = m * (0.5 + 0.5 * smooth(0.0, 0.12, holes))
        fibre = noise((row_h, size), seed + 30 + i, (0.7, size / 6.0), 1.3)
        sh = (1.0 + 0.06 * fibre)[..., None]
        rgb[i * row_h:(i + 1) * row_h, :size] = np.clip(out_c * sh, 0, 1)
        rgb[i * row_h:(i + 1) * row_h, size:] = np.clip(in_c * sh, 0, 1)
        alpha[i * row_h:(i + 1) * row_h, :size] = a
        alpha[i * row_h:(i + 1) * row_h, size:] = a
    return {"rgb": rgb, "alpha": alpha}
