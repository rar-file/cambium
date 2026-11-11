# Sources opened, 2026-11-11 (step S of the plan)

Model: Fable 5.2 (ID `claude-fable-5-2`). Plan: `reports/design/2026-11-11_plan.md`, step S. Allowed by DECISIONS 110, items 3 and 9. No model, target, test, design or species value was changed. No commit. This file is the only one written in the repository.

CONFIRMED = I read it today at the place named. SUSPECTED = my arithmetic on published numbers, or a reading I could not check. "The model" numbers are quoted from the plan and designs, not re-run.

## How it was done

- **One download**, as allowed: Hynynen et al. 2002 from Luke's repository (Jukuri), saved in the new folder `birch-data/hynynen_2002/` as `951-40-1815-X.pdf`, 17,307,766 bytes (the record says 16.51 MB), SHA-256 `64939d4a...4f9535`. My first request returned the repository's web page, not the file (348 KB of HTML under the same name); I deleted that and fetched the file itself. The folder holds only the PDF.
- The PDF is a scan with a poor text layer. I read text with `pdftotext` and read every number below from the page images, taken out of the file as JPEGs into my scratch folder. Nothing in the file was run.
- **Chrome** (the owner's, through the extension): one tab of my own, closed at the end, with the empty tab the tool made. No form filled, no login, no cookie banner clicked, no dialog. Searches at repositories were made by address.
- **Stopped at:** ScienceDirect (CAPTCHA), Oxford's repository (CAPTCHA), Springer and Annual Reviews (paywall). Three files are served only as downloads (Oikarinen 1983, Kärkkäinen 1976, Siipilehto & Kangas 2015); I checked the response headers only and did not fetch them.
- **Fries 1964** is shown in the browser by SLU, not sent as a download. I read it there: its text layer in the page's memory to find the pages, then the page images on screen. Nothing was saved.
- **Uri et al. 2012** is behind the CAPTCHA. It is reprinted in Varik's 2014 thesis. I opened the thesis record at the Estonian University of Life Sciences today (1.48 MB, 1,555,633 bytes), and read the copy already in `birch-data/` from 2026-11-08, which has the same byte count.
- One quote in this file, under 15 words. Everything else is numbers and paraphrase.

## 1. Hynynen et al. 2002: birch's own height rule (CONFIRMED)

Hynynen, Ojansuu, Hökkä, Siipilehto, Salminen & Haapala 2002. Models for predicting stand development in MELA System. Finnish Forest Research Institute, Research Papers 835. 116 p.

| What | Value | Where |
|---|---|---|
| Form, birch | 5-year height step = dominants' 5-year step × (d ÷ Ddom) ^ ((a1 + a2 × PLANT) × RDFL) | Eq. 33, p. 40 |
| a1 | 1.54405 (SE 0.1325; 95 % 1.284 to 1.804) | Table 24, p. 41 |
| a2 | −0.81202 (SE 0.1875; 95 % −1.180 to −0.444). PLANT = 1 in planted stands, so their exponent is 0.732 × RDFL | Table 24, p. 41 |
| Fit | RMSE 0.5623 m per 5 years; 2,572 observations, 1,540 trees, 402 plots. No predicted mean is printed for birch | Table 24; Table 1, p. 15 |
| Pine and spruce form (Eq. 32) | A different form: exponent = a1 × IHdom^a2 + a3 × (cr ÷ CRdom) + a4 × cr + a5 × RDFL. Pine: 0.80171, 0.43530, −0.49724, −0.64383, 0.08193; 23,992 observations | Eq. 32, Table 24 |
| Ddom | Mean diameter of the trees thicker than the basal-area-weighted mean diameter. Not the 100 thickest per hectare | Symbols, p. 9; Preface |
| Dominants' step | The 5-year step of the mean dominant tree, from the report's own dominant-height model (chapter 4.1). Site index there = dominant height at breast-height age 50 | p. 26, p. 40 |
| RDFL | Sum, over the trees larger than this tree (all species), of each tree's smallest growing space. Growing space = 1 ÷ (the self-thinning line's stem number at that tree's stump diameter) | Eqs. 20-23, pp. 30-31 |
| Self-thinning line, silver birch | ln N = 14.1979 − 2.2178 × ln(Dgs); SE 0.2853 and 0.0942; between-stand SD 0.160, residual SD 0.106. Dgs = basal-area-weighted mean stump diameter | Eq. 50, Table 34, p. 53 |
| Stump diameter | 2.0 + 1.25 × DBH (cm) | Eq. 3, p. 22 (text layer only) |
| Species | "Birch sp.": silver and downy birch together | Table 1 |
| Where the trees grew | 26 birch stands in the inventory plots (14 silver, 12 downy); birch mixed into 181 pine and 95 spruce stands, mostly under 20 % of volume; 13 thinning trials (12 silver; 11 planted, 2 self-sown; 6 on old fields), of whose sample trees 15 % were used | p. 14 |
| Data range | DBH 1.0-41.4 cm (mean 12.2); height 1.7-31.4 m; crown ratio 0.08-0.98 (mean 0.57); dominant height 2.6-31.2 m (mean 14.8); stand age 12-193 (mean 74.9); basal area 0.1-58.9 m²/ha; RDF 0.027-1.567 (mean 0.474); site index 6.6-27.0 (mean 17.6) | Table 5, p. 18 |

What the birch rule does (my arithmetic, SUSPECTED), beside the pine rule in `2026-11-11_earned_size.md`:

| d ÷ Ddom | Birch, self-sown, RDFL 0.2 / 0.4 / 0.6 / 0.8 | Birch, planted, same RDFL | Pine 1995, age 30 / 45 / 60 (from the design) |
|---|---|---|---|
| 0.4 | 0.75 / 0.57 / 0.43 / 0.32 | 0.87 / 0.76 / 0.67 / 0.58 | 0.79 / 0.95 / 1.02 |
| 0.6 | 0.85 / 0.73 / 0.62 / 0.53 | 0.93 / 0.86 / 0.80 / 0.74 | 0.92 / 1.02 / 1.06 |
| 0.8 | 0.93 / 0.87 / 0.81 / 0.76 | 0.97 / 0.94 / 0.91 / 0.88 | 0.98 / 1.03 / 1.04 |
| 1.0 | 1.00 | 1.00 | 1.00 |

- **Corrects the design.** Birch's rule has a different form from the pine one. It doesn't depend on the dominants' growth rate or on the tree's ratio a second time. It depends on how much stand is larger than the tree.
- **No catch-up.** A tree thinner than the dominants never gets more than the dominants' step, at any age. The pine rule gives it 1.02-1.06 after 45. The plan's expected failure of arm A rests on that catch-up.
- **Stronger in dense self-sown stands, about half as strong in planted ones.** The report says the same in words (p. 40).
- **Limits.** Both birches pooled, most trees were birch mixed into conifer stands, and the definitions of Ddom and of the dominants' step are the report's own. With the 100 thickest per hectare as Ddom, most of the report's "dominant" trees would get a ratio under 1 and the stand's top height would sink by construction.
- The model's plots sit at RDF 0.62 / 0.78 / 0.81 / 0.89 at 30 / 45 / 50 / 60 by this line (section 4), so a small tree's RDFL is roughly 0.5-0.8.

## 2. Hemery, Savill & Pryor 2005: crown diameter on stem diameter

| Route | Result |
|---|---|
| Publisher (ScienceDirect, DOI 10.1016/j.foreco.2005.05.016) | **Blocked:** CAPTCHA, as on 2026-11-09. Table 1 is still unread |
| Oxford University Research Archive | **Blocked:** a human-check box |
| The first author's own site, post of 2011-06-15, "How big will this tree grow?" | **Opened.** A table of crown diameter by stem diameter for nine species, from the paper's data |

Silver birch, from the author's table (CONFIRMED there, not in the paper):

| DBH, m | 0.10 | 0.20 | 0.30 | 0.40 | 0.50 | 0.60 | 0.70 |
|---|---|---|---|---|---|---|---|
| Crown diameter, m | 2.58 | 4.19 | 5.81 | 7.43 | 9.05 | 10.67 | 12.29 |
| 0.96 + 16.2 × d (m), the species file's `reference.crown` line | 2.58 | 4.20 | 5.82 | 7.44 | 9.06 | 10.68 | 12.30 |
| 0.932 + 0.177 × DBH (cm), `crown_frame.crown_a/b`, the cap | 2.70 | 4.47 | 6.24 | 8.01 | 9.78 | 11.55 | 13.32 |
| The cap over the author's table | +4.7 % | +6.7 % | +7.4 % | +7.8 % | +8.1 % | +8.3 % | +8.4 % |

- **The author's table is the line 0.96 + 16.2 × d,** to within 0.2 %. The cap the model uses is 5-8 % wider at every size. On 2026-11-09 this was read off a graph by eye; now it is from printed numbers.
- **Range:** the table runs from 0.10 to 0.70 m. The author states the trees were open-grown and that forest trees won't follow the table closely.
- **Small stems:** nothing is printed below 10 cm. The stand tree's crown at 11-20 years is held to this line at stems of 3-5 cm, which is outside the printed range. Whether the paper's Table 1 goes lower is unknown.
- Not opened: a search-result excerpt says the ratio settles from about 30 cm and the line is near-linear at 20-50 cm. SUSPECTED until the paper is read.

## 3. A published crown-contact rule

| Source | Opened? | What it gives |
|---|---|---|
| Purves, Lichstein & Pacala 2007, PLoS ONE 2(9): e870 | **Yes,** publisher, open | Canopy crowns tessellate and usually don't grow into each other. Two stated assumptions: the summed exposed crown area of canopy trees can't exceed the ground area, and with enough plasticity no canopy space is left unused. In its "shell" form each tree drops the shaded part of a potential crown where it joins a neighbour's; in the simple form one join height holds for the whole stand, and a tree keeps only the crown above it. Fitted for 250 North American species, no *B. pendula* |
| Mitchell 1975, Forest Science Monograph 17 (TASS) | **No.** No publisher or funder copy found; my DOI guess did not resolve | Still second-hand through García 2014, which C1 opened |
| Pretzsch et al. 2002 (SILVA), FEM 162 | **No.** ScienceDirect, same CAPTCHA; not tried again | Unread |
| Fries 1964 (below) | Yes | Defines crown base in the field: the lowest green branch not parted from the crown by more than three whorls (English summary, p. 219-220) |

- **For C1:** a primary, opened source now states a rule of this form. Its first assumption is C1's condition 1 (summed crown area against the ground). It is a rule about whole crowns and a join height, not about one limb in one direction, so C1's literal rule is still closer to TASS than to this.
- No source for what stops a birch limb at contact (abrasion, shade) was opened.

## 4. Measured stands and series

### 4a. Dahlgren Lidman et al. 2021, Silva Fennica 55(4): 10485 (CONFIRMED, publisher's full text)

| Point | What the paper prints |
|---|---|
| Sites | Two clearcuts of 1977 left to regenerate, 62°23' and 62°56' N, 115 and 140 m, mesic till. Five blocks; plots 20 × 30 m |
| At 30 (2007), birch | 11,425 (SD 4,106) and 10,642 (1,023) stems/ha; quadratic mean diameter 5.2 and 5.7 cm; dominant height 13.8 and 14.8 m; basal area 22.9 and 27.1 m²/ha. Spruce 2,473 and 3,158/ha below (Table 1) |
| The ± | "this and all subsequent error intervals are standard deviations" (Results 3.1). With five control plots they read as between-plot SDs (SUSPECTED) |
| Counting rule | DBH was recorded for all trees. Trees under 5 cm have their own volume function, so there is no 5 cm cut-off |
| Species | Both birches at the start. Of birches left after the 2007 harvest, over 99.9 % were silver birch (thinned plots) |
| Unthinned control at 42 (2019), birch | Quadratic mean diameter 9.5 (0.7) cm; basal area 31.4 (2) m²/ha; the 300 largest per ha 17.4 (0.9) cm; crown ratio 42 (3) %; crown length 6.08 m (Tables 4, 5). That is about 4,430 birch/ha (my arithmetic) |
| Crown ratio at 33 (2010) | Control 50 ± 7 %; thinned 44 ± 5 and 46 ± 6 % |
| Volume, "315 against 257" | No conflict. 315 ± 15 m³/ha is total production of all species (Table 4). 257 (93) is birch alone and 33 (8) spruce (Table 5) |
| Mortality | 610 stems/ha a year lost in the control, 2007-2019 |

- **Corrects the validation design:** the two volumes agree; the ± is an SD; the counting rule is known.
- **New doubt (SUSPECTED):** crown length 6.08 m at crown ratio 0.42 means sample trees about 14.5 m tall at 42. The model's top height then is near 19-20 m. The site is poorer than SI 23, so "same height at 30" does not hold at 42. No dominant height at 42 is printed.

### 4b. Uri et al. 2012, FEM 267: 117-126, as reprinted in Varik 2014 (CONFIRMED in the thesis copy)

Eight self-sown silver birch stands, Oxalis site type, south-east Estonia, closed canopies.

| Stand | Age | Mean D, cm | Mean H, m | Stems/ha | Basal area, m²/ha | Stems, t/ha | Branches, t/ha | Leaves, t/ha | Note |
|---|---|---|---|---|---|---|---|---|---|
| Järvselja | 6 | 1.3 | 3.4 | 100,000 | 12.9 | 18.2 | 4.1 | 1.7 | |
| Kambja | 13 | 5.8 | 10.9 | 7,670 | 20.1 | 58.8 | 5.0 | 3.1 | old field |
| Alatskivi 1 | 14 | 9.9 | 11.5 | 1,350 | 10.6 | 30.8 | 6.0 | 2.4 | thinned |
| Kooraste 1 | 18 | 8.0 | 13.5 | 3,630 | 19.4 | 72.3 | 5.5 | 2.9 | |
| Kooraste 2 | 28 | 15.0 | 19.8 | 1,800 | 31.0 | 77.6 | 10.1 | 3.2 | thinned |
| Alatskivi 2 | 32 | 10.8 | 17.0 | 3,210 | 29.2 | 127.0 | 9.1 | 3.4 | |
| Erastvere | 45 | 20.1 | 25.6 | 940 | 29.8 | 201.8 | 15.7 | 2.6 | |
| Aakre | 60 | 31.0 | 30.1 | 305 | 23.7 | 165.4 | 18.6 | 2.3 | storm-cut 2003-2008, under normal density |

(From the thesis's summary chapter, its Tables 1 and 3, pp. 20 and 32, which rest on Uri et al. 2012 and the thesis's other papers. I did not compare them cell by cell with the reprint's own Table 1. Current-year shoots are a separate column, 0.4-1.7 t/ha.)

- The 45-year stand is taller than the model (mean 25.6 m against 18.9 m) and denser (940 against 846/ha, basal area 29.8 against 24.0).
- Branches are 7.1 % of above-ground mass at 45 and 10.0 % at 60.
- Only one stand is near 50-60 and unthinned in effect: the 45-year one. The 60-year stand was cut. So this is still INFO at 60, as the challenge said.

### 4c. Hynynen et al. 2002: unthinned silver birch stands that were self-thinning (CONFIRMED)

| What | Value | Where |
|---|---|---|
| Data | 10 stands, 17 plots, 59 measurements. Even-aged, at least 75 % birch by volume, mineral soil, never thinned, no large damage, stem number falling in the period before | p. 21, Table 8 |
| Age | mean 61, SD 28, range 15-109 (breast-height age 56, 11-104) | Table 11, p. 23 |
| Dominant height | 20.7 m (SD 4.8; 9.9-29) | Table 11 |
| Stems/ha | 1,988 (SD 1,240; 572-6,484) | Table 11 |
| Mean diameter (weighted) | 16.4 cm (SD 4.8; 7.4-25.5) | Table 11 |
| Basal area | 23.8 m²/ha (SD 3.2; 14.9-29.1) | Table 11 |
| Site index | 27.0 (SD 5.1; 13.9-31.6) | Table 11 |

Stems against this line (my arithmetic, SUSPECTED; I used the plain mean diameter where the line wants the weighted stump diameter, which reads a few per cent low):

| Stand | Stems/ha | Mean D, cm | The line's stems/ha | Share of the line |
|---|---|---|---|---|
| Model plots at 30 / 45 / 50 / 60 | 2,640 / 846 / 667 / 474 | 9.5 / 19.0 / 21.7 / 26.8 | 4,253 / 1,089 / 828 / 533 | 0.62 / 0.78 / 0.81 / 0.89 |
| Uri, 32 and 45 | 3,210; 940 | 10.8; 20.1 | 3,359; 971 | 0.96; 0.97 |
| Dahlgren Lidman control at 42, birch only | about 4,430 | 9.5 | 4,294 | 1.03 |
| Hagemeier, 45 (tuned against) | 880 | 19 | 1,090 | 0.81 |

- **A set of measured unthinned stands that spans 50-60.** The model's basal area, 24.7 / 26.8 at 50 / 60, is inside the measured 23.8 ± 3.2 (range 14.9-29.1).
- **The model thins itself early.** Unthinned stands in Estonia and Sweden sit on the Finnish line (0.96-1.03). The model's plots sit at 0.62 at 30 and 0.89 at 60. This agrees with the plan's "too few stems" finding and puts a published line under it.

### 4d. Fries 1964, Studia Forestalia Suecica 14 (CONFIRMED on the page images; partly read)

Yield of silver birch in middle Sweden and southern north Sweden. 303 p., Swedish with an English summary (from p. 219). Built from 92 sample plots measured once, with earlier growth rebuilt from cores and stumps. The yield tables are in Appendix 8. I read one.

Table A 7, Svealand, h50 = 22, thinning programme G 1.3 (pp. 280-281), under bark:

| Total age (breast-height age) | Top height H10, m | D10, cm | Before thinning: DG cm / stems / basal area m² / volume m³ | After thinning: DG cm / mean height m / crown base m / stems / basal area / volume | Total production, m³/ha |
|---|---|---|---|---|---|
| 29 (23) | 13.0 | 15.8 | 10.4 / 1,900 / 16.3 / 90 | 11.6 / 11.9 / 3.8 / 1,100 / 11.7 / 66 | 101 |
| 33 (27) | 14.8 | 17.5 | 12.9 / 1,100 / 14.4 / 91 | 12.9 / 13.6 / 5.1 / 1,100 / 14.4 / 91 | 127 |
| 38 (32) | 16.7 | 19.4 | 14.1 / 1,100 / 17.1 / 122 | 15.1 / 15.6 / 6.3 / 650 / 11.7 / 84 | 157 |
| 49 (43) | 20.2 | 23.2 | 17.8 / 650 / 16.1 / 138 | 18.8 / 19.2 / 8.5 / 400 / 11.2 / 96 | 211 |
| 54 (48) | 21.5 | 24.8 | 20.2 / 400 / 12.8 / 117 | 20.2 / 20.4 / 9.2 / 400 / 12.8 / 117 | 232 |
| 60 (54) | 22.9 | 26.9 | 21.7 / 400 / 14.8 / 142 | 22.3 / 21.9 / 10.0 / 300 / 11.7 / 113 | 257 |

- A like-for-like test for the **stand tree** (thinned), not for the unthinned plots. The model's stand tree is 21.9 / 23.7 m at 50 / 60, about a metre above this table, so it falls between the h50 = 22 and h50 = 24 tables.
- The column I give as crown base is headed KDG, beside HDG for the mean tree's height. I read it as the crown-base height from the units and the values; the heading is not spelled out on the two pages I read (SUSPECTED).
- I did not read the definitions of H10 and D10, the other site classes, or the 92 plots' own table (Appendix 3, Table II), which holds each plot's age and height. Those plots are the measured stands; the yield tables are fitted to them.

### 4e. Not read

| Source | Where | Why not |
|---|---|---|
| Oikarinen 1983, Commun. Inst. For. Fenn. 113, 75 p. (planted silver birch, southern Finland) | Record opened at Luke's repository | The only file is an 81.55 MB PDF sent as a download |
| Gustavsen & Mielikäinen 1984, Folia Forestalia 597, 20 p. Site index curves for natural birch stands in Finland | Record opened, same place. **New lead** | 49.4 MB PDF, a download |
| Siipilehto & Kangas 2015, Metsätieteen aikakauskirja 4/2015, article 6584 | Record and Finnish abstract opened (Luke, and the journal) | Full text is PDF only (0.7 MB), a download. It is about the height-on-diameter curve (Näslund), not diameter distributions. Data: the same Finnish inventory plots; the broadleaf set mixes birch stands, birch among conifers and a few other species |
| Niemistö 1995a, SJFR 10: 235 | Not tried again | Paywall on 2026-11-09. The approved 0.30-0.45 band still cites it unopened |
| Johansson 1996, Trees 10: 223 | Springer, abstract only | Paywall. Abstract: light under birch stands of 20-40 years, measured in 1991, correlated with basal area and stem number at r 0.54 and 0.57. No light values in the abstract. Not found in SLU's repository |

## 5. Height to the crown base by tree height

| Source | What it gives | Conditions |
|---|---|---|
| Hynynen et al. 2002, Eq. 65 and Table 38, pp. 59-60 (CONFIRMED) | Crown ratio = 1 − exp(−(a1 + a11 × PLANT) × ln(Hdom)^−a2 × d^a3 × ln(h)^−a4 × exp(−(a5 + a12 × PLANT) × RDF)). a1 2.02622, a2 0.62383, a3 0.54674, a4 1.67423, a5 0.32816, a11 1.71650, a12 0.64030. Predicted mean 0.5668, RMSE 0.100, 5,235 observations | Both birches; the data of section 1. Crown base = the lowest living branch with fewer than two dead whorls above it (p. 59). A later check against the national inventory found a mean bias of −0.018 for silver birch over 1,440 trees (Table 64, p. 104; read from the text layer only) |
| Fries 1964, Table A 7 (above) | Crown base of the mean tree 3.8 / 5.1 / 6.3 m at mean height 11.9 / 13.6 / 15.6 m; 9.2 / 10.0 m at 20.4 / 21.9 m. Crown ratio 0.62 / 0.60 at 13.6 / 15.6 m and 0.55 / 0.54 at 54 / 60 years | Thinned, 1,100/ha at 13.6-15.6 m, middle Sweden |

The Finnish equation worked for the cases in the plan (my arithmetic, SUSPECTED; RDF from the line in section 1):

| Case | Crown ratio | Crown base, m | The model |
|---|---|---|---|
| Planted, 1,600/ha, a leading tree at top height 13 / 14 / 15 m (DBH 11 / 12 / 13 cm) | 0.66 / 0.62 / 0.58 | 4.5 / 5.3 / 6.3 | stand trees 0.89 m |
| Self-sown, 5,078/ha, leading tree 13.3 m, DBH 10 cm | 0.47 | 7.0 | plots' dominants 2.56 m |
| Self-sown, 2,640/ha, leading tree 15.6 m, DBH 13 cm | 0.48 | 8.0 | plots' dominants 5.00 m |
| Self-sown plots at 45 / 50 / 60, mean tree | 0.48 / 0.48 / 0.49 | 9.9 / 10.3 / 11.1 | crown ratio 0.50 / 0.47 / 0.42 |

- **The guide's 5-7 m now has measured support** for planted or thinned stands: 4.5-6.3 m from the Finnish equation and 5.1-6.3 m from the Swedish table. The stand tree's 0.89 m is a real miss against both.
- **For unthinned self-sown stands the measured figure is higher, about 7-8 m at 13-16 m.** So the plots' leading trees (2.6-5.0 m) miss by more than the guide suggested, and a plot "pass" at 5-7 m would be wrong twice over.
- At 45-60 the model's crown ratio is near the equation (0.47 against 0.48 at 50) and under it at 60 (0.42 against 0.49), inside one RMSE.
- The DBH values I put in are guesses. The crown-base definitions differ a little from the model's lowest live branch. The equation is for both birches.

## 6. Branch bark share; branch litterfall

| Item | Source | Opened? | What it gives |
|---|---|---|---|
| Branch litterfall | Uri et al. 2012, Table 8, p. 122 (the reprint in the thesis copy) | **Yes** (CONFIRMED) | Branch litter 0.02, 0.13 and 0.78 t/ha a year at 14, 32 and 45 years; leaf litter 2.31, 3.01 and 2.01. Ten litter traps of 0.25-0.53 m² per stand. At 45 branches were 21 % of the litter carbon; under 1 % and 4 % in the young and middle-aged stands |
| Branch stock | Uri et al. 2012 (section 4b) | Yes | 15.7 t/ha at 45 (940/ha) and 18.6 at 60 (305/ha), bark included |
| Branch bark share | Kärkkäinen 1976, Silva Fennica 10(3), article 4948 | **Abstract only.** The PDF (14.8 MB) is sent as a download | 1,056 branch samples of birch, spruce and pine, cut every 20 cm along the branch, from small trees; bark share, wood and bark density, all changing with branch diameter. No numbers in the abstract |
| Branch bark share, other | none | No | UNVERIFIED as before |

- **At 45 the measured branch litter is 0.83 kg per tree a year,** 5.0 % of the branch stock (my arithmetic). The model sheds about 4.7 kg of branch wood per tree a year at 50-60 (branch-wood challenge), which is 3.1 / 2.2 t/ha at 50 / 60: three to four times the Estonian figure per hectare.
- Small traps miss large dead limbs, and dead birch limbs can stay on the tree, so the trap figure is a floor (SUSPECTED). It is still the first measured birch figure, and nothing has been tuned against it.
- The measured branch stock at 45, 15.7 t/ha, is nearer Repola's A3 for the plots (14.0-15.5) than Eq. 9 (16.9-21.9). That supports DECISIONS 110 (6a).

## 7. Sprugel, Hinckley & Schaap 1991

| Route | Result |
|---|---|
| Annual Reviews, Annu. Rev. Ecol. Syst. 22: 309-334 | **Blocked:** the page gives the title and asks for a login or purchase. No abstract. It stays UNVERIFIED, as the branch-wood challenge marked it |

## What the plan should change (proposals; nothing edited)

1. **Step E.** Birch's own rule is read. Add an arm with it (Eq. 33, self-sown exponent 1.544 × RDFL), labelled sourced for birch with its limits (both birches; mostly birch among conifers). It needs RDFL, so also the self-thinning line and the stump-diameter rule. Use the report's Ddom and dominants' step with it, or say what is swapped. The pine arm stays "borrowed". The plan's forecast for arm A (catch-up after 45) does not carry over to the birch arm; its own risk is top height sinking if Ddom is read at the 100 thickest.
2. **The plan's limits for E** (start at top height 10 m, ratio floor 0.4) came from the pine data. The birch data runs from dominant height 2.6 m and DBH 1.0 cm.
3. **Q40 and S1.** A measured source exists for the crown base: the Finnish equation and Fries's table. For planted or thinned stands it backs 5-7 m (4.5-6.3 m). For unthinned self-sown stands it gives about 7-8 m at 13-16 m. Whether the row is scored again is the maintainer's call.
4. **Hemery.** The cap is 5-8 % wider than the author's own printed table, which the species file's other line reproduces. The printed range starts at 10 cm. The label for small stems should say "outside the printed range". The DOI fix from 2026-11-09 still waits.
5. **C1.** A primary source for the rule's form is opened (Purves et al. 2007). Mitchell 1975 stays unopened.
6. **Independent tests at 50-60.** Candidates now opened: basal area and stems against the Finnish unthinned silver birch stands and their line; Uri's 45-year stand; Fries's table for the stand tree. None is entered as a target. Decision 7 holds yield tables back for a release test; the self-thinning line and Uri's stands need the same decision.
7. **Too few stems.** The model's plots are at 0.62-0.89 of the published line while measured unthinned stands are at 0.96-1.03. This belongs in the "not now" row for stems as its first published yardstick.
8. **Branch wood (step B).** Add the branch litter figure as a check row (reported, not tuned): 0.78 t/ha a year at 45. Bark share is still unopened.
9. **Dahlgren Lidman rows.** Correct three notes: the volumes agree, the ± is an SD, all trees were counted. Add the doubt about height at 42.

## Needs the maintainer

1. Three more downloads, each from the publisher's own site, if wanted: Oikarinen 1983 (81.55 MB, Luke), Kärkkäinen 1976 (14.8 MB, Silva Fennica), Siipilehto & Kangas 2015 (0.7 MB). Also the new lead, Gustavsen & Mielikäinen 1984 (49.4 MB, Luke).
2. Hemery 2005's Table 1, Niemistö 1995a, Johansson 1996 and Sprugel 1991 need a person: CAPTCHA or paywall.
3. Fries 1964 can be read further in the browser (other site classes; the 92 plots). About an hour of reading.

## What I checked, and what I didn't

- CONFIRMED on the page images: every Hynynen number in sections 1, 4c and 5 except Eq. 3 and Table 64, which I read from the text layer; Fries's Table A 7.
- CONFIRMED in the publisher's or author's page text: Hemery's table, Dahlgren Lidman, Purves, the abstracts, the repository records. Uri's tables in the thesis copy.
- SUSPECTED: all my arithmetic (the modifier table, RDF shares, crown bases, litter per tree), and the inputs I guessed for it.
- Not done: Hemery's Table 1, Mitchell 1975, Pretzsch 2002, a bark share, the dominant-height model's birch values in Hynynen 2002 (Table 14), Fries beyond one table.
