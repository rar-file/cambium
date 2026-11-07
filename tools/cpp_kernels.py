"""A measured small port: a few of the model's passes in plain C++ (tools/cpp_cost_kernels.cpp), run on the arrays a real tree reached, beside
the numpy or numba they stand for.  Evidence for reports/cpp_port_plan.md, not the port: nothing here is used by the model.  Server only.

    python tools/cpp_kernels.py --label node_cpp_res --seed 1

Builds with the server's g++: 'strict' (-O2, no fused multiply-add: what the game's science core asks of its compiler), 'o3' (-O3, the same rule) and 'fused'
(-O3 -mcpu=native, g++'s default, which fuses multiply-add: quicker, other bits).  Each timing is the best of a few runs on a fresh copy of the same input, in the
same process, one thread.  The tree grows on with its own numbers: every test works on copies, so a seed's tree stays what it is.  light_rows is on so that the
row sweep gets real input.  This is the server's ARM core and g++, not the game's PC and MSVC.
"""
from __future__ import annotations

import argparse
import copy
import ctypes
import json
import math
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

from cpp_cost import FULL, LOSSLESS  # noqa: E402

BASE = ROOT / "out" / "bench" / "ensemble"
AGES = (3, 10, 30, 50, 60)      # age 3 is about the size of most trees in a young plot
BUILDS = {"strict": ["-O2", "-ffp-contract=off"], "o3": ["-O3", "-ffp-contract=off"], "fused": ["-O3", "-mcpu=native"]}


def build(folder: Path) -> dict:
    libs = {}
    for name, flags in BUILDS.items():
        so = folder / f"kernels_{name}.so"
        t0 = time.time()
        subprocess.run(["g++", "-std=c++20", "-shared", "-fPIC", *flags, str(ROOT / "tools" / "cpp_cost_kernels.cpp"), "-o", str(so)], check=True)
        print(f"built {name} in {time.time() - t0:.1f} s", flush=True)
        libs[name] = ctypes.CDLL(str(so))
    return libs


def P(a):
    return ctypes.c_void_p(a.ctypes.data)


def I(v):
    return ctypes.c_int64(int(v))


def F(v):
    return ctypes.c_double(float(v))


def U(v):
    return ctypes.c_uint8(1 if v else 0)


def best(fn, repeats=3):
    """Best time of a few runs of fn(), which gets a fresh input each time: only what it times inside counts."""
    out = None
    t = float("inf")
    for _ in range(repeats):
        dt, out = fn()
        t = min(t, dt)
    return t, out


def compare(a, b) -> dict:
    """Bits and size of the differences between two arrays of the same shape."""
    a, b = np.asarray(a), np.asarray(b)
    same = a.tobytes() == b.tobytes()
    if same:
        return {"same_bits": True, "differ": 0, "max_rel": 0.0}
    x, y = np.abs(a).astype(np.float64), np.abs(b).astype(np.float64)
    d = np.abs(a - b).astype(np.float64)
    rel = d / np.maximum(np.maximum(x, y), 1e-300)
    return {"same_bits": False, "differ": int(np.count_nonzero(a != b)), "of": int(a.size), "max_rel": float(np.nanmax(rel)), "max_abs": float(np.nanmax(d))}


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--label", required=True)
    ap.add_argument("--seed", type=int, default=1)
    a = ap.parse_args()
    out = BASE / a.label
    out.mkdir(parents=True, exist_ok=True)
    libs = build(out)

    import cli
    from scipy import fft as sfft

    from treegen import checkpoint, fast, hydraulics, mechanics
    from treegen.growth import GrowthModel
    from treegen.light import LightField

    sp, _ = cli.load_species("betula_pendula")
    checkpoint.set_values(sp, FULL + LOSSLESS + ["speed.light_rows=true"])
    env_p, _ = cli.load_environment("sweden_open_field")
    now = {"year": 0}
    rows = []
    done = set()

    def first(kernel) -> bool:
        y = now["year"]
        if y in AGES and (kernel, y) not in done:
            done.add((kernel, y))
            return True
        return False

    def note(kernel, size, times, bits):
        row = {"kernel": kernel, "age": now["year"], "size": size, "times": times, "bits": bits}
        rows.append(row)
        print(json.dumps(row), flush=True)
        (out / f"kernels_s{a.seed}.json").write_text(json.dumps(rows), encoding="utf-8")

    # hydraulics.solve: numpy against C++
    real_solve = hydraulics.solve

    def solve(tree, levels, alive, bud_nodes, leaf_area, light, area, K_root, hp, psi_soil):
        if K_root > 0.0 and first("hydraulics.solve"):
            n = tree.n

            def py():
                t0 = time.perf_counter()
                res = real_solve(tree, levels, alive, bud_nodes, leaf_area, light, area, K_root, hp, psi_soil)
                return time.perf_counter() - t0, res
            t_py, res = best(py)
            times, bits = {"numpy": t_py}, {}
            al = np.ascontiguousarray(alive, np.uint8)
            bud, la, li, ar = (np.ascontiguousarray(x) for x in (np.asarray(bud_nodes, np.int64), np.asarray(leaf_area, np.float64), np.asarray(light, np.float64), np.asarray(area, np.float64)))
            up, down = np.ascontiguousarray(levels.up, np.int64), np.ascontiguousarray(levels.down, np.int64)
            pos, rad, length = np.ascontiguousarray(tree.pos[:n]), np.ascontiguousarray(tree.radius[:n]), np.ascontiguousarray(tree.length[:n])
            for name, lib in libs.items():
                psi, phi = np.zeros(n), np.zeros(len(bud))
                flow, collar = ctypes.c_double(), ctypes.c_double()

                def cc():
                    t0 = time.perf_counter()
                    lib.hydraulics_solve(I(n), P(tree.parent), P(rad), P(length), P(pos), P(al), P(ar), P(bud), I(len(bud)), P(la), P(li), P(up), I(len(up)), P(down), I(len(down)), F(hp.transpiration_max), F(hp.xylem_conductivity),
                                         F(hp.psi_stomata_open), F(hp.psi_stomata_closed), F(hp.conductivity_reference_radius), F(hp.conductivity_exponent), F(K_root), F(psi_soil), P(psi), P(phi), ctypes.byref(flow), ctypes.byref(collar))
                    return time.perf_counter() - t0, None
                times[name], _ = best(cc)
                bits[name] = {"psi": compare(res[0], psi), "phi": compare(res[1], phi), "flow": float(flow.value) == res[2], "collar": float(collar.value) == res[3]}
            note("hydraulics.solve", {"nodes": n, "buds": len(bud)}, times, bits)
        return real_solve(tree, levels, alive, bud_nodes, leaf_area, light, area, K_root, hp, psi_soil)
    hydraulics.solve = solve

    # mechanics.bend_and_correct: numpy, numba, C++
    real_bend = mechanics.bend_and_correct

    def bend(tree, levels, alive, mp, leaves_now, leaves_prev, r_prev, setpoint, zmin, target_dir=None, stem=None, limbs=None, compiled=False):
        if first("mechanics.bend_and_correct"):
            names = ("pos", "dir", "term_dir", "lat_dir", "ref")
            n = tree.n

            def fresh():
                t = copy.copy(tree)
                for name in names:
                    setattr(t, name, getattr(tree, name).copy())
                return t

            def py(comp):
                def run():
                    t = fresh()
                    t0 = time.perf_counter()
                    real_bend(t, levels, alive, mp, leaves_now, leaves_prev, r_prev, setpoint, zmin, target_dir, stem, limbs, compiled=comp)
                    return time.perf_counter() - t0, t
                return run
            t_np, res_np = best(py(False), 2)
            t_nb, res_nb = best(py(True), 3)
            times = {"numpy": t_np, "numba": t_nb}
            bits = {"numba": {k: compare(getattr(res_np, k)[:n], getattr(res_nb, k)[:n]) for k in names}}
            al = np.ascontiguousarray(alive, np.uint8)
            alive_idx = np.nonzero(alive)[0].astype(np.int64)
            idx = alive_idx[alive_idx > 0]
            down, up = np.ascontiguousarray(levels.down, np.int64), np.ascontiguousarray(levels.up, np.int64)
            stem_m = np.ascontiguousarray((tree.order[:n] == 0) if stem is None else stem, np.uint8)
            limb_m = np.ascontiguousarray(limbs, np.uint8) if limbs is not None else np.zeros(n, np.uint8)
            td = np.ascontiguousarray(target_dir, np.float64) if target_dir is not None else np.zeros((1, 3))
            ln, lp, rp, sp_ = (np.ascontiguousarray(x, np.float64) for x in (leaves_now, leaves_prev, r_prev, setpoint))
            rad, length = np.ascontiguousarray(tree.radius[:n]), np.ascontiguousarray(tree.length[:n])
            sine = bool(getattr(mp, "sine_law", False))
            sin_sat = math.sin(math.radians(float(getattr(mp, "sine_law_saturation_deg", 90.0))))
            for name, lib in libs.items():
                def cc():
                    t = fresh()
                    t0 = time.perf_counter()
                    lib.mechanics_year(I(n), P(tree.parent), P(rad), P(length), P(al), P(idx), I(len(idx)), P(alive_idx), I(len(alive_idx)), P(down), I(len(down)), P(up), I(len(up)), P(t.pos), P(t.dir), P(t.term_dir), P(t.lat_dir), P(t.ref),
                                       P(ln), P(lp), P(rp), P(sp_), F(zmin), P(td), U(target_dir is not None), P(stem_m), P(limb_m), U(limbs is not None), F(mp.pendulous_radius), F(getattr(mp, "pendulous_radius_limb", 0.0) or 0.0), F(mp.pendulous_sharpness),
                                       F(mp.youngs_modulus_wood), F(mp.youngs_modulus_shoot), F(mp.wood_density), F(mp.leaf_mass), I(int(mp.substeps)), F(mp.max_rotation_per_step), F(mp.reaction_wood_coefficient), U(sine), F(sin_sat))
                    return time.perf_counter() - t0, t
                times[name], res = best(cc)
                bits[name] = {k: compare(getattr(res_np, k)[:n], getattr(res, k)[:n]) for k in names}
            note("mechanics.bend_and_correct", {"nodes": n, "alive": len(alive_idx), "substeps": int(mp.substeps)}, times, bits)
        return real_bend(tree, levels, alive, mp, leaves_now, leaves_prev, r_prev, setpoint, zmin, target_dir, stem, limbs, compiled=compiled)
    mechanics.bend_and_correct = bend

    # the light sweep: numpy layer by layer, numba by rows, C++ by rows; the FFTs apart, which are C++ already
    grid = {}
    real_blur = fast.blur_layers

    def blur(a_, b_, w, wrap):
        grid["shape"] = a_.shape
        if first("light: leaf blur"):
            nz, nx, ny = a_.shape

            def nb():
                x, y = a_.copy(), np.zeros_like(b_)
                t0 = time.perf_counter()
                h = real_blur(x, y, w, wrap)
                return time.perf_counter() - t0, (y, h)
            t_nb, (res, has) = best(nb)
            times, bits = {"numba": t_nb}, {}
            ww = np.ascontiguousarray(w, np.float64)
            for name, lib in libs.items():
                hh = np.zeros(nz, np.uint8)

                def cc():
                    x, y = a_.copy(), np.zeros_like(b_)
                    t0 = time.perf_counter()
                    lib.blur_layers(P(x), P(y), P(ww), I((len(ww) - 1) // 2), I(nz), I(nx), I(ny), U(wrap), P(hh))
                    return time.perf_counter() - t0, y
                times[name], r = best(cc)
                bits[name] = compare(res, r)
            note("light: leaf blur", {"grid": [nx, ny, nz]}, times, bits)
        return real_blur(a_, b_, w, wrap)
    fast.blur_layers = blur
    real_sweep = fast.sweep_rows

    def sweep(H, has, top, bottom, Tr, Ti, wk, dz, wd, fr, fi):
        if first("light: sweep"):
            nz, nx, nyf = H.shape
            K = wk.shape[0]
            ny = grid["shape"][2]

            def nb():
                x, r_, i_ = H.copy(), np.zeros_like(fr), np.zeros_like(fi)
                t0 = time.perf_counter()
                real_sweep(x, has, top, bottom, Tr, Ti, wk, dz, wd, r_, i_)
                return time.perf_counter() - t0, x
            t_nb, res = best(nb)
            times, bits = {"numba rows": t_nb}, {}
            tf = (np.transpose(Tr, (1, 0, 2)) + 1j * np.transpose(Ti, (1, 0, 2))).astype(np.complex64)

            def layers():
                B = np.zeros(tf.shape, np.complex64)
                t0 = time.perf_counter()
                for z in range(top, bottom - 1, -1):
                    B *= tf
                    if has[z]:
                        B += H[z][None]
                    np.tensordot(wk, B, axes=1)
                return time.perf_counter() - t0, None
            times["numpy layers"], _ = best(layers, 2)
            hh = np.ascontiguousarray(has, np.uint8)
            dzz = np.ascontiguousarray(dz, np.int64)
            for name, lib in libs.items():
                def cc():
                    x, r_, i_ = H.copy(), np.zeros_like(fr), np.zeros_like(fi)
                    t0 = time.perf_counter()
                    lib.sweep_rows(P(x), P(hh), I(nz), I(nx), I(nyf), I(K), I(top), I(bottom), P(Tr), P(Ti), P(wk), P(dzz), I(len(dzz)), P(wd), P(r_), P(i_))
                    return time.perf_counter() - t0, x
                times[name], r = best(cc)
                bits[name] = compare(res, r)
            # the FFTs a year's field takes, the same libraries a port would call: scipy's by rows, numpy's by layers
            layer_list = [z for z in range(top, bottom - 1, -1)]
            spec = [res[z] for z in layer_list]

            def inv(fn):
                def run():
                    t0 = time.perf_counter()
                    outp = [fn(s, s=(nx, ny)) for s in spec]
                    return time.perf_counter() - t0, outp
                return run
            times["scipy inverse FFT"], space = best(inv(sfft.irfft2), 2)
            times["numpy inverse FFT"], _ = best(inv(np.fft.irfft2), 2)

            def fwd(fn):
                def run():
                    t0 = time.perf_counter()
                    for s in space:
                        fn(s)
                    return time.perf_counter() - t0, None
                return run
            times["scipy forward FFT"], _ = best(fwd(sfft.rfft2), 2)
            times["numpy forward FFT"], _ = best(fwd(np.fft.rfft2), 2)
            note("light: sweep", {"grid": [nx, ny, nz], "layers": len(layer_list), "directions": K}, times, bits)
        return real_sweep(H, has, top, bottom, Tr, Ti, wk, dz, wd, fr, fi)
    fast.sweep_rows = sweep

    # bud's direction of least shade: numpy calls and a numba lookup against C++
    real_opt = LightField.optimal_direction

    def optimal(self, pos, heading):
        if first("light: optimal_direction") and self.__dict__.get("S_layers") is not None and self.periodic:
            p = self.p

            def py():
                t0 = time.perf_counter()
                r = real_opt(self, pos, heading)
                return time.perf_counter() - t0, r
            t_py, res = best(py)
            times, bits = {"numpy and numba": t_py}, {}
            S = self.S_layers
            nz, nx, ny = S.shape
            pp, hh, dd = (np.ascontiguousarray(x, np.float64) for x in (pos, heading, p.probe_dirs))
            for name, lib in libs.items():
                o = np.zeros_like(pp)

                def cc():
                    t0 = time.perf_counter()
                    lib.optimal_direction(I(len(pp)), I(len(dd)), P(pp), P(hh), P(dd), F(p.perception_r), F(p.perception_cos), F(p.softmin), F(p.C), P(S), I(nz), I(nx), I(ny), I(self.lo[0]), I(self.lo[1]), I(self.lo[2]), F(p.vs), P(o))
                    return time.perf_counter() - t0, None
                times[name], _ = best(cc)
                bits[name] = compare(res, o)
            note("light: optimal_direction", {"buds": len(pp), "probes": len(dd)}, times, bits)
        return real_opt(self, pos, heading)
    LightField.optimal_direction = optimal

    # the order of passes: numpy's sort, numba's count, C++
    real_order = fast.level_order

    def order(mask, depth, is_lateral):
        if first("tree: level order"):
            n = mask.shape[0]

            def np_way():
                t0 = time.perf_counter()
                idx = np.nonzero(mask)[0]
                d = depth[idx]
                o = np.argsort(d, kind="stable")
                idx, d = idx[o], d[o]
                bounds = np.searchsorted(d, np.arange(int(d.max()) + 2))
                lat = is_lateral[idx]
                seen = []
                for k in range(len(bounds) - 1):
                    a_, b_ = bounds[k], bounds[k + 1]
                    seg = idx[a_:b_]
                    sl = lat[a_:b_]
                    seen.append((seg, seg[~sl], seg[sl]))
                np.concatenate([x for _, m, l in reversed(seen[1:]) for x in (m, l)])
                return time.perf_counter() - t0, None
            times = {"numpy": best(np_way)[0]}

            def nb():
                t0 = time.perf_counter()
                r = real_order(mask, depth, is_lateral)
                return time.perf_counter() - t0, r
            times["numba"], res = best(nb)
            bits = {}
            m8, l8 = np.ascontiguousarray(mask[:n], np.uint8), np.ascontiguousarray(is_lateral[:n], np.uint8)
            count = int(mask.sum())
            for name, lib in libs.items():
                idx, dn, up = np.zeros(count, np.int64), np.zeros(count, np.int64), np.zeros(count, np.int64)

                def cc():
                    t0 = time.perf_counter()
                    lib.level_order(I(n), P(m8), P(depth), P(l8), P(idx), P(dn), P(up))
                    return time.perf_counter() - t0, None
                times[name], _ = best(cc)
                bits[name] = compare(res[0], idx)
            note("tree: level order", {"nodes": n, "alive": count}, times, bits)
        return real_order(mask, depth, is_lateral)
    fast.level_order = order

    m = GrowthModel(sp, cli.make_environment(env_p), a.seed, stand=True, soil=cli.make_soil(env_p), lean=True)
    for _ in range(max(AGES)):
        now["year"] = m.year + 1
        m.step()
    print("done", flush=True)


if __name__ == "__main__":
    main()
