Model: claude-fable-5-2 (Fable 5.2)

# Challenge to the crown and light design, 2026-11-11

Challenges `reports/design/2026-11-11_crown_light.md`. Read only: no model runs, no tests, no commits.
- CONFIRMED = I saw it in code or in the saved runs. SUSPECTED = worked out, not run.
- Scripts: `<scratchpad>\challenge_crown\chk1.py` to `chk6.py` in that folder.
- I opened no paper; for sources I rely on `reports/sources_opened_2026-11-09.md` and `reports/birch_knowledge_base.md`. I did not look at Lintunen 2013, Konopka 2023, Repola or Skogsstyrelsen 2014.
- Every forecast below is geometry or arithmetic on saved runs, not a model run.

## Verdict: sound with changes

1. The diagnosis mostly holds: crown width follows caps and formulas, not light. Most of its numbers reproduce.
2. The main fix, P1, does not do what the design says. On the saved forests its height test frees no limb where the crown is wide, and Hemery's formula takes over in its place.
3. P1 is likely to open the canopy at 50 and 60, not close it. Light at 60 has 0.3 points of room.
4. Two numbers are wrong, and "mostly a test artefact" for the 0.89 m is not supported.
5. P1 should not be coded as written. The changes are at the end.

## What I recomputed

| Claim | Mine | Reads |
|---|---|---|
| Plots: trees at 0.9 of the spacing cap or more, shortest / tallest height quartile, at 45, 50, 60 | 60 / 98, 57 / 99, 62 / 100 % | CONFIRMED |
| Dominants' crown over the cap, 25 to 60 | 0.92-1.03 | CONFIRMED |
| Dominants' lowest live branch at 25 / 30 | 2.63 / 5.11 m | CONFIRMED |
| Plot LAI at 20, 22, 25, 28, then 50 / 60 | 5.12, 5.27, 5.59, 5.73, then 4.51 / 4.29 | CONFIRMED |
| Stand tree: crown over Hemery at 11, 20, 50, 60; carbon turned down at 8 / 15; twigs at a cap at 15 / 20 | 0.81, 0.98, 0.98, 0.98; 47 / 30 %; 98 / 84 % | CONFIRMED |
| 5.13, 4.22 and 19.6 %; code at growth.py:2287-2292, 2240-2249, 1963 and plot.py:401 | the same; as described | CONFIRMED |
| `node_f5_plots` equals `node_cd2_C` | 72 of 72 rows (seeds 1-18; ages 20, 30, 50, 60) | CONFIRMED |
| Plots: dominants' crown over Hemery "0.61-0.78" | 0.65-0.85 (0.81 / 0.85 at 50 / 60) | WRONG, problem 2 |
| "Every crown claims 1.3 times its ground share" | 1.04 in plots, 1.20 for stand trees | WRONG: 1.15² leaves out pi/4 |
| Cap binds in plots "at every age" | At 30, 12-51 % of trees are at 0.9 of it; at 35, 29-73 % | Overstated; crowns still sit at 0.86-0.94 of it |

## Problems

### 1. P1's height test never fires where the crown is wide. CONFIRMED in data

I applied P1's rule to every living tree in the 20 saved plots, in 72 directions, at the height of the longest limbs (0.65 of the way down the crown, `peak_depth`).

| Age | 15 | 22 | 30 | 45 | 50 | 60 |
|---|---|---|---|---|---|---|
| Limb directions the height test frees | 0.00 % | 0.00 % | 0.00 % | 0.00 % | 0.00 % | 0.00 % |
| Directions where Hemery, not a neighbour, is then the limit | 14 % | 21 % | 34 % | 42 % | 43 % | 44 % |
| Crown area allowed, summed, over the ground: today | 1.04 | 1.04 | 1.03 | 1.00 | 0.99 | 0.99 |
| The same under P1 | 1.07 | 1.02 | 0.90 | 0.86 | 0.84 | 0.85 |
| Width P1 allows over today's cap, shortest / tallest quartile | 0.95 / 1.00 | 0.91 / 0.96 | 0.86 / 0.92 | 0.82 / 0.92 | 0.80 / 0.93 | 0.80 / 0.94 |

- Heights differ by about 1 m and the longest limbs sit metres under the top, so every neighbour counts as taller. The test frees limbs only near the top (22-29 % of directions a tenth of the way down), where limbs are a third of full length.
- So P1 is a symmetric rule: two neighbours each get 0.575 of the gap between them. "A dominant can spread over smaller neighbours" does not happen. The crown radius P1 passes to each tree is never used.
- Hemery becomes the limit in 42-44 % of directions at 45-60. That is more formula, not light. The goal "the quartiles separate" is then met by construction: a smaller stem has a smaller Hemery ceiling.
- The crown area allowed falls by about 15 % at 45-60. The design expects P1 to close gaps. SUSPECTED: it opens them, and light at 60 goes over 19.8 %.
- P1 names no published rule, which PROTOCOL section 4 asks of a new mechanism. The sector of 45 degrees is invented.

### 2. Hemery already binds on half the plot trees at 45-60. CONFIRMED

The design's script multiplies the saved DBH by 1.1 ("assumes dbh_cm is wood"). Tree lists save DBH over bark (`tools/tree_list.py:80`), so bark is counted twice.

| Crown width over Hemery, by DBH quartile, smallest to largest | 30 | 45 | 50 | 60 |
|---|---|---|---|---|
| Mean | 0.83, 0.77, 0.74, 0.71 | 0.95, 0.92, 0.87, 0.80 | 0.97, 0.94, 0.89, 0.82 | 1.00, 0.98, 0.92, 0.85 |
| Smallest quartile: trees at 0.9 of Hemery or more | 5 % | 91 % | 96 % | 99 % |

- "Hemery's width does not bind in plots" is wrong for the smaller half at 45-60. The short quartile's "0.90-0.92 of the cap" is Hemery binding, not the spacing.
- P4's "12-19 per m² of real crown" becomes about 10-17.

### 3. Equal crowns do not give equal leaf area. CONFIRMED

| Spread (SD over mean) | 30 | 45 | 50 | 60 |
|---|---|---|---|---|
| Crown width | 0.04 | 0.06 | 0.07 | 0.07 |
| Leaf area | 0.24 | 0.26 | 0.26 | 0.27 |
| DBH | 0.13 | 0.14 | 0.15 | 0.15 |

Leaf area spreads four times as much as crown width. Stems already follow leaf area. To reach the measured 0.32, leaf area's spread would have to about double. SUSPECTED: wider crown spread alone can't do that.

### 4. On stand trees P1 shrinks the young crown. Code CONFIRMED, size SUSPECTED

- The design says a stand tree's copies are "never closer than Hemery's width". The code allows 0.6 of the mean spacing (growth.py:554): 1.42 m at 1,800/ha, against a Hemery width of 1.95 m at 15 and 2.59 m at 20.
- I redrew the placement rule 400 times. These are not the 20 seeds' own layouts.

| Under P1, stand tree | 20 | 30 | 50 | 60 |
|---|---|---|---|---|
| Directions limited below Hemery | 45 % | 55 % | 62 % | 73 % |
| Crown area allowed, over today's | 0.86 | 0.81 | 0.79 | 0.85 |

- A smaller young crown closes later, which makes the 0.89 m worse. The stand trees' two scored passes at 50 / 60 (LAI 4.73 / 4.60, light 16.6 / 17.1) are at risk, and the plan doesn't guard them (problem 8).

### 5. The 0.89 m is not "mostly" a test artefact. Data CONFIRMED, forecast SUSPECTED

- Plots have been closed since 17-18 and hold 5,078 stems/ha at 25, three times Hynynen & Niemisto's 1,600. Their dominants read 2.63 m at 13.4 m, none in 5-7 m.
- The stand tree's low limbs die at about 0.2 m a year at 22-31 % light, and 0.7 m a year under 18 % (ages 25-30). On the Finnish schedule its crown must reach 2.69 m to close, about age 21-22. At those rates I get about 2.5-4.5 m at 13-15 m: still a miss.
- So the schedule is part of the gap, not most of it. The 5-7 m figure is a web guide's rule for planted stands and is not in `targets.yaml` (Q40 is open).

### 6. P3: 0.21 is not a measured death line, and the records already say what it does

- The paper's 21.0 % is the median light where the lowest shade leaves sit (120-150 readings), so half of them sit below it. Its methods define minimum light as the lowest reading, about 18.7 % by eye from Fig. 6. As a death line, 0.21 is DERIVED.
- Only the spur line ever had it as a source. `short_shoot_light` was 0.30 before, and the limb line was "set to" the spur line.
- `shedding.shade_softness` 0.5 (TUNED; growth.py:1537-1549) is missing from the design's rule table. The chance of dying rises from 0 at the line to 1 at half of it. That is why young plots read 5.6-5.7 at 13-14 % light, not 5.13. SUSPECTED: 0.21 gives about 4.7, not 4.22, still over Varik's 4.4.
- The design says no figure exists for 0.21. Three do, under older rules:
  - both lines 0.21 to 0.15 lowered stand-tree light by 2.99 / 2.66 points at 50 / 60 (`reports/milestone_M2.md:396`);
  - a limb-light switch lifted plot light to 21.9 / 20.5 % at 50 / 60 (DECISIONS 99);
  - the limb line at 0.21 alone gave +1.0 point and -0.28 LAI at 22 (`reports/overnight_log.md:611`).
- Gaps are 3.0 / 3.7 % of the ground at 50 / 60. Closing every one would lower light by about 2.5 / 3.1 points at most. So expect A2 to fail light.
- "Varik's stand fits 0.21" is not a light measurement. It is a leaf area from tree sizes times a German stand's k.

### 7. P4 trims the tallest trees and passes its own guard by construction. CONFIRMED in data

| Leaf area per m² of own crown, shortest to tallest height quartile | 30 | 50 | 60 |
|---|---|---|---|
| Median | 5.3, 6.3, 7.1, 8.1 | 3.8, 4.4, 4.9, 5.6 | 3.4, 3.8, 4.3, 5.0 |
| Trees over 7 | 4, 22, 52, 87 % | 0, 0, 0, 7 % | 0, 0, 0, 2 % |

- A cap of 7 cuts the tall trees and leaves the short ones, so the forest gets more even.
- Almost no tree is over 7 at 60, so "LAI at 60 stays at 3.6 or more" can't fail.
- The 7 was tuned on Hemery's crown. On a smaller crown it is a new tuned cap. Adopting it for lowering young LAI makes Varik "tuned against", by the design's own rule.

### 8. Gaps in the test plan

1. Light is read from `plot.json` only. The stand trees' scored LAI and light at 50 / 60 are not must-holds.
2. The Baltic LAI row at 60 (4.29, top 4.5) can flip to a fail without breaking any rule.
3. P1 is adopted if nothing breaks. No untuned row has to move. "Open trees bit-identical" passes by construction: they have no neighbours.
4. No rule says what happens if the 30 or 60 degree arm does better. Picking one by light makes the sector TUNED.
5. P1 "fixes finding 6", but no old forest with regeneration is run. The wind load still uses the mean spacing with seedlings in it (growth.py:1682).
6. Light at 60 has 0.3 points of room, about 2 SE of a 20-plot mean (SD 0.73). The plan doesn't say how a result that close is judged.

### 9. Sources

| Source | State | Problem |
|---|---|---|
| Hemery 2005 Table 1 | Not opened (CAPTCHA) | `labels.yaml` says VERIFY, not sourced. The repo holds two "Hemery" lines, and the author's graph, by eye, puts this one 5-8 % wide. It sets stand-tree width at every age. "Open-grown" is UNVERIFIED |
| Hagemeier & Leuschner 2019b | Opened at mdpi.com | No table or section given for 0.21. Mature German stands of 45 and 67 years, 85 % birch; used here on young stands |
| Varik et al. 2009 Table 1 | Opened at the publisher | LAI from tree sizes, not measured light. Its 14-year stand has 1,350 stems/ha, the model 5,078 at that height |
| Hynynen & Niemisto 2009 | Web guide, read earlier, not re-opened on 2026-11-09 | Planted stands; no table. 375/ha and 20.5 m are DERIVED |
| Hagemeier 2019a Table 3 (0.32, 3 m) | Opened | One stand, 85 % birch; whether the spread covers the other species isn't recorded |

`labels.yaml` has no entry for `spacing_overlap`, `crown_lai_max`, `open_lai_max`, `shade_softness`, `peak_depth`, `base_share`, `profile_power`, `reach_scatter` or `stem_cm_per_height_m`. No fixed rule of the maintainer's is broken.

## Changes required before anyone codes

1. Correct the Hemery ratios in plots (problem 2), the 1.3, and "at every age". Say Hemery binds on the smaller half at 45-60. Label Hemery VERIFY, and add the nine missing labels.
2. Don't code P1 as written. First work any new rule on the saved tree lists, as in problem 1. It goes ahead only if the crown area allowed at 50 and 60 is not below today's and its size test fires where the crown is wide.
3. If dominance is wanted, limit a limb by the neighbour's own crown at that height, using the radius already passed. Name a published rule, or label it invented.
4. Drop the sector, or fix 45 degrees now and report the other two only.
5. Keep P1 off stand trees unless problem 4 is answered. Make the stand trees' scored rows at 50 / 60 must-holds either way.
6. Add must-holds: no approved row goes from pass to fail (Baltic at 60), and one untuned row must move the right way by over 2 SE before P1 is adopted.
7. Call the 0.89 m "part schedule, part real", and write S1's expected result (about 2.5-4.5 m) before the run.
8. P3: label 0.21 DERIVED, add `shade_softness` to the rule table, cite the three records, and state the expected fail. Then the maintainer decides if it is worth the server time.
9. P4: drop it, or show it by height class at 25-35 and label it a new TUNED cap. Don't adopt it on young LAI.
10. Drop "fixes finding 6", or add an old forest with regeneration and say what spacing the wind load uses.
