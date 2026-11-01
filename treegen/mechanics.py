"""Branch mechanics: bending under load and posture control.

Incremental cantilever model after Jirasek, Prusinkiewicz & Moulia (2000),
"Integrating biomechanics into developmental plant models expressed using
L-systems": wood is laid down on the already deformed branch, so last year's
shape is locked in and each year only the *increment* of load bends it
further.  Every living internode i, of length l and radius r, bends by

    d(theta)_i = l * dM_i / (E(r) I(r)),   I = pi r^4 / 4,

where dM_i is the moment of this year's added mass (new wood ring, change in
leaf mass, new shoots) carried beyond its base.  The increment is applied in
sub-steps on the updated geometry, so long thin shoots can swing all the way
down and then stop, since a hanging shoot has no lever arm left.

Posture control (Almeras & Fournier 2009, J. Theor. Biol. 256:370): reaction
wood formed in the new ring bends an internode back towards its gravitropic
set-point at a rate of at most  C_rw * dr / r^2  radians per metre per year.
The correction is integrated from the base outwards, each internode fixing
only the error left after its ancestors moved it.  Thick limbs keep their
angle that way; thin shoots of a pendulous species do not, which is the
trait: correction and stiffness of thin side shoots are scaled down by
s(r) = (r/r_p)^p / (1 + (r/r_p)^p).  The stem is exempt (orthotropic).

Rotations are composed exactly with quaternions.  The passes from the base
outwards (composing rotations, posture control, positions) run compiled
(kernels.py), node by node in level order.
"""
from __future__ import annotations

import math

import numpy as np

from . import kernels

G = 9.81


def pendulous_factor(r: np.ndarray, r_p: float, p: float) -> np.ndarray:
    """0 for thin shoots (no correction, low stiffness), 1 for wood."""
    rp = np.power(np.maximum(r, 1e-9) / r_p, p)
    return rp / (1.0 + rp)


# -- quaternions (w, x, y, z) ------------------------------------------------
def _quat(omega: np.ndarray) -> np.ndarray:
    th = np.linalg.norm(omega, axis=-1, keepdims=True)
    k = omega / np.maximum(th, 1e-12)
    return np.concatenate([np.cos(0.5 * th), np.sin(0.5 * th) * k], axis=-1)


def _qrot(q: np.ndarray, v: np.ndarray) -> np.ndarray:
    w, u = q[..., :1], q[..., 1:]
    t = 2.0 * np.cross(u, v)
    return v + w * t + np.cross(u, t)


def setpoint_directions(dirs: np.ndarray, gsa: np.ndarray) -> np.ndarray:
    """Direction in each shoot's own vertical plane at angle gsa from vertical."""
    h = dirs.copy()
    h[:, 2] = 0.0
    hn = np.linalg.norm(h, axis=1, keepdims=True)
    h = np.where(hn > 1e-6, h / np.maximum(hn, 1e-12), np.array([1.0, 0.0, 0.0]))
    return np.cos(gsa)[:, None] * np.array([0.0, 0.0, 1.0]) + np.sin(gsa)[:, None] * h


def _update_positions(tree, levels, zmin: float):
    """pos = pos[parent] + length * dir, keeping nodes above the ground."""
    kernels.positions(levels.down, tree.parent, tree.pos, tree.dir, tree.length, float(zmin))


def _apply(tree, levels, alive, qtot: np.ndarray, zmin: float):
    T = tree
    idx = np.nonzero(alive & (np.abs(qtot[:, 1:]).sum(1) > 0))[0]
    if idx.size:
        q = qtot[idx]
        for name in ("dir", "term_dir", "lat_dir", "ref"):
            arr = getattr(T, name)
            arr[idx] = _qrot(q, arr[idx])
        T.dir[idx] /= np.linalg.norm(T.dir[idx], axis=1, keepdims=True)
    _update_positions(T, levels, zmin)


def bend_and_correct(tree, levels, alive, mp, leaves_now, leaves_prev, r_prev, setpoint, zmin, target_dir=None,
                     stem=None):
    """One year of mechanics on the living structure.

    leaves_now/leaves_prev: leaves carried at each node this and last season.
    r_prev: radius of each node last year (0 for new internodes).
    setpoint: gravitropic set-point angle (rad from vertical) of each node.
    stem: nodes of the stem's axes (with replacement leaders); default order 0.
    """
    T = tree
    n = T.n
    par = T.parent
    idx = np.nonzero(alive)[0]
    idx = idx[idx > 0]
    r = T.radius[:n]
    L = T.length[:n]
    s = pendulous_factor(r, float(mp.pendulous_radius), float(mp.pendulous_sharpness))
    # the stem is strictly orthotropic: the pendulous trait is a twig trait
    s = np.where((T.order[:n] == 0) if stem is None else stem, 1.0, s)
    E_wood, E_shoot = float(mp.youngs_modulus_wood), float(mp.youngs_modulus_shoot)
    E = E_shoot + (E_wood - E_shoot) * s
    EI = E * np.pi * r ** 4 / 4.0
    # this year's added load (kg): new wood ring, change in leaf mass
    dm = np.zeros(n)
    dm[idx] = (float(mp.wood_density) * np.pi * np.maximum(r[idx] ** 2 - r_prev[idx] ** 2, 0.0) * L[idx]
               + float(mp.leaf_mass) * (leaves_now[idx] - leaves_prev[idx]))
    steps = int(mp.substeps)
    cap = float(mp.max_rotation_per_step)
    up = np.array([0.0, 0.0, 1.0])
    ident = np.zeros((n, 4))
    ident[:, 0] = 1.0

    # 1. bending under this year's added load, in sub-steps
    for _ in range(steps):
        c = T.pos[:n] - 0.5 * L[:, None] * T.dir[:n]           # internode centroids
        acc = np.zeros((n, 4))
        acc[:, 0] = dm / steps
        acc[:, 1:] = (dm / steps)[:, None] * c
        acc = T.basipetal(levels, acc)
        base = T.pos[par[:n].clip(0)]
        arm = acc[:, 1:] - acc[:, :1] * base                    # first moment about each base
        M = np.cross(arm, -G * up)                              # (n,3), horizontal
        omega = np.zeros((n, 3))
        omega[idx] = M[idx] * (L[idx] / np.maximum(EI[idx], 1e-30))[:, None]
        mag = np.linalg.norm(omega, axis=1, keepdims=True)
        omega *= np.minimum(1.0, cap / np.maximum(mag, 1e-12))
        qloc = _quat(omega)
        qtot = ident.copy()
        # local bends are defined in this sub-step's frame: ancestors act last
        kernels.compose(levels.down, par, qtot, qloc)
        _apply(T, levels, alive, qtot, zmin)

    # 2. posture control towards the set-point, limited by reaction wood,
    #    integrated from the base so no internode overshoots
    dr = np.maximum(r - r_prev, 0.0)
    rate = float(mp.reaction_wood_coefficient) * dr / np.maximum(r, 1e-9) ** 2 * s
    budget = np.zeros(n)
    budget[idx] = rate[idx] * L[idx]
    qtot = ident.copy()
    # each node turns towards its set-point after its ancestors' correction.
    # Nodes with their own posture target (target_dir finite: the stem inside
    # a lopsided crown leans towards its light) turn towards that instead.
    # The gravitropic response follows the sine law (Galland 2002; Bastien
    # et al. 2013): reaction wood asymmetry, and so the correction, scales
    # with the sine of the deviation, so small leans are corrected slowly
    # and stems keep some lean and sweep
    sine = bool(getattr(mp, "sine_law", False))
    sin_sat = math.sin(math.radians(float(getattr(mp, "sine_law_saturation_deg", 90.0))))
    td = np.zeros((1, 3)) if target_dir is None else np.ascontiguousarray(target_dir, dtype=float)
    kernels.posture(levels.down, par, T.dir, np.ascontiguousarray(setpoint, dtype=float), td, target_dir is not None,
                    budget, sine, sin_sat, qtot)
    _apply(T, levels, alive, qtot, zmin)
