Fresh reviewer's report, saved as it stands.

# Review: M1c source checks, audit merge, start of M2 (2026-11-06)

**Bottom line**
- **Holds:** the alpha table recomputes exactly. "No alpha fits both" holds on stand trees for every value run.
- **Doesn't hold:**
  - "Under the band's 3.6 at every alpha" is contradicted by a saved run (alpha 6.0: LAI 3.67 at 60).
  - "Which points at how carbon is shared out" isn't earned. Saved results point at least as strongly to a ceiling set by light.
- **Missing:** a like-for-like control for `--set`.
- **M1c and the audit merge:** record-keeping items only. The merge's arithmetic is right.

**How I checked:** read-only scripts on saved files, plus `tools/ensemble_sweep.py table` and `tools/paired.py`. No growth, no tests, no SSH, no repo edits (`git status` clean). I didn't re-open any paper or see the node live.

| Point | M1c | Audit merge | M2 start |
|---|---|---|---|
| 1. Did what was approved | OK | OK | FIX |
| 2. Noise | n/a | FIX | FIX |
| 3. Linked failures | n/a | n/a | FIX |
| 4. Wrong knob | n/a | FIX | ASK MAINTAINER |
| 5. Like for like | n/a | OK | FIX |
| 6. Idle machines | n/a | n/a | FIX |
| 7. Shared machines | n/a | n/a | OK on arithmetic, unverified live |
| 8. Sources | FIX | OK | FIX |
| 9. Claims | FIX | OK | FIX |
| 10. Guesses labelled | OK | OK | FIX |

## 1. Did each step do what was approved?

**M1c: OK.** Row 23 asked for values unchanged and listed. `git show 740031a` shows one comment line changed in the species file, six rows added, and the list in `research_notes.md`.

**Audit merge: OK.** `tools/param_audit.py`, redirected to the scratchpad, reproduces `parameter_audit.csv` byte for byte. All 15 `screen20` rows and 145 `screen5` rows carry over exactly, with ranks 1-160 contiguous.

**M2: FIX.**
- `CAMPAIGN.md:34` and `M2_design_draft.md:3` want the cut rule in DECISIONS.md before any run. The sweep's files are dated 08:52-09:20; row 51 ("no cuts") was committed at 09:25. Nothing was cut, so no harm, but it's an exemption written afterwards.
- `PROTOCOL.md:82` puts diagnosis first, with file:line. No M2 text states a mechanism.
- The maintainer's rule was kept: height and LAI are judged together, and nothing is adopted (`alpha: 4.8`, species:127).

## 2. Noise: M2 FIX, audit FIX

**Recomputed:** the tool's output has no diff against `m2_alpha_table.txt`, and my separate means and SDs agree with it.

| Alpha | Height 50, 60 (band top 25.12, 26.73) | LAI 50 +- SE | LAI 60 +- SE | SEs under 3.6 at 50, 60 | Median LAI 60 | Seeds at 3.6+ at 60 |
|---|---|---|---|---|---|---|
| 2.7 | 14.61, 15.67 | 1.714 +- 0.098 | 1.606 +- 0.103 | 19.2, 19.3 | 1.78 | 0 |
| 3.5 | 19.85, 21.56 | 2.206 +- 0.117 | 2.424 +- 0.127 | 12.0, 9.3 | 2.49 | 1 |
| 4.0 | 21.91, 23.42 | 2.815 +- 0.074 | 3.020 +- 0.068 | 10.6, 8.6 | 3.00 | 0 |
| 4.4 | 23.45, 25.16 | 3.086 +- 0.089 | 3.308 +- 0.089 | 5.8, 3.3 | 3.35 | 3 |
| 4.8 | 25.29, 27.07 | 3.094 +- 0.091 | 3.274 +- 0.083 | 5.6, 3.9 | 3.28 | 4 |
| 5.2 | 26.18, 28.01 | 3.427 +- 0.076 | 3.482 +- 0.069 | 2.3, 1.7 | 3.47 | 9 |
| 5.8 | 27.62, 29.61 | 3.458 +- 0.091 | 3.530 +- 0.091 | 1.6, 0.8 | 3.61 | 10 |
| **6.0, screen, not in the sweep** | 27.28, 29.41 | 3.452 +- 0.091 | **3.671 +- 0.070** | 1.6, above | 3.71 | 13 |
| 6.8 | 29.12, 31.33 | 3.418 +- 0.132 | 3.519 +- 0.138 | 1.4, 0.6 | 3.62 | 10 |

Alpha 6.0 is `out/bench/node/screen20/resource.alpha__x1.25__s*.json`: same node and seeds, code `68782d9`.

**Paired LAI, `tools/paired.py` arithmetic (difference +- SE, ratio):**

| Step | At 50 | At 60 | Counts over 2 SE? |
|---|---|---|---|
| 4.4 to 4.8 | +0.008 +- 0.106 (0.1) | -0.034 +- 0.084 (0.4) | no |
| 4.8 to 5.2 | +0.333 +- 0.073 (4.6) | +0.208 +- 0.076 (2.7) | yes |
| 5.2 to 5.8 | +0.031 +- 0.060 (0.5) | +0.048 +- 0.059 (0.8) | no |
| 5.8 to 6.8 | -0.040 +- 0.122 (0.3) | -0.011 +- 0.121 (0.1) | no |
| 5.2 to 6.8 | -0.009 +- 0.120 (0.1) | +0.037 +- 0.107 (0.3) | no |

**Is "levels out near 3.5" backed?** Yes, as "no rise detected from 5.2 to 6.8", and the mean over ages 45-60 agrees (+0.008 +- 0.105).
- The 2-SE comparison is required (`PROTOCOL.md:30`), and no report has it. It's the table above.
- The bound is loose: at 60 the 2-SE range is -0.18 to +0.25, so the plateau could be as high as about 3.73.
- The shape is flat, then a step, then flat, not a smooth saturation. The step is unexplained.

**Is "under 3.6 at every alpha" backed?** No. At 5.2 and up it is within noise at 60, the median seed reaches 3.6 at 5.8 and 6.8, and 6.0's mean passes. `milestone_M1.md:309` already reports alpha x 1.25 as LAI +13.2 % at 60.

**Does "no alpha fits both" follow? Yes, on stand trees.**
- Where height passes at both 50 and 60 (3.5-4.4), LAI is at least 3.3 SE short. Its upper 2-SE limits at 4.4 are 3.27 and 3.49.
- Between values, by interpolation (not a run): height reaches the band top at alpha 4.76 at age 50 and 4.73 at age 60, with LAI about 3.09 and 3.28 there.
- One window is open: the unexplained step lies somewhere between 4.8 and 5.2, and it might start lower. Even then LAI would be about 3.43-3.48, under the band. Alpha 4.6 and 5.0 close this.
- Counting age 20 tightens it. Height at 4.4 is over the band top by 1.6 SE, which is within noise, and at 4.8 by 11.8 SE.

**Height verdicts near the band edge are soft.** At 4.8 the misses are 1.7 SE at 40, 1.2 at 50 and 2.0 at 60. This doesn't change the answer, because LAI is what binds there.

**Audit: FIX.** Ranks 16-160 rest on 5 seeds and the largest of 12 comparisons. Of the 83 values outside the noise, 36 have a ratio of only 2-3. `root_share_max` fell from 6.21 to 2.39 at 20 seeds, and from -6.97 % to -1.52 %. Treat ranks 16 and below as unreplicated when `M2_design_draft.md:25` draws on them.

## 3. Are two failures really one? M2 FIX

**LAI and light on stand trees are one failure.**
- Implied k at 60 is 0.383-0.397 at every alpha. Correlation of ln(light) with LAI within an alpha is -0.80 to -0.98.
- Passing LAI doesn't pass light: alpha 6.0 has LAI 3.67 and light 24.79 %.
- `daily:119` lists them side by side without saying this; the link is at `daily:43`.

**Height and LAI are linked too, and that isn't reported.** LAI = leaves x leaf area x `stems_per_ha(height)` (`growth.py:2152`, `:458-469`), so alpha moves the denominator.

| Alpha | First year at 450/ha | Seeds at 450/ha at 30 | at 50 | at 60 |
|---|---|---|---|---|
| 2.7 | 51.3, 14 seeds never | 0 | 3 | 6 |
| 3.5 | 33.7 | 4 | 20 | 20 |
| 4.0 | 29.1 | 14 | 20 | 20 |
| 4.4 | 25.9 | 19 | 20 | 20 |
| 4.8 | 22.8 | 20 | 20 | 20 |
| 6.8 | 20.5 | 20 | 20 | 20 |

- The alpha 2.7 row (LAI 1.71, 1.61) is mostly at 1000/ha, so it isn't like for like. At 450/ha it would be about 0.87, 0.92 (arithmetic).
- The stage-30 test at `M2_design_draft.md:61` must therefore use per-tree leaf area. From 3.5 to 4.0 at age 30, LAI falls (2.21 to 2.11) while the tree's leaf area rises (26.2 to 37.7 m2).

## 4. Wrong knob? ASK MAINTAINER (audit gap: FIX)

The conclusion isn't earned. Everything below is a lead, not a finding. In plain accounting, extra carbon does go to wood rather than leaves. What isn't shown is that the sharing rule is why leaves stop.

**Saved 20-seed screen, x 1.25, paired with the baseline.** Baseline: height 25.29, 27.07; LAI 3.09, 3.27; light 30.1, 27.5.

| Value | Height at 50, 60 (m) | LAI at 50, 60 | Light at 50, 60 (points) |
|---|---|---|---|
| `extinction_coefficient` | -1.34, -1.58 | -0.540 +- 0.095, -0.582 +- 0.078 | -0.58 +- 1.16, **-0.07 +- 0.63** |
| `leaf_area_m2` | -4.31, -4.25 | +0.068 +- 0.114, +0.145 +- 0.100 | +0.31, -0.69 |
| `lma_reference_g_m2` | -1.41, -1.21 | +0.346 +- 0.076, +0.280 +- 0.091 | -2.79, -1.72 |
| `huber_value` | +0.51, +0.45 | +0.488 +- 0.084, +0.429 +- 0.085 | -5.03, -3.88 |
| `transpiration_max` | -2.91, -3.05 | +0.243 +- 0.080, +0.080 +- 0.072 | -2.06, -0.32 |

**Lead A, a ceiling set by light (the strongest):**
- Raising k by 25 % cut LAI by 18 % and left light at 60 unchanged. The canopy seems to fill to a light level.
- Plots, 5 seeds at 50 and 60: LAI 3.769 and 3.761 (SD 0.031, 0.016), light 22.32 and 22.29 % (SD 0.10). LAI's SD falls from 0.39 at 20. That is very tight for a chaotic model.
- The code has light gates:
  - A resting bud becomes a spur only at Q >= 0.30 (`growth.py:1094`). That value has no source (species:307; audit: read level none).
  - A spur dies under 0.21 (`:1113`, species:311). `parameter_checks.csv:14` calls this use "a transfer".
  - A limb is shed under 0.21 (`:735`, species:447).
- Arithmetic, ignoring own-shoot exclusion and gaps: at k 0.37-0.39, Q 0.30 means LAI 3.1-3.25 above the bud, and Q 0.21 means LAI 4.0-4.2. The plateau of 3.4-3.5 sits between them, and mean bud light at the plateau is 0.32-0.33.
- **The light band's top (19.8 %) is below the death line (21 %),** and plots sit at 22.3 %. That band may be out of reach by construction. `M2_design_draft.md:17` wants LAI 4.1-4.4 on plots; the gates suggest 4.0-4.2 at most.
- 5 seeds, x 1.25 only, largest effect (reported at the age shown), which runs against the gates: `short_shoot_survival_light` leaf area -11.49 % +- 3.09 at 50; `short_shoot_light` -6.72 % +- 2.62 at 50; `light_per_leaf_threshold` -25.73 % +- 6.21 at 30.

**Lead B, spurs and carbon:**
- Spurs get no share of the split (`growth.py:888-893`). They carry about 74-80 % of leaf weight at alpha 4.8 and up (2.5 x spurs / leaves, ignoring leaf-size scaling).
- From 4.4 to 6.8 spurs stay flat (15,846 to 15,408), while living internodes rise 25 % (29,663 to 37,059). So leaf sites aren't what's short.
- Carbon isn't short either. From 4.8 to 6.8 at 60, the leaves' cost falls from 21.9 % to 15.8 % of fixed carbon, and shoot carbon left after upkeep rises from 24,674 to 45,108. Stomatal opening is 0.97-0.99 at every alpha.

**Lead C, wood shade:** `light.woody_shade` is on, k_wood 0.40 with no page, and `parameter_checks.csv:13` says the double count "looks real". Implied k is 0.383-0.397 against 0.37. Set aside at `CAMPAIGN.md:38`, not tested.

**Lead D, leaf size:** `leaf_area_m2` x 1.25 lowers height 4.25 m at 60 (to 22.82) with no LAI loss (3.42). By interpolation, alpha at that height gives LAI about 2.8. So alpha's height-for-leaves trade-off isn't general. Carbon is counted in reference leaves (`growth.py:807`), so this acts partly like a lower alpha per m2. This is not a proposal to tune it.

**Lead E, spacing:** LAI's multiplier ends at 450/ha (species:916-919), against 880 at 45 and 420 at 67 in the source (`targets.yaml:44`).
- The screen can't vary it (`numeric_paths` skips lists of dicts), so it has no rank.
- By reading, `--set` can't either: JSON gives dicts, and `growth.py:463` needs attributes.
- Plots reach LAI 3.76 with the same sharing code at about 1,450-1,600 stems/ha, not like for like (Q13).

**Against these, carbon sharing stays a live reading:**
- `apical_control_old` and `_young` x 1.25 move leaf area -39.6 % and -29.4 %, largest at age 30, 5 seeds.
- Stand-tree crowns cover only 0.42-0.58 of their ground (`QUESTIONS.md:56`), so wider crowns might hold more leaves above the gates. That is M3's ground.

**Lead F, alpha is the wrong knob for "too tall when young".** Arithmetic with the approved equation (it reproduces the band edges exactly). No approved band applies below 20, so this is information, not a verdict.

| Height (m) at age | 5 | 10 | 15 | 20 | 50 | 60 |
|---|---|---|---|---|---|---|
| Curve SI26 | 1.30 | 5.12 | 9.69 | 13.61 | 25.12 | 26.73 |
| Alpha 2.7 | 3.62 | 6.34 | 8.51 | 9.92 | 14.61 | 15.67 |
| Alpha 3.5 | 4.75 | 8.07 | 10.43 | 12.55 | 19.85 | 21.56 |
| Alpha 4.0 | 5.23 | 8.74 | 11.02 | 13.28 | 21.91 | 23.42 |
| Alpha 4.8 | 5.71 | 9.26 | 12.10 | 14.89 | 25.29 | 27.07 |
| Alpha 6.8 | 5.85 | 9.96 | 13.03 | 16.03 | 29.12 | 31.33 |

- Trees pass 1.3 m in year 2 (year 3 at alpha 2.7). The curve's T13 is 5.0-6.0 years.
- At 4.8 the excess over SI26 peaks at 4.87 m at age 7, and is 1.28 m at 20, where the table starts. Even alpha 2.7 is 1.22 m over at 10.
- `shoot.max_shoot_length` 1.2 (species:83, `growth.py:1536`, no source, page not checked) looks like the limit: increments top out at 1.18 m, and 59-66 % of seed-years at ages 2-10 are within 0.03 of 1.17 m at alpha 4.8 and 6.8.
- "Height passes" means inside a band, not on a curve. Position in the band, age 20 to 60: alpha 3.5 goes 81 % to 14 %, 4.0 goes 94 % to 45 %, 4.4 goes 104 % to 74 %, 5.2 goes 127 % to 121 %. Lowering alpha passes the band by crossing site-index curves.

**For the maintainer.** Their rule assigns the cause in advance if no alpha fits.
- (a) Report as they asked, and add these leads as open.
- (b) Hold the attribution until the runs in FIX 3.
- Recommendation: (a), with the runs going meanwhile. Put it in QUESTIONS.md, not a dialog.
- Also ask whether the curve should show as INFO below age 20. That needs the maintainer, and Eriksson's valid age range is unread.

## 5. Like for like: M2 FIX

**OK by evidence:**
- All 160 manifests read the node's name, one maths thread, the same library versions and 19 options on, with seeds 1-20.
- `base_trees` has code `null` (row 35). The sweep has `f45928e`.
- The species hash differs by one comment.
- The screen's baseline equals `base_trees` on all 120 fields compared.

**`--set` by reading: honoured the same way.**
- It's applied before the model is built (`cli.py:76-79`).
- Alpha is read at run time (`growth.py:807, 943, 979, 1593`), with no derived copy at load.
- Plots deep-copy it, then multiply by vigour (`treegen/plot.py:108-109`).
- The stand-path code diff is the array growth factor (`structure.py:91`), a history-write guard and a manifest field. I find no route to a number.

**Not shown by run:**
- `CAMPAIGN.md:35` says the baseline "holds" for `f45928e`. The golden evidence is seed 1, default alpha, not lean (`golden.py:43`), and row 45 lists those gaps.
- No run at 4.8 through `--set` exists.

**The one cross-code check at a non-default alpha:**

| Alpha 6.0 minus | Height at 30 | Height at 50 | Height at 60 | LAI at 50 | LAI at 60 |
|---|---|---|---|---|---|
| 5.8 | **-0.97 +- 0.17 (5.6)** | -0.34 +- 0.20 (1.7) | -0.20 +- 0.21 (1.0) | -0.01 +- 0.12 | +0.14 +- 0.07 (1.9) |
| 5.2 | -0.02 +- 0.20 (0.1) | +1.10 +- 0.14 (7.7) | +1.40 +- 0.20 (6.9) | +0.03 +- 0.11 | +0.19 +- 0.07 (2.9) |

At 50 and 60 it's mostly in family, except LAI against 5.2 at 60. At 30 it reverses, with SD 0.35 against 0.63-1.12 elsewhere. The 4.8 point shows no matching offset.

- If a rerun gives identical files, the cause is the model itself, and seed SEs understate differences between settings. That matters for the gate.
- If the rerun differs, the comparison is broken.

## 6. Idle machines: M2 FIX

- 10 plots against a limit of 14 leaves 4 slots unused, if others stayed under 1 core. `CAMPAIGN.md:28` queues nothing else for the node, and "what M2 can still do" is undefined.
- Runs in FIX 1, 3 and 5 fit those slots: under 0.6 GB each, about 2 minutes each, about 115 an hour with `ORIGIN_RESERVE=10` (arithmetic from `base_trees/runs.csv`).
- If others are now above 1 core, the limit is 8 and nothing more may start.

## 7. Shared machines: OK on arithmetic, not verified live

- **Memory:** 10 x 7 GB = 70 GB (`ensemble.py:36`), with about 91 GB free at an earlier launch, leaving about 21 GB against the 8 GB floor.
- **Batches don't see each other:** `run_batch` counts only its own children's growth. That's harmless at this size; check by hand before adding a third batch.
- **CPU:** 10 is allowed only if others were under 1 core at launch. That line is in the node's logs, and the local `usage.log` stops at 05:08.
- **Disk:** `--no-saves` for these plots is my inference from the 7 GB figure. `CAMPAIGN.md:28` doesn't say.

## 8. Sources

**M1c: FIX.** Levels are stated honestly and repository copies are flagged (`milestone_M1.md:421`). Remaining:
- `parameter_checks.csv:67-68` say `no` on abstracts alone, while lines 4 and 10 say `not checked` for the same read level.
- `csv:72` keeps `calibrated` for `wood_volume_per_carbon`, though the notes say that label "overstates it".
- `KNOWN_ISSUES.md:2133` calls `10.1038/2051030a0` "the right one", but the wrong DOIs were on Can. J. Bot. citations (`:107`, `:1791`), and it doesn't say whether those papers exist. The species label `[CK66]` is for a 1965 paper.

**Audit: OK.** "5 of 15 give the number" recounts.

**M2 bounds: FIX, text only.**
- Row 51 says exploring only, and the species file is unchanged.
- But `M2_design_draft.md:23` still marks them "Certain", and `:48` samples inside them. `PROTOCOL.md:105` wants published ranges, and `research_notes.md:85` says the stand routes aren't independent of the model.
- `CAMPAIGN.md:188` says "recheck before any use", yet they set the sweep's range.
- Nothing was tuned to a number.

## 9. Claims beyond the work: FIX

- `daily:119`, "under the band's 3.6 at every alpha": see point 2.
- `daily:119`, "light never gets under 25 %": alpha 6.0 is 24.79 at 60, and 10 % of seeds at 6.8 are inside the band. True only of the sweep's means.
- `daily:119`, "which points at how carbon is shared out": no test behind it.
- Row 51, commit `1c99fdf`, `CAMPAIGN.md:58`: "no alpha" should be "none of the 8 values run".
- `CAMPAIGN.md:35`: "holds" (point 5).
- `740031a`'s title and `CAMPAIGN.md:184`, "none has a page": two rest on abstracts. Checker B caught the wording but not this reason.
- `research_notes.md`: the "where from" table uses 20-seed ranks while the section says 5-seed. Its row "5, 6, 11" is wrong, because rank 5 is `wood_volume_per_carbon`, which has no source.

**OK:** "exploring only", "plots running", "that's on stand trees", and the table itself.

## 10. Guesses labelled: M2 FIX

Most are labelled ("inferred", "subagent's arithmetic", "arithmetic, not a model run"). Not labelled: `daily:119`'s "points at", and "Certain" at `M2_design_draft.md:23`.

## FIX items, in priority order

1. **`--set` control.** Run `--set resource.alpha=4.8` and `=6.0`, 20 seeds, lean, on the node's code.
   - *Settles it:* 4.8 is identical to `base_trees` and 6.0 to the screen's results. If so, measure ensemble-level noise with 4.79 and 4.81.
2. **Correct the claims.** Reword `daily:119`, row 51, `CAMPAIGN.md:35` and `:58`. Add the paired table and the 6.0 row.
   - *Settles it:* each sentence checks against those tables, with the guess labelled.
3. **Diagnose before attributing (`PROTOCOL.md:82`).** Exploring only, 20 seeds each, paired with `base_trees`:
   - `bud_fate.short_shoot_light=0.21`
   - `light.woody_shade.enabled=false`
   - `resource.apical_control_young=0.45` and `resource.apical_control_old=0.375` (one run, both x 0.75)
   - a lower `shoot.max_shoot_length`

   Copy the 5-seed per-seed results back too; their LAI needs no new runs.
   - *Settles it:* the plateau moves with the light gates and not apical control (light), the reverse (sharing), or both. Height at 5-15 moves with the cap and not with alpha (cap).
4. **Write the plots' decision rule now, before reading them.** `M2_design_draft.md:33` uses Baltic 2.5-4.5, while `daily:37` and `ensemble_sweep.py:23` use Hagemeier 3.6-5.4. Both apply at 50 and 60 (`scorecard_base_plots_master.txt:8-9, 13-14`), and the answer can flip on the choice. My recommendation is that an alpha must pass both, so 3.6-4.5.
   - *Settles it:* a DECISIONS row committed before the results are read, naming bands, ages, and which height definition counts.
5. **Close the open window.** Run alpha 4.6 and 5.0, 20 seeds.
   - *Settles it:* LAI there, paired, against 3.6, and where the step falls.
6. **Use the free slots.** Run 1, 3 and 5 with `ORIGIN_RESERVE=10`, and write "what M2 can still do" in `CAMPAIGN.md:28`.
   - *Settles it:* a queue exists, within limits.
7. **Height reporting.** Add position in band, young ages as INFO, and the height band to the table (`ensemble_sweep.py:66-70` omits it). Default `--ref` to the tag (`:85`). Targets at master equal the tag today, so nothing changes now.
   - *Settles it:* the table shows target beside number.
8. **M2 draft and row 51.** Remove "Certain" and the bounds as sampling limits. State per-tree leaf area for stage 30. Note that row 51 was logged after the run and mark it as the builder's decision. Recheck 10 seeds per candidate (LAI SD at 60 runs from 0.30 to 0.62 across alphas, not one figure).
   - *Settles it:* the draft and row 51 agree.
9. **M1c and audit records.** `csv:67-68` to `not checked`, `csv:72` status, the `where` column in `param_audit.py:35` (`-48.67` is on `fixed at 30`, unreadable without it), the rank row, and `KNOWN_ISSUES.md:2133`.
   - *Settles it:* a Crossref lookup of the two Can. J. Bot. citations, and regenerating the audit.
10. **Node evidence.** Copy back each plot batch's first log line, the launch command and `usage.log`.
    - *Settles it:* N at launch, `--no-saves`, and free memory and disk.

**Scripts** (read-only; they may not outlive the session, and every number can be recomputed from the paths above):
- <scratchpad>\recompute.py
- <scratchpad>\leads.py
- <scratchpad>\screen20_lai.py
- <scratchpad>\alpha_consistency.py
- <scratchpad>\contrasts.py
- <scratchpad>\yearly.py
- <scratchpad>\audit_checks.py
- <scratchpad>\final_checks.py
- <scratchpad>\young.py
