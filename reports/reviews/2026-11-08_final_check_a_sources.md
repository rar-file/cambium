# Final check (a): sources and targets, on 359bea4

A fresh checker (PROTOCOL 7a) ran on 2026-11-08 and made no edits. Its report follows below, kept as written apart from formatting.

## Builder's notes (added after reading)

- **Finding 1's impact claim rests on a stale folder.** The checker read `Cambium-int/out/bench/ensemble/node_v1_plots/plot_1/plot.json`. That folder was an old run at 0dd7b41 (2026-11-07 08:23) under the same label, with damage off. I've moved it to `node_v1_plots_old_0dd7b41`.
  - The final plots run on 359bea4 with `cases/crown2_with_roots_speed.txt`, which sets `damage.old_age.enabled=true`. So `Mortality.old_age_elsewhere` is true (`plot.py:173`) and `thinning.old_age_rate` isn't used. node_H_plot200 (e277a9a) shows the same setting in its plot.json.
  - The code fault is real: the yearly hazard is wrong whenever damage's old age is off. It's being fixed. It doesn't touch node_v1_200 or the old-tree fix figures.
- **Finding 7 is accepted.** The open-tree width matching Hemery holds by construction. I reported it to the maintainer as a check (19:51 log); that's being corrected.
- ASK MAINTAINER items go to QUESTIONS.md as Q30-Q36.

---

## Checker (a), sources and targets: 359bea4 (reset-integration)

I made no edits to the repo. Cambium-int is still clean at 359bea4 and Cambium/master is clean too. I ran nothing heavy: git, file reads, small read-only YAML/PDF-text scripts, curl and web fetches. Five read-only helper agents re-opened the sources in parallel. Their downloads are in `birch-data\checkA_2026-11-08_*`.

**Access limits this round:**
- The Chrome extension was not connected.
- mdpi.com returned 403 to curl and WebFetch for every Forests or Plants paper.
- Taylor & Francis, Elsevier and Oxford returned a bot check or a paywall.
- No one tried mdpi-res.com, so as not to go round a refusal.

### Findings, most serious first

| # | Mark | Finding | Evidence |
|---|---|---|---|
| 1 | FIX | **Old-age mortality in the mortality block misreads Elfving.** `treegen/thinning.py:113-116` uses p = 1/(1+exp(10 − 12A/Amax)) as a yearly hazard, on total age (`plot.py:481`). Elfving 2010 p. 68 says p is "the probability that a tree has died by age weakening at age A", with p(m5) = [p(A+5) − p(A)]/[1 − p(A)], and A is breast-height age (p. 67). `treegen/damage.py:122-131` does it right. The species comment at line 1236 also says "a year". This path runs whenever `mortality.enabled` is on and `damage.old_age` is off. The checker said that was the setting in the final plots, citing a stale folder (see the builder's notes). The hazard is about 25-29 times the source's: at age 200, 0.163 a year against 0.0057. | Elfving PDF pp. 67-68 |
| 2 | FIX | **Open-grown runs are saved as stand trees.** `tools/tree_table.py:335` writes `"mode": "stand"` even with `--open`. The final check's open trees say mode "stand", with no stand spacing and no subcanopy light. `scorecard.py:56` maps "stand" to stand-tree/managed. Scoring them would wrongly apply the LAI, height and crown-ratio targets to open trees, and would skip `crown_width_open_grown`. | file:line |
| 3 | FIX | **Wrong PDF, still there.** `birch-data\02_branch_architecture\Niemisto_1995_Crown_branch_properties_silver_birch.pdf` is Tuomela & Kanninen 1995 (Eucalyptus microtheca, Silva Fennica 29(3):217-224). `catalogue.csv` row 12 has the wrong DOI (sf.a9209) and licence. Known since M1 (Q15). All other referenced local files match their claims. The Zubizarreta filename says "birch", but the paper is mostly Scots pine. | |
| 4 | FIX | **Labels that say "sourced" for a value that was worked out, is second-hand, or isn't on the page cited.** See the table below. | |
| 5 | FIX | **labels.yaml doesn't agree with the species file.** 109 keys added since f659fc5 (outside appearance and speed) have no label; 46 numbers therefore count as VERIFY "no label", although the comments call many SOURCE. The appearance block's provenance says 12 SOURCE, 13 DERIVED and 78 TUNED, but `species_schema.read_labels` scores them as 204 VERIFY and 1 TUNED. | script over both files |
| 6 | FIX | **Guesses labelled TUNED** with no target: crown_frame.gap_scatter, steep_limit, chase, twig_shoot_max_m, limb_rivals; roots.paid.collar_primordium_lifespan; height_driver.store_fraction. Borderline: height_driver.light_full and water_full. These should be VERIFY, or say what they were set against. | species file |
| 7 | FIX | **Matches that hold by construction are reported as agreement.** crown_frame caps a limb's reach at Hemery's crown (`growth.py:2196-2205`), so the open-tree width "8.55 / 9.32 m (Hemery 8.70 / 9.52)" isn't a test. The same holds for height under height_driver. | code |
| 8 | FIX | **The LAI target is quoted as "at least 3.6"** in reset_brief.md:45, tree_handover.md:35 and tree_table.py:40. The approved band is [3.6, 5.4]. tree_table also hard-codes other target bands (lines 40-43) instead of reading the tag. | |
| 9 | FIX | **The light height is overclaimed.** `tools/tree_table.py:406` says "diffuse, at 1-2 m, as the target measures it"; the target says the sensor's height "is not stated". | |
| 10 | FIX | **Source comments with wrong numbers or pages.** See the list below. | |
| 11 | FIX | **A top-height column under the wrong name.** stand_table's "Top height (m)" is the mean height of the 100 thickest, not the approved Naslund-curve top height (`targets.yaml:160`). The scorecard does it right. | |
| 12 | FIX | **A non-target used as pass/fail and as a tuning target.** The open DBH band [30, 50] is `reference.dbh.open_grown_band_cm`, VERIFY and not a target; its source (Dubois, Claessens & Ligot 2021) was read only as an abstract, and the figure is a potential, not a band. stem_cm_per_height_m and surplus_to_stem are TUNED against it; mark that abstract-only. | |
| 13 | ASK MAINTAINER | The Baltic LAI target's conditions don't match Uri 2012: only 1 of 8 stands on abandoned farmland, two young stands thinned, and no LAI printed anywhere. Keep, correct the text, or drop the band? | |
| 14 | ASK MAINTAINER | The seedling root:shoot target isn't printed in Konôpka 2023: no ratio, no ages 1-3, no 0.4-1.5 m band. A recomputation falls inside the band, but the band isn't on the page. "Laitakari 1935" is printed 1934. | |
| 15 | ASK MAINTAINER | Hagemeier stand 2 doesn't add up: 420 stems/ha at 25 ± 3 cm gives about 20.9 m²/ha, not 28.5. The paper was blocked. | |
| 16 | ASK MAINTAINER | sdi_max against Lee 2025 (full text open in Jukuri, CC BY): k1 11.9013, Nmax 898 at Dq 25 cm, for plantations. Should Lee's line stand, or the natural-stand 763? | |
| 17 | ASK MAINTAINER | Which targets are still tests? Height is set by height_driver, width capped by crown_frame, and light and LAI tuned against through the shedding thresholds. | |
| 18 | ASK MAINTAINER | Old target wording: Repola's targets say mode "managed", but most plots were naturally regenerated and mixed (34 % B. pubescens). The Krišāns 101 kN m/m³ is called "an empirical regression" but is the builder's fit through two site means. Both INFO. | |
| 19 | ASK MAINTAINER | Access: the maintainer's browser, or an approved route, is needed for Hagemeier 2019a and b, Zeltins 2018, Krišāns 2022, Liu & Evans 2021, Fedorov 2024, Jones 2021 and 2023, Thomas & Martin 2012, Donis 2024, Hemery 2005, Hansen 2023, Eriksson 1997, Niemistö 1995 and Hynynen 2010. Hemery's crown_a/b drive the crown frame unread, and two different "Hemery Table 1" lines are in the file (0.96 + 16.2·d(m), and 0.932 + 0.177·d(cm)). Confirm three routes used: Lee via Jukuri; the Liu & Evans abstract via Mount Sinai's research portal; Uri 2012 via Varik's thesis reprint on EMU's repository. | |

### Finding 4: labels that overstate

| Value | Label says | Source says |
|---|---|---|
| damage.dbh_over_bark_factor 1.098 | sourced | Worked out, with Hansen's intercept dropped; Hansen blocked |
| damage.stem_form_factor 0.45 | sourced | Computed from two site means |
| damage.old_age.years_to_breast_height 5.5 | sourced | 150/27.5, where 27.5 is VERIFY |
| damage.snap.beta_concentration 3.2 | sourced, "SD 24 %" | Fig. 4 bar chart, no SD printed; 3.2-3.5 by eye |
| damage.snow.return_years 5 | sourced | Southern Finland's figure, used for Uppland |
| damage.wind.intercept "at the means" | sourced | Inferred from figures |
| height_driver.reference_age_years 50 | "Elfving App. 9" | Not on that page; rests on Eriksson 1997, unopened |
| regeneration.spread.mast_share | sourced, p. 739 | p. 740, second-hand from Sarvas 1948; a reading |
| regeneration.spread.mast_factor | sourced | A ratio; Table 3 gives 5.1 and 3.9 |
| regeneration.spread.seed_min_dbh_wood_cm 11 | sourced | Converted from 12 cm through the model's bark |
| architecture.branch_angle_deg [43, 42, 48] | sourced | Only 43 is sourced; Zeltins blocked |
| plot.height_follows_dominants | sourced | Paraphrases Elfving p. 58 wrongly ("height on the height curve at the mean diameter of the 100 thickest") |
| roots.paid rel_sum_d2, wood_density, fine_root_turnover, far_d_exponent | SOURCE | DERIVED |
| roots.paid dS = 2 + 1.25d | SOURCE | Repola p. 611: "a transformation rather than an estimate of stump diameter" |
| appearance chlorophyll_ramp | SOURCE | Worked out; the soybean anchor is 0.0371, not 0.038 |
| black.height_m, at_dbh_cm | SOURCE | Means of three trials; Jones blocked |
| black.tree_range low end 0.15 | DERIVED | A choice: the ratios give 0 and 0.22 |
| mortality.vigour.relative_size_slope | comment TUNED, labels VERIFY | Disagree. Now settled at −3.263 by Maleki & Kiviste Table 3 |

### Finding 10: wrong numbers or pages in source comments

- **Hökkä 2012 (line 1130):** 3,010 birch/ha after five seasons (pp. 696, 702), not "about 3,400 after 6".
- **Dahlgren Lidman Table 2 (1022):** the range is 3.3-17.6 seedlings per m², not 9-18.
- **sdi_max "the highest SDI" (1169-1175):** Martinik's age-18 row gives 766.
- **rate_at_max (1180-1186):** fitted to Martinik "17 to 22", but those are two different stands; each stand's own recount shows no loss.
- **Lee "intercept isn't in the abstract" (1170):** out of date; the full text is open.
- **collar_evenness (1500):** the figures are on p. 185, are means for strong- and weak-rooted trees, and use the horizontal diameter (the narrow way).
- **collar_spacing (1514):** Kalliokoski Table 1, not Table 3.
- **Table 7 (1495-1505):** Eq. 2 parameters, not taper values; the fits reach zero at 6.6 and 8.5 m.
- **length_per_reach 1.07 (1707):** needs an unstated 1.1 bark factor; Hemery at 10 cm gives 1.14; 1.54 m is a chord in a model figure.
- **crown_lai_max note (1726):** recomputing Repola Eq. 12 gives 3.6, not 3.2.
- **size_cv (1894):** Kovacic CV runs 11.6-15.9 %; Caesar's 13.2 cm² is for short-shoot leaves.
- **Söderberg (`stand_table.py:35`):** reproduces only at SI(pine) 26, pure broadleaf, 800 stems/ha.
- **Thomas & Martin citation (`targets.yaml:224`):** pages 332-352.

### OK (summary)

- targets.yaml: no diff against `targets-approved` (bb3048c). scorecard.py, reference.py and bark.py are unchanged since the tag.
- Species defaults: no value changed since f659fc5. 519 keys were added, all off or null.
- The scorecard applies scenario, mode, age, density and options conditions as written. Plot top height uses the approved Naslund definition.
- About 200 numbers re-read exactly or within rounding: Kitenberga, Nykänen, Zubizarreta, Elfving (listed pages), Aosaar, Martinik, Maleki & Kiviste, Tiebel, Lee, Repola, Kalliokoski, Laitakari, Lintunen, Konôpka, Viherä-Aarnio, Caesar, LOPEX, Kovacic & Nikolic, Konôpka & Pajtik, Juola, Zhang.

### VERIFY items and what settles them

| Item | Settles it |
|---|---|
| Baltic LAI 2.5-4.5 | Its real source, or drop it (Q) |
| Eriksson 1997 table, SIS reading | Eriksson et al. 1997 Table 3, Eq. 4 |
| Light sensor height | Hagemeier 2019b Methods 2.3 |
| spread ln_mean Eq. 2 sign | Liu & Evans 2021 Eq. 2, Table 1 |
| spread windthrow_mineral 0.12 | Šamonil et al. 2010 |
| mortality.vigour.relative_size_slope | Settled: Maleki & Kiviste Table 3, −3.263 on a logit |
| damage.wind.min_dbh_cm 14 | Settled: p. 3 |
| damage.old_age.site_index_sis_m 27.5 | A choice; make it agree with height_driver.site_index 23 and mortality.old_age's SIS 26 |
| damage.snow.break_share 0.063 | Donis et al. 2024 |
| crown_frame.crown_a/b; reference.crown | Hemery 2005 Table 1 |
| crown_frame angles and fork_share; branch_angle | Zeltins 2018 |
| reference.dbh.open_grown_band_cm | Dubois et al. 2021 full text |
| hansen_double_mm and its units | Hansen 2023 and correction |
| black.*; leaf angle_by_height | Jones 2021, 2023; Hagemeier 2019a |
| 46 unlabelled numbers, appearance block | labels.yaml entries |
| About 200 older VERIFY values | A page each, or a TUNED label naming its target; not re-checked this round |

### Sources opened

| Read level | Sources |
|---|---|
| Full text | Kitenberga 2021; Nykänen 1997; Zubizarreta 2012; Elfving 2010 (pp. 1-3, 9-10, 54-59, 62-68); Aosaar 2016; Repola 2008; Martinik 2018; Maleki & Kiviste 2016; Tiebel 2020; Hökkä 2012; Lee 2025 (Jukuri); Dahlgren Lidman 2024; Kalliokoski 2008; Lintunen 2013; Konôpka 2023 (PMC HTML); Viherä-Aarnio 2017; Kovacic & Nikolic 2005; Konôpka & Pajtik 2026; Juola 2020; Zhang 2020; LOPEX93 metadata; Uri 2012 and Varik 2015 (Varik's 2014 thesis, EMU repository); taperNOR 0.2.1 code |
| Part read | Caesar 1983; Laitakari 1934; the Niemistö file (page 1: the wrong paper) |
| Abstract only | Liu & Evans 2021; Dubois et al. 2021; Hagemeier 2019a and b; Thomas & Martin 2012; Hynynen 2010; Sims 2009; Huth & Wagner 2006 |
| Blocked | MDPI papers (403); Hansen 2023, Eriksson 1997, Niemistö 1995 (T&F bot check); Hemery 2005, Uri 2012 publisher pages (Elsevier); Konôpka PMC PDF (proof-of-work check) |

**Not done:** the roughly 200 older VERIFY values one by one, values behind blocked sources, other Elfving pages, and master-only log claims (Forests 2020 abstract, Vakkari 2009, Gailis 2020).

**Count:** about 200 numbers or conditions checked against a page, about 45 couldn't be (blocked); 162 new species values and 205 appearance values checked for labels. 12 FIX, 7 ASK MAINTAINER.
