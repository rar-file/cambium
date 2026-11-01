"""Compiled tree passes (numba).

Each kernel walks the nodes in an order that respects the tree (``down``:
parents before children; ``up``: the deepest level first, each level's main
children before its laterals, as ``Tree.basipetal`` does level by level) and
repeats the numpy expressions of the level loops it replaces operation for
operation: the same association of sums and products and no fused
multiply-add, so results are bit-identical.  Before, every level was a
handful of numpy calls on a few nodes; a 50-year birch has about 1000 levels.
"""
from __future__ import annotations

import math

import numpy as np
from numba import njit


@njit(cache=True)
def basipetal(up, par, acc):
    """acc[parent] += acc[node] for every node in ``up`` (acc: n x k, in place)."""
    for j in range(up.shape[0]):
        i = up[j]
        p = par[i]
        for c in range(acc.shape[1]):
            acc[p, c] += acc[i, c]


@njit(cache=True)
def compose(down, par, qtot, qloc):
    """qtot[i] = qtot[parent] * qloc[i] (quaternions w, x, y, z)."""
    for j in range(down.shape[0]):
        i = down[j]
        p = par[i]
        aw, ax, ay, az = qtot[p, 0], qtot[p, 1], qtot[p, 2], qtot[p, 3]
        bw, bx, by, bz = qloc[i, 0], qloc[i, 1], qloc[i, 2], qloc[i, 3]
        qtot[i, 0] = aw * bw - ax * bx - ay * by - az * bz
        qtot[i, 1] = aw * bx + ax * bw + ay * bz - az * by
        qtot[i, 2] = aw * by - ax * bz + ay * bw + az * bx
        qtot[i, 3] = aw * bz + ax * by - ay * bx + az * bw


@njit(cache=True)
def positions(down, par, pos, dirs, length, zmin):
    """pos = pos[parent] + length * dir, turning internodes that would end
    below zmin up to it (mechanics._update_positions)."""
    for j in range(down.shape[0]):
        i = down[j]
        p = par[i]
        L = length[i]
        if pos[p, 2] + L * dirs[i, 2] < zmin:
            dz = min(max((zmin - pos[p, 2]) / L, -1.0), 1.0)
            hx, hy = dirs[i, 0], dirs[i, 1]
            hn = math.sqrt(hx * hx + hy * hy)
            scale = math.sqrt(max(1.0 - dz * dz, 0.0)) / max(hn, 1e-12)
            if hn > 1e-9:
                dirs[i, 0] = hx * scale
                dirs[i, 1] = hy * scale
            else:
                dirs[i, 0] = 0.0
                dirs[i, 1] = 0.0
            dirs[i, 2] = dz
        pos[i, 0] = pos[p, 0] + L * dirs[i, 0]
        pos[i, 1] = pos[p, 1] + L * dirs[i, 1]
        pos[i, 2] = pos[p, 2] + L * dirs[i, 2]


@njit(cache=True)
def posture(down, par, dirs, setpoint, target_dir, has_target, budget, sine, sin_sat, qtot):
    """Posture control from the base outwards (mechanics.bend_and_correct,
    step 2): each node turns towards its set-point (or its own target) by at
    most its reaction-wood budget, after its ancestors' corrections."""
    for j in range(down.shape[0]):
        i = down[j]
        p = par[i]
        qw, qx, qy, qz = qtot[p, 0], qtot[p, 1], qtot[p, 2], qtot[p, 3]
        vx, vy, vz = dirs[i, 0], dirs[i, 1], dirs[i, 2]
        # direction after the ancestors' correction: v + w t + u x t, t = 2 u x v
        tx = 2.0 * (qy * vz - qz * vy)
        ty = 2.0 * (qz * vx - qx * vz)
        tz = 2.0 * (qx * vy - qy * vx)
        dx = vx + qw * tx + (qy * tz - qz * ty)
        dy = vy + qw * ty + (qz * tx - qx * tz)
        dz = vz + qw * tz + (qx * ty - qy * tx)
        # set-point direction in the shoot's own vertical plane
        hn = math.sqrt(dx * dx + dy * dy + 0.0 * 0.0)
        if hn > 1e-6:
            hm = max(hn, 1e-12)
            hx, hy, hz = dx / hm, dy / hm, 0.0 / hm
        else:
            hx, hy, hz = 1.0, 0.0, 0.0
        cg, sg = math.cos(setpoint[i]), math.sin(setpoint[i])
        ex = cg * 0.0 + sg * hx
        ey = cg * 0.0 + sg * hy
        ez = cg * 1.0 + sg * hz
        if has_target and math.isfinite(target_dir[i, 0]):
            ex, ey, ez = target_dir[i, 0], target_dir[i, 1], target_dir[i, 2]
        err = math.acos(min(max(dx * ex + dy * ey + dz * ez, -1.0), 1.0))
        ax = dy * ez - dz * ey
        ay = dz * ex - dx * ez
        az = dx * ey - dy * ex
        an = math.sqrt(ax * ax + ay * ay + az * az)
        if an > 1e-9:
            am = max(an, 1e-12)
            ax, ay, az = ax / am, ay / am, az / am
        else:
            ax, ay, az = 0.0, 0.0, 0.0
        gain = min(1.0, math.sin(err) / sin_sat) if sine else 1.0
        corr = min(err, budget[i] * gain)
        # qtot[i] = quat(axis * corr) * qtot[parent]
        ox, oy, oz = ax * corr, ay * corr, az * corr
        th = math.sqrt(ox * ox + oy * oy + oz * oz)
        tm = max(th, 1e-12)
        sh = math.sin(0.5 * th)
        bw, bx, by, bz = math.cos(0.5 * th), sh * (ox / tm), sh * (oy / tm), sh * (oz / tm)
        qtot[i, 0] = bw * qw - bx * qx - by * qy - bz * qz
        qtot[i, 1] = bw * qx + bx * qw + by * qz - bz * qy
        qtot[i, 2] = bw * qy - bx * qz + by * qw + bz * qx
        qtot[i, 3] = bw * qz + bx * qy - by * qx + bz * qw
