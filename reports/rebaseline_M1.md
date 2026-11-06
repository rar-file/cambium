# One-off ensemble re-baseline (DECISIONS.md rows 28, 39)

**In force.** Checker A confirmed the target edits and the tag moved (DECISIONS.md row 50). No-PASS-to-FAIL applies against the verdicts in the last column. "The tag" in the tables below is the previous tag, `41d18c1`, and "master" the tag as moved.

- **Machine:** the node, kernel `neoversen1`, one maths thread.
- **Code:** `68782d9`. The manifests' commit is null, because the node had no git; 24 of 24 Python files were checked against that commit (DECISIONS.md row 35).
- **Seeds:** 1-20 for trees, 1-5 for plots, natural mode, 100 trees at the start, 556 m².
- **Routes:** the five plots count as one ensemble, on the route check (row 42): seed 1 resumed and straight, 302 of 302 files identical; seed 2 is the straight run; seeds 3, 4, 5 straight with no save files.
- **Source:** `tools/verdict_table.py`; output at `out/bench/ensemble/verdicts_two_refs.txt`. "Share" is the share of seeds inside the band.

## Stand trees, 20 seeds

| Target | Age | Mean +- SD | At the tag: band top, verdict, share | At master: band top, verdict, share |
|---|---|---|---|---|
| Height (m) | 20 | 14.89 +- 0.48 | 14.31, FAIL, 5 % | 13.61, FAIL, 5 % |
| Height (m) | 30 | 19.73 +- 0.71 | 19.67, FAIL, 35 % | 19.24, FAIL, 20 % |
| Height (m) | 40 | 23.07 +- 0.75 | 23.07, **PASS**, 45 % | 22.79, FAIL, 35 % |
| Height (m) | 50 | 25.29 +- 0.62 | 25.31, **PASS**, 60 % | 25.12, FAIL, 30 % |
| Height (m) | 60 | 27.07 +- 0.74 | 26.87, FAIL, 40 % | 26.73, FAIL, 30 % |
| LAI | 50 | 3.09 +- 0.41 | band 3.6-5.4, FAIL, 10 % | same |
| LAI | 60 | 3.27 +- 0.37 | band 3.6-5.4, FAIL, 20 % | same |
| Diffuse light (%) | 50 | 30.1 +- 4.2 | band 6.4-19.8, FAIL, 0 % | same; +15.3 points from the median of 14.8 % |
| Diffuse light (%) | 60 | 27.5 +- 2.7 | band 6.4-19.8, FAIL, 0 % | same; +12.7 points from the median |

**How near these height verdicts are** (`out/bench/m1/figures.txt`, from unrounded bands): at master, age 40 is 0.28 m over the band top (1.66 standard errors of the mean), age 50 is 0.16 m (1.17), and age 60 is 0.34 m (2.03). Age 20 is 1.28 m over (11.8), and age 30 is 0.49 m (3.09). **At the tag,** the passes are thin: age 40 by 0.003 m (0.02) and age 50 by 0.03 m (0.20).

## Plots, 5 seeds

| Target | Age | Mean +- SD | At the tag | At master: band, verdict, share |
|---|---|---|---|---|
| Top height, on the curve (m) | 20 | 15.43 +- 0.32 | not scored: definition unconfirmed | up to 13.61, FAIL, 0 % |
| Top height, on the curve (m) | 30 | 21.78 +- 0.25 | not scored | up to 19.24, FAIL, 0 % |
| Top height, on the curve (m) | 40 | 26.17 +- 0.36 | not scored | up to 22.79, FAIL, 0 % |
| Top height, on the curve (m) | 50 | 28.88 +- 0.39 | not scored | up to 25.12, FAIL, 0 % |
| Top height, on the curve (m) | 60 | 30.59 +- 0.30 | not scored | up to 26.73, FAIL, 0 % |
| LAI, Baltic | 50 | 3.77 +- 0.03 | 2.5-4.5, PASS, 100 % | same |
| LAI, Baltic | 60 | 3.76 +- 0.02 | 2.5-4.5, PASS, 100 % | same |
| LAI, Hagemeier | 50 | 3.77 +- 0.03 | 3.6-5.4, PASS, 100 % | same |
| LAI, Hagemeier | 60 | 3.76 +- 0.02 | 3.6-5.4, PASS, 100 % | same |
| Diffuse light (%) | 50 | 22.3 +- 0.1 | 6.4-19.8, FAIL, 0 % | same; +7.5 points from the median |
| Diffuse light (%) | 60 | 22.3 +- 0.1 | 6.4-19.8, FAIL, 0 % | same; +7.5 points from the median |
| Crown ratio, dense stand | 20 | 0.72 +- 0.03 | 0.30-0.45, FAIL, 0 % | same |
| Stems/ha, INFO | 45 | 1,566 +- 52 | 880 in the source stand, not scored | same |

Each plot holds only 5.56 of the top-height trees, so the scorecard calls that figure noisy. Those trees' mean height, shown beside it, is 27.92 at 50 and 29.41 at 60: lower than the curve, and still 2.7-2.8 m over the band top. All live trees average 21.85 and 22.80 m, inside the band (`out/bench/m1/figures.txt`).

**Not like for like, and noted:** these plots hold about 1,500 stems/ha at 50-60, against 880 and 420 in the Hagemeier stands, and about 1,700 at 20, against 3,000-5,000 in the crown-ratio target's text. Stand trees' crowns cover about 0.42 and 0.58 of the ground at 50 and 60 (checker A's arithmetic), against the source's closure above 0.9. So the plots' LAI PASS isn't quoted as like for like. QUESTIONS.md Q13.

## Verdicts that changed

| Target | Before | Now, at master | Why |
|---|---|---|---|
| Stand-tree height at 40 | FAIL (seed 1, PC) | FAIL; at the tag, PASS by 0.003 m | Many seeds, at the tag |
| Stand-tree height at 50 | PASS (seed 1, PC) | FAIL | The corrected band, with many seeds: at the tag the ensemble passes by 0.03 m |
| Stand-tree height at 60 | PASS (seed 1, PC) | FAIL | Many seeds, and the corrected band: at the tag the ensemble fails too, so seeds alone do it |
| Plot top height at 20-60 | FAIL on `p38_nat` at master, by 100 thickest (28.20, 29.54 m at 50, 60); not scored at the tag | FAIL, on the curve | None at master; the definition changed |
| Plot light at 50, 60 | Not scored on `p38_nat`, which never recorded it | FAIL | Newly scored |

Old runs: `out/bench/ensemble/scorecard_seed1_pc.txt`, `scorecard_p38_nat_seed1.txt`.

## What's one failure, and what isn't

- **Too tall:** the height rows at five ages, on trees and on plots. Whether they're one problem is not calculated: the trees' excess shrinks with age (1.28 to 0.16-0.34 m), and the plots' grows (1.82 to 3.85 m on the curve).
- **Leaf area and light on stand trees: linked.** Light follows LAI at k 0.367-0.393 by age, against the paper's 0.37, which the model takes as an input. Correlation within an age is 0.705-0.892, so at age 50 leaf area explains about half of the seed-to-seed spread in light. The largest single-seed gap is 22 points at age 20, and 15.7 at age 50 (`out/bench/ensemble/light_lai_link.txt`).
- **Leaf area and light on plots: linked too, with a different verdict for each.** LAI passes and light fails. By Beer-Lambert, 19.8 % needs LAI 4.38 at k = 0.37, or 4.06-4.07 at the plots' own k of 0.398-0.399, and 3.6 gives 26.4 % at k = 0.37. So the lower part of the LAI band can't pass the light band. That's arithmetic (`out/bench/m1/figures.txt`), not a model run.
