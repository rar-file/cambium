Model: claude-opus-5-5 (Opus 5.5)

# Crown and light: what sets a crown's size, and why stand trees keep low limbs

Design for one track of the 2026-11-11 science review. Read only: no model runs, no tests, no commits; code and saved runs read with small Python reads. CONFIRMED = seen in code or data. SUSPECTED = inferred, not checked.

Runs read:
- Plots: `node_cd2_C` + `node_cd2_C2` (20 plots, fix C, tree lists 11-60), and `node_cd2_base*` (same seeds before fix C).
- The fresh run `node_f5_plots` gives the same numbers as `node_cd2_C` at 20-60 (CONFIRMED: LAI, stems, top height and dominants' readings are identical).
- Stand trees: `node_f5_trees` (20 seeds, yearly stats).
- No open-grown run was in the folders I was given, so every open-tree claim below is SUSPECTED.

Scripts (scratchpad, read only): `crown_stand.py`, `crown_plots.py`, `crown_pair.py`, `crown_cap.py` in
`<scratchpad>\`.

## Summary

1. **Plots: crown width is set by stem count, not by light.** Every plot tree's limbs stop at 1.15 x half the plot's *mean* spacing (`growth.py:2287-2292`, `plot.py:401`). At 45-60, 58-100 % of trees in every height quartile have crowns at 0.9 of that cap or more. The shortest quartile's crowns are about as wide as the tallest's (0.90-0.92 of the cap against 0.99-1.03). Equal crowns give equal leaf area and so equal stems. That is SUSPECTED to be part of why the forest is too even.
2. **Stand trees: crown width is set by Hemery's formula.** The crown width is 0.81-0.98 of Hemery's open-grown width at every age from 11 to 60. Young stand trees turn down 30-47 % of the carbon they could fix at ages 8-15, because 84-98 % of their twig shoots sit at a cap.
3. **The 0.89 m lowest live branch is mostly a timing artefact, plus a real fault.**
   - The single stand tree's canopy closes late, at 10.6 m (age 20). One year later its schedule thins it at 11 m (1,800 to 1,000 stems/ha), which reopens it.
   - Hynynen & Niemistö's stands keep 1,600/ha until the first thinning at 13-15 m. So the comparison is not like for like.
   - The real fault: the young crown is held to a formula, so it can't close the canopy sooner.
4. **The plots' "pass" on 5-7 m flatters them.** On the dominants, at the year top height is 13.4 m (age 25), the lowest live branch is 2.64 m. At 15.7 m (age 30) it is 5.10 m. At 14 m that is about 3.3 m by interpolation, which is a likely miss. The 5.28 m reported was every 13-15 m stem at age 30, mostly suppressed trees under a 15.7 m canopy.
5. **Young leaf area overshoot.** Once a young plot closes (age 18 on), its LAI goes to 5.1-5.7. That is where Beer's law with k 0.37 puts the leaf-death line of 0.15 light: -ln(0.15)/0.37 = 5.13.
   - The 0.15 is TUNED. Its source value, the light at which birch's lowest shade leaves sit, is 0.21 (Hagemeier & Leuschner 2019b), which gives 4.22.
   - Varik's densest stand (3,208/ha, 17 m) carries 4.4, leaving 19.6 % light at its base.
6. **Proposed changes:**
   - (P1) limbs stop at their *own* neighbours, and only at neighbours tall enough to meet them;
   - (P2) a stand-tree arm on Hynynen & Niemistö's own schedule, so 5-7 m is tested under its conditions;
   - (P3) an arm that returns the leaf-death line to its source, 0.21, judged against light at 50/60;
   - (P4) the crown leaf-area cap measured on the crown the tree is allowed, or its label corrected.
   - Hemery stays as the ceiling, honestly labelled.

## 1. Every rule that sets limb reach and crown leaf

Rows are in the order the code applies them.
- "Binds" is read from the saved runs.
- cw = crown width. hem = Hemery's width at the tree's stem. cap = 1.15 x mean spacing.
- Dominants are the 10 tallest trees per 1,000 m² plot.

| # | Rule | file:line | What it does | Kind | Binds in practice? |
|---|---|---|---|---|---|
| 1 | Hemery reach (`crown_a` 0.932, `crown_b` 0.177) | growth.py:2240-2249; yaml:1763-1764 | Crown radius = ½(0.932 + 0.177 x DBH over bark) | Sourced: Hemery 2005 Table 1, but the paper is not opened, so UNVERIFIED | **Stand trees: yes**, cw/hem 0.81 at 11, 0.98 at 20, 0.98 / 0.98 at 50 / 60. **Plots: no**, dominants 0.61-0.78. Open trees: by construction (SUSPECTED) |
| 2 | `stem_cm_per_height_m` 2.4 | growth.py:2248; yaml:1769 | The stem that counts in rule 1 is at most 2.4 cm per m of height | TUNED against Dubois' open band (abstract only) | Open trees only (SUSPECTED); stand trees sit far below it (25.5 cm at 21.9 m) |
| 3 | `spacing_overlap` 1.15 x half the **mean** spacing | growth.py:2287-2292; plot.py:394-401; yaml:1775 | Limb reach ≤ 0.575 x sqrt(plot area / all living trees), or the stand schedule's hexagonal spacing | TUNED against stand light and LAI | **Plots: yes, at every age.** At or above 0.9 of the cap: 88-100 % of trees at 15, 77-99 % at 22, 58-99 % at 50, 64-100 % at 60. Dominants cw/cap 0.92-1.03 at 25-60. **Stand trees: only at 50 / 60** (cw 5.77 / 6.35 against 5.83) |
| 4 | Profile: `top_share` 0.165, `peak_depth` 0.65, `base_share` 0.4, `profile_power` 0.8 | growth.py:2293-2299 | Reach by depth in the crown | top_share from Lintunen Fig. 5 (model output); the other three TUNED to the outline | Always: shapes the goal from rules 1 and 3 |
| 5 | `reach_scatter` 0.5, at most 1 | growth.py:2163-2165 | Each limb's own share of the goal | TUNED, to the look | Always (lowers some limbs only) |
| 6 | Limb standing against its 5 neighbours (`limb_rivals`) | growth.py:2251-2280, 2380-2383 | A limb behind its neighbours gets less of the goal | GUESS (`limb_rivals` VERIFY) | Lower limbs; not measured |
| 7 | `chase` 1.0, `limb_shoot_floor_m` 0.5, leader's shoot (÷0.8 in the open) | growth.py:2403-2408; yaml:1802, 1807 | Yearly limb shoot = min(chase x room left, the longer of the leader's shoot and 0.5 m) | TUNED to Konopka 2023 Eq. 4 (fix C) | Young trees: with chase 1, a lit limb reaches its goal in a year or two. The goal binds, not this |
| 8 | Light at the limb tip x water | growth.py:2416-2421 | Shoot x min(light, 1) | Mechanism | **The only light term in reach.** It slows a limb; it can't widen a crown past rules 1 and 3 |
| 9 | Apical room | growth.py:2335-2343 | No limb tip above where the leader was 3 years ago | GUESS | Top of the crown only |
| 10 | Twig reach: limb tip + `twig_shoot_max_m` 0.5 | growth.py:2301-2327; yaml:1810 | Twigs go at most 0.5 m past their limb's tip | TUNED, to the look | **Stand trees at 15-20: 84-98 % of twig shoots at a cap** (`height_limit.use.at_cap`; that count mixes all caps, so which one is SUSPECTED) |
| 11 | `leaf_growth_max` 1.5 | growth.py:1951-1954; yaml:1676 | Side shoots add ≤ 1.5 x the crown's leaf area a year | TUNED against a crash; roughly against Konopka | Not seen to bind: stand trees grow x1.4 a year at 13-15, limit x2.5 |
| 12 | `crown_lai_max` 7, `open_lai_max` 5 | growth.py:1956-1966; yaml:1815-1817 | Leaf area ≤ 7 x π (Hemery reach)² | TUNED, a sink limit | **Plots: no.** Its area is Hemery's open crown, not the crown allowed (row 3), so in plots it allows about 7 x (hem/cw)² ≈ 12-19 per m² of real crown. Stand trees reach 72-83 % of it at 20-25 and 27 % at 15 |
| 13 | `surplus_to_stem` 1.0 | growth.py:2227-2238 | Unused carbon goes on the stem | VERIFY, a choice | Open trees only; 0 in stands and plots |
| 14 | Leaf and limb death line 0.15 (`shedding.light_per_leaf_threshold`, `short_shoot_survival_light`, `short_shoot_light`) | yaml:326, 333, 473 | Spurs and limbs die below 15 % light | TUNED against canopy light. The source says 0.21 (Hagemeier & Leuschner 2019b) | **Sets closed young canopies' LAI** (section 3) and the crown base |
| 15 | Stand cell: `thinning` 1,800 / 1,000 at 11 m / 450 at 16 m; `size_cv` 0.10; `min_distance` 0.6 | growth.py:533-646; yaml:1296-1328 | A stand tree's neighbours are scaled copies of itself at that density | Schedule sourced (Skogsstyrelsen 2014); size_cv VERIFY | Sets when a stand tree's canopy closes (section 2) |

All four caps on crown size (rows 1, 3, 10 and 12) are formula or tuned bounds. Only row 8 is light, and it can only make a limb shorter. That confirms the review's point.

## 2. The single stand tree's 0.89 m

A stand tree sees its neighbours as copies of its own crown (`_stand_cell`, growth.py:571-646).
- Under the default "random" layout there are 15 copies in a periodic square cell, each turned at random and scaled by a fixed size draw (SD 0.10).
- The light grid wraps, so the stand has no edge. Shade doesn't fade sideways or downwards in stands (`stand.shadow_*` 1000 m).
- So the canopy closes exactly when the tree's own crown is as wide as the schedule's spacing, and never earlier.
- Its crown is Hemery's width from its own stem (row 1).

**Stand tree, mean of 20 (node_f5_trees):**

| Age | Height m | Stems/ha | Spacing m | Crown width m | Hemery width m | LAI | Ground light % | Lowest live branch m | Carbon turned down |
|---|---|---|---|---|---|---|---|---|---|
| 11 | 4.41 | 1800 | 2.53 | 1.15 | 1.42 | 0.25 | 95.9 | 0.20 | 34 % |
| 15 | 7.29 | 1800 | 2.53 | 1.78 | 1.95 | 1.01 | 80.6 | 0.20 | 30 % |
| 18 | 9.34 | 1800 | 2.53 | 2.31 | 2.37 | 3.19 | 53.3 | 0.20 | 28 % |
| 20 | 10.61 | 1800 | 2.53 | 2.54 | 2.59 | 4.79 | 31.2 | 0.38 | 23 % |
| 22 | 11.81 | 1000 | 3.40 | 2.73 | 2.83 | 3.10 | 37.6 | 0.78 | 25 % |
| 25 | 13.46 | 1000 | 3.40 | 3.05 | 3.19 | 4.62 | 21.2 | **0.89** | 20 % |
| 28 | 14.94 | 1000 | 3.40 | 3.35 | 3.50 | 5.24 | 15.0 | 2.63 | 15 % |
| 30 | 15.84 | 1000 | 3.40 | 3.53 | 3.73 | 5.61 | 13.6 | 3.97 | 6 % |
| 35 | 17.81 | 450 | 5.07 | 4.29 | 4.43 | 3.93 | 26.6 | 5.48 | 7 % |
| 50 | 21.90 | 450 | 5.07 | 5.77 | 5.90 | 4.73 | 16.6 | 10.33 | 0 % |
| 60 | 23.73 | 450 | 5.07 | 6.35 | 6.49 | 4.60 | 17.1 | 12.64 | 0 % |

(The spacing column is the hexagonal spacing that caps reach. Hemery's width is worked from the saved DBH, wood x 1.1.)

**Same height, stand tree against plot dominants (node_cd2_C, 20 plots, 10 tallest per plot):**

| Height m | Stand tree: age, lowest live branch, crown ratio, light % | Plot dominants: age, lowest live branch, crown ratio, plot light % |
|---|---|---|
| 10.6 | 20, 0.38, 0.95, 31.2 | 20, 0.91, 0.89, 15.9 |
| 13.4 | 25, **0.89**, 0.89, 21.2 | 25, **2.64**, 0.77, 13.4 |
| 15.7-15.8 | 30, 3.97, 0.72, 13.6 | 30, 5.10, 0.65, 16.0 |
| 21.7-21.9 (age 50) | 50, 10.33, 0.52, 16.6 | 50, 10.29, 0.50, 18.2 |
| 23.3-23.7 (age 60) | 60, 12.64, 0.46, 17.1 | 60, 12.58, 0.45, 19.5 |

Reading:
- **CONFIRMED in data: the stand tree's canopy is closed only twice before 35.**
  - First at 18-21: light 53 to 31 %, crown width reaches the 2.53 m spacing at 20. The 11 m thinning reopens it (37.6 % at 22).
  - Then at 25-31, until the 16 m thinning (26.6 % at 35).
  - Its low limbs die only in those windows: 0.38 m to 0.89 m, then 0.89 m to 3.97 m.
- **CONFIRMED: the plot closes at 15-18** (ground light 47 % to 21 %), starting from 13,700 stems/ha. That is why plot dominants of the same height have 1.2-1.8 m more clear stem.
- **So the 0.89 m is mostly an artefact of the test conditions.** Hynynen & Niemistö (2009, waldwissen.net, `reports/birch_knowledge_base.md` C1) give 1,600/ha with *no* thinning until dominant height 13-15 m. The stand tree is thinned at 11 m, 2-4 m earlier, to 1,000/ha.
- **There is also a real fault, which shows at the same height.**
  - The young stand tree's crown is held to Hemery's open-grown width from a 3-5 cm stem. 84-98 % of its twig shoots are at a cap at 15-20, and it turns down 23-34 % of its carbon at 11-22.
  - A crown that may only be as wide as an open tree of the same stem can close a 1,800/ha canopy only when the stem reaches about 8 cm.
- **"Neighbours are copies" adds a third, smaller part.**
  - No neighbour can be bigger than the tree, so it is never overtopped.
  - Its whole stand closes in the same year.
- Plots don't have this problem, but they have the opposite one (row 3): every crown is the same width.
- **The plots' 5-7 m pass needs correcting, on the dominants:**
  - 2.64 m at 13.4 m (age 25) and 5.10 m at 15.7 m (age 30).
  - Before fix C: 0.74 and 2.79.
  - Q40's "plot trees pass the 5-7 m check by height" rests on all 13-15 m stems at age 30 (5.27 m). Most of those are suppressed under a 15.7 m canopy.
  - SUSPECTED miss at 13-15 m on the dominants. It needs tree lists at 25-29 to read exactly.

## 3. Young leaf area: where and why

**Plots (node_cd2_C, 20 plots), by age, against Varik et al. 2009 (Table 1 as read at the publisher, `reports/sources_opened_2026-11-09.md` §3):**

| Age | Top height m | Mean height m | Stems/ha | LAI | Ground light % | Varik at that age |
|---|---|---|---|---|---|---|
| 11 | 4.48 | 3.26 | 13,752 | 1.27 | 87.6 | – |
| 14 (interpolated) | about 6.6 | about 5.1 | about 13,300 | about 3.0 | about 58 | 3.2 (1,350/ha, mean H 11.5 m) |
| 15 | 7.36 | 5.76 | 13,220 | 3.65 | 47.3 | – |
| 20 | 10.63 | 8.73 | 9,324 | **5.12** | 15.9 | – |
| 22 | 11.79 | 9.85 | 7,319 | **5.27** | 14.6 | – |
| 25 | 13.34 | 11.42 | 5,078 | **5.59** | 13.4 | – |
| 28 | 14.67 | – | 3,454 | **5.73** | 14.4 | – |
| 32 (interpolated) | about 16.3 | about 14.6 | about 2,200 | about 5.3 | about 16.4 | 4.4 (3,208/ha, mean H 17.0 m) |
| 45 | 20.48 | 18.93 | 846 | 4.72 | – | 2.5 (941/ha, mean H 25.6 m) |
| 50 | 21.58 | 20.04 | 667 | 4.51 | 18.2 | – |
| 60 | 23.26 | 21.89 | 474 | 4.29 | 19.5 | – |

**By mean height (DECISIONS 105):**
- At 11.5 m the model has 5.59 (age 25), against Varik's 3.2.
- At 17.0 m it has about 4.9 (age about 38), against 4.4.
- At 25.6 m the model never gets there; it is 4.29 at 21.9 m against 2.5.

So the overshoot depends on how it is read:
- By age it is at 20-35.
- By height it is largest at 10-15 m: about +2.4 on Varik's young stand, though that stand had a quarter of the stems.

**Per tree or per stand:**
- Per tree, the dominants' leaf area for height was tuned to Konopka 2023 (fix C, 0.85-0.98 of hers). It is not an independent reading.
- Per stand, the excess comes from closure: after 18 the stand's light sits at 13-16 %.
- The dominants' leaf per m² of their own crown is 6.1 at 22 and 8.1 at 30. That is above crown_lai_max's 7, which doesn't bind in plots (row 12).
- The stand tree reads the same way: LAI 5.61 at 15.8 m, light 13.6 %.

**Which rule:**
- In a closed canopy, leaves and limbs live down to the death line (row 14), so the canopy fills until its base sits near 0.15 light.
- Beer's law with the model's k 0.37 gives LAI -ln(0.15)/0.37 = **5.13**. The young plots read 5.1-5.7. CONFIRMED as arithmetic; SUSPECTED as the whole cause.
- The 15 % overlap of crowns (row 3) helps this along, because every crown claims 1.3 times its ground share.
- With the source's 0.21 line the same sum gives **4.22**.
- Two measurements fit 4.22. Varik's densest stand (4.4 at 3,208/ha) leaves exp(-0.37 x 4.4) = 19.6 % at its base. Hagemeier's own lowest shade leaves sit at 21 %.

**Why mature stands differ:**
- At 50 / 60 the model's ground light is 18.2 / 19.5 %, above the 0.15 line. So old canopies are not at the line: they are limited by gaps and by thin crowns.
- That is why the 0.15 retune lowered old light without old LAI hitting 5.1. Fix C raised young LAI further. My paired read of `node_cd2_C` against `node_cd2_base` gives +0.31, +0.75, +0.48 and +0.66 at 11, 15, 20 and 22 (SE ≤ 0.02), and no change at 50 / 60 (+0.01 ± 0.03, -0.08 ± 0.03).

## 4. Proposal: the smallest set of changes

| # | Change | What it replaces | New values | Open-grown tree |
|---|---|---|---|---|
| P1 | **Limbs stop at their own neighbours.** Each year a plot passes each tree its neighbours (positions with wrap, height, last year's crown radius). A limb heading in direction θ from height z is limited only by neighbours within ±45° of θ whose top is above z. Its reach ≤ 0.5 x `spacing_overlap` x the distance to the nearest such neighbour. A limb above a shorter tree has no space limit; there, light (row 8) and the death line (row 14) decide. Stand trees do the same with their cell's copies (`_stand_map`). | The mean spacing (rows 3 and 15). It also replaces `plot.spacing_min_height_share` and fixes review finding 6 (seedlings shrinking veterans) without a switch | Sector ±45°: GUESS, labelled. 1.15 is unchanged and keeps its TUNED label until re-checked | Unchanged: no neighbours, no limit. Must be bit-identical |
| P2 | **Test 5-7 m under its own conditions.** A stand-tree arm on Hynynen & Niemistö's schedule: 1,600/ha, 700 at 14 m, 375 at 20.5 m. The second thinning comes "about 15 years later", which is about 20.5 m on the SI 23 curve. | Nothing in the model. The Swedish schedule stays the default | Schedule DERIVED from a web guide, labelled | – |
| P3 | **Arm: the death line back to its source**, 0.21 for all three tied values (row 14) | The TUNED 0.15 | 0.21 = Hagemeier & Leuschner 2019b (sourced) | Affects open trees too: check them |
| P4 | **The leaf cap on the crown the tree is allowed.** `crown_lai_max` uses π x (reach after P1)², not Hemery's open crown (growth.py:1963). If not adopted, correct its label: in stands it is "per m² of an open tree's crown", which it doesn't say now. | The area row 12 uses | none | Unchanged (no neighbours) |
| – | **Hemery stays as the ceiling everywhere.** It is honest as a ceiling: no crown in a stand is wider than an open-grown birch with the same stem. | – | – | Open width = Hemery by construction. Its row is "by design", not a check. Open trees' independent checks are Evo and Tallo (the species file keeps them out of the rules) |

Notes:
- P1 is the one change that makes extent follow space and light.
  - In a plot, a dominant can spread over smaller neighbours and a suppressed tree is hemmed in.
  - So crown width, leaf area and then stem diverge from light and position, not from a draw. SUSPECTED to widen the diameter spread (0.14 against 0.32 at 45). The height spread stays tied to the vigour draw, which is another track.
- P1 doesn't help young stand trees: their copies are never closer than Hemery's width.
  - Their remaining fault is that a 3-5 cm stem holds the young crown.
  - Lifting Hemery below its data range would be an arm E. But Hemery 2005's DBH range is unknown (paper not opened), so E waits until Table 1 is read at the publisher. If it's paywalled, it stays UNVERIFIED and E isn't run.
- P3 is a return to source, not a retune.
  - Its risk is light at 50 / 60. The line was 0.18 and then 0.21 before it was tuned down to 0.15 against canopy light (yaml:1705, 1715, 472). The files I read keep no figure at 50 / 60 for 0.21 under today's rules, so the risk is SUSPECTED and unmeasured.
  - P1 should close mature gaps (gap fraction 3-4 % at 50-60), so P3 is tested only on top of P1.
  - Decision fixed now: if P1+P3 puts light at 50 or 60 over 19.8 %, the line stays 0.15. The young-LAI overshoot is then recorded as a known miss caused by that tuned value. No new value is tuned to hide it.
- Not proposed:
  - a new cap on young LAI. That would be tuning a cap to a target.
  - changing `light.penumbra_diffusion`. SUSPECTED to smooth the canopy; it is outside this track.

## 5. What is sourced, tuned and independent

| Value or check | Status |
|---|---|
| Hemery 0.932 + 0.177 DBH | Sourced, paper not opened (UNVERIFIED). A ceiling everywhere; by design for open trees |
| Limb count 5.2 per 10 % of crown | Sourced (Lintunen 2013 Table 3) |
| Death line 0.21 | Sourced (Hagemeier & Leuschner 2019b). P3 returns to it; 0.15 is TUNED against canopy light |
| k 0.37 | Sourced (same paper, Table 5). Light and LAI are therefore one test, not two |
| `spacing_overlap` 1.15 | TUNED against stand light and LAI. Keeps its value; re-checked under P1 |
| `chase` 1.0, `limb_shoot_floor_m` 0.5 | TUNED against Konopka 2023 Eq. 4. Young per-tree leaf area is "tuned against" |
| Sector ±45° (P1) | GUESS, labelled. A sensitivity arm at ±30° and ±60° |
| H&N schedule (P2) | DERIVED from a web guide, test conditions only |
| **Independent tests here:** lowest live branch 5-7 m on dominants at 13-15 m (Q40; web guide); Varik LAI by height; diameter and height spread (Hagemeier Table 3); branch wood against Repola; Evo / Tallo open crown width | None of these is tuned against in this design. If an arm is chosen by one of them, that one becomes "tuned against" |

## 6. Test plan for the server

Code: one branch per change (P1, P3 as a `--set`, P4), from master. P1 behind `crown_frame.space: local`, off by default, so A0 is bit-identical to master.

| Arm | Plots (20 x 1,000 m², seeds 1-20, to 60) | Stand trees (seeds 1-20, to 60) | Open trees (seeds 1-10, to 60) |
|---|---|---|---|
| A0 | master | master (Swedish schedule) | master |
| A1 | P1 | P1 | P1 (must be bit-identical to A0) |
| A2 | P1 + P3 | P1 + P3 | P3 |
| A3 | P1 + P4 | P1 + P4 | – |
| A1s | P1 at sectors ±30° and ±60°, seeds 1-10 | – | – |
| S1 | – | H&N schedule (P2), master rules | – |
| S2 | – | H&N schedule + P1 (+P3 if A2 passes) | – |

Pairing and saving:
- Every arm pairs seed for seed with A0. A difference counts only if its mean is over 2 SE of the paired differences.
- Plots: `--tree-lists 11,15,20,22,25,26,27,28,29,30,35,40,45,50,60`, plus `mortality`, `natural_start` and `stand_measures` as in v1.
- Stand trees keep yearly stats.

Height classes, read at every list age:
- the dominants: 100 tallest per ha;
- 0-5, 5-10, 10-13, 13-15, 15-20 and over 20 m;
- the year the dominants first reach 13 m and 15 m.

Read at 11, 15, 20, 22, 30, 50 and 60, and at the 13-15 m year:

| Measure | How | Must hold (A1-A3 against A0) |
|---|---|---|
| Ground light, diffuse % | plot.json | ≤ 19.8 at 50 **and** 60, every arm mean (A0: 18.2 / 19.5) |
| LAI | plot.json | Hagemeier 3.6-5.4 at 50 / 60; Baltic band reported as now (A0: 4.51 FAIL by 0.01, 4.29). No arm may make 50 worse by over 2 SE |
| Top height (Naslund, 100 thickest) | scorecard way | Inside SI 20-26 at 30 / 50 / 60; curve held the leader in all seed-years |
| Lowest live branch and crown ratio, dominants at 13-15 m | tree lists 25-29; stand-tree stats | Reported against 5-7 m (Q40). Goal: S1/S2 and A1 move into it |
| Crown width / own local gap and / Hemery, by height quartile | tree lists | Shows what binds. Goal: the quartiles separate (A0: 0.90 against 0.99 of the cap at 50) |
| DBH CV and height SD at 45 | tree lists | Reported against 0.32 and 3 m. Not tuned against |
| Carbon turned down, dominants and stand trees | `carbon_ledger.py` | Reported; expected to fall at 11-22 |
| Branch wood against Repola | `independent_checks.py` | Must not rise above A0's 26-33 % over |
| Stems/ha at 45; basal area at 50 / 60 | plot.json | INFO; report the change |
| Open trees: height, crown width, DBH at 50 / 60 | stats | A1 bit-identical. Under A2, crown width within 2 SE of A0 or explained; reported against Evo / Tallo |

Decision rule (written now):
- Adopt P1 if light and LAI hold at 50 / 60, height stays on the curve, and open trees are bit-identical.
- Then adopt P3 only if A2 also holds light at 50 and 60.
- Adopt P4 only if it lowers young LAI without breaking LAI ≥ 3.6 at 60. Otherwise fix its label only.
- P2 is a test condition. It is reported, not adopted. Cost: about 3 plot, 4 stand-tree and 3 open ensembles to 60, server only.

## Open points for the maintainer

1. Q40's note "plot trees pass 5-7 m" should read "all 13-15 m stems pass at age 30; dominants at 13-15 m likely miss (2.6 m at 13.4 m)". I flag it and haven't edited it, since this phase is read only.
2. Q30's proposed tightening (Varik ages 14-45, top 4.4) bears on P3's verdict at 50 / 60. Nothing is loosened here.
