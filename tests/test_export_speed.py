"""Faster exports change only PNG bytes and seconds: a map's pixels, a mesh's buffers and what an export bakes stay as they were.
Made-up data throughout, no tree grown.  The same is checked on whole exports of real trees by tools/export_timing.py, on the server."""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from treegen import export, game  # noqa: E402
from treegen import game_unreal as gu  # noqa: E402
from treegen.export import GameGLB, encode_image, read_glb, validate_glb  # noqa: E402


def _u8(rgb, alpha=None):
    """What a map's pixels are: the rule both writers have always used."""
    a = np.clip(np.asarray(rgb, np.float32), 0.0, 1.0)
    if alpha is not None:
        a = np.concatenate([a, np.clip(np.asarray(alpha, np.float32), 0.0, 1.0)[..., None]], axis=-1)
    return (a * 255.0 + 0.5).astype(np.uint8)


def _png(pixels, level):
    buf = io.BytesIO()
    Image.fromarray(pixels).save(buf, "PNG", optimize=False, compress_level=level)
    return buf.getvalue()


def _maps(rng, h=48, w=32):
    return {"rgb": rng.random((h, w, 3)).astype(np.float32), "alpha": rng.random((h, w)).astype(np.float32),
            "normal": rng.random((h, w, 3)).astype(np.float32) * 2.0 - 1.0, "rough": rng.random((h, w)).astype(np.float32)}


def _mesh(rng, n=6):
    return {"V": rng.random((n, 3)), "N": np.tile([0.0, -1.0, 0.0], (n, 1)), "F": np.array([[0, 1, 2], [3, 4, 5]]), "UV": rng.random((n, 2)),
            "T": np.tile([1.0, 0.0, 0.0, 1.0], (n, 1)), "node": np.arange(n), "radius": rng.random(n)}


def _buffers(glb: GameGLB) -> list:
    """Every accessor's bytes: positions, normals, tangents, UVs, colours, attributes, indices, mesh by mesh."""
    return [bytes(glb.blob[v["byteOffset"]:v["byteOffset"] + v["byteLength"]]) for v in (glb.views[a["bufferView"]] for a in glb.accessors)]


# -- PNG compression ------------------------------------------------------------------------------
@pytest.mark.parametrize("with_alpha", [False, True])
def test_a_png_holds_the_same_pixels_at_the_level_it_is_now_written_at(tmp_path, with_alpha):
    rng = np.random.default_rng(1)
    m = _maps(rng)
    m["rgb"] = m["rgb"] * 1.2 - 0.1      # some of it out of range, as a bake can be
    alpha = m["alpha"] if with_alpha else None
    want = _u8(m["rgb"], alpha)
    old = _png(want, 6)      # the level both writers used before
    assert np.array_equal(np.asarray(Image.open(io.BytesIO(old))), want)
    # the plain export's writer
    data, mime = encode_image(m["rgb"], alpha, kind="png")
    assert mime == "image/png" and data == _png(want, export.PNG_LEVEL)
    got = Image.open(io.BytesIO(data))
    assert got.mode == ("RGBA" if with_alpha else "RGB") and np.array_equal(np.asarray(got), want)
    # the Unreal target's writer: the same level, the same pixels, 8 bits a channel
    name = gu._write_png(tmp_path / "m_diff_2k.png", m["rgb"], alpha)
    raw = (tmp_path / name).read_bytes()
    assert raw == _png(want, export.PNG_LEVEL) and raw[24] == 8
    assert np.array_equal(np.asarray(Image.open(tmp_path / name)), want)


def test_every_png_level_decodes_to_the_same_pixels():
    rng = np.random.default_rng(2)
    y, x = np.mgrid[0:96, 0:64]
    for pixels in (_u8(_maps(rng)["rgb"]), _u8(np.dstack([x / 64.0, y / 96.0, (x + y) / 160.0]), np.hypot(x - 32, y - 48) < 30)):
        for level in range(10):
            assert np.array_equal(np.asarray(Image.open(io.BytesIO(_png(pixels, level)))), pixels)
    # the level in use does compress: level 0 only stores
    assert 1 <= export.PNG_LEVEL <= 9 and len(_png(pixels, export.PNG_LEVEL)) < len(_png(pixels, 0))


# -- atlases once per export ----------------------------------------------------------------------
def test_an_atlas_is_baked_once_for_an_export_and_every_age_gets_its_maps(tmp_path):
    rng = np.random.default_rng(3)
    atlas, made = _maps(rng), []
    maps, kept = gu.Maps(tmp_path / "once", "birch"), {}

    def make():
        made.append(1)
        return atlas

    first, files_30 = maps.write_once(kept, "leaf", "birch_age030_leaf", make)
    again, files_60 = maps.write_once(kept, "leaf", "birch_age060_leaf", make)
    assert len(made) == 1 and first is atlas and again is atlas
    assert files_30 == {"diff": "birch_age030_leaf_diff_2k.png", "nor": "birch_age030_leaf_nor_gl_2k.png", "rough": "birch_age030_leaf_rough_2k.png"}
    assert files_60 == {k: v.replace("age030", "age060") for k, v in files_30.items()}
    # as before, when each age baked the atlas again and wrote it itself: the same files, holding the same pixels
    each = gu.Maps(tmp_path / "each", "birch")
    for slot in ("birch_age030_leaf", "birch_age060_leaf"):
        assert each.write(slot, atlas["rgb"], atlas["normal"], atlas["rough"], alpha=atlas["alpha"]) == (files_30 if "030" in slot else files_60)
    assert sorted(p.name for p in maps.folder.iterdir()) == sorted(p.name for p in each.folder.iterdir())
    for p in each.folder.iterdir():
        a, b = Image.open(p), Image.open(maps.folder / p.name)
        assert a.mode == b.mode and np.array_equal(np.asarray(a), np.asarray(b)), p.name
    # asking for the same slot again writes nothing new and doesn't fail
    assert maps.write_once(kept, "leaf", "birch_age030_leaf", make)[1] == files_30 and len(made) == 1


def test_bark_strips_are_encoded_once_and_every_file_holds_the_same_map(tmp_path, monkeypatch):
    rng = np.random.default_rng(4)
    tex, m = _maps(rng), _mesh(rng)
    strips = SimpleNamespace(vertices=m["V"], normals=m["N"], faces=m["F"], uv=m["UV"], colour=np.ones((6, 4)))
    calls = []
    real = game.encode_image
    monkeypatch.setattr(game, "encode_image", lambda *a, **k: calls.append(1) or real(*a, **k))
    from treegen import appearance as ap

    want = _u8(ap.linear_to_srgb(tex["rgb"]), tex["alpha"])
    blobs = []
    for name in ("a", "b"):
        glb = GameGLB(tmp_path / f"{name}.glb", name, {})
        game.add_strips(glb, {}, strips, tex)
        glb.write()
        doc, blob = read_glb(tmp_path / f"{name}.glb")
        view = doc["bufferViews"][doc["images"][0]["bufferView"]]
        assert np.array_equal(np.asarray(Image.open(io.BytesIO(blob[view["byteOffset"]:view["byteOffset"] + view["byteLength"]]))), want)
        blobs.append(blob)
    assert len(calls) == 1 and blobs[0] == blobs[1]


# -- the geometry-only export ---------------------------------------------------------------------
def test_without_textures_the_unreal_files_hold_the_same_buffers_and_name_no_map(tmp_path):
    rng = np.random.default_rng(5)
    tex, m = _maps(rng), _mesh(rng)
    bake = {"albedo": tex["rgb"], "rough": tex["rough"], "ao": tex["alpha"], "normal": tex["normal"], "height": tex["rough"] * 0.01 - 0.004}
    docs, bins, ranges = {}, {}, {}
    for name, textures in (("full", True), ("plain", False)):
        out = tmp_path / name
        maps = gu.Maps(out, "birch", textures)
        split = out / "SourceArt" / "PolyHaven_split" / "birch"
        split.mkdir(parents=True)
        glb = GameGLB(split / "birch_age030.gltf", "birch_age030", {"species": "made up"})
        files = gu._bark_maps(maps, "birch_age030_stem_bark", bake)
        ranges[name] = files["height_range_m"]
        mat = maps.material(glb, "birch_age030_stem_bark", files, gu.REPEAT, gu.CLAMP)
        glb.add_mesh("stem", mat, m["V"], m["N"], m["F"], m["UV"], m["T"], colour=np.ones((6, 4)), colour_8bit=True, extra_uv=[m["UV"], m["UV"], m["UV"]])
        _, leaf_files = maps.write_once({}, "leaf", "birch_age030_leaf", lambda: tex)
        leaf = maps.material(glb, "birch_age030_leaf", leaf_files, gu.CLAMP, gu.CLAMP, alpha_clip=0.5, two_sided=True, extras={"note": 1})
        glb.add_mesh("leaves", leaf, m["V"] + 1.0, m["N"], m["F"], m["UV"], m["T"], colour=np.ones((6, 4)), colour_8bit=True)
        glb.write_gltf()
        assert validate_glb(glb.path)["triangles"] == 4
        docs[name], bins[name] = json.loads(glb.path.read_text(encoding="utf-8")), glb.path.with_suffix(".bin").read_bytes()
    assert bins["full"] == bins["plain"] and ranges["full"] == ranges["plain"]
    assert docs["full"]["meshes"] == docs["plain"]["meshes"] and docs["full"]["accessors"] == docs["plain"]["accessors"]
    assert len(list((tmp_path / "full").rglob("*.png"))) == 6 and len(docs["full"]["images"]) == 6
    assert not list((tmp_path / "plain").rglob("*.png")) and "images" not in docs["plain"] and "textures" not in docs["plain"]
    # the same slots, so the same materials by name; the wind's data is still marked as not a colour
    assert [x["name"] for x in docs["plain"]["materials"]] == [x["name"] for x in docs["full"]["materials"]]
    assert all(x["extras"]["color0"] == "wind" for x in docs["plain"]["materials"]) and docs["plain"]["materials"][1]["doubleSided"] is True


def test_without_textures_the_plain_export_holds_the_same_buffers_and_no_image(tmp_path):
    rng = np.random.default_rng(6)
    tex, stem, branch = _maps(rng), _mesh(rng), _mesh(rng)
    branch.update(tint=rng.random((6, 3)) + 0.5, col=np.array([0, 0, 0, 1, 1, 1]))

    def bake(h, w):
        return {"albedo": rng.random((h, w, 3)).astype(np.float32), "rough": rng.random((h, w)).astype(np.float32), "ao": rng.random((h, w)).astype(np.float32),
                "normal": np.dstack([np.zeros((h, w)), np.zeros((h, w)), np.ones((h, w))]).astype(np.float32), "height": rng.random((h, w)).astype(np.float32) * 0.01}

    atlas = {**bake(16, 32), "layout": [(4, 12, 0.1), (20, 28, 0.3)]}
    strips = SimpleNamespace(vertices=stem["V"] + 2.0, normals=stem["N"], faces=stem["F"], uv=stem["UV"], colour=np.ones((6, 4)))
    ll = {"scale": np.array([0.2, 0.5, 0.1]), "dt_factor": 0.4, "dt_colour": np.array([0.3, 0.6, 0.1])}
    glbs = {}
    for name, textures in (("full", True), ("plain", False)):
        wood = SimpleNamespace(stem_bake=bake(32, 16), atlas=dict(atlas), layout_uv=[(4 / 32, 12 / 32, 0.1), (20 / 32, 28 / 32, 0.3)], encoded={})
        glb = GameGLB(tmp_path / f"{name}.glb", name, {})
        game.add_wood(glb, wood, {"stem": stem, "branch": branch}, 88, 1.0, 1.0, textures)
        game.add_strips(glb, {}, strips, dict(tex), textures)
        mat = game._leaf_material(glb, "leaf_blade", tex, ll, 88, textures)
        glb.add_mesh("leaves", mat, stem["V"] + 3.0, stem["N"], stem["F"], stem["UV"], stem["T"], colour=np.ones((6, 4)))
        glb.write()
        assert validate_glb(glb.path)["images"] == (11 if textures else 0)
        glbs[name] = glb
    full, plain = glbs["full"], glbs["plain"]
    # stem, branches, strips, leaves: positions, normals, tangents, UVs, colours, node ids, radii, indices
    assert _buffers(full) == _buffers(plain) and len(_buffers(plain)) == 7 + 8 + 6 + 6
    assert full.meshes == plain.meshes and [x["name"] for x in full.materials] == [x["name"] for x in plain.materials]
    assert not plain.images and not plain.textures and not plain.extensions
    assert next(x for x in plain.materials if x["name"] == "leaf_blade")["doubleSided"] is True


def test_the_commands_ask_for_textures_unless_told_not_to():
    from cambium.cli import parser

    assert parser().parse_args(["export", "--out", "x"]).textures is True
    assert parser().parse_args(["export", "--out", "x", "--no-textures"]).textures is False
    assert parser().parse_args(["grow", "--export", "glb", "--no-textures"]).textures is False
    import inspect

    from cambium import Tree

    assert inspect.signature(Tree.export).parameters["textures"].default is True


# -- the check that compares whole exports on the server ------------------------------------------
def test_the_export_comparison_passes_png_bytes_and_catches_a_pixel_or_a_vertex(tmp_path):
    import export_timing as et

    rng = np.random.default_rng(7)
    pixels = _u8(_maps(rng)["rgb"], _maps(rng)["alpha"])
    m = _mesh(rng)

    def write(folder, level, lift=0.0, flip=0, textures=True):
        (tmp_path / folder).mkdir()
        img = pixels.copy()
        img[0, 0, 0] ^= flip
        glb = GameGLB(tmp_path / folder / "t.glb", "t", {"run_manifest": {"git_commit": folder}})
        mat = {"name": "m"}
        if textures:
            mat["pbrMetallicRoughness"] = {"baseColorTexture": {"index": glb.add_texture(_png(img, level), "image/png")}}
        glb.add_mesh("a", glb.add_material(mat), m["V"] + lift, m["N"], m["F"], m["UV"], m["T"])
        glb.write()
        (tmp_path / folder / "m_diff_2k.png").write_bytes(_png(img, level))
        (tmp_path / folder / "game_manifest.json").write_text(json.dumps({"run_manifest": folder, "stages": [{"file_mb": level, "triangles": 2 + flip}]}), encoding="utf-8")

    write("old", 6)
    write("new", 1)
    write("pixel", 1, flip=1)
    write("vertex", 1, lift=0.001)
    write("plain", 1, textures=False)
    assert (tmp_path / "old" / "m_diff_2k.png").read_bytes() != (tmp_path / "new" / "m_diff_2k.png").read_bytes()
    # an export is compared by its hashes, so neither has to be kept on disk
    d = {name: et.digest(tmp_path / name) for name in ("old", "new", "pixel", "vertex", "plain")}
    assert et.compare(d["old"], d["old"])["by_kind"] == {".json": {"bytes": 1}, ".png": {"bytes": 1}, ".glb": {"bytes": 1}}
    same = et.compare(d["old"], d["new"])
    assert same["identical"] and same["by_kind"] == {".json": {"content": 1}, ".png": {"content": 1}, ".glb": {"content": 1}}
    pixel = et.compare(d["old"], d["pixel"])
    assert not pixel["identical"] and pixel["different"] == ["game_manifest.json: DIFFERENT json", "m_diff_2k.png: DIFFERENT pixels", "t.glb: DIFFERENT pixels"]
    vertex = et.compare(d["old"], d["vertex"])
    assert not vertex["identical"] and vertex["different"] == ["t.glb: DIFFERENT buffers, json, meshes"]
    # a file with nothing to decode is the same only if its bytes are
    assert et.same({"bytes": "a"}, {"bytes": "b"}) == "DIFFERENT"
    # a geometry-only export against the full one: the same buffers, or it says so
    assert et.compare_geometry(d["new"], d["plain"]) == {"files": 1, "accessors": 5, "different": [], "not_written": [], "identical": True}
    assert et.compare_geometry(d["vertex"], d["plain"])["different"] == ["t.glb"]
    # the table: a row for each age and for the whole export, and an export that failed says so
    size = et.sizes(tmp_path / "old")
    assert size["triangles"] == {"t.glb": 2} and set(size["bytes"]) == {"png", "mesh", "other"}
    runs = [{"what": "glb", "mode": "stand", "textures": True, "code": "abc", "seconds": {"geometry": 1.0, "bake": 2.0, "png": 0.5}, "load": [1.0, 2.0],
             "rows": {"30": {"seconds": {"geometry": 1.0}, **size}}, "all": size},
            {"what": "usd", "mode": "open", "textures": True, "code": "abc", "failed": True}]
    text = et.table({"runs": runs, "compare": {"stand glb": same}})
    assert "| stand | glb | abc | 30 | 1.0 | 1.0 |" in text and "| stand | glb | abc | whole export | 3.5 | 1.0 | 2.0 | 0.5 | 0.5 |" in text
    assert "| open | usd | abc | FAILED |" in text and "- stand glb: IDENTICAL" in text
