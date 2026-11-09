# Final check (b): numbers and consistency, on reports/birch_v1_final.md at 8521164

A fresh checker (PROTOCOL 7b) ran on 2026-11-08/09 and made no edits. It checked 32 items: 16 FIX, 5 ASK MAINTAINER, 11 OK. Below is its report, kept as written apart from formatting, with my response.

## Builder's response

All 16 FIX items are accepted, and the report is being rewritten against them.

The main change of message is items 3 and 4. At 50 and 60:
- Height matches by design.
- Light and Hagemeier LAI are one result, both tuned against.
- The Baltic band was tuned against too.

So no independent target passes at 50 or 60. The independent checks that exist (young crown ratio; Baltic LAI at young ages) fail. The maintainer is told this plainly.

The ASK MAINTAINER items go to QUESTIONS.md: item 17 joins Q34, item 18 becomes Q37, item 20 joins Q32. Items 19 and 21 are fixed in the report and in tree_handover.md.

Golden proof hashes are now copied to `Cambium-int/out/bench/golden/node_gold_v1pre` and `node_gold_v1post` so they can be checked.

---

## FIX, most serious first

1. **The test record leaves out the version described.** Section 7 says only the 4 known environment failures, but the log at 23:42 says d5f0ea3 has 28 failures, 24 of them from the defaults switch, some possibly real faults: the game export KeyError 'lod0', export-then-render, root pipes, speed state and four forest tests.
2. **The report is stale against its own branch.**
   - The golden proof says PENDING; the log says done, 225 files, 0 differ.
   - The value counts are d5f0ea3's. HEAD has 21 DERIVED, 90 TUNED, 216 VERIFY and 0 older labels.
   - surplus_to_stem is now VERIFY, a choice.
   - open_grown_share is "TUNED, against photos of open-grown birches", not "a guess".
   - The header says code 8c2c496; the branch is at 8521164.
3. **The Baltic band is labelled "Independent", but plot LAI at 50-60 was tuned against.** wind_speed_m_s is TUNED "against Dg, stems/ha and LAI on plots", and the light death lines are TUNED "against LAI and light". Only the young-age Baltic readings might be independent.
4. **The "In short" passes are linked metrics counted as separate wins.**
   - Light follows LAI at a near-fixed k: 0.372 / 0.381 on plots, 0.384 / 0.395 on stand trees. The input extinction coefficient is 0.37, from the light target's own paper. So the light pass and the Hagemeier LAI pass are one result.
   - Height is by design, so no independent target passes at 50 or 60.
   - The Baltic fail at 50 and "light near the top" are one lever pulled two ways. At k 0.372, light at the 14.8 % median needs LAI of about 5.1, which fails the Baltic band by 0.6. Keeping LAI at 4.5 or less means light of at least 18.7 %.
5. **"Differ by noise only" (treesR against trees) is wrong for light at 60.** Paired over 20 seeds: light at 50 is −0.21 ± 0.22, at 60 −0.73 ± 0.30 (2.5 SE). LAI +0.05 ± 0.035 / +0.075 ± 0.047. The shift is towards the median.
6. **"With the height fix, LAI at 50 rose from 4.44 to 4.54" compares different seeds and commits.**
   - On the same 20 seeds: 4.509 to 4.542, +0.034 ± 0.036, which is noise. The height fix alone (3 seeds) gives 4.349 to 4.389.
   - Not reported: on the same 20 seeds, light at 50 rose 17.64 to 18.47 (+0.83 ± 0.26, 3.3 SE), and at 60 by +0.35 ± 0.28. The fixes were adopted on 3 seeds.
7. **The managed crown ratio 0.51 / 0.45 is from node_v1_trees.** On node_v1_treesR it's 0.527 / 0.447; seeds at or over 0.5 are 85 % at 50, 15 % at 60.
8. **"Base 1.2 m at about 14 m tall" can't be reproduced.** At 13.46 m on node_v1_treesR, the lowest live branch is 0.8 m (0.2-1.8) and the crown base 1.6 m (0.5-2.9); 0 of 20 seeds are in 5-7 m.
9. **The 200-year table mixes definitions.**
   - Top height is the cross-check. The approved Naslund height is 23.05 / 26.39 / 27.56 / 26.87 at 60 / 100 / 150 / 200, against the SI 23 curve's 23.75 / 27.50 / 29.33 / 30.17.
   - Light is sky-and-sun; diffuse is 19.1 / 19.8 / 28.5 / 42.0 / 33.6.
   - Stems are past 1.3 m; all stems are 780 / 540 / 637 / 2,117 / 1,590.
   - "All" first generation at 60 is 520-550/ha.
   - 3 plots is below the 5 needed for a verdict.
10. **"Keep their first generation past 150 years, as real ones do" goes beyond the sources.** Those say stands persist to 121-150 (abstract only) and maximum age is about 100, sometimes 150. The model has 30-90/ha at 200. Neither source was checked by checker (a).
11. **"Over the Baltic band from 20 to 50" understates it.** Over 4.5 every year from 18 to 54 (peak 5.63 at 27), under 2.5 from 6 to 14. Inside only at 15-17 and 55-60: 9 of 55 years. Q30's "near the band anyway" overstates the same.
12. **Verdicts the scorecard didn't give, and no spreads or shares.**
    - The young crown-ratio FAIL is by hand (the scorecard says not applicable).
    - Shares inside: Baltic 40 % / 85 %; plot light 75 % / 75 %; stand-tree LAI 80 % / 70 %; stand-tree light 80 % / 80 %.
    - The stand density INFO row (953 at 45 against 880) is missing.
13. **The hanging strands "5.3-6.6 m" are node_v1_open2's.** node_v1_openR gives a longest of 5.20 / 6.11 m, and p90 at 60 of 4.12 m (3.89-4.32).
14. **Stand branch wood is inside Repola's scatter** (1.5 and 1.2 times the ×/÷ 1.19), but Repola includes bark and the model is wood only, so like for like the gap is somewhat larger. Say both.
15. **Gaps in the Kind column.**
    - Stand-tree LAI is tuned against (spacing_overlap).
    - Managed crown ratio is tuned against (profile_power).
    - The Hagemeier stems and Dg comparison is tuned against (wind_speed, sdi_max, rate_at_max).
    - Hemery's widths are VERIFY and second-hand.
16. **References not on the report's branch.** The review and Q30-Q36 are on master only. KNOWN_ISSUES.md ends at M2 and is stale ("1,480-1,660 stems/ha at 60").

## ASK MAINTAINER

17. Is the young crown ratio independent? profile_power was tuned on crown ratio at 50-60, not the 11-22 band. The plots are denser than Niemistö's, and denser stands have lower crown ratios, so the FAIL holds.
18. Dropping J for "light, young LAI and crown ratio worse". Paired against H, 10 seeds:
    - Light +0.71 ± 0.45 / +0.31 ± 0.47, which is noise.
    - Young LAI +0.58 at 20, +0.85 at 22, which is real.
    - Crown ratio lower by 0.025 / 0.018 / 0.072 at 50 / 60 / 30. Lower moves towards the only natural-plot crown-ratio target.
19. **Numbers with no saved output.**
    - "Leaves about 17 cm²": the final runs give 15.00 cm² on every seed, by construction (growth.py:3116-3117). 17 came from earlier look runs.
    - "Canopy closes about 10 years late": no number given.
    - "Shorter than Niemistö's fertile stands": Niemistö is unopened.
    - "Double tops 4-6 of 20 (loose)": not in any table.
20. **Hagemeier's stands.** Stand 2 isn't mentioned in the report though Q32 says it is. Stand 1 has the same kind of problem: 880 at 19 ± 6 cm gives about 27.4 m²/ha if ± 6 is between trees, not 25.2.
21. **reports/tree_handover.md:79** says the lowest live branch at 14 m is 5.2 m, 13 of 20 seeds in 5-7 m: an older crown, not marked superseded. The final runs give 0.8 m, 0 of 20.

## OK (summary)

- The forest-grown tree table, natural forest table, plot top height (21.348 / 23.144) and young crown ratio (0.917 / 0.955 / 0.937 / 0.928) all reproduce.
- Scorecard verdicts at 50 and 60 reproduce: Baltic fail at 50 by 0.042, SE 0.034.
- Lone trees reproduce, with "by design" confirmed in growth.py.
- "Grow the same trees" holds:
  - node_v1_young matches node_v1_plots in 440 plot-years;
  - node_v1_open matches node_v1_open2;
  - node_v1_trees matches node_c2Hf20s in 1,220 seed-years.
- All runs were on one machine, at clean commits.
- Bark and conditions are like for like.
- Leaf density at the top, strict double tops and the branch-wood arithmetic are right.
- The 200-year stems, basal area and first-generation counts are right.

**Not checked:** the golden proof, the tests at 513e81c and 4e503cb, the loose double tops, and which trees died of carbon shortfall.
