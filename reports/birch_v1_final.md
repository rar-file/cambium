# Silver birch v1: final report

2026-11-08. Branch `reset-integration`.
- Code: 8c2c496.
- The final settings became the species defaults at d5f0ea3.
- Runs were on the server, at commits 359bea4, a0f4880 and 8c2c496, which grow the same trees (see "How this was checked").

This report is the reset's one full check (PROTOCOL section 10, `reports/reset_brief.md`). Checker (a), sources and targets, has run and its FIX items are fixed (`reports/reviews/2026-11-08_final_check_a_sources.md`). Checkers (b), numbers, and (c), rules, see this report.

## In short

- **Ages 50 and 60:** a forest-grown birch and a natural birch forest meet every scored target, except one. The Baltic leaf-cover band fails at 50 by 0.04, and that band's source is in doubt (Q30). Light under the forest is near the top of the real range.
- **Young forests (11-22 years) fail clearly.** Crowns reach almost to the ground: crown ratio 0.92-0.96 against 0.30-0.45. Leaf cover is over the Baltic band from 20 to 50.
- **Matches by design, not tests:** height follows the published site-index curves, and the lone tree's crown can't grow wider than Hemery's measured widths.
- **The biggest real misses:** young crowns start far too low, young forests carry too many leaves, and leaves are too big.
- **Old forests** keep their first generation past 150 years, as real ones do. Their old trees then lose their crowns to an unsourced carbon rule.

## 1. What's in the model

| Part | What it does | Status |
|---|---|---|
| Height | The leader grows up to the Eriksson 1997 site-index curve (SI 23), less when short of light, water or carbon | By design (height_driver) |
| Crown | Limbs earn their reach and place in the crown (crown_frame, earned); twigs, short shoots and leaves follow bud rules | Rules mostly VERIFY or TUNED, listed in section 5 |
| Stem | Pipe-model sapwood, heartwood by own foliage, wind-load stem theory | Mixed |
| Roots | Roots that cost carbon (roots.paid), lateral set-points | Mixed |
| Damage | Old age (Elfving 2010), wind (Kitenberga 2021), snow | Sourced shapes; some readings DERIVED |
| Forest | Self-thinning (Lee 2025 slope, sdi_max 763 TUNED), vigour and size mortality, seed rain and regeneration | Mixed |
| Look | Bark colour by age, black base by tree (Jones), leaves on shoots, limb atlas | Look block: 9 sourced, 15 DERIVED, 181 TUNED |

The species file's value counts (`tools/species_report.py` at d5f0ea3): 417 model values. 90 sourced (55 checked against the page), 20 DERIVED, 80 TUNED, 227 unchecked (VERIFY). 12 of these have a label older than their value; they're being relabelled. Switches and choices aren't counted.

## 2. Results at ages 50 and 60

### Forest-grown trees: 20 seeds (node_v1_treesR, full settings)

| Age | Height m | Stem cm over bark | LAI | Light % | Stem kg (Repola) | Branch kg (Repola) | Crown width m |
|---|---|---|---|---|---|---|---|
| 50 | 21.91 | 26.9 | 4.82 | 16.2 | 229 (237) | 60.0 (46.4) | 5.25 |
| 60 | 23.71 | 30.4 | 4.68 | 16.4 | 335 (316) | 78.2 (63.8) | 5.77 |

The same trees without roots and damage (node_v1_trees) differ by noise only: LAI 4.77 / 4.60, light 16.4 / 17.1.

### Natural forests: 20 plots of 1,000 m² (node_v1_plots, 359bea4)

| Age | Stems/ha | Basal area m²/ha | Dg cm | Top height m (approved definition) | LAI | Light % |
|---|---|---|---|---|---|---|
| 50 | 751 (640-810) | 23.9 | 20.1 | 21.35 | 4.54 | 18.5 (17.1-21.6) |
| 60 | 520 (470-570) | 25.7 | 25.1 | 23.14 | 4.36 | 19.0 (17.3-20.9) |

Real stands, which are not targets unless named in targets.yaml:
- Hagemeier & Leuschner: 880 stems/ha at 45 (DBH 19 cm, 25.2 m²/ha). These plots reach Dg 19.1 at 48, with 803 stems and 23.6 m²/ha.

### Lone trees: 8 seeds (node_v1_openR)

| Age | Height m | Stem cm over bark | Crown width m | Hemery's formula at that stem |
|---|---|---|---|---|
| 50 | 17.77 | 44.5 | 8.65 | 8.81 |
| 60 | 19.24 | 49.4 | 9.35 | 9.68 |

Width is capped at Hemery's crown by design, so this is not a test.

### Old forests: 3 plots to 200 years (node_v1_200)

| Age | Stems/ha | Basal area | Top height m | Light % | First generation alive per ha |
|---|---|---|---|---|---|
| 50 | 777 | 23.7 | 21.3 | 19.0 | all |
| 60 | 537 | 25.3 | 23.2 | 19.6 | all |
| 100 | 330 | 31.2 | 26.9 | 28.3 | 230-280 |
| 150 | 1,513 | 23.5 | 27.9 | 41.8 | 90-140 |
| 200 | 1,137 | 25.1 | 26.9 | 33.5 | 30-90 |

Before the forest fixes (node_H_plot200), no first-generation tree lived past 150, and top height ran 3 m over the curve.

## 3. Targets

| Target | What | Age 50 | Age 60 | Verdict | Kind |
|---|---|---|---|---|---|
| Light under the canopy, 6.4-19.8 % (median 14.8) | plots | 18.5 | 19.0 | PASS | Tuned against, through the shedding thresholds |
| | stand trees | 16.2 | 16.4 | PASS | Tuned against |
| Hagemeier LAI, 3.6-5.4 | plots | 4.54 | 4.36 | PASS | Tuned against, with light |
| | stand trees | 4.82 | 4.68 | PASS | |
| Baltic LAI, 2.5-4.5 at 6-60 | plots | 4.54 | 4.36 | **FAIL at 50**, PASS at 60. At other ages: 0.96 at 11 (under), 2.9 at 15, 4.6 at 20-22, 5.5 at 30, 4.8 at 40 (over) | Independent; its source is in doubt (Q30) |
| Site-index height, SI 20-26 band | plots, top height | 21.35 (18.76-25.12) | 23.14 (20.72-26.73) | PASS | By design |
| | stand trees | 21.91 | 23.71 | PASS | By design |
| Crown ratio, dense young stands, 0.30-0.45 at 11-22 | plots, mean of all live trees | 0.92 at 11, 0.96 at 15, 0.94 at 20, 0.93 at 22 | | **FAIL**, far off | Independent |
| Open crown width (Hemery) | lone trees | 8.65 | 9.35 | INFO | By design |
| Crown ratio, managed (Repola; Hynynen at least 0.5) | stand trees | 0.51 | 0.45 | INFO | |

Not scored, because scorecard.py computes no value for them: bark thickness, wood density, carbon fraction, turning moment, foliage biomass. Seedling targets need seedling runs, which weren't part of this check.

Plot top height isn't scored by the scorecard itself, because plot runs don't keep per-tree yearly records. I worked it out with the scorecard's own `naslund_top_height` on the plots' tree lists (over-bark DBH).

## 4. What's still wrong

| Miss | Ours | Real | Why, as far as known |
|---|---|---|---|
| Crown starts too low on young trees | base 1.2 m at about 14 m tall | 5-7 m (Hynynen & Niemistö 2009) | Young limbs extend slowly under the crown frame's rules, so the canopy closes about 10 years late |
| Young forest crown ratio | 0.92-0.96 at 11-22 (node_v1_young, 20 plots; mean height 3.3-9.8 m) | 0.30-0.45 at 11-22 (Niemistö 1995) | The same cause. Our trees are also shorter at those ages than Niemistö's fertile stands |
| Young forests carry too many leaves | LAI 4.6-5.5 at 20-40 | Varik 2.5-4.4 (abstract only) | The same; leaf rules VERIFY |
| Baltic LAI at 50 | 4.54 | 4.5 at most | Narrow. With the height fix, LAI at 50 rose from 4.44 to 4.54 |
| Light near the top of the real range | 18.5 / 19.0 % | median 14.8 % | Crowns a little thin |
| Leaves too big | about 17 cm² | 11.9 ± 5.7 cm² (Konôpka & Pajtík 2026) | Blocked by leaves-per-node: smaller leaves made stems 7-9 cm thicker |
| Leaf density near the top | 0.19-0.22 | their fit's 1.97 | Untouched |
| Double tops | 0 of 20 (strict), 4-6 of 20 (loose) | 35 % (Zeltins) | Only an axis's end bud starts long shoots |
| Stand branch wood | 29-32 % over Repola at 50, 23 % at 60 | Repola's scatter ×/÷ 1.19 (20-tree mean) | Unknown |
| Lone trees' longest hanging strands | 5.3-6.6 m | about 2-4 m in photos | Mean and p90 are inside the photo range |
| Old trees die of carbon shortfall after 120 | crowns lost from below | no source gives a rate | Per-internode upkeep untested at those ages |
| Foliage in stands | single strands | clumped sprays | Option J (d278fd4) gave sprays but missed on light and young LAI |

## 5. Guessed values that matter most

These are TUNED or VERIFY, with what they were set against. The full list is in `reference/betula_pendula/labels.yaml`.

| Value | Set to | Against |
|---|---|---|
| shedding.light_per_leaf_threshold, short-shoot light | 0.15 | light under the canopy |
| crown_frame.profile_power | 0.8 | crown ratio in plots, between measured ends of 0.6 and 1.0 |
| crown_frame.limb_sag_deg | 45 | the look |
| crown_frame.reach_scatter | 0.5 | the fishbone look |
| crown_frame.open_lai_max | 5 | the look (sky between curtains), open trees only |
| crown_frame.stem_cm_per_height_m, surplus_to_stem | 2.4, 1.0 | the open DBH band, which is abstract-only and not a target |
| height_driver.open_grown_share | 0.8 | a guess |
| mortality sdi_max, rate_at_max | 763, 0.247 | Aosaar and Martinik stands (Q33) |
| regeneration far_share | 0.003 | spread distance |

## 6. How this departs from a real tree

- Stand trees' neighbours are copies of themselves.
- Leaves come per node: two and a half per short shoot, at a fixed size.
- Only an axis's end bud starts long shoots.
- Limb curve comes from a set-point that moves with wood age, not from mechanics.
- Open trees have a leaf cap and put all spare carbon on the stem.
- Height follows a curve by design.
- Browsing is a setting of place, off in the main tree.
- Cuts, wounds, hanging dead branches and stump sprouts are not modelled yet. They're the next step for the game (`reports/cpp_port_plan.md`).

## 7. How this was checked

- **Tests:** 391 tests on the server at 513e81c and 4e503cb. Only the 4 known environment failures (no .git, no .python-version on the server copy). They need a real clone.
- **Speed settings:** all six give identical trees (seeds 1 and 8 to 30).
- **Defaults switch:** golden runs with the final settings set by hand on 8c2c496 (node_gold_v1pre) against the new defaults at d5f0ea3 (node_gold_v1post). PENDING.
- **Merges after the plots ran:**
  - Labels and comments only.
  - tree_table's saved mode for open runs.
  - The mortality block's old-age formula, which isn't used while damage's old age is on, as it is here (a test shows it).
  - Stand trees at 359bea4 (node_v1_trees) are identical to Crown 2's at e10c6a4 (node_c2Hf20s).
- **Checker (a)** re-read about 200 numbers against their pages and found them right. It couldn't open about 45 (MDPI, T&F and Elsevier blocked; Q36).

## 8. Tried and dropped

- J, two end buds per shoot (d278fd4): sprays closer to real, but light, young LAI and crown ratio worse.
- af_zero 3.2.
- twigs_age.
- end_buds_per_m.
- Surplus to the stem with neighbours.
- The Evo frame for stand trees.
- Line 0.19 and branch_aging_years 12.

All are logged in commits.

## 9. For the maintainer

Open questions Q30-Q36 in QUESTIONS.md, about target sources, the crowding limit, which checks are real tests, and papers to open in Chrome. None blocks this version.

Renders:
- the 60-year forest: `.claude/worktrees/agent-a44ce00ffda54f4a6/out/bench/ensemble/node_c2fL_g/group.png`
- the lone tree at 30 and 60: `node_c2FL_o/look_s5.png`
