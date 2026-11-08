# Tree agent's handover to the Crown agent

The maintainer judged that none of the renders looked right yet. The numbers below hold; the look doesn't. Shape starts from test A. Every setting here is off by default.

Server and PC results are never compared with each other. Where a row says "PC", it's only against other PC rows.

## Test A

Add `--set` before each:

```
height_driver.enabled=true
height_driver.ring_share_max=0.5
height_driver.lateral_cap_ratio=0.6
stats.limbs_on_leader=true
pipe_model.heartwood_by_own_foliage=true
pipe_model.branch_sapwood_senescence=0.30
resource.apical_dominance=0.75
bud_fate.long_shoot_threshold=5
bud_fate.density_control.enabled=true
bud_fate.density_control.after_growth=true
shedding.shade_softness=0.5
shedding.light_per_leaf_threshold=0.18
bud_fate.short_shoot_survival_light=0.18
```

Run it with `tools/tree_table.py run --label node_X --seeds 20 --set ...`. It writes the same `stats.json` as an ensemble, plus `tree.json`. Read it with `tools/tree_table.py table|seeds|fall|shape|shapeseeds|stem|roots|young|driver|open`.

### Results: 20 server seeds, old settings (`node_base`) and A (`node_A2`)

| | Old, 50 | Old, 60 | A, 50 | A, 60 | Target or data |
|---|---|---|---|---|---|
| Height (m) | 25.29 | 27.07 | 21.95 | 23.75 | SI 23: 21.95, 23.75 |
| Reads as SI | 26.2 | 26.3 | 23.0 | 23.0 | one value, 15 to 60 |
| LAI | 3.09 | 3.27 | 4.27 | 4.09 | 3.6-5.4 |
| Seeds at 3.6 or more | 2/20 | 4/20 | 19/20 | 17/20 | the band is 3.6-5.4; this counts its lower edge only |
| Light (%) | 30.1 | 27.5 | 18.8 | 19.4 | 6.4-19.8 |
| Seeds inside the light band | 0/20 | 0/20 | 15/20 | 11/20 | |
| Implied k | 0.393 | 0.398 | 0.394 | 0.406 | paper 0.37 |
| Stem over bark (cm) | 30.7 | 33.4 | 26.9 | 29.8 | |
| Stem wood, kg (Repola) | 321 (341) | 419 (419) | 235 (237) | 306 (305) | |
| Branch wood, kg (Repola) | 52.8 (61.3) | 74.0 (74.5) | 38.5 (46.1) | 52.6 (59.2) | see below |
| Crown width (m) | 3.37 | 3.95 | 6.61 | 7.29 | Evo: 4.69 at 20-25 cm, 5.21 at 25-30 cm |
| Mean first-order branch (m) | 1.25 | 1.28 | 1.57 | 2.37 | Lintunen 1.02, ages 4-32 |
| Branches per 10 % of crown | 19.0 | 18.4 | 13.2 | 9.6 | Lintunen 5.2 |
| Crown ratio | 0.72 | 0.69 | 0.56 | 0.54 | Repola's trees: mean 0.58, band 0.29-0.96 |

Over all ages:

| | Old | A |
|---|---|---|
| Years under 2 cm of height growth | 165 of 1,120 | 0 of 1,120 |
| Whole-crown flips | 205 of 1,120 | 1 of 1,120 |
| Largest one-year fall in leaf area: median, worst seed | 22 %, 53 % | 4 %, 7 % |

The old settings' branch-wood mean is false; see "Why branch wood looked fine".

### Crown width at the same stem diameter (wood only, as `tools/m3_crown_compare.py` bins it)

| Stem (cm) | Evo (m) | Old (m) | A (m) | A + `resource.branch_aging_years=12` (m) |
|---|---|---|---|---|
| 10-15 | 3.47 | 1.84 | 2.93 | 2.56 |
| 15-20 | 3.95 | 2.33 | 4.25 | 4.24 |
| 20-25 | 4.69 | 2.71 | 6.33 | 5.53 |
| 25-30 | 5.21 | 3.18 | 7.21 | 6.50 |

Open-grown data barely enters this: only one open-grown tree was grown (L6, one seed, below), against Hemery 2005's formula in the target file, a paper not opened.

### Twigs, branches and crown lift: A, 20 server seeds

| Age | Branches shed /yr | Twigs shed /yr | Short shoots lost /yr | Crown base (m) | Lowest live branch (m) | Crown ratio |
|---|---|---|---|---|---|---|
| 20 | 19.1 | 54 | 1126 | 4.3 (2.4-5.1) | 4.2 | 0.59 (0.52-0.77) |
| 30 | 12.3 | 37 | 956 | 6.6 (4.4-8.7) | 6.6 | 0.58 (0.45-0.72) |
| 40 | 8.0 | 34 | 718 | 7.3 (4.4-9.3) | 7.0 | 0.63 (0.52-0.78) |
| 50 | 6.7 | 33 | 1161 | 9.6 (5.8-12.8) | 9.3 | 0.56 (0.41-0.73) |
| 60 | 2.9 | 20 | 649 | 10.8 (5.8-13.6) | 10.6 | 0.54 (0.43-0.75) |

All of it falls by each part's own light and carbon, with no schedule by age. Every seed is inside Repola's band at every age. Hynynen's managed floor of 0.50 is met by 13/20 at 50 and 9/20 at 60; it's a recommendation, not a target. As a cross-check, at about 14 m tall the lowest live branch is 5.2 m (3.8-6.4), with 13/20 inside Hynynen & Niemisto's 5-7 m (planted stands, as `reports/birch_knowledge_base.md` C1 has it).

Plots, ages 11-22, 0.30-0.45: I ran no plots. Stand trees read about 0.59 at 20, which is above that band, but a stand tree thins to 1,000 stems/ha by 11 m and isn't that case.

### Roots: 20 server seeds

| | Old, 50 | Old, 60 | A, 50 | A, 60 |
|---|---|---|---|---|
| Root share of carbon | 0.253 | 0.256 | 0.250 | 0.251 |
| Carbon to roots (units) | 18,114 | 19,325 | 21,560 | 22,738 |
| Structural root wood (kg) | 10 (8-15) | 13 (11-20) | 8 (6-9) | 11 (8-13) |
| Root length (m) | 865 | 1,152 | 895 | 1,220 |
| Fine roots (kg) | 1.71 | 1.82 | 2.34 | 2.30 |

- The limit doesn't change the root share: it comes from water stress.
- Roots get more carbon and more length, but about 15-20 % less structural wood, because root wood is laid from the stem base's radius and A's stem is thinner.
- Structural root wood is only about 3-4 % of stem wood on both settings. That looks low to me; I read no source for it.

### What each setting does

| Setting | What it did | Evidence |
|---|---|---|
| Height limit | Height reads SI 23 at every age, no years under 2 cm | 20 server seeds |
| `bud_fate.density_control` | The big one: flips 42 to 0 of 448, largest leaf-area fall 38 % to 5 %, LAI at 50 3.86 to 4.24 | 8 PC seeds, with other settings the same, except the cap, ratio 1.0 against 0.85 |
| `ring_share_max` 0.5 | Flips 116 to 42 of 448 | 8 PC seeds, before density control |
| `branch_sapwood_senescence` | Branch wood at 50: 15.3, 24.6, 33.5 kg at 0, 0.1, 0.2. 0.4 gave 50.1 kg, with the default pendulous radius | 8 PC seeds |
| `heartwood_by_own_foliage` | Stops a forked or broken stem rebuilding its sapwood every year | seed 3 by hand; `node_brk_*` tests it across seeds |
| `shade_softness` 0.5 | Removing it: LAI 4.14, 3.91 against A's 4.27, 4.09; light 19.9, 20.7 against 18.8, 19.4; flips 0 against 1. A small gain, so it could go | 20 server seeds |
| `apical_dominance` 0.75 | Back at 0.62: width 4.67, 5.55 (nearer Evo), LAI 4.10, 3.99, light 20.7, 20.2, branch wood 33.1, 43.2 kg, flips 23 against 1 | 20 server seeds |
| `branch_aging_years` 12 (not in A) | Width 5.59, 6.48 and everything else holds: LAI 4.25, 4.08, light 19.2, 19.3, branch wood 38.2, 49.9 kg, flips 1. **Best lead for width** | 20 server seeds |
| `lateral_cap_ratio` | Removed: width 8.74, 9.46 at 50, 60 | 20 server seeds |
| `leaf_growth_max` 1.0 instead of 1.5 | Almost nothing at 50 or 60; a bit less young leaf area | 20 server seeds |

### Dead ends

| Tried | Result | Evidence |
|---|---|---|
| `lateral_cap_ratio` 0.45 | No narrower at 60 (7.13 m), LAI down to 3.63, branches longer | 8 PC seeds |
| `light.woody_shade` off, fresh laterals charged, k 0.40 | LAI 3.0, light 39 %, flips back | 3 PC seeds only, so weak |
| No `ring_share_max` | Flips 116 of 448, some seeds stuck under LAI 2 | 8 PC seeds, before density control |
| `shedding.persist_years` (a wait before shade death) | Removed: leaves below compensation for years, the pool hits zero | 2 PC seeds |
| `height_driver.crown_growth_ratio` (side shoots tied to the leader's Borchert-Honda share) | Removed: crown 1.2-1.7 m wide, or the share swings wildly | 1-2 PC seeds |
| `twig_cap_ratio` 0.3 | Worse by eye | 1 seed |
| `stem_bud_every` 6 with the shape settings | Stem leans, lopsided crown | 1 seed. 20-seed tests of 3 and 6 cancelled |
| `pendulous_radius_limb` 0.002-0.003 with all twigs set to grow down | Limbs do rise, but the crown collapses to a narrow column, and seedling limbs survive as a V from the ground | 1 seed each |
| Carbon store (`store_fraction`) | Built, never needed, never tested | - |

### L6: limbs arch, twigs hang, not better than A by eye

A plus: `mechanics.pendulous_radius_limb=0.005`, `mechanics.pendulous_radius=0.008`, `height_driver.leader_lost_in_crown=true`, `tropism.setpoint_angle_deg=[0,43,45,120]`, `tropism.gravitropism_per_m=[2.0,3.5,2.0,2.0]`, `tropism.twigs_keep_gravitropism=true`.

On 20 server seeds at 50, 60:
- **Passes:** LAI 4.29, 4.02; light 18.7, 19.5; stem wood 235, 299 kg (Repola 249, 318); branch wood 46.2, 67.1 kg (51.3, 64.7); crown ratio 0.63, 0.60; 2 flips of 1,120.
- **Doesn't:** width 7.13, 9.38 m, with one seed at 17 m from a long low limb. Limb angles 91-116 deg.

By eye the crown is narrower and thinner than A's. Grown in the open, one seed, it's a full curtain to the ground, but with DBH 89 cm at 60. The species file gives 40-50 cm for open-grown or released trees, so that fails.

## Code to reuse for limbs

| What | Where |
|---|---|
| The limit: curve, light and water factors, leader paid first | `treegen/growth.py`: `_curve_height`, `_height_limit_plan`, `_growth_factor` (`lead_at`), `_height_limit_log` |
| The stem is the path to the paid shoot | `_height_limit_settle_stem`; `Tree.stem_tip` in `treegen/structure.py` |
| The cap and its floor; nothing ends above the leader | `_height_limit_caps`: `lateral_cap_ratio`, `lateral_cap_floor_m`, `twig_cap_ratio` |
| Limb softness | `mechanics.pendulous_radius`, `mechanics.pendulous_radius_limb`; `_limb_nodes`; `mechanics.bend_and_correct(limbs=...)` |
| Limb and twig tropisms | `tropism.setpoint_angle_deg`, `tropism.gravitropism_per_m`, `tropism.twigs_keep_gravitropism`, in `_grow_shoots` |
| The leader lost in the crown | `height_driver.leader_lost_in_crown`: after `resource.reiteration` says dominance is lost, the highest tip carries the height, and reiterated limbs skip the cap |
| Limb wood | `pipe_model.branch_sapwood_senescence`, `_sapwood_loss` |
| One limb per so many stem buds | `bud_fate.stem_bud_every` |

## Limb angle

- **The measure:** `crown_shape()` in `tools/tree_table.py`; read it with `tree_table.py shape X` or `shapeseeds X`. `angle_low`, `angle_mid`, `angle_up` are the angle from vertical of the chord from a limb's base to 0.5 m along it, by where the limb sits in the crown (limbs of 0.3 m or more). The same record has where the crown is widest, rival tops, bare stem at the top, hanging twigs, lone limbs and side fill. Side fill is my own measure, and no paper read gives it.
- **The published 43 deg:** mean 43.2 deg, range 15-80, SD 10.4, Forests 9:52 (2018), a clonal plantation in Latvia, as the species file quotes it at `architecture.branch_angle_deg`. I didn't open the paper. Check how it measured the angle before holding a 0.5 m chord to it. Mäkinen et al. 2003 has branch-angle models, read only as an abstract.
- **No value found:** for angle by height in the crown, where a birch crown is widest, leader loss, or how far twigs hang.

| 20 server seeds, deg from vertical | Age | Low | Mid | Up | Tip chord, low | Mid | Up |
|---|---|---|---|---|---|---|---|
| A | 30 | 96 | 111 | 97 | 139 | 153 | 119 |
| A | 50 | 87 | 92 | 92 | 115 | 131 | 121 |
| A | 60 | 84 | 88 | 95 | 119 | 134 | 144 |
| L6 | 60 | 91 | 98 | 105 | 98 | 122 | 140 |
| Height limit off | 60 | 62 | 64 | 64 | 88 | 118 | 136 |

So limbs leave the stem level or below it, and end well below it. That's the measured form of what the renders show. The old settings weren't measured this way.

## The height limit's effect on limb wood

Test A without the limit, its ring cap or its side shoot cap (`node_A_lim`, 20 server seeds):

| At 50, 60 | Limit off | A |
|---|---|---|
| Limb angle at the stem (deg) | 62-67 | 84-95 |
| Branch wood (kg) | 122, 178 (Repola 85, 94) | 38.5, 52.6 (Repola 46, 59) |
| Height (m) | 30.6, 32.8 (SI 31-32) | 21.95, 23.75 |
| Flips | 104 of 1,120 | 1 of 1,120 |
| Years under 2 cm | 196 of 1,120 | 0 of 1,120 |

My reading, untested: more wood per limb makes limbs stiffer and lays more reaction wood, so they rise. That says thicker limbs, not necessarily no limit. A tree this much taller isn't a like-for-like comparison, and three settings were off together. If limbs can't reach real angles with the limit on, that's the maintainer's decision, with this as the evidence.

Why limbs are thin under the limit: A has about 100 first-order limbs at 60 (Lintunen's count would suggest about half that), and on seed 3 about 70 % of side wood was exactly what the sapwood rule asks (test Z, before `branch_sapwood_senescence`). 42-51 % of fixed carbon goes unused to age 10, thrown away at `leaf_growth_max`, while the tree is held to the curve. Whether keeping it would thicken limbs isn't tested. The first lead I'd try: `pipe_model.stress_floor.safety_factor` thickens a limb at its base, by bending stress, instead of evenly. One render at 10 is on the PC only, no numbers. That wood isn't charged to the carbon budget, so charge it if you use it.

## The side shoot cap fault

`caps[i] = ratio x leader's shoot / internode`, and a new lateral needs `long_shoot_threshold` nodes. At ratio 0.6 and threshold 5, once the leader's shoot falls under 0.21 m (about age 46 at SI 23), the cap is under the threshold, and no new side shoot can start anywhere except on reiterated limbs. Tips still extend, so nothing flags it. This comes from reading the code; no count across seeds was made. In A, the bare stem at the top goes from 0.7 m at 50 to 2.0 m at 60.

- `height_driver.lateral_cap_floor_m=0.25` removes the fault. One seed by eye shows no spike. The 20-seed test (`node_F2`) was cancelled, so **test this first**.
- A has this fault as it stands.
- It isn't the whole spike. With the limit and the cap both off, the bare top is longer: 3.5 m at 60.

## Faults in the old model, all behind off settings (the old settings keep them)

1. **Stem measure.** After a leader switch, `trunk_chain` follows a thin side stem, because a replacement's first node is forced as thick as the stem. On the server, seeds 8, 9, 20 read 0.187-0.301 m3, with the measured stem's top at 9.5-13.6 m on 26-28 m trees. On PC the path to their tallest tip is 0.91-1.02 m3. They aren't thin. Only the old settings do this; with the limit on, A's measured stem reaches the tree's height in all 20 seeds, 0.42-0.72 m3. **The limit is needed for that fix: it comes from `stem_tip`, so plots on the old settings still have the fault.**
2. **Why branch wood looked fine.** Those three seeds' real stems count as branches, 378-483 kg each. The other 17 read 10.3 kg against Repola's 69.8, and stem wood 469 against 404. The earlier "wood is fine" came from that mean.
3. **Crown ratio, same cause.** `measure()` counts order == 1 as limbs, so a replaced leader reads as a low limb, and those seeds read about 0.92. `stats.limbs_on_leader` fixes it. On stand trees the gap is about 0.01 in the mean, but those seeds carry it. Plots' 0.72 against 0.30-0.45 may hold some of this; I ran no plots.
4. **Sapwood below the crown base.** `crown_rise_heartwood` gives every node below the crown base one figure, the crown base's. On a fork or a broken stem, that figure is low, so sapwood is cut and rebuilt every year. On a default tree, seed 7, broken at 40 with leaf area 60 to 1.5 m2, DBH at 60 was 30.0 cm against 29.5 cm untouched, and the yearly ring at 1.3 m matched that rule. `pipe_model.heartwood_by_own_foliage` fixes it. A, 20 server seeds: leaf area 94 to 2.6, then 50 m2 by 60; height 14.4 m against 23.7 m; DBH gain 62 % of the untouched tree's. `node_brk_base` and `node_brk_fix` test it across seeds at commit 740eb9d. Read them with `tools/top_break_check.py table`.
5. **Wind moment.** New leaves raise the wind moment, and with it the whole stem's ring need, in `_growth_factor`. With the limit on it stays the canopy's moment. In the old model it's still there.
6. **Year-to-year reading.** Light is read before the year's shedding and LAI after it. When foliage swings, the two readings disagree. Once it's steady, they agree.

## Where the model departs from real birch

- **The height limit**
  - Height follows the curve almost regardless of the tree: all 1,200 seed-years of A were held by the curve, none by light, water or carbon. At alpha 2.0, 42 % of normal, with the link to alpha switched off, height doesn't change at all at 20 to 60, and DBH is 12.6 cm at 60. The leader's cost is under 2 % of the pool past age 5, so paying it first hides a shortage. It falls short only in extreme cases: a broken top, starved test trees, the first five years at low alpha. So in normal use it's close to scripted. That's the opposite of what the maintainer asked for, and it needs deciding.
  - Nodes are real and cost carbon, and no node is moved (`tests/test_height_limit.py`).
  - With `height_driver.reference_alpha` on (the default), a plot tree's alpha does move its limit.
  - Water and light shortage are tested only one tree at a time, and light has never run on plots.
  - Below 1.3 m the path is a power law with no source. Lost height comes back at 1.25 x the curve's increment, which real trees don't do.
  - Age 5 reads 1.16 m against the establishment band's 1.2-1.8 m.
- **Stems and forks.** A second replacement leader always becomes a limb, so there are no true forks, only crooks. Forks and stem defects should be counted against 39-42 %.
- **Carbon.** 42-51 % of fixed carbon is lost to age 10. It stands in for nutrients and competition. Real trees would down-regulate, store it, or use it. Stem wind thickening waits when rings are capped.
- **Leaf area.** Twice to 4.5 times Konopka's at ages 10-15.
- **Shedding.**
  - The shade death chance has no source.
  - Death lines at 0.18 are under the 0.21 measured: on seed 5 of L6 that keeps low limbs alive at 0.18-0.21 light, right at the line. Across seeds it isn't tested.
  - Dead branches vanish at once, while real birches hold them for years. No wind or snow breakage is called yet (`treegen/damage.py` isn't wired in).
- **Stand trees.** Neighbours are copies of the tree, which makes the whole canopy cross any line at once.
- **Free wood.** `stress_floor` wood isn't charged.
- **Limbs.** Level or drooping from the stem, too thin and too many, too wide at 40-60. No fill measure against photos.
- **Light and LAI.** Light goes from 26.9 to about 19 % through tuned values, not anything measured about birch.

## Open questions

1. Can limbs reach about 43 deg, with leaf area and light holding? Which comes first: fewer and thicker limbs, a stress-based limb base, or the floor?
2. Is the limit acceptable as it stands, given it almost never falls short? The maintainer's decision.
3. Does the floor remove the spike across seeds? What makes the 3.5 m bare top with the limit off?
4. Is the leader carrying fewer leaves than it would without the limit? Not measured.
5. Does `branch_aging_years` 12 hold up at 40 seeds? It's the best width lead.
6. Open-grown trees: DBH 89 cm and far too wide on one L6 seed. Carbon needs a limit there. `node_base_open`, `node_F2open` were cancelled.
7. A on plots: `node_int_A`, running under main.
8. Young leaf area over Konopka; root wood at 3-4 % of stem.
9. `stem_bud_every` across seeds, against Lintunen's count: A is 2-3 times his count at 20-50.
10. Top-of-crown fill and the lone low limbs: measure with `shape`, which includes `lone` and `fill`.

## Site index

`height_driver.site_index` is a plain setting, and the years to breast height follow it. The game's Siljan site reads about 15-17 in its own unverified translation. The targets don't cover that site, and the climate stayed Uppsala's (59.86 N, `sweden_open_field`), not Siljan's.

SI 16 against A, both on 8 PC seeds. This only shows whether the tree still behaves on a poorer site:

| At 50, 60 | SI 16 | A (SI 23) |
|---|---|---|
| Height (m) | 14.54, 16.59 | 21.95, 23.75 |
| Reads as SI | 16.0, 16.0 | 23.0, 23.0 |
| Stem over bark (cm) | 22.2, 24.5 | 26.1, 28.9 |
| LAI | 3.97, 2.30 | 4.11, 3.87 |
| Light (%) | 20.6, 42.9 | 19.7, 20.6 |
| Stem wood, kg (Repola) | 93 (111), 133 (152) | 222 (226), 285 (291) |
| Branch wood, kg (Repola) | 9.4 (37.3), 13.4 (45.3) | 38.4 (42.2), 50.7 (54.3) |
| Crown width (m) | 4.02, 3.86 | 6.70, 7.38 |
| Crown ratio | 0.50, 0.45 | 0.61, 0.59 |
| Flips, of 448 | 3 | 0 |
| Largest leaf-area fall: median, worst seed | 12 %, 17 % | 4 %, 7 % |

The fall in LAI at 60 comes from the stand's thinning table, which is keyed to height: the tree reaches 16 m and goes to 450 stems/ha at about age 58. That's the likely cause, though I didn't test it separately. Branch wood is about a quarter to 30 % of Repola's, so the wood rule doesn't carry to this site.
