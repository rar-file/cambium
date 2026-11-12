# Limbs of the open-grown tree: a census

Checked by Fable 5.2 (ID `claude-fable-5-2`): nothing that grows changed and every row of the census table matched its recomputation; the wording corrections it asked for are made in this version (second tops on 2 of 10 trees, both fork readings, what the light log does and does not show, "no net bend" in place of "straight"). "Living reiterated limbs" in the table leaves out the second top, which is itself a reiterated limb (with it: 3.0; 5.0 open and 3.4; 4.95 stand at 50; 60). Thickest limb at 60: 11.5 (SD 1.3) cm open, 8.3 (0.8) cm stand; over the stem at 1.3 m 0.26 (0.03) and 0.29 (0.03).

## In short

1. **The open-grown tree has many limbs, evenly sized, on one dominant stem.** It keeps 72-76 living limbs from 30 to 60 (the stand tree: 65 falling to 45). At 50 and 60 its largest limb holds 7-9 % of the leaf, and 12 limbs share half of it.
2. **Its limbs are not thin by tape.** At 60 the median limb is 5.5 cm at its base, 40 limbs are over 5 cm, and the thickest is 11.5 cm. Against the stem at breast height they look thin: the thickest is 0.26 of the stem's diameter (stand tree: 0.29). Nothing near the stem's size grows low down.
3. **Forks exist inside limbs; at the scale of the tree it depends on the reading.** 87 % of limbs carry an axis at least 0.6 as thick as the limb beside it. The model named 146 fork axes on 43 limbs. At 60 a strict double top stands on 2 of 10 trees (seeds 3 and 10) and the model's own second top on 2 of 10 others (seeds 5 and 8). On the loose reading 9 of 10 trees have a double top at 50 and 60 (10 of 20 in the stand). Which reading counts is the owner's choice.
4. **Open limbs are well lit and die less often than stand limbs.** Their median light is 0.64 of open sky at 60, and none is under 0.3 at 30, 50 or 60 (over all years 45 of 31,208 readings are, in years 15-26 on limbs within 1.8 m of the ground, and one is under the 0.15 line; that limb lived). Of 112 limbs made in 60 years, 40 died (36 %, against 68 % in the stand), a median 26 years old. They died for want of carbon: by then they were nearly bare (0.02 m² of leaf), while still standing in 0.58 light. No death by light is seen; the light in the very year a limb dies is not logged (the log holds living limbs only).
5. **So "fishbone" fits in number and evenness, not in thickness.** "Fewer, thicker, forking" would need three rule changes:
   - fewer limbs started, or losing limbs dying;
   - leaf flowing to winners;
   - forks at the scale of the whole tree.

   No measurement of real open-grown birch limbs was found to set any of them.

2026-11-12. Opus 5.5 (ID `claude-opus-5-5`). Branch `limb-log` from `limbs` (`33ca42f`) with master (`0b49969`) merged; the build is `5c16dab`. CONFIRMED means computed by me from the fetched run files, or read by me in the code. SUSPECTED means an inference or a reading through a search tool's summary. Tables give the mean over seeds and, where shown, the (SD over seeds). Open-grown: 10 seeds. Stand: 20 seeds.

## 1. What was built, and the proof (CONFIRMED)

**The log.** With `shedding.log_limbs` on, `tools/tree_table.py` now writes `limb_light.json` beside `limbs.json`. It has one row a living limb a year: the same limbs, in the same order, as `limbs.json`. Its columns are `year`, `node`, `light`, `kind` and `fork_axes`.
- `light` is the leaf-weighted mean light on the buds of everything on the limb, as the shedding test read it at the start of the year (`ratio` in `treegen/growth.py`; 1 = open sky). It is null for a limb too young for the test.
- `kind` is `limb`, `reiterated` (a limb in `resource.reiteration`'s list) or `second_top` (the one reiterated limb that goes up as a second top).
- `fork_axes` is how many living axes on the limb the model named as its forks (`crown_frame.fork_leaf_area_m2`).

Nothing in `treegen` changed. The light was already kept (`model._limb_log`) whenever the log was on. Kind and forks are read from the model's own records without calling anything that sets them. The code is in `tools/limb_wood.py` (`limb_light_rows`, `LIGHT_COLUMNS`, `LIGHT_WHAT`). `limbs.json` is byte for byte as before. Without the log no new file is written.

**The open-grown run.** It needed no new option. `tools/tree_table.py run --open --set log.rings=true --set shedding.log_limbs=true` grows the tree the way `tools/hang_run.py --open` grows it (same model, `lean=True`, same species and site).

| Check, on the server at `5c16dab` | Result |
|---|---|
| Full tests (`node_lm_tests`) | 669 run: 664 passed, 1 skipped, 4 failed. The 4 are the known server failures (`test_scorecard_runs`, `test_birchs_targets_are_read_through_the_approved_tag`, `test_a_different_version_is_reported`, `test_this_pc_matches_the_lock_file`). The three new tests in `tests/test_limb_light.py` passed |
| Golden check (`tools/golden.py record node_lm_golden --check`) | IDENTICAL on all 10 runs; `cases/golden_server.json` untouched |
| Switch-off rule, stand trees with both logs on (`node_lm_kt3`) against `node_t2_kt`, `--switched shedding.log_limbs` | IDENTICAL for seeds 1-3 (`stats.json`, `tree.json`, and `limbs.json` with the same sha256); then IDENTICAL for all 20 seeds. `limb_light.json`: "only in the second, not compared" |
| Open-grown seeds 1-10 to 60 with both logs on (`node_lm_open`) against the hang track's default open trees (`node_hang_open3`, commit `1dc00bc`): height, stem and leaf area at 20, 50 and 60 | 90 of 90 values equal, exactly; checked on the fetched copy and on the server's copy |
| Run time, one open tree to 60 with both logs on | 131 s alone; 118-126 s with one other running (stand tree: 76-85 s) |

## 2. The census at 30, 50 and 60 (CONFIRMED)

The rows are the design's section 1 (`2026-11-12_limbs.md`). A limb is a side axis on the stem, or on a leader that replaced it. "At the joint" means the stem where the limb leaves it. "Real leaf" means at least 0.05 m². Stand light comes from the 20 stand trees rerun with the new log (`node_lm_kt3`, identical trees to `node_t2_kt`). "Light" is the new column, read the year the census is taken.

| Measure | Open 30 | Open 50 | Open 60 | Stand 30 | Stand 50 | Stand 60 |
|---|---|---|---|---|---|---|
| Height, m; stem at 1.3 m, cm; leaf area, m² | 12.7; 28.3; 134 | 17.6; 39.6; 246 | 19.2; 43.9; 283 | 15.8; 14.4; 56 | 21.9; 25.5; 105 | 23.7; 28.6; 102 |
| Living first-order limbs (SD); with real leaf; per m of crown | 72.9 (1.5); 56.6; 6.5 | 76.4 (2.5); 64.0; 5.2 | 72.0 (4.2); 60.4; 4.6 | 64.7 (3.2); 51.7; 5.7 | 51.1 (2.5); 41.0; 4.5 | 45.4 (3.1); 37.4; 4.2 |
| By height on the stem, share of tree height: under 0.4; 0.4-0.6; 0.6-0.8; over 0.8 | 28; 16; 16; 13 | 23; 17; 19; 17 | 20; 17; 18; 17 | 9; 20; 20; 15 | 0; 7; 21; 23 | 0; 3; 17; 26 |
| Base diameter, cm: median (SD); 90th percentile; thickest | 1.9 (0.2); 4.9; 6.5 | 4.3 (0.3); 8.0; 9.7 | 5.5 (0.4); 9.0; 11.5 | 1.3 (0.1); 3.1; 3.8 | 2.8 (0.3); 5.7; 7.0 | 3.2 (0.6); 6.4; 8.3 |
| Thickest limb over the stem at 1.3 m | 0.23 | 0.25 | 0.26 | 0.26 | 0.27 | 0.29 |
| Limbs over 2 (SD); 5; 7.5; 10 cm | 35.7 (2.2); 7.3; 0; 0 | 54.1 (1.4); 32.2; 11.3; 0.2 | 54.4 (3.4); 40.1; 20.2; 2.4 | 23.1 (2.8); 0; 0; 0 | 29.1 (2.4); 10.9; 0.1; 0 | 27.4 (3.0); 14.1; 1.6; 0.1 |
| Limb over stem at the joint: median (SD); 90th; largest | 0.33 (0.03); 0.52; 0.68 | 0.42 (0.03); 0.67; 0.88 | 0.42 (0.02); 0.75; 1.01 | 0.37 (0.01); 0.52; 0.71 | 0.49 (0.02); 0.69; 0.85 | 0.55 (0.02); 0.76; 0.89 |
| Own-axis length, m: median (SD); 90th; longest | 1.7 (0.1); 3.6; 4.8 | 2.8 (0.2); 5.1; 6.8 | 3.3 (0.2); 5.3; 7.3 | 1.1 (0.2); 2.4; 3.0 | 2.1 (0.3); 4.0; 5.8 | 2.2 (0.2); 4.2; 6.3 |
| Crown width, m | 6.2 | 8.8 | 9.7 | 3.5 | 5.8 | 6.4 |
| Angle from vertical at the stem, low; mid; upper crown, degrees (base to tip in brackets) | 50; 54; 64 (49; 51; 71) | 53; 54; 50 (53; 50; 52) | 54; 53; 48 (55; 53; 49) | 47; 49; 68 (44; 48; 72) | 48; 50; 53 (45; 46; 56) | 49; 50; 50 (46; 47; 52) |
| Limb age, years: median (SD); 90th; oldest | 12 (0); 21; 26 | 25 (1); 38; 45 | 32 (1); 46; 55 | 9 (0); 15; 18 | 15 (1); 25; 29 | 18 (1); 30; 35 |
| Leaf: largest limb's share (SD); the five largest; limbs that hold half | 0.08 (0.01); 0.31; 10.2 | 0.07 (0.02); 0.27; 12.6 | 0.09 (0.03); 0.29; 11.9 | 0.07 (0.01); 0.27; 11.2 | 0.09 (0.03); 0.33; 9.4 | 0.13 (0.04); 0.41; 7.3 |
| The thickest limb: share of leaf; height on the stem over tree height | 0.07; 0.25 | 0.07; 0.38 | 0.08; 0.41 | 0.04; 0.36 | 0.08; 0.58 | 0.11; 0.63 |
| Limbs with an axis at least 0.6 as thick as the limb beside it (share, SD) | 0.58 (0.04) | 0.80 (0.05) | 0.87 (0.03) | 0.40 (0.04) | 0.65 (0.05) | 0.69 (0.08) |
| Limbs carrying a fork axis the model named (SD); named fork axes (new log) | 22.2 (2.3); 43 | 38.1 (3.0); 119 | 42.6 (3.0); 146 | 11.7 (2.7); 12 | 24.6 (2.8); 51 | 23.2 (2.9); 56 |
| Living reiterated limbs (SD); second tops a tree (new log) | 0 (0); 0 | 2.8 (0.4); 0.2 | 4.8 (0.4); 0.2 | 0 (0); 0.05 | 3.2 (0.5); 0.2 | 4.8 (0.7); 0.2 |
| Trees with a double top, strict; loose (`tools/tree_table.py`'s two readings) | 0; 0 of 10 | 1; 9 of 10 | 2; 9 of 10 | 0; 0 of 20 | 1; 10 of 20 | 1; 10 of 20 |
| Branch wood, kg (SD); over Repola's A3 (a stand-tree equation: information only for open trees) | 58 (1); 0.53 | 320 (19); 1.52 | 522 (33); 2.03 | 14 (2); 1.12 | 64 (12); 1.47 | 89 (17); 1.76 |
| Of it: limbs' own axes; axes on them; finer | 0.47; 0.24; 0.29 | 0.51; 0.24; 0.26 | 0.48; 0.25; 0.27 | 0.59; 0.27; 0.14 | 0.68; 0.19; 0.12 | 0.68; 0.19; 0.12 |
| Wood on limbs with a base under 3; 3-5; 5-7.5; 7.5-10; over 10 cm | 0.12; 0.39; 0.49; 0; 0 | 0.01; 0.07; 0.40; 0.49; 0.02 | 0.00; 0.03; 0.23; 0.56; 0.17 | 0.53; 0.47; 0; 0; 0 | 0.04; 0.30; 0.63; 0.03; 0 | 0.03; 0.14; 0.60; 0.21; 0.02 |
| Wood on limbs over 20 years old | 0.05 | 0.95 | 0.98 | 0.00 | 0.66 | 0.86 |
| Light on a limb's leaves: median (SD); 10th; 90th percentile of limbs | 0.60 (0.02); 0.43; 0.91 | 0.63 (0.01); 0.53; 0.84 | 0.64 (0.01); 0.54; 0.79 | 0.54 (0.05); 0.17; 0.90 | 0.42 (0.04); 0.20; 0.86 | 0.41 (0.04); 0.21; 0.82 |
| Leaf-weighted light over all limbs (SD); limbs under 0.3 | 0.55 (0.01); 0 | 0.62 (0.01); 0 | 0.63 (0.00); 0 | 0.40 (0.02); 17.6 | 0.37 (0.03); 15.3 | 0.36 (0.03); 14.4 |
| Light on the thickest limb (SD); over the tree's 90th percentile | 0.49 (0.05); 0.54 | 0.62 (0.05); 0.74 | 0.62 (0.06); 0.78 | 0.19 (0.04); 0.21 | 0.30 (0.10); 0.35 | 0.34 (0.06); 0.42 |
| Light, median: limbs over 5 cm; limbs of 2 cm or less | 0.49; 0.83 | 0.61; 0.78 | 0.63; 0.72 | –; 0.75 | 0.25; 0.77 | 0.26; 0.74 |
| Correlation of light with base diameter among leafy limbs, within a tree (SD) | −0.70 (0.06) | −0.61 (0.09) | −0.51 (0.09) | −0.84 (0.03) | −0.81 (0.04) | −0.80 (0.05) |

**How long a limb lives.** Life is the last year alive minus the birth year, as the challenge counts it.

| Over 60 years, a tree | Open | Stand |
|---|---|---|
| Limbs made; dead by 60 | 111.8 (3.0); 39.8 (3.9) | 142.7 (3.5); 97.3 (3.8) |
| Last alive in years 1-29; 30-49; 50-59 (by year of death: 3.5; 23.6; 11.6 and 1.1 in year 60 open, 25.8; 52.3; 18.0 and 1.4 stand) | 4.0; 24.3; 11.5 | 30.0; 50.2; 17.2 |
| Life of those that died, years: median (SD); 10th-90th; longest | 25.8 (1.3); 15.8-39.7; 48.8 | 18.3 (1.1); 14.2-26.9; 33.2 |
| In its last year: light (SD); own carbon over upkeep; leaf, m²; base, cm; height on the stem over tree height (medians) | 0.58 (0.01); 0.74; 0.02; 1.9; 0.29 | 0.17 (0.01); 0.75; 0.21; 2.4; 0.41 |
| Dying limbs whose own carbon was under their upkeep in their last year | 100 % | 99 % |

- **The stand figures are the design's own,** recomputed with my code from the same files. Means and percentiles match its section 1 and the challenge's section 1 to their rounding, A3 included (1.12 / 1.47 / 1.76).
- **In a stand the thick limbs are the shaded ones.** Light falls as base diameter rises (r about −0.8), and at 60 the thickest limb sits in 0.34 light, 0.42 of the tree's best-lit limbs. The challenge read this on one limb of seed 1; it holds over 20 trees.
- **In the open no limb is shaded enough for the light line** (0.15). Limbs die by the carbon test once their leaf has gone, while their light is still 0.58. What takes the leaf first is not in the log (SUSPECTED: the age clock, `resource.branch_aging_years`, and twig shedding inside the limb).

## 3. Is the open-grown tree a fishbone of many thin straight limbs?

In plain words: **many, yes; evenly sized, yes; on one stem, yes; thin, only beside the stem's base; with no net bend, by the one measure the logs hold.**

- **Many and even (CONFIRMED).** 72-76 living limbs, 4.6-6.5 to a metre of crown, from the base to the top in near-equal numbers (17-20 in each band of height at 60). No limb holds more than about a tenth of the leaf, and the five largest hold 27-31 %. In the stand the share concentrates with age (13 % and 41 % at 60); in the open it does not.
- **Not thin by tape (CONFIRMED).** At 50 and 60 the open tree's median limb is thicker than the stand tree's thickest limb at 30, and at 60 it has 40 limbs over 5 cm. Beside the stem at breast height (44 cm), though, the thickest limb is a quarter of it. That is the look audit's "none near the stem's size", and it is no different from the stand tree (0.26 against 0.29).
- **No net bend in the means of each crown third (CONFIRMED as far as measured).** At 50 and 60 the mean chord from base to tip runs within 4° of the mean angle of the first half metre, at 48-55° from vertical (at 30 the upper third differs by 7°). Per-limb angles are not saved, so bends can cancel across limbs as well as within one: this shows no net bend, not that each limb is straight.
- **One stem (CONFIRMED).** Limbs fork inside themselves (87 % by the 0.6 reading; 146 named fork axes on 43 limbs at 60). Yet at 60 a strict double top stands on 2 of 10 trees (seeds 3 and 10) and the model's second top on 2 of 10 (seeds 5 and 8; 4 of 20 in the stand). They are different trees, so 4 of 10 carry one or the other. On the loose reading 9 of 10 open trees have a double top at 50 and 60 (10 of 20 in the stand).

**What "fewer, thicker, forking" would have to change there** (SUSPECTED: read from the rules the design lists in its section 2, not run):

1. **Fewer.** A limb is started for every stretch of new stem (at 60, about one each 0.22 m by my arithmetic on the design's formula), whatever the room. In the open only 40 of 112 die by 60. So either fewer would be started, which has no source for open birch (Lintunen's 5.2 per tenth of crown is from stands), or limbs that lose to their neighbours would have to die. The light line never acts in the open, since no limb is under 0.3. A limb's share would have to fall against its neighbours': a relative rule like the off-by-default `shedding.limb_relative_light`, or competition in the shoot share.
2. **Thicker few.** Thickness follows leaf times age, and the leaf is shared evenly by four rules:
   - the shared envelope (reach capped at the published crown, which this tree already exceeds by 10 %, per the design);
   - limbs' shoots paid first, at one pace;
   - the age clock;
   - the ring rule.

   A few limbs could pull ahead only if leaf flowed to winners (Nikinmaa 2003's form for Scots pine is the one candidate the design names; no birch value). That must not widen the crown.
3. **Forking at the scale of the tree.** Today the model's own route to a rival stem is reiteration (SUSPECTED as the only route: of 36 open limbs at 60 that are at least 0.7 of the stem at their joint and 3 m or more under the top, 24 are plain limbs and 12 reiterated). That starts after year 30 once the leader slows, at one limb each 5 years and only in the upper crown, and only one limb goes up as a second top, on a drawn 34.9 % of trees. A lost leader is replaced by one shoot. Low rival stems would need reiteration earlier or lower, or two shoots after a lost leader. That is the design's open fork question (its section 7, question 2).

**What this means for part R (SUSPECTED).** Open limbs read 0.63 leaf-weighted light at 60, not near 1. On the rule as written (q on open sky), part R would cut about a third of the replaced ring on open limbs too. That is the challenge's warning, now with a number under it. The desk reading of part R can now be redone on the real column for both kinds of tree. I have not done it.

## 4. Real open-grown birch, and the photos

- **Measured limbs of open-grown birch: none found.** The design found no source for the number or size of limbs on open-grown birch. One more web search today found only stand and competition studies (Lintunen & Kaitaniemi 2010; Mäkinen, Ojansuu & Niemistö 2003), through the search tool's summary (SUSPECTED). What exists for open trees is crown width from stem size (Hemery et al. 2005, as the target file quotes it; not opened). The design's one candidate for open-grown limbs over 5 cm is Van Den Berge et al. 2021: eleven hedgerow birches as cylinder models, CC BY 4.0, with the laser scans' limits. It is not opened. So no row of the census above has a measured open-grown value beside it.
- **What the reference photos can show.** Three photos are classed solitary (Oslo, Meilen, and the young Hallinden tree), each read only inside its boxes (`reference/betula_pendula/hang_photo_frames.json`; I did not open the images). They can show the outline and the main limbs that stand out against the sky. They can also show whether a tree carries two or more rival stems or a low fork. The reiteration interval is already tuned to "4-7 major limbs in the reference photos" (`labels.yaml`).
- **What they cannot show.** They cannot show limb diameters, since neither the distance nor a scale is known. They cannot count thin limbs, which merge or hide behind each other and behind leaf, nor show limb age, life or light. Nor do three trees give a spread. So they can test "how many big limbs, and are there forks at the scale of the tree", but not "how thick" or "how many in all".

## 5. The picture

**Not made.** The repository's leafless drawing (`tools/hang_render.py` `draw`) draws every internode in black, and `tools/tree_table.py` keeps no tree at 60 to draw. `draw` takes the radii as an argument, so drawing the first-order limbs thicker needs no change to it; colouring them does. Either way it would need:
- for colour, a colour argument in `draw`, about three lines;
- a script to grow a tree, mark the limbs' own axes and save the picture, about fifteen lines;
- a render job on the server.

That is more than the few lines allowed. There is a plain leafless picture of this same tree, open seed 1 at 60, in the hang track's run folder: `out/bench/ensemble/node_hang_open3/1/leafless_east_age60.png` and its north view. It is the same tree, since height, stem and leaf area are equal (section 1). It is not in the repository.

## What I checked, and what I didn't

- CONFIRMED: every model figure above, computed with new scripts kept outside the repository from the fetched `limbs.json`, `limb_light.json`, `tree.json` and `stats.json` of `node_lm_open` (10 seeds) and `node_lm_kt3` (20 seeds), and from `node_t2_kt` for the check against the design. The proofs in section 1 were run on the server.
- SUSPECTED: everything in section 3's "would have to change" and "part R" paragraphs; the web search's summary; what takes an open limb's leaf before it dies.
- Not done: the picture (section 5); any change to a growth rule; part R's desk reading on the new column; a measure of bends along a limb; opening any paper or the reference photos.
