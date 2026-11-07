"""The look of a tree and its game export: values, textures, .glb files, stages."""
from __future__ import annotations

import copy
import json
import struct
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from treegen import appearance as ap  # noqa: E402
from treegen import mesh, textures as tx  # noqa: E402
from treegen.export import GameGLB, read_glb, validate_glb  # noqa: E402
from treegen.params import load_species, option_values, to_namespace  # noqa: E402


@pytest.fixture(scope="module")
def look():
    return ap.load_look(load_species("betula_pendula")[1])


# -- the block in the species file ---------------------------------------------------------------
def test_the_block_adds_no_option_and_no_growth_value():
    """Run manifests list every true or false and every "stage" integer: none here, or the golden
    hash would count them.  And nothing in growth reads the block."""
    _, raw = load_species("betula_pendula")
    assert option_values(to_namespace(raw["appearance"])) == {}
    for name in ("growth.py", "plot.py", "regeneration.py", "light.py", "hydraulics.py", "roots.py"):
        assert "appearance" not in (ROOT / "treegen" / name).read_text(encoding="utf-8")


def _numbers(o, path=""):
    if isinstance(o, dict):
        for k, v in o.items():
            yield from _numbers(v, f"{path}.{k}" if path else k)
    elif isinstance(o, list):
        for v in o:
            yield from _numbers(v, path)
    elif isinstance(o, (int, float)) and not isinstance(o, bool):
        yield path


def test_every_number_says_where_it_came_from(look):
    prov = look["provenance"]
    assert all(v.split(":")[0] in ("SOURCE", "DERIVED", "TUNED") for v in prov.values())
    block = {k: v for k, v in look.items() if k != "provenance"}
    missing = [p for p in set(_numbers(block)) if not any(p == k or p.startswith(k + ".") for k in prov)]
    assert not missing, f"no provenance for: {sorted(missing)}"


# -- bark values ---------------------------------------------------------------------------------
def test_bark_thickness_comes_from_the_same_equation_as_tools_bark(look):
    import bark

    assert tuple(look["bark"]["thickness"]["hansen_double_mm"]) == bark.BARK
    # at a calibration of 1 it is Hansen's own number, at the same over-bark diameter
    plain = copy.deepcopy(look)
    plain["bark"]["thickness"]["calibration"] = 1.0
    dbh = 30.0
    d_ob = 25.0
    wall = float(bark.bark_mm(d_ob, dbh)) / 2.0 / 1000.0
    d_wood = d_ob / 100.0 - 2.0 * wall
    assert float(ap.bark_wall_m(plain, d_wood, dbh)) == pytest.approx(wall, rel=1e-6)


def test_bark_thickness_meets_the_measured_table(look):
    """Vihera-Aarnio & Velling 2017, Table 5, age 22, Tuusula: 11.4 mm at the stump, 3.6 at 1.3 m,
    2.7 at 3 m, 2.2 at 6 m; a tree of DBH 11.3 cm over bark, 14.8 m tall."""
    dbh, H, age = 11.3, 14.8, 22
    import bark

    for z, want, tol in ((3.0, 2.7, 0.25), (6.0, 2.2, 0.25)):
        d_ob = float(bark.d_over_bark(z, dbh, H))
        st = ap.part_state(look, age - 2, (d_ob - 2.0 * want / 10.0) / 100.0, z, H, dbh)
        assert float(st["wall_m"]) * 1000.0 == pytest.approx(want, rel=tol)
    d_stump = 0.14
    st = ap.part_state(look, age, d_stump, 0.0, H, dbh)
    assert float(st["wall_m"]) * 1000.0 == pytest.approx(11.4, rel=0.25)


def test_each_stage_follows_a_parts_own_age_and_size(look):
    H, dbh = 25.0, 30.0
    # a twig stays a twig on an old tree, because it's young and thin
    st = ap.part_state(look, 1.0, 0.004, 15.0, H, dbh)
    assert st["weights"][1] < 0.01 and st["weights"][2] == 0.0
    # the same height, an old thick limb is white
    st = ap.part_state(look, 40.0, 0.12, 15.0, H, dbh)
    assert st["weights"][1] > 0.99 and st["weights"][2] == 0.0
    # the rough base climbs with age, and never reaches the upper stem
    tops = []
    for age in (20, 40, 60, 80, 100):
        z = np.linspace(0.0, 20.0, 401)
        w = ap.part_state(look, np.full_like(z, age), np.full_like(z, 0.3), z, H, dbh)["weights"][2]
        tops.append(float(z[np.nonzero(w > 0.5)[0][-1]]) if (w > 0.5).any() else 0.0)
    assert tops == sorted(tops) and tops[-1] > tops[0] + 1.0
    assert 2.0 <= tops[2] <= 4.0 and tops[-1] < 6.0
    assert ap.part_state(look, 100.0, 0.3, 12.0, H, dbh)["weights"][2] == 0.0
    # deep fissures only where it's rough, and peeling only on white bark that has aged
    young = ap.part_state(look, 3.0, 0.05, 1.0, H, dbh)
    old = ap.part_state(look, 90.0, 0.4, 0.4, H, dbh)
    mid = ap.part_state(look, 30.0, 0.2, 8.0, H, dbh)
    assert young["fissure_m"] == 0.0 and old["fissure_m"] > 0.005
    assert young["peel"] < 1e-3 and old["peel"] < 1e-3 and mid["peel"] > 0.02


def test_look_changes_slowly_from_one_age_to_the_next(look):
    """What makes neighbouring stages line up: a year moves no part's state by much."""
    z = np.linspace(0.0, 12.0, 121)
    d = np.linspace(0.25, 0.12, 121)
    H, dbh = 22.0, 28.0
    a = ap.part_state(look, np.full_like(z, 40.0), d, z, H, dbh)
    b = ap.part_state(look, np.full_like(z, 41.0), d, z, H, dbh)
    assert np.abs(a["weights"] - b["weights"]).max() < 0.08
    assert np.abs(a["wall_m"] - b["wall_m"]).max() < 0.001


# -- leaves --------------------------------------------------------------------------------------
def test_leaf_colours_come_from_the_table_and_turn_yellow_in_autumn(look):
    R, T = ap.leaf_colours(look, np.array([1.0, 0.038]))
    # at full chlorophyll the colours are the measured ones; the tuned lift only touches the yellow end
    measured = look["leaves"]["chlorophyll_ramp"][0]
    assert R[0] + look["leaves"]["specular_f0"] == pytest.approx(np.array(measured["reflectance_linear"]), abs=1e-6)
    assert T[0] == pytest.approx(np.array(measured["transmittance_linear"]), abs=1e-6)
    assert R[0, 1] > R[0, 0]             # green: more green than red
    assert R[1, 0] > 1.5 * R[1, 1]       # yellow-orange
    days = look["leaves"]["season"]["days"]
    no = np.zeros(1)
    assert ap.chlorophyll_at(look, days["summer"], no, no) == pytest.approx(1.0)
    assert ap.chlorophyll_at(look, days["autumn"], no, no) < 0.3
    assert ap.chlorophyll_at(look, days["spring"], no, no) < 0.7
    # a leaf that turns later is greener on the same autumn day; a sun leaf is paler in summer
    assert ap.chlorophyll_at(look, 272, no, no + 8.0) > ap.chlorophyll_at(look, 272, no, no)
    assert ap.chlorophyll_at(look, days["summer"], no + 1.0, no) < 1.0


def test_leaf_count_and_area_are_the_models():
    from types import SimpleNamespace

    _, raw = load_species("betula_pendula")
    look = ap.load_look(raw)
    n = 3000
    rng = np.random.default_rng(1)
    leaves = rng.choice([0.0, 1.0, 2.5, 2.5 * 0.7], n)
    size = rng.choice([0.0, 0.0015, 0.0011], n)
    snap = ap.LeafSnapshot(10, leaves, size, np.full(n, 60.0), rng.random(n) < 0.5, 0.0015)
    sp = SimpleNamespace(light=SimpleNamespace(sun_shade=None))
    pos = rng.random((n, 3)) * 5.0
    out = ap.leaf_instances(look, sp, snap, pos, np.full(n, 0.002), 10, 0.9)
    # area: the model counts leaves * reference area
    assert out.area.sum() == pytest.approx(leaves.sum() * 0.0015, rel=0.02)
    # the same leaf in the same place when asked again
    again = ap.leaf_instances(look, sp, snap, pos, np.full(n, 0.002), 11, 0.9)
    assert np.array_equal(out.along, again.along) and np.array_equal(out.base, again.base)


# -- textures ------------------------------------------------------------------------------------
def test_tiles_are_periodic_and_generated_from_values(look):
    small = copy.deepcopy(look)
    small["bark"]["tile_px"] = 128
    tiles = tx.make_tiles(small)
    assert [t.name for t in tiles] == [s["name"] for s in look["bark"]["stages"]]
    for t in tiles:
        a = t.mips[0]
        # the jump across the wrap is no bigger than a step inside
        for axis in (0, 1):
            inside = np.abs(np.diff(a[..., 0:3], axis=axis)).mean()
            wrap = np.abs(np.take(a[..., 0:3], 0, axis) - np.take(a[..., 0:3], -1, axis)).mean()
            assert wrap < 3.0 * inside + 0.02
    # rough bark comes out dark and white bark light: the colours asked for
    means = [t.mean_colour.mean() for t in tiles]
    assert means[1] > 0.4 > means[0] and means[2] < 0.1


def test_another_species_needs_only_other_values(look):
    """A made-up species with one smooth and one plated stage, no peeling, no marks."""
    other = {
        "bark": {
            "thickness": look["bark"]["thickness"], "tile_size_m": 0.5, "tile_px": 64, "stem_texture_px": [32, 64], "stem_rows": [[2.0, 0.5]],
            "atlas_px": [256, 64], "branch_circumference_m": [0.03, 0.12],
            "stage_ramps": {"plated": {"part_age_years": [5.0, 15.0], "diameter_m": [0.02, 0.1]}},
            "stages": [
                {"name": "smooth", "colour": [120, 120, 90], "colour_variation": [100, 100, 80], "blotch_m": [0.05, 0.05], "roughness": 0.5, "fibre_depth_m": 0.0},
                {"name": "plated", "colour": [70, 60, 50], "colour_variation": [90, 80, 70], "blotch_m": [0.05, 0.1], "roughness": 0.9, "fibre_depth_m": 0.0,
                 "plates": {"size_m": [0.02, 0.08], "furrow_colour": [20, 18, 15], "furrow_width": 0.8, "cross_crack": 0.3}},
            ],
        },
        "leaves": look["leaves"],
        "game": look["game"],
    }
    tiles = tx.make_tiles(other)
    st = ap.part_state(other, np.array([1.0, 30.0]), np.array([0.01, 0.3]), np.array([1.0, 1.0]), 20.0, 30.0)
    assert st["weights"][1][0] == 0.0 and st["weights"][1][1] == 1.0 and (st["peel"] == 0.0).all()
    prof = tx.StemProfile(np.array([0.0, 5.0]), np.array([0.1, 0.02]), np.array([30.0, 3.0]), np.array([0.2, 0.04]), np.array([0.0, 5.0]))
    bake = tx.bake_stem(other, tiles, prof, lambda a, d, z: ap.part_state(other, a, d, z, 5.0, 20.0), [])
    assert bake["albedo"].shape == (64, 32, 3) and np.isfinite(bake["normal"]).all()
    assert bake["albedo"][:8].mean() < bake["albedo"][-8:].mean()      # plates at the base, smooth at the top
    atlas = tx.bake_branch_atlas(other, tiles, [None, None])
    assert atlas["albedo"].shape == (64, 256, 3)


def test_atlas_columns_fit_and_stem_rows_invert(look):
    lay = tx.atlas_layout(look)
    W, H = look["bark"]["atlas_px"]
    assert len(lay) == len(look["bark"]["branch_circumference_m"])
    assert all(0 <= x0 < x1 <= W for x0, x1, _ in lay)
    assert all(a[1] < b[0] for a, b in zip(lay, lay[1:]))
    s = np.linspace(0.0, 24.0, 97)
    assert tx.stem_s(look, tx.stem_v(look, s, 24.0), 24.0) == pytest.approx(s, abs=1e-9)
    assert tx.stem_v(look, 24.0, 24.0) == pytest.approx(1.0)
    # most rows go to the part a player stands next to, and the same rows at any age past it
    z, share = look["bark"]["stem_rows"][0]
    assert tx.stem_v(look, z, 24.0) == pytest.approx(share) and tx.stem_v(look, z, 12.0) == pytest.approx(share)


# -- the mesher ----------------------------------------------------------------------------------
def test_the_default_mesh_is_untouched_by_the_setting():
    assert mesh.MeshSettings().ring_attributes is False


# -- the .glb writer and its check ---------------------------------------------------------------
def _small_glb(path):
    g = GameGLB(path, "t", {"note": "test"})
    V = np.array([[0, 0, 0], [1, 0, 0], [0, 0, 1.0]])
    N = np.array([[0, -1.0, 0]] * 3)
    m = g.add_material({"name": "m", "pbrMetallicRoughness": {"metallicFactor": 0.0}})
    g.add_mesh("a", m, V, N, np.array([[0, 1, 2]]), uv=np.array([[0, 0], [1, 0], [0, 1.0]]), colour=np.ones((3, 4)), attributes={"NODE_ID": np.arange(3)})
    return g.write()


def test_glb_writer_round_trips(tmp_path):
    p = tmp_path / "a.glb"
    assert _small_glb(p)["triangles"] == 1
    info = validate_glb(p)
    assert info == {"triangles": 1, "vertices": 3, "meshes": 1, "materials": 1, "images": 0, "extensions_used": []}
    import trimesh

    scene = trimesh.load(p, process=False)
    g = list(scene.geometry.values())[0]
    # z-up in, y-up out, as glTF requires
    assert np.asarray(g.vertices)[2] == pytest.approx([0.0, 1.0, 0.0])


def test_the_check_catches_a_damaged_file(tmp_path):
    p = tmp_path / "a.glb"
    _small_glb(p)
    good = p.read_bytes()
    p.write_bytes(good[:-8])
    with pytest.raises(ValueError):
        validate_glb(p)
    # an index out of range
    n_json = struct.unpack_from("<I", good, 12)[0]
    doc = json.loads(good[20:20 + n_json])
    blob = bytearray(good[20 + n_json + 8:])
    prim = doc["meshes"][0]["primitives"][0]
    acc = doc["accessors"][prim["indices"]]
    at = doc["bufferViews"][acc["bufferView"]]["byteOffset"]
    blob[at:at + 4] = struct.pack("<I", 99)
    js = json.dumps(doc).encode()
    js += b" " * (-len(js) % 4)
    p.write_bytes(struct.pack("<4sII", b"glTF", 2, 12 + 8 + len(js) + 8 + len(blob)) + struct.pack("<I4s", len(js), b"JSON") + js + struct.pack("<I4s", len(blob), b"BIN\x00") + bytes(blob))
    with pytest.raises(ValueError, match="out of range"):
        validate_glb(p)


# -- the whole way through -----------------------------------------------------------------------
SMALL = ["bark.tile_px=256", "bark.stem_texture_px=[128,512]", "bark.atlas_px=[512,256]", "game.lods=" + json.dumps(
    [{"name": "lod0", "kind": "full", "budget": None, "stem_texture_scale": 1.0, "atlas_scale": 1.0, "leaf_kind": "blades", "peel_strips": 1},
     {"name": "lod1", "kind": "reduced", "budget": 4000, "wood_share": 0.4, "stem_texture_scale": 0.5, "atlas_scale": 0.5, "leaf_kind": "cards", "peel_strips": 0},
     {"name": "lod2", "kind": "far", "budget": 12, "cards": 3, "texture_px": 128}]), "game.leaf_card.texture_px=256"]


def _run_export(out, ages="6,8", seasons="summer,autumn,winter"):
    from argparse import Namespace

    import game_export as ge

    ge.main_export(Namespace(ages=ages, seasons=seasons, out=str(out), state=None, species="betula_pendula", seed=1, environment="sweden_open_field",
                             stand=True, set=[], budget=[], look=SMALL, levels=""))


@pytest.fixture(scope="module")
def exported(tmp_path_factory):
    """A small tree at two ages, in three seasons, through the real export, with small textures."""
    out = tmp_path_factory.mktemp("game")
    _run_export(out)
    return out, json.loads((out / "game_manifest.json").read_text(encoding="utf-8"))


def test_every_file_loads_and_every_level_keeps_its_budget(exported):
    import game_export as ge

    out, doc = exported
    files = sorted(p.name for p in out.glob("*.glb"))
    assert len(files) == 2 * 3 * 3
    assert len(ge.check_files(out)) == len(files)
    for st in doc["stages"]:
        for levels in st["seasons"].values():
            assert levels["lod1"]["triangles"] <= 4000 and levels["lod1"]["within_budget"]
            assert levels["lod2"]["triangles"] == 12
            assert levels["lod0"]["triangles"] > levels["lod1"]["triangles"] > levels["lod2"]["triangles"]


def test_leaves_at_every_level_are_the_models(exported):
    out, doc = exported
    for st in doc["stages"]:
        # the model's own leaf area, near enough: leaves are whole numbers per node
        assert st["exported_leaf_area_m2"] == pytest.approx(st["model_leaf_area_m2"], rel=0.03)
        # the cards stand for the same area
        cards = st["seasons"]["summer"]["lod1"]["parts"]
        assert cards["leaf_area_represented_m2"] == pytest.approx(st["model_leaf_area_m2"], rel=0.03)


def test_materials_are_pbr_with_textures_and_winter_has_no_leaves(exported):
    out, doc = exported
    st = doc["stages"][-1]
    near = read_glb(out / st["seasons"]["summer"]["lod0"]["file"])[0]
    names = {m["name"]: m for m in near["materials"]}
    for n in ("bark_stem", "bark_branch"):
        pbr = names[n]["pbrMetallicRoughness"]
        assert "baseColorTexture" in pbr and "metallicRoughnessTexture" in pbr and "normalTexture" in names[n]
        assert "heightTexture" in names[n]["extras"]
    leaf = names["leaf_blade"]
    assert leaf["alphaMode"] == "MASK" and leaf["doubleSided"] is True
    assert "KHR_materials_diffuse_transmission" in leaf["extensions"]
    assert "KHR_materials_diffuse_transmission" in near["extensionsUsed"] and "extensionsRequired" not in near
    far = read_glb(out / st["seasons"]["summer"]["lod2"]["file"])[0]
    assert far["materials"][0]["alphaMode"] == "MASK" and not far["materials"][0].get("doubleSided")
    winter = read_glb(out / st["seasons"]["winter"]["lod0"]["file"])[0]
    assert not any(m["name"].startswith("leaf") for m in winter["materials"])


def test_autumn_is_yellower_than_summer_in_the_file(exported):
    from treegen.export import glb_accessor

    out, doc = exported
    st = doc["stages"][-1]

    def colour(season):
        d, blob = read_glb(out / st["seasons"][season]["lod0"]["file"])
        m = next(x for x in d["meshes"] if x["name"] == "leaves")["primitives"][0]
        factor = d["materials"][m["material"]]["pbrMetallicRoughness"]["baseColorFactor"]
        c = glb_accessor(d, blob, m["attributes"]["COLOR_0"]) / 65535.0
        return c[:, :3].mean(0) * np.asarray(factor[:3])

    s, a = colour("summer"), colour("autumn")
    assert s[1] > s[0]
    assert a[0] > a[1] and a[0] > 2.0 * s[0]


def test_a_second_export_gives_the_same_files(exported, tmp_path):
    """Everything is seeded: the same tree and the same settings give the same bytes."""
    out, doc = exported
    _run_export(tmp_path, seasons="summer")
    for level in ("lod0", "lod1", "lod2"):
        name = doc["stages"][0]["seasons"]["summer"][level]["file"]
        first, second = read_glb(out / name), read_glb(tmp_path / name)
        assert first[1] == second[1], name


def test_neighbouring_stages_line_up(look):
    """The same stem five years apart, thicker and a little rougher: same place on the stem, same
    pattern.  The manifest holds the same figure for a real tree."""
    small = copy.deepcopy(look)
    small["bark"]["tile_px"] = 256
    tiles = tx.make_tiles(small)

    def bake(age, r0):
        s = np.linspace(0.0, 15.0, 61)
        r = r0 * (1.0 - s / 16.0)
        prof = tx.StemProfile(s, r, np.maximum(age - s, 0.0), 2.0 * r, s)
        return tx.bake_stem(small, tiles, prof, lambda a, d, z: ap.part_state(small, a, d, z, 15.0, 200.0 * r0), [], px=(256, 1024))["albedo"].mean(-1)

    a, b = bake(40, 0.10), bake(45, 0.108)
    n = int(float(small["bark"]["stem_rows"][0][1]) * a.shape[0])
    assert np.corrcoef(a[:n].ravel(), b[:n].ravel())[0, 1] > 0.8
    assert abs(float(a[:n].mean() - b[:n].mean())) < 0.05


def test_a_stem_passing_a_doubling_keeps_most_of_its_pattern(look):
    """Past each doubling of circumference the tile count changes, patch by patch."""
    small = copy.deepcopy(look)
    small["bark"]["tile_px"] = 256
    tiles = tx.make_tiles(small)

    def bake(r0):
        s = np.linspace(0.0, 3.0, 13)
        prof = tx.StemProfile(s, np.full_like(s, r0), np.full_like(s, 40.0), np.full_like(s, 2.0 * r0), s + 8.0)
        return tx.bake_stem(small, tiles, prof, lambda a, d, z: ap.part_state(small, a, d, z, 30.0, 200.0 * r0), [], px=(256, 512))["albedo"].mean(-1)

    # circumferences of 0.98 m and 1.02 m: either side of 1 m
    a, b = bake(0.156), bake(0.162)
    assert np.corrcoef(a.ravel(), b.ravel())[0, 1] > 0.8


# -- the Unreal target ---------------------------------------------------------------------------
def test_the_new_mesh_settings_are_off_unless_asked():
    s = mesh.MeshSettings()
    assert s.drop_hidden_rings is False and s.ring_tolerance == 0.0 and s.ring_tolerance_m == 0.0
    assert s.stem_edge_by_height == () and s.buttress_hold_m == 0.0 and s.no_stem_ridges is False


def test_a_dense_run_of_ring_samples_doesnt_drop_itself_whole():
    gs = np.arange(0.0, 1.0, 0.001)
    keep = mesh._spaced_samples(gs, np.full(len(gs), 0.01), np.zeros(len(gs), np.int64))
    # against its neighbour every one of these would go: every sample is within 3 mm of the one before
    kept = gs[keep]
    assert np.diff(kept).max() < 0.005 and len(kept) > 200
    # and a new axis always starts
    sa = np.r_[np.zeros(500, np.int64), np.ones(500, np.int64)]
    assert mesh._spaced_samples(gs, np.full(len(gs), 0.01), sa)[500]


def test_thinning_keeps_what_shapes_the_tube():
    # a straight even run of rings needs only its ends, up to the longest span
    ss = np.linspace(0.0, 1.0, 21)
    X = np.c_[np.zeros(21), np.zeros(21), ss]
    R = np.full(21, 0.01)
    keep = mesh._thin_rings(ss, X, R, 0.1, 0.0, np.zeros(21, bool), 10.0)
    assert np.nonzero(keep)[0].tolist() == [0, 20]
    # ... and no run is longer than asked, so wind can still bend it
    keep = mesh._thin_rings(ss, X, R, 0.1, 0.0, np.zeros(21, bool), 0.5)
    assert np.diff(ss[keep]).max() <= 0.5 + 1e-9
    # a bend stays, and what's drawn stays within the tolerance of every ring
    Y = X.copy()
    Y[10, 0] = 0.005
    keep = mesh._thin_rings(ss, Y, R, 0.1, 0.0, np.zeros(21, bool), 10.0)
    assert keep[10]
    back = np.stack([np.interp(ss, ss[keep], Y[keep, k]) for k in range(3)], 1)
    assert np.linalg.norm(back - Y, axis=1).max() <= 0.1 * 0.01 + 1e-9
    # rings told to stay, stay
    fixed = np.zeros(21, bool)
    fixed[3] = True
    assert mesh._thin_rings(ss, X, R, 0.1, 0.0, fixed, 10.0)[3]


def _run_unreal(out, ages="6,8", seasons="summer,winter", look=()):
    from argparse import Namespace

    import game_export as ge

    ge.main_export(Namespace(ages=ages, seasons=seasons, out=str(out), state=None, species="betula_pendula", seed=1, environment="sweden_open_field",
                             stand=True, set=[], budget=[], look=SMALL + list(look), levels="", target="unreal"))


@pytest.fixture(scope="module")
def unreal_export(tmp_path_factory):
    out = tmp_path_factory.mktemp("unreal")
    _run_unreal(out)
    return out, json.loads((out / "game_manifest.json").read_text(encoding="utf-8"))


def _attribute(d, blob, prim, name, dtype, width):
    acc = d["accessors"][prim["attributes"][name]]
    view = d["bufferViews"][acc["bufferView"]]
    return np.frombuffer(blob, dtype, acc["count"] * width, view["byteOffset"] + acc.get("byteOffset", 0)).reshape(-1, width)


def _named(d, name):
    return next(m["primitives"][0] for m in d["meshes"] if m["name"] == name)


def test_unreal_files_are_where_the_games_scripts_look(unreal_export):
    from PIL import Image

    out, doc = unreal_export
    asset = doc["asset"]
    split = out / "SourceArt" / "PolyHaven_split" / asset
    textures = out / "SourceArt" / "PolyHaven" / asset / "textures"
    assert (split / f"{asset}_age008.gltf").exists() and (split / f"{asset}_age008.bin").exists()
    assert (split / f"{asset}_age008_winter_lod1.gltf").exists() and (split / f"{asset}_age008_roots.gltf").exists()
    names = sorted(p.name for p in textures.iterdir())
    assert names and all(n.endswith(("_diff_2k.png", "_nor_gl_2k.png", "_rough_2k.png")) for n in names)
    for p in textures.iterdir():
        im = Image.open(p)
        # the game's rule: 16-bit PNGs import blank
        assert im.mode in ("RGB", "RGBA")
        # its alpha rule picks the master: bark is opaque, leaves and strips have alpha in the colour map
        if "_diff_" in p.name:
            assert (im.mode == "RGBA") == ("_bark_diff" not in p.name and "_bark_lod1_diff" not in p.name)
    frag = json.loads((out / "fragments" / "flora_variants.json").read_text(encoding="utf-8"))
    assert f"{asset}_age008" in {f["id"] for f in frag}


def test_unreal_files_hold_only_what_the_import_keeps(unreal_export):
    out, _ = unreal_export
    files = list(out.rglob("*.gltf"))
    assert files
    for path in files:
        assert validate_glb(path)["triangles"] > 0
        d, _ = read_glb(path)
        assert not d.get("extensionsRequired")
        for mesh_ in d["meshes"]:
            for prim in mesh_["primitives"]:
                a = prim["attributes"]
                # Nanite keeps 4
                assert "TEXCOORD_0" in a and sum(k.startswith("TEXCOORD_") for k in a) <= 4
                # wind data, 8-bit: what the import stores anyway
                c = d["accessors"][a["COLOR_0"]]
                assert c["type"] == "VEC4" and c["componentType"] == 5121 and c["normalized"] is True


def test_unreal_colour0_is_the_games_wind_data(unreal_export):
    out, doc = unreal_export
    d, blob = read_glb(out / doc["stages"][-1]["seasons"]["summer"]["lod0"]["file"])

    def colours(name):
        return _attribute(d, blob, _named(d, name), "COLOR_0", np.uint8, 4) / 255.0

    leaf, stem = colours("leaves"), colours("stem")
    d2, blob2 = read_glb(out / doc["stages"][-1]["roots"]["files"]["lod0"]["file"])
    root = _attribute(d2, blob2, d2["meshes"][0]["primitives"][0], "COLOR_0", np.uint8, 4) / 255.0
    assert leaf[:, 2].min() == 1.0 and stem[:, 2].max() == 0.0           # blue: leaves
    assert stem[:, 3].min() == 1.0 and leaf[:, 3].max() < 1.0            # alpha: 255 off leaves, leaf ids to 254
    assert stem[:, 0].min() < 0.05 and leaf[:, 0].max() > 0.5            # red: flex grows along the stems
    assert np.ptp(leaf[:, 1]) == 0.0 and leaf[0, 1] == stem[0, 1]        # green: one phase for the tree
    assert root[:, 0].max() == 0.0                                       # roots don't sway


def test_unreal_leaves_are_the_models_area_with_real_outlines(unreal_export):
    out, doc = unreal_export
    for st in doc["stages"]:
        assert st["exported_leaf_area_m2"] == pytest.approx(st["model_leaf_area_m2"], rel=0.03)
        d, blob = read_glb(out / st["seasons"]["summer"]["lod0"]["file"])
        prim = _named(d, "leaves")
        V = _attribute(d, blob, prim, "POSITION", "<f4", 3)
        idx = d["accessors"][prim["indices"]]
        F = np.frombuffer(blob, "<u4", idx["count"], d["bufferViews"][idx["bufferView"]]["byteOffset"]).reshape(-1, 3)
        area = 0.5 * np.linalg.norm(np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]]), axis=1).sum()
        # the mesh's own area, fold and all, within what its coarse teeth and curl add or take
        assert area == pytest.approx(st["exported_leaf_area_m2"], rel=0.15)
        # 26 in the blade, its main teeth and its fold, 4 in the stalk
        assert len(F) == st["exported_leaves"] * 30
        # the small teeth are cut by the colour map's alpha
        assert next(m for m in d["materials"] if m["name"].endswith("_leaf"))["alphaMode"] == "MASK"
        assert "leaves" not in {m["name"] for m in read_glb(out / st["seasons"]["winter"]["lod0"]["file"])[0]["meshes"]}


def test_unreal_roots_are_the_models_and_meet_the_tree(unreal_export):
    out, doc = unreal_export
    for st in doc["stages"]:
        rt = st["roots"]
        line = rt["ground_line_m"]
        assert line < 0.0
        below = rt["files"]["lod0"]
        # the model's depth, less the ground line, as the roots sink by that going out
        assert below["triangles"] > 0 and below["min_z_m"] == pytest.approx(line - rt["deepest_m"], abs=0.1)
        near = st["seasons"]["summer"]["lod0"]
        # a small tree may have no root thick enough to show; what shows meets what doesn't, with no seam
        if near["parts"].get("surface_roots"):
            d, blob = read_glb(out / near["file"])
            A = _attribute(d, blob, _named(d, "surface_roots"), "POSITION", "<f4", 3)
            d2, blob2 = read_glb(out / below["file"])
            B = _attribute(d2, blob2, d2["meshes"][0]["primitives"][0], "POSITION", "<f4", 3)
            assert {tuple(p) for p in np.round(A, 5).tolist()} & {tuple(p) for p in np.round(B, 5).tolist()}


def test_unreal_origin_keeps_the_games_ground_moss_off(unreal_export):
    """M_Surface's moss at a model's base reads height above the origin, over GroundBlendCm 20 + 6 of
    noise, and smears up an upright surface: nothing in the file may be that low.  The game seats by the
    lowest point, so every level's lowest point is one place: the ground line less the game's sink."""
    out, doc = unreal_export
    for st in doc["stages"]:
        o = st["origin"]
        assert o["lowest_in_file_m"] * 100.0 >= 26.0
        assert o["ground_in_file_m"] - o["lowest_in_file_m"] == pytest.approx(doc["fragments"]["sink_m"], abs=0.001)
        for level in st["seasons"]["summer"].values():
            d, _ = read_glb(out / level["file"])
            # y is up in the file
            lowest = min(d["accessors"][p["attributes"]["POSITION"]]["min"][1] for m in d["meshes"] for p in m["primitives"])
            # not lower, or that moss comes on; about there, or the seat is off.  A coarse level's foot may stop a little short
            assert o["lowest_in_file_m"] - 0.002 <= lowest <= o["lowest_in_file_m"] + 0.03


def test_unreal_stem_relief_is_almost_nothing_on_young_white_bark(unreal_export):
    _, doc = unreal_export
    for st in doc["stages"]:
        lo, hi = st["stem_height_range_m"]
        assert -0.008 < lo <= 0.0 and 0.0 <= hi < 0.008


def test_the_stem_mesh_is_finest_where_its_cracks_are_deep():
    import treegen.game_unreal as gu

    class Wood:
        @staticmethod
        def state(age, d, z):
            return {"fissure_m": np.where(np.asarray(z) < 1.0, 0.02, 0.0)}

    cfg = {"full_at_fissure_m": 0.006, "edge_coarse_m": 0.03, "edge_fine_m": 0.005}
    z = np.array([0.0, 5.0])
    t = np.asarray(gu.stem_edges(Wood(), z, np.array([30.0, 1.0]), np.array([0.3, 0.05]), -0.1, 0.1, cfg))
    assert np.interp(0.5, t[:, 0], t[:, 1]) == pytest.approx(0.005)
    assert np.interp(3.0, t[:, 0], t[:, 1]) == pytest.approx(0.03)


def _root_tube(z0, z1, r0, r1, sides=8, rings=12):
    """One root as a mesh, running out along x."""
    s = np.linspace(0.0, 1.0, rings)
    a = np.linspace(0.0, 2.0 * np.pi, sides, endpoint=False)
    V, along, radius = [], [], []
    for t in s:
        r = r0 + (r1 - r0) * t
        c = np.array([2.0 * t, 0.0, z0 + (z1 - z0) * t])
        V += [c + np.array([0.0, r * np.cos(b), r * np.sin(b)]) for b in a]
        along += [2.0 * t] * sides
        radius += [r] * sides
    V = np.array(V)
    F = np.array([[0, 1, 2]])
    attrs = {"axis_id": np.ones(len(V), np.int32), "ring_along": np.array(along, np.float32), "radius": np.array(radius, np.float32)}
    return mesh.MeshData(V, F, np.tile([0.0, 0.0, 1.0], (len(V), 1)), attrs), sides


def test_a_root_lies_on_the_ground_and_its_thin_end_is_under_it():
    import treegen.game_unreal as gu

    cfg = {"sink_length_radii": 2.0, "surface_min_radius_m": 0.006, "surface_min_radius_share": 0.09, "centre_above_ground_radii": 0.25, "visible_radii": 12.0, "under_share": 0.85, "sink_power": 1.3, "flow_out_radii": 3.0, "flow_width_radii": 1.25, "flow_up_radii": 4.0, "flow_max_share": 0.8}
    line = -0.2
    # a strut: high at the stem, as the model's roots are measured from its own zero
    md, sides = _root_tube(0.1, 0.1, 0.09, 0.002)
    out = gu.sink_roots(md, line, np.array([0.0, 0.0]), 0.1, 0.14, cfg)
    centres = out.vertices.reshape(-1, sides, 3).mean(1)[:, 2]
    r = md.attributes["radius"][::sides]
    thick = r >= 0.09 * 0.14
    assert np.all(centres[thick] <= line + 0.25 * r[thick] + 1e-6)
    # the end is under the ground, whole
    assert centres[-1] + r[-1] < line
    # and the section stays round: every vertex of a ring moved by the same amount
    moved = (out.vertices - md.vertices)[:, 2].reshape(-1, sides)
    assert np.ptp(moved, axis=1).max() < 1e-6
    # only the height moves
    assert np.array_equal(out.vertices[:, :2], md.vertices[:, :2])


def test_a_root_goes_under_with_a_rounded_end_not_a_long_point():
    import treegen.game_unreal as gu

    cfg = {"sink_length_radii": 15.0, "surface_min_radius_m": 0.006, "surface_min_radius_share": 0.25, "centre_above_ground_radii": -0.25, "visible_radii": 8.0, "under_share": 0.85, "sink_power": 1.3,
           "flow_out_radii": 3.0, "flow_width_radii": 1.25, "flow_up_radii": 4.0, "flow_max_share": 0.8}
    line = -0.2
    md, sides = _root_tube(0.0, -0.1, 0.06, 0.004, rings=120)
    out = gu.sink_roots(md, line, np.array([0.0, 0.0]), 0.1, 0.17, cfg)
    centres = out.vertices.reshape(-1, sides, 3).mean(1)[:, 2]
    r = md.attributes["radius"][::sides]
    x = md.vertices.reshape(-1, sides, 3).mean(1)[:, 0]
    crest = centres + r - line
    shows = crest > 0.0
    # it shows, and it's gone by eight of its radii along, long before the model's thin end
    assert shows.any() and x[shows].max() < 0.1 + 8.0 * 0.06 + 0.05
    # and it's gone before it's thin, so nothing tapers to a point on the ground
    assert r[shows].min() > 0.85 * 0.25 * 0.17 * 0.9
    # it sinks all along what shows, going down from ring to ring
    run = shows & (x > 0.1)
    assert np.all(np.diff(crest[run]) <= 1e-6)
    assert crest[run][0] > 3.0 * crest[run][int(0.8 * run.sum())]


def test_a_swell_runs_out_along_a_root_and_up_the_stem_to_nothing():
    import treegen.game_unreal as gu

    # out 0.2 m at a root's crest 0.04 m over the ground, gone 0.3 m above that
    flows = np.array([[0.5, 0.2, 0.4, 0.3, 0.04]])
    at = gu.flow_offset(np.full(5, 0.5), np.array([0.0, 0.04, 0.0625, 0.19, 0.5]), flows)
    assert at[1] == pytest.approx(0.2) and at[4] == 0.0
    # it spreads on to the ground below the crest, so no upright lip
    assert at[0] > at[1] > at[2] > at[3] > at[4]
    # and flattest where it lands, steep higher on the stem
    assert (at[1] - at[2]) / (0.0625 - 0.04) > 1.2 * (at[2] - at[3]) / (0.19 - 0.0625)
    # nothing on the far side of the stem
    assert gu.flow_offset(np.array([0.5 + np.pi]), np.array([0.0]), flows)[0] < 1e-6


def test_the_stems_foot_takes_whole_rings_so_a_tilted_one_cant_show():
    import treegen.game_unreal as gu

    # a stem's tube, upright to z = -0.3, then rings tilted by a taproot that leans off, one side as high as the ground
    sides, rings = 16, []
    a = np.linspace(0.0, 2.0 * np.pi, sides, endpoint=False)
    heights = [0.0, -0.1, -0.2, -0.3, -0.35, -0.4]
    tilt = [0.0, 0.0, 0.0, 0.0, 0.5, 0.8]
    V = np.array([[0.2 * np.cos(b), 0.2 * np.sin(b), z + t * 0.2 * np.cos(b)] for z, t in zip(heights, tilt) for b in a])
    along = np.repeat(-np.array(heights, float), sides)
    F = []
    for r in range(len(heights) - 1):
        for k in range(sides):
            p, q = r * sides + k, r * sides + (k + 1) % sides
            F += [[p, q, p + sides], [q, q + sides, p + sides]]
    attrs = {"axis_id": np.zeros(len(V), np.int32), "ring_along": along.astype(np.float32), "radius": np.full(len(V), 0.2, np.float32)}
    md = mesh.MeshData(V, np.array(F), np.tile([1.0, 0.0, 0.0], (len(V), 1)), attrs)
    cfg = {"surface_min_radius_m": 0.006, "surface_min_radius_share": 0.14, "surface_depth_m": 0.1}
    line = -0.2
    foot, surface, below = gu.split_roots(md, cfg, line, 0.2)
    # the foot stops at the cut, at -0.3, level; the tilted rings' high sides, up to -0.24, are under
    assert foot.vertices[:, 2].min() == pytest.approx(-0.3)
    assert np.ptp(foot.vertices[foot.vertices[:, 2] < -0.25, 2]) == pytest.approx(0.0)
    assert surface is None and below is not None


def test_a_thick_roots_swell_ends_in_a_slope_not_a_wall():
    import treegen.game_unreal as gu

    # as at age 60 with the default roots: a root half the stem's radius
    out_m, crest = 0.2, 0.06
    flows = np.array([[0.0, out_m, 0.4, 0.3, crest]])
    at = gu.flow_offset(np.zeros(2), np.array([0.0, crest]), flows)
    # from the crest down to the ground it runs out by more than it drops
    assert at[0] - at[1] >= 1.5 * crest


def test_a_swell_covers_its_root_where_it_comes_out_of_the_stem(look):
    import treegen.game_unreal as gu

    cfg = {**look["game"]["unreal"]["roots"], "sink_length_radii": 15.0, "surface_min_radius_share": 0.25}
    line, foot_r, collar, r = -0.2, 0.15, 0.17, 0.05
    out_m, width, up_m, crest = gu.flow_shape(r, foot_r, cfg)
    flows = np.array([[0.0, out_m, width, up_m, crest]])
    # the root comes out of the swell at its end, top and side
    assert gu.flow_offset(np.array([0.0]), np.array([crest]), flows)[0] == pytest.approx(out_m)
    assert gu.flow_offset(np.array([r / foot_r]), np.array([crest - r]), flows)[0] > 0.5 * out_m
    # and the root itself stays low there: nothing raises it to meet the swell
    md, sides = _root_tube(-0.1, -0.15, r, 0.004, rings=300)
    moved = gu.sink_roots(md, line, np.array([-foot_r, 0.0]), foot_r, collar, cfg)
    tops = moved.vertices.reshape(-1, sides, 3).mean(1)[:, 2] + md.attributes["radius"][::sides] - line
    x = md.vertices.reshape(-1, sides, 3).mean(1)[:, 0]
    assert tops[x >= out_m].max() <= crest + 1e-6
    assert tops.max() <= (1.0 + cfg["centre_above_ground_radii"]) * r + 1e-6
    # only the height moved
    assert np.array_equal(moved.vertices[:, :2], md.vertices[:, :2])


def test_the_flows_come_from_the_roots_at_the_stem(look):
    import treegen.game_unreal as gu

    cfg = look["game"]["unreal"]["roots"]
    md, sides = _root_tube(0.0, -0.1, 0.06, 0.004, rings=40)
    flows = gu.root_flows(md, np.array([0.0, 0.0]), 0.15, cfg)
    assert flows.shape == (1, 5) and flows[0, 0] == pytest.approx(0.0, abs=0.01)
    # a root that starts far out is no swell on the stem
    assert not len(gu.root_flows(md, np.array([-3.0, 0.0]), 0.15, cfg))


def test_moss_is_patches_on_one_side_with_no_edge(look):
    import treegen.game_unreal as gu

    cfg = look["game"]["unreal"]["roots"]
    above = np.linspace(0.0, 1.3, 400)
    u = (np.arange(512) + 0.5) / 512.0
    amount, _ = gu.moss_amount(above, u, np.ones(400), cfg, 77)
    toward = float(ap.hash01(np.array([77]), 72)[0])
    round_to = np.abs((u - toward + 0.5) % 1.0 - 0.5)
    near, far = amount[:80][:, round_to < 0.2], amount[:80][:, round_to > 0.3]
    assert near.mean() > 3.0 * far.mean()
    # not a coat, even low down on the side it favours
    assert (near > 0.1).mean() < 0.7
    # and on no side is it a band round the foot
    assert (far > 0.1).mean() < 0.15
    # and it thins out going up, with no level where it stops
    rows = amount.mean(1)
    assert rows[-1] == 0.0 and np.abs(np.diff(np.convolve(rows, np.ones(20) / 20.0, mode="valid"))).max() < 0.25 * rows[:40].mean()


def _rough_at(look, seed, age, z):
    """The rough stage's weight round a stem at these heights, 256 places round."""
    edge = tx.UnevenTop(look, age, seed)
    u = (np.arange(256) + 0.5) / 256.0
    n, W = len(z), len(u)
    at = edge.heights(u, z, z)
    return ap.part_state(look, np.full((n, W), float(age)), np.full((n, W), 0.3), at, 25.0, 30.0)["weights"][-1]


@pytest.fixture(scope="module")
def uneven(look):
    out = copy.deepcopy(look)
    out["bark"]["uneven_top"]["strength"] = 1.0
    return out


def test_the_rough_base_is_level_unless_asked(look):
    assert float(look["bark"]["uneven_top"]["strength"]) == 0.0
    assert tx.uneven_top(look, 60.0, 5) is None


def test_the_unreal_target_asks_for_an_uneven_base(look):
    import treegen.game_unreal as gu

    assert tx.uneven_top(gu.unreal_look(look), 60.0, 5) is not None


def test_the_rough_base_stops_at_no_one_level_and_differs_by_tree(uneven):
    z = np.linspace(0.05, 7.0, 400)
    tops = {}
    for seed in range(1, 7):
        w = _rough_at(uneven, seed, 60, z)
        # the highest it's half way on, column by column
        tops[seed] = z[(w > 0.5).shape[0] - 1 - np.argmax((w > 0.5)[::-1], axis=0)]
        # round one stem, more than a metre between its lowest and its highest
        assert np.percentile(tops[seed], 95) - np.percentile(tops[seed], 5) > 1.0
    means = [float(t.mean()) for t in tops.values()]
    assert max(means) - min(means) > 0.5


def test_the_rough_base_leaves_white_plates_and_grows_with_the_tree(uneven):
    z = np.linspace(0.05, 7.0, 400)
    w = _rough_at(uneven, 5, 60, z)
    # part way: the stage has taken the furrows and left the plates
    assert ((w > 0.2) & (w < 0.8))[z < 4.0].mean() > 0.1
    # solid black only low down, somewhere on the stem, and nothing near the top of the range
    assert w[z < 0.3].max() > 0.9 and w[z > 6.5].max() < 0.5
    # an older tree has more of it, in the same place: the pattern is the tree's
    young, old = _rough_at(uneven, 5, 30, z), _rough_at(uneven, 5, 60, z)
    assert old.sum() > 1.5 * young.sum()
    rows = z < 3.0
    assert np.corrcoef(young[rows].ravel(), old[rows].ravel())[0, 1] > 0.5


def test_leaves_hang_at_the_measured_angles(look):
    import treegen.game_unreal as gu

    cfg = look["game"]["unreal"]["leaf"]
    n = 4000
    z = np.linspace(0.0, 1.0, n)
    az = np.linspace(0.0, 40.0, n)
    along = np.stack([np.cos(az), np.sin(az), 0.0 * az], 1)
    leaves = ap.LeafInstances(node=np.zeros(n, np.int64), base=np.zeros((n, 3)), along=along, across=np.stack([-np.sin(az), np.cos(az), 0.0 * az], 1), length=np.ones(n), width=np.ones(n),
                              area=np.ones(n), sun=np.ones(n), delay=np.zeros(n))
    out = gu.hang_leaves(leaves, z, cfg)
    # what was measured is a blade's slope from base to tip, which takes in the curl the mesh will give it
    curl = cfg["curl"][0] + (cfg["curl"][1] - cfg["curl"][0]) * ap.hash01(np.arange(n), 86)
    angle = np.degrees(np.arcsin(-out.along[:, 2]) + np.arctan(curl))
    assert np.all(angle > 0.0)                                      # all hang
    assert angle[z > 0.97].mean() == pytest.approx(55.0, abs=4.0)   # Hagemeier & Leuschner 2019a: at the top
    assert angle[z < 0.3].mean() == pytest.approx(30.0, abs=4.0)    # and in the lowest shade crown


def test_the_leaf_outline_is_a_real_one(look):
    """Atkinson & Codling 1986 and the floras: triangular, long drawn out tip, large teeth carrying small."""
    import treegen.game_unreal as gu

    sh = gu.unreal_look(look)["leaves"]["shape"]
    m = tx.leaf_margin(sh, 0)
    t = np.linspace(0.0, 1.0, 501)
    half = tx.leaf_half_at(m, t) * m["hmax"]
    assert 0.2 < t[np.argmax(half)] < 0.45                          # widest low down
    assert half[-1] == pytest.approx(0.0, abs=1e-6)                 # comes to a point
    width_at = lambda a: half[np.argmin(np.abs(t - a))]  # noqa: E731
    # against a straight line from the widest point to the tip: curved out at the shoulder, drawn in to the tip
    straight = lambda a: half.max() * (1.0 - a) / (1.0 - t[np.argmax(half)])  # noqa: E731
    assert width_at(0.56) > 1.1 * straight(0.56)
    assert width_at(0.94) < 0.9 * straight(0.94)
    assert len(m["tips"][1]) == int(sh["main_teeth"]) and int(sh["minor_per_main"]) >= 1


def test_thinning_saves_triangles_and_leaves_the_stem_alone(unreal_export, tmp_path):
    out, doc = unreal_export
    _run_unreal(tmp_path, ages="8", seasons="summer", look=["game.unreal.ring_tolerance=0", "game.unreal.ring_tolerance_m=0"])
    all_rings = json.loads((tmp_path / "game_manifest.json").read_text(encoding="utf-8"))["stages"][0]["seasons"]["summer"]["lod0"]
    thinned = doc["stages"][-1]["seasons"]["summer"]["lod0"]
    assert thinned["parts"]["wood"] < all_rings["parts"]["wood"]
    assert thinned["parts"]["leaves"] == all_rings["parts"]["leaves"]
    for got in (all_rings, thinned):
        assert got["bounds"]["height_cm"] == pytest.approx(thinned["bounds"]["height_cm"], rel=0.002)


def test_the_generic_export_ignores_the_unreal_block(exported):
    out, doc = exported
    assert doc.get("target") != "unreal"
    assert not list(out.rglob("*.gltf"))
    near = read_glb(out / doc["stages"][-1]["seasons"]["summer"]["lod0"]["file"])[0]
    assert all("TEXCOORD_1" not in p["attributes"] for m in near["meshes"] for p in m["primitives"])
    # 16-bit colour, as it was
    prim = next(m["primitives"][0] for m in near["meshes"] if m["name"] == "leaves")
    assert near["accessors"][prim["attributes"]["COLOR_0"]]["componentType"] == 5123


def test_unreal_textures_are_powers_of_two_and_extras_are_plain(unreal_export):
    from PIL import Image

    out, doc = unreal_export
    # Unreal's import refuses other sizes
    for p in (out / "SourceArt" / "PolyHaven" / doc["asset"] / "textures").iterdir():
        w, h = Image.open(p).size
        assert w & (w - 1) == 0 and h & (h - 1) == 0, p.name
    # and logs an error for nested extras
    for path in out.rglob("*.gltf"):
        d, _ = read_glb(path)
        for extras in [d["asset"].get("extras", {})] + [m.get("extras", {}) for m in d["materials"]]:
            assert all(isinstance(v, (str, int, float, bool)) for v in extras.values())


def test_the_unreal_scripts_at_least_compile():
    import py_compile

    scripts = list((ROOT / "tools" / "unreal").glob("*.py")) + [ROOT / "tools" / "unreal_test.py"]
    assert len(scripts) >= 5
    for s in scripts:
        py_compile.compile(str(s), cfile=str(ROOT / "out" / "unreal_compile_check.pyc"), doraise=True)
