Model: Fable 5.2 (claude-fable-5-2)

# Code audit: is the code professional? 2026-11-11

Read-only review of master at `b84ab90`, with the public copy (`d0de191`) beside it.

How it was done:
- I read the engine (`treegen/`), the public layer (`cambium/`), `cli.py`, the species file, the tools folder, the build files and the CI files.
- The counts come from small scripts that parse the files (Python's `ast`, YAML, `git ls-files`).
- The only code run was the `cambium` command's error paths, which stop before a tree is built. No growth, no pytest, no renders.
- No table here holds model results, because nothing was grown. So there are no figures at 50 or 60 to give.

## Verdict in plain words

1. It works, it is tested, and a run repeats to the bit. That part is professional.
2. It is not yet code a second maintainer could change safely. The model is one class of 3,113 lines, and its main method is 569 lines long.
3. Settings have piled up. About 80 are switches. Some say "off" while their code runs. One says "on" and does nothing.
4. The hot rules exist twice, in numpy and compiled. A science change must be made in both.
5. The safety net for fixing any of this, the golden hashes, is not in the repository or in CI.
6. No formatter, linter or type checker is set up. Line endings are mixed.
7. The pendulous look and the slow runs are not code-quality faults. But both are harder to fix safely while points 2 to 5 stand.

**Score: 5 / 10.** Repeatable runs, tests and packaging checks earn it. Structure, switches and tooling hold it down.

## The code in numbers

| What | Count |
|---|---|
| Tracked Python | 39,850 lines: engine 15,682, public layer 841, `cli.py` 459, tests 5,914, tools about 17,000 |
| `treegen/growth.py` | 3,189 lines; `GrowthModel` is 3,113 of them, with 80 methods |
| Longest functions | `step` 569, `build_mesh` 506, `_growth_factor` 371, `_grow_shoots` 233, `export_stage` 230; 13 over 100 lines |
| Functions without a docstring | 281 of 707 |
| Species file | 812 values (500 model, 312 look); 2,391 lines, 1,445 of them comments; longest line 877 characters |
| On/off switches in it | 62: 40 on, 22 off. Plus 15 values where null means off, and 4 mode choosers |
| `getattr(x, name, default)` in the engine | 330; 172 in `growth.py` |
| Settings with a number as fallback in code | 44; 20 of them real values, not 0 or 1 |
| Schema coverage | 374 of 500 model values; never run when a file loads |
| `tools/` | 143 tracked files: 104 at the top, 34 under `node/`, 5 under `unreal/` |
| Line endings | 63 files CRLF, 262 LF; no `.gitattributes` |
| Lines over 120 characters | 1,822; 168 over 200 |

## Findings, most serious first

### G1. The golden hashes are not in the repository or in CI. High. CONFIRMED
- Where: `tools/golden.py:42`, `.gitignore:14`, `.github/workflows/tests.yml`.
- What: the four golden runs write their hashes under `out/`, which git ignores. No tracked file that a test or CI reads holds a result hash. CI runs pytest and a packaging check. The 2026-11-09 review asked for this; the default-tree tests were added, the golden check was not.
- Why: every step in the plan below rests on "same hashes". Today that can be shown on one machine, by hand. A contributor can't show it at all.
- Fix: a CI job that runs the golden cases at the base commit and at the change, on the same runner, then `tools/golden.py compare`. Comparing on one machine avoids the CPU difference. Also commit the reference machine's hash file. Effort: S.

### SW1. Some switches do not say what runs. High. CONFIRMED
- `pipe_model.crown_rise_heartwood: false`, but its code runs at `stem_theory.stage` 1 and up (`growth.py:1743`). The default stage is 2.
- `pipe_model.wind_load.enabled: false`, but stage 2 turns the wind on, with another wind speed (`growth.py:1670`, `:1684-1686`).
- `resource.young_limbs_import: true`, but it is read only inside a block that runs when `branch_export_fraction` is set, and that is null (`growth.py:1064-1079`).
- `pipe_model.huber_path_exponent` (0.283) and `huber_radius_exponent` (0.312) carry long derivations in the species file. Both are set to 0 at stage 1 and up (`growth.py:1725-1726`).
- `bud_fate.idle_buds_no_sink` cannot act in the default growth mode (`growth.py:1176`).
- `bud_fate.axillary_buds_below_one_metamer`: false is the active setting, and the code's own fallback is the opposite (`growth.py:2621`).
- Why: each run's manifest lists `options_on`. That list is how a reader learns which model ran. In these places it misleads.
- Fix: delete the dead ones. Give stage 2 its parts as plain values of its own. Effort: S.

### SW2. Fallback values live in the code, and a misspelt setting is ignored without a word. High. CONFIRMED
- Where: the 330 `getattr` reads; `treegen/params.py:3`; `treegen/species_schema.py:593`; `treegen/checkpoint.py:39-49`.
- What:
  - `params.py` says "Nothing species-specific is defined in code". Yet wood density 530, carbon fraction 0.48, seed mass 0.21 mg and wood shade 0.40 are fallbacks in `growth.py:738` and `:910-914`. `plot.py:348-349` repeats the last one.
  - The fallbacks describe an older model than birch runs: growth mode "pipe" against "lignum" (`growth.py:1146`), stage 0 against 2, layout "lattice" against "random", speed off against on.
  - A schema with units and ranges exists, which is good. Nothing calls it when a file loads or when `--set` changes a value. All 40 `crown_frame` values, all 15 `height_driver` and all 24 `mortality` values are missing from it.
- Why: a second species, or an edited file, with one missing or misspelt key grows a different model and reports nothing.
- Fix: one loader that holds every default once, refuses unknown and missing keys, and checks ranges. `--set` goes through it. Bring the schema up to date. Effort: M.

### S1. The model is one class. High. CONFIRMED
- Where: `treegen/growth.py:77`, `:720` (`step`, no docstring), `:1702` (`_growth_factor`, four nested functions); `treegen/plot.py:399-405`.
- What: light, shedding, water, carbon, allocation, the crown frame, the height driver, radii and the yearly measures share one object. About 60 private attributes hold its state. 27 are read with `getattr(self, "_x", default)` because they are made on the way or set from outside. A plot steers each tree by setting four private attributes before `step()` and clearing them after.
- Smaller signs of the same: the stem mask is rebuilt 18 times, the "is this tree alone" test is written out 6 times, and two near-identical "surplus to the stem" blocks sit at `growth.py:1985-1996` and `:1997-2009`.
- Why: no rule can be read or tested alone. Each experiment adds a branch to the same two functions.
- Fix: split by job, as pure moves, in the order given below. Declare all state in `__init__`. A plot hands over one context object. Effort: L.

### D1. The hot rules exist twice. High. CONFIRMED
- Where: `growth.py:1869-1904` against `fast.py:179-277` (the carbon solve); `mechanics.py:127-144` against `fast.bend_steps`; `growth.py:1941-1950` against `fast.quick_bisect`; `light.py:169`, `:322`; `structure.py:149`; `roots.py:240`.
- What: `fast.py` holds 11 compiled functions behind 8 `speed` switches. Six are on by default, so the numpy forms no longer run in a default tree. `fast.py:1` still says "all off by default".
- Why: a science change must be made in both copies. The branch-wood track's ring rule is at `growth.py:1881` and at `fast.py:220-222`. `tests/test_speed.py` catches drift, but only on the cases it grows.
- Fix: make the compiled path the only path for the six lossless settings. Keep the numpy forms under `tests/` as the check. Remove the six switches. The default path does not change, so the hashes do not. Effort: M.

### F1. The public layer runs scripts, and library code lives in scripts. Medium. CONFIRMED
- Where: `cambium/_engine.py:44-68`; `pyproject.toml:72-74`; `treegen/params.py:17-18`; `cambium/_forest.py:21-29` and `:113-147` against `tools/forest.py:42-56`; `cambium/_tree.py:207-216` against `tools/game_export.py:262-275`.
- What: growing a tree, the USD export, the game export and the tree list live in `cli.py` and two files under `tools/`. The wheel copies those scripts in. `cambium` runs them under private names, saving and restoring `sys.path` and `sys.modules`. `treegen` alone cannot find its species files once installed. The forest loop and the game manifest are each written twice. 75 tools insert into `sys.path`. 36 files build `GrowthModel` by hand.
- Why: it is fragile, and the two copies of the forest run can drift apart.
- Fix: move those functions into the package. Scripts become thin. Data is found with `importlib.resources`. Delete `_engine.load`. Effort: M.

### A1. The command checks some inputs well and others not at all. Medium. CONFIRMED by running the error paths

| Input | What happens |
|---|---|
| Unknown species or environment | Exit 2, one clear line that lists the known names. Good |
| Missing species file; `--years 0` | Exit 2, one clear line. Good |
| `--set resource.nosuch=1` | Exit 2, "no such parameter". Good |
| `--set nosuch.alpha=1` (grow and forest) | A Python traceback |
| `--set resource.alpha` | Exit 2, "not enough values to unpack (expected 2, got 1)" |
| `--set resource.alpha=abc` | Exit 2, "Expecting value: line 1 column 1 (char 0)" |
| `cambium export` without `--out` | Exit 1, where every other user error is 2 |
| `--ages x` | Exit 2, Python's own `int()` message |

- Also: a set value's type and range are not checked. `--lod` and `--seasons` are checked only after the tree has grown (`cambium/cli.py:107-111`; `cambium/_tree.py:184-186`, `:202`), so a typing slip costs a whole run. The output folder is first written after growth too. Plot area and stem count are unchecked (SUSPECTED).
- Fix: check every argument and the output folder before growing. One error type, exit 2, plain messages. Effort: S.

### T1. No formatter, linter or type checker; mixed line endings. Medium. CONFIRMED
- Where: `pyproject.toml` (no tool section for any of them); no `.gitattributes`; `.github/workflows/tests.yml` (no lint job).
- What: 190 `noqa` marks show a linter was run by hand at some time. `growth.py`, `cli.py` and the species file are CRLF; most other files are LF. Parameters are `SimpleNamespace`, so no checker can catch a misspelt name.
- Fix: `ruff format` and `ruff check` settings in `pyproject.toml`, `* text=auto eol=lf`, one commit that only reformats, a lint job in CI, then a type checker on `cambium/` first. Changing the species file's line endings changes its SHA-256 in run manifests, but not the golden hashes, which leave the manifest out (`tools/golden.py:47`). Effort: S.

### TL1. The tools folder is bigger than the engine and mostly one-off. Medium. CONFIRMED
- What: of the 104 top-level files, 2 ship in the wheel, 27 are imported by tests, 9 are in the docs, 20 are used by other tools, and 46 are used by nothing. Most of the 46 are named after a past step (`m1_`, `m2_`, `m3_`, `speed_`, `proof_`). `tools/node/runs/` holds 22 scripts that each launched one past batch. In the private copy some of them start by changing to a path inside the owner's home folder.
- Why: a newcomer cannot tell the 30 tools that matter from the rest. The golden runs themselves go through `tools/plot.py`.
- Fix: keep what tests, docs or the package use. Move the rest to an `archive/` folder left out of the public copy, or delete them; git keeps them. Effort: S.

### R1. Comments are lab notes, and private names sit in the source. Medium. CONFIRMED
- What: the engine and the species file refer to "phase 37", "option J", "test A", about 30 run labels and 9 commit hashes. A reader needs the project's history to follow them. The species file has 49 lines over 200 characters; one is 877. Much of that text is what was tried before.
- The owner's first name appears 457 times in 73 tracked files of the private copy, 8 of them in the engine and species file. The public copy has none, but only because a list of text rules rewrites it. 43 code files and the species file differ between the two copies, so the species file's SHA-256 does too.
- Fix: a comment says what the value is, its unit, its source and its label. History goes to `DECISIONS.md`. Clean the names at the source, so publishing becomes a file filter. Effort: M.

### RNG1. Two random streams are the same stream. Medium. CONFIRMED (the size of the effect is not measured)
- Where: `treegen/growth.py:119` and `treegen/roots.py:146`.
- What: leader damage and root growth are both seeded with the tree's seed and the bare number 104729. They draw the same sequence. The other streams have their own numbers, written as bare numbers in nine more places (`growth.py`, `plot.py`, `regeneration.py`); only `damage.py` names its two.
- Why: two processes meant to be independent are tied. Fixing it changes results, so it belongs with the next approved model change, not with the tidy-up.
- Fix: one table of named stream tags, with a test that none repeats. Effort: S, plus a new golden recording.

### P1. The publish tool is not under version control. Medium. CONFIRMED
- What: the folder that builds the public copy is not a git repository and has no tests. It holds the only copies of the public README, CONTRIBUTING, CHANGELOG and NOTICE, and the rules that strip private details.
- Fix: put it in its own private repository, with a test that the built copy holds none of the private strings. Effort: S.

### Smaller points
- **N1. Low. CONFIRMED.** Four names: `Origin` (the old name, still in the `ORIGIN_*` variables, 46 uses in 32 files), `treegen`, `cambium`, `pycambium`. Three versions: `treegen/__init__.py:6` says 0.1.0, `cli.py:411` says "treegen 0.4", `cambium/__init__.py:24` says 0.9.0. Fix: one version read from one place; `CAMBIUM_*` variables with the old ones still accepted. S.
- **U1. Low. CONFIRMED.** `treegen/__init__.py:1` says "engine-agnostic", but `treegen/game_unreal.py` (1,369 lines) writes one game's folder and material names. About 6,300 lines of the package are export and look, 8,250 are the model. Fix: sub-packages `model`, `export`, `exporters`. M.
- **L1. Low. CONFIRMED.** Importing the package sets the maths libraries of the whole process to one thread (`treegen/threads.py:43-53`). It is documented, but a host program pays for it. Progress goes through `print`; there is no logging. The engine raises 14 errors in 15,682 lines, none in `growth.py`, `roots.py`, `plot.py` or `light.py`.
- **H1. Low. CONFIRMED.** 49 branches, 17 of them left by agents. `requirements.lock` pins a package no tracked code imports (`pypdf`); `requirements.txt` lacks `pillow`, which `pyproject.toml` lists. `growth.py` and `damage.py` import each other.

## Switches: what to do with each (SW3. Medium. CONFIRMED)

The rule in CONTRIBUTING is "new behaviour is an option, off by default". It has no second half, so nothing is ever removed.

| Group | Settings | Do |
|---|---|---|
| Dead, or their value is ignored | `young_limbs_import`, `idle_buds_no_sink`, `crown_rise_heartwood`, `wind_load.enabled`, the two Huber exponents, `germination.cotyledon_area_cm2` | Remove |
| Old modes nothing default uses | `pipe_model.growth` pipe, rings and stem_rings; `stem_theory.stage` 0 and 1; `stand.layout` lattice | Remove once their tests move to the default |
| Off experiments no test names | `branch_export_fraction` (about 45 lines), `borchert_honda_published`, `charge_fresh_laterals`, `sapwood_for_next_season`, `sapwood_replacement_is_upkeep`, `limb_share_by_leaf`, `limb_light_line`, `limb_relative_light`, `limb_carbon_margin`, `lateral_cap_ratio`, `store_fraction`, `speed.light_rows` | Remove; the species file itself calls most of them a test or a diagnosis that failed |
| Bug fixes kept as switches | `roots.paid.tip_weight_apart`, `roots.paid.widen_from_node_start`, `anchorage.moments_unrounded`, `stats.limbs_on_leader` | Become the only path |
| Lossless speed | `compiled_carbon`, `compiled_mechanics`, `light_layers`, `keep_soil_grids`, `quick_solve`, `quick_levels` | Become the only path (D1) |
| Real options | `mortality`, `regeneration.spread`, `plot.natural_start`, `plot.stand_measures`, `germination`, `soil_water_balance`, `field_layer_competition`, `damage.*`, the lossy speed settings, the two logging switches | Keep, each with a test |

None of the four design tracks uses a setting in the first three rows (searched). Removing a path that is off cannot change a default run.

## What is genuinely good

- **Repeatable runs.** One maths thread, seeded streams, no fast-math, a locked set of versions, and a run manifest with file hashes.
- **Tests and CI.** 29 test files with names that say what they prove. CI runs quick tests on pull requests and all tests nightly. It builds the wheel on three Python versions and runs the command from outside the checkout. The public repo's last runs are green.
- **Bit-identity checks.** Compiled against numpy, lean against full, resumed against straight. Few projects have these.
- **Clean dependencies.** Apart from `growth` and `damage`, the engine's imports form no cycle. A search for unused functions found two.
- **The public layer is small and well documented.** `grow`, `forest`, `Tree`, `Forest` and `Stats` have clear docstrings and good messages for the common mistakes.
- **The schema.** Units, ranges and cross-checks for 374 values. It only needs to be finished and switched on.
- **Honest notes.** `SECURITY.md` warns about pickles. The species file says where a value is tuned or unverified.

## What to restructure first, with no result changed

Each step is its own set of small changes. The golden compare must pass after every one.

1. **The safety net (G1).** Golden compare in CI; the reference hashes committed.
2. **Tooling (T1).** `.gitattributes`, formatter, linter, one reformat-only commit, lint in CI.
3. **Parameters (SW2).** One loader with every default, strict keys, ranges. Same values in, same bits out.
4. **Remove dead and failed switches; fold in the bug fixes (SW1, SW3).** One switch per change.
5. **One copy of the hot rules (D1).** Compiled only; numpy forms kept in tests.
6. **Library code out of scripts (F1).** Then the public layer imports it the plain way.
7. **Split `GrowthModel` (S1).** Pure moves, in this order: the yearly measures; leader damage; the stand cell; the crown frame; the height driver; the carbon solve; last, the phases of `step`. Keep every sum in its present order.
8. **Tools, names, versions (TL1, N1).** Archive the one-off tools. One version. `CAMBIUM_*` variables.
9. **Clean the source of private names (R1, P1).** Then publishing only filters files.

Steps 1 to 4 are days. Steps 5 and 6 are about a week each. Step 7 is weeks.

**What should wait:**
- The shared random stream (RNG1). It changes results.
- Any rewrite that reorders a sum or vectorises a loop. It changes the last bit.
- Renaming `treegen`. Saved states name the module, so old checkpoints would stop loading.
- Moving the species file's history out of its comments. One label reader parses those comments (`species_schema.py:634`). Finish `labels.yaml` first.
- A C++ port. Port one path, after step 5, not two.

## On the four design tracks

I don't dispute their science; that is not this area. One point on how they land. Each plans a new switch, off by default, inside `step` or `_growth_factor`. The branch-wood track's arm A would need its change in both copies of the carbon solve. Two requests:
- Give every new switch an end date: adopted and the old path deleted, or removed, within one release.
- If they can, land them after steps 1 to 5. If not, at least after step 1, with a row for each new switch in `tests/test_speed.py`.

## Not checked

- The tests' content, the science, speed and the renders: other areas.
- Whether `pycambium` is free on PyPI.
- How the six fallbacks that differ from birch would change a tree. That needs growth runs.
