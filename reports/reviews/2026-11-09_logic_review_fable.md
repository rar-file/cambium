Model: claude-fable-5-2 (the only model name or ID my system prompt gives; it gives no separate display name)

# Cambium logic review, 2026-11-09

Independent, read-only review at commit `38ce58e` (branch `worktree-agent-a45137b46e1cc8267`).

How it was done:
- I read the model code, species file, targets, scorecard, decisions and the final report myself.
- Two helper agents read the tests and the export, replay and packaging code. Their findings are marked "delegated read". I spot-checked a few and dropped one that was wrong.
- Nothing was run except two small calculations (the height curve and the light sum). No model growth, no pytest.
- No saved run outputs are in the repository (`out/` is ignored), so I could not recompute the reports' result numbers. Where a finding depends on them it is marked SUSPECTED.

## Verdict in plain words

1. The project is unusually honest: its own report says height is scripted, the two passes were tuned, and no independent check passes at 50 or 60. I agree with that reading.
2. The model is less "self-organising" than its name suggests. At 50 and 60, height comes from a published curve, crown width from a published formula, and spare carbon is thrown away. Light and carbon mostly shape the detail, not the size.
3. So the trees are plausible-looking birches that follow forestry tables. They are not yet evidence that the growth rules are right.
4. The engineering for repeatable runs is good. The tests do not check a default tree at 50 or 60, and replaying past years is approximate.
5. Fix first: one fresh full run on today's defaults, tests nobody tuned against, and an honest carbon ledger.

## Scores out of 10

| Area | Score | Why |
|---|---|---|
| Model logic | 5 | The chain from light to death is coherent in code, but at maturity the main sizes are prescribed and carbon does not limit them |
| Validation logic | 5 | Labelling of tuned, by-design and independent is exemplary; but nothing independent passes, bands rest on 2-3 stands, and the young-stand comparison was changed after it failed |
| Engineering | 6 | Strong seeding, bit-identity and resume tests; weak end-to-end tests, golden runs outside CI, approximate replay, fragile packaging |

## What I recomputed

| Check | Age 50 | Age 60 | Reads |
|---|---|---|---|
| Eriksson curve, SI 23, T13 5.45 y (m) | 21.95 | 23.75 | Matches the report's 21.95 / 23.75; stand trees 21.91 / 23.71 sit on it |
| Band SI 20 to SI 26 (m) | 18.76-25.12 | 20.72-26.73 | Matches the report |
| k implied by plot light and LAI, -ln(light)/LAI | 0.372 | 0.381 | Matches the report; equals the model's input k of 0.37 |
| k implied by stand-tree light and LAI | 0.378 | 0.386 | Same link |

The same curve gives 4.45 m at total age 11 for SI 23, and 3.27 m for SI 20.

## Findings, most serious first

### 1. Carbon does not limit growth at the ages that are validated. CONFIRMED in code; size SUSPECTED

- Where: `treegen/growth.py:2521-2531`, `1851-1862`, `1951-1966`, `2047-2071`, `937-938`, `1386`.
- What:
  - The leader's shoot is the curve's yearly step times light, water and vigour factors. The project's own count says the curve alone set it in 1,200 of 1,200 seed-years (`reports/birch_v1_workings.txt:23`).
  - Limbs are "paid first" at a length set by the crown frame, not by the carbon solve (`1856-1859`).
  - Side shoots are capped by a leaf-area growth limit and a crown leaf-area ceiling (`1951-1966`).
  - What the pool cannot spend is "lost" (`2048`), then subtracted from the year's fixed carbon as "never fixed" (`2065-2071`).
  - Shortfalls are clipped to zero, so there is no debt or reserve (`937-938`). The roots' unspent share is logged as "rest" (`1386`).
- Why it matters: light to carbon to growth exists in the code, but for a healthy tree the answer is set by the curve, the frame and the caps. Changing photosynthesis would mostly change how much is discarded. That is sink-limited growth, a legitimate choice, but it means results at 50 and 60 say little about the carbon rules.
- Fix: save the discarded share (sink_limited / fixed, and the roots' rest) per year and print it at 50 and 60. Describe the model publicly as curve-driven with emergent crown detail until that share is small.

### 2. Height differences inside a forest are drawn, not earned. CONFIRMED

- Where: `treegen/growth.py:2523-2529`; `treegen/plot.py:131-132`, `214-228`.
- What: each plot tree gets a random vigour (spread 0.06) that multiplies its carbon and, directly, its yearly height step (`alpha / reference_alpha`). Each year the reference is reset so the plot's dominants land on the curve.
- Why it matters: plot top height passes by construction every year, and which trees are tall is largely the draw. Light can only slow a tree below 60 % light. The report labels height "by design" but not that the ranking is scripted.
- Fix: say so in the report. Longer term, let vigour act through carbon only and test whether size ranking emerges.

### 3. Nothing independent passes, and the two passes are one result. CONFIRMED

- Where: `reports/birch_v1_final.md:11-12`, `103-115`; `reference/targets.yaml:37-66`; `reference/betula_pendula/labels.yaml:55`.
- What:
  - Light under the canopy and leaf area are tied by light = exp(-k x LAI). The model's k (0.37) comes from the same paper as the light target, measured on the same two stands as the LAI target. My recomputed k (table above) confirms the tie.
  - The paper's own middle values cannot both be met at k 0.37: light 14.8 % needs LAI about 5.1.
  - The LAI band (3.6-5.4) is just the two stands' values. The Baltic band is three stands stretched to ages 6-60.
  - The light band 6.4-19.8 % is the range of "individual values". The model's stand mean is compared with that range, not with the 14.8 % median. SUSPECTED: I could not open the paper to see what an individual value is.
  - After crown fix C, plot light at 60 is 19.48 against a top of 19.8 (DECISIONS 107).
- Why it matters: "PASS" at 50 and 60 means "tuned until inside a wide band built from two stands". The report says this. Anyone reading only the scorecard would not see it.
- Fix: add checks nobody tuned against and score them: basal area and stem volume against yield tables, Repola stem and branch mass at the model's own DBH and height, diameter spread, height-diameter curve. Score light against the median with a stated tolerance.

### 4. The young-stand comparison was changed after it failed, and the fix was tuned on the new measure. CONFIRMED

- Where: `DECISIONS.md` rows 105 and 107; `KNOWN_ISSUES.md:2174-2176`; `reference/targets.yaml:96-107`.
- What:
  - The approved test is crown ratio 0.30-0.45 at ages 11-22. The model gave 0.92-0.96.
  - Row 105 switched to comparing at the same stand height. That is defensible: the source stands grew much faster.
  - But the figures then used (crown ratio 0.55-0.6 at 15 m, lowest branch 5-7 m at 13-15 m, Konopka's leaf area for height) are not in `targets.yaml`, not at the approved tag, and not scored by `scorecard.py`.
  - Crown fix C was tuned against these same young-crown measures and then reported against them. So it is "tuned against", not a pass.
  - The approved 0.30-0.45 band is no longer reported at all. By age the model still reads 0.94-0.97.
  - Row 105 says the model "follows Eriksson SI 23 (3.3 m at 11)". The SI 23 curve gives 4.45 m at 11. The 3.3 m is the plots' mean height.
  - The fix also pushed young LAI to 5.1-5.3 at 20-22, further over the Baltic band, and light up by 0.77 at 60.
- Why it matters: the one clearly independent failing test has been replaced by softer, unapproved ones on the day it failed.
- Fix: put the height-matched targets through the normal approval, with sources opened. Label fix C's results "tuned against". Better still, run the model at the source site's own site index and compare by age, as the target was written.

### 5. Published results do not describe the shipped defaults. CONFIRMED for the mismatch; SUSPECTED for stand trees

- Where: `reports/birch_v1_final.md:3-6`; `docs/site/how-real.md:80-84`; DECISIONS 99, 106, 107.
- What: the final report and the public page give v1 numbers. Since then the defaults changed three times (unrounded root strength, young roots, crown fix C). Row 107 reran 20 plots and 10 lone trees. I found no rerun of the 20 stand trees.
- Why it matters: a user who installs Cambium 0.9 gets trees the report does not describe.
- Fix: one full run of all four ensembles at the release commit, then regenerate the report and the page from it.

### 6. In old forests, seedlings shrink the big trees' crowns. CONFIRMED in code; effect SUSPECTED

- Where: `treegen/plot.py:394`; used at `treegen/growth.py:2287-2292` and `1682`.
- What: every tree's "spacing" is sqrt(area / all living trees), seedlings included. Limb reach is capped at 0.575 x spacing. At 150 years the report has 2,117 stems/ha, so the cap is about 1.25 m for a 27 m tree. The same spacing feeds the wind load.
- Why it matters: it may explain part of the 42 % light at 150 and the old trees' loss of crown. Results at 50 and 60 are barely touched, since there are few recruits then.
- Fix: count only neighbours of comparable height, or use each tree's local gap.

### 7. The carbon books are not a ledger. CONFIRMED

- Where: `treegen/growth.py:942-955`, `2042-2044`, `2065-2071`; `reference/betula_pendula/labels.yaml:33`.
- What: carbon-use efficiency is computed while the discarded carbon still counts as production. "Fixed" is lowered afterwards and the efficiency is not recomputed. The wood upkeep rate was tuned against that efficiency (0.47).
- Why it matters: one tuned value rests on an inflated number, and saved carbon figures do not add up. No test checks that carbon in equals carbon out (delegated read; only the roots' share is tested, `tests/test_roots_paid.py:47`).
- Fix: one yearly balance (fixed = respired + built + discarded) saved in stats, with a test.

### 8. Tests do not check a default tree at a meaningful age, and assert the scripted height. CONFIRMED by delegated read; two spot-checked

- Where: `tests/test_height_limit.py:59-62`, `:92`; `tests/test_crown_frame.py:153-154`; `tests/test_treegen.py:235-240`; `tests/test_roots_paid.py:84`; `tests/test_forest.py:430-432`, `488-491`.
- What:
  - The longest default run in the tests is about 25 years. The only whole-tree size check is height over 2 m at 14.
  - Height is required to equal the curve within 0.08 m. The "short of carbon" case only works with settings that are not the defaults.
  - Crown tests override the values crown fix C just set (floor 0.15 against 0.5, overlap 1.0 against 1.15), so fix C has no test.
  - Several tests switch a default off because the default broke them.
- Why it matters: the tests guard the machinery well but would not notice a default tree going wrong at 50.
- Fix: one slow test growing the shipped defaults to 60 with loose sanity bounds, and the golden run checked in CI.

### 9. Verdicts are written by hand because the scorecard cannot score forest runs. CONFIRMED

- Where: `reports/birch_v1_final.md:110-119`; `tools/scorecard.py:231-246`, `465-488`; `PROTOCOL.md:14`.
- What: forest runs keep no yearly per-tree records, so the scorecard returns "not applicable" for plot height and crown ratio. The report's "PASS (worked by hand)" and "FAIL (worked by hand)" come from `tools/v1_workings.py`. The protocol says never to write PASS or FAIL by hand.
- Also: the scorecard reads targets at the tag, while the working `targets.yaml` differs from it (Repola's mode now includes natural; Baltic source text). The wheel ships the working copy.
- Fix: let the scorecard read the plots' tree lists. Move the tag or revert the working copy so there is one set of targets.

### 10. Replay of past years is approximate, and the check is not on the default export. CONFIRMED by delegated read; one spot-checked

- Where: `treegen/export.py:559-602`, `781-794`; `treegen/growth.py:78`, `1339`; `git show replay:tools/replay.py` lines 209, 241-276.
- What: the timeline stores exact birth and death years, radii to 2 %, and positions only every 5 years. Between keyframes positions are held, and nodes born since get their final-year position. The replay check on branch `replay` grows with yearly keyframes, so the default 5-year export is never verified. That branch is unmerged and hardcodes a path under `~`.
- Why it matters: the game is meant to show growth stage by stage; between keyframes limbs will jump.
- Fix: state the position error in the header, interpolate between keyframes, and run the check on the default export.
- Dropped: the helper said the header mislabels the keyframe step. I checked `export.py:721-722`; it sits under `radius_encoding` and is right.

### 11. Wood shade is counted twice. CONFIRMED, self-disclosed

- Where: `reference/betula_pendula/labels.yaml:76`; `species/betula_pendula.yaml` `light.woody_shade`.
- What: the 0.37 was measured as light against leaf area with the wood already in it. The model adds wood shade on top. The label says so; it stays on.
- Why it matters: small here (implied k 0.37-0.39), but it is a known error left in a tuned result.
- Fix: turn it off, or lower the leaf k so the total is 0.37.

### 12. Smaller points

- CONFIRMED. `species/betula_pendula.yaml:845` keeps 4 years to breast height for the stats' own height check (`treegen/reference.py:28`), against 5.45 in the driver and scorecard. Two height bands in the outputs.
- CONFIRMED. `README.md:50` says every parameter has a source with estimates marked VERIFY. By my count of `labels.yaml`: 92 sourced, 212 VERIFY, 63 TUNED. The README title is still "treegen" and does not mention the height curve; the docs site does.
- CONFIRMED, minor. Plot tree seeds are `seed*1000 + k` (`treegen/plot.py:134`), so a plot starting with over 1,000 trees shares seeds with the next plot.
- CONFIRMED, minor. In a plot all trees share one damage random stream with draws that depend on state (`treegen/damage.py:343-350`), so paired plots stop being paired after the first difference.
- Delegated read. Checkpoints are plain pickle with no version stamp (`treegen/checkpoint.py:27,36`; `treegen/plot.py:535-545`).
- Delegated read. "Same bits on every machine" (`cambium/__init__.py:14-15`) is stronger than `pyproject.toml:14` and PROTOCOL allow; dependencies are ranges.
- Delegated read. Golden hashes live only in the ignored `out/` folder and are not run in CI (`tools/golden.py:42`); all four golden runs are seed 1, none open-grown.
- Delegated read. `treegen` alone cannot find species files from an installed wheel (`treegen/params.py:17-19`); the `cambium` layer works round it by loading `cli.py` as a script (`cambium/_engine.py:44-68`).
- Delegated read. `requirements.txt`, `requirements.lock` and `pyproject.toml` disagree (pillow, pypdf, numba pin, the NumPy comment).
- Delegated read. Private names remain in tracked files that ship, such as `species/betula_pendula.yaml:1995-2042`. DECISIONS 100 plans a cleaned copy; this checkout is not it.
- SUSPECTED. `treegen/game_unreal.py:1087` and `:1095` write a y value with opposite signs.

## What's genuinely good

- **Honesty.** The final report's own summary is harsher than most outside reviews would be. Tuned, derived, by-design and independent are kept apart, per value, in `labels.yaml`.
- **Corrections are recorded.** Wrong earlier claims are listed and withdrawn (`KNOWN_ISSUES.md:2188-2199`), including ones told to the owner.
- **Statistics.** Ensembles of 20 trees or plots, paired seeds, a 2-standard-error rule, a second draw when one looked lucky (DECISIONS 77).
- **Decision rules written before results** (DECISIONS 52, 62, 66, 68), and "pick nothing" when they were not met.
- **Determinism.** Every random stream is seeded per subsystem; no global random state; compiled kernels without fast-math; one maths thread; lossy speed options off by default (delegated read).
- **Bit-identity tests.** Lean against full, speed flags against originals, checkpoint resume against a straight run, pipe-model invariants.
- **Mechanisms that are real.** Light on a voxel grid, pipe-model stems, shedding by a branch's own light and carbon, a shared soil, and mortality with cited forms. Nothing moves a node to hit a number.
- **Disclosure in the public docs.** `docs/site/how-real.md` says "by design" and "this isn't a test" where it should.

## The top 5 to fix first

1. **One fresh full run on the release defaults** (stand trees, plots, lone trees, old forests), then regenerate the report and the public page. Finding 5.
2. **Add untuned tests and score them in the scorecard:** basal area, volume, Repola mass, diameter spread; light against the median. Finding 3.
3. **Settle the young-stand test properly:** approve the height-matched targets with sources opened, or run at the source site's site index; label crown fix C "tuned against". Finding 4.
4. **Make carbon an honest ledger** and report the discarded share at 50 and 60, so it is clear how much of the tree is curve and how much is carbon. Findings 1 and 7.
5. **Close the test gaps:** a default tree to 60, crown fix C on its real values, golden hashes in the repository and in CI; and fix the spacing rule before trusting anything past 100 years. Findings 6 and 8.
