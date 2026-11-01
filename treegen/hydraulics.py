"""Water transport: one physical limit on growth.

Leaves transpire in proportion to their light (and stomatal opening); the
flow through every internode is the sum of the leaves beyond it; each
internode resists that flow in proportion to its length over its conducting
area, the cross-section of the pipes that still lead to living foliage
(pipe model, Shinozaki et al. 1964).  Leaf water potential is then

    psi_leaf = psi_soil - F_total / K_root - sum(path F_i L_i / (k_s A_i)) - rho g z

with K_root the uptake conductance of the root system (roots.py).  Height
(the gravity term) and path length (the friction term) both lower psi_leaf,
as in the hydraulic limitation of tree height (Ryan & Yoder 1997; Koch et al.
2004).  psi_leaf sets two things:

* stomatal opening phi in [0, 1]: closes linearly between psi_open and
  psi_close, which scales the leaf's transpiration and its carbon gain;
* turgor-driven expansion: internode and leaf size fall from full at
  psi_full_expansion to the floor at the turgor-loss point.

Transpiration depends on phi; the equilibrium is found by bisection (see solve).
"""
from __future__ import annotations

import numpy as np

RHO_G = 0.0098  # MPa per metre of height


def active_pipe_area(tree, levels, alive, tip_pipe, leaf_pipe, bud_nodes, bud_leaves, gamma):
    """Conducting cross-section of each internode: the pipes that still lead
    to living foliage, one per leaf, plus the shoot tips (pipe model; pipes
    to dead foliage are heartwood)."""
    n = tree.n
    own = np.where(alive & (tree.main_child[:n] < 0) & (tree.term[:n] == 1), tip_pipe, 0.0)
    np.add.at(own, bud_nodes, leaf_pipe * bud_leaves)
    P = tree.basipetal(levels, own)
    r = np.power(np.maximum(P, 1e-30), 1.0 / gamma)
    return np.pi * r * r


def sapwood_area(tree, levels, alive, bud_nodes, bud_leaf_area, huber):
    """Conducting cross-section of each internode as the pipe model counts
    it (Shinozaki et al. 1964): every unit of leaf area beyond is served by
    its own pipe of xylem, ``huber`` m2 of xylem per m2 of leaf, and pipes add
    up by area.  It can be no larger than the wood that carries it."""
    n = tree.n
    own = np.zeros(n)
    np.add.at(own, bud_nodes, huber * bud_leaf_area)
    A = tree.basipetal(levels, own)
    wood = np.pi * tree.radius[:n] ** 2
    return np.where(alive & (wood > 0), np.minimum(A, wood), A)


def solve(tree, levels, alive, bud_nodes, leaf_area, light, area, K_root, hp, psi_soil):
    """Water potential at every node and stomatal opening of every bud.

    Water potential is linear in transpiration, so with all leaves scaled by
    a common stomatal factor s the potential of bud j is
    psi_j(s) = psi_soil - rho g z_j - s D_j, where D_j is its total drop at
    full opening.  The equilibrium s* is where s equals the flow-weighted
    mean opening phi_j(psi_j(s)) (bisection; the right side falls with s),
    which is where stomata close just enough for supply to meet demand.
    """
    n = tree.n
    par = tree.parent
    e_max = float(hp.transpiration_max)
    ks = float(hp.xylem_conductivity)
    p_open, p_close = float(hp.psi_stomata_open), float(hp.psi_stomata_closed)
    # vessels widen from the twig tips towards the base (Anfodillo et al. 2006;
    # Olson et al. 2014), so conductivity grows with branch size
    r_ref, c = float(hp.conductivity_reference_radius), float(hp.conductivity_exponent)
    ks_r = ks * np.minimum(1.0, np.power(np.maximum(tree.radius[:n], 1e-5) / r_ref, c))
    R = np.where(alive, tree.length[:n] / (ks_r * np.maximum(area, 1e-12)), 0.0)
    z = tree.pos[:n, 2]
    E1 = e_max * leaf_area * light
    E = np.zeros(n)
    np.add.at(E, bud_nodes, E1)
    F = tree.basipetal(levels, E)
    acc = F * R
    for seg, _, _ in levels[1:]:
        acc[seg] += acc[par[seg]]
    root_drop = F[0] / max(K_root, 1e-12)
    D = root_drop + acc                       # drop at full opening, every node
    base = psi_soil - RHO_G * np.maximum(z, 0.0)
    wE = E1 / max(float(E1.sum()), 1e-30)
    Db, bb = D[bud_nodes], base[bud_nodes]

    def mean_phi(sv):
        ph = np.clip((bb - sv * Db - p_close) / (p_open - p_close), 0.0, 1.0)
        return float((wE * ph).sum())

    lo_s, hi_s = 0.0, 1.0
    if mean_phi(1.0) >= 1.0:
        lo_s = hi_s = 1.0
    else:
        for _ in range(40):
            mid = 0.5 * (lo_s + hi_s)
            if mean_phi(mid) > mid:
                lo_s = mid
            else:
                hi_s = mid
    s_eq = 0.5 * (lo_s + hi_s)
    psi = base - s_eq * D
    phi = np.clip((psi[bud_nodes] - p_close) / (p_open - p_close), 0.0, 1.0)
    collar = psi_soil - s_eq * root_drop
    return psi, phi, float(s_eq * F[0]), float(collar)


def expansion(psi, hp, floor):
    """Turgor-limited expansion factor (Koch et al. 2004)."""
    full, tlp = float(hp.psi_full_expansion), float(hp.psi_turgor_loss)
    return np.clip((psi - tlp) / (full - tlp), float(floor), 1.0)
