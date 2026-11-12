# Two height faults: why a tree stands above its curve, and why thinned neighbours come back

2026-11-12. Model: Opus 5.5 (ID `claude-opus-5-5`). Branch `height-trace` from master `e6c22a8`; its one commit adds `tools/height_trace.py`, which only reads the model while it grows. No growth rule, default or test was changed. Growth ran on the server only; on the PC I only read fetched JSON. CONFIRMED = traced in a run or read in code today. SUSPECTED = inferred, not traced.

**In five lines, for a reader who doesn't code:**
1. When a tree stands above its height curve, the part on top is never the stem. It is almost always a second top or a fork on an upper limb, which grew in below the stem's top and was swung above it the same year by the model's wood mechanics (sagging, then straightening).
2. The curve only limits where a shoot grows to, before the mechanics run; nothing checks the height after them. The leak in the shoot cap that the T2 report suspected is real but small (a sixth of trees, under 0.4 m).
3. On today's defaults it touches forking trees and big forked limbs from age 36 on, and fades within about 10 years as the stem catches up. No source I opened says how often a real birch's side top stands above its leader.
4. A stand tree's neighbours are counted from its height every year, with no memory, so a storm that shortens it brings removed neighbours back. On the defaults: 0 of 20 trees. On the Finnish schedule (arm S1): 1 of 20.
5. Recommended: record the stem's top beside the height everywhere (no growth change); and make a thinning, once reached, stay (a bug fix that leaves every default run identical).

**Built since, by Fable 5.2 (the last section, "The build"):** both parts of line 5, each off by default, on the branch `stem-top`. Nothing is merged or adopted.

## How it was traced (CONFIRMED)

| Run (label) | What | Proof it changed nothing |
|---|---|---|
| `node_ht_kt` | Stand trees seeds 11, 14, 10, defaults, to 60 | height_m equal to the control `node_t2_kt` in every year 1-60, 3 of 3 trees |
| `node_ht_s1` | Stand trees seeds 8, 10, 12, arm S1's schedule, to 60 | equal to `node_t2_s1` in every year, 3 of 3 |
| `node_ht_p1` | Forest plot seed 1, 1,000 m², to 45: the control plot with the most trees over at 45 (20 of 85) | every living tree's height equal to the control plot's tree lists at 30, 35, 40, 42 and 45 (85-279 trees, 0 differ) |

The tool wraps `GrowthModel._finish_year`, `fast.bend_steps` and a stand tree's `_stand_cell`: each copies positions out and calls the original with the same arguments. Each year it records the stem's top (last node of `Tree.trunk_chain`), the leader's limit (`_hd_ref`), the highest living node (its axis, limb, birth year and the height it was born at) and how far that node moved in the year's bending and in the posture correction after it.

## Fault 1. Which part is on top, and how it got there (CONFIRMED)

Stem top minus limit was at most +0.005 m in every traced year: the stem stays on its curve. "Over" = highest point more than 0.05 m above the stem's top.

| Tree | Over at 45; 50; 60, m | Years over (most) | The part on top | Its limb | Born where | The year it went over: bending, then posture |
|---|---|---|---|---|---|---|
| Control seed 11 (forks) | 1.29; 0.26; 0 | 39-40, 42-51 (1.44 m at 43) | the tree's second top: the limb's own axis, order 3 | born year 34 at 16.88 m on the stem, reiterated year 36; base radius 0.95 cm at 6.1 m long (year 42) | year-42 tip grew to 18.84 m, 1.18 m under the stem's top | −2.15 m, then +4.73 m: 1.41 m over |
| Control seed 14 (no fork) | 0; 0; 0.37 | 59-60 (0.37 m at 60) | a fork of a limb (order 4); the limb's highest node moved among 4 fork axes in years 53-59 | born year 30 at 14.98 m, not reiterated | year-59 tip at 22.94 m, 0.66 m under | −1.18, +1.99 (59); −0.49, +0.87 (60) |
| S1 seed 8 (forks) | 1.03; 0; 0 | 42-48 (1.44 m at 43) | second top, order 2 | born 29 at 14.35 m, reiterated 36 | 19.91 m, 0.11 m under | −3.33, +4.83 |
| S1 seed 12 (forks) | 0.73; 0; 0 | 36, 42-47 (0.93 m at 44) | second top, order 5 | born 24 at 12.04 m, reiterated 30 | 18.98 m, 1.03 m under; its shoot set off pointing down (slope −0.41) | −1.65, +3.14 |
| Seed 10, both runs | 0; 0; 0 | never | the stem | – | – | – |

- **Year by year, seed 11's second top:** the limb's highest node fell from 0.40 to 1.23 m under the stem's top over years 34-36. In year 38 its new shoot grew to 15.9 m and the mechanics lifted it to 18.0 m; in 39 to 19.5 m (over); in 42 a new tip grown to 18.8 m was lifted to 21.4 m. After that the tip never grew again (its room under the leader is zero, `growth.py:2369-2375`) but kept rising 0.31, 0.25, 0.12, 0.06 m in years 43-46 by posture, while the stem rose 0.23-0.27 m a year. The excess fell 0.2 m a year until the stem passed it in year 52. This is the report's "stopped lengthening, then rose 0.8 m": the posture correction.
- **Not the cause:** a lost leader (all three traced control trees had lost one by year 11; seed 10 never went over), growth above the cap as the main part (in stand trees every tip on top was born under the stem's top, 6 of 6 episodes; in the plot 34 of 41 trees, below), the snap (seed 10 never went over).

**In a forest plot** (`node_ht_p1`, seed 1, CONFIRMED). From plot year 30 to 45, 41 trees were more than 0.3 m over in 126 tree-years. The part on top: the tree's second top in 124, a twig in 2. All 41 are forking trees and every one sits on a reiterated limb (reiterated at tree age 30-41), born at tree age 23-36, median 6.2 m long on a 2.5 cm base.

| Plot age | Trees | Over by > 0.3 m (most) | Approved top height on highest points; on stem tops; difference, m | Height SD on highest points; on stem tops, m |
|---|---|---|---|---|
| 35 | 177 | 6, 3.4 % (1.50 m) | 17.295; 17.260; +0.035 | 0.988; 0.970 |
| 40 | 116 | 8, 6.9 % (0.97 m) | 18.900; 18.905; −0.005 | 0.990; 1.009 |
| 42 | 101 | 11, 10.9 % (1.46 m) | 19.627; 19.484; +0.143 | 1.089; 1.016 |
| 45 | 85 | 20, 23.5 % (1.84 m) | 20.584; 20.304; +0.280 | 1.122; 1.003 |
| 50, 60 | not run | the T2 report, 20 plots: 6.0 % and 1.8 %; top height +0.05 and +0.01 m; part not traced | – | – |

- **How each tree first went over:** in 34 of 41 the tip on top was born under the stem's top (median 0.41 m under, up to 1.88). In 7 it was born up to 0.38 m over it (up to 0.62 m over the cap's own line, the leader's start-of-year top): a second-top shoot that set off shallow from under the stem's top (first slope −0.07 to 0.38) and curved upward as it grew. The cap assumes a straight shoot, and skips any bud sloping 0.02 or less (2 of the 7) (`growth.py:2375`). In all 41 the same year's mechanics then lifted it: bending median −2.93 m, posture median +4.45 m, net +0.39 to +2.60 m (median +1.28 m against a median excess of 0.76 m). So the cap the T2 report suspected adds a little in a sixth of trees; the mechanics make the excess.
- In the plot trace's `detail`, `year` and `born` are the tree's own age (plot year less germination); its `rows` are by plot year. All runs are at commit `ea78b2b`.
- This plot's +0.280 m at 45 is the T2 report's largest plot (+0.280, rebuilt there from the curve): the two methods agree.

## Fault 1. The mechanism in the code (CONFIRMED read and traced; why its size: SUSPECTED)

1. Growth caps where a shoot ends, on a straight line from its bud: `_height_limit_caps` (`growth.py:2573-2596`) and, for limbs, forks and the second top, `_frame_room` (`2361-2375`, applied at `1844-1850`). A limb tip may end no higher than the leader's start-of-year top less 3 shoot lengths; the second top up to the leader's start-of-year top (`2370-2371`). The trace shows these hold.
2. Then `_finish_year` (`growth.py:1316-1339`) runs `mechanics.bend_and_correct` (`mechanics.py:85-168`): bending under the year's load (`fast.bend_steps`), then posture control towards each node's set-point (`kernels.posture`). The second top's set-point is the reiteration's 12° from vertical (`_frame_setpoints`, `growth.py:2132-2142`); a fork's young wood stands 15° above its limb's own angle (`limb_sag_deg` 45, `growth.py:1329-1335`). The budget is `reaction_wood_coefficient × ring width / r²` (`mechanics.py:148-151`), so a new 1-2 mm shoot can turn all the way to its set-point in one year.
3. Nothing compares any node with the stem's top after step 2, and `measure()` reports the highest living node (`growth.py:3136`). A 6 m axis turned towards 12° from vertical from 16.9 m reaches about 22.8 m, above a 20.0 m stem.
- **Why not before year 36 (CONFIRMED in code, timing in 4 trees):** a tree's second top is the first reiterated limb in its crown's upper half (`_frame_tops`, `2144-2154`); reiteration starts at age 30 at the earliest, once the leader's step falls under half its peak, one limb per 5 years (`_reiterate`, `473-525`; species `resource.reiteration`). The traced trees reiterated first in year 30, 31 or 36. Forks need a limb carrying 1.5 m² of leaf per axis. SUSPECTED, not traced: the lift must also outrun a stem step that is 0.35 m at 36 and 0.25 m at 45.
- **SUSPECTED, flagged:** the swings are large. Seed 11's 6.1 m axis on a 1.9 cm base sagged 2.15 m and was lifted 4.73 m in one year. I opened no source on how fast a birch limb rights itself; a diagnosis of that is a separate question from this note.

## Fault 1. How real (what I know, and what is not sourced)

- Zeltins et al. 2018 (Forests 9:52, read at the publisher today): 40-year-old grafted plus-tree clones at 400/ha recorded "double tops" per tree, with no definition and no height for either top; the species file's 34.9 % comes from its Table 1. CONFIRMED that it gives no frequency of a side top standing above the leader, nor by how much.
- I found no published share of birches at 45 with a side limb 1-2 m above the leader. **Not sourced; no number is offered.** That a forked birch's two tops differ in height is ordinary in the field (SUSPECTED, no source opened). A 6 m limb lifted 2-5 m in one season is, I suspect, not (no source opened).

## Fault 1. What "height" should mean, place by place (my recommendation; the maintainer decides)

| Where | Reads today | Should read | Why |
|---|---|---|---|
| A tree's stats (`height_m`) | highest living point | highest point, plus a stem-top column | Foresters measure to the highest point; the curve sets the stem. Show both |
| Plot top height, approved (`scorecard.naslund_top_height`) | highest points | approved definition on highest points, and printed beside it on stem tops | The "by design" claim (top height follows the curve) holds for stem tops only; the plan's decision-1 row should be read on both |
| Tree lists | highest point | both columns | Lists feed templates and the plan's spread rows |
| A stand tree's thinning schedule | highest point (start of year) | stem top, with fault 2's memory | A transient lift moved S1's last thinning 1-2 years early (fault 2 table); stem tops follow the curve the schedule was meant for |
| Game export | highest point (`tools/game_export.py:89`), and the mesh's bounds | highest point | The game shows the mesh; its bounds must hold every node |

## Fault 1. Fix options

| Option | Kind | What it moves | Cost | How proven |
|---|---|---|---|---|
| A. Cap every shoot tip by absolute height, not only upward buds | rule change | little: 7 of 41 plot trees' tips grew 0.04-0.38 m over the stem's top, and the mechanics' 0.4-2.6 m stays | a few lines in `_height_limit_caps` and `_frame_room` | would leave most of the excess: not worth building alone |
| B. After the mechanics, no living node above the stem's top (cut the posture turn where it would lift one there) | rule change (mechanics) | top height −0.13 / −0.05 / −0.01 m at 45 / 50 / 60 and height SD −0.07 m at 45 (the T2 report's capped figures, SUSPECTED to carry over); forking crowns' tops; leaf area and light SUSPECTED small | `mechanics.py` and its compiled copy; 20 plots, 20 stand trees | control trees never more than 0.006 m over their limit (14 of 20) stay bit-identical; seeds 1, 5, 8, 11, 14, 20 change (stats.json, CONFIRMED); 20 paired plots on the plan's rows at 50 and 60 |
| C. Report the stem top beside height everywhere | records only | no result; the plan's height rows can be read on stem tops | the lines below | switch-off on plots seeds 1-2 and trees seeds 1-3 |
| D. Diagnose the posture swing first (is a 2-5 m lift a year real?) | diagnosis | nothing | one traced run per mechanics setting | – |

**Recommended: C now, and D before any rule.** C is not a rule change and moves no number; it lets decision 1 and E's height rows be read on stems. B would make heights follow the curve by force; it is the maintainer's call and should wait on D.

**The smallest logging addition (proposal, not made):**
- `tools/tree_list.py:101-108` (`last_year_of`): add `"stem_top_m": float(model.tree.pos[model.tree.trunk_chain(model.leader_axes)[-1], 2])`, and the name to `EXTRA` (line 55). A dead tree's row takes it from `plot._finish`'s `last` (`treegen/plot.py:555-556`), one more key.
- `tools/tree_table.py:343-348` (stand trees' yearly record in tree.json): the same value as `"stem_top_m"`. Not in `growth.measure()`: stats.json is compared whole by `tools/switch_off.py`, and tree.json only on shared keys.
- `treegen/plot.py:_log_year` (`606-618`, log.stand only): a second `top_height_approved_stem_m` from the same diameters and stem tops.

## Fault 2. Thinned neighbours come back (CONFIRMED)

- **Mechanism.** `stand_spacing(height)` (`growth.py:533-540`) picks the last schedule row whose `from_height_m` the height passed, every call, with no memory; `stems_per_ha` (`542-544`) follows. The light cell reads it at the start of each year from the highest living point (`growth.py:751-752`), after that winter's damage (`step` runs `damage.tree_year` at line 723). Also read the same way: soil water LAI (`894-895`, off by default), wind load (`1684`), crown reach (`2322`), damage's stand state (`damage.py:390`), and stats' `stand_spacing_m` and `lai` (`growth.py:3204-3208`, end-of-year height). So a shorter tree gets its removed neighbours back, and a lifted side top brings a thinning forward.
- **Plots: nothing can undo a removal.** `Plot._finish` (`plot.py:547-564`) takes a tree out of `alive` and frees it; `_thin` only removes; natural mode thins by the hazards (`_self_thin`) and the carbon rule; a plot's spacing is its live count (`plot.py:428-435`). Plot trees never call `_stand_cell`; their own stats' `stand_spacing_m` and `lai` are records nothing in a plot reads.

| Run (20 stand trees each) | Seeds where the row went backwards | Rows at 50; at 60 | A thinning moved by the highest point |
|---|---|---|---|
| Control `node_t2_kt` (= the fresh run, identical in stats.json: T2 report section 1) | none. Seed 10's year-45 snap left 18.95 m, over the last row's 16 m | 450 in 20 of 20; 450 in 20 of 20 | none: the rows change at 11 and 16 m, reached in years 21 and 31, before any tree is over |
| D0 `node_t2_d0` | none (seed 10's snap left 19.01 m) | 450; 450 | none |
| S1 `node_t2_s1` | seed 10: the snap at the start of year 45 left 19.33 m, under 20.5 m. The light read 700/ha in years 45-48 (375 first in 49); the stats rows read 375 at 44 and 700 at 45-47 | 375 in 20 of 20; 375 | seed 8: 375 read from year 43, seed 12 from 44; on stem tops both would be 45 (2 and 1 years early) |

- How much it moved those trees at 50 and 60 is not computed: that needs the fix built and the three seeds rerun. **Published figures on affected trees:** no default figure (control, D0, the fresh run, the scorecard's stand-tree rows) contains one. The T2 report's S1 rows at 50 and 60 (section 11, INFO) include seeds 8, 10 and 12; its 13-15 m reading (years 25-28) is before any of it.
- **The fix:** keep the highest schedule row reached (`stand_spacing` reads `max(row reached so far, row for this height)`, the row stored once a year). **A bug fix**, I judge: a thinning removes trees and the species file's own text describes a programme of removals; nothing in it brings them back. Under the plan: section 3, it touches `growth.py:533-544`, which E, B and pay-first don't; `_frame_goal` (C2's function) calls it, and C2 is stopped. Section 5: about 60 stand trees (control, D0, S1; 80 s each) and the tests. Section 8: no item applies. DECISIONS 111 asks every model change to be a switch; since no default run changes, whether this needs one is the maintainer's call.
- **Proof:** control 20 of 20 and D0 20 of 20 bit-identical (`tools/switch_off.py`), golden hashes unchanged, plots untouched by construction; S1 identical in 19 of 20, seed 10 from year 45. A unit test: a stand tree cut under a row's height keeps the row. Reading the schedule on stem tops (the table above) is a separate rule choice; it would move S1 seeds 8 and 12 from year 43 and 44, and no default tree.

## The switch-off tool (proposal only)

`tools/switch_off.py:109` allows an option to differ only if its name starts with `log.`. `shedding.log_limbs` is a log (it fills `limbs.json` and changes no growth: T2 section 1) but lives under `shedding`. Smallest right fix: a named set beside line 47, `LOG_OPTIONS = frozenset({"shedding.log_limbs"})`, read on line 109 as `name.startswith("log.") or name in LOG_OPTIONS`, with the docstring (line 29) saying so. `tests/test_switch_off.py:159-164` asserts today's behaviour and must change with it. Not `damage.log_snow_trees`: it adds rows to plot.json, which the tool compares.

## What I could not trace

1. How far the fault-2 fix would move S1 seeds 8, 10, 12 at 50 and 60: it needs the fix.
2. Whether the posture swings are physically real: no source opened. The plot's lineage covers one plot, to 45.
3. Ages 50 and 60 in the plot trace: run to 45 only (disk and the 8-plot limit). At 50 and 60 the stand-tree rows above apply; the plot share at 50 and 60 is the T2 report's (6.0 % and 1.8 %), with its part not traced.

## The build: the stem's top recorded, and a thinning that stays

2026-11-12. Model: Fable 5.2 (ID `claude-fable-5-2`). Branch `stem-top`: `height-trace` (`7b6f05c`) with master (`81425c8`) merged in. Commits: `17abd6e` (the build), then `34bd912` and `a6139cd` (a table tool and its tests; no model, species or run-tool file changed after `17abd6e`: CONFIRMED with git). Not merged, nothing adopted. All growth, tests and the golden check ran on the server. On the PC: edits, reading files, one model built from its seed with no year grown (to time it), and five unit tests run one at a time, each under a second. CONFIRMED = checked in a run or in code today. SUSPECTED = not.

**In five lines:**
1. A new record, off by default, writes each tree's stem top beside its height: in a stand tree's yearly file, in a plot's tree lists, and in a new yearly file for each plot. It changes no result.
2. Two new switches, both off by default, correct how a stand tree counts its neighbours. One keeps a thinning once it is reached. The other reads the schedule at the stem's top. Off is today's behaviour, bit for bit.
3. On the default schedule the two switches together change none of the 20 stand trees. On the Finnish schedule they change 3 of 20, the trees and years the diagnosis named: seed 10 from year 45 (first switch), seeds 8 and 12 from years 43 and 44 (second).
4. Read on stem tops, the two plots' top height at 45 is 0.24 m lower than reported and their height spread 0.12 m smaller. At 50 and 60 top height is 0.05 and 0.01 m lower.
5. New: at 50 the spread on stem tops is not always the smaller one. A stem a storm broke stands under its own limbs for some years.

### What was built, where, and how to switch it on

| What | Where it is written | How to switch it on |
|---|---|---|
| The record `log.stem_tops` | Species file, block `log`; `treegen/names.py`; `treegen/logs.py` | `--set log.stem_tops=true` on any run |
| A stand tree, every year | `tree.json`, each row of `yearly`: `stem_top_m`, beside that year's `height_m` in `stats.json` (`tools/tree_table.py`) | The same, on `tools/tree_table.py run` |
| Every tree of a plot | `trees_<age>.json`: a column `stem_top_m` right after `height_m`, for living and dead trees, and a header line `stem_top` (`tools/tree_list.py`) | The same, on `tools/forest.py` with `--tree-lists` |
| A plot, every year | `stem_log.json` beside `plot.json`, a row a year: `top_height_approved_m` (on highest points) and `top_height_approved_stem_m`; the dominants' mean height both ways; `height_sd_m` and `height_sd_stem_m`; `trees_over` and `over_most_m` (`treegen/plot.py` `_log_stem_tops`, called right after `_log_year`) | The same, on `tools/forest.py` |
| Switch 1, `stand.thinning_stays` | Species file, block `stand`; `treegen/growth.py` `_schedule_height` | `--set stand.thinning_stays=true` |
| Switch 2, `stand.thinning_on_stem_top` | The same. A managed plot's own thinning follows it too (`treegen/plot.py` `_thin`) | `--set stand.thinning_on_stem_top=true` |
| The tables below | `tools/stem_top_table.py plots <folder>` and `changed <control> <arm>`; it only reads saved files | – |

- **The stem's top** is the height of the last node of the stem, as the diagnosis read it. It is kept at the moment the year's `height_m` is read, so a storm later that year can't part the two. It is kept on the tree and never in the yearly row: `stats.json` has no new key.
- **The plot's record is its own file**, not new keys in `stand_log.json`, because the switch-off tool compares `stand_log.json` whole. So a run with every record on reads IDENTICAL by the tool's own verdict. Its top height on highest points is `stand_log.json`'s figure. My choice; flagged below.
- **The two switches are corrections of the model's own bookkeeping, not values from a source.** The labels file needs no row for them: it takes none for an on/off switch (CONFIRMED: the label check reads none of the three names as a value and reports no problem).
- **Every place that reads the schedule goes through one function now**: the light's neighbours, the soil water's leaf area (off by default), the wind's load, a limb's reach, damage, and the yearly row's spacing and leaf area index. A unit test fails if a new reader skips it. Switch 1 reads the schedule at the greatest height it has been read at so far. Switch 2 reads it at the stem's top, at the moment each place read the height before.
- **A managed plot** (not used by the plan's forest runs) only ever removes trees, so its thinnings stay already. With switch 2 it reads its dominants' stem tops.

### Proof (CONFIRMED, all on the server)

| Check | Result |
|---|---|
| Full tests at `a6139cd` | 612 passed, 1 skipped, and only the 4 that always fail on the server. At `17abd6e`: 610 passed, the same 4 |
| New unit tests (`tests/test_stem_top.py`) | 19 tests, no tree grown. The 17 timed alone on the server took 0.70 s at most |
| Golden check at `34bd912` | IDENTICAL on all eight runs. `cases/golden_server.json` is untouched |
| Records on, switches off: plots seeds 1-2 to 60 (`node_st_plots`, at `17abd6e`) against `node_t1r_plots_395355d` | IDENTICAL. `plot.json` whole, and all 311,190 and 316,638 values the tree lists share (18,271 and 18,616 tree rows over 19 ages). New and not compared: `stem_log.json`, `stand_log.json`, the lists' new columns |
| Records on, switches off: stand trees seeds 1-3 (`node_st_rec`) against `node_t2_kt` | IDENTICAL. `stats.json`, `limbs.json`, and all 1,370 values `tree.json` shares. New: `yearly.stem_top_m` |
| The record against the diagnosis's trace, made by another tool | Stand trees seeds 10, 11, 14: equal in 60 of 60 years each. Plot 1 at 35, 40, 42 and 45: the two top heights and the counts in the trace's table above, to the last digit printed there (20.584 and 20.304 m at 45) |
| The plot's yearly row against the tree lists | Worked out again from each age's list: the same at all 19 ages in both plots. Its top height on highest points equals `stand_log.json`'s in 60 of 60 years, both plots |

### The switches on (CONFIRMED)

20 stand trees a run, seeds 1-20, to 60, at `34bd912`, compared with `tools/switch_off.py`. Each run has its control's own settings (`log.rings`, `shedding.log_limbs`, and for S1 its schedule) plus `log.stem_tops` and the switches named. "Identical" means `stats.json`, `limbs.json` and every value `tree.json` shares.

| Run | Schedule | Switches | Against | Result |
|---|---|---|---|---|
| `node_st_kt_both` | default | both | `node_t2_kt` | 20 of 20 identical. No seed changed in any year, as the diagnosis expected |
| `node_st_s1_both` | Finnish (S1) | both | `node_t2_s1` | 17 of 20 identical. Changed: seeds 8, 10, 12 |
| `node_st_s1_stays` | Finnish (S1) | 1 only | `node_t2_s1` | 19 of 20 identical. Changed: seed 10, the same tree as with both on |
| `node_st_s1_stem` | Finnish (S1) | 2 only | `node_t2_s1` | 18 of 20 identical. Changed: seeds 8 and 12, the same trees as with both on |

| Seed | Switch | Where the yearly rows hold another schedule row: control; switched, stems/ha | The tree itself changes from |
|---|---|---|---|
| 8 | 2 | years 42-43: 375; 700 | year 43. Its last thinning comes 2 years later |
| 10 | 1 | years 45-47: 700; 375 | year 45. The thinning reached at the end of year 44 holds through the storm of year 45 |
| 12 | 2 | year 43: 375; 700 | year 44. Its last thinning comes 1 year later |

The three trees at 50 and 60. Each cell: control; switched.

| Seed | Age | Height, m | Stem top, m (switched) | DBH, wood, cm | Leaf area, m² | LAI | Crown base, m | Lowest live branch, m |
|---|---|---|---|---|---|---|---|---|
| 8 | 50 | 21.95; 21.95 | 21.95 | 26.33; 25.84 | 133.9; 125.8 | 5.02; 4.72 | 10.76; 10.91 | 9.20; 9.51 |
| 8 | 60 | 23.75; 23.75 | 23.75 | 30.49; 29.73 | 137.7; 128.1 | 5.17; 4.80 | 13.10; 13.10 | 13.10; 13.10 |
| 10 | 50 | 21.17; 21.16 | 21.16 | 27.27; 27.84 | 93.9; 117.3 | 3.52; 4.40 | 10.79; 10.79 | 10.79; 10.23 |
| 10 | 60 | 23.42; 23.42 | 23.42 | 31.37; 32.01 | 128.7; 136.7 | 4.83; 5.13 | 13.64; 13.64 | 13.64; 13.64 |
| 12 | 50 | 21.95; 21.95 | 21.95 | 21.77; 21.55 | 95.9; 93.6 | 3.60; 3.51 | 10.03; 10.03 | 10.03; 10.03 |
| 12 | 60 | 23.75; 23.75 | 23.75 | 24.68; 24.38 | 90.3; 88.9 | 3.38; 3.33 | 12.04; 12.04 | 12.04; 12.04 |

- This answers item 1 of "What I could not trace". Seed 10 carries a quarter more leaf at 50 when its thinning stays, and 0.6 cm more stem at 50 and 60. Seeds 8 and 12, thinned later, are 0.2-0.8 cm thinner. Heights move by 0.01 m at most.
- Over the 20 trees these cancel: the Finnish arm's mean DBH moves by 0.01 cm at 50 and 0.02 cm at 60, its mean LAI by 0.02 and 0.01 (arithmetic on the rows above). The T2 report's S1 rows are INFO and stand as printed.
- With switch 2 alone a broken stem can still get its neighbours back (seed 10 is identical to the control there). SUSPECTED, not run on more trees: the two belong together.

### The height rows on stem tops (CONFIRMED; two plots, not the plan's 20)

`node_st_plots`, seeds 1 and 2, 1,000 m². Top height is the approved definition both times, on the same trees and diameters. Height SD is the plan's spread row (`tools/independent_checks.py`): the sample SD over the living trees with a DBH. "Over" counts trees whose highest point is more than 0.3 m above their stem's top.

| Age | Plot | Trees | Top height on highest points; on stem tops; difference, m | Height SD on highest points; on stem tops; difference, m | Trees over (the most) |
|---|---|---|---|---|---|
| 30 | 1 | 279 | 15.363; 15.363; 0.000 | 0.914; 0.914; 0.000 | 0 |
| 30 | 2 | 290 | 15.191; 15.191; 0.000 | 0.806; 0.806; 0.000 | 0 |
| 45 | 1 | 85 | 20.584; 20.304; +0.280 | 1.129; 1.009; +0.120 | 20, 23.5 % (1.84 m) |
| 45 | 2 | 98 | 20.441; 20.240; +0.201 | 1.068; 0.950; +0.118 | 12, 12.2 % (1.76 m) |
| 50 | 1 | 65 | 21.581; 21.579; +0.002 | 1.089; 1.172; −0.083 | 7, 10.8 % (1.58 m) |
| 50 | 2 | 73 | 21.391; 21.300; +0.091 | 1.040; 1.003; +0.037 | 5, 6.8 % (1.89 m) |
| 60 | 1 | 49 | 23.515; 23.496; +0.020 | 1.307; 1.294; +0.013 | 1, 2.0 % (0.92 m) |
| 60 | 2 | 54 | 23.156; 23.148; +0.008 | 0.966; 0.969; −0.003 | 1, 1.9 % (0.50 m) |
| Mean of the two, at 30; 45; 50; 60 | – | – | difference 0.000; +0.241; +0.047; +0.014 | difference 0.000; +0.119; −0.023; +0.005 | 0 of 569; 32 of 183; 12 of 138; 2 of 103 |

- **Against the T2 report's 20 plots** (top height +0.13 / +0.05 / +0.01 m and height SD +0.07 / +0.02 / 0.00 m at 45 / 50 / 60). Top height: about twice that at 45, the same at 50 and 60. Height SD: about twice that at 45, the other sign at 50 (−0.02 against +0.02), nothing at 60. Seed 1 is that report's largest plot at 45 (+0.280 there too). The first tree stands over its stem in year 35 in both plots.
- **The two methods differ for a broken stem.** The T2 report counted each tree no taller than its curve limit. This record reads the stem's real top. In plot 1 a storm in year 49 snapped tree 1537 at 15.47 m. At 50 its stem's new top is at 15.81 m and its limbs reach 17.39 m, 1.58 m over. By 60 the stem is the top again. That one tree makes the spread on stem tops the larger one at 50 (1.172 against 1.089). Without it the two are 1.055 and 1.043, still not smaller on stem tops: 5 of the 6 other trees over their stems have stems shorter than the plot's mean, so their limbs bring them nearer the mean.
- **For the plan's rows.** Height SD at 45, step E's adoption row, reads 0.98 m on stem tops against 1.10 m reported, as the mean of these two plots. Top height at 50 and 60 reads 21.44 and 23.32 m on stem tops against 21.49 and 23.34 m. The plan's 20-plot control rows can't be re-read this way: those plots kept no stem tops.
- The diagnosis's table gave the SD over n trees; this one over n − 1, as the plan's row does. That is the whole difference between 1.122 and 1.129 at 45.
- Run time with every record on: 3,323 and 3,372 s against the control's 3,253 and 3,215 s. Other jobs ran beside mine, so I can't say what the records cost (SUSPECTED little: one walk down the stem a tree a year).

### What is not done, and what I flag for the maintainer

1. **No rule keeps a limb under the stem's top.** Options A, B and D above are untouched.
2. **Only two plots have stem tops.** Reading the plan's height rows on stem tops for all 20 control plots means running them again with the record on (about 2 h 45 min at 8 at once).
3. **Each switch alone ran on the Finnish schedule only.** On the default schedule only both together ran (20 of 20 identical). The D0 arm was not rerun. The golden runs were not recorded with a switch on.
4. **Whether either switch should be on by default is not decided here.** On the default schedule the two together change no tree of seeds 1-20.
5. **Which height the plan's rows should read** (highest points, stem tops, or both printed) is the maintainer's call, as the table "What height should mean" above says.
6. **The plot's record is a file of its own.** Say if the stem-top top height should go into `stand_log.json` as well; that file would then differ from every earlier run's.
7. **Not written anywhere else:** `cli.py`'s single trees and the game export don't record the stem's top.
8. **Seen and not changed, two reading tools** work the schedule row out again from the saved height: `tools/damage_check.py:32` and `tools/root_measure.py:227` (which has 1,800 / 1,000 / 450 written in). With a switch on, or on another schedule, they can read another row than the tree grew with. Proposal: read the row's saved `stand_spacing_m` instead.
9. **Seen and not changed:** a stand tree takes the last schedule row in the file's order whose height it has passed; a plot sorts the rows by height first. They agree while the file's rows are in order, as they are (CONFIRMED in code; no run).
