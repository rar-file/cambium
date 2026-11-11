# Challenge: validation design of 2026-11-11

Challenger: Opus 5.5, ID `claude-opus-5-5`. Written 2026-11-11. Read only; no model run, no pytest. Challenges `reports/design/2026-11-11_validation.md`.

**Verdict: sound with changes.** The main diagnosis holds: no independent scored row applies at 50 or 60, and the branch-wood row is tuned. But one diagnosis points the wrong way (leaf area per kg). The pass rule, applied to the design's own rows, disqualifies some of them. And after the changes the 50/60 header would still read at most "1 of 1". The design doesn't say so.

## What I confirmed (code or saved data)

- **Branch wood is tuned.** `species/betula_pendula.yaml:652-654` says `branch_sapwood_senescence: 0.30` is "TUNED, against Repola's branch wood". `tools/independent_checks.py:77-78` says "no value was set against it". CONFIRMED.
- **`twig_bud_every` isn't read.** Its TUNED comment is at `:1826-1829`. It isn't read with `earned: true` (`:1832`, `:1837`). Calling stem wood "seen" is fair. CONFIRMED.
- **Labels.** `labels_cover.py` with the project venv: 812 values, 381 labelled, 370 unlabelled non-switch values, 312 of them `appearance`, so 58 are left. **38** unlabelled values have a TUNED comment, not 37, which is trivial. One of them is `height_driver.light_full` (`:1662`), which touches the height driver. CONFIRMED.
- **No kind field.** `targets.yaml` has no `kind` field. Its `dense_unmanaged_stand` conditions are ages 11-22, "NOT a target for mature stands". CONFIRMED.
- **Recomputed from the 20 saved plots with my own script** (`chk1.py` in the scratchpad):
  - Stems at 50 / 60: 667 / 474. Basal area: 24.7 / 26.78 m².
  - LAI: 4.51 / 4.29. Light: 18.09 / 19.33 %. Light is `subcanopy_light_pct` from plot.json, which runs 0.1 % under the design's 18.2 / 19.5. I didn't trace which light field the design used.
  - Crown ratio: 0.468 / 0.421. Diameter spread: 0.147 / 0.146.
  - Leaf area per kg: 19.42 / 19.06 m²/kg.
  - Deaths: 22,969 self-thinned of 31,052, and 1 "died" (the upkeep rule). All CONFIRMED.
  - `node_cd2_C+C2` and `node_f5_plots` give identical yearly stats. The run reproduces.
- **Q40 row A (my own script, `chk2.py`).** The 100 thickest per ha have their lowest live branch at 2.56 m at height 13.34 m (age 25) and 5.00 m at 15.56 m (age 30). CONFIRMED.
- **README claims, spot-checked:**
  - `README.md:14` `pip install pycambium`.
  - `:106` "21 %".
  - `:136` "never thins... own carbon".
  - Public `overlay/README.md:31-33, 121-127` read as the design quotes them.
  - I didn't check PyPI.
- **Dahlgren Lidman 2021**, opened at silvafennica.fi/article/10485 through the page summariser, not the PDF:
  - Table 1 birch: 11,425 (SD 4,106) and 10,642 (SD 1,023) stems/ha. Mean diameter (QMD) 5.2 / 5.7 cm. Dominant height 13.8 / 14.8 m. Basal area 22.9 / 27.1 m².
  - At 42, the unthinned control: birch basal area 31.4 (SD 2), QMD 9.5. Crown ratio 42 (3) %, and 50 ± 7 % in 2010.
  - **The paper states that its "±" values are standard deviations.** That settles the design's open point.

## Problems

### P1. The leaf-area diagnosis points the wrong way (CONFIRMED in code)
The design suspects the stats, which count every leaf at 15 cm² (`growth.py:3161`). The code says otherwise:
- **Leaf mass per leaf is fixed.** Leaf dry mass is bud weight × 15 cm² × LMA (`growth.py:869`, `:1479`). The bud weights already include each leaf's size (`_size_rel`, `:243-248`, `:1497-1500`). Size is 15 cm² × 60.8 / LMA (`:1452-1453`, `size_lma_exponent: 1.0`), so every leaf weighs about 0.091 g whatever its light.
- **Correct counting wouldn't fix it.** Counted with each leaf's true size, area per kg would be 1/LMA. That is 19.8 m²/kg for a shade leaf (LMA 50.5 g/m²), which is where the model already sits (19.1-20.5).
- **What sets 19-20 m²/kg is the leaf-thickness rule.** LMA = 50.5 + 38.7 q^3.3 (`species:400-402`, exponent marked VERIFY). Under it nearly every leaf in a closed canopy is a thin shade leaf. Varik's 12.7-15.1 m²/kg means a mean LMA of 66-79 g/m².
- **Shading and reporting use different leaf areas.** The weights that shade (`:681`) include leaf size. The reported LAI (`:3161`) doesn't. Fixing the count as the design implies would raise the reported LAI, by up to about 20 % in shade (SUSPECTED size), and push the two tuned LAI rows further over. The design must name this risk.

### P2. F12 fails the design's own rule 1
Leaf area per kg is LAI over leaf mass. LAI is tuned (`stem_theory.wind_speed_m_s`, labels.yaml:132). Leaf mass (F11) is "partly" tied to it. So F12 is "a figure tied to a tuned one by a formula inside the model", which rule 1 excludes. Yet the design puts it in the held-back independent pool.

### P3. F1-F3 are one finding, and rule 1 is ambiguous about them
- **Stems are a tuned quantity.** `wind_speed_m_s` was tuned against "Dg, stems/ha and LAI on plots" at 50/60 (labels.yaml:132). `sdi_max`, `rate_at_max` and `shape` were tuned too (`species:1212-1231`).
- **The design is inconsistent.** Its rule 1 names stems, diameter and basal area as tied figures, yet it calls stems and basal area against Dahlgren Lidman independent.
- **Needed:** state whether "independent" means "a source never on the table" or "a quantity never tuned". Same quantity, new stand is honest out-of-sample evidence. It should be labelled as that, not "nobody set a value against these".
- **F1, F2 and F3 are one symptom counted three times.** Relative density (RD) holds at 0.84 from age 20 to 30. Stems fall from 9,335 to 2,657 while the ceiling stays at 763, and the plots start at about 16,000/ha with no ingrowth (plot.json `new_trees` 0).
- **Evidence for 763 is left out.** The species file cites Martinik et al. 2018: 731, 743 and 766 (`:1214-1215`). The design mentions none of them.
- **"Tuned on one stand" is wrong for the rate.** `rate_at_max` was fitted to Aosaar and Martinik (`:1225-1230`). That also applies to the README wording "a crowding rule fitted to a measured stand".

### P4. Dahlgren Lidman doesn't match as cleanly as the design says
- **Both birches.** The birch is *B. pendula* and *B. pubescens* together.
- **Spruce underneath.** There are 2,473-3,158 spruce/ha, 2.9 m² of basal area, with a crown ratio of 0.79. The model's plots are pure silver birch. F3's density indexes must say whether spruce is counted.
- **No site index and no ages printed.** "A site like the model's" rests on height alone. Table 1 has no age column. 30, 33 and 42 are years since the 1977 felling.
- **Counting rule not stated.** Table 1 was measured before a biomass harvest, and the smallest diameter counted isn't given.
- **The volume tables disagree.** Table 5's birch 257 plus spruce 33 is 290 m³, against Table 4's 315.
- **Row E breaks rule 4.** Two sites means INFO under the design's own rule, yet E is scored. F7 (two stands) is held at INFO. That is one rule applied two ways. The SD is between plots, not between stands.

### P5. The 50/60 count barely moves, and the test plan wouldn't show it
Under the design's own rules, which independent rows could be scored at 50 or 60?
- **F4:** the source has no point at those heights.
- **F7:** two stands, so INFO.
- **T2:** one planted stand, so INFO.
- **F12:** tied to LAI (P2).
- **Uri 2012:** one 60-year stand, so INFO.
- **T4 (Repola A6)** is the only candidate. At 60, only **44 % of stems and 32 % of basal area** lie inside its 11-26 cm range (CONFIRMED). A6 would be scored on the smaller trees.

The header would read "0-1 of 0-1". The yield tables are the only route to more, and they are model-like averages, not stands. The design must say which basis under rule 4 they would meet.

### P6. Top height is used two ways
At 30, the appendix uses 15.21 m (the approved definition). F1, F10 and T1 use 15.56 m (plot.json `top_height_m`). At 50 / 60 plot.json reads 21.58 / 23.26 against 21.39 / 23.14.

The ±2 m matching rule is about 4-5 years of growth at 30 on SI 23. That is loose for crown ratio and stems, which change fast then. The 13.8-14.8 m against 15.2-15.6 m match sits at the edge of it.

### P7. A tuned-against source is missing, and one kind has no block
- **Konopka.** Crown fix C was TUNED against Konopka et al. 2023's young leaf area for height (DECISIONS 107). Section 1 doesn't list it. Young LAI, leaf mass (F11, D) and young crowns are all downstream of it.
- **"Seen".** T3 and T6 are "seen" rows, but the three-block scorecard has no place for them. They should go in block B.

### P8. Smaller points
- **The carbon rule kills more than 1 tree.** "1 death by the carbon rule" is right for upkeep (`plot.py:458-467`). But the 533 "failed to establish" deaths are the no-carbon rule (`plot.py:444-456`). The README rewording should name both.
- **Unread sources.** Repola's A6 band (×0.81-1.23) and the Varik and Aosaar figures were not reopened by me (UNVERIFIED by me). Aosaar and the Finnish guide were read through a summariser, as the design admits.
- **T4's band was proposed after the result was seen.** It came from Repola's printed spread, so it can stand, but its page must be recorded before the release run.

## Breaks of the owner's rules
- **None found.**
- **Q40 is still open** (QUESTIONS.md:7). Commit 20a14e1 only added the question. So making A INFO and dropping B loosens nothing that was approved.
- **Make the 0.89 m failure visible.** Stand trees miss row A, and block C should still print that as FAIL text beside the INFO.

## Changes required before anyone implements it
1. **Rewrite the leaf section (P1).** Drop "15 cm² is the cause".
   - Name the LMA-vs-light rule (`lma_exponent` 3.3, VERIFY) and canopy light as the likely cause.
   - Add a row checking that reported leaf area equals the leaf area that shades.
   - State that correcting it may raise the tuned LAI.
2. **Take F12 out of the independent pool**, or rule that a ratio of a tuned figure is never independent (P2).
3. **Define independence explicitly** (source never on the table, or quantity never tuned).
   - Add an "out-of-sample" kind for F1-F3 and F5.
   - Count F1-F3 as one finding.
   - Cite Martinik 2018 beside the 763 ceiling.
4. **Record Dahlgren Lidman's conditions in each row's `conditions`.** Mixed species, spruce understory, no site index, ages since felling, unknown smallest diameter. Mark the ages as inferred.
   - Make row E INFO under rule 4, or change rule 4 for both E and F7 alike.
   - Re-read Tables 1, 4 and 5 in the PDF, not through a summariser.
5. **Give every equation row a diameter-range rule.**
   - Print the share of stems inside the range.
   - The row is INFO when under two thirds are inside, which T4 at 60 already is.
6. **State the expected 50/60 header** after the changes (0-1 of 0-1).
   - Make opening a stand series with a band basis at 50-60 a precondition of the release run, not a later step.
   - Say what rule 4 makes of yield tables.
7. **One top-height definition** (the approved one) everywhere.
   - Tighten by-age matching to ±1 m, or match crown and stem rows by height always.
8. **Fill the gaps in the kinds.**
   - Add Konopka 2023 (crown fix C) to the list of tuned-against sources.
   - Put "seen" rows in block B.
   - Fix the counts: 38 TUNED unlabelled, `rate_at_max` fitted to two stands, establishment deaths in the README wording.
9. **Test plan.**
   - Add a unit test that block C can never count a row whose `tied_to` names a tuned target.
   - Save `leaf_size`-weighted leaf area beside the count.

## Scripts
- `<scratchpad>\chk1.py`: stems, deaths, crown ratio, area per kg.
- `<scratchpad>\chk2.py`: the 100 thickest per ha.
- The design's `labels_cover.py`, run with `.venv\Scripts\python.exe`.
- Inline: the share of stems inside A6's range.
