"""Core invariants: determinism, pipe model, geometric sanity, roots,
hydraulics, stand mode, export round trip."""
from __future__ import annotations

import json

import numpy as np
import pytest

from cli import anchorage_numbers, build_meshes, reduced_threshold, skeleton, stream
from treegen import export, mesh
from treegen.environment import make_environment, make_soil
from treegen.growth import GrowthModel, LAT_SPUR
from treegen.params import load_environment, load_species
from treegen.reference import reference_block

SPECIES = "betula_pendula"
ENV = "sweden_open_field"
YEARS = 18


def new_model(seed: int, stand: bool = False) -> tuple[GrowthModel, object]:
    sp, _ = load_species(SPECIES)
    env, _ = load_environment(ENV)
    return GrowthModel(sp, make_environment(env), seed, stand=stand, soil=make_soil(env)), sp


@pytest.fixture(scope="module")
def grown():
    """One open-grown run, checking the pipe model after every year."""
    m, sp = new_model(7)
    residuals = []
    m.run(YEARS, callback=lambda mm: residuals.append(mm.pipe_residual()))
    living, pruned, roots_md = build_meshes(m, sp)
    return m, sp, residuals, living, pruned, roots_md


def _outputs(seed, stand, tmp_path, years=12):
    m, sp = new_model(seed, stand)
    m.run(years)
    meta = {"seed": seed}
    export.write_timeline(tmp_path / "timeline.json", m, meta)
    export.write_stats(tmp_path / "stats.json", m, meta, reference_block(sp, m.stats), anchorage_numbers(m, sp))
    living, _, roots_md = build_meshes(m, sp)
    with np.load(tmp_path / "timeline.npz") as z:
        arrays = {k: z[k] for k in z.files}
    return ((tmp_path / "timeline.json").read_bytes(), (tmp_path / "stats.json").read_bytes(),
            arrays, living, roots_md)


@pytest.mark.parametrize("stand", [False, True])
def test_same_seed_gives_identical_output(tmp_path, stand):
    (tmp_path / "a").mkdir()
    (tmp_path / "b").mkdir()
    a = _outputs(3, stand, tmp_path / "a")
    b = _outputs(3, stand, tmp_path / "b")
    assert a[0] == b[0] and a[1] == b[1]
    assert a[2].keys() == b[2].keys() and all(np.array_equal(a[2][k], b[2][k]) for k in a[2])
    for x, y in ((a[3], b[3]), (a[4], b[4])):
        assert np.array_equal(x.vertices, y.vertices)
        assert np.array_equal(x.faces, y.faces)
        for key in x.attributes:
            assert np.array_equal(x.attributes[key], y.attributes[key])


def test_different_seeds_differ():
    a, _ = new_model(3)
    b, _ = new_model(4)
    a.run(10)
    b.run(10)
    k = min(a.tree.n, b.tree.n)
    assert a.tree.n != b.tree.n or not np.allclose(a.tree.pos[:k], b.tree.pos[:k])


def test_pipe_model_every_year(grown):
    _, _, residuals, *_ = grown
    assert len(residuals) == YEARS
    assert max(residuals) < 1e-9


def test_pipe_model_at_every_junction(grown):
    """Independent check: r_parent^g = sum r_child^g + own pipes (tips, short
    shoots, shed branches kept as heartwood), and own pipes are non-negative."""
    m = grown[0]
    T, g = m.tree, m.gamma
    n = T.n
    alive = T.death[:n] < 0
    # the pipes; the stem may carry more wood than its pipes (annual rings)
    assert (T.radius[:n][alive] >= m._r_pipe[:n][alive] - 1e-12).all()
    P = m._r_pipe[:n] ** g
    children = np.zeros(n)
    kids = np.nonzero(alive)[0][1:]
    np.add.at(children, T.parent[kids], P[kids])
    own = P - children
    tip = np.where(T.main_child[:n] < 0, m.tip_pipe, 0.0)
    junction = alive & ((T.main_child[:n] >= 0) | (T.lat_child[:n] >= 0))
    assert junction.sum() > 100
    rel = np.abs(own - (T.own_pipe[:n] + tip))[junction] / P[junction]
    assert rel.max() < 1e-9
    assert (T.own_pipe[:n] >= 0).all()
    assert (m._r_pipe[T.parent[kids]] >= m._r_pipe[kids] - 1e-12).all()


def test_root_pipes_continue_the_stem(grown):
    """The stem's pipes continue into the roots: collar radius = stem base,
    and the root pipe sums hold at every root junction."""
    m = grown[0]
    R = m.roots.tree
    n = R.n
    alive = R.death[:n] < 0
    g = m.gamma
    assert abs(R.radius[0] - m.tree.radius[0]) / m.tree.radius[0] < 1e-9
    P = R.radius[:n] ** g
    kids = np.nonzero(alive)[0][1:]
    children = np.zeros(n)
    np.add.at(children, R.parent[kids], P[kids])
    assert (P[alive] - children[alive] >= -1e-12 * P[alive].max()).all()


def test_radius_never_shrinks(grown):
    H = grown[0].radius_history
    for y in range(1, len(H)):
        prev = H[y - 1]
        assert (H[y][: len(prev)] >= prev - 1e-7).all()


def test_no_nan_or_zero_length_segments(grown):
    m, _, _, living, pruned, roots_md = grown
    for T in (m.tree, m.roots.tree):
        n = T.n
        assert np.isfinite(T.pos[:n]).all()
        seg = np.linalg.norm(T.pos[1:n] - T.pos[T.parent[1:n]], axis=1)
        alive = T.death[:n] < 0
        # bending rotates internodes but never stretches them (a shed branch
        # stays where it died while its parent may keep bending, so only
        # internodes whose parent died in a different year may differ, in
        # either direction: the gap to the parent's current position can be
        # anything)
        same = alive[1:] | (T.death[1:n] == T.death[T.parent[1:n]])
        assert seg[same].min() > 1e-3, f"shortest internode {seg[same].min():.2e} m"
        assert np.allclose(seg[same], T.length[1:n][same], rtol=1e-6, atol=1e-9)
        assert np.isfinite(T.radius[:n]).all() and (T.radius[1:n][alive[1:]] > 0).all()
    for h in m.radius_history:
        assert np.isfinite(h).all()
    for s in m.stats:
        json.dumps(s, allow_nan=False)
    for md in (living, pruned, roots_md):
        if md is None:
            continue
        V, F, N = md.vertices, md.faces, md.normals
        assert np.isfinite(V).all() and np.isfinite(N).all()
        assert F.min() >= 0 and F.max() < len(V)
        assert np.allclose(np.linalg.norm(N, axis=1), 1.0, atol=1e-6)
        assert ((F[:, 0] != F[:, 1]) & (F[:, 1] != F[:, 2]) & (F[:, 0] != F[:, 2])).all()
        area = 0.5 * np.linalg.norm(np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]]), axis=1)
        assert area.min() > 0.0
        for key, arr in md.attributes.items():
            assert len(arr) == len(V), key
            assert np.isfinite(arr).all(), key


def test_roots_stay_in_the_soil(grown):
    m = grown[0]
    R = m.roots.tree
    alive = R.death[: R.n] < 0
    z = R.pos[: R.n][alive, 2]
    assert z.max() <= 1e-9
    # never below the local rootable depth (which varies over the ground)
    local = m.soil.depth_at(R.pos[: R.n][alive, :2], m.roots.seed)
    assert (-z <= local + 0.05).all()


def test_hydraulics_sane(grown):
    w = grown[0].stats[-1]["water"]
    assert 0.0 <= w["stomatal_opening"] <= 1.0
    assert w["psi_collar_mpa"] <= grown[0].soil.water_potential + 1e-9
    assert w["psi_top_mpa"] <= w["psi_collar_mpa"] + 1e-9
    assert 0.0 < w["root_share"] < 1.0


def test_mesh_faces_point_outward(grown):
    living = grown[3]
    V, F, N = living.vertices, living.faces, living.normals
    fn = np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]])
    agree = (fn * N[F].mean(1)).sum(1) > 0
    assert agree.mean() > 0.99


def test_crown_and_roots_meet_without_a_gap(grown):
    """The two meshes share the ring at the ground line: same positions,
    same normals."""
    living, roots_md = grown[3], grown[5]
    a = living.vertices[np.abs(living.vertices[:, 2]) < 1e-6]
    b = roots_md.vertices[np.abs(roots_md.vertices[:, 2]) < 1e-6]
    if len(a) and len(b):
        d = np.min(np.linalg.norm(a[:, None, :] - b[None, :, :], axis=2), axis=1)
        assert d.max() < 1e-9
    # shallow roots may show their top above ground; they stay in the root mesh
    assert (roots_md.vertices[:, 2] <= grown[0].roots.tree.radius.max() + 0.05).all()
    assert "depth_below_ground" in roots_md.attributes


def test_attributes_cover_history(grown):
    m, _, _, living, pruned, _ = grown
    a = living.attributes
    assert a["birth_year"].min() >= 0 and a["birth_year"].max() <= m.year
    assert (a["death_year"] == -1).all()
    assert (a["radius"] > 0).all()
    if pruned is not None:
        d = pruned.attributes["death_year"]
        assert (d > 0).all() and (d <= m.year).all()
        assert (pruned.attributes["birth_year"] < d).all()


def test_spur_log_consistent(grown):
    m = grown[0]
    T = m.tree
    births = np.array(m.spurs.birth)
    deaths = np.array(m.spurs.death)
    assert ((deaths == -1) | (deaths > births)).all()
    live = {nd for nd, de in zip(m.spurs.node, m.spurs.death) if de == -1}
    flagged = set(np.nonzero((T.lat[: T.n] == LAT_SPUR) & (T.death[: T.n] < 0))[0].tolist())
    assert live == flagged


def test_stand_mode_runs_and_shades():
    m, _ = new_model(5, stand=True)
    m.run(14)
    s = m.stats[-1]
    assert s["stand_spacing_m"] > 1.0
    assert s["height_m"] > 2.0


def test_chunked_mesh_matches_one_pass(grown):
    """Streaming the mesh in small chunks gives the same surface as meshing
    the whole tree at once."""
    from scipy.spatial import cKDTree

    m, sp = grown[0], grown[1]
    skel, rad, is_root, orig = skeleton(m)
    full = mesh.build_mesh(skel, np.ones(skel.n, bool), rad, sp.geometry)
    parts = list(mesh.build_mesh_chunks(skel, np.ones(skel.n, bool), rad, sp.geometry, budget=15_000))
    assert len(parts) > 3
    assert sum(p.n_vertices for p in parts) == full.n_vertices
    assert sum(len(p.faces) for p in parts) == len(full.faces)
    d, _ = cKDTree(full.vertices).query(np.concatenate([p.vertices for p in parts]))
    # fillet vertices at a junction cut by a chunk boundary may move a
    # fraction of a millimetre (the context axis is sampled a little
    # differently); everything else is identical.  How many vertices that is
    # depends on how many junctions the chunk boundaries happen to cut, i.e.
    # on the tree's shape (0.12 % with the phase-9 defaults)
    assert d.max() < 5e-4
    assert (d < 1e-9).mean() > 0.998


def test_reduced_mesh_under_ten_percent(grown):
    m, sp = grown[0], grown[1]
    skel, rad, is_root, orig = skeleton(m)
    count = {"hero": 0, "reduced": 0}

    def counter(key):
        return lambda c, r: count.__setitem__(key, count[key] + len(c.faces) + len(r.faces))
    stream(skel, np.ones(skel.n, bool), rad, is_root, orig, sp, [counter("hero")], 50_000)
    thr = reduced_threshold(skel, rad, is_root, orig, sp, count["hero"], 50_000)
    stream(skel, rad[: skel.n] >= thr, rad, is_root, orig, sp, [counter("reduced")], 50_000)
    assert 0 < count["reduced"] < 0.10 * count["hero"]


def test_timeline_radius_within_two_percent(grown, tmp_path):
    m = grown[0]
    h = export.write_timeline(tmp_path / "timeline.json", m, {})
    assert h["radius_encoding"]["max_relative_error_shoots"] <= 0.02
    assert h["radius_encoding"]["max_relative_error_roots"] <= 0.02
    tl = export.Timeline(tmp_path / "timeline.json")
    for prefix, T, hist in (("shoot_", m.tree, m.radius_history), ("root_", m.roots.tree, m.roots.radius_history)):
        for y in range(1, m.year + 1, 3):
            r = tl.radius_at(y, prefix)
            H = hist[y].astype(np.float32)
            k = len(H)
            pres = (T.birth[:k] <= y) & ((T.death[:k] < 0) | (T.death[:k] > y))
            assert (np.abs(r[:k][pres] - H[pres]) <= 0.0201 * H[pres] + 1e-7).all()
            assert (r[:k][~pres] == 0).all()


def test_exports_round_trip(grown, tmp_path):
    import trimesh
    from pxr import Usd, UsdGeom

    m, sp, _, living, pruned, roots_md = grown
    meta = {"species": "Betula pendula", "seed": 7}
    attrs = ["birth_year", "death_year", "branch_order", "radius", "node_id"]
    usd = export.USDWriter(tmp_path / "tree.usdc", meta, part_vertices=20_000)
    usd.group("Living")
    usd.group("Roots", attrs={"anchorage:plateRadiusM": 1.0})
    usd.group("PrunedHistory", hidden=True)
    g = export.GLBWriter(tmp_path / "tree.glb", "tree", meta, attrs)
    gr = export.GLBWriter(tmp_path / "tree_roots.glb", "roots", meta, attrs + ["depth_below_ground"])
    # write in pieces, as the streaming export does
    expect = {}
    for md, name, glb in ((living, "Living", g), (roots_md, "Roots", gr), (pruned, "PrunedHistory", None)):
        pieces = list(_pieces(md, 4))
        expect[name] = (sum(p.n_vertices for p in pieces), sum(len(p.faces) for p in pieces))
        for part in pieces:
            usd.add(name, part)
            if glb is not None:
                glb.add(part)
    usd.close()
    assert g.close()["vertices"] == expect["Living"][0]
    gr.close()
    export.write_timeline(tmp_path / "timeline.json", m, meta)

    stage = Usd.Stage.Open(str(tmp_path / "tree.usdc"))
    assert UsdGeom.GetStageUpAxis(stage) == UsdGeom.Tokens.z
    assert len(list((tmp_path / "tree_parts").iterdir())) > 1
    for prim, name in (("/Tree/Living", "Living"), ("/Tree/Roots", "Roots")):
        meshes = [UsdGeom.Mesh(p) for p in Usd.PrimRange(stage.GetPrimAtPath(prim)) if p.IsA(UsdGeom.Mesh)]
        assert sum(len(x.GetPointsAttr().Get()) for x in meshes) == expect[name][0]
        for x in meshes:
            pv = UsdGeom.PrimvarsAPI(x)
            for name in ("birth_year", "branch_order", "radius", "death_year", "node_id"):
                p = pv.GetPrimvar(name)
                assert p and len(p.Get()) == len(x.GetPointsAttr().Get())
    roots0 = next(p for p in Usd.PrimRange(stage.GetPrimAtPath("/Tree/Roots")) if p.IsA(UsdGeom.Mesh))
    assert UsdGeom.PrimvarsAPI(UsdGeom.Mesh(roots0)).GetPrimvar("depth_below_ground")
    assert stage.GetPrimAtPath("/Tree/Roots").GetAttribute("anchorage:plateRadiusM").Get() == 1.0

    for f, name, key in ((tmp_path / "tree.glb", "_BIRTH_YEAR", "Living"),
                         (tmp_path / "tree_roots.glb", "_DEPTH_BELOW_GROUND", "Roots")):
        scene = trimesh.load(f, process=False)
        geom = next(iter(scene.geometry.values()))
        assert name in geom.vertex_attributes
        assert (len(geom.vertices), len(geom.faces)) == expect[key]

    tl = export.Timeline(tmp_path / "timeline.json")
    assert set(tl.header["arrays"]) == set(tl.a)
    for prefix, T in (("shoot_", m.tree), ("root_", m.roots.tree)):
        alive = T.death[: T.n] < 0
        assert len(tl[prefix + "parent"]) == T.n
        assert np.array_equal(tl[prefix + "birth_year"], T.birth[: T.n])
        assert np.allclose(tl.radius_at(m.year, prefix)[alive], T.radius[: T.n][alive], rtol=1e-3)
    assert np.allclose(tl.positions_at(m.year), m.tree.pos[: m.tree.n], atol=1e-6)
    assert np.allclose(tl.positions_at(10)[: len(m.keyframes[10])], m.keyframes[10], atol=2e-3)


def _pieces(md, k):
    """Split a mesh into k pieces by faces (vertices re-indexed)."""
    for f in np.array_split(md.faces, k):
        used = np.unique(f)
        remap = np.full(md.n_vertices, -1)
        remap[used] = np.arange(used.size)
        yield mesh.MeshData(md.vertices[used], remap[f], md.normals[used], {a: v[used] for a, v in md.attributes.items()})


def test_timeline_rings_and_leaf_traits(grown, tmp_path):
    """Ring widths of every wood node add up to its radius in its last year;
    every short shoot carries a leaf area and LMA."""
    m = grown[0]
    export.write_timeline(tmp_path / "timeline.json", m, {})
    tl = export.Timeline(tmp_path / "timeline.json")
    assert len(tl["spur_leaf_area_m2"]) == len(tl["spur_node"]) == len(tl["spur_lma_g_m2"])
    assert (tl["spur_leaf_area_m2"] >= 0).all()
    T = m.tree
    nodes, counts, widths = tl["shoot_ring_node"], tl["shoot_ring_count"].astype(int), tl["shoot_ring_width_m"]
    assert counts.sum() == len(widths)
    off = np.r_[0, np.cumsum(counts)]
    for k in range(0, len(nodes), max(1, len(nodes) // 50)):
        i = int(nodes[k])
        last = m.year if T.death[i] < 0 else T.death[i] - 1
        assert counts[k] == last - T.birth[i] + 1
        assert abs(widths[off[k]:off[k + 1]].sum() - m.radius_history[last][i]) < 1e-5
