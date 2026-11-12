"""Marks the long tests ``slow``, without touching the tests themselves.

    pytest                  # everything (about 10 minutes on one core)
    pytest -m "not slow"    # the quick part (about 2 minutes): every pull request runs this
    pytest -m slow          # the long part: run on main and every night (.github/workflows/tests.yml)

A test is slow if it took 3 s or more on the project's reference machine (one core, at 03db9e1), or
if it reads a fixture that takes that long to build.  Timings: pytest --durations=0.
"""
from __future__ import annotations

import pytest

SLOW_FIXTURES = {"unreal_export", "small_exports"}
SLOW = {
    "tests/test_cambium.py::test_a_small_forest",
    "tests/test_cambium.py::test_glb_export_every_level_and_stage",
    "tests/test_checkpoint.py::test_a_tree_saved_and_resumed_is_the_same_tree",
    "tests/test_crown_frame.py::test_a_full_crown_stops_making_leaves_and_its_surplus_is_paid_for",
    "tests/test_crown_frame.py::test_earned_a_full_crown_sheds_its_oldest_short_shoots",
    "tests/test_crown_frame.py::test_earned_a_limb_behind_its_neighbours_has_less_supply",
    "tests/test_crown_frame.py::test_earned_browsing_only_on_a_lone_tree_and_only_within_reach",
    "tests/test_crown_frame.py::test_earned_limb_sag_makes_a_limb_low_at_the_stem_and_rising_at_its_end",
    "tests/test_crown_frame.py::test_earned_limbs_fork_by_leaf_area_and_the_forks_are_limbs",
    "tests/test_crown_frame.py::test_earned_no_limb_goes_past_the_published_crown",
    "tests/test_crown_frame.py::test_earned_no_limb_tip_near_the_leader_and_new_limbs_still_start",
    "tests/test_crown_frame.py::test_earned_on_a_tree_that_forks_one_limb_goes_up_as_a_second_top",
    "tests/test_crown_frame.py::test_earned_only_a_shoots_end_bud_starts_a_long_shoot",
    "tests/test_crown_frame.py::test_earned_surplus_goes_on_the_stem_only_with_no_neighbours",
    "tests/test_crown_frame.py::test_earned_surplus_stops_at_the_most_stem_for_the_height",
    "tests/test_crown_frame.py::test_fewer_limbs_than_without_the_frame",
    "tests/test_crown_frame.py::test_open_grown_share_leaves_a_stand_tree_bit_identical",
    "tests/test_crown_frame.py::test_open_lai_max_leaves_a_stand_tree_bit_identical",
    "tests/test_crown_frame.py::test_steep_limb_does_not_climb_the_stem",
    "tests/test_crown_frame.py::test_thick_limbs_sapwood_turns_over_more_slowly",
    "tests/test_defaults.py::test_a_default_stand_tree_is_a_sane_birch_at_50_and_60",
    "tests/test_defaults.py::test_crown_fix_c_is_the_default_and_young_limbs_reach_further_with_it",
    "tests/test_defaults.py::test_plot_spacing_counts_every_tree_by_default_and_only_the_canopy_with_the_switch",
    "tests/test_forest.py::test_a_plot_year_as_a_plain_tree_list",
    "tests/test_forest.py::test_lean_plot_grows_the_same_trees",
    "tests/test_game_export.py::test_a_limbs_bark_goes_white_a_little_at_a_time_and_only_adds",
    "tests/test_game_export.py::test_a_trees_black_only_rises_as_it_thickens",
    "tests/test_game_export.py::test_every_file_loads_and_every_level_keeps_its_budget",
    "tests/test_game_export.py::test_thinning_saves_triangles_and_leaves_the_stem_alone",
    "tests/test_height_limit.py::test_a_lost_leader_is_replaced_and_gets_back_to_the_curve",
    "tests/test_leaves_each_year.py::test_cambiums_export_takes_the_option_too",
    "tests/test_height_limit.py::test_a_side_shoot_never_ends_above_the_leader",
    "tests/test_roots_paid.py::test_anchorage_and_the_root_plate_still_read_the_roots",
    "tests/test_roots_paid.py::test_measuring_the_roots_changes_nothing",
    "tests/test_roots_paid.py::test_the_taproot_stops_at_its_length_whichever_way_stones_turn_it",
    "tests/test_species_data.py::test_a_species_that_isnt_birch_grows_ten_years_with_no_birch_file_in_reach",
    "tests/test_speed.py::test_a_dropped_tree_holds_only_what_it_needs",
    "tests/test_speed.py::test_a_tree_is_the_same_with_the_settings_on",
    "tests/test_speed.py::test_dropping_dead_nodes_keeps_every_yearly_stat",
    "tests/test_speed.py::test_dropping_dead_nodes_keeps_the_count_of_what_fell_and_the_new_shoots",
    "tests/test_speed.py::test_scars_on_living_wood_stay_after_a_drop",
    "tests/test_treegen.py::test_pipe_model_every_year",
    "tests/test_treegen.py::test_root_pipes_continue_the_stem",
    "tests/test_treegen.py::test_same_seed_gives_identical_output",
}


def pytest_configure(config):
    config.addinivalue_line("markers", "slow: takes 3 s or more; left out of the quick run (pytest -m 'not slow')")


def pytest_collection_modifyitems(config, items):
    for item in items:
        if item.nodeid.split("[")[0] in SLOW or SLOW_FIXTURES & set(getattr(item, "fixturenames", ())):
            item.add_marker(pytest.mark.slow)
