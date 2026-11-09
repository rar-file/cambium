# Silver birch v1: final report

2026-11-09. Branch `reset-integration`.
- The final settings became the species defaults at d5f0ea3.
- The runs below were on the server at 359bea4, a0f4880 and 8c2c496. These grow the same trees: section 7 has the proof.

This report is the reset's one full check (PROTOCOL section 10, `reports/reset_brief.md`). The reviews and the maintainer's open questions are on master:
- Checker (a), sources and targets: `reports/reviews/2026-11-08_final_check_a_sources.md`. Its FIX items are fixed.
- Checker (b), numbers and consistency: `reports/reviews/2026-11-09_final_check_b_numbers.md`. This version answers its FIX items.
- QUESTIONS.md Q30-Q37.

## In short

- **At ages 50 and 60, no independent target passes.**
  - Height matches the site-index curve by design.
  - Light under the canopy and the Hagemeier leaf cover pass, but they're one result, and it was tuned against. Light follows leaf cover at a near-fixed extinction coefficient, k about 0.37-0.40, which is the light paper's own 0.37.
  - The Baltic leaf-cover band fails at 50 by 0.04, with 40 % of plots inside, and passes at 60. Plot leaf cover at those ages was tuned against too.
  - Light sits near the top of the real range, 18.5 / 19.0 % against a median of 14.8 %. With this k, the two leaf targets pull against each other. Light at the median needs leaf cover of about 5.1, which would fail the Baltic band. Keeping leaf cover at 4.5 or less means light of at least about 18.7 %.
- **The independent checks fail clearly.**
  - Young forests at 11-22 have crowns almost to the ground: crown ratio 0.92-0.96, where real ones are 0.30-0.45.
  - Plot leaf cover is outside the Baltic band in 46 of the 55 years it covers: under it at 6-14, over it at 18-54.
- **Old forests:** 30-90 first-generation trees per ha are still standing at 200 years, from 3 plots, which is below the 5 a verdict needs. That's longer than the sources found suggest: stands persisting to 121-150, and a typical maximum age of about 100, sometimes 150.

## 1. What's in the model

| Part | What it does | Status |
|---|---|---|
| Height | The leader grows up to the Eriksson 1997 site-index curve (SI 23), less when short of light, water or carbon | By design |
| Crown | Limbs earn their reach and place (crown_frame, earned); twigs, short shoots and leaves follow bud rules | Mostly VERIFY or TUNED (section 5) |
| Stem | Pipe-model sapwood, heartwood by own foliage, wind-load stem theory | Mixed |
| Roots | Roots that cost carbon, lateral set-points | Mixed |
| Damage | Old age (Elfving 2010), wind (Kitenberga 2021), snow | Sourced shapes; some readings DERIVED |
| Forest | Self-thinning (Lee 2025 slope; sdi_max 763 TUNED), vigour and size mortality, seed rain, regeneration | Mixed |
| Look | Bark colour by age, black base by tree, leaves on shoots, limb atlas | Look block: 9 sourced, 15 DERIVED, 181 TUNED |

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
- The two forest fixes, on the same 20 seeds against the settings before them: light at 50 rose 17.64 → 18.47 (+0.83 ± 0.26, 3.3 SE), and at 60 by +0.35 ± 0.28. LAI at 50 went 4.51 → 4.54, which is noise. The fixes were first judged on 3 seeds. They still pass, but light moved further from the median.

### Lone trees: 8 seeds (node_v1_openR, 8c2c496)

| Age | Height m | Stem cm over bark | Crown width m | Hemery's formula at that stem |
|---|---|---|---|---|
| 50 | 17.77 | 44.5 | 8.65 | 8.81 |
| 60 | 19.24 | 49.4 | 9.35 | 9.68 |

Width is capped at Hemery's crown by design (growth.py:2196-2205), so this isn't a test. Hemery's coefficients are VERIFY, taken second-hand (Q36).

### Old forests: 3 plots to 200 years (node_v1_200, 359bea4)

Indicative only: a verdict needs 5 plots.

| Age | Stems/ha, all (past 1.3 m) | Basal area | Top height m (approved) | SI 23 curve m | Light % (diffuse) | First generation alive per ha |
|---|---|---|---|---|---|---|
| 50 | 780 (777) | 23.7 | no tree list | 21.95 | 19.1 | 770-790 |
| 60 | 540 (537) | 25.3 | 23.05 | 23.75 | 19.8 | 520-550 |
| 100 | 637 (330) | 31.2 | 26.39 | 27.50 | 28.5 | 230-280 |
| 150 | 2,117 (1,513) | 23.5 | 27.56 | 29.33 | 42.0 | 90-140 |
| 200 | 1,590 (1,137) | 25.1 | 26.87 | 30.17 | 33.6 | 30-90 |

Before the forest fixes (node_H_plot200), no first-generation tree lived to 150, and top height ran 2.3-2.6 m over the curve.

## 3. Targets

"Kind":
- **By design:** the model is built to match.
- **Tuned against:** values were set to bring it closer.
- **Independent:** nothing was set against it.

| Target | Run | Age 50 | Age 60 | Share inside, 50 / 60 | Verdict | Kind |
|---|---|---|---|---|---|---|
| Light under the canopy, 6.4-19.8 % (median 14.8) | plots | 18.5 | 19.0 | 75 % / 75 % | PASS | Tuned against (shedding thresholds, death lines) |
| | stand trees | 16.2 | 16.4 | 80 % / 80 % | PASS | Tuned against |
| Hagemeier LAI, 3.6-5.4 | plots | 4.54 | 4.36 | 100 % / 100 % | PASS | Tuned against; the same result as light (k) |
| | stand trees | 4.82 | 4.68 | 80 % / 70 % | PASS | Tuned against (spacing_overlap) |
| Baltic LAI, 2.5-4.5 at 6-60 | plots | 4.54 | 4.36 | 40 % / 85 % | **FAIL at 50**, PASS at 60 | Tuned against at 50-60 (wind_speed, death lines); independent at young ages, where it fails: inside only at 15-17 and 55-60 |
| Site-index height, SI 20-26 | plots, top height | 21.35 (18.76-25.12) | 23.14 (20.72-26.73) | | PASS | By design |
| | stand trees | 21.91 | 23.71 | 100 % / 100 % | PASS | By design |
| Crown ratio, dense young stands, 0.30-0.45 at 11-22 | plots | 0.92 at 11, 0.96 at 15, 0.94 at 20, 0.93 at 22 | | 0 % | **FAIL**, far off (worked out by hand) | Independent; profile_power was tuned on crown ratio at 50-60, not this band (Q34) |
| Stand density, 880 at 45 | plots | 953 at 45 | | | INFO | Tuned against (wind_speed, sdi_max, rate_at_max) |
| Open crown width (Hemery) | lone trees | 8.65 | 9.35 | | INFO | By design |
| Crown ratio, managed (Repola; Hynynen at least 0.5) | stand trees | 0.53 | 0.45 | 85 % / 15 % at or over 0.5 | INFO | Tuned against (profile_power) |

How some of these were worked out:
- **Plot top height:** the scorecard doesn't score it, because plot runs keep no per-tree yearly records. I used the scorecard's own `naslund_top_height` on the plots' tree lists (over-bark DBH).
- **Young crown ratio:** the same way. It's the mean over plots of each plot's mean (height − crown base) / height of live trees. No plot and no tree is at 0.45 or under at any of those ages.
- **Not scored,** because scorecard.py computes no value for them: bark thickness, wood density, carbon fraction, turning moment, foliage biomass.
- **Seedling targets** need seedling runs, which weren't part of this check.

## 4. What's still wrong

| Miss | Ours | Real | Why, as far as known |
|---|---|---|---|
| Young forests' crowns reach the ground | crown ratio 0.92-0.96 at 11-22 (20 plots; mean height 3.3-9.8 m) | 0.30-0.45 (Niemistö 1995, unopened; read through targets.yaml) | My reading, not tested: lower limbs and short shoots stay alive in deep shade, and the death lines were lowered to 0.15 to keep light in the band, which works against this. |
| Crown starts too low on young trees | at 13.5 m tall: lowest live branch 0.8 m (0.2-1.8), crown base 1.6 m (0.5-2.9); 0 of 20 in 5-7 m | 5-7 m at 13-15 m tall (Hynynen & Niemistö 2009) | The same. Crown 2 reads it as young limbs extending slowly, so the canopy closes late; there's no measured number for that |
| Leaf cover outside the Baltic band | under 2.5 at 6-14; over 4.5 at 18-54, peak 5.63 at 27 | 2.5-4.5 at 6-60 (its source is in doubt, Q30) | Young crowns hold too much leaf. At 50-60 it's the light trade-off above |
| Light near the top of the real range | 18.5 / 19.0 % | median 14.8 % | Linked to the line above through k. The forest fixes moved it up by 0.8 points at 50 |
| Leaves too big | 15.0 cm² per leaf, fixed (growth.py:3116, 0.0015 m²) | 11.9 ± 5.7 cm² (Konôpka & Pajtík 2026, trees aged 4-20) | Leaves per node: smaller leaves at the same count gave 7-9 cm thicker stems. The look mesh draws its own spread around a mean |
| Leaf density near the top | 0.19 / 0.22 | their fit's 1.97 | Untouched |
| Double tops | 0 of 20 (strict) | 35 % (Zeltins, unopened) | Only an axis's end bud starts long shoots |
| Lone trees' longest hanging strands | longest 5.2 / 6.1 m; p90 at 60 4.1 m (3.9-4.3) | about 2-4 m in photos, judged by eye | p90 is at the top of the photo range |
| Old trees die of carbon shortfall after 120 | crowns lost from below | no source gives a rate | Per-internode upkeep is untested at those ages |
| Foliage in stands | single strands | clumped sprays | Option J (d278fd4) gave sprays (Q37) |

Unclear rather than missed: stand branch wood is 29 % over Repola at 50 and 23 % at 60. That's inside 2 times Repola's ×/÷ 1.19 scatter for a 20-tree mean. But Repola includes bark and the model is wood only, so like for like the gap is somewhat larger.

## 5. Guessed values that matter most

These are TUNED, DERIVED or VERIFY. The full list is in `reference/betula_pendula/labels.yaml`.

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
| mortality.vigour.relative_size_slope | 3.263 | DERIVED: Maleki & Kiviste 2016 Table 3, used as an odds factor |

## 6. How this departs from a real tree

- Stand trees' neighbours are copies of themselves.
- Every leaf is 15 cm², and leaves come per node: two and a half per short shoot.
- Only an axis's end bud starts long shoots.
- Limb curve comes from a set-point that moves with wood age, not from mechanics.
- Open trees have a leaf cap and put all spare carbon on the stem.
- Height follows a curve by design.
- Browsing is a setting of place, off in the main tree.
- Cuts, wounds, hanging dead branches and stump sprouts aren't modelled yet. They're next for the game (`reports/cpp_port_plan.md`).

## 7. How this was checked

- **Same trees across commits:**
  - Stand trees at 359bea4 (node_v1_trees) are identical to Crown 2's at e10c6a4 (node_c2Hf20s): 1,220 seed-years.
  - The young plots at 8c2c496 match node_v1_plots at 359bea4 in all 440 plot-years to 22.
  - Open trees match between 359bea4 and a0f4880.
- **Defaults switch (golden proof):**
  - The four golden runs were recorded with the final settings set by hand on 8c2c496 (node_gold_v1pre), and as defaults on d5f0ea3 (node_gold_v1post).
  - All 225 output files are identical.
  - The hashes are in `Cambium-int/out/bench/golden/node_gold_v1pre` and `node_gold_v1post`.
- **Speed settings:** all six together give identical trees (2 seeds, stand trees to 30).
- **Tests:**
  - 391 tests at 513e81c and 4e503cb, with only the 4 known environment failures (no .git or .python-version on the server copy). They need a real clone.
  - **On the new defaults (d5f0ea3), 28 fail: the 4 known ones and 24 from the switch.** Most assume the switches are off. Some may be real faults: the game export's KeyError 'lod0', export then render, root pipes, a speed-state check, and four forest tests. They're being fixed. This version isn't final until they pass.
- **Checker (a)** re-read about 200 numbers against their pages. About 45 couldn't be opened (Q36).

## 8. Tried and dropped

- **J, two end buds per shoot (d278fd4).** Paired against the final crown on 10 seeds:
  - young LAI higher (+0.58 at 20, +0.85 at 22: worse);
  - crown ratio lower by 0.07 at 30 and 0.02 at 50-60 (towards the young-forest target);
  - light differences within noise.
  - Its stand sprays look more like photos.
  - It was dropped on light and young LAI. Light doesn't hold up as a reason, so the choice is closer than first said (Q37).
- af_zero 3.2.
- twigs_age.
- end_buds_per_m.
- Surplus to the stem with neighbours.
- The Evo frame for stand trees.
- Line 0.19 and branch_aging_years 12.

## 9. For the maintainer

Open questions Q30-Q37 in QUESTIONS.md, about:
- target sources;
- the crowding limit;
- which checks are real tests;
- papers to open in Chrome;
- whether J deserves another look.

Renders:
- the 60-year forest: `.claude/worktrees/agent-a44ce00ffda54f4a6/out/bench/ensemble/node_c2fL_g/group.png`;
- the lone tree at 30 and 60: `node_c2FL_o/look_s5.png`.
