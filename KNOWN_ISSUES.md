# Known issues

## Phase 20: leaves and fine roots cost carbon

### Step 1: leaf and fine-root costs

Leaves and fine roots were free. Every year each tree now pays (`resource.leaf_costs`):
- **Rebuilding its leaves:** this season's leaf dry mass (leaf area × LMA), plus growth respiration.
- **Leaf maintenance:** 0.79 g C per g per year (Oleksyn et al. 2000; season and temperature VERIFY).
- **Fine-root maintenance:** 0.93 g C per g per year (Ryan, Lavigne & Gower 1997), for fine roots weighing 0.48 of the leaves (Aosaar et al. 2016).

Grams are converted to model units through the wood the unit builds (1.2e-6 m³ at 530 kg m⁻³, so 0.64 g). Each branch's carbon balance also counts its own leaves.

**CUE 0.47 cannot be kept.** Leaf and fine-root respiration plus growth respiration take ~45 % of the fixed carbon on their own.
- Wood maintenance went 0.7 → 0.2, now ~10 % of the fixed carbon.
- The plots' CUE (all tree-years from age 20) is 0.38–0.40, as before (0.38–0.41).
- That is within the published 0.40–0.52 (boreal at the low end), at its edge.
- The weakest input is the leaf respiration's measurement temperature, which is not stated in the source.

**Death rule.** At first a tree died in its first deficit year, before it could shed the branches that did not pay. The natural plot lost 96 of 100 trees by 35. A tree in deficit now sheds its starving branches before the next flush, and dies only if it is still in deficit the next year. The plot also no longer crashes when its last tree dies.

**Alpha 5.6 → 6.2.**
- At 5.6 the managed plot's mean height fell just under the band at 60 (21.0 m), with crowns down to 1.9 m.
- At 7.0 the top quarter was 1–3 m above the band.
- At 6.2 a short shoot's leaves break even at ~22 % light, against the measured 21 % of the lowest birch leaves.

**Plots at 6.2** (seed 1; before = the phase-17 runs; band from Eriksson et al. 1997):

| | age | N/ha | H mean | top 25 % | band | DBH | crown ratio | crown base | LAI |
|---|---|---|---|---|---|---|---|---|---|
| managed, before | 30 | 450 | 19.6 | 21.2 | 13.4–19.7 | 18.3 | 0.81 | 3.9 | 3.61 |
| | 50 | 450 | 24.5 | 26.2 | 19.2–25.3 | 20.6 | 0.66 | 8.2 | 3.66 |
| | 60 | 450 | 25.9 | 27.3 | 21.1–26.9 | 21.6 | 0.64 | 9.4 | 3.70 |
| managed, now | 30 | 450 | 18.7 | 20.4 | 13.4–19.7 | 19.9 | 0.74 | 5.0 | 3.15 |
| | 50 | 450 | 22.7 | 24.1 | 19.2–25.3 | 21.2 | 0.72 | 6.4 | 3.12 |
| | 60 | 450 | 24.0 | 25.2 | 21.1–26.9 | 21.6 | 0.75 | 6.0 | 3.12 |
| natural, before | 30 | 1170 | 17.2 | 20.5 | 13.4–19.7 | 14.1 | 0.73 | 5.0 | 3.77 |
| | 50 | 765 | 23.4 | 25.5 | 19.2–25.3 | 17.4 | 0.60 | 9.7 | 3.62 |
| | 60 | 585 | 25.6 | 26.9 | 21.1–26.9 | 19.5 | 0.45 | 14.1 | 3.69 |
| natural, now | 30 | 1206 | 16.8 | 20.1 | 13.4–19.7 | 14.8 | 0.63 | 6.5 | 3.06 |
| | 50 | 1080 | 18.9 | 24.1 | 19.2–25.3 | 14.8 | 0.60 | 8.1 | 2.95 |
| | 60 | 972 | 20.0 | 25.3 | 21.1–26.9 | 15.3 | 0.62 | 8.2 | 2.95 |

**Stem metrics** (noise-matched, 4.6 px), now against before (photos: off-line 1.60 %, turning 11.4°, lean 2.2°):
- natural: off-line 1.89 % (1.68), turning 8.5° (7.5), lean 1.9° (2.0);
- managed: off-line 1.86 % (1.79), turning 8.4° (7.6), lean 2.6° (3.1).

**Still off:**
- The natural plot self-thins less (972/ha at 60, against 585 before).
- Its deaths: 35 of carbon deficit, 10 of no carbon, 1 failed to establish.
- LAI fell from ~3.7 to ~3.0–3.1.
- The managed crown base is 6 m at 60, against 9.4 m before.

### Step 2: ground light (diagnosis; the fix is open)

**The light model is not the cause.** Ground light (median over the plot, at 0.1 m) follows Beer–Lambert at the plot's own LAI to within ~2 points:

| plot | LAI | ground light | exp(−0.37 × LAI) |
|---|---|---|---|
| natural, phase 17 | 3.65 | 27.9 % | 25.9 % |
| natural, step 1 | 2.95 | 35.5 % | 33.5 % |
| managed, step 1 | 3.16 | 33.1 % | 31.1 % |

**Stems and branches.** Hagemeier & Leuschner took K_PAR = 0.37 from measured transmission against litter-trap (leaf-only) LAI. Woody shade is therefore already in K, and adding it would count it twice.

**The cause is leaf area.** Their stands measured 14.8 % at LAI 4.6. A canopy keeps leaves down to ~21 % light, which at K = 0.37 means LAI ≈ 4.2. The model's canopy stops near 33–35 %. Estonian silver-birch stands span LAI 2.5–4.4 (Uri et al.).

**Branch carbon balance limits the model's LAI.** From the managed year-55 checkpoint, 5 years:
- with it switched off, LAI climbs 3.1 → 3.55 and is still rising;
- with the 21 % light-per-leaf rule switched off, nothing changes.

**The starving branches are well lit.** Bud light is 0.40 (median), and they are order-2 limbs with ~33 buds at ~18 m. Fully watered, their own carbon would be 59 units against 7 (wood) + 34 (leaves). They starve because the trees are water-limited:

| | stomatal opening at 30 / 45 / 55 | root share at 55 |
|---|---|---|
| managed, phase 17 | 0.91 / 0.83 / 0.79 | 0.32 |
| managed, step 1 | 0.76 / 0.70 / 0.66 | 0.37 |

**Chain:**
1. Fine-root maintenance (step 1) comes out of the root share, which halves root building (~0.1 of the fixed carbon against ~0.2).
2. Root length per carbon (`root_segments_per_unit`, VERIFY) and uptake per root length were tuned when roots were free, so water uptake falls.
3. The stomata close, branches lose a third of their carbon, the well-lit limbs are shed, and LAI falls.

**Open.** The fix is to re-tune what the roots buy per unit of carbon, for which no source has been found. One option: let water uptake come from the same fine-root mass the tree now pays for (0.48 of leaf mass, via specific root length).

## Phase 19: seedlings on stones, the no-carbon death, regeneration (first version)

**The 9 seedlings that never grew** (phase 18) had three causes, now fixed.
- **Stones reached the surface everywhere.** Stones now lie below a stone-free organic layer of 6 cm (4–10 cm on mesic till, Larson et al. 2023, Sci. Rep. 13:14909). They reach the surface only on `surface_stone_cover` of the ground (2 %, VERIFY).
- **A root tip meeting a stone tried three random deflections and then stopped.** It now turns sideways along the stone by the smallest turn that clears it: 30°, 60° or 90°, towards any of 8 sides (Massa & Gilroy 2003, Plant J. 33:435).
- **A tree with no absorbing root got a token uptake conductance of 1e-12.** It could fix a trickle of carbon forever. It now gets none: no water, no carbon.

**Death rule.** In either plot mode, a tree that fixes no carbon two years running dies. In its first 5 years this is logged as "failed to establish".

**Natural plot, seed 1, at 15 years:**
- All 9 seedlings now establish and grow to 6.0–11.0 m.
- Deaths: 1 of carbon deficit (year 14), 1 failed to establish (on a surface stone, year 3).
- The 97 trees alive in both runs moved by 0.15 m on average against the first reference.

**Regeneration** (`treegen/regeneration.py`; `tools/plot.py --regeneration`; values in `regeneration:` in the species YAML) works as follows:
- **Seed rain** from every tree past `maturity_years`, falling off with distance.
- **One-year seedlings per seed** depend on the seedbed: exposed mineral soil or the organic layer.
- **Light:** germinants below the 21 % light at which birch leaves die are lost.
- **Recruits:** at most one per 1 m cell per year, grown on as full trees.

Short test: the 55-year natural plot (13 trees, 585/ha), resumed and run 8 years with regeneration.
- **Seed rain** was 7,500–8,000 seeds/m² a year. Liu & Evans 2021 report up to 2,000–9,600 within 40–50 m of a seed tree.
- **Ground light** was 25–29 % everywhere under the 60-year canopy. That is above 21 %, so every free cell recruited in the first year: 212 recruits on 222 m². None followed, because every cell was then occupied.
- **Survival:** all 212 were alive after 7 seasons, at a median height of 0 m (max 0.18 m).
- **Published survival:**
  - paper birch on Alaskan clear-cuts: about 20 % of first-year germinants alive after 5 years (USDA Silvics);
  - mountain birch in Iceland: over 50 % after 1–2 years (Óskarsdóttir et al. 2025, Ecol. Appl. 35:e70115);
  - silver birch is shade-intolerant, and its seedlings do not persist under a closed canopy.

**Causes, open:**
1. **A shaded seedling never extends and never dies.** Its bud gets about 1.5 carbon units a year, and a long shoot needs 3. So it stays a single short shoot. It has no wood and so pays no upkeep, and it still fixes carbon, so neither death rule applies.
2. **Nothing shades seedlings below the canopy.** The field layer (herbs, grasses, dwarf shrubs) is off by default.
   - With it on, a seedling under 27 % canopy light would get about 7 % at 5 cm and lose its leaves.
   - But a seedling in full light would get only about 25 %, also short of a long shoot. So the field layer alone would stop all regeneration, the first cohort included.
3. **Browsing of small seedlings (voles, hares) after their first year** is not modelled. No source has been found yet.

**Not yet modelled:** old-age death, uprooting (root plates exposing mineral soil), and variation in the seed crop between years.

## Phase 18: speed (shared soil, compiled tree passes)

The workloads are timed one at a time on the same machine, one run each:
- a natural plot, seed 1, to 15 years (`tools/plot.py --no-mesh`);
- one stand tree to 30;
- 3 plot years from age 55 (resumed from a checkpoint).

| change | plot to 15 | stand tree to 30 | plot years 55–58 |
|---|---|---|---|
| before | 280 s (peak 1.8 GB) | 9.8 s | 31.8 s |
| 1. one shared soil per plot | 129 s (0.9 GB) | 9.6 s | 30.1 s |
| 2. bending and posture compiled | 79 s | 7.2 s | 19.8 s |
| 3. subtree sums compiled | **61 s** | **6.2 s** | **16.0 s** |
| overall | 4.6× | 1.6× | 2.0× |

**Change 1, the shared soil, changes results.** Before it, every tree in a plot rebuilt the whole plot's soil grid every year with its own seed, so the trees did not share stones or rootable depth.
- At 15, the 91 trees that grew in both runs moved by +0.2 % in mean height and +1.3 % in mean DBH (0.22 m per tree on average).
- Single trees are untouched (bit-identical).
- Part of change 1's 2.2× comes from 9 trees that no longer grow (below). Without them it is about 2×.

**Changes 2 and 3 do not change results.** Every array of every timeline and every per-year statistic is bit-identical to the run before each change. The numba kernels repeat the numpy expressions operation for operation.

**Seedlings on a stone never establish, and never die.** This is open.
- With private soils every stem sat on the corner of four stone cells, so the radicle always found a stone-free cell.
- In the shared soil 13 of 100 stems start above a stone (the top-soil stone fraction is 8–10 %). In 9 of them the radicle cannot get past it, and the tree stays at 0 m.
- The natural-mode death rule (carbon below upkeep) never removes these trees, because both are zero. They lower plot means (mean height at 15: 8.51 → 7.71 m with them included).
- A seedling that cannot root should fail to establish. This needs a rule before natural regeneration is added.

## Phase 17: noise-matched traces, stem gravitropism refitted on the plot

**Fair comparison.** The model's projected stems are now clicked like the hand traces:
- each trunk gets a click count drawn from the 144 hand traces (2–9, median 4);
- each click gets Gaussian scatter;
- each result is the mean of the medians over 60 random repeats.

**Scatter estimate.** The hand-trace scatter is estimated from the 60 traces with 5 or more clicks, as the residual around a quadratic: median 0.5 % of image height, which is 9.1 px on the render. This is an upper bound, because it includes real wobble and wobblier trunks got more clicks. The central case is half of it, 4.6 px.

**Fit.** Stem gravitropism was fitted on the natural plot (13 trees at 60) against lean, max off-line and total turning together. The loss is the sum of squared relative errors against the photos' medians:

| scatter | 1/m | 2/m | 3/m | 4/m |
|---|---|---|---|---|
| 2.3 px | 0.65 | **0.41** | 0.61 | 0.98 |
| 4.6 px | 0.81 | **0.14** | 0.20 | 0.41 |
| 9.1 px | 1.93 | 0.52 | 0.38 | **0.35** |

- The stem gravitropism is now 2/m (a convergence length of about 0.5 m), which is best at the central and low scatter.
- Heights are unchanged and in the band. The mean is 23.4 / 25.6 m at 50 / 60 in the natural plot and 24.5 / 25.9 m in the managed plot, against a band of 19.2–25.3 / 21.1–26.9 m.

**Noise-matched, 4.6 px** (medians, middle half in brackets):

| | Gullmarsskogen (54) | all photos (144) | natural 4 / 1 / 2 per m | managed 4 / 1 / 2 per m |
|---|---|---|---|---|
| max off-line, % | 1.7 (1.3–2.7) | 1.6 (1.1–2.7) | 1.3 / 2.7 / **1.7** (0.9–2.6) | 1.4 / 2.4 / **1.8** (1.0–2.6) |
| total turning | 12.7° (7–24) | 11.4° (5–21) | 6.1 / 10.7 / **7.5°** (3–15) | 6.6 / 10.5 / **7.6°** (4–16) |
| bends per trunk | 1 (1–2) | 1 (0–2) | 0.9 / 1.0 / **1.0** (0–2) | 1.0 / 1.0 / **1.0** (0–2) |
| mean bend | 8.5° | 8.4° | 6.8 / 7.9 / **7.0°** | 6.8 / 7.8 / **7.0°** |
| lean | 2.1° (1.0–3.7) | 2.2° (1.0–4.1) | 1.3 / 3.6 / **2.0°** (1.0–3.2) | 1.7 / 5.0 / **3.1°** (1.6–4.9) |
| forked | 0 % | 2 % | 0 / 0 / 7 % | 0 / 9 / 0 % |

- With scatter matched, the phase-15 stems (4/m) were already 80 % of the photos' off-line value and half their turning. The perfect-click comparison overstated the gap (0.5 % and 1°).
- At 2/m, off-line, bends and the natural plot's lean match.
  - Turning is still a third low (7.5° against 11.4°), but this depends on the scatter: at the 9.1 px upper bound the model gives 13.5°.
  - Lean in the managed plot overshoots (3.1°).

**Top breakage: no sourced rate.** No annual rate of snow or wind top breakage in Nordic birch was found:
- Donis et al. 2024 (*Forests* 15:275), young hemiboreal birch in Latvia: one freezing-rain and snow event damaged 31.0 % of trees.
  - 93.7 % of the damaged trees were bent, so only about 2 % were broken or uprooted.
  - After one season, 31.3 % had less bending and 8.2 % more. There is no return rate.
- Díaz-Yáñez et al. 2016 (*PLoS ONE* 11:e0161361), the Norwegian national forest inventory 1995–2014: birch was the most snow-resistant species. No breakage share is given for birch.
- *Snow damage to birch stands in Northern Moravia* (*J. For. Sci.* 2012): bending was predominant and breakage was at most 4 % of trees (not Nordic).
- Valinger & Fridman 1999 (*Environ. Manage.*): paywalled, not read.

Nothing was added. The documented damage in young birch is snow bending followed by partial recovery, not breakage, and it has no sourced frequency either.

## Phase 16: why the stems were straight

**Stem over time** (stem sections grown at ages 0–5, 5–10, 10–20 and 20–30, measured every 5 years to 60, 6 trees per plot):
- At the multi-metre scale, bends never formed. Each section was laid down almost straight (offset 0.02–0.07 %, turning 0.3–0.5°), then sagged slowly (to 0.4–0.9 % by 60). There were no bends of 4° or more at any age.
- Consecutive 5-year sections left the leader within 0.5–0.6° of each other (p90 1.2–3.7°), also when a neighbour within 3 m died (23 % of sections).

**Annual sympodial kinks** (seed 1, yearly):
- They form at 9.5° (median; p90 18°) and are straightened to 7.8 / 4.6 / 2.8 / 2.3 / 2.0° after 1 / 2 / 3 / 5 / 10 years. With posture control off they stay at 12–17°.
- The correction is within physics. It uses 1 / 11 / 15 / 7 % of what the new ring allows (C·Δr/r², Alméras & Fournier), at joint radii of 0.45 / 0.89 / 1.34 / 2.08 cm. Sections thicker than 2 cm already keep their shape (0.3° a year).
- These kinks are 0.6 m features in random directions, invisible to 4-click traces. Limiting the correction would change nothing there.

**The cause: the leader could not change course.**
- Leader gravitropism of 4 per m (no source) brought a deflected leader back on its target within 0.25 m of growth.
- Against phototropism of 0.8 per m, the leader could turn toward light by at most ~11°, typically 1–3°, and only for as long as the light stayed one-sided.
- Leader changes come only from browsing at 0.3–3 m. No sourced rates exist for top breakage higher up.

**Fix.** Stem gravitropism 4 → 1 per m (a ~1 m convergence length), and replacement leaders now use the stem's tropisms. (Refitted to 2/m on the plot in phase 17.)
- Calibrated on one observable, the lean of single stand trees (seeds 1–3 at 40: 0.8 / 1.6 / 2.1 / 2.6° at 4 / 2 / 1 / 0.5 per m; photos 2.1–2.2°). Height unchanged.
- In the plots, 5-year sections now change course by 1.6–1.8° (p90 3.7–5.0°), and bends develop over the years (offsets 1.3–1.7 % and 6–9° of turning by 60).

**Against the 144 hand traces** (4 clicks, `tools/stem_metrics.py`):

| median | Gullmarsskogen | all photos | natural before / after | managed before / after |
|---|---|---|---|---|
| max off-line, % | 1.7 | 1.6 | 0.5 / 2.2 | 0.7 / 1.8 |
| total turning | 13° | 11° | 1 / 7° | 2 / 6° |
| bends per trunk | 1 | 1 | 0 / 1 | 0 / 1 |
| mean bend | 8.5° | 8.4° | – / 6.3° | – / 6.9° |
| lean | 2.1° | 2.2° | 1.2 / 3.5° | 1.7 / 4.9° |
| forked | 0 % | 2 % | 0 / 0 % | 0 / 9 % |

- Off-line and bends are now in the photos' range; total turning is about half.
- Lean overshoots in the plots (3.5–4.9° against 2.1–2.2°), although it matched in the single-tree stands it was calibrated on. Plot trees grow next to real, uneven neighbours.
- Plot heights stay in the Swedish band (mean 19.6–19.7 / 23.4–23.5 / 25.2 m at 30 / 45 / 60).

## Stem straightness: hand traces against the model

- **Hand traces:** 144 trunks hand-traced with the Birch Stem Tracer (`tools/birch-stem-tracer.html`, served by `tools/serve_tracer.py`) on 23 photos: 54 trunks on the three Gullmarsskogen stand photos, 90 on iNaturalist whole-tree photos. Median 4 clicks per trunk; traces in `reference/stem_traces.json`.
- **Model:** the stems of the phase-15 plots, projected through the same camera as the photo-matched render and selected as the tracing instructions say (base in frame, not touching the edges, at least 15 % of the image height). Measured with the tool's own code (`tools/stem_metrics.py`), resampled to 4 evenly spaced clicks per trunk.
- Medians (middle half); bend threshold 4°:

| | Gullmarsskogen (54) | all photos (144) | natural plot (13 trees) | managed plot (10 trees) |
|---|---|---|---|---|
| max off-line, % of length | 1.7 (1.3–2.7) | 1.6 (1.1–2.7) | 0.5 (0.3–0.8) | 0.7 (0.4–1.0) |
| total turning | 13° (7–24) | 11° (5–20) | 1° (0–2) | 2° (1–3) |
| bends per trunk | 1 (1–2) | 1 (0–2) | 0 (0–0) | 0 (0–0) |
| mean bend | 8.5° | 8.4° | – | – |
| lean from vertical | 2.1° | 2.2° | 1.2° | 1.7° |
| forked | 0 % | 2 % | 0 % | 0 % |

- **Click scatter does not explain it.** A perfectly straight stem traced with 4 clicks of 2 / 4 / 6 px scatter measures 0.35 / 0.68 / 1.07 % off-line and 0 / 2 / 5° turning, with no bends.
- **The model's stems are 2–3× straighter than real birch and have no bends of 4° or more.** The traced model trunks are tiled copies of 13 and 10 trees.
- *Phase 17:* with the hand traces' own scatter added to the model's clicks, most of this gap was click scatter (see above).
- **Candidate causes**, the tool's list, not yet tested:
  - posture control correcting too fully;
  - too few leader changes;
  - light that does not shift as neighbours die.

## Phase 15: twig packing, short shoots, sub-branches

**Why twigs packed** (seed 1 at 15 and 25 years, second-order leafy buds):
- **Not the light grid.** Only 14–18 % of a twig bud's shade comes from its own 10 cm layer; reading the shade one voxel up raised bud light only from 0.29–0.33 to 0.31–0.38.
- **Not internode length.** Internodes are 2.5–3.1 cm on all orders, the birch value.
- **The long-shoot gate.** At 1 metamer (phase 14) every bud that could afford one or two metamers made a 1–2-node long shoot. That gave 12× as many third-order shoots and doubled the local leaf density (3.8 → 7.3 m² m⁻³ within 0.25 m).
- The gate is back at 3: birch laterals make either a short shoot or a long shoot of several nodes. Second-order shoots then survive (99 % after 5–8 years, against 53 %). But they stay small: 0.054 m² of leaf and 0.51 cm at 12 years.

**Why sub-branches stayed small.**
- Short shoots were sinks in the Borchert–Honda split: 73 % of the shoot resource went to them and was lost (years 15–30). The tips of sub-branches got almost nothing after their first year.
- Short shoots are now self-financing (`bud_fate.short_shoots_self_financing`, [M82]): they fix carbon with their own leaves and draw nothing. Release of short shoots into long shoots, uncommon in birch, no longer happens.
- Also tried: excluding every bud that will not grow from the split (`idle_buds_no_sink`). All resource then went to growing buds, and leaders raced ahead of their stems (whips, H/D ~190; CUE 0.34). Off.
- Heights left the band with the change, so `alpha` went 6.6 → 5.6.

**Managed plot (40 → 10 trees at 450/ha), limbs against the 6 Nordic scans** (scan counts are an upper bound: QSM overestimates thin branches, Demol et al. 2022, Silva Fennica):

| | scans, 15.5–19.7 m | phase 14 (gate 1), 30 y / 17.4 m | phase 15, 30 y / 20.1 m | phase 15, 60 y / 26.2 m |
|---|---|---|---|---|
| branches ≥ 1 cm, order 1 / 2 / 3 | 68 / 440 / 826 | 120 / 18 / 0 | 94 / 1 / 0 | 26 / 28 / 10 |
| sub-branches ≥ 1 cm per limb > 2 cm | 6.8 | 0.71 | 0.13 | 8.0 |
| limbs > 2 cm | 58 | 30 | 16.5 | 4 |
| largest limb / stem diameter, p90 | 0.67 | 0.29 | 0.28 | 0.64 |
| leaf area per second-order branch at 60 (median) | – | 0.013 m² | – | 0.094 m² |

- At 60 the limbs branch like the scans: 8 sub-branches ≥ 1 cm per limb, limb/stem ratio 0.64, crowns of a few large limbs.
- At the scans' height (20 m, year 30) the sub-branches have not thickened yet: they reach 1 cm about 30 years later than in the scanned trees.

**Natural plot at 60** (same setup): 585/ha (27 of 40 died); DBH 18.9 ± 3.4 cm; mean height 25.6 m, top quarter 27.0 m; LAI 3.72.
- Sky fraction 27 / 40 / 62 / 68 % at 5–15 / 15–25 / 25–35 / 35–45°, against the photos' 12–14 / 37–49 / 45–61 / 60–68 %. Phase 14 had 16 / 46 / 67 / 73 %.
- Crowns spread on longer limbs with fewer twig clusters.
- The low band is more open than the photos because the stand has fewer stems. Stems are still uniform grey.

## Phase 14: respiration, limb branching, whips and junction bulbs

**Respiration** (`resource.maintenance_per_internode`, `growth_respiration_coefficient`).
- Growth respiration: 0.25 g C per g C built (Ryan 1991; VERIFY).
- Maintenance is paid from the tree's pool before allocation. Charged along the flow instead (P09/LIGNUM), a realistic rate drained long limbs: 73 % of limb tips got under one metamer.
- Wood rings, shoots and roots are built from what remains.
- Calibrated to a carbon use efficiency of ~0.47 (Waring et al. 1998: 0.47 ± 0.04; Collalti & Prentice 2019: 0.46 ± 0.12): maintenance 0.02 → 0.7 per internode.
- `alpha` re-tuned 4.6 → 5.8 to the Swedish height curves it was tuned to before, now as gross carbon.
- Seed 1 stand: mean CUE 0.45–0.50 over 20–60, with a basal fork. Young growth is slower and the canopy closes later, so a fully lit low limb keeps up with the leader.

**Natural plot at 60, before and after** (40 trees at 1800/ha on 222 m², seed 1, every default on):

| | before | after |
|---|---|---|
| stems/ha | 1575 (5 of 40 died) | 810 (22 died) |
| DBH | 19.7 ± 8.8 cm, CV 45 % | 20.0 ± 3.5 cm, CV 18 %, Gini 0.10 |
| height mean / tallest quarter / max | 25.7 / 33.9 / 35.8 m | 18.7 / 20.9 / 22.2 m (band 21.1–26.9) |
| crown base | 8.5 m (0.29 H) | 5.5 m (0.28 H) |
| LAI | 4.33 | 3.80 |
| sky fraction 5–15 / 15–25 / 25–35 / 35–45° | 6 / 14 / 35 / 47 % | 16 / 46 / 67 / 73 % (photos 12–14 / 37–49 / 45–61 / 60–68 %) |
| forked / crooked at 60 | 0 / 31 % | 28 / 11 % (crown); 0 on the bole |

- Self-thinning now works.
- Overgrowth is gone; heights are now slightly low (mean below the band).
- Low limbs are not killed: relative crown base unchanged.
- The "1.3 m survivor" of phase 13 was a browsed tree 3.4 m tall whose stem record broke at the leader change, so it had no DBH. None is left.

**Limb branching against the 6 Nordic scans** (the managed plot, as the scans are probably managed stands; plot trees at 17.4 m, year 30):

| | scans | managed plot before (age 20) | managed plot after |
|---|---|---|---|
| branches ≥ 1 cm, order 1 / 2 / 3 | 68 / 440 / 826 | 60 / 23 / 0 | 120 / 18 / 0 |
| bifurcation N1/N2, N2/N3 | 0.18, 0.52 | 2.6, 23 | 6.3, 18 |
| sub-branches ≥ 1 cm per limb > 2 cm | 6.8 | 0.9 | 0.7 |
| limbs > 2 cm | 58 | 27 | 30 |
| largest limb / stem diameter, p90 | 0.67 | 0.32 | 0.29 |

- The long-shoot gate was not the cause. At 3 metamers (no source) it turned 42 % of the fresh lateral buds on limbs into short shoots. It is now 1, as in P09, and the gap did not close.
- The cause is shedding: of 112 k second-order shoots made by year 25 in the managed plot, 80 % died, at a median of 2 years. The survivors are 0.35 cm thick at 30; 1 % reach 1 cm.
- They die by the light and carbon tests inside dense twig clusters (phase 11: 7 m² m⁻³ of leaf within 0.25 m of a twig bud). Not fixed.
- TreeQSM probably over-counts thin branches, but not twentyfold.

**Whips.**
- The 34–36 m trees were browsed trees whose replacement leader (an order-1 axis) passed its old limb's physiological age to the laterals it grew. Those laterals lost vigour, and the leader took everything: 0.5–0.65 m of height a year at 0.1 cm of DBH (H/D up to 268).
- Laterals on any leader now start their own scaffold. The tallest tree is now 22.2 m.

**Bulbous bases.**
- Not the root ridges: on thin trees the main roots are 0.06–0.35 of the stem radius, so their ridges are small.
- The bulbs were browsing junctions at 0.3–1 m: a thick old stem stub, a replacement leader joining it with a 35 % branch collar, and fillet flaps.
- Fixes: the collar scales with 1 − branch/parent radius (none on a co-dominant junction), and a replacement leader's base is never thinner than the stem below it. One near tree in the render still shows fillet flaps.

## Phase 13: checkpoints, natural stands, stress-floor rings

**Checkpoints.** Every 5 years each plot tree's yearly history goes to disk, its arrays are trimmed, the plot is pickled and `plot.json` rewritten. Trees are exported as they leave the plot.
- A resumed run is identical to a straight one: stand statistics, every year's radii, keyframes and root history all match (checked at year 15 in both modes).
- The natural plot below peaked at 2.2 GB, against 5.5 GB for the 25-tree managed plot before.

**Natural mode** (`--mode natural`): no thinning; a tree dies when its own carbon no longer pays the upkeep of its living wood.
- The combined run: 40 trees at 1800/ha on 222 m², unthinned, every default on (browsing, buttresses, stress floor), 60 years.
- Area: 100 trees on the managed plot's 556 m² would need roughly 10 GB by 60.

| plot year | stems/ha | DBH | CV | Gini | tallest tree | LAI |
|---|---|---|---|---|---|---|
| 20 | 1800 | 13.5 ± 6.0 cm | 44 % | 0.22 | 18.3 m | 4.00 |
| 30 | 1710 | 16.2 ± 6.9 cm | 43 % | 0.23 | 24.5 m | 4.04 |
| 45 | 1665 | 18.2 ± 7.9 cm | 43 % | 0.24 | 29.3 m | 4.40 |
| 60 | 1575 | 19.8 ± 8.8 cm | 45 % | 0.25 | 35.8 m | 4.33 |

- **Spread:** wider than any published managed or planted stand (Romans 2023 Gini 0.09–0.13; Hagemeier & Leuschner 2019 CV 32 % at 880/ha). There is no measured DBH distribution for Gullmarsskogen; the photos show stems of every size.
- **Self-thinning is far too weak:** 5 of 40 trees died in 60 years, leaving 1575/ha.
  - Healthy trees fix 20–60 times their wood upkeep, so the rule kills only trees that have lost almost all their leafy buds.
  - One tree still under 1.3 m is alive at 60.
  - The light low in the stand is too high (phase 10: floor 0.24 against 0.15 measured), so suppressed crowns stay just above the 21 % death threshold.
- **Stem form:** 14 of 35 survivors were browsed. 31 % have a crooked stem above 1.3 m and 3–9 % a fork at 20–25 (published: 39–42 % with a stem defect at 22). Forks are gone again at 60. Largest branch / stem diameter: median 0.47 at 60.
- **Render:** framed like the photos, at the plot's true positions. Sky fraction 6 / 14 / 35 / 47 % by band (photos 12–14 / 37–49 / 45–61 / 60–68 %).
  - Stems of every size, thin suppressed ones among the dominants, and some crooked stems: closer to Gullmarsskogen than the thinned plot.
  - Still too dense, with uniform grey stems, and twigs clustered high in the crowns.
  - Several thin stems have bulbous bases, probably buttress ridges sized by roots that are large relative to a suppressed stem. To check.
- **Height:** the tallest trees reach 33–36 m at 60 in both plots, against 26.9 m at the top of the Swedish band. Dominants in a plot outgrow the single-tree stands (29–30 m).

**Stress-floor rings** (`pipe_model.stress_floor`): each ring is at least what keeps the self-weight bending stress under green MOR / safety factor.
- Green MOR 57 MPa: 114 MPa seasoned silver birch × the green/seasoned ratio of yellow birch (VERIFY). Safety factor 3.5 (Univ. Tokyo branch study). So 16 MPa.
- **It never binds.** In seed 1 at 20 the model's limbs carry 1.6 MPa at the base (median), 3.6 MPa at most; no internode reaches the limit. With the floor on or off: 2 limbs over 2 cm, limb/stem ratio p90 0.31, 18 m of branch wood at least 1 cm thick.
- The model's limbs are thin because they are light (the largest carry 400–900 leaves), not because the ring rule is too weak.
- The extra wood would not be charged to the carbon budget.

**Limbs against the 6 Nordic stand scans** (15.5–19.7 m):

| | scans (median) | thinned plot, age 20 | natural plot, trees at 15–20 m | seed 1 stand, age 20 |
|---|---|---|---|---|
| limbs > 2 cm | 58 | 27 | 4 | 2 |
| largest limb / stem diameter, 90th percentile | 0.67 | 0.32 | 0.31 | 0.31 |
| branch wood ≥ 1 cm | 869 m | 70 m | 34 m | 18 m |

The limb deficit is in growth (limb length and the shoots each limb carries), not in strength.

## Phase 12: the plot to 60, Nordic stand scans, iNaturalist photos

**The 25-tree plot to 60** (seed 1, every default on: browsing, buttress flare).
- It grew all 60 years in 1688 s.
- Memory: peak 5.5 GB, not the 3–3.5 GB estimated. Each tree's history (keyframes every 5 years, radius samples) grows by about 3.5 MB a year once the stand has thinned to 25 trees.
- Claude Code's low-memory guard stopped it during the export, after 16 trees, with a 17th written in part (timeline, stats and crown mesh). The other 8 survivors and `plot.json` were never written.
- The layout, germination years and vigour factors were rebuilt exactly from the plot seed, and checked: every tree's last year = 60 − germination year.
- Stand rows for all 25 trees come from the log. Tree-level numbers come from the 17 exported trees (export follows tree id, not size).

| plot year | stems/ha | DBH, all 25 trees | CV | tallest tree | LAI |
|---|---|---|---|---|---|
| 10 | 1800 | 6.1 ± 3.0 cm | 50 % | 7.3 m | 2.33 |
| 15 | 1008 | 15.7 ± 3.0 cm | 19 % | 13.1 m | 3.32 |
| 20 | 450 | 22.3 ± 2.6 cm | 12 % | 18.0 m | 2.94 |
| 30 | 450 | 28.1 ± 3.6 cm | 13 % | 24.4 m | 3.60 |
| 40 | 450 | 31.4 ± 3.6 cm | 11 % | 27.9 m | 4.09 |
| 50 | 450 | 33.9 ± 3.6 cm | 11 % | 31.7 m | 4.26 |
| 60 | 450 | 35.9 ± 3.7 cm | 10 % | 36.5 m | 4.29 |

The 36.5 m tree is one of the 8 that were not exported. The 17 exported trees top out at 31.8 m, so it cannot be examined.

**Diameter distribution against published stands** (17 exported trees):

| | age | stems/ha | DBH / QMD | spread |
|---|---|---|---|---|
| model plot | 30 | 450 | QMD 27.3 cm | Gini 0.052, CV 9 % (13 % over all 25) |
| model plot | 33 | 450 | QMD 28.5 cm | Gini 0.052 |
| Romans 2023 (SLU MSc), Skräddarbo, planted 1989, fenced | ≈33 | 1233–2056 at 19 years, one later thinning of unrecorded intensity | QMD 14.2–17.7 cm | Gini 0.09–0.13 |
| model plot | 45 | 450 | 32.7 ± 3.6 cm (all 25) | CV 11 % |
| Hagemeier & Leuschner 2019 (Forests 10:925), Germany | 45 | 880 | 19 ± 6 cm | CV 32 % |
| model plot | 50 / 60 | 450 | 33.9 / 35.9 cm (all 25) | CV 10.5 / 10.3 % |
| Hagemeier & Leuschner 2019, Germany | 67 | 420 | 25 ± 3 cm | CV 12 % |

- **Spread:** at 50–60 it matches the German stand of similar density (12 %). At 30–45 it is about half the published spread: thinning from below to 450/ha by 16 m removes the small trees, and the survivors stay within ±20 % of each other.
- **Size:** at matched density, DBH is about 40 % above the German stand (35.9 cm at 60 against 25 cm at 67). Height is above the Swedish band too (below).

**Forks and crooks.**
- None of the 17 crop trees lost a leader, so none is forked or crooked at age 20, 25 or 60 (the stem is the leader axis; crooks are bends of 10° or more between 0.5 m chords above 1.3 m).
- About half of all trees should have been browsed once. Unbrowsed survivors by chance would have a probability of about 0.48^17 ≈ 4 × 10⁻⁶.
- So thinning from below removed every browsed tree: a browsed tree loses about 2.3 m of height by age 22 and falls behind.
- Single-tree stands (20 seeds, browsing on / off):

| age | forked | crooked | H on / off |
|---|---|---|---|
| 22 | 20 % / 0 | 45 % / 0 | 15.9 / 18.2 m |
| 50 | 20 % / 0 | 45 % / 0 | 27.6 / 27.8 m |
| 60 | 25 % / 0 | 45 % / 0 | 30.5 / 29.4 m |
| published | 38.6–41.7 % with a stem defect at 22 (Viherä-Aarnio & Velling 2008) | | |

**Height against the Swedish band** (Eriksson, Johansson & Kiviste 1997, site index H50 20–26 m; total age = breast-height age + 4):

| age | band | single trees, browsed | single trees, unbrowsed | plot crop trees (mean / max) |
|---|---|---|---|---|
| 22 | 10.0–15.6 m | 15.9 m | 18.2 m | – |
| 50 | 19.2–25.3 m | 27.6 m | 27.8 m | 28.7 / 30.1 m |
| 60 | 21.1–26.9 m | 30.5 m | 29.4 m | 30.4 / 31.8 m |

- The site curves come from real, browsed stands. Browsing closes 2.3 m of the gap at 22 but nothing at 50–60: browsed trees catch up by about 50.
- In the plot, the browsed trees were thinned out, so the crop trees are the unbrowsed ones.
- The gap at 50–60 (2.3–3.6 m above the top of the band) is not browsing. It is left for the nitrogen and growing-season phase.

**Persistent basal limbs in the plot.**
- Some crop trees keep living limbs from their first 2–7 years at 0.1–2 m, with 5–35 living short shoots each at 60 (tree 003: 15 limbs below 3 m; 063: 5; 013: none).
- The light low in the stand stays above the 21 % death threshold: the model's floor light is 0.24, against 0.15 measured (phase 10).
- The early-germinated crop trees also had smaller neighbours while young.
- This is the base-limb problem of the open-grown trees, now in the plot. Not fixed this round (no new mechanisms).

**Photo-matched winter render of the plot.**
- The plot's 17 exported trees laid out at random at 450/ha (true positions incomplete), framed as before.
- Sky fraction 9 / 15 / 36 / 47 % at 5–15 / 15–25 / 25–35 / 35–45°. The clone stand had 12 / 19 / 43 / 56 %; Gullmarsskogen has 12–14 / 37–49 / 45–61 / 60–68 %.
- It still reads as a plantation: straight, smooth, parallel grey stems of similar size and no forks or crooks. Twigs sit in clusters at the crown tops. The photos show leaning and crooked stems of every size, forks, and long ascending limbs.

**Nordic stand-grown scans (FOR-species20K): 6 of 30 so far.**
- 30 silver-birch TLS scans were chosen from `../tree-data/for-species20k` (GPL-3.0, read only): the Junttila (Finland) and Luke (Natural Resources Institute Finland) sets, trees 15.5–29 m tall with at least 0.6 M points.
- Not chosen: Liang_2018 (94 trees) is too sparse (median 47 k points), REMBIOFOR is Polish, VanDeBerge is the Belgian hedgerow set already used.
- Branch models were built with TreeQSM in Python (PyTLidar 1.0.1, GPL-3.0), in a separate scratch environment (Python 3.12) outside the repo. Clouds were thinned to at most 1 M points (voxel 0.4–1.5 cm), with TreeQSM's own automatic patch sizes.
- Scan outputs stay outside the repo and are used only as comparison numbers. No scan geometry enters the generator.
- Only 6 trees finished (15.5–19.7 m):
  - one failed on a PyTLidar index error in its stem-top search (12829);
  - one QSM run grew to 8.4 GB and brought the machine to 0.4 GB free (12827), so the batch was stopped;
  - 23 trees are still to run.
- Metric definitions as for the Belgian scans and the model: base diameter = the smaller of the branch's first two cylinders; ratio = branch / stem diameter at the attachment for branches > 2 cm below 0.8 H; angle = TreeQSM branch angle to the parent; low limbs = first-order branches > 2 cm below 0.5 H.

| | Nordic scans, 15.5–19.7 m (median, p10–p90) | model plot trees at 20 (17.5 m) | model plot trees at 30 (23.4 m) |
|---|---|---|---|
| DBH | 17.7 cm (13.3–19.4) | 22.0 cm | 27.4 cm |
| first-order branches > 2 / 5 / 10 cm | 58 / 3 / 0 (29–68 / 1–26 / 0–2) | 27 / 0 / 0 | 41 / 0 / 0 |
| largest branch / stem diameter, max | 0.95 (0.90–1.34; values > 1 are QSM artefacts) | 0.38 | 0.35 |
| the same, 90th percentile | 0.67 (0.57–0.73) | 0.32 | 0.30 |
| branch angle, low / mid / top third | 58 / 48 / 68° | 44 / 51 / 55° | 44 / 49 / 47° |
| limbs > 2 cm below 0.5 H (of which within 45° of the stem) | 5 (2–16), ascending 2.5 (0–8) | 18, ascending 10 | 14, ascending 5 |
| branch wood ≥ 1 cm diameter | 869 m (482–1319) | 70 m | 130 m |

What the Nordic scans say so far:
- The model has about a tenth of the branch wood of 1 cm and more of a real stand birch of the same height. It has half the limbs over 2 cm, and its biggest limbs are half as thick relative to the stem (90th-percentile ratio 0.32 against 0.67).
- This is the same gap as against the Belgian hedgerow trees (phase 10), now confirmed on Nordic stand trees.
- The model's low limbs are not too few at 20: it has more limbs over 2 cm below 0.5 H than the scans (18 against 5). The difference is in the crown above.
- The scans' lowest branch over 2 cm sits at 0.03–0.46 H (median 0.04). TLS records dead branches and understorey too, so this needs the scans' point clouds checked before it is used.
- Six trees, all in the shorter half of the selection, are a preliminary sample.

**iNaturalist photos.**
- 13 of the 43 silver-birch `whole_tree` photos in `../tree-data/inat-photos` show the whole tree (crown top and stem base in frame). They are listed in `reference/CREDITS.md` with author, licence and link, and read from that folder, not copied.
- 3 are leafless (#22 park tree, #24 edge group, #40 dying with a dead top); 10 are in leaf.
- Nearly all are open-grown or edge trees: crowns reach far down the stem through long ascending limbs with an even veil of twigs. The model's stand trees are bare to about 0.6 H, with clustered twigs at the top.
- The like-for-like model is the open-grown mode, which is on hold.

## Phase 11: leader damage, a plot of real competitors, winter crowns, root buttresses

**Leader damage** (`leader_damage`, on by default).
- Moose browsing: 16.8 %/yr of leaders between 0.3 and 3 m (Bergqvist, Bergström & Wallgren 2014, Silva Fennica 48:1077, southern Swedish young birch stands).
- The leader's last annual shoot dies; the two uppermost buds or young laterals within 0.5 m take over with the stem's vigour and posture target. Forks and crooks emerge from growth.
- No published yearly rates were found for late frost, snow or wind breakage of the top, so they are not included.

Stand seeds 1–20 at 22 years:

| | forked | crooked | leader losses / tree | H |
|---|---|---|---|---|
| no damage | 0 % | 0 % | 0 | 18.2 m |
| moose browsing | 20 % | 45 % | 0.8 | 15.8 m |
| published | 38.6–41.7 % with a stem defect (fork or vertical branch) at 22, local Finnish provenances (Viherä-Aarnio & Velling 2008, Silva Fennica 42(5)) | | | |

**Plot of real competitors** (`treegen/plot.py`, `tools/plot.py`).
- 100 trees at 1800/ha on 556 m² (25 at 450/ha after thinning), each its own simulation.
- One periodic light field from all trees' leaves; each tree's soil-water field also holds the others' absorbing roots.
- Trees differ in seed, germination year (0–3, weights 0.4/0.3/0.2/0.1; VERIFY) and a lognormal growth factor on carbon gain (SD 0.06; VERIFY).
- Thinned from below to the programme density by dominant height.
- Memory: about 290 MB peak for one stand tree at 60, so a 25-tree plot (100 trees until the first thinning) was estimated at 3–3.5 GB and fits at full resolution.
- Both full runs reached year 15 and were stopped there:
  - the 25-tree run (403 s, peak 2.3 GB) was stopped by hand when another program took 7.9 GB and system commit reached 26.7 of 27.2 GB;
  - a 20-tree rerun (226 s, peak 1.7 GB) was stopped by Claude Code's low-memory guard.
- **Plot results to 60 are pending a run on a quiet machine** (the 20-tree run needs about 3 GB at 60, plus about 0.8 GB more while each tree is exported). The 20-tree run gave the same picture as the 25-tree one: at 15 years 990/ha, DBH 15.7 ± 2.9 cm (CV 19 %), LAI 3.34.

| year | stems/ha | DBH mean ± SD | CV | LAI |
|---|---|---|---|---|
| 10 | 1800 | 6.1 ± 3.0 cm | 50 % | 2.33 |
| 15 | 1008 (thinned from below) | 15.7 ± 3.0 cm | 19 % | 3.32 |

Against the clone stand (20 single-tree stand seeds, round-10 defaults), whose DBH CV is only 2–6 % at every age because every neighbour is a copy:
- DBH spread, published: Gini 0.09–0.13 (≈ CV 16–23 %) in a planted, fenced Swedish silver birch spacing trial at about 33 years (Skräddarbo, Sala; Romans 2023, SLU MSc thesis); CV 32 % (45 years, 880/ha) and 12 % (67 years, 420/ha) in two German stands (Hagemeier & Leuschner 2019, Forests 10:925, Table 2).
- The plot's 19 % CV after the first thinning is in that range.

**Sparse winter crowns: the cause was the render.**
- The round-10 stand render drew the central 20 trees with hero meshes and the 8 surrounding copies with `tree_reduced.glb`. That mesh drops every branch under 1.09 cm radius (50k of 440k triangles), so every tree beyond the patch had no twigs at all.
- Re-rendered with hero meshes for every tree in view to 120 m, framed like the photos (level camera; Sony RX100 at 10.4 mm, f = 1513 px; horizon row from the farthest stem bases), the stand gets the fine-twig haze of the photos.

Sky fraction by elevation angle, one classifier for photos and renders (blue-dominant pixel; render sky painted in the photos' measured sky colour):

| elevation | Gullmarsskogen 1 / 5 / 6 | model, matched render |
|---|---|---|
| 5–15° | 12.8 / 13.5 / 12.1 % | 11.9 % |
| 15–25° | 37.4 / 48.5 / 39.5 % | 19.0 % |
| 25–35° | 45.0 / 61.3 / 53.8 % | 42.9 % |
| 35–45° | 60.0 / 67.9 / – % | 55.6 % |

The model is now as dense as the photos, or denser, at every elevation. The round-10 measure (bands from the top of differently framed images) was confounded by framing and is withdrawn. In leaf (same framing, plain leaf cards) the canopy is closed: sky fraction 7 / 1 / 5 / 17 %. The photos are leafless, so there is no summer reference.

Still different in the matched render:
- the model stems are all alike, straight, grey and thicker;
- the photos show long, ascending limbs lower on the stem, crooks and forks, and stems of every size;
- the model reads as a plantation of clones.


Structure checked against measurements (seed 1 stand):
- Crown leaf-area density by 2 m layer (leaf area / crown-envelope volume, as Hagemeier & Leuschner 2019, Forests 10:265, measured it; their birch fit 0.142 + 2.91 x^9.02):

| age | 0.5–0.85 H | top tenth |
|---|---|---|
| 30 (22 m) | 0.18–1.54 (fit 0.14–0.79) | 1.82 (fit 1.74) |
| 45 | 0.10–1.04 (fit 0.15–0.88) | 0.58–0.81 (fit 1.7–3.3) |
| 60 | 0.06–0.55 (fit 0.14–0.82) | 0.55–0.70 (fit 1.5–2.7) |

- Twig lifespans after age 30: order-2 axes shed at a median 10–15 years, order 3+ at 8.
- Every shed branch failed the light test (none the carbon test, apart from 7 after age 45).
- In the dense phase (10–20 years, 1800/ha, stand LAI 3.1–3.5) twigs die at 2–3 years, at bud light 0.13–0.19. That is ordinary self-pruning under a closed young canopy.
- At 30–60 years, LAI 3.5–4.0 (measured 3.6 and 5.4) and the leaf area per layer is in the measured range. Only the top tenth of the crown is too thin.

**Young-stand LAI by age** (20 clone-stand seeds, mean and range; Estonian stands aged 14–45: 2.5–4.4):

| age | 10 | 12 | 15 | 18 | 20 | 25 | 30 | 40 | 50 | 60 |
|---|---|---|---|---|---|---|---|---|---|---|
| LAI | 3.55 | 3.87 | 2.73 (2.12–3.49) | 3.05 | 1.80 (1.32–2.28) | 3.23 | 4.05 | 4.09 | 4.37 | 4.55 |
| stems/ha | 1800 | 1800 | 1000 | 1000 | 450 | 450 | 450 | 450 | 450 | 450 |

- The low values come right after each thinning: the programme removes 44 % and then 55 % of the stems.
- The 2.2 at 15 quoted in phase 10 was seed 1 alone.
- The plot (real competitors) had LAI 3.32 at 15, after its first thinning.

**Base flare follows the roots** (`geometry.root_flare_mode: buttress`).
- Each main structural root (a root leaving the stem/taproot axis below ground) raises a ridge on the stem at its own azimuth.
- The ridge stands out by the root's radius at the ground line, spans the arc the root covers on the stem, and fades smoothly upwards. The largest root's ridge reaches the uppermost root collar: 0.4862 DBH[cm] + 0.4979 H[m] cm for birch (Laasasenaho 1982; relative SE 44 %), 29 cm at DBH 29 cm / H 29 m. Smaller roots' ridges stay proportionally lower.
- Seed 1 stand at 60 has 7 main roots, 1.4–5.6 cm in radius. Mesh sections against each mesh's own radius at 1.3 m:

| height | old bell | buttress ridges |
|---|---|---|
| 0.02 m | +32 % all round | mean +11 %, ridges to +33 %, troughs −3 % |
| 0.10 m | +40 % | mean +12 %, ridges to +28 % |
| 0.30 m | +27 % | +5 % |
| 0.50 m | +15 % | +3 % |

- The uniform bell remains as the fallback for meshes without roots.
- Not sourced: ridge width and height in proportion to root size (VERIFY). The ridges are modest because the model's main roots are thin: their cross-sections at the collar sum to 280 cm², against 742 cm² of stem.

**Numbers at 50 and 60** (20 clone-stand seeds, round-10 defaults: no browsing; these are the trees in the stand renders):

| age | DBH | H | crown base | LAI |
|---|---|---|---|---|
| 50 | 29.5 ± 1.4 cm | 27.8 m | 14.8 m | 4.37 (3.48–5.16) |
| 60 | 31.6 ± 1.6 cm | 29.5 m | 16.9 m | 4.55 (3.46–5.71) |

With browsing on, the trees are about 2.4 m shorter at 22. Runs to 60 with the combined defaults (browsing, buttresses, plot) were not made in this round (memory).

**Still open after phase 11:**
- The plot to 60: DBH distribution, fork and crook shares among real competitors, and plot renders.
- Forks: 20 % of browsed stand trees at 22, against 39–42 % with a stem defect in Finnish trials. Late frost, snow and wind breakage are missing for want of sourced rates.
- The near-fork ratio (largest branch / stem diameter) in the scans is 0.72–0.91; in the model it is 0.36 (stand) and 0.45 (open) at 17 m.
- Long, ascending limbs low on the stem, as in the photos, are missing. Stand limbs stay short and their twigs sit in dense clusters (leaf-area density about 7 m² m⁻³ within 0.25 m of a twig bud at 12–16 years).
- The top tenth of the crown carries too little leaf area (0.55–0.8 against 1.5–3.3 m² m⁻³ measured).
- Reduced meshes have no fine twigs (see README). A distant tree needs the hero mesh or twig cards.

## Phase 10: limb death, limb wood, stand renders

**What killed limbs** (seed 1 stand, every first-order limb shed after age 30, logged at death):
- Of 138, 111 died of light at 0.19–0.20, and they were young (median 11–18 years) and high (0.80–0.84 H), in the shade of the reiterated head.
- Old lower limbs were mostly not shed. They went leafless: short shoots died at a fixed age of 8 years (`spur_lifespan`, unsourced), and limbs whose meristems had aged could not make new ones.

Death now comes from light and carbon, and ageing only lowers vigour:
- short shoots and branches die below 21 % light, the measured light of the lowest birch shade leaves (Hagemeier & Leuschner 2019);
- a branch whose own leaves no longer fix enough carbon to pay the upkeep of its wood is shed (`shedding.carbon_balance`);
- short shoots have no fixed lifespan.

Seed 1 stand at 60: crown base 0.65 → 0.53 H, LAI 2.95 → 4.05 (measured 4.6), light at the lowest leaves 0.35 → 0.24 (measured ~0.21), floor 0.36 → 0.24 (measured 0.15).

**Limb wood.** The ring allocation does what Pressler and the pipe model say:
- every living node with leaves beyond it adds a ring each year, at one constant ring area per unit leaf area (2.46e-5 m²/m² at age 25);
- wood never decreases, so the wood of shed twigs stays;
- 127 of 219 limbs at 25 are held at the pipe-model floor.

Stand limbs are thin because each carries little foliage. At 17 m the stand tree has 36 m² of leaves over 164 limbs (median share 0.2 %, largest 4.6 %); the open-grown tree has 315 m².

First-order branches by base diameter at about 17 m:

| | 1–2 / 2–3 / 3–5 / 5–10 / >10 cm | largest branch / stem diameter |
|---|---|---|
| scans, 16–19 m (4 hedgerow birches) | 6–17 / 5–23 / 14–35 / 8–36 / 1–6 | 0.72–0.91 |
| model, open-grown, 17.2 m | 66 / 21 / 21 / 21 / 0 | 0.45 |
| model, stand, 17.5 m | 32 / 6 / 0 / 0 / 0 | 0.36 |

- The open-grown model, the like-for-like match for hedgerow trees, matches the scans from 2 to 10 cm.
- Missing in every mode: limbs over 10 cm and near-forks (largest branch near the stem's diameter).
- In the stand, young-stand LAI is low: 2.2 at 15 years and 1.6 just after the thinning to 450/ha, against 2.5–4.4 in Estonian stands. That leaves too little foliage per limb.
- Carbon-balance death also halves the number of limbs over 2 cm at 60 (67 → 26–36): old limbs whose wood costs more upkeep than their few leaves fix are shed.

**Stand seeds 1–3 at 60:**
- crown base 0.53 / 0.31 / 0.64 H (stand photos 0.32–0.6);
- LAI 4.05 / 4.65 / 3.46 (measured 4.6);
- H/D 100 / 90 / 99;
- DBH 29.3 / 33.1 / 29.7 cm;
- lean 2.1 / 2.7 / 2.5°;
- no base twigs (lowest live branch 7.9–12.5 m).

**Stand render.** 20 seeds at 450 stems/ha, viewed from the forest floor at eye level and framed like the Gullmarsskogen photos (the patch is repeated around itself, at reduced detail, to fill the background); a summer version uses plain leaf cards at the stored short shoots.

It reads as a birch stand at first glance: many slender pale stems, crowns high, a fine-twig haze above.

Against the photos:
- the crowns carry much less fine twig mass;
- stems are smoother and straighter (no crooks);
- stems are thicker for their height;
- the stand is thinned to 450/ha, while Gullmarsskogen is an unmanaged reserve with more stems.

## Phase 9: light in the stand, stem lean, laser-scan branch reference

**Stand light, against measurements.** Hagemeier & Leuschner 2019 (Forests 10:925) measured two closed *B. pendula* stands (45 and 67 years, 880 and 420 stems/ha, 20–25 m):
- forest-floor PAR 14.8 % (6.4–19.8 %);
- lowermost shade leaves at ~21 %;
- LAI 4.6, K_PAR 0.37, clumping index 0.42.

Neighbour shade in the model was already leaf area along the light path: neighbours are copies of the focal tree's leaves, not volumes. What was off was the shade per leaf area. The model used k = 0.5 (spherical leaves); it now uses the measured 0.37.

| seed 1 stand, age 60 | k 0.5 | k 0.37 (default) | measured |
|---|---|---|---|
| bud light, crown top | 0.68 | 0.70 | ~1 |
| bud light, mid crown | 0.31 | 0.34 | – |
| bud light, lowest leaves | 0.34 | 0.35 | ~0.21 |
| stand floor, 1.5 m | ~0.35 | 0.36 | 0.15 (0.06–0.20) |
| LAI | 2.18 | 2.95 | 4.6 |
| lowest live branch | 0.17 m | 6.7 m | – |

- The measured coefficient raises LAI by a third and kills the seedling-era base twigs; seed 3 keeps one.
- The floor is still twice as bright as measured, because LAI is still lower. The lowest leaves sit at 35 % light, well above the 21 % at which birch shade leaves die, yet the crown base stays at 0.65 H. Lower limbs die of meristem ageing (`branch_aging_years` 20, with inheritance), not of shade. That is the next lever for crown base and LAI.

**Stem lean.** Posture control was already growth-limited (rate ∝ C ṙ/r², Alméras & Fournier). It removed every lean because it always aimed at vertical. Seed 1 stand at 60, lean from base to top:

| posture control | lean |
|---|---|
| none (upper bound of the lean forces) | 4.4° |
| sine law, no saturation | 0.6° |
| sine law, full above 10° | 0.27° |
| same, half the reaction-wood asymmetry | 0.30° (limbs sag to 65°) |
| same, plus stem posture target tilted towards the crown's light (default) | 1.2° (seeds 1–3: 1.2–2.0°) |

- The leader also turns towards the brighter side of its own crown (`tropism.stem_crown_phototropism`). Its posture target inside the crown tilts by phototropism over gravitropism (0.8/4.0) times the crown's light asymmetry (whole-tree phototropism, Loehle 1986).
- The stem's 4/m gravitropism has no source (VERIFY). Lowering it to 1–2/m did not change the lean.

**Laser-scan branch reference.** 11 leaf-off hedgerow *B. pendula* with TreeQSM models (Van Den Berge et al. 2021, Zenodo 10.5281/zenodo.4487116, CC BY 4.0), each averaged over its 10 QSM repetitions. Note: TreeQSM's `FCB` often points at a branch's second cylinder; the first one is `CiB[0]`. Branch base diameters use the smaller of the first two cylinders, since the first is often inflated where it enters the stem.

| first-order branches | scans (5.5–19 m) median (range) | model age 20 (17 m) | model age 60 (30 m) |
|---|---|---|---|
| > 2 / 5 / 10 cm | 27 (15–94) / 6.2 (2–38) / 0.1 (0–5.8) | 7–18 / 0 / 0 | 67–69 / 2–4 / 0–1 |
| largest branch / stem diameter | 0.93 (0.72–0.95) | 0.32–0.36 | 0.57–0.64 |
| 90th percentile of that ratio | 0.81 (0.54–0.95) | 0.30–0.35 | 0.16–0.19 |
| insertion angle, low / mid / top third | 64 / 63 / 68° | – / 52–55 / 53–55° | 50 / 47 / 46° |
| own length / H, low / mid / top third | 0.11 / 0.11 / 0.09 | – / 0.13–0.14 / 0.10–0.11 | 0.13 / 0.12 / 0.10 |

- Angles and lengths are close.
- The model's limbs are far too thin: no branch over 5 cm at 17 m, where scanned birches of that size carry 11–38. The largest limb is a third of the stem's diameter, where the scans show near-forks.
- Hedgerow trees are more open-grown than stand trees, so part of the gap is expected. Most of it is not: limb wood is too small.

**FOR-species20K** (Zenodo 13255198; licence on the record: GPL-3.0-or-later; not downloaded):
- 735 *Betula pendula* in the development metadata: 171 TLS, 366 ULS and 198 MLS;
- from Puliti a/b (518), Liang 2018 (94), Junttila (43), NIBIO (39), REMBIOFOR (24), Van Den Berge 2021 (8), Weiser 2022b (7) and Luke (2);
- 1.5–30 m tall (median 13.9 m);
- point clouds only, no QSMs. The data are in `dev.zip` (25.4 GB).

## Phase 8: architecture against photographs (stand, open)

Matching the reference photos (`reference/`, Wikimedia Commons, comparison only) is now the main acceptance test; the numbers are a range check.

**Metrics** (fractions of tree height H; photos digitised by hand on a grid, about ±0.03; the model's width and widest point come from its eye-level render, the rest from its geometry):

| metric | stand photos (Brastad ×2, Russia) | solitary photos (Oslo, Meilen, Hallinden) | dense stand (Gullmarsskogen) | model before | model now, seeds 1–3 |
|---|---|---|---|---|---|
| crown width / H | 0.22–0.25, 0.43 | 0.53–0.76 | (tops out of frame) | 0.19 | 0.19–0.23 |
| widest point | 0.64–0.75 | 0.44–0.58 | – | 0.62 | 0.34, 0.95, 0.91 |
| crown base | 0.32–0.6 | 0.20–0.43 | – | 0.72 | 0.61–0.64 |
| major limbs | 3–5 | 4–7 | – | 1 | 4–5 |
| leader | forks in the top 20 % | lost or forked at 0.43–0.85 H | – | dominant, spire | nominal (0.1 m above the next axis) |
| stem lean | 1–3° | 4–11° | 0–5°, median ~3° | 0° | 0° |

**What changed:**
- **Base artefacts.** These were living seedling-year limbs at 0.2–1.5 m, kept alive because shade faded with depth below the canopy (`light.shadow_decay_length` 30 m). Stands now keep their shade below the canopy (`stand.shadow_decay_length`). On the lattice layout the lowest live branch rises from 0.17 to 6.6 m. With random neighbours, a few small twigs survive in gap light (q ≈ 0.3).
- **Random neighbours** (`stand.layout: random`). Hard-core random positions at the scheduled density, relative sizes with CV 0.10, random turns. Light is now uneven, but stems stay straight; see below.
- **Reiteration** (`resource.reiteration`). Loss of dominance is detected once the tree is past 30 and the leader's yearly growth is below half its peak. From then on, the most vigorous well-lit first-order limb in the upper three quarters of the crown becomes a reiterated complex every 5 years: partly rejuvenated, with an orthotropic axis.
  - Literature: Barthélémy & Caraglio 2007; Millet, Bouchard & Édelin 1999, where grey birch keeps a hierarchic architecture, loses dominance into short forks at maturity, and has at most two total reiterates; and the ARCHI "duplication" concept.
  - The thresholds have no published values. A vigour bar relative to the leader was cliff-like: 0.45 gave 13–63 complexes and a broom on a pole, 0.55–0.7 gave none. The sequential rule with a 5-year interval (calibrated to the photos' 4–7 major limbs) gives 7 complexes and 4–5 major limbs.
  - The spire top is gone in all three seeds, replaced by an irregular head. But the complexes sit at 0.63–0.89 H, and the crown below is still a fishbone of short limbs.
- **Stem lean is not solved.** Stems were exactly vertical because posture control removed any deviation every year. A sine-law correction (`mechanics.sine_law`, off) gives at most 0.9° of lean, and it makes limbs sag to 67° (57–60° with saturation at 10°) against the measured 43°.
  - The deeper cause: nothing pushes the stem. At the top of the canopy the leader's phototropism sees open sky in every direction, and the stem's gravitropism (4/m, VERIFY) removes the sympodial deflections within each year.
  - Candidates for next time: leader phototropism from the sky view, or a weaker stem gravitropism with sources.

**Range check, stand seeds 1–3 at 50 / 60:**
- Height 27.3–27.7 / 28.8–29.5 m: still over the band by about 2–2.6 m (nitrogen and season missing).
- DBH 23.5–26.1 / 25.0–27.9 cm.
- H/D 106–118: above the 80–100 target.
- LAI 2.18–2.90: seed 1 below the 2.5 published minimum. Less light reaches the lower crown now that shade no longer fades.

## Phase 7: the carbon budget (seed 1)

Several results pointed to one cause: the tree was short on carbon. The changes, tested one at a time and then combined on seed 1, are now defaults. Carbon is in model resource units (about one metamer each).

| step | change | stand at 60: H / DBH / H/D / LAI / carbon |
|---|---|---|
| – | phase-6 defaults | 22.8 / 15.7 / 145 / 2.51 / 18.9k |
| 1 | own-shoot shade excluded from bud light | 24.4 / 17.0 / 144 / 2.65 / 21.0k |
| 2 | Huber fix (additive sapwood, 1.24e-4) alone | 17.6 / 13.7 / 128 / 2.11 / 16.8k |
| 2 | Huber fix + root uptake ×2 | 25.5 / 21.1 / 121 / 3.55 / 32.5k |
| 1+2 | combined | 26.0 / 21.9 / 119 / 3.33 / 32.7k |
| 1+2+3 | + full rings | 21.6 / 27.7 / 78 / 1.62 / 16.6k |
| 1+2+3 | + full rings with the pipe floor | 26.9 / 30.6 / 88 / 3.38 / 31.9k |
| 4 | + limbs inherit stem age, 43 deg limbs | 31.8 / 29.8 / 106 / 3.32 / 25.3k |

- **Own-shoot shade** is subtracted exactly: the light propagation is linear, so its impulse response gives the shade a shoot's own leaves cast. It is only about a quarter of the shade on outer buds (surface q 0.65 → 0.71). Still, carbon rose 50 % open and 11 % stand at 60.
- **Huber value:** hydraulics had merged leaf pipes with the branching exponent 2.5. That made conducting area 4× the published value at the shoots and made it fall toward the stem. It now counts additive pipes, 1.24e-4 m² of xylem per m² of leaf (Õunapuu-Pikas et al. 2022), capped by the wood.
- **Root uptake:** Sellin's 5-year saplings put the whole-tree conductance gap in the roots, which took 85–93 % of the sapling's water-potential drop. Root uptake per metre is now calibrated to Sellin's soil-to-branch conductance (2.28 mmol m⁻² s⁻¹ MPa⁻¹).
  - Sapling ψ_top is now −0.87 to −0.94 MPa (Sellin: −1.07), and stomatal opening at 60 is 0.80–0.85.
  - Sapling K_T is still about half Sellin's (0.57 against 1.15). Transpiration per leaf area is also half (0.48 against 0.92 mmol m⁻² s⁻¹).
- **Full rings** collapsed the crown not because of the budget but because of stiffness. Rings gave limbs only their leaf-area share of wood, about 40 % thinner than the pipe model, so 6–10× less stiff. At age 40 the limbs pointed down. The floor "wood is never thinner than the pipes it carries", already used on the stem in stem-rings mode, fixed it.
- **The twin top** came from meristem ageing. A limb born at 45 near the top counted its age from zero, so it was 2.4× as vigorous as the 45-year-old leader and overtook it by 1.1–1.4 m at 60, in every run checked. Limbs now inherit the stem's physiological age at birth (Barthélémy & Caraglio 2007), and the leader stays on top. The stand tree then overshoots the height band by about 5 m. See "Next phase" for nitrogen and season.
- **Limb angles:** the old 25 deg set-point was chosen to hit a crown width, and stiff ring-grown limbs held it exactly (median 25 deg), which gives the poplar look. Insertion and set-point are now the measured 43 deg (Forests 9:52, 2018). The realised median is 43 deg with the angle alone and 54 deg with inheritance, where weaker limbs bend further.

## Next phase: what holds boreal height growth back (open)

The phase-7 carbon fixes put stand seed 1 at the top of the Swedish height band at 60: 26.9 m against 21.1–26.9 m (Eriksson et al. 1997). The open-grown tree overshoots it: 30.0 m with steps 1 and 2. No height limit was added.

The model has a water limit only. Boreal tree growth is mainly held back by two things it does not have yet:
- **Nitrogen.** Most Nordic forest soils are nitrogen-limited.
- **A short, cold growing season.** Shoot extension and cambial activity stop with temperature and day length.

Both belong in the environment and the carbon budget, not a height cap.

## Open-grown trees: on hold (base limbs)

Open-grown trees are on hold, since most of the forest is stand-grown. In open ground, the seedling-era limbs attached in the first metre stay dominant: they are never shaded out (see "Open-grown crown reads as a bottle brush"). Neither branch autonomy nor the herb layer fixed this. No more batches will be spent on it until stand mode is settled.

## Open-grown crown reads as a bottle brush (open)

A mature open-grown silver birch has a handful of dominant ascending limbs, an
open inner crown and most of its foliage on the outer shell. The model's crown
at 60 years has many limbs of the same size instead.

**Diagnosis** (phase-3 model, 10 seeds, age 60; `stats.json` → `scaffold`):

| | model | mature birch |
|---|---|---|
| living first-order limbs | 285–318 | a few dominant ones plus small ones |
| limbs over 5 cm / over 10 cm | 43–59 / 0–1 | a handful over 10 cm |
| five largest limbs | 8–9 cm each | dominant limbs much thicker than the rest |
| leaf share of the 5 biggest limbs | 13–17 % | most of the crown |
| leaf share in the inner 40 % of crown radius | 18–23 % | low (open interior) |
| leaf share in the outer shell (≥ 60 % radius) | 44–47 % | most |
| leaf area by height | even from 30 % to 100 % of height | concentrated in the upper crown |

**What was tried** (seed 1, age 60; height band 21.1–26.9 m):

| run | change | height | limbs | > 10 cm | top-5 leaf share | inner / outer |
|---|---|---|---|---|---|---|
| E0b | none | 21.4 | 305 | 0 | 15 % | 21 % / 45 % |
| E1 | branch ageing 20 → 60 y | 17.2 | 329 | 4 | 25 % | 23 % / 57 % |
| E3 | E1 + old apical control 0.50 → 0.42 | 10.7 | 238 | 4 | 43 % | 14 % / 65 % |
| E4 | shade death 0.20 → 0.30 | 20.0 | 135 | 2 | 21 % | 19 % / 50 % |
| E5 | E4 + branch ageing 35 y | 17.3 | 154 | 2 | 22 % | 21 % / 56 % |
| E6 | E5 + old apical control 0.46 | 13.2 | 131 | 5 | 35 % | 12 % / 72 % |
| E7 | E4 + stem ageing 45 → 70 y | 21.0 | 169 | 2 | 19 % | 19 % / 49 % |
| E8 | shade death 0.35 | 19.1 | 95 | 4 | 26 % | 16 % / 57 % |
| E9 | E5 + gravimorphism 1.0 → 1.6 | 18.7 | 187 | 3 | 20 % | 22 % / 53 % |
| E10 | E9 + stem ageing 70 y | 19.6 | 228 | 4 | 21 % | 23 % / 52 % |

Every variant either changes little or starves the leader. Limbs and the leader
draw on one shared Borchert–Honda pool. Stronger shade death cuts the limb count
in half, but vigour never concentrates in a few mid-crown limbs. Whenever limbs
keep their vigour longer, the oldest, lowest limbs win and the leader loses.

**Branch autonomy** (Sprugel, Hinckley & Schaap 1991) is implemented and
switched off (`resource.branch_export_fraction: null`). With it, each limb lives
on its own carbon, exports a fraction to the stem and is shed when it cannot pay
its upkeep; water stays shared. One batch (export 0.1, 0.2 and 0.35, and with
shade death 0.30):

- The leader holds: height 24–26 m at 60, inside the band.
- But foliage moves to the bottom. The biggest limbs sit 0.1–3 m up and 77–97 % of the leaf area is in the lowest 40 % of the height. Limbs born on the leader are self-funding from their first year, so they never establish. In a stand, the tree overshoots to 29.6 m with a crown ratio of 1.0.

**Branch autonomy with young-limb import** (`resource.young_limbs_import`) was
tried next. A young limb draws its Borchert–Honda share from the stem pool until
its own carbon covers what it drew the year before; then it runs on its own
budget. Two batches on seed 1 at age 60. The first ran autonomy alone (C1a, C1b);
the second ran it with pre-dawn turgor and the ground-contact, root-avoidance and
taproot fixes (X1, X2):

| run | export | height | 5 biggest limbs attached at | top-5 leaf share | leaf share at 30–70 % of height |
|---|---|---|---|---|---|
| base | – | 21.1 | 5–13 m | 14 % | 52 % |
| C1a | 0.1 | 19.8 | 0.1–0.9 m | 46 % | 57 % |
| C1b | 0.2 | 20.5 | 0.1–10 m | 28 % | 43 % |
| X1 | 0.1 | 19.0 | 0.1–0.9 m | 39 % | 57 % |
| X2 | 0.2 | 20.1 | 0.1–1.0 m | 23 % | 54 % |

- Young-limb import does let the mid crown develop: leaf share at 30–70 % of height rose from about 20 % without import to 54–57 %.
- But the dominant limbs are still seedling-era branches attached in the first metre. They become self-funding early and are never shaded out in an open field. They ascend from the base, so the rule that kills branches lying in the ground layer does not catch them.
- The leader also drops below the height band.
- Autonomy stays off. A likely next step is shade from the herb layer (ground vegetation) on foliage in the first metre: open-grown birch self-prunes those first branches in its first decade, and the open-field light model has nothing that does it.

**Herb layer, then autonomy with young-limb import** (phase 6). The field layer
is a Beer–Lambert layer 0.6 m tall with leaf-area index 3 and extinction 0.4
(`environments/sweden_open_field.yaml` → `ground_vegetation`, Monsi & Saeki
1953). Light at height z is multiplied by exp(−0.4 · 3 · (1 − z/0.6)). Seed 1:

| run | mode | height 50 / 60 | DBH 60 | 5 biggest limbs attached at (60) |
|---|---|---|---|---|
| base | open | 20.4 / 21.6 | 29.7 | 5–12 m |
| herb layer | open | 14.5 / 16.9 | 26.1 | 4–9 m |
| herb layer + autonomy | open | 14.4 / 16.4 | 23.7 | 0.7–1.3 m |
| base | stand | 20.1 / 21.9 | 17.1 | 13–18 m |
| herb layer | stand | 13.9 / 15.9 | 15.2 | 8–12 m |
| herb layer + autonomy | stand | 15.2 / 17.1 | 13.3 | 9–11 m |

- The herb layer alone does not deform the crown, but it holds the seedling back for about 8 years, and the tree ends 5–6 m below the height band.
  - Its first leaves sit inside the layer at 10–30 % light, so its first-year carbon is a fraction of the open-field value.
  - A real birch seedling on an unmown field also grows slowly, so the direction is right. Height at 50–60 then depends on the seedling years, which have no calibration data here.
  - The seedling died at first: its radicle stopped counting as an absorbing root after 3 years, before any lateral had grown. Living root tips now always absorb.
- With autonomy on top, the seedling-era base limbs still win in open ground. The five biggest limbs at 60 are attached 0.66–1.33 m up and carry the crown.
  - These branches start inside the herb layer but grow out of it within a few years. Above 0.6 m they are in full light and self-funding again.
  - The herb layer shades a branch only while it is young. Real birch sheds these limbs over decades as the crown above shades them, and in the model the open crown above never shades them enough.
- Both stay off (`ground_vegetation.enabled: false`, `branch_export_fraction: null`).

## Combined defaults (phase 6): 3 seeds, ages 50 and 60

The defaults are now:

- sun/shade leaves on (absolute bud light);
- 15 cm² reference leaf;
- xylem conductivity 4;
- stem rings;
- smooth twig arcs (sympodial bend 0.1 m, correlated noise 0.3 m);
- the herb layer and branch autonomy off.

Means over seeds 1–3 (min–max), with the phase-5 defaults in brackets:

| | open 50 | open 60 | stand 50 | stand 60 | published |
|---|---|---|---|---|---|
| height (m) | 21.5 (20.4) | 24.1 (21.3) | 20.5 (20.2) | 22.6 (22.0) | 19.2–25.3 at 50, 21.1–26.9 at 60 |
| DBH (cm) | 21.2 (26.0) | 24.9 (29.3) | 14.0 (15.8) | 15.7 (17.2) | open 30–50 at 60; stand 25–30 |
| crown width (m) | 7.3 (8.1) | 8.7 (9.4) | 5.2 (5.6) | 5.2 (5.7) | from DBH: 4.4 / 5.0 open, 3.2 / 3.5 stand |
| leaf area (m²) | 241 (289) | 278 (304) | 51 (53) | 57 (50) | – |
| LAI | 6.3* | 5.2* | 2.31 | 2.55 | stands 2.5–4.4 (EE), 3.6–5.4 (DE) |
| top leaf ψ midday (MPa) | −1.61 (−1.83) | −1.66 (−1.97) | −1.38 (−1.46) | −1.40 (−1.50) | −1.0 to −1.3 well watered |
| form factor (Laasasenaho) | 0.52 (0.46) | 0.52 (0.46) | 0.62 (0.49) | 0.63 (0.49) | – |
| d 1.3 / 50 % / 75 % height (cm) | 21.2 / 15.6 / 10.5 | 24.9 / 18.5 / 12.2 | 14.0 / 11.7 / 8.7 | 15.7 / 13.4 / 10.1 | – |
| mean hanging twig (m) | 0.88 (0.92) | 1.06 (1.20) | 0.0 (0.12) | 0.20 (0.11) | – |

\* For open-grown trees LAI is leaf area per crown projection.

- **Height** is in the band in every run.
- **DBH fell further below the published bands.** The 15 cm² leaf brings more self-shade and less leaf area per crown volume.
- **Open-grown stems are now too full** (form factor 0.52 against 0.46). The stand stems are still poles.

## Stand trees

- **DBH is too low:** 15.7 cm at 60 with the phase-6 defaults (17.2 in phase 5, about 20 earlier) against 25–30 cm. The neighbours are copies of the focal crown, so they grow with it, and density follows the Swedish programme [SS14]; the schedule did not change DBH. The crown is too sparse (about 60 m² of leaves). Its leaf area per unit of basal area (0.19 m²/cm²) is lower than the open tree's (0.36), so the trunk is not thin for its foliage. In the mid crown the BH resource per bud is close to zero (v ≈ 0.03).
- **Expansion now follows pre-dawn water potential** (soil minus 0.0098 MPa/m of height), and midday water potential only closes stomata. Seed 1 at age 60:
  - Open-grown: the upper crown now weeps (401 hanging twigs against 2, mean 0.76 m) and height stays in the band (21.3 m). But the bigger upper leaves transpire more, so midday leaf water potential drops to −2.0 MPa, stomatal opening falls from 0.71 to 0.60, and DBH falls from 35.3 to 29.5 cm.
  - Stand: DBH falls from 20.0 to 17.6 cm and leaf area from 59 to 54 m². There are still no hanging twigs in the stand's upper crown.

## Anchorage (resolved)

Phase 5 tried to get overturning resistance from the simulated root plate. The rule for the plate radius mattered more than anything else, since resistance grows with the cube of the radius. No rule landed in the published range: the end of the taper zone gave 5× too little in open trees and 14× too little in stands. The taper zone stays as the root data have it (2.2 × DBH), so the visible root shape follows the roots, not the anchorage figure.

The **critical turning moment** is now computed the way ForestGALES does it: an empirical regression of tree-pulling moments on stem size.

- **Regression:** M = 101 kN m per m³ of stem volume. This is a least-squares fit through the origin to the silver-birch pulling means of Krišāns et al. 2022: 0.67 m³ → 46.9 kN m and 1.43 m³ → 154.3 kN m.
- **Rooting depth:** the deepest root within 1.5 m of the stem (capped by the soil), divided by the 0.85 m depth of the uprooted plates in Krišāns et al., clipped to 0.5–1.2.
- **Root asymmetry, per wind direction:** half of the moment comes from windward root tension (Coutts 1986). That half scales with the windward roots' tension capacity relative to their mean over all directions.

It is reported in `stats.json` → `anchorage.critical_turning_moment` and on the USD Roots prim (`treegen:criticalTurningMoment*`). Seed 1, against M = (25–38) kN m/m³ × H × DBH² (the scaling of the same pulling data):

| | weakest direction – mean (kN m) | H × DBH² range (kN m) |
|---|---|---|
| open 40 | 22–43 | 23–36 |
| open 60 | 57–81 | 47–72 |
| stand 40 | 11–20 | 9–13 |
| stand 60 | 21–39 | 16–24 |

The mean runs at or a little above the H × DBH² range. The stand stems carry too much volume for their DBH (form factor 0.66 against 0.48, see Stem form), and the regression is on volume.

## Sun and shade leaves (phase 6)

Each short shoot takes its leaf size and LMA from its light (`light.sun_shade`):

- LMA = 50.5 + 38.7 q^3.3 g m⁻². This is the vertical LMA profile of adult birch in Hagemeier & Leuschner 2019, with relative light q in place of relative height.
- Leaf size goes as 15 cm² × (60.8 / LMA), so every leaf has the same dry mass. The 15 cm² reference leaf and 60.8 g m⁻² mean shoot LMA are from Õunapuu-Pikas et al. 2022: 167 cm² of leaf on a 27.9 cm current-year shoot.

Both are stored per short shoot in the timeline.

**On the absolute exposure, the gradient was unstable.** Seed 1, LMA in the top 10 % of height against the lowest decile of leaves:

| run | age 50 | age 60 |
|---|---|---|
| sun/shade alone, 12 cm² leaf | 62 / 54 | 83 / 55 (top leaves 8.8 cm², lowest 13.4 cm²) |
| combined (15 cm² leaf, k_s 4, stem rings, twigs) | 57 / 57 | 56 / 59 |

In the combined runs even the outermost leaves came out as shade leaves. Leaves within 0.25 m of the top of their 0.5 m column averaged q 0.67 and LMA 62, and the top metre of the tree averaged LMA 59.

- **Cause:** the model's bud exposure tops out at about 0.6–0.7 even on the crown surface, because each bud sits in the shade of its own shoot cluster (leaf-area density 5–6 m² m⁻³ in occupied 10 cm voxels near the top).
- **Feedback:** shade leaves are larger, so they cast more shade, which makes more shade leaves. Near q = 1 the size response is steeper than 1:1, so the top of the crown can flip between a sun state and a shade state from year to year.

**What was tried** (seed 1, combined settings):

- **Exposure relative to the 99th percentile of the year's bud exposures** (`sun_reference_percentile: 99`): no better. The top 10 % of height averaged LMA 60 against 65 low in the crown (open, age 60). The best-lit 1 % of buds are isolated tips already near q = 1, and the bulk of the outer shell stays at about 0.5.
- **The same reference applied to the shoot and branch light thresholds:** no material change; stand LAI was 2.6.
- **Not yet tested:** leaf traits from the light reaching the shoot from above (`sun_shade.light: above`). This is shade from one voxel up, without the shoot's own cluster, the way LMA–light relations are measured (canopy openness at the shoot). The test run was stopped when the machine ran low on memory.

**State:** sun/shade leaves are on and stored per short shoot. They span the published LMA range (51–83 against 50–89 g m⁻²), but the vertical gradient is flat, or slightly inverted in open-grown crowns.

## Stand leaf-area index (phase 6)

LAI = leaf area × stems per hectare. Published values for mature birch:

- 2.5–4.4 in Estonian silver-birch stands aged 14–45;
- 3.6 and 5.4 in two German birch stands (Hagemeier & Leuschner 2019).

| | age 50 | age 60 |
|---|---|---|
| model (3 seeds, combined defaults) | 2.31 (2.26–2.34) | 2.55 (2.51–2.60) |

That is at the bottom of the Estonian range and below the German stands. The same local over-shading that flattens the sun/shade gradient limits it. Short shoots die below 20 % light, the published shade-leaf light demand. If the canopy top sat at q = 1 with k = 0.5, that threshold would allow an LAI of ln 5 / 0.5 = 3.2. The model's outer shell starts at about 0.6, so the canopy fills only to about 2.4.

A calibration through the light model's VERIFY parameter for leaf spread (`light.leaf_spread` 0.06 → 0.10 m) was queued but stopped with the memory shortage. The stand DBH deficit (15.7 cm at 60) follows from the same small crown.

## Stem form and annual rings (phase 6)

There are three ways to grow radii (`pipe_model.growth`):

- `pipe` recomputes every radius each year from the pipes to the current foliage, plus disused pipes.
- `rings` lays down the year's wood (a share of the shoot carbon) as rings on every internode, in proportion to the leaf area beyond it (Pressler; LIGNUM).
- `stem_rings` keeps the pipe model for branches. On the stem, each internode in the crown adds the growth of its pipe area, and one below the crown base adds the crown-base ring (Pressler). This is the default now.

The comparison below uses the Laasasenaho (1982) birch volume function: V = 0.011197 d^2.10253 0.986^d h^3.98519 (h − 1.3)^−2.659 dm³, as implemented in the `forester` R package. Its form factor is V / (basal area × height). The taper-curve polynomial coefficients for birch could not be found outside the 1982 monograph.

Seed 1, age 60 (diameters in cm, form factor in brackets against Laasasenaho):

| run | mode | d 1.3 m | d 50 % height | d 75 % height | form factor | leaf area |
|---|---|---|---|---|---|---|
| pipe (old) | open | 29.7 | 19.1 | 11.1 | 0.45 (0.43) | 315 m² |
| stem rings | open | 29.5 | 18.8 | 11.0 | 0.46 (0.43) | 306 m² |
| full rings | open | 25.8 | 12.0 | 5.7 | 0.34 (0.45) | 56 m² |
| pipe (old) | stand | 17.1 | 14.9 | 11.3 | 0.66 (0.48) | 53 m² |
| stem rings | stand | 17.8 | 15.2 | 11.5 | 0.64 (0.48) | 53 m² |
| full rings | stand | 16.6 | 9.9 | 4.8 | 0.42 (0.48) | 28 m² |

- **Open-grown taper is already close to Laasasenaho** (0.45 against 0.43), with any method.
- **The stand stem is a pole:** d at 75 % of height is 2/3 of DBH, and the form factor is 0.66 against 0.48. Stem rings barely change it: DBH rises 0.7 cm.
  - The cause is that stand foliage hardly grows after canopy closure (50–57 m² from age 35 on in the phase-5 run). The pipe model then adds stem wood only through the disused pipes of shed branches, which also thickens the upper stem.
  - Rings would thicken the lower bole only if each year's ring were larger than the year's growth of pipe area, that is, if wood were laid down from carbon rather than from new foliage. That is the full-rings method.
- **Full rings starve the twigs.** With a fixed wood volume per unit carbon, the finest shoots get rings far thinner than their pipes. Twigs end up too thin to hold their foliage, and the crown collapses to 56 m² (open) and 28 m² (stand) of leaves. Making it work needs a separate allocation of carbon between twig extension and stem rings, which the model does not have.
- **Ring widths per year** are in the timeline (`shoot_ring_node`, `shoot_ring_count`, `shoot_ring_width_m`, and the same for roots) for every internode thicker than 1 cm, with the year of each ring.

## Twigs (phase 6)

The wiggle in fine hanging twigs did not come from direction noise. On seed 1 (open, 60), 40 % of fine-twig internodes are year joints: an annual shoot has only about 2.5 internodes. Each year joint takes the sympodial deviation (8°) as one kink.

- Correlated direction noise alone (an Ornstein–Uhlenbeck process along the shoot, 0.3 m correlation length) changed nothing visible.
- **The fix** spreads the sympodial deviation as a curvature over the first 0.1 m of the new shoot (`architecture.sympodial_bend_length_m`), together with the correlated noise.
- The median turn per internode on hanging twigs fell from 7.8° to 3.4°, and the median sinuosity from 1.022 to 1.016. Height, DBH and leaf area changed by less than 1 %.

## Hydraulics check (phase 6)

Seed 1, age 60, against published silver-birch values. "Shoot" is a branch tip carrying 120–250 cm² of leaves, about a current-year shoot (Õunapuu-Pikas et al. 2022: 167 cm²).

| quantity | model, k_s 2 (old) open / stand | model, k_s 4 (default) open / stand | published | source |
|---|---|---|---|---|
| Huber value, shoot (sapwood / leaf area) | 5.7 / 5.8 × 10⁻⁴ | 5.0 / 5.2 × 10⁻⁴ | 1.24 × 10⁻⁴ | Õunapuu-Pikas et al. 2022, Forests 13:594 |
| Huber value, stem at 1.3 m | 0.75 / 1.2 × 10⁻⁴ | 0.65 / 0.97 × 10⁻⁴ | – | – |
| leaf-specific conductivity, shoot (kg m⁻¹ s⁻¹ MPa⁻¹) | 2.1 / 2.4 × 10⁻⁴ | 3.5 / 4.2 × 10⁻⁴ | no birch value found | – |
| whole-tree leaf-specific conductance (mmol m⁻² s⁻¹ MPa⁻¹) | 0.28 / 0.26 | 0.32 / 0.27 | 1.15 (young trees) | Sellin et al., PMC3976162 |
| midday ψ, top leaves (MPa) | −1.96 / −1.49 | −1.68 / −1.39 | −1.0 to −1.3 well watered; −1.9 to −2.1 severe deficit | Sellin et al., PMC3976162 |
| P50, branches (MPa) | none: stomata shut at −2.0 | same | −1.8 (pneumatic), −2.0 (centrifuge); −1.80 | PMC6025199; Klepsch et al. 2018 |

- **Midday ψ was clearly off.** With k_s 2, a well-watered open tree held its top leaves at −2.0 MPa. That is the branch P50, and silver birch only reaches it in severe drought. Doubling k_s to 4 (inside the 1–5 range for diffuse-porous wood) gives −1.7 open and −1.4 in the stand.
- **Whole-tree conductance is still about 4× too low** (0.3 against 1.15). The published figure is for young trees, so it is not directly comparable.
- **The Huber value at the shoot is 4× too high.** The pipe model gives every short shoot a fixed pipe (`spur_radius` 0.8 mm). The model compensates a too-high Huber value with a too-low k_s, so leaf-specific conductivity is probably about right. Changing either needs a measured birch LSC.
- **k_s 4 alone overshoots height:** 29.1 m open and 28.2 m in the stand at 60, against a band of 21.1–26.9 m. In the combined defaults the larger leaves pull it back.
- **There is no embolism model.** Stomata shut at −2.0 MPa, so leaves never pass the branch P50.

## Other

- Limbs that reach the ground layer now stop, and a branch lying there dies. Nodes coming back to the trunk below 3 m fell from 95 to 32 on seed 1 (open), but not to zero.
- Roots near the collar avoid the stem and each other and turn at most 30° per 5 cm segment. Segments heading back to the stem fell by about half in open-grown seed 1 (2435 → 1031) but rose in the stand run (314 → 454). Sharp kinks fell only slightly (3.8 → 3.2 % of collar segments).
- Blender is not installed on this machine. The shaded previews come from the built-in rasterizer (exact rasterization, supersampling, sky and sun light; no shadows).
