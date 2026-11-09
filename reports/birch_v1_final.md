# Silver birch v1: final report

2026-11-09. Branch `reset-integration`.
- The final settings became the species defaults at d5f0ea3.
- Forests also rely on `tools/forest.py` switching on self-thinning (`mortality.enabled` is false in the species file), the natural start and regeneration.
- The runs below were on the server at 359bea4, a0f4880 and 8c2c496. These grow the same trees: section 9 has the proof.
- Hand-worked numbers are recomputed by `tools/v1_workings.py`. Its output is in `reports/birch_v1_workings.txt`.

## Summary

1. At ages 50 and 60 the birch matches what it was tuned to: light and leaf cover (one linked result). Height follows the published curves by design.
2. No independent check passes at 50 or 60.
3. Independent checks fail on young forests:
   - crowns reach almost to the ground (0.92-0.96 against 0.30-0.45 at 11-22);
   - leaf cover is outside the Baltic band in 46 of 55 years.
4. Old forests keep some first-generation trees to 200, longer than the (abstract-only) sources suggest.
5. Open: young crowns, leaf size, young roots, early deaths, and the game's full ageing (branch fall, cuts, more species). See sections 4 and 6.

The three reviews and the maintainer's open questions are on master:
- Checker (a), sources and targets: `reports/reviews/2026-11-08_final_check_a_sources.md`;
- Checker (b), numbers and consistency: `reports/reviews/2026-11-09_final_check_b_numbers.md`;
- Checker (c), rules and completeness: `reports/reviews/2026-11-09_final_check_c_rules.md`;
- QUESTIONS.md Q30-Q39.

## 1. What's in the model

| Part | What it does | Status |
|---|---|---|
| Height | The leader grows up to the Eriksson 1997 site-index curve (SI 23). The code can hold it back when light, water or carbon run short. But in the 20 final stand trees the curve set the leader's growth in every one of 1,200 seed-years, so height is close to scripted | By design |
| Crown | Limbs earn their reach and place (crown_frame, earned); twigs, short shoots and leaves follow bud rules | Mostly VERIFY or TUNED (section 5) |
| Stem | Pipe-model sapwood, heartwood by own foliage, wind-load stem theory | Mixed |
| Roots | Roots that cost carbon, lateral set-points | Mixed |
| Damage | Old age (Elfving 2010), wind (Kitenberga 2021), snow, and moose browsing of the leader (leader_damage, on) | Sourced shapes; some readings DERIVED |
| Forest | Self-thinning (Lee 2025 slope; sdi_max 763 TUNED), vigour and size mortality, seed rain, regeneration | Mixed |
| Look | Bark colour and black base by age and tree, fissures, peeling, lenticels, autumn colour, leaves on shoots, limb atlas | Look block: 9 sourced, 15 DERIVED, 181 TUNED. About half the look's tuned lines say they were set by eye on renders, and a few to the maintainer's taste (leaves.yellow_lift). Most of the look is not checked against data |

Value counts (`tools/species_report.py`, at 8521164): 417 model values, of which:
- 90 sourced, 55 of them checked against the page;
- 21 DERIVED;
- 90 TUNED;
- 216 unchecked (VERIFY).

All labels match their current values. Switches and choices aren't counted.

## 2. Results at ages 50 and 60

### Forest-grown trees: 20 seeds, final settings (node_v1_treesR, 8c2c496)

| Age | Height m | Stem cm over bark | LAI | Light % | Stem kg (Repola) | Branch kg (Repola) | Crown width m | Crown ratio |
|---|---|---|---|---|---|---|---|---|
| 50 | 21.91 | 26.9 | 4.82 | 16.2 | 229 (237) | 60.0 (46.4) | 5.25 | 0.53 |
| 60 | 23.71 | 30.4 | 4.68 | 16.4 | 335 (316) | 78.2 (63.8) | 5.77 | 0.45 |

Without roots and damage (node_v1_trees), paired over 20 seeds:
- Light is lower by 0.21 ± 0.22 points at 50 (noise) and by 0.73 ± 0.30 at 60 (2.5 SE, towards the median).
- LAI is higher by 0.05 ± 0.04 and 0.08 ± 0.05.

### Natural forests: 20 plots of 1,000 m² (node_v1_plots, 359bea4)

| Age | Stems/ha | Basal area m²/ha | Dg cm | Top height m (approved definition) | LAI | Light % (diffuse, 1-2 m) |
|---|---|---|---|---|---|---|
| 50 | 751 (640-810) | 23.9 | 20.1 | 21.35 | 4.54 | 18.5 (17.1-21.6) |
| 60 | 520 (470-570) | 25.7 | 25.1 | 23.14 | 4.36 | 19.0 (17.3-20.9) |

- Stems at 45: 953 per ha, against Hagemeier & Leuschner's 880 (an INFO target).
- At the same stem size: Dg 19.1 at age 48, with 803 stems and 23.6 m²/ha, against Hagemeier's 880 stems and 25.2 m²/ha at 45. That stand's printed figures don't add up (Q32), and stems and Dg were tuned against (section 3).
- The two forest fixes, on the same 20 seeds against the settings before them:
  - light at 50 rose 17.64 → 18.47 (+0.83 ± 0.26, 3.3 SE), and at 60 by +0.35 ± 0.28;
  - LAI changed by +0.03 ± 0.04, which is noise;
  - the fixes were first judged on 3 seeds. They still pass, but light moved further from the median.

### Lone trees: 8 seeds (node_v1_openR, 8c2c496)

| Age | Height m | Stem cm over bark | Crown width m | Hemery's formula at that stem |
|---|---|---|---|---|
| 50 | 17.77 | 44.5 | 8.65 | 8.81 |
| 60 | 19.24 | 49.4 | 9.35 | 9.68 |

This isn't a test. Width is capped at Hemery's crown by design (growth.py:2196-2205), at a stem of at most 2.4 cm per metre of height (2203). Hemery's coefficients are VERIFY and second-hand (Q36).

### Old forests: 3 plots to 200 years (node_v1_200, 359bea4)

Indicative only: a verdict needs 5 plots.

| Age | Stems/ha, all (past 1.3 m) | Basal area | Top height m (approved) | SI 23 curve m | Light % (diffuse) | First generation alive per ha |
|---|---|---|---|---|---|---|
| 50 | 780 (777) | 23.7 | no tree list | 21.95 | 19.1 | 770-790 |
| 60 | 540 (537) | 25.3 | 23.05 | 23.75 | 19.8 | 520-550 |
| 100 | 637 (330) | 31.2 | 26.39 | 27.50 | 28.5 | 230-280 |
| 150 | 2,117 (1,513) | 23.5 | 27.56 | 29.33 | 42.0 | 90-140 |
| 200 | 1,590 (1,137) | 25.1 | 26.87 | 30.17 | 33.6 | 30-90 |

- Before the forest fixes (node_H_plot200), no first-generation tree lived to 150, and top height ran 2.3-2.6 m over the curve.
- The sources for old-stand lifespan were read only as an abstract (Forests 2020) and a guideline page (Vakkari 2009). No checker has re-opened them.

## 3. Targets

"Kind":
- **By design:** the model is built to match.
- **Tuned against:** values were set to bring it closer.
- **Independent:** nothing was set against it.

| Target | Run | Age 50 | Age 60 | Share inside, 50 / 60 | Verdict | Kind |
|---|---|---|---|---|---|---|
| Light under the canopy, 6.4-19.8 % (median 14.8) | plots | 18.5 | 19.0 | 75 % / 75 % | PASS (scorecard) | Tuned against (shedding thresholds, death lines) |
| | stand trees | 16.2 | 16.4 | 80 % / 80 % | PASS (scorecard) | Tuned against |
| Hagemeier LAI, 3.6-5.4 | plots | 4.54 | 4.36 | 100 % / 100 % | PASS (scorecard) | Tuned against; the same result as light (k) |
| | stand trees | 4.82 | 4.68 | 80 % / 70 % | PASS (scorecard) | Tuned against (spacing_overlap) |
| Baltic LAI, 2.5-4.5 at 6-60 | plots | 4.54 | 4.36 | 40 % / 85 % | **FAIL at 50**, PASS at 60 (scorecard) | Tuned against at 50-60 (wind_speed, death lines). Independent at young ages, where it fails: inside only at 15-17 and 55-60 |
| Site-index height, SI 20-26 | plots, top height | 21.35 (18.76-25.12) | 23.14 (20.72-26.73) | | PASS (worked by hand) | By design |
| | stand trees | 21.91 | 23.71 | 100 % / 100 % | PASS (scorecard) | By design |
| Crown ratio, dense young stands, 0.30-0.45 at 11-22 | plots | 0.92 at 11, 0.96 at 15, 0.94 at 20, 0.93 at 22 | | 1 tree of about 27,000 at 11; none later | **FAIL**, far off (worked by hand) | Independent (Q34): profile_power was tuned on crown ratio at 50-60, not this band |
| Stand density, 880 at 45 | plots | 953 at 45 | | | INFO | Tuned against (wind_speed, sdi_max, rate_at_max) |
| Open crown width (Hemery) | lone trees | 8.65 | 9.35 | | INFO | By design |
| Crown ratio, managed (Repola; Hynynen at least 0.5) | stand trees | 0.53 | 0.45 | 85 % / 15 % at or over 0.5 | INFO | Tuned against (profile_power) |

How the hand-worked ones were done (all in `tools/v1_workings.py`):
- **Plot top height:** the scorecard doesn't score it, because plot runs keep no per-tree yearly records. It uses the scorecard's own `naslund_top_height` on the plots' tree lists (over-bark DBH).
- **Young crown ratio:** the scorecard says not applicable for the same reason. The figure is the mean over plots of each plot's mean (height − crown base) / height of live trees.
- **k:** −ln(light/100)/LAI per plot. It's 0.372 at 50 and 0.381 at 60.
  - Light at the 14.8 % median would need LAI 5.13 / 5.02.
  - Light at LAI 4.5 is 18.7 / 18.0 %.
- **Not scored,** because scorecard.py computes no value for them: bark thickness, wood density, carbon fraction, turning moment, foliage biomass.
- **Seedling targets** need seedling runs, which weren't part of this check.

## 4. What's still wrong

| Miss | Ours | Real | Why, as far as known |
|---|---|---|---|
| Young forests' crowns reach the ground | crown ratio 0.92-0.96 at 11-22 (20 plots; mean height 3.3-9.8 m) | 0.30-0.45 (Niemistö 1995, unopened; through targets.yaml) | My reading, not tested: lower limbs and short shoots stay alive in deep shade. The death lines were lowered to 0.15 to keep light in the band, which works against this |
| Crown starts too low on young trees | at 13.5 m tall: lowest live branch 0.8 m (0.2-1.8), crown base 1.6 m (0.5-2.9); 0 of 20 in 5-7 m | 5-7 m at 13-15 m tall (Hynynen & Niemistö 2009) | The same. Crown 2 reads it as young limbs extending slowly so the canopy closes late; there's no measured number for that |
| Leaf cover outside the Baltic band | under 2.5 at 6-14; over 4.5 at 18-54, peak 5.63 at 27 | 2.5-4.5 at 6-60 (its source is in doubt, Q30) | Young crowns hold too much leaf. At 50-60 it's the light trade-off in section 3 |
| Light near the top of the real range | 18.5 / 19.0 % | median 14.8 % | Linked to the line above through k. The forest fixes moved it up 0.8 points at 50 |
| Leaves too big | Sun and shade leaves are sized by light: 0.0015 × 60.8/LMA, so 10.2-18.1 cm² (growth.py:1414-1426). Earlier look runs measured a mean of 17-17.8 cm². The stats' steady 15.00 cm² is an artefact (growth.py:3116-3117) | 11.9 ± 5.7 cm² (Konôpka & Pajtík 2026, trees aged 4-20) | Leaves per node: smaller leaves at the same count gave 7-9 cm thicker stems |
| Leaf density near the top | 0.19 / 0.22 | their fit's 1.97 | Untouched |
| Double tops | 0 of 20 (strict) | 35 % (Zeltins 2018, read on mdpi.com earlier; couldn't be reopened in this check) | Cause unknown. Second tops are drawn per tree at Zeltins' 0.349 (growth.py:2052-2053) and through reiteration, and still don't last |
| Lone trees' longest hanging strands | longest 5.2 / 6.1 m; p90 at 60 4.1 m (3.9-4.3) | about 2-4 m in photos, judged by eye | p90 is at the top of the photo range |
| No early deaths in young dense forests | none of the trees in a 9,000/ha plot die in their first 5 years | real young stands lose stems at this stage | Self-thinning and background death act at any size. But self-thinning can't start until stems past 1.3 m make the stand dense, the "suppressed" hazard needs a stem diameter, and the carbon rule kills none. Trees on the height curve stay under 1.3 m for the first years |
| Young trees grow almost no roots | a 6-year tree has one root axis, 10 cm long; collar roots at 14 sum to 0.69, under Kalliokoski's lowest stand (0.86) | Laitakari 1934 p. 182: small trees (DBH under 5 cm) "may have only 2-3" main roots | The collar's room for roots is set by spacing tuned on 8-30 cm stumps (roots.py `_collar_waiting`). The fix comes after v1 |
| Small trees' uprooting decided by rounding | root strength read at 0.01 kNm steps; an 8-year tree's directions read 0.00-0.02, giving uproot chances of 1.0 or 0.0006 | | roots.py:855-857 rounds what damage reads. Fixed after v1 (DECISIONS 98) |
| Old trees die of carbon shortfall after 120 | crowns lost from below | no source gives a rate | Per-internode upkeep is untested at those ages |
| Foliage in stands | single strands | clumped sprays | Option J (d278fd4) gave sprays (Q37) |

Unclear rather than missed: stand branch wood is 29 % over Repola at 50 and 23 % at 60. That's inside 2 times Repola's ×/÷ 1.19 scatter for a 20-tree mean. But Repola includes bark and the model is wood only, so like for like the gap is somewhat larger.

## 5. Guessed values that matter most

These are TUNED, DERIVED or VERIFY; the full list is in `reference/betula_pendula/labels.yaml`.

| Value | Set to | Label: against what |
|---|---|---|
| short_shoot_light, short_shoot_survival_light, shedding.light_per_leaf_threshold | 0.15 | TUNED: light under the canopy. It no longer matches Hagemeier's 21 % shade-leaf light |
| pipe_model.stem_theory.wind_speed_m_s | 8 | TUNED: Dg, stems/ha and LAI on plots |
| crown_frame.profile_power | 0.8 | TUNED: the outline and crown ratio at 50-60 |
| crown_frame.spacing_overlap | 1.15 | TUNED: stand light and width |
| bud_fate.long_shoot_threshold, density_control.af_zero | 5, 1.7 | TUNED: crown flips, branch count, crown fill |
| crown_frame.limb_sag_deg, reach_scatter, open_lai_max, twig_shoot_max_m; mechanics.pendulous_radius | 45, 0.5, 5, 0.5, 0.012 | TUNED: the look |
| crown_frame.stem_cm_per_height_m | 2.4 | TUNED: the open DBH band, which is abstract-only and not a target |
| crown_frame.surplus_to_stem | 1.0 | VERIFY: a choice, not a fit |
| height_driver.open_grown_share | 0.8 | TUNED: photos of open-grown birches |
| mortality sdi_max, rate_at_max | 763, 0.247 | TUNED: Aosaar and Martinik stands (Q33) |
| mortality.vigour.* | | TUNED against model behaviour: base plots whose trees stood still |
| mortality.vigour.relative_size_slope | 3.263 | DERIVED: Maleki & Kiviste 2016 Table 3, used as an odds factor |

## 6. The rest of the reset: what's there and what isn't

The reset asked for a birch matching real life, forests that spread like real ones, every aspect of ageing in the game, and room for more species.

| Part | State |
|---|---|
| Forest spread | Seed strips reach about 575 m by year 45, at the fast end of real rates. far_share 0.003 is TUNED; it was changed from 0.005 after the plots in this report ran. Small storm gaps never refill: 3 of 373 seedlings got past 10 years. A 314 m² windthrow does refill (master log, 19:15). |
| Bark ageing | Bark colour by age, black base by tree (Jones, via the look), fissures, peeling and lenticels are in the look code. Bark thickness follows Hansen 2023. Most look values were set by eye on renders, and none is scored against data. |
| Autumn | Autumn leaf colour exists in the look and game export. It's set partly to the maintainer's taste. |
| Branches falling | Twigs and limbs are shed by light and carbon. Nothing lands on the ground, and hanging dead branches aren't modelled. Both are needed for the game (DECISIONS 91). |
| Cutting and felling | Not modelled yet: cuts, wounds, hand-over to the game, stump sprouts (`reports/cpp_port_plan.md`). |
| More species | docs/adding_a_species.md and species/_template.yaml exist. But 427 settings aren't in species_schema.py, and plots hold one species. Pine and spruce dominate the game area. |
| Game export | Tested in a separate Unreal project. On the v1 defaults, trees 6 years old or younger got no below-ground roots file. The export fix is on final-fixes-b, being reviewed. Real roots do reach the export from age 8. |
| Live growth in the game | About 38-43 MB per tree in Python, about 140 full trees per GB, against 4,222 birches in reach (estimates in the port plan). The game's own memory hasn't been measured; that needs the game run. |

## 7. How this departs from a real tree

- Stand trees' neighbours are copies of themselves.
- Leaves come per node: two and a half per short shoot. Their size is set by light alone.
- Long shoots: on axes finer than the stem, only the end bud starts them (growth.py:995-1001). The stem's limbs come from buds the crown frame names.
- Limb curve comes from a set-point that moves with wood age, plus the load bend from mechanics.
- Open trees: the leaf cap is open_lai_max 5 (stand trees have crown_lai_max 7). Spare carbon goes on the stem only up to 2.4 cm per m of height.
- In stands, reach also stops at 1.15 × half the spacing.
- Height follows a curve by design.
- Twig browsing is a setting of place, off in the main tree. Moose browsing of the leader is on.

## 8. Changes made in this check

- **Checker (a):** labels and comments made honest, with a DERIVED status added, 42 new labels and 7 guesses moved to VERIFY. tree_table saves open runs as open. The mortality block's old age now follows Elfving.
- **Defaults switch (d5f0ea3):** 48 values. The 12 labels older than their new values were relabelled from the record (final-fixes-b).
- **Tests:**
  - 22 tests that assumed the old defaults or the old tree size now set what they need. A separate review is checking that none is loosened.
  - example_tree handles a tree under 1.3 m.
  - The damage log keeps small moments (4 significant figures).
  - The game export always writes a roots file.
- **Checker (b):** this report rewritten.
- **Checker (c):**
  - this report corrected;
  - the workings script added;
  - KNOWN_ISSUES.md given a v1 section with the corrections;
  - DECISIONS rows 93-98 added;
  - docs/unreal.md and cpp_port_plan.md brought in line with row 91.

## 9. How this was checked

- **Same trees across commits:**
  - Stand trees at 359bea4 (node_v1_trees) are identical to Crown 2's at e10c6a4 (node_c2Hf20s): 1,220 seed-years.
  - The young plots at 8c2c496 match node_v1_plots at 359bea4 in all 440 plot-years to 22.
  - Open trees match between 359bea4 and a0f4880.
- **Defaults switch (golden proof):**
  - Golden runs recorded with the final settings set by hand on 8c2c496 (node_gold_v1pre), and as defaults on d5f0ea3 (node_gold_v1post).
  - All 225 output files are identical. Hashes are in `Cambium-int/out/bench/golden/`.
  - A new golden baseline is recorded after the last merge, since the damage-log and export fixes change some output files.
- **Speed settings:** all six together give identical trees (2 seeds, stand trees to 30).
- **Tests, at 64b3fc2 (merged as 85d147a):**
  - 392 tests; 6 fail.
  - Two are known model faults, kept failing on purpose (DECISIONS 98):
    - small trees' root strength is rounded to 0.01 kNm (roots.py:855-857), so whether they uproot depends on rounding;
    - on the shipped defaults the 14-year collar sums to 0.69, under the 0.70 floor (`test_on_the_v1_defaults_the_collar_sums_to_the_stump`, added after the test-edit review).
  - The other 4 need the full project: the approved-targets-tag test, the scorecard test and two machine tests. They last passed on the PC at ae1a2e1 (2026-11-07) and were **not run for v1**. A full clone on the server was blocked by a safety check, and the PC is the maintainer's (Q39).
  - A separate review of the 23 changed tests, 2 helpers and 3 new tests since 359bea4 found none loosened (master: `reports/reviews/2026-11-09_test_edits_review.md`).
- **The three checkers** ran on three versions: (a) at 359bea4, (b) at 8521164, (c) at 8fd4fdb. Each version after the last checked one changed labels, tests, the export and this report, not growth.

## 10. Corrections to earlier reports

Also in KNOWN_ISSUES.md:
- The open-tree width matching Hemery was reported to the maintainer as a check. It holds by design.
- reports/tree_handover.md's 5.2 m crown base at 14 m was the older crown. v1 has 0.8 m.
- The old-age hazard was misread as yearly at 03:30 on 2026-11-08. The forest agent corrected it.
- Q30 said the model sits "near the band anyway". It's outside the Baltic band in 46 of 55 years.
- Earlier drafts of this report:
  - said leaves are a fixed 15 cm²;
  - said mortality acts only past 1.3 m;
  - said "Zeltins, unopened";
  - said browsing is off;
  - said "noise only" for light at 60 between the tree runs.
- The birch-data PDF filed as Niemistö 1995 is Tuomela & Kanninen 1995. birch-data's catalogue is corrected; the file itself stays.

## 11. Decisions

DECISIONS.md rows 93-98:
- 93: the defaults switch;
- 94: the forest fixes, adopted on 3 plots, then confirmed on 20 with light up 0.8 at 50;
- 95: keeping the current crown over J;
- 96: server-only work while the PC is the maintainer's;
- 97: the targets.yaml citation fix without moving the tag;
- 98: v1 ships with the small-tree root-strength rounding, young roots and early deaths as known faults, fixed together after v1 with one re-run.

The maintainer's open questions: Q30-Q39.

## 12. Tried and dropped

- **J, two end buds per shoot (d278fd4).** Paired against the final crown on 10 seeds:
  - young LAI is higher (+0.58 at 20, +0.85 at 22), which is worse;
  - crown ratio is lower by 0.07 at 30 and 0.02 at 50-60, which is towards the young-forest target and Repola's 0.58 at 30;
  - basal area is a little higher (23.1 / 25.2 against 22.8 / 24.6), closer to Hagemeier's 25.2 / 28.5;
  - light differences are within noise;
  - its stand sprays look more like photos.
  - It was dropped on light and young LAI. Light doesn't hold up as a reason, so the choice is closer than first said (Q37).
- af_zero 3.2.
- twigs_age.
- end_buds_per_m.
- Surplus to the stem with neighbours.
- The Evo frame for stand trees.
- Line 0.19 and branch_aging_years 12.

## Renders

Copied into `reports/renders/`:
- `v1_stand_60.png`: the 60-year forest;
- `v1_open_30_60.png`: the lone tree at 30 and 60.

Both were made at d9d4ce1. Its crown is the same as v1's; the forest fixes and defaults change no single tree.
