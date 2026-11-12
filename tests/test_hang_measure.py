"""The hang measures on made-up trees with known answers, the picture instrument on drawn lines whose directions are
known, and that measuring a growing tree changes no number."""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

import hang_measure as hm  # noqa: E402
import hang_photo as hp  # noqa: E402
import hang_render as hr  # noqa: E402
import hang_run  # noqa: E402


# -- the rule ----------------------------------------------------------------------------------------------------------
def test_hanging_is_defined_once_and_it_is_the_engines_rule():
    from treegen.growth import HANGING_DZ

    assert hm.HANG_DZ == HANGING_DZ == -0.5
    assert math.isclose(-math.sin(math.radians(hm.HANG_BELOW_LEVEL_DEG)), hm.HANG_DZ)
    assert hp.HANG_DEG == hm.HANG_BELOW_LEVEL_DEG and hp.NEAR_DEG == hm.NEAR_VERTICAL_DEG


def _twig(below_level_deg: float):
    """A 2 m stem with one 1 m twig leaving its top at this many degrees below level."""
    a = math.radians(below_level_deg)
    return hm.geometry([[0, 0, 0], [0, 0, 2], [math.cos(a), 0, 2 - math.sin(a)]], [-1, 0, 1], stem=[True, True, False])


def test_thirty_degrees_below_level_is_the_line():
    assert not hm.hangs(_twig(29.0)).any()
    assert hm.hangs(_twig(31.0)).tolist() == [False, False, True]
    assert not hm.hangs(_twig(-60.0)).any()        # rising steeply is not hanging


# -- a made-up tree with known answers ---------------------------------------------------------------------------------
def _one_strand():
    """A 3 m stem.  At 2 m a level branch 2 m long, 12 mm thick; from its end a strand 1.5 m straight down, 4 mm thick,
    2 leaves a node.  From the top a 1 m branch rising at 45 degrees, 8 mm thick, 4 leaves."""
    s = math.sqrt(0.5)
    pos = [[0, 0, 0], [0, 0, 1], [0, 0, 2], [0, 0, 3], [1, 0, 2], [2, 0, 2], [2, 0, 1.5], [2, 0, 1.0], [2, 0, 0.5], [s, 0, 3 + s]]
    parent = [-1, 0, 1, 2, 2, 4, 5, 6, 7, 3]
    radius = [0.05, 0.05, 0.05, 0.05, 0.006, 0.006, 0.002, 0.002, 0.002, 0.004]
    leaves = [0, 0, 0, 0, 0, 0, 2, 2, 2, 4]
    return hm.geometry(pos, parent, radius, leaves, stem=[True] * 4 + [False] * 6)


def test_one_strand_tree_gives_the_answers_worked_by_hand():
    m = hm.measures(_one_strand())
    height = 3.0 + math.sqrt(0.5)
    assert m["height_m"] == pytest.approx(height)
    assert m["branch_length_m"] == pytest.approx(4.5) and m["hanging_length_m"] == pytest.approx(1.5)
    h1 = m["H1_hanging_share_of_branch_length"]
    assert h1["all"] == pytest.approx(1.5 / 4.5)
    assert h1["under_5mm"] == {"length_m": pytest.approx(1.5), "share": pytest.approx(1.0)}
    assert h1["5_10mm"] == {"length_m": pytest.approx(1.0), "share": pytest.approx(0.0)}
    assert h1["10_20mm"] == {"length_m": pytest.approx(2.0), "share": pytest.approx(0.0)}
    assert h1["over_20mm"] == {"length_m": 0.0, "share": None}
    assert m["H2_leaves_on_hanging_share"] == pytest.approx(0.6)
    h3 = m["H3_hanging_run"]
    assert h3["runs"] == 1 and h3["mean_m"] == h3["p90_m"] == h3["longest_m"] == pytest.approx(1.5)
    assert h3["longest_over_height"] == pytest.approx(1.5 / height)
    one_cord = {"sprays": 1, "ends_per_spray": 1.0, "single_strand_share": 1.0, "longest_path_share_of_spray_length": pytest.approx(1.0)}
    assert m["H4_sprays"] == {**one_cord, "starting_under_5mm": one_cord}       # the strand is 4 mm thick where it starts
    # the side view: east sees the level branch level, the strand upright, the rising branch at 45; north sees the
    # level branch end on (no length), and both others upright
    side = m["H5_side_view"]["all_wood"]
    assert side["near_vertical_share"] == pytest.approx(0.5 * (1.5 / 4.5 + 1.0))
    assert side["of_which_down"] == pytest.approx(0.5 * (1.0 + 1.5 / (1.5 + math.sqrt(0.5))))
    # the east view sees all 4.5 m of branch; the north view sees the level branch end on, the strand, and the rising branch's rise
    assert side["seen_m"] == pytest.approx(0.5 * (4.5 + 1.5 + math.sqrt(0.5)))
    # wood under 5 mm left out: only the level branch and the rising one show
    assert hm.side_view(_one_strand(), 0.005)["of_which_down"] == pytest.approx(0.0)
    assert m["hanging_held_at_ground_m"] == 0.0


def test_a_strand_that_forks_is_one_spray_with_two_ends():
    pos = [[0, 0, 0], [0, 0, 2], [1, 0, 2], [1, 0, 1.5], [1, 0, 1.0], [1.2, 0, 1.2]]
    g = hm.geometry(pos, [-1, 0, 1, 2, 3, 3], radius=[0.05, 0.05, 0.004, 0.004, 0.001, 0.001], stem=[True, True, False, False, False, False])
    side = math.hypot(0.2, 0.3)
    m = hm.measures(g)
    # it starts on wood 8 mm thick, so it is not one of the twigs' own sprays
    assert m["H4_sprays"]["starting_under_5mm"] == {"sprays": 0, "ends_per_spray": None, "single_strand_share": None, "longest_path_share_of_spray_length": None}
    assert m["H3_hanging_run"]["runs"] == 2
    assert m["H3_hanging_run"]["longest_m"] == pytest.approx(1.0) and m["H3_hanging_run"]["mean_m"] == pytest.approx(0.5 * (1.0 + 0.5 + side))
    assert m["H3_hanging_run"]["longest_over_height"] == pytest.approx(0.5)
    assert m["H4_sprays"]["sprays"] == 1 and m["H4_sprays"]["ends_per_spray"] == 2.0 and m["H4_sprays"]["single_strand_share"] == 0.0
    assert m["H4_sprays"]["longest_path_share_of_spray_length"] == pytest.approx(1.0 / (1.0 + side))


def test_a_short_hanging_twig_is_hanging_wood_but_not_a_run():
    g = hm.geometry([[0, 0, 0], [0, 0, 2], [1, 0, 2], [1, 0, 1.9]], [-1, 0, 1, 2], leaves=[0, 0, 1, 1], stem=[True, True, False, False])
    m = hm.measures(g)
    assert m["H1_hanging_share_of_branch_length"]["all"] == pytest.approx(0.1 / 1.1)
    assert m["H2_leaves_on_hanging_share"] == pytest.approx(0.5)
    assert m["H3_hanging_run"]["runs"] == 0 and m["H3_hanging_run"]["longest_m"] is None
    assert m["H4_sprays"]["sprays"] == 0 and m["H4_sprays"]["ends_per_spray"] is None


def test_the_stem_and_shed_wood_never_count():
    # a stem whose top points down, a dead hanging twig, and one living hanging twig
    pos = [[0, 0, 0], [0, 0, 2], [0.5, 0, 1.0], [-1, 0, 2], [-1, 0, 1], [1, 0, 2], [1, 0, 1]]
    g = hm.geometry(pos, [-1, 0, 1, 1, 3, 1, 5], stem=[True, True, True, False, False, False, False],
                    alive=[True, True, True, False, False, True, True], leaves=[0, 0, 0, 5, 5, 1, 1])
    assert hm.hangs(g).tolist() == [False, False, False, False, False, False, True]
    m = hm.measures(g)
    assert m["branch_length_m"] == pytest.approx(2.0) and m["hanging_length_m"] == pytest.approx(1.0)
    assert m["H2_leaves_on_hanging_share"] == pytest.approx(0.5)


def test_first_age_at_which_a_tenth_of_the_leaves_hang():
    assert hm.first_age_over({8: 0.02, 9: 0.09, 10: 0.11, 11: 0.30}) == 10
    assert hm.first_age_over({8: 0.02, 9: 0.09}) is None
    # a one-year blip at 6 is the first age it passes, but the habit sets in at 12; keys may be text, as JSON keeps them
    blip = {"5": 0.05, "6": 0.15, "7": 0.04, "10": 0.05, "11": 0.09, "12": 0.12, "13": 0.16}
    assert hm.first_age_over(blip) == 6 and hm.first_age_staying_over(blip) == 12
    assert hm.first_age_staying_over({8: 0.2, 9: 0.05}) is None


def test_outline_of_a_made_up_crown():
    """A 10 m stem with a ring of branch ends 6 m across at 4.5 m and one 3 m across at 7.5 m: widest at 0.45 of height."""
    pos, parent, stem = [[0, 0, 0]], [-1], [True]
    for z in range(1, 11):
        pos.append([0, 0, z]); parent.append(len(pos) - 2); stem.append(True)
    for z, half in ((4.5, 3.0), (7.5, 1.5)):
        for x in np.linspace(-half, half, 21):
            for across in ([x, 0, z], [0, x, z]):
                pos.append(across); parent.append(4 if z < 5 else 7); stem.append(False)
    o = hm.outline(hm.geometry(pos, parent, stem=stem))
    assert o["widest_at"] == 0.45
    assert 0.50 <= o["width_over_height"] <= 0.60


# -- the picture instrument, on pictures drawn by the same code that draws the model ----------------------------------------
PX = 400            # the made-up trees are 10 m tall and drawn 400 px tall: 40 px to the metre
STEM = ([[0.0, 0.0, 0.0]], [[0.0, 0.0, 10.0]], [0.075])     # 6 px wide: thick wood, which the instrument leaves out


def _picture(p0, p1, widths_px):
    """A picture of the stem plus these lines (x, z in metres), each this many pixels wide; and what measure() needs."""
    a = np.asarray(STEM[0] + [[x, 0.0, z] for x, z in p0])
    b = np.asarray(STEM[1] + [[x, 0.0, z] for x, z in p1])
    r = np.asarray(STEM[2] + [w / 80.0 for w in widths_px])
    grey, info = hr.draw(a, b, r, "east", PX)
    return grey.astype(float) / 255.0, info


def test_a_hairline_darkens_its_pixels_by_its_width():
    """Wood a quarter of a pixel wide takes a quarter of the light from the pixels it crosses, as in a photo."""
    grey, info = hr.draw(np.array([[0.0, 0.0, 0.0]]), np.array([[0.0, 0.0, 10.0]]), np.array([0.25 / 80.0]), "east", PX)
    assert info["px_per_m"] == pytest.approx(40.0) and info["base_y"] - info["top_y"] == pytest.approx(PX)
    assert grey.shape[0] == PX + 2 * hr.MARGIN_PX
    dark = 1.0 - grey[int(info["top_y"]) + 20: int(info["base_y"]) - 20].astype(float) / 255.0
    assert dark.sum(axis=1).mean() == pytest.approx(0.25, abs=0.03)


def _rods(angle_from_vertical_deg: float, n: int = 12):
    """n parallel lines 3 m long, 0.5 m apart, at this angle from vertical, left of the stem."""
    a = math.radians(angle_from_vertical_deg)
    dx, dz = 1.5 * math.sin(a), 1.5 * math.cos(a)
    # each line runs along (sin a, cos a); the next one sits half a metre to its side, along (cos a, -sin a)
    p0 = [(-8.0 + 0.5 * k * math.cos(a) - dx, 6.0 - 0.5 * k * math.sin(a) - dz) for k in range(n)]
    p1 = [(-8.0 + 0.5 * k * math.cos(a) + dx, 6.0 - 0.5 * k * math.sin(a) + dz) for k in range(n)]
    return p0, p1


@pytest.mark.parametrize("angle, upright, level", [(0.0, 1.0, 0.0), (90.0, 0.0, 1.0), (45.0, 0.0, 0.0), (10.0, 1.0, 0.0), (30.0, 0.0, 0.0)])
def test_lines_are_read_in_the_direction_they_were_drawn(angle, upright, level):
    p0, p1 = _rods(angle)
    img, info = _picture(p0, p1, [1.2] * len(p0))
    m = hp.measure(img, None, info["base_y"], info["top_y"])
    assert m["near_vertical_share"] == pytest.approx(upright, abs=0.06)
    assert m["near_level_share"] == pytest.approx(level, abs=0.06)
    # 12 lines of 3 m at 40 px to the metre: all of their length is found, and the 6 px stem is not
    assert m["fine_line_px"] == pytest.approx(12 * 120, rel=0.12)


def test_half_upright_and_half_level_reads_as_half():
    u0, u1 = _rods(0.0)
    l0, l1 = _rods(90.0)
    shift = [(x + 14.0, z) for x, z in l0], [(x + 14.0, z) for x, z in l1]      # the level ones to the right of the stem
    img, info = _picture(u0 + shift[0], u1 + shift[1], [1.2] * 24)
    m = hp.measure(img, None, info["base_y"], info["top_y"])
    assert m["near_vertical_share"] == pytest.approx(0.5, abs=0.05) and m["near_level_share"] == pytest.approx(0.5, abs=0.05)


def test_colour_light_and_which_is_darker_change_nothing():
    """White twigs on a dark sky, a dim flat exposure, or a tinted picture read the same as black twigs on white."""
    p0, p1 = _rods(0.0)
    l0, l1 = _rods(60.0)
    img, info = _picture(p0 + [(x + 14.0, z) for x, z in l0], p1 + [(x + 14.0, z) for x, z in l1], [1.2] * 24)
    plain = hp.measure(img, None, info["base_y"], info["top_y"])
    tinted = np.stack([0.9 * img, 0.6 * img, 0.3 * img], axis=2)
    for other in (1.0 - img, 0.4 + 0.3 * img, tinted):
        m = hp.measure(other, None, info["base_y"], info["top_y"])
        assert m["near_vertical_share"] == pytest.approx(plain["near_vertical_share"], abs=0.01)
        assert m["fine_line_px"] == pytest.approx(plain["fine_line_px"], rel=0.02)


def test_a_picture_turned_into_a_photo_still_reads_the_same_way():
    """Softened, flattened, grainy and saved as a JPEG, upright lines still read as upright, and bare sky gives no lines."""
    p0, p1 = _rods(0.0)
    grey, info = hr.draw(np.asarray(STEM[0] + [[x, 0.0, z] for x, z in p0]), np.asarray(STEM[1] + [[x, 0.0, z] for x, z in p1]),
                         np.asarray(STEM[2] + [1.2 / 80.0] * len(p0)), "east", PX)
    photo = hr.like_a_photo(grey, 1)
    assert photo.shape == grey.shape and photo.dtype == np.uint8
    m = hp.measure(photo.astype(float) / 255.0, None, info["base_y"], info["top_y"])
    assert m["near_vertical_share"] > 0.9 and m["fine_line_px"] == pytest.approx(12 * 120, rel=0.15)
    sky = hr.like_a_photo(np.full((200, 200), 255, np.uint8), 2)
    stem_only = np.concatenate([sky, np.zeros((200, 20), np.uint8) + 60], axis=1)       # a dark bar beside it, so the picture has contrast
    assert hp.measure(stem_only.astype(float) / 255.0)["fine_line_px"] < 40


def _fringe():
    """A level limb at 8 m from the stem out to 6 m, with a twig 1.5 m straight down every half metre."""
    xs = [0.75 + 0.5 * k for k in range(10)]
    p0 = [(0.0, 8.0)] + [(x, 8.0) for x in xs]
    p1 = [(6.0, 8.0)] + [(x, 6.5) for x in xs]
    return p0, p1, [2.0] + [1.0] * len(xs)


def test_twig_ends_are_told_as_down_and_as_up_when_the_picture_is_turned_over():
    img, info = _picture(*_fringe())
    m = hp.measure(img, None, info["base_y"], info["top_y"])
    # ten twigs point down; the limb's own end points sideways
    assert m["tips"]["told"] >= 8 and m["tips"]["down_share"] >= 0.8 and (m["tips"]["up_share"] or 0.0) == 0.0
    # each twig is 60 px of a 400 px tree; a few pixels at the limb and at the tip are not traced
    assert m["hanging_run"]["runs"] >= 8
    assert 0.10 <= m["hanging_run"]["mean_over_height"] <= 0.155 and m["hanging_run"]["longest_over_height"] <= 0.16
    # near-vertical twigs reach down to 6.5 m of 10: 5 % of them sit under about 0.66
    assert 0.64 <= m["fringe_low_at"] <= 0.68
    h = img.shape[0]
    over = hp.measure(img[::-1], None, h - info["top_y"], h - info["base_y"])
    assert over["tips"]["told"] >= 8 and over["tips"]["up_share"] >= 0.8 and over["hanging_run"]["runs"] == 0


def test_outline_of_a_drawn_crown():
    """Level limbs 6 m across at 4.5 m and 3 m across at 7.5 m, on a 10 m tree: widest at 0.45, about 0.58 of height wide."""
    img, info = _picture([(-3.0, 4.5), (-1.5, 7.5)], [(3.0, 4.5), (1.5, 7.5)], [1.5, 1.5])
    o = hp.measure(img, None, info["base_y"], info["top_y"])["outline"]
    assert o["widest_at"] == 0.45 and o["width_over_height"] == pytest.approx(0.576, abs=0.03)


def test_without_a_base_and_a_top_only_directions_are_given():
    p0, p1 = _rods(0.0)
    img, _ = _picture(p0, p1, [1.2] * len(p0))
    m = hp.measure(img)
    assert m["near_vertical_share"] > 0.9 and m["outline"] is None and m["hanging_run"] is None and m["fringe_low_at"] is None


def test_a_frame_reads_only_inside_its_boxes():
    m = hp.frame_mask((100, 200), {"include": [[0.0, 0.0, 0.5, 1.0]], "exclude": [[0.0, 0.0, 0.5, 0.25]]})
    assert m.sum() == 100 * 75 and not m[:, 100:].any() and not m[:25].any()


# -- the same part of the tree, on a photo and on the model ----------------------------------------------------------------
# a made-up photo, 300 x 400 px: the tree's foot at (180, 360), its top at (150, 40), so 320 px tall and leaning 30 px left
FRAME = {"picture_px": [300, 400], "base_x": 0.6, "base_y": 0.9, "top_x": 0.5, "top_y": 0.1,
         "include": [[0.1, 0.05, 0.9, 0.5], [0.1, 0.5, 0.55, 0.7]], "exclude": [[0.4, 0.3, 0.5, 0.4]]}


def test_a_photos_boxes_become_tree_heights_from_the_foot_of_its_stem():
    w = hp.window_of(FRAME)
    assert w["tree_height_px"] == pytest.approx(320.0) and w["lean"] == pytest.approx(-30 / 320)
    # the first box is x 30-270, y 20-200: sideways from the foot, then height above it, in tree heights
    assert w["include"][0] == pytest.approx([-150 / 320, 160 / 320, 90 / 320, 340 / 320], abs=1e-6)
    assert w["include"][1] == pytest.approx([-150 / 320, 80 / 320, -15 / 320, 160 / 320], abs=1e-6)
    assert w["exclude"] == [pytest.approx([-60 / 320, 200 / 320, -30 / 320, 240 / 320], abs=1e-6)]
    span = hp.window_span(w)
    assert span["from"] == pytest.approx(0.25) and span["full_width_from"] == pytest.approx(0.5) and span["to"] == 1.0
    # no foot or top in frame, or no size: no window
    assert hp.window_of({**FRAME, "base_y": None}) is None and hp.window_of({**FRAME, "picture_px": None}) is None


def test_a_photo_is_read_through_the_function_that_lays_its_window_on_the_model():
    """One definition of "inside the boxes": frame_roi goes through window_mask and gives frame_mask's own pixels."""
    for frame in (FRAME, {**FRAME, "top_x": 0.85, "exclude": []}, {**FRAME, "picture_px": [301, 399]}):
        w, h = frame["picture_px"]
        assert (hp.frame_roi((h, w), frame) == hp.frame_mask((h, w), frame)).all()
    with pytest.raises(ValueError):
        hp.frame_roi((400, 301), FRAME)                     # not the picture the frame was set on
    loose = {"include": [[0.0, 0.0, 1.0, 0.4]], "base_y": None, "top_y": None}
    assert (hp.frame_roi((100, 50), loose) == hp.frame_mask((100, 50), loose)).all()


def test_a_window_follows_the_stem_line_and_can_be_laid_on_either_side():
    w = {"tree_height_px": 100.0, "lean": 0.0, "include": [[0.1, 0.2, 0.4, 0.8]], "exclude": []}
    m = hp.window_mask((120, 200), w, (100.0, 110.0), (100.0, 10.0))
    ys, xs = np.nonzero(m)
    assert (xs.min(), xs.max(), ys.min(), ys.max()) == (110, 139, 30, 89)
    assert (hp.window_mask((120, 200), w, (100.0, 110.0), (100.0, 10.0), mirror=True) == m[:, ::-1]).all()
    # a tree whose top stands 50 px right of its foot: half way up, the window has moved 25 px with the stem
    lean = hp.window_mask((120, 200), w, (100.0, 110.0), (150.0, 10.0))
    assert np.nonzero(lean[59])[0][[0, -1]].tolist() == [135, 164]


def test_the_reference_photos_windows_are_their_frames_restated():
    """The numbers file holds each photo's window; it must be the frames file's boxes, or the photos were not re-read
    after a frame changed.  Both files are numbers only."""
    frames = json.loads(hp.FRAMES.read_text(encoding="utf-8"))["photos"]
    numbers = json.loads(hp.NUMBERS.read_text(encoding="utf-8"))["photos"]
    assert set(frames) == set(numbers)
    whole = 0
    for name, frame in frames.items():
        assert numbers[name]["window"] == hp.window_of(frame)
        if hp.window_of(frame) is not None:
            whole += 1
            assert numbers[name]["tree_height_px"] == pytest.approx(hp.window_of(frame)["tree_height_px"], abs=0.1)
            assert numbers[name]["picture_px"] == frame["picture_px"]
    assert whole == 6
    # every tree is compared with the photos of its own kind, and each of those has a window
    assert sorted(hang_run.photos_for("open")) == ["hallinden_sweden", "meilen_switzerland_solitary", "oslo_norway"]
    assert sorted(hang_run.photos_for("stand")) == ["brastad_sweden_first_snow", "russia_birch_forest", "tuntorp_sweden"]


def _two_storeys():
    """A 10 m stem.  At 4.5 m a level limb 3.5 m long to each of the four sides, each with twelve twigs 2.5 m straight
    down: the hanging lower storey.  From 6 to 8.5 m, six level limbs 3 m long to each side: the upper storey."""
    pos, parent, radius, stem, on_stem = [[0.0, 0.0, 0.0]], [-1], [0.075], [True], {}
    for z in (4.5, 6.0, 6.5, 7.0, 7.5, 8.0, 8.5, 10.0):
        pos.append([0.0, 0.0, z]); parent.append(len(pos) - 2); radius.append(0.075); stem.append(True)
        on_stem[z] = len(pos) - 1

    def add(to, onto):
        pos.append(list(to)); parent.append(onto); radius.append(0.0125); stem.append(False)       # 1 px wide at 40 px to the metre
        return len(pos) - 1

    for ex, ey in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        at = on_stem[4.5]
        for k in range(1, 15):                                          # the lower limb, in quarter metres
            at = add((0.25 * k * ex, 0.25 * k * ey, 4.5), at)
            if 2 <= k <= 13:
                add((0.25 * k * ex, 0.25 * k * ey, 2.0), at)
        for z in (6.0, 6.5, 7.0, 7.5, 8.0, 8.5):
            add((3.0 * ex, 3.0 * ey, z), on_stem[z])
    return hm.geometry(pos, parent, radius, stem=stem)


def test_the_model_and_a_photo_are_read_through_the_same_window():
    """A picture read as a photo inside its frame, and the same tree read as the model through that frame's window,
    give the same numbers; read whole, the model would read its hanging lower storey too."""
    g = _two_storeys()
    p0, p1, r = hr.segments(g)
    grey, info = hr.draw(p0, p1, r, "east", PX)
    h, w = grey.shape
    img = grey.astype(float) / 255.0
    # the "photo" is read from its top down to 5.2 m of the tree's 10: above the hanging storey
    frame = {"picture_px": [w, h], "base_x": info["base_x"] / w, "base_y": info["base_y"] / h, "top_x": info["top_x"] / w, "top_y": info["top_y"] / h,
             "include": [[0.0, 0.0, 1.0, (info["base_y"] - 0.52 * PX) / h]], "exclude": []}
    photo = hp.measure_framed(img, frame)
    window = hp.window_of(frame)
    assert window["tree_height_px"] == pytest.approx(PX) and hp.window_span(window)["from"] == pytest.approx(0.52, abs=0.005)
    # the model: drawn as tall as the photo's tree, then read through the window
    again, where = hr.draw(p0, p1, r, "east", int(round(window["tree_height_px"])))
    model = hang_run.read_in_window(again, where, window)
    for key in ("near_vertical_share", "near_level_share", "fine_line_px", "near_vertical_share_strict"):
        assert model[key] == pytest.approx(photo[key], abs=1e-9)
    assert model["tips"] == photo["tips"] and model["outline"]["width_over_height"] == pytest.approx(photo["outline"]["width_over_height"], abs=0.01)
    whole = hp.measure(img, None, info["base_y"], info["top_y"])
    assert model["near_vertical_share"] < 0.05 and whole["near_vertical_share"] > 0.3
    # ... and that is the reading the runner reports against a photo: four of them, none read whole
    out = hang_run.matched(p0, p1, r, g, {"window": window, "camera": {"blur_sigma_px": 0.8, "grain_share_of_contrast": 0.004, "jpeg_quality": 87}})
    assert out["tree_px"] == PX and [(x["view"], x["mirror"]) for x in out["window"]] == [("east", False), ("east", True), ("north", False), ("north", True)]
    assert out["window"][0]["near_vertical_share"] == pytest.approx(model["near_vertical_share"], abs=1e-9)
    assert all(x["near_vertical_share"] < 0.05 for x in out["window"] + out["as_that_photo"] + out["from_the_ground"]["1x"] + out["from_the_ground"]["2x"])
    assert len(out["as_that_photo"]) == len(out["from_the_ground"]["1x"]) == len(out["from_the_ground"]["2x"]) == 4
    assert all(x["near_vertical_share"] > 0.3 for x in out["whole"]) and len(out["whole"]) == 2
    # the geometry's twin through the same window sees level limbs only: 6 limbs of 3 m to each side, in either view
    assert out["twin"]["near_vertical_share"] == pytest.approx(0.0) and out["twin"]["seen_m"] == pytest.approx(36.0)
    assert hm.side_view(g)["near_vertical_share"] > 0.3


def test_a_ground_camera_sees_the_tree_as_tall_and_keeps_upright_twigs_upright():
    """Seen from one tree height away, the tree is still drawn base to top over the height asked for, and twigs that hang
    straight down still read as near vertical."""
    g = _two_storeys()
    p0, p1, r = hr.segments(g)
    grey, info = hr.draw(p0, p1, r, "east", PX, camera=1.0)
    assert info["base_y"] - info["top_y"] == pytest.approx(PX) and grey.shape[0] >= PX + 2 * hr.MARGIN_PX
    level, _ = hr.draw(p0, p1, r, "east", PX)
    near = hp.measure(grey.astype(float) / 255.0, None, info["base_y"], info["top_y"], full=False)["near_vertical_share"]
    far = hp.measure(level.astype(float) / 255.0, full=False)["near_vertical_share"]
    assert near == pytest.approx(far, abs=0.15) and near > 0.25


def test_how_soft_and_grainy_a_picture_is_can_be_read_from_it():
    """A 40 px dark bar on a light sky.  As drawn, its edges read as soft as this drawing is; blurred by 1.5 px, about
    1.5 px; and grain put in is grain read back."""
    p0 = np.array([[0.0, 0.0, 0.0], [-2.0, 0.0, 1.0], [2.0, 0.0, 1.0]])
    p1 = np.array([[0.0, 0.0, 10.0], [-2.0, 0.0, 2.0], [2.0, 0.0, 2.0]])
    grey, _ = hr.draw(p0, p1, np.array([0.5, 0.0125, 0.0125]), "east", PX)
    drawn = hp.sharpness(grey.astype(float) / 255.0)
    assert drawn["edges"] > 100 and drawn["blur_sigma_px"] == pytest.approx(hr.RENDER_SIGMA_PX, abs=0.15)
    soft = hp.sharpness(hr.like_a_photo(grey, 3, blur_px=1.5, grain=0.0, quality=95).astype(float) / 255.0)
    assert soft["blur_sigma_px"] == pytest.approx(math.hypot(1.5, hr.RENDER_SIGMA_PX), abs=0.25)
    grainy = hp.sharpness(hr.like_a_photo(grey, 3, blur_px=0.0, grain=0.01, quality=100).astype(float) / 255.0)
    assert 0.009 <= grainy["grain_share_of_contrast"] <= 0.017          # 0.01 of full range on a picture at 0.65 of it, less what the JPEG smooths
    assert hp.sharpness(grey.astype(float) / 255.0)["grain_share_of_contrast"] < 0.001
    # a photo's measured figures make the copy: softer by what the photo shows beyond the drawing's own softness
    copy = hp.sharpness(hr.as_photo(grey, {"blur_sigma_px": 1.0, "grain_share_of_contrast": 0.0, "jpeg_quality": 95}).astype(float) / 255.0)
    assert copy["blur_sigma_px"] == pytest.approx(1.0, abs=0.2)


def test_the_near_vertical_share_is_never_ranked_alone():
    """H5 can't tell hanging wood from upright wood, so a change counts as closer to the photos only if less wood hangs
    and no more of it stands upright."""
    photos = (0.23, 0.32)
    now = {"near_vertical": 0.70, "twin": 0.75, "of_which_down": 0.95, "seen_m": 1000.0, "hanging_share": 0.88}
    # twigs that spread, on shorter cords: less upright wood, most of what is left still pointing down
    spread = {"near_vertical": 0.45, "twin": 0.40, "of_which_down": 0.90, "seen_m": 700.0, "hanging_share": 0.60}
    verdict = hm.closer_on_h5(now, spread, photos)
    # upright wood pointing up is a larger share (0.040 against 0.0375) of less wood (28 m against 37.5 m): not risen
    assert verdict["closer"] and verdict["figures"]["upright_pointing_up_m"] == [pytest.approx(37.5), pytest.approx(28.0)]
    # hanging twigs turned upright: the picture reads lower and less wood hangs, but upright wood has risen
    upright = {"near_vertical": 0.55, "twin": 0.60, "of_which_down": 0.30, "seen_m": 1000.0, "hanging_share": 0.30}
    verdict = hm.closer_on_h5(now, upright, photos)
    assert verdict["nearer_the_photos"] and verdict["less_wood_hangs"] and verdict["less_upright_wood_points_down"]
    assert not verdict["no_more_upright_wood_points_up"] and not verdict["closer"]
    # the picture reads lower while as much wood hangs: not closer
    assert not hm.closer_on_h5(now, {**now, "near_vertical": 0.60}, photos)["closer"]
    # already inside the photos' range, as the model's 3 m pole at age 10 is: nothing can be nearer
    assert not hm.closer_on_h5({**now, "near_vertical": 0.31}, {**spread, "near_vertical": 0.25}, photos)["nearer_the_photos"]


# -- on a growing tree ---------------------------------------------------------------------------------------------------
def _model(seed: int = 4):
    from treegen.environment import make_environment, make_soil
    from treegen.growth import GrowthModel
    from treegen.params import load_environment, load_species

    sp, _ = load_species("betula_pendula")
    env, _ = load_environment("sweden_open_field")
    return GrowthModel(sp, make_environment(env), seed, stand=True, soil=make_soil(env), lean=True)


def test_measuring_a_growing_tree_changes_nothing_and_agrees_with_the_engine():
    plain, read = _model(), _model()
    for year in range(1, 13):
        plain.step()
        read.step()
        g = hm.from_model(read)
        hm.leaf_share(g)
        if year >= 10:
            # against the reference photos in the last year only: it is the slow part
            photos = hang_run.photos_for("stand") if year == 12 else {}
            row = hang_run.at_age(read, g, None, year, photos)
            assert sorted(row["matched"]) == sorted(photos)
            for name, m in row["matched"].items():
                # drawn as tall as the photo's tree, and read four times through its window, never whole
                assert m["tree_px"] == int(round(photos[name]["window"]["tree_height_px"])) and len(m["window"]) == 4
            assert row["check"]["rules_differ_on"] == 0
            assert row["geometry"]["height_m"] == pytest.approx(read.stats[-1]["height_m"], abs=1e-3)
            longest = row["geometry"]["H3_hanging_run"]["longest_m"] or 0.0
            assert longest >= row["check"]["engine_longest_run_m"] - 1e-9 or row["check"]["engine_longest_run_m"] < hm.MIN_RUN_M
    assert json.dumps(plain.stats, sort_keys=True) == json.dumps(read.stats, sort_keys=True)


def test_one_tree_is_grown_measured_and_written(tmp_path):
    assert hang_run.one(1, [], tmp_path, 3, True, (2, 3), True) == 0
    got = json.loads((tmp_path / "hang.json").read_text(encoding="utf-8"))
    assert sorted(got["ages"]) == ["2", "3"] and got["mode"] == "stand" and len(got["leaves_on_hanging_share_by_age"]) == 3
    assert (tmp_path / "leafless_east_age03.png").exists() and (tmp_path / "manifest.json").exists()
