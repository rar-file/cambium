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
            assert (im.mode == "RGBA") == ("_bark_diff" not in p.name)
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

    leaf, stem, root = colours("leaves"), colours("stem"), colours("surface_roots")
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
        assert len(F) == st["exported_leaves"] * 4 * (8 - 1)
        # no alpha to lose: the colour map's alpha is solid on near leaves
        assert "alphaMode" not in next(m for m in d["materials"] if m["name"].endswith("_leaf"))
        assert "leaves" not in {m["name"] for m in read_glb(out / st["seasons"]["winter"]["lod0"]["file"])[0]["meshes"]}


def test_unreal_roots_are_the_models_and_meet_the_tree(unreal_export):
    out, doc = unreal_export
    for st in doc["stages"]:
        rt = st["roots"]
        line = rt["ground_line_m"]
        assert line < 0.0
        below = rt["files"]["lod0"]
        assert below["triangles"] > 0 and below["min_z_m"] == pytest.approx(-rt["deepest_m"], abs=0.1)
        near = st["seasons"]["summer"]["lod0"]
        assert near["parts"]["surface_roots"] > 0
        # the game seats a tree by its lowest point: here, the ground line and a little more
        assert near["bounds"]["min_z_cm"] == pytest.approx((line - 0.10) * 100.0, abs=4.0)
        d, blob = read_glb(out / near["file"])
        A = _attribute(d, blob, _named(d, "surface_roots"), "POSITION", "<f4", 3)
        d2, blob2 = read_glb(out / below["file"])
        B = _attribute(d2, blob2, d2["meshes"][0]["primitives"][0], "POSITION", "<f4", 3)
        # they share the vertices along their cut, so no seam
        assert {tuple(p) for p in np.round(A, 5).tolist()} & {tuple(p) for p in np.round(B, 5).tolist()}
        # and the part with the tree holds no thin root
        assert np.ptp(A[:, 1]) > 0.0


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
