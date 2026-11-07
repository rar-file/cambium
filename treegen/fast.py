"""Compiled copies of hot passes, for the species file's ``speed`` settings (all off by default).

Each one repeats the numpy expressions it replaces operation for operation, so a run gives the same bits with the setting on
or off: tests/test_speed.py checks each kernel against its numpy form, and tools/golden.py checks whole runs.  What makes that
possible, each checked on this model's machines: numpy's sum() is 0 + a pairwise sum of a fixed shape (reproduced below);
np.linalg.norm on 3-vectors is sqrt(((x2 + y2) + z2)); numba's sin, cos, exp, cbrt and sqrt give numpy's bits; float32 values
read as double keep their value.  Fused multiply-add stays off (numba's default), which is why these can match.

If you change a numpy form these copy (GrowthModel._growth_factor's parts, mechanics.bend_and_correct), change the copy too:
tests/test_speed.py fails if they drift.
"""
from __future__ import annotations

import dataclasses
import math

import numpy as np
from numba import njit

from .kernels import basipetal, compose, positions


def on(species, name: str) -> bool:
    """Is this speed setting on?  (Models pickled or species files written before the settings existed: no.)"""
    return bool(getattr(getattr(species, "speed", None), name, False))


def light_every(species) -> int:
    """How many years one light field lasts (speed.light_every; lossy).  1: a new field each year."""
    return max(1, int(getattr(getattr(species, "speed", None), "light_every", 1) or 1))


def light_environment(species, environment):
    """The environment with fewer light directions, where speed asks for them (lossy)."""
    s = getattr(species, "speed", None)
    change = {}
    for name in ("sky_elevations_deg", "sky_azimuth_count", "sun_hour_step"):
        v = getattr(s, name, None)
        if v is not None:
            change[name] = v
    return dataclasses.replace(environment, **change) if change else environment


@njit(cache=True)
def deposit(d, i, j, k, v):
    """np.add.at(d, (i, j, k), v), in order, on a float32 grid."""
    for n in range(v.shape[0]):
        d[i[n], j[n], k[n]] += v[n]


@njit(cache=True)
def _block(a, lo, n):
    """numpy's pairwise sum of up to 128 values: 8 running sums."""
    if n < 8:
        res = 0.0
        for i in range(lo, lo + n):
            res += a[i]
        return res
    r0, r1, r2, r3 = a[lo], a[lo + 1], a[lo + 2], a[lo + 3]
    r4, r5, r6, r7 = a[lo + 4], a[lo + 5], a[lo + 6], a[lo + 7]
    i = 8
    m = n - (n % 8)
    while i < m:
        r0 += a[lo + i]
        r1 += a[lo + i + 1]
        r2 += a[lo + i + 2]
        r3 += a[lo + i + 3]
        r4 += a[lo + i + 4]
        r5 += a[lo + i + 5]
        r6 += a[lo + i + 6]
        r7 += a[lo + i + 7]
        i += 8
    res = ((r0 + r1) + (r2 + r3)) + ((r4 + r5) + (r6 + r7))
    while i < n:
        res += a[lo + i]
        i += 1
    return res


@njit(cache=True)
def np_sum(a, n):
    """Exactly what a[:n].sum() gives for a contiguous float64 array: 0 + the pairwise sum, whose halves are cut at multiples
    of 8 and added left + right.  An explicit stack, so a cached function needn't call itself."""
    if n <= 128:
        return 0.0 + _block(a, 0, n)
    los = np.empty(96, np.int64)
    ns = np.empty(96, np.int64)
    vals = np.empty(48)
    sp, vp = 1, 0
    los[0], ns[0] = 0, n
    while sp > 0:
        sp -= 1
        lo, m = los[sp], ns[sp]
        if m < 0:                       # both halves done: left + right
            vp -= 1
            vals[vp - 1] = vals[vp - 1] + vals[vp]
        elif m <= 128:
            vals[vp] = _block(a, lo, m)
            vp += 1
        else:
            m2 = m // 2
            m2 -= m2 % 8
            los[sp], ns[sp] = 0, -1
            los[sp + 1], ns[sp + 1] = lo + m2, m - m2
            los[sp + 2], ns[sp + 2] = lo, m2     # the left half first
            sp += 3
    return 0.0 + vals[0]


@njit(cache=True)
def _subtree(up, par, acc):
    for j in range(up.shape[0]):
        i = up[j]
        acc[par[i]] += acc[i]


@njit(cache=True)
def carbon_parts(lam, lead_at, lead_v, ahead, share, thr, caps, full, per_met, early, lma, extra_per_node, starts, z_start,
                 up, alive, par, la_now, hv, keep, L, f_wind, a_wind_coef, laz_now, z_base, wood_keep, ring_cap, has_ring_cap,
                 tip_area, unit, g_per_unit, g_resp, ring, dla, dlaz, buf_a, buf_b):
    """One evaluation of the carbon solve, as GrowthModel._growth_factor's parts(): shoots' wood, leaves, rings and the wind's
    extra.  Fills ring; returns (carbon units used, sapwood units, wind units).  buf_a, buf_b: as long as starts; ring, dla, dlaz:
    as L, zero at dead nodes, and only living nodes are worked on: at a dead node every term of parts() is zero, and the sums
    still run over all nodes, since where a value sits decides how numpy's sum rounds.  The wind's cube root, the costly step, is
    taken only where the result could count: a_wind > need exactly when coef^3 m^2 > need^3, and the margin covers rounding."""
    n, m, na = L.shape[0], starts.shape[0], alive.shape[0]
    for q in range(na):
        dla[alive[q]] = 0.0
    wind = f_wind > 0.0
    if wind:
        for q in range(na):
            dlaz[alive[q]] = 0.0
    k = 0
    for i in range(m):
        v = lam * share[i]
        grow = (v >= thr[i]) and (share[i] > 0.0)
        if lead_at >= 0:
            grow = grow and (caps[i] >= thr[i])
            if i == lead_at:
                v = lead_v
                grow = lead_v > 0.0
        vc = v if v < caps[i] else caps[i]
        if grow:
            buf_a[k] = full[i] * vc
            k += 1
            fl = np.floor(vc)
            la = (fl if fl > 1.0 else 1.0) * per_met[i] + early[i]
            piped = la + fl * extra_per_node[i] if ahead else la
        else:
            la = 0.0
            piped = 0.0
        buf_b[i] = la * lma[i]
        s = starts[i]
        dla[s] += piped
        if wind:
            dlaz[s] += piped * z_start[i]
    shoot_vol = tip_area * np_sum(buf_a, k)
    leaf_units = np_sum(buf_b, m) / g_per_unit * g_resp if g_per_unit > 0.0 else 0.0
    _subtree(up, par, dla)
    for q in range(na):
        j = alive[q]
        dla[j] = la_now[j] + dla[j]             # now the leaf area beyond each node
        r = hv[j] * dla[j] - keep[j]
        ring[j] = r if r > 0.0 else 0.0
    sap_units = wind_units = 0.0
    if wind:
        _subtree(up, par, dlaz)
        coef3 = a_wind_coef * a_wind_coef * a_wind_coef
        lead = lead_at >= 0
        for q in range(na):
            j = alive[q]
            dlaz[j] = laz_now[j] + dlaz[j]      # now the leaf area x height beyond each node
        if not lead:
            f_year = f_wind
        else:
            d0 = dlaz[0] if dlaz[0] > 1e-12 else 1e-12
            f_year = f_wind * laz_now[0] / d0
        for q in range(na):
            j = alive[q]
            x = dlaz[j] - z_base[j] * dla[j]
            m_w = f_year * (x if x > 0.0 else 0.0)
            need = ring[j] + wood_keep[j]
            if m_w == 0.0 or coef3 * m_w * m_w < need * need * need * (1.0 - 1e-12):
                # it can't reach what's there: no extra.  (need is 0 or more, and with m_w 0 the area is 0)
                if lead:
                    dlaz[j] = 0.0
                continue
            c = np.cbrt(m_w)
            a_w = a_wind_coef * (c * c)
            if lead:
                e = a_w - wood_keep[j] - ring[j]
                dlaz[j] = e if e > 0.0 else 0.0     # now the wind's extra ring
            else:
                e = a_w - wood_keep[j]
                ring[j] = ring[j] if ring[j] >= e else e
        if lead:
            for q in range(na):
                j = alive[q]
                dla[j] = ring[j] * L[j]
            sap_units = np_sum(dla, n) / unit
            for q in range(na):
                j = alive[q]
                dla[j] = dlaz[j] * L[j]
            extra_units = np_sum(dla, n) / unit
            wind_units = extra_units
            if has_ring_cap:
                room = ring_cap - sap_units
                room = room if room > 0.0 else 0.0
                if extra_units > room:
                    t = room / extra_units
                    for q in range(na):
                        j = alive[q]
                        dlaz[j] = dlaz[j] * t
            for q in range(na):
                j = alive[q]
                ring[j] = ring[j] + dlaz[j]
    for q in range(na):
        j = alive[q]
        dla[j] = ring[j] * L[j]
    return (shoot_vol + np_sum(dla, n)) / unit + leaf_units, sap_units, wind_units


@njit(cache=True)
def apply_rotation(alive_idx, down, par, qtot, pos, dirs, term_dir, lat_dir, ref, length, zmin):
    """mechanics._apply: each living node's rotation, where it has one, on its direction vectors; then the positions."""
    for j in range(alive_idx.shape[0]):
        i = alive_idx[j]
        ux, uy, uz = qtot[i, 1], qtot[i, 2], qtot[i, 3]
        if abs(ux) + abs(uy) + abs(uz) > 0:
            w = qtot[i, 0]
            for a in (dirs, term_dir, lat_dir, ref):
                vx, vy, vz = a[i, 0], a[i, 1], a[i, 2]
                tx = 2.0 * (uy * vz - uz * vy)
                ty = 2.0 * (uz * vx - ux * vz)
                tz = 2.0 * (ux * vy - uy * vx)
                a[i, 0] = vx + w * tx + (uy * tz - uz * ty)
                a[i, 1] = vy + w * ty + (uz * tx - ux * tz)
                a[i, 2] = vz + w * tz + (ux * ty - uy * tx)
            dx, dy, dz = dirs[i, 0], dirs[i, 1], dirs[i, 2]
            s = math.sqrt(dx * dx + dy * dy + dz * dz)
            dirs[i, 0] = dx / s
            dirs[i, 1] = dy / s
            dirs[i, 2] = dz / s
    positions(down, par, pos, dirs, length, zmin)


@njit(cache=True)
def bend_steps(steps, cap, grav, idx, alive_idx, down, up, par, pos, dirs, term_dir, lat_dir, ref, length, dm, ei, zmin, qtot):
    """mechanics.bend_and_correct's step 1 on the living nodes.  qtot comes in as identity rotations and is overwritten
    for every node that has a parent."""
    n = dm.shape[0]
    acc = np.zeros((n, 4))
    qloc = np.zeros((n, 4))
    b0, b1, b2 = -grav * 0.0, -grav * 0.0, -grav * 1.0
    for _ in range(steps):
        for j in range(alive_idx.shape[0]):
            i = alive_idx[j]
            d = dm[i] / steps
            h = 0.5 * length[i]
            acc[i, 0] = d
            acc[i, 1] = d * (pos[i, 0] - h * dirs[i, 0])
            acc[i, 2] = d * (pos[i, 1] - h * dirs[i, 1])
            acc[i, 3] = d * (pos[i, 2] - h * dirs[i, 2])
        basipetal(up, par, acc)
        for j in range(idx.shape[0]):
            i = idx[j]
            p = par[i]
            # the moment arm about the node's base, and the moment arm x (-g up)
            a0 = acc[i, 1] - acc[i, 0] * pos[p, 0]
            a1 = acc[i, 2] - acc[i, 0] * pos[p, 1]
            a2 = acc[i, 3] - acc[i, 0] * pos[p, 2]
            m0 = a1 * b2 - a2 * b1
            m1 = a2 * b0 - a0 * b2
            m2 = a0 * b1 - a1 * b0
            e = ei[i] if ei[i] > 1e-30 else 1e-30
            f = length[i] / e
            ox, oy, oz = m0 * f, m1 * f, m2 * f
            mag = math.sqrt(ox * ox + oy * oy + oz * oz)
            mm = mag if mag > 1e-12 else 1e-12
            lim = cap / mm
            lim = lim if lim < 1.0 else 1.0
            ox, oy, oz = ox * lim, oy * lim, oz * lim
            th = math.sqrt(ox * ox + oy * oy + oz * oz)
            tm = th if th > 1e-12 else 1e-12
            sh = math.sin(0.5 * th)
            qloc[i, 0] = math.cos(0.5 * th)
            qloc[i, 1] = sh * (ox / tm)
            qloc[i, 2] = sh * (oy / tm)
            qloc[i, 3] = sh * (oz / tm)
        compose(down, par, qtot, qloc)
        apply_rotation(alive_idx, down, par, qtot, pos, dirs, term_dir, lat_dir, ref, length, zmin)


@njit(cache=True)
def blur_layers(a, b, w, wrap):
    """scipy.ndimage.gaussian_filter with truncate=3 on a float32 grid held layer first, a[z, x, y], with mode ("wrap", "wrap",
    "constant") when wrap and "constant" otherwise, operation for operation.  Each value is read as a double and each sum is
    (c w0), then each pair of neighbours from the outermost in; each axis's result is stored as float32, in the order x, y, z.
    Keeping a layer's cells together is what makes this quick: the x and y passes stay inside one layer, and an empty layer is
    skipped.  a holds the sources and is overwritten; b (all zeros, same shape) gets the result.  w: the symmetric weights, odd
    length.  Returns each layer's "has anything" flag, of the result."""
    nz, nx, ny = a.shape
    h = (w.shape[0] - 1) // 2
    wc = w[h]
    has = np.zeros(nz, np.bool_)
    line = np.zeros(ny)
    ext = np.zeros(ny + 2 * h)
    zero = np.zeros(ny, np.float32)
    tmp = np.empty((nx, ny), np.float32)
    for z in range(nz):
        layer = a[z]
        empty = True
        for x in range(nx):
            row = layer[x]
            for y in range(ny):
                if row[y] != 0.0:
                    empty = False
                    break
            if not empty:
                break
        if empty:
            continue
        has[z] = True
        # along x
        for x in range(nx):
            row = layer[x]
            for y in range(ny):
                line[y] = np.float64(row[y]) * wc
            for j in range(h, 0, -1):
                lo, hi = x - j, x + j
                if wrap:
                    lo, hi = lo % nx, hi % nx
                rl = layer[lo] if 0 <= lo < nx else zero
                rh = layer[hi] if 0 <= hi < nx else zero
                wj = w[h - j]
                for y in range(ny):
                    line[y] += (np.float64(rl[y]) + np.float64(rh[y])) * wj
            out = tmp[x]
            for y in range(ny):
                out[y] = line[y]
        # along y, back into the layer
        for x in range(nx):
            row = tmp[x]
            for y in range(ny):
                ext[h + y] = row[y]
            for j in range(h):
                if wrap:
                    ext[h - 1 - j] = ext[h + (ny - 1 - j) % ny]
                    ext[h + ny + j] = ext[h + j % ny]
                else:
                    ext[h - 1 - j] = 0.0
                    ext[h + ny + j] = 0.0
            for y in range(ny):
                line[y] = ext[h + y] * wc
            for j in range(h, 0, -1):
                wj = w[h - j]
                for y in range(ny):
                    line[y] += (ext[h + y - j] + ext[h + y + j]) * wj
            out = layer[x]
            for y in range(ny):
                out[y] = line[y]
    # along z: into b, layer by layer; a layer's result has something if one of its neighbours has
    flags = has.copy()
    for z in range(nz):
        near = False
        for k in range(max(z - h, 0), min(z + h, nz - 1) + 1):
            if flags[k]:
                near = True
                break
        has[z] = near
        if not near:
            continue
        for x in range(nx):
            row = a[z, x]
            for y in range(ny):
                line[y] = np.float64(row[y]) * wc
            for j in range(h, 0, -1):
                lo, hi = z - j, z + j
                rl = a[lo, x] if lo >= 0 else zero
                rh = a[hi, x] if hi < nz else zero
                wj = w[h - j]
                for y in range(ny):
                    line[y] += (np.float64(rl[y]) + np.float64(rh[y])) * wj
            out = b[z, x]
            for y in range(ny):
                out[y] = line[y]
    return has


@njit(cache=True)
def sweep_rows(H, has, top, bottom, Tr, Ti, wk, diff_z, wd, Dfr, Dfi):
    """The light sweep, one row of frequencies at a time (speed.light_rows; not the same bits as the sweep by layers).
    H[z, x, y]: each layer's spectrum on the way in, each layer's weighted spectrum on the way out.  Tr, Ti[x, k, y]: the transfer
    function's real and imaginary parts, by row and direction.  Dfr, Dfi[d, x, y]: the sky-only spectrum at layers diff_z[d]."""
    nz, nx, nyf = H.shape
    K = wk.shape[0]
    Br = np.empty((K, nyf), np.float32)
    Bi = np.empty((K, nyf), np.float32)
    Sr = np.empty(nyf, np.float32)
    Si = np.empty(nyf, np.float32)
    Dr = np.empty(nyf, np.float32)
    Di = np.empty(nyf, np.float32)
    ndz = diff_z.shape[0]
    for x in range(nx):
        Br[:] = 0.0
        Bi[:] = 0.0
        tr, ti = Tr[x], Ti[x]
        for z in range(top, bottom - 1, -1):
            row = H[z, x]
            if has[z]:
                for y in range(nyf):
                    Dr[y] = row[y].real
                    Di[y] = row[y].imag
            else:
                Dr[:] = 0.0
                Di[:] = 0.0
            Sr[:] = 0.0
            Si[:] = 0.0
            for k in range(K):
                br, bi, r, i = Br[k], Bi[k], tr[k], ti[k]
                w = wk[k]
                for y in range(nyf):
                    a = br[y] * r[y] - bi[y] * i[y] + Dr[y]
                    b = br[y] * i[y] + bi[y] * r[y] + Di[y]
                    br[y] = a
                    bi[y] = b
                    Sr[y] += w * a
                    Si[y] += w * b
            for y in range(nyf):
                row[y] = complex(Sr[y], Si[y])
            for d in range(ndz):
                if diff_z[d] == z:
                    fr, fi = Dfr[d, x], Dfi[d, x]
                    for k in range(K):
                        br, bi = Br[k], Bi[k]
                        w = wd[k]
                        for y in range(nyf):
                            fr[y] += w * br[y]
                            fi[y] += w * bi[y]


def parts_function(hd, lead_at, ahead, share, thr, caps, full, per_met, early, lma, extra_per_node, starts, z_node, levels, alive, par,
                   la_now, hv, keep, L, f_wind, a_wind_coef, laz_now, z_base, wood_keep, ring_cap, tip_area, unit, g_per_unit, g_resp):
    """GrowthModel._growth_factor's parts(), compiled: the same inputs, once, and a function of lambda."""
    n, m = len(L), len(starts)
    la = -1 if lead_at is None else int(lead_at)
    args = dict(share=share, thr=thr, full=full, per_met=per_met, early=early, lma=lma, la_now=la_now, keep=keep, L=L,
                laz_now=laz_now, z_base=z_base, wood_keep=wood_keep)
    a = {k: np.ascontiguousarray(v, dtype=np.float64) for k, v in args.items()}
    caps_a = np.full(m, float(caps)) if np.ndim(caps) == 0 else np.ascontiguousarray(caps, dtype=np.float64)
    hv_a = np.full(n, float(hv)) if np.ndim(hv) == 0 else np.ascontiguousarray(hv, dtype=np.float64)
    extra_a = np.zeros(m) if np.ndim(extra_per_node) == 0 else np.ascontiguousarray(extra_per_node, dtype=np.float64)
    starts_a = np.ascontiguousarray(starts, dtype=np.int64)
    z_start = np.ascontiguousarray(z_node[starts_a], dtype=np.float64)
    up = levels.up
    live = np.nonzero(alive)[0]
    ring, dla, dlaz, buf_a, buf_b = np.zeros(n), np.zeros(n), np.zeros(n), np.zeros(m), np.zeros(m)
    has_cap = ring_cap is not None
    cap = 0.0 if ring_cap is None else float(ring_cap)
    f, coef = float(f_wind), float(a_wind_coef)

    def parts(lam):
        total, sap, wind = carbon_parts(float(lam), la, float(hd["v"]) if la >= 0 else 0.0, bool(ahead), a["share"], a["thr"], caps_a, a["full"],
                                        a["per_met"], a["early"], a["lma"], extra_a, starts_a, z_start, up, live, par, a["la_now"], hv_a, a["keep"],
                                        a["L"], f, coef, a["laz_now"], a["z_base"], a["wood_keep"], cap, has_cap, float(tip_area), float(unit),
                                        float(g_per_unit), float(g_resp), ring, dla, dlaz, buf_a, buf_b)
        if la >= 0 and f > 0.0:
            hd["sap_units"], hd["wind_units"] = sap, wind
        return total, ring.copy()

    return parts


def gaussian_weights(sigma: float, truncate: float = 3.0) -> np.ndarray:
    """scipy.ndimage.gaussian_filter1d's weights."""
    sd = float(sigma)
    lw = int(truncate * sd + 0.5)
    x = np.arange(-lw, lw + 1)
    phi = np.exp(-0.5 / (sd * sd) * x ** 2)
    return phi / phi.sum()
