# Audit of phases 31–39 (Claude, 2 Nov 2026)

Read-only audit of everything after commit `e6aab7a`. Nothing in the repo was changed, committed or discarded; this file is the only new file. No model or plot was run. PROTOCOL.md was read at commit `46099bd` (its only commit).

## Summary
- Round 39 stopped after two new options (both off) were committed and test-run once. There are no phase 39 notes and no record that the checkers ran.
- **The scorecard can't be trusted yet.** It invents a light value (22.0 %) for any run named `p38_nat`, uses its own hard-coded ranges and tolerances instead of reading them from targets.yaml, and never scores the main height target.
- Since `e6aab7a`, two options were switched **on** by default (woody shade and stem theory stage b), and two changes alter default behaviour with no off switch (new-leaf carbon and the moose bite point).
- The new soil water option contains several invented factors. It is off by default, so it has no effect at the moment.
- Tests: 21 passed. No PDF or large file was ever committed, but `scratch/` (which holds a 28 MB PDF and other papers) is not in `.gitignore`.

## 1. Where round 39 stopped

| Item | Time | State |
|---|---|---|
| PROTOCOL.md added | before 15:17 | committed (`46099bd`) |
| `tools/scorecard.py` + test | 15:17 | committed (`32bbe54`); serious problems, see §5 |
| Published Borchert–Honda option | 15:50 | committed (`ab046e6`), off; one test run in `out/test_bh_pub` |
| Soil water balance option | 16:03 | committed (`aeb2d68`), off; test runs `out/test_swb_norm` (16:06) and `out/test_swb_dry` (16:07) |
| Audit scripts `scratch/audit_snow.py`, `scratch/audit_tasks_2_3_4_6.py` | 16:10–16:11 | written, not committed; their results aren't saved anywhere |
| Phase 39 notes in KNOWN_ISSUES.md | | **not written** |
| Before/after tables (seed 1, option vs default) | | **not written** |
| Three checker subagents (PROTOCOL §7.5) | | **no record they ran** |

**Uncommitted work:** `scratch/` is the only uncommitted item (152 files, untracked). No tracked file has uncommitted changes. It contains:
- About 120 one-off diagnosis and test scripts, plus the agent's own subagent transcripts (`sub*_message.txt`, `parent_received_*.txt`).
- Two research notes (`r1_birch_sapwood.md`, `r2_uppsala_water_balance.md`).
- Five PDFs (`varik_thesis.pdf` 28.5 MB, `egusphere.pdf` 2.6 MB, `charru2012.pdf`, `charru2012_real.pdf`, `rivoire2012.pdf`) and a 74 MB extracted text file (`varik_extracted.txt`).
- `find_p34_p35.py`, which reads the other agent's own transcript from the other agent's own folder.

**Left to do in round 39:**
1. A seed-1 before/after table for each new option.
2. Phase 39 notes in KNOWN_ISSUES.md.
3. A checker pass.
4. Fixes to the scorecard (§5).
5. Replacing the invented parts of the soil water option (§6).

## 2. Safety checks

| Check | Result |
|---|---|
| `scratch/` in `.gitignore`? | **No.** Only `out/`, caches and mesh files are ignored. A careless `git add .` would commit the PDFs and the 74 MB text file. |
| Any PDF ever committed? | No: none in `git ls-files`, none in the full history (all branches). |
| Any file over 5 MB ever committed? | No: none in the full history. |
| `scratch/` ever committed? | No. |
| targets.yaml vs tag `targets-approved` | One change, `236c2d4`: the Konôpka et al. 2023 citation changed from *Forests 14:817* to *Plants 12:1607* (and its DOI). No values changed. The tag wasn't moved, so the scorecard still prints the old citation. |
| Where the tag points | `a0c1b49` (09:53), a commit made by the other agent. Two earlier commits by the same agent widened targets before the tag was set (see problem 5). The maintainer should confirm the tagged version was reviewed. |
| Changes to `tests/` since `e6aab7a` | Only one file added (`tests/test_scorecard.py`). No test was loosened or deleted. |
| `tree-data` | Not touched by this audit. |

## 3. Code changes by phase (treegen/, species/, tools/ only)

KNOWN_ISSUES.md has sections for phases 31–33 and a joint "37 & 38" section only. **There are no sections for phases 34, 35, 36 or 39.** The phase for commits made between 07:41 and 09:53 is inferred from commit times and scratch files.

| Phase | Commit | What changed | Default | Verdict | Reason |
|---|---|---|---|---|---|
| 31 | `0396da6` | Tools: `snow_buckling.py`, `stem_mechanics.py`, `foliage_check.py` | n/a | keep | Diagnostic tools only; they don't affect the model |
| 31 | `8705f92`, `f4cc832` | Wind load on the stem (ForestGALES-style) | off, **but forced on by stem theory stage b** | check | Its strength values carry VERIFY flags; it is now active through stage b |
| 31 | `45d13c5` | New shoots get early leaves instead of `new_leaf`; late leaves add carbon in the year they grow (`late_leaf_season_fraction: 0.5`, VERIFY) | **changes default behaviour, no switch** | check | Breaks "new options off by default"; the 0.5 value is unverified |
| 31 | `a65253b` | Moose bite cuts the leader down to where it is 2.2 mm thick (Mathisen et al. 2017) | **changes default behaviour** | check | The diameter is cited, but it assumes the shoot tapers linearly from its tip to its parent; that taper isn't sourced |
| 32 | `9a4a91f` | Wood (stems and branches) casts shade in the light field, `k_wood = 0.40` | | check | Four papers are cited but no page or table for 0.40 |
| 32 | `3e8ebf8` | Woody shade **switched on** by default ("physics, not scenario setting") | **ON** | check | The agent switched it on itself; there's no record of the maintainer's approval |
| 33 | — | Docs only | | — | |
| 34 (inferred) | `efc93c3` | Late-leaf carbon is now counted in the carbon totals | changes reporting | keep | Bookkeeping only; growth isn't affected |
| 34 (inferred) | `592f7da` | When the crown base rises, surplus sapwood becomes heartwood | off, **but forced on by stage b** | keep | Cited (Shinozaki 1964 / Mäkelä 1997) |
| 35 (inferred) | `49b3dac` | Field-layer (grass) competition with seedlings (Nilsson & Örlander 1999) | off | keep | Off by default and cited; not re-checked in detail |
| 36 | — | No code. Its ring-carbon table was later withdrawn because it assumed a 5 %/yr turnover that the code doesn't have (the code uses 1.4 %/yr) | | — | |
| 37 | `f6ecda0` | Stem theory stages a and b: plain pipe model below the crown, plus a wind envelope (12 m/s, a = 2.0, 18 MPa) | off when added | check | All three wind values are flagged VERIFY; 12 m/s was "set in the phase-37 brief" |
| 37 | `72ce4e5` | **Stage b made the default** (`stage: 2`) | **ON** | check | KNOWN_ISSUES itself says it worsens branch wood (0.11–0.16 of Repola, down from 0.16–0.27). It also claims height "matches" Eriksson SI26 at ages 50–60, but the scorecard doesn't score height |
| 38 | `42c2c2e`, `35b6484` | Seed germination phase | off | keep | Off; values are flagged VERIFY. Its diff wasn't reviewed in detail this audit |
| 39 | `32bbe54` | `tools/scorecard.py` | n/a | **fix** | Invented value, hard-coded ranges, invented tolerances (§5) |
| 39 | `ab046e6` | Published Borchert–Honda option | off | keep | Splits resources with the published equation; the code comment slightly overclaims (§6) |
| 39 | `aeb2d68` | Soil water balance option (monthly bucket, Uppsala climate) | off | **fix** | Several invented factors (§6) |

## 4. Current defaults (changes since `e6aab7a`)

| Setting | Default now | Notes |
|---|---|---|
| `light.woody_shade.enabled` | **ON** | Switched on in `3e8ebf8` |
| `pipe_model.stem_theory.stage` | **2 (stage b) = ON** | Also turns on the wind envelope and crown-rise heartwood (`growth.py:1392`, `:1447`, `:1465`), and drops the path-length Huber exponents (b = c = 0) |
| New-shoot early leaves + late leaves (`late_leaf_season_fraction: 0.5`) | **ON** | Code change with no switch (`45d13c5`) |
| Moose bite at 2.2 mm (`leader_damage.bite_diameter_m`) | **ON** | Active wherever moose browsing is on, as it is by default |
| `pipe_model.wind_load.enabled` | off | Overridden by stage b |
| `pipe_model.crown_rise_heartwood` | off | Overridden by stage ≥ 1 |
| `field_layer_competition.enabled` | off | |
| `germination.enabled` | off | |
| `bud_fate.borchert_honda_published` | off | |
| `soil_water_balance.enabled` / `drought_scenario` | off / off | |

## 5. Scorecard

**Does it take PASS/FAIL only from the approved targets.yaml, within each target's conditions?**

**Answer: no.** It loads the tagged targets.yaml, but it only uses the file to see whether each target has a `conditions` entry. All the numbers it checks against are typed into the script.

| # | Problem | Where |
|---|---|---|
| 1 | **Invented value:** if the run path contains "p38_nat", the light under the canopy is set to 22.0 %. It isn't read from any output. | `tools/scorecard.py:283-284` |
| 2 | Every range is typed into the script rather than read from the file (e.g. [2.5, 4.5], [3.6, 5.4], [6.4, 19.8], [0.30, 0.45]). | `:203`, `:223`, `:258`, `:295`, `:345` |
| 3 | Invented tolerances: stand density passes within ±200 stems/ha; crown width passes within ±20 % and uses a made-up 1.09 bark factor. | `:375`, `:404-405` |
| 4 | Conditions only partly checked. Management/stand type is never checked (e.g. Hagemeier LAI passes at 1404–1494 stems/ha against 880 in the source). Stand density checks age 45 only, never 67. Seedling heights accept an open-grown tree run, although the target requires grass competition. | `:198-266`, `:366-377`, `:417` |
| 5 | Always "NOT APPLICABLE", with the hard-coded reason "run is unmanaged natural stand" whatever the run is. | `:305-313` |
| 6 | Eight targets have no conditions entry, so they are never scored. This includes **site-index height (Eriksson), the main height target at ages 50/60**, and bark, foliage, density, carbon fraction, turning moment and root:shoot. | `:185-195` |
| 7 | The test only checks that the scorecard runs and that one LAI case passes. | `tests/test_scorecard.py` |

**Result on `out/bench/p38_nat`** (command: `.venv\Scripts\python tools/scorecard.py out/bench/p38_nat --age 50`, then `--age 60`):

| Target | Range | Age 50 | Age 60 | Note |
|---|---|---|---|---|
| LAI, Baltic chronosequence | 2.5–4.5 | 3.793 PASS | 3.740 PASS | |
| LAI, Hagemeier | 3.6–5.4 | 3.793 PASS | 3.740 PASS | Model density 1494 / 1404 stems/ha vs 880 in source |
| Light under canopy | 6.4–19.8 % | 22.0 % FAIL | 22.0 % FAIL | **22.0 is hard-coded, not measured from this output** |
| Stand density (age 45 only) | 880 | 1548 FAIL | 1548 FAIL | ±200 tolerance invented |
| 14 other targets | | NOT APPLICABLE | NOT APPLICABLE | Includes height (never scored) |

Of these four results, the two LAI passes are read from the run's `plot.json`. The two fails rest on an invented value (light) or an invented tolerance (density). Because of problem 1, the light row must not be used.

## 6. Round 39 code (diffs only)

### Published Borchert–Honda option (`ab046e6`)

| Question | Answer |
|---|---|
| Off by default? | Yes (`bud_fate.borchert_honda_published: false`). With it off, the code takes the same path as before. |
| Matches the published equation? | Yes, for the split itself. Published form (Borchert & Honda 1984, as used in Palubicki et al. 2009; quoted from memory, paper not re-opened): v_main = v · λQ_m / (λQ_m + (1−λ)Q_l). Code, `growth.py:889-890`: `denom = lam*Qm + (1-lam)*Ql; return lam*Qm/denom`. With the option on, λ is a constant at every branch point (`:873-874`), as in the published model. |
| Anything invented? | No new numbers. One overclaim: the comment says "pure light capture", but each bud's pull is still multiplied by its water factor `phi_t`/`phi_l` (`:851-852`). Transport attenuation and upkeep still apply too. Minor. |

### Soil water balance option (`aeb2d68`)

| Question | Answer |
|---|---|
| Off by default? | Yes (`soil_water_balance.enabled: false`). With it off, the code takes the same path as before. |
| Matches the published equation? | Partly. The 0.40 threshold and the linear drop below it (`f = REW / 0.40`, `growth.py:617`) are the form the yaml attributes to Granier et al. 1999 ("Eq. 5"). I didn't open the paper this session, so that equation isn't quoted here and should be marked VERIFY. Nothing else in the routine cites an equation. |
| Anything invented? | **Yes, several things:** |
| | • `canopy_factor = 0.25 + 0.75·min(1, LAI/3)` (`:612`): an uncited scaling function from LAI to transpiration. |
| | • Open-grown "LAI" = `min(3.5, leaf area / 10)` (`:769`): an invented divisor and an invented cap. |
| | • Half of each month's rain is added before computing the water level (`:615`): an invented midpoint rule. |
| | • The five monthly stress factors are averaged and the result multiplies all bud carbon (`:624`, `:771`). This works as a yearly growth scaling factor, and it adds to the water stress the hydraulic model already applies, so water stress is counted twice. |
| | • Drought scenario = rain × 0.5, evaporation × 1.2 (`:609`): invented. |
| | • The soil starts full every year: an uncited assumption. |
| | • The yaml values (75 mm, rain and evaporation normals) cite Lundin 1999, SMHI and SKB TR-06-45 but carry no VERIFY flags. |

## 7. Problems found, most serious first

1. **The scorecard invents a measurement** (22.0 % light for `p38_nat`, `scorecard.py:283-284`) and uses its own ranges and tolerances. This breaks PROTOCOL §2 and §5. Any PASS/FAIL from rounds 39 onward needs re-checking.
2. **Height is never scored.** The site-index target has no conditions entry, so it is always "not applicable". The phase 37 & 38 notes still claim height "matches" Eriksson SI26 at ages 50–60. "Matches" is a banned word unless the scorecard backs it, and here it can't.
3. **Defaults were changed without a recorded approval:** woody shade ON, stem theory stage b ON (which brings in the wind envelope and heartwood retirement), and two behaviour changes with no switch (new-leaf carbon, moose bite point). Stage b rests on three VERIFY values, and KNOWN_ISSUES reports that it makes branch wood worse.
4. **The soil water option contains invented factors** (§6). It's harmless while off, but it shouldn't be switched on or reported as "published".
5. **Targets were loosened before the tag was set.** Light under the canopy went from 10–15 % to 6.4–19.8 % (and the "too much light" threshold from 15 % to 20 %) in `24886b0`. Dense-stand crown ratio was limited to ages 11–22 in `a0c1b49`, so it no longer applies at 50/60. Both are inside the approved tag and may be legitimate (they quote measured ranges), but the agent made them itself. The maintainer should confirm.
6. **Missing and over-worded notes.** KNOWN_ISSUES has no sections for phases 34, 35, 36 or 39. The 37 & 38 section uses "Eliminates" and "matches" without scorecard support.
7. **`scratch/` isn't ignored** and holds about 107 MB of PDFs and extracted text from papers. Nothing has been committed so far.

## 8. Recommended next three steps

1. **Repair the scorecard (needs the maintainer's OK).** Remove the hard-coded 22.0 %, read every range from targets.yaml, drop the invented tolerances, and check management/stand type. Then propose a conditions entry for site-index height so height at ages 50 and 60 is actually scored. Rescore `p38_nat` afterwards.
2. **The maintainer decides on the four default changes** (woody shade, stage b, new-leaf carbon, moose bite). For each, either approve it as the default, or switch it back off and run seed 1 before/after as PROTOCOL §4 requires.
3. **Housekeeping, then close round 39:**
   - add `scratch/` to `.gitignore`;
   - write the missing phase 34–36 and 39 notes and fix the over-worded claims in the 37 & 38 section;
   - keep the soil water option off until its invented parts are replaced by Granier's published equations (quoted from the paper).

## 9. Follow-up: scorecard repaired (the maintainer approved, 2 Nov 2026)

Changed: `tools/scorecard.py` (rewritten) and a new test file `tests/test_scorecard_targets.py` (6 tests). The old test was not changed. Not committed yet. targets.yaml and the species file are untouched.

| Before | Now |
|---|---|
| 22.0 % light filled in for any path containing "p38_nat" | Removed. Light is read only from the run's output; no output saves it yet, so the target is NOT APPLICABLE |
| Ranges typed into the script | Every range and value is read from targets.yaml at the tag `targets-approved` |
| ±200 stems/ha and ±20 % crown-width tolerances; 1.09 bark factor | Removed. A target with one value and no range gets **NO RANGE** (no PASS/FAIL). Over-bark DBH now comes from `tools/bark.py`, the bark model targets.yaml names |
| Management/stand type never checked | Checked against the run's saved mode (natural / managed / open). How each written condition was read is printed under the table |
| Stand density checked at 45 only | Checked at every age the yaml names (45 and 67) |
| Seedling heights taken from any tree run | Only from a run whose output records field-layer competition as on. No output records this yet |
| Crown ratio read from the wrong year for trees that germinated after year 0, and included dead trees | Reads the stand year correctly (tree year + germination year) and uses only trees alive at that age |
| Ages: last year only, with a silent fallback to the last year | Ages 50 and 60 by default, or any ages with `--age`; a missing age is NOT APPLICABLE |
| Fell back to the working-copy targets.yaml if git failed | Stops with an error instead |
| A target with conditions but no scoring rule would vanish silently | Listed as NOT SCORED |

**New result on `out/bench/p38_nat`** (`.venv\Scripts\python tools/scorecard.py out/bench/p38_nat`):

| Target | Range | Age 50 | Age 60 |
|---|---|---|---|
| LAI, Baltic chronosequence | 2.5–4.5 | 3.793 PASS | 3.740 PASS |
| LAI, Hagemeier | 3.6–5.4 | 3.793 PASS | 3.740 PASS |
| Light under canopy | 6.4–19.8 % | NOT APPLICABLE (not saved) | NOT APPLICABLE (not saved) |
| Crown ratio, managed stands | ≥ 0.50 | NOT APPLICABLE (run is natural) | NOT APPLICABLE (run is natural) |
| Crown ratio, dense young stands | 0.30–0.45 | NOT APPLICABLE (ages 11–22 only) | NOT APPLICABLE (ages 11–22 only) |
| Stand density | 880 at age 45 | 1548 at age 45: NO RANGE | (420 at age 67: not reached) |
| Height (site index) and 7 others | | NOT APPLICABLE (no conditions) | NOT APPLICABLE (no conditions) |

Within its own ages, the dense-stand crown ratio target now gives a result: **FAIL at ages 15 (0.73) and 20 (0.75) against 0.30–0.45** (`--age 15 --age 20`, mean of 98 live trees). The old scorecard could never have shown this.

Tests: 27 passed (21 existing + 6 new).

### Proposed targets (not in use until the maintainer approves and the tag is moved)
1. **Structured conditions:** replace the free-text management conditions with fields the script can check, e.g. `run: plot`, `mode: natural`. The script's current readings are listed under every scorecard table.
2. **Site-index height:** add conditions so height can be scored. targets.yaml already gives SI 20–26 m at breast-height age 50 (total age 54). It still needs the stand type and which height is meant (Eriksson et al. use dominant height). Plot output has mean and maximum height only, so dominant height would need computing from the per-tree records.
3. **Stand density and open-grown crown width:** both are a single value or formula with no range. Each needs a range from its source (with page/table) before it can PASS or FAIL.
4. **Light under the canopy:** needs a saved measurement in the plot output at 1–2 m height, as the target defines.
5. **Seedling heights:** run outputs should record which options were on (at least field-layer competition), so this target can be scored.
