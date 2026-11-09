# How real is it

This page sums up the validation report for the birch (`reports/birch_v1_final.md` in the repository). The numbers are copied from it as they stand. The runs used the final settings of birch v1, which became the species defaults.

## In short

1. At ages 50 and 60, the birch matches what it was tuned to: light under the canopy and leaf area. These are one linked result. Height follows the published curves by design.
2. No independent check passes at 50 or 60.
3. Independent checks fail on young forests. Their crowns reach almost to the ground: a crown ratio of 0.92-0.96, against 0.30-0.45 at ages 11-22. Leaf area is outside the Baltic band in 46 of 55 years.
4. Old forests keep some first-generation trees to age 200, longer than the sources suggest. Those sources were read only as an abstract and a guideline page.

Version 1.0 is planned to fix young trees.

## Three kinds of check

- **By design:** the model is built to match. Height is one: the leader grows up to the Eriksson et al. (1997) site-index curve (SI 23). The code can hold it back when light, water or carbon run short, but in the 20 forest-grown trees the curve set the leader's growth in every one of 1,200 seed-years. So height is close to scripted.
- **Tuned against:** values were set to bring the model closer.
- **Independent:** nothing was set against it. Only these test the model.

## Results at ages 50 and 60

### Forest-grown trees

20 seeds. Each tree grows among neighbours that are copies of itself (`stand=True`). Repola's equations give the figures in brackets.

| Age | Height m | Stem cm over bark | LAI | Light % | Stem kg (Repola) | Branch kg (Repola) | Crown width m | Crown ratio |
|---|---|---|---|---|---|---|---|---|
| 50 | 21.91 | 26.9 | 4.82 | 16.2 | 229 (237) | 60.0 (46.4) | 5.25 | 0.53 |
| 60 | 23.71 | 30.4 | 4.68 | 16.4 | 335 (316) | 78.2 (63.8) | 5.77 | 0.45 |

Branch wood is 29 % over Repola at 50 and 23 % at 60. That is inside twice Repola's ×/÷ 1.19 scatter for a mean of 20 trees. But Repola includes bark and the model is wood only, so like for like the gap is somewhat larger.

### Natural forests

20 plots of 1,000 m², never thinned (`cambium.forest`). Ranges over the plots in brackets.

| Age | Stems/ha | Basal area m²/ha | Dg cm | Top height m | LAI | Light % (diffuse, 1-2 m) |
|---|---|---|---|---|---|---|
| 50 | 751 (640-810) | 23.9 | 20.1 | 21.35 | 4.54 | 18.5 (17.1-21.6) |
| 60 | 520 (470-570) | 25.7 | 25.1 | 23.14 | 4.36 | 19.0 (17.3-20.9) |

At 45 the plots hold 953 stems per hectare, against Hagemeier & Leuschner's 880. Stems and Dg were tuned against that stand, and its printed figures don't add up, so this is information only.

### Lone trees

8 seeds, grown in the open.

| Age | Height m | Stem cm over bark | Crown width m | Hemery's formula at that stem |
|---|---|---|---|---|
| 50 | 17.77 | 44.5 | 8.65 | 8.81 |
| 60 | 19.24 | 49.4 | 9.35 | 9.68 |

This isn't a test. The crown width is capped at Hemery's crown by design, at a stem of at most 2.4 cm per metre of height. Hemery's coefficients are themselves VERIFY and second-hand.

### Old forests

3 plots to 200 years. Indicative only: a verdict needs 5 plots.

| Age | Stems/ha, all (past 1.3 m) | Basal area m²/ha | Top height m | SI 23 curve m | Light % (diffuse) | First generation alive per ha |
|---|---|---|---|---|---|---|
| 50 | 780 (777) | 23.7 | no tree list | 21.95 | 19.1 | 770-790 |
| 60 | 540 (537) | 25.3 | 23.05 | 23.75 | 19.8 | 520-550 |
| 100 | 637 (330) | 31.2 | 26.39 | 27.50 | 28.5 | 230-280 |
| 150 | 2,117 (1,513) | 23.5 | 27.56 | 29.33 | 42.0 | 90-140 |
| 200 | 1,590 (1,137) | 25.1 | 26.87 | 30.17 | 33.6 | 30-90 |

The sources for how long trees live in old stands were read only as an abstract (Forests 2020) and a guideline page (Vakkari 2009).

## Targets

"Share inside" is the share of runs inside the target range.

| Target (source) | Run | Age 50 | Age 60 | Share inside, 50 / 60 | Verdict | Kind |
|---|---|---|---|---|---|---|
| Light under the canopy, 6.4-19.8 %, median 14.8 (Hagemeier & Leuschner 2019b) | forests | 18.5 | 19.0 | 75 % / 75 % | Pass | Tuned against |
| | forest-grown trees | 16.2 | 16.4 | 80 % / 80 % | Pass | Tuned against |
| Leaf area index, 3.6-5.4 (Hagemeier & Leuschner 2019) | forests | 4.54 | 4.36 | 100 % / 100 % | Pass | Tuned against; the same result as light |
| | forest-grown trees | 4.82 | 4.68 | 80 % / 70 % | Pass | Tuned against |
| Baltic leaf area index, 2.5-4.5 at ages 6-60 (Uri et al. 2012; Varik et al. 2015) | forests | 4.54 | 4.36 | 40 % / 85 % | **Fail at 50**, pass at 60 | Tuned against at 50-60. Independent at young ages, where it fails: inside only at 15-17 and 55-60 |
| Site-index height, SI 20-26 (Eriksson et al. 1997) | forests, top height | 21.35 (18.76-25.12) | 23.14 (20.72-26.73) | | Pass | By design |
| | forest-grown trees | 21.91 | 23.71 | 100 % / 100 % | Pass | By design |
| Crown ratio in dense young stands, 0.30-0.45 at ages 11-22 (Niemistö 1995; Repola 2008) | forests | – | – | 1 tree of about 27,000 at 11; none later | **Fail, far off**: 0.92 at 11, 0.96 at 15, 0.94 at 20, 0.93 at 22 | Independent |
| Stand density, 880 stems/ha at 45 (Hagemeier & Leuschner 2019) | forests | 953 at 45 | | | Information | Tuned against |
| Open-grown crown width (Hemery et al. 2005) | lone trees | 8.65 | 9.35 | | Information | By design |
| Crown ratio, managed stands, at least 0.5 (Repola 2008; Hynynen et al. 2010) | forest-grown trees | 0.53 | 0.45 | 85 % / 15 % at or over 0.5 | Information | Tuned against |

Light and leaf area are one result, linked through the extinction coefficient k = −ln(light / 100) / LAI. In the forests k comes out at 0.372 at 50 and 0.381 at 60; the measured value is 0.37. Light at the 14.8 % median would need a leaf area index of 5.13 at 50 and 5.02 at 60.

Not scored yet: bark thickness, wood density, carbon fraction, turning moment and foliage biomass. Seedling targets need seedling runs, which weren't part of this check.

## What is still wrong

- **Young forests' crowns reach the ground.** Crown ratio 0.92-0.96 at ages 11-22 (20 plots, mean height 3.3-9.8 m), against 0.30-0.45 (Niemistö 1995, cited through the targets file; the paper itself is not yet opened). A likely cause, not yet tested: lower limbs and short shoots stay alive in deep shade. The light at which they die was lowered to 0.15 to keep light under the canopy in its band, which works against this.
- **The crown starts too low on young trees.** At 13.5 m tall, the lowest live branch is at 0.8 m (0.2-1.8) and the crown base at 1.6 m (0.5-2.9); none of 20 trees is in the 5-7 m that Hynynen & Niemistö (2009) give at 13-15 m tall.
- **Too much leaf in young forests.** Leaf area index is under 2.5 at ages 6-14 and over 4.5 at 18-54, peaking at 5.63 at 27, against the Baltic band of 2.5-4.5. The band's own source is in doubt.
- **Light near the top of the real range.** 18.5 % at 50 and 19.0 % at 60 in the forests, against a median of 14.8 %.
- **Leaves too big.** Leaves are sized by light, 10.2-18.1 cm²; runs measured a mean of 17-17.8 cm². Real birch: 11.9 ± 5.7 cm² (Konôpka & Pajtík 2026, trees aged 4-20). The steady 15.00 cm² a leaf in the yearly statistics is an artefact, not the leaf size. Smaller leaves at the same count gave stems 7-9 cm thicker.
- **No double tops.** 0 of 20 trees, against 35 % (Zeltins 2018). Second tops are started, but don't last. The cause is unknown.
- **Long hanging strands on lone trees.** The longest are 5.2 m at 50 and 6.1 m at 60; at 60, 90 % are under 4.1 m (3.9-4.3). Photos suggest about 2-4 m, judged by eye.
- **No early deaths in young dense forests.** None of the trees in a 9,000 per hectare plot die in their first 5 years. Real young stands lose stems at this stage. Self-thinning can't start until stems past 1.3 m make the stand dense, the suppression hazard needs a stem diameter, and the carbon rule kills none. Trees on the height curve stay under 1.3 m for their first years.
- **Young trees grow almost no roots.** A 6-year tree has one root axis, 10 cm long. At 14, the roots at the collar add up to 0.69, under the lowest stand Kalliokoski measured (0.86). Laitakari (1934, p. 182): small trees "may have only 2-3" main roots.
- **Old trees die of carbon shortfall after 120.** Crowns are lost from below. No source gives a rate.
- **Foliage in stands hangs in single strands,** where real birch has clumped sprays.

In the runs above, whether a small tree uprooted could depend on rounding: root strength was read in steps of 0.01 kNm. The species file now reads it unrounded (`anchorage.moments_unrounded`).

## How the model departs from a real tree

- A forest-grown single tree's neighbours are copies of itself. Use `cambium.forest` for separate trees.
- Height follows a curve by design.
- Leaves come per node: two and a half per short shoot. Their size is set by light alone.
- Open-grown trees: leaf area is capped (leaf area index 5 over the crown), and spare carbon goes to the stem only up to 2.4 cm per metre of height.
- In stands, a limb's reach stops at 1.15 times half the spacing.
- Branches are shed, but nothing lands on the ground, and hanging dead branches aren't modelled.
- Cutting, felling, wounds and stump sprouts aren't modelled yet.
- Bark colour, peeling and autumn colour are in the look, but most look values were set by eye, and a few to taste. None is scored against data.

## Guessed values that matter most

The values with the most effect on the results are TUNED or VERIFY. For example, the light at which short shoots and branches die (0.15) is tuned to the light under the canopy, and no longer matches Hagemeier & Leuschner's 21 % for the lowest shade leaves. The full list, each with what it was tuned against, is in `reference/betula_pendula/labels.yaml`. See [Species and sources](species.md).

## Tests that fail on purpose

Tests that mark a known model fault are kept failing on purpose, not skipped. One example is the young-tree collar roots test in `tests/test_roots_paid.py`. They will pass when the fault is fixed.

## Version 1.0

1.0 is planned to fix young trees: a darker canopy so that low limbs die, young roots and early deaths, plus fair tests on which nothing has been tuned. It will be judged at ages 11-22, 50 and 60.
