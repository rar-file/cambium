# Milestone M1: Foundations (draft, in progress)

Protocol hash at the start of the campaign: `0e58497`.

## M1a. Alpha provenance

Answer: 4.8 is traceable, but it's a one-point model calibration, not a published value. It now carries VERIFY.

**Where it came from.** Commit `c3fd2dc` (2026-11-01, phase 22; KNOWN_ISSUES.md:618-621). The chain:

| Step | Value | Source |
|---|---|---|
| Tree NPP, 10-year-old stand | 13.02 Mg/ha/yr | Aosaar et al. 2016, Table 4, p. 8 (opened) |
| Leaf mass | 2.81 Mg/ha | same table |
| SLA | 15 m²/kg, so LAI 4.21 | Uri et al. 2007, as cited in the species file; not opened this round |
| Carbon fraction | 0.48 | Thomas & Martin 2012, as cited in targets.yaml; not opened this round |
| CUE | 0.45 | assumed in that commit; the species file gives 0.47 elsewhere (Waring et al. 1998, not opened this round) |
| GPP per m² of leaf | 329 g C, 1080 model units at 0.305 g C per unit | calculation, `tools/alpha_check.py` |
| alpha | 4.8 | the value at which one natural-plot run fixed that much per m² of leaf at years 16-20 |

So the knowledge base is right that 4.8 isn't in Aosaar and that the paper has no light or photosynthesis data (a search of the PDF finds no LAI, GPP or photosynthesis measurements). "No traceable source" goes too far: the path is in the git log. The species comment's "set from sources, not from heights" also went too far: the inputs are from sources but the 4.8 comes from a model run.

**Before that, it was tuned to height.** The values went 5.6, 6.2, 5.2, 4.8 (`git log -G` on the species file), and earlier values back to 4.6 are in the comment at `species/betula_pendula.yaml:101-109`. Those earlier ones were tuned to the height curves.

**How much depends on it.**
- **All carbon.** Fixed carbon is alpha × Σ(light × stomatal opening × leaf weight) (`treegen/growth.py:797`). The same alpha sets each branch's carbon balance, so it also drives branch death (`:933`, `:969`), and it pays the late leaves (`:1583-1589`). Plot trees multiply it by their vigour (`treegen/plot.py:85`, `:179`).
- **Two values were fitted with alpha already at 4.8:**
  - `maintenance_per_internode` 0.5, set in the same commit, to reach a plot CUE of 0.42;
  - `huber_path_exponent` 0.283, fitted by running the model (`tools/fit_huber_exponent.py`; commit `14c4b23`).

  `huber_radius_exponent` was fitted the same way but is no longer used. Full list: `out/bench/m1/species_changes_since_alpha.txt`.
- **Every scorecard verdict on a model output** rests on it, because they all come from runs at alpha 4.8.
- **Older calibrations were made at other alphas and never redone,** such as `wood_volume_per_carbon` and the phase 16 gravitropism fit. Their dependence on alpha is not calculated.

**Does the derivation still hold?** On the seed-1 stand tree the model fixes 0.92-1.12 times the derived figure per m² of leaf (`out/bench/m1/alpha_check.txt`):

| Age | LAI | g C per m² of leaf | Ratio to the 329 derived |
|---|---|---|---|
| 10 | 2.58 | 305 | 0.92 |
| 20 | 1.86 | 370 | 1.12 |
| 30 | 2.11 | 348 | 1.06 |
| 50 | 2.99 | 302 | 0.92 |
| 60 | 2.95 | 312 | 0.95 |

But the derivation assumed CUE 0.45 and the seed-1 tree's CUE was 0.54 at age 30 (`carbon.cue`, same run). That inconsistency goes to M2. A sensitivity number for alpha itself is not calculated yet: it needs model runs (CAMPAIGN.md, blocker B1).

Change: comment only (species values unchanged, checked by loading the YAML before and after).

## M1b. Height target

Answer: the 1.3 m offset and breast-height age were already right; the fixed 4-year shift was not. Corrected, but the tag isn't moved until checker A confirms.

**Source, opened this round** (Elfving 2010, `birch-data/07_stand_dynamics/Elfving_Heureka_prognossystem.pdf`, 99 pages, dated 05/02/2010):
- p. 58: "For birch the equation gives height development above breast height as function of age at breast height."
- p. 56: "For other broad-leaves (birch, aspen etc.) the following relation is applied: T13 = 150/SIS".
- p. 55: "sis site index according to site factors, given as top height at age 100, m".
- p. 58, Table 1: asi 7, beta 394, b2 −1.3870.

**What the code did.** `treegen/reference.py:15-18` subtracts 1.3 from the site index, runs the curve on breast-height age and adds 1.3 back. That agrees with p. 58. `tools/scorecard.py` then used a fixed 4 years to get breast-height age.

**Where the source leaves a gap.** SIS is a top height at age 100 set from site factors for a site-indicative species (pp. 20, 38, 55). The target's site index is birch height at breast-height age 50. Elfving prints no conversion, and I found none in the Heureka wiki pages on disk. The knowledge base's "about 5.8 at SI 26" treats the two scales as the same. I used this curve's own height at total age 100 as SIS, solved together with T13, because that keeps the source's definition of SIS as top height at age 100. It's still a stand-in: birch, not the site-indicative species. Flagged VERIFY in targets.yaml.

| Site index | SIS used | T13 used | 150/SI, the knowledge base's reading | Fixed value before |
|---|---|---|---|---|
| 20 | 25.08 m | 5.98 yr | 7.50 yr | 4 yr |
| 26 | 29.93 m | 5.01 yr | 5.77 yr | 4 yr |

**Band before and after (m), with the other reading for comparison:**

| Total age | Before (T13 = 4) | After | If T13 = 150/SI |
|---|---|---|---|
| 20 | 9.05-14.31 | 8.05-13.61 | 7.26-13.07 |
| 30 | 13.44-19.67 | 12.66-19.24 | 12.03-18.90 |
| 40 | 16.74-23.07 | 16.16-22.79 | 15.69-22.57 |
| 50 | 19.20-25.31 | 18.76-25.12 | 18.42-24.98 |
| 60 | 21.05-26.87 | 20.72-26.73 | 20.46-26.63 |

The band moves down at both edges. It isn't looser: the top edge drops at every age.

**Rescored against the corrected file** (`tools/rescore_compare.py`, saved as `out/bench/m1/height_rescore.txt`; a preview until the tag moves). One verdict changed:

| Run | Age | Model height | Before | After |
|---|---|---|---|---|
| p41_germ | 20 | 14.09 m | PASS | FAIL |

- p40_default: no verdict changed (FAIL at 20, 30, 40; PASS at 50, 60).
- p41_germ: otherwise no change (PASS at 30, 40, 50, 60).
- p38_nat: NOT APPLICABLE before and after; plot top height is still unconfirmed (DECISIONS.md row 15).

The choice of SIS matters at the margin. With T13 = 150/SI these would also change: p40_default at 50 (25.02 m against 24.98) and p41_germ at 30 (18.91 m against 18.90). That's a decision for the maintainer (section 8).

**Not changed:** `reference.years_to_breast_height: 4` in the species file, used only by the height check inside stats.json, never by growth or the scorecard. A comment now says so.
