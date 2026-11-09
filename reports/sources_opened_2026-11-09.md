# Sources opened, 2026-11-09 (overnight sources job)

Done on the branch `worktree-agent-a08d8cd816f7a7ae9`, from master 28519b3, between 03:44 and about 04:30. The maintainer's Chrome was used through the Claude in Chrome extension, as agreed in Q36.

**How the sources were read:**
- Only at the publisher, at Crossref (for DOI metadata), at Luke's Jukuri, at the Estonian University of Life Sciences repository (record page only), and on the author's own website (Hemery).
- Pages were read in the browser as HTML. Nothing was downloaded and no form was filled.
- No third-party copies were used.

**Cookie banners:** I took the most private choice on each site: MDPI "Deny", Taylor & Francis "Reject All", Wiley "Reject Non-Essential". Where a site showed a CAPTCHA or bot check, I stopped and moved on: ScienceDirect (Cloudflare "Are you a robot?", hit twice, once for each DOI) and Oxford Academic ("Performing security verification").

**What I record from papers:** only numbers and table or page references, and at most one short quote per paper. MDPI and T&F HTML has no page numbers, so I cite sections, tables and figures instead.

**The browser afterwards:** the extension stopped responding after I closed my tab at the end (two tries, both "not connected"). By then the browser work was finished. The one thing it stopped was a re-check of Repola 2008's stand origin, so I use final check (a)'s reading for that.

**No runs:** no model runs, tests or renders. The only scripts were small arithmetic checks and the byte-level text edits.

---

## 1. The 14 blocked papers

The list is final check (a)'s finding 19, which names 15 papers. Counted as 14 with Jones 2021 and 2023 together, **10 opened and 4 blocked**. Counted separately, 11 opened.

| Paper | Route | Opened? | What it says, against what we claim | Proposed fix |
|---|---|---|---|---|
| **Hemery, Savill & Pryor 2005**, FEM 215:285-294 (top priority) | ScienceDirect via doi.org; Crossref API; the author's own site, gabrielhemery.com (2011 post "Estimating tree crown size") | **Blocked:** Cloudflare CAPTCHA at ScienceDirect, twice. No open copy at the publisher, and none found in an Oxford repository. | **The DOI in `targets.yaml` is wrong.** Crossref says 10.1016/j.foreco.2005.05.014 is López-Serrano et al., a paper on pines (pp. 251-270). Hemery's paper is 10.1016/j.foreco.2005.05.016.<br>**Table 1 is still unread.** The author's own graph, read by eye, plots crown:stem diameter ratio (z) against DBH, 0.10-0.70 m, for nine species including birch. Birch's z there is about 25.8 at 10 cm, 19.7 at 26 cm, 18.8 at 46 cm and 17.8 at 70 cm. Against the two lines in our files:<br>- **crown_frame's** 0.932 + 0.177 DBH(cm), from targets.yaml, gives 27.0, 21.3, 19.7 and 19.0. That is a crown 5-8 % wider than the graph at 10-70 cm.<br>- **reference.crown's** 0.96 + 16.2 d(m) gives 25.8, 19.9, 18.3 and 17.6. That is within about 3 % of the graph.<br>So the graph sits nearer the line the species file calls "a linear fit to [H05]'s table" than the line that caps open-grown crowns. A graph read by eye doesn't settle it. | (1) Correct the DOI to `10.1016/j.foreco.2005.05.016` in `targets.yaml` (crown_width_open_grown). This is a citation fix like DECISIONS 97; I haven't made it, because it's outside tonight's list.<br>(2) the maintainer opens Table 1 himself, or through a library, since ScienceDirect wants a CAPTCHA.<br>(3) Keep crown_frame.crown_a/b as VERIFY. If Table 1 confirms the second line, the open-grown cap is 5-8 % wide. |
| **Hagemeier & Leuschner 2019a**, Forests 10:265 | mdpi.com HTML | **Opened** | **Table 3:** birch stand 1 is 45 yr, 25.2 m²/ha, 880 /ha, 85 % birch, H 20 ± 3, dbh 19 ± 6. Stand 2 is 67 yr, 28.5, 420, 98 %, 25 ± 3, 25 ± 3. Its footnote calls the dbh an "arithmetic mean".<br>**Methods:** two circular 1000 m² plots per stand; canopy closure > 0.9.<br>**Section 3.2:** LAI 3.6 and 5.4, and the paper notes that admixed species are included in these figures.<br>**Table 4:** Betula LMA = 50.5 + 38.7 x^3.3, so 50.5 is the fit at relative height 0, below a birch crown.<br>**Leaf angle:** crown mean 49°.<br>**Leaf area density fit:** a 0.142, b 2.91, c 9.02.<br>**Leaf area:** all in the upper half of the stem.<br>All of this agrees with the repo. | Add "admixed species included" to `lai_hagemeier.measures` (wording, for the next tag). For the basal area, see Q32 below. |
| **Hagemeier & Leuschner 2019b**, Forests 10:925 | mdpi.com HTML | **Opened** | **Table 2:** the same stand figures as 10:265.<br>**Table 5:** LAI 4.6, LAD 3.2 (sun) and 0.3 (shade), K_PAR 0.37, Ω 0.42. The text gives Ω 0.41.<br>**Results 3.2 and Fig. 5:** median 14.8 %, single readings 6.4-19.8 %, 110-241 points, overcast, 11:00-14:00.<br>**Methods 2.3:** the sensor is on a 2 m pole, and its height above the ground is not stated.<br>**Minimum light:** shade leaves and saplings (50-90 cm) both 21.0 %, each a median of 120-150 readings. Methods define minimum light demand as the lowest reading, while Results give medians.<br>All agrees with the targets file and the labels. | None |
| **Zeltins et al. 2018**, Forests 9:52 | mdpi.com HTML | **Opened** | **Table 1:**<br>- Branch angle: 43.2, range 15.0-80.0, SD 10.4.<br>- Double tops: 34.9 % (6.0-75.1). The asterisk on this row means "Mean values for clones", so 34.9 is a mean of 22 clones' shares, not a share of all trees.<br>- Also: DBH 27.7, H 26.2, lowest live branch 11.2 m, mean crown projection 2.9 m.<br>**Stand:** 400 trees/ha, grafted plus-tree clones aged 40, an abandoned seed orchard with only an initial cleaning.<br>The paper defines neither the branch angle nor the crown projection, and has no angle for higher orders, so our 42 and 48 are unsourced. | In `crown_frame.fork_share_of_trees`' label and comment, say it's the mean over clones. Otherwise it agrees. |
| **Krišāns et al. 2022**, Forests 13:127 | mdpi.com HTML | **Opened** | **Table 1, birch sites 5 and 6:**<br>- DBH 25.5 and 35.0 cm; H 29.1 and 32.8 m; stem volume 0.67 and 1.43 m³; uprooted plate depth 0.85 and 0.84 m.<br>- The ± values are 95 % confidence intervals, not SDs.<br>- The trees were de-topped before pulling.<br>**Table 2:** moment at secondary failure 46.9 and 154.3 kN m, with no stem breaks, so all failed by uprooting.<br>**Table 3** is the paper's own linear mixed model, with an intercept, a volume slope and a species interaction.<br>**Our 101** is least squares through the origin over the two site means. I recomputed it: 101.1. It is not the paper's model, as the checker said.<br>**Rechecked:** form factor 0.451 and 0.453; reference rooting depth 0.85; h·DBH² coefficient 31, the mean of the site ratios 24.8 and 38.4. | **Done:** "an empirical regression" became "my line through two published averages" in `targets.yaml`, the species file and 4 labels (Q35). |
| **Liu & Evans 2021**, Forests 12:929 | mdpi.com HTML | **Opened** | **Abstract:** about 137,000 seeds from a tree of 20 cm DBH in 2015; mean distance 65 m in the open and 38 m in a closed stand.<br>**Table 1, best model:** b0 15.23, u0 4.18, ut −0.18, p0 −0.86, pt −0.04.<br>**Mapping:** trees over 15 cm DBH, counted in 10 m × 10 m cells.<br>**Eq. 2 in the publisher's HTML** has "+ p²/2" inside the square, so u is the mean distance, as the text says. The species file (line 1137) says Eq. 2 prints "− p²/2". The HTML disagrees; the PDF wasn't opened. | The VERIFY on the sign can close: the code's reading, u as the mean, matches the HTML. Correct the comment. Not done tonight, being outside the list. |
| **Fedorov et al. 2024**, Forests 15:34 | doi.org to mdpi.com HTML | **Opened** | **Table 1:** the far edge is 640, 391, 756 and 776 m from the seed source.<br>**Table 2, far from the source:** 740, 504, 256 and 720 stems/ha, at ages 20-21, 21-22, 19-22 and 20.<br>**Table 2, near the source:** 1568, 1548, 476 and 1068 stems/ha, at 21-24 years.<br>**Text (Fig. 4):** on plot 1 at 8-9 years, cover was about 24 % within 100 m and at most 5 % at 200-600 m.<br>**Against our wording:** we write "256-740 stems/ha at 21-24 years". The far-edge stands are 19-22 years old; 21-24 is the range near the source. The rest agrees. | In `regeneration.spread.far_share`' comment and label, write "19-22 years". This is wording only. |
| **Jones et al. 2021**, Forests 12:159 | doi.org to mdpi.com HTML | **Opened** | **Table 2,** Hyssna and Brunsberg:<br>- Bark height: n 1141 and 1390; mean 67 and 46 cm; minimum 0 and 10; maximum 280 and 240; phenotypic CV 65 and 74 %.<br>- DBH at 19: 110 and 98 mm; CV 25 and 28 %.<br>**Table 3** (phenotypic correlations, above the diagonal): r(DBH19, bark height) is 0.53 and 0.51.<br>All agrees. | None |
| **Jones et al. 2023**, Forests 14:2031 | doi.org to mdpi.com HTML | **Opened** | **Table 1, silver birch:** n 118, DBH15 110 mm (SD 33), fissured bark height 69 cm (SD 33). The text says 70 cm.<br>Our 70 cm and CV 48 % (33/69) agree.<br>This paper measures "fissured bark height", while 2021 measures the height where smooth bark dominates. Neither paper says the two are the same boundary. | A note only. |
| **Thomas & Martin 2012**, Forests 3:332 | doi.org to mdpi.com HTML | **Opened** | **Pages:** 332-352, confirming DECISIONS 97's fix.<br>**Table 2,** temperate/boreal angiosperms: 48.8 ± 0.6 % from 10 references and 54 species; the IPCC value reprinted is 48 ± 2.<br>The HTML has no page numbers, so p. 337 isn't checked. | None |
| **Donis et al. 2024**, Forests 15:275 | doi.org to mdpi.com HTML | **Opened** | **Damage:** 31.0 % of birch trees had stem damage, and 93.7 % of those were bent. Trees bent 15° or less counted as undamaged.<br>**Stands:** 99 stands, 215 ha, aged 2-29, in Latvia, after freezing rain and snow, with B. pendula and B. pubescens together.<br>**Against our wording:** "about 31 % of a young stand" is really 31 % of birches across 99 young stands of both birches. break_share 0.063 = 1 − 0.937 covers broken and uprooted trees together. | Wording in `damage.snow.crown_catch_fraction`' label: "31 % of birches over 99 young stands (both species)". |
| **Hansen et al. 2023**, SJFR 38:413, and its correction, SJFR 39:254 | tandfonline.com, open access | **Opened** | **Eq. 9, birch,** gives double bark B = −0.0483 + 0.0050 D + 0.0846 d, with B, D and d all in cm. The 2024 correction changed "B in mm" to "B in cm".<br>**Against taperNOR:** times 10, Eq. 9 gives −0.483 + 0.050 D + 0.846 d in mm, which is taperNOR's −0.4855, 0.04958, 0.8468, as in `tools/bark.py`, diameters in cm.<br>**Model form:** Hannrup 2004 (Eq. A31). Birch bark RMSE is 4.1 mm. | **Units settled.** `mortality.bark_double_mm` and `bark.thickness.hansen_double_mm` can cite Eq. 9 itself, not just taperNOR. The VERIFY "hansen_double_mm and its units" can close. Not done tonight. |
| **Eriksson, Johansson & Kiviste 1997**, SJFR 12:149 | tandfonline.com | **Blocked:** paywall, abstract page only | **Abstract:** 266 top-height trees of both birches on 155 temporary and 12 permanent plots across Sweden; a Hossfeld IV difference model of height over breast-height age.<br>The abstract has no reference age and no table. | It stays VERIFY. The paper needs the maintainer's library access. |
| **Niemistö 1995a and 1995b**, SJFR 10:235 and 10:245 | tandfonline.com | **Blocked:** paywall, abstract pages only | **Both are planted spacing trials:** four experiments, 400-5000 trees/ha, ages 11-22.<br>**1995a's abstract** has no crown ratio.<br>**1995b's abstract:** in the densest stands, 4000 live trees/ha at a dominant height of 15 m, height and volume growth begin to slow. Dominant trees' diameter growth slows above 1000/ha, and height growth is lower at 400/ha. That partly supports `dominant_height_invariance`.<br>`dense_unmanaged_stand` is labelled natural but rests on planted trials. Its own text already says it is unchecked. | It stays unchecked. The paper needs the maintainer's access. |
| **Hynynen et al. 2010**, Forestry 83:103 | academic.oup.com; Jukuri | **Blocked:** Cloudflare bot check at Oxford. Jukuri's record (c8ab9105…) has metadata only, with no file. | Unread. | It stays as INFO. The paper needs the maintainer's access. |

---

## 2. Hagemeier, Q32: what the papers print

**Verdict: we copied the figures correctly. The paper's own columns don't agree.**

- Both Forests 10:265 (Table 3) and 10:925 (Table 2) print stand 1 as 25.2 m²/ha, 880 /ha, dbh 19 ± 6. They print stand 2 as 28.5, 420, 25 ± 3.
- 10:265 footnotes the dbh as an arithmetic mean.
- From stems/ha and the arithmetic mean plus its SD, so the quadratic mean, the basal areas would be:
  - Stand 1: 27.4 m²/ha, against 25.2 printed.
  - Stand 2: 20.9 m²/ha, against 28.5 printed.

The mismatch isn't only birch's. Here is the same check on all ten stands in the table:

| Stand | Printed BA | From N and mean ± SD | Printed ÷ computed |
|---|---|---|---|
| Betula 1 | 25.2 | 27.4 | 0.92 |
| Betula 2 | 28.5 | 20.9 | 1.36 |
| Quercus 3 | 27.5 | 28.7 | 0.96 |
| Quercus 4 | 23.8 | 29.4 | 0.81 |
| Carpinus 5 | 31.5 | 22.8 | 1.38 |
| Carpinus 6 | 37.0 | 36.5 | 1.02 |
| Tilia 7 | 35.9 | 17.7 | 2.03 |
| Tilia 8 | 37.7 | 34.6 | 1.09 |
| Fagus 9 | 30.8 | 52.2 | 0.59 |
| Fagus 10 | 24.2 | 43.6 | 0.56 |

Eight of the ten are more than 5 % off, in both directions. Neither paper says how basal area was summed, for example all species, or another plot. So we can't tell which column is wrong.

**Proposed correction (not made; targets unchanged):**
- Keep 880 and 420 stems/ha and the other figures exactly as printed.
- Add to `stand_density.measures`: "the paper's basal areas don't square with its stems and mean dbh (8 of 10 stands off by more than 5 %, both ways), so basal area is not used as a check."
- In the species file's sdi_max note, the RDs for Hagemeier, 574 and 543 SDI "with their printed basal areas", inherit the same doubt. I've noted that in the comment.

The finding is also added to Q32 in QUESTIONS.md. Q32 stays open for the maintainer's choice.

---

## 3. Q30: where the Baltic LAI band 2.5-4.5 comes from

**Found:** Varik, M., Aosaar, J. & Uri, V. 2009. *Biomass production and carbon accumulation in silver birch stands in Oxalis site type.* Forestry Studies / Metsanduslikud Uurimused 51: 5-16. doi:10.2478/v10132-011-0073-y.

- **Where I read it:** the publisher (reference-global.com), which marks it open access. Its "read online" view shows the paper, which is in Estonian with an English abstract.
- **Date:** it's volume 51, dated 2009 and put online in March 2011. The knowledge base calls it "Varik 2011, paywalled". It's 2009, and it's open.
- **What the abstract says:** LAI "ranged 2.5-4.4 m2 m-2 in the studied stands".
- **Results:** LAI 3.2, 4.4 and 2.5 at ages 14, 32 and 45.
- **Table 1:** the three stands are natural silver birch on fertile forest land (Oxalis site type), in Alatskivi and Erastvere, southern Estonia, measured in 2008.

| Age | Stems/ha | Mean D (cm) | Mean H (m) | Basal area (m²/ha) | LAI |
|---|---|---|---|---|---|
| 14 | 1350 | 9.9 | 11.5 | 10.6 | 3.2 |
| 32 | 3208 | 10.8 | 17.0 | 29.2 | 4.4 |
| 45 | 941 | 20.1 | 25.6 | 29.8 | 2.5 |

**How LAI was measured:** the model trees' total leaf area, scaled to the stand through a leaf-area-on-DBH relation.

**Against the target:**
- **Top of the band:** 4.5 rounds the printed 4.4 up.
- **Ages:** the LAI exists only at 14, 32 and 45. The target runs from 6 to 60, an age range that comes from Uri 2012's chronosequence, which prints no LAI.
- **Site:** forest land, not abandoned farmland, as the old text said.
- **LAI by age:** LAI peaks at 32 and is lowest at 45. Nothing supports 2.5-4.5 at 50-60, which is where it's scored and tuned against.

**Done (Q30, wording only):** the band's `source`, `doi`, `citation`, `page_table`, `measures` and `conditions.text` now name Varik et al. 2009, and say the age and density labels are wider than the source. The band and the age, density and mode labels are unchanged.

**Proposed for the maintainer:** narrow the conditions to ages 14-45, and the top to 4.4. That tightens the target, so it's the maintainer's decision.

---

## 4. Fair tests: published *B. pendula* stand data not used for tuning

I checked each candidate against `labels.yaml`, the species file and `targets.yaml`.

**Already used, so not independent:**
- Aosaar 2016, Martinik 2018, Hagemeier 2019a/b, Kitenberga 2021, Maleki & Kiviste 2016, Hökkä 2012, Dahlgren Lidman 2023/24, Tiebel 2020, Lee 2025, Fedorov's far edge.
- Evo TLS: the crown width is tuned against it (species file lines 1652 and 1748), so it's no longer a check.

| Rank | Source | Access | What it gives, at which ages | Used already? |
|---|---|---|---|---|
| 1 | **Estonian Oxalis chronosequence:** Uri et al. 2012, FEM 267:117 (Table 1 stand data, Table 4 leaf mass), and Varik, Aosaar & Uri 2009 (Table 1) | Varik 2009 is open at the publisher. Uri 2012 is in Varik's 2014 thesis on dspace.emu.ee (an approved route); the only route is a 1.48 MB PDF, which I didn't open, because that's a download. | **Natural stands at 6, 13, 14, 18, 28, 32, 45 and 60:** stems/ha, mean D and H, basal area, and leaf mass of 1.7-3.4 t/ha (checker A's reading of Uri). **Varik:** N, D, H, basal area and above-ground biomass at 14, 32 and 45. | Only as the Baltic band's credit. The stand structure and leaf mass aren't used. Two of Uri's stands were thinned and one was storm-cut, so use the unthinned ones. |
| 2 | **Dahlgren Lidman, Holmström et al. 2021**, Silva Fennica 55, article 10485 | Open at silvafennica.fi (CC BY-SA); I read the abstract | **Two clearcuts that regenerated on their own** to birch-dominated stands, both birches with spruce coming in, in Sweden. An **unthinned control** was measured 42 years after the clearcut, beside three thinning strategies. It gives stem volume, density and species mix. | No. The repo uses this group's 2023/24 papers only for regeneration. |
| 3 | **Starikova et al. 2025**, Baltic Forestry 31(2), id 754 | Open at balticforestryojs.lammc.lt; I read the abstract | **Six natural silver birch plots** in Belavezhskaya Pushcha, Belarus, regrown after clearcuts in the early 1900s. They were remeasured 2-4 times from 1972 to 2023, so at ages from about 33-60 up to 84-111. It gives DBH, height and canopy position, and records succession to spruce or aspen. It's a check on natural stand dynamics through and beyond 60, and on old-age survival. | No |
| 4 | **Fedorov et al. 2024, near the seed source** (Table 2) | Open at mdpi.com; opened | **Natural colonisation of abandoned fields** in Bashkortostan: 1568, 1548, 476 and 1068 stems/ha, mean H 11.9-14.8 m, at 21-24 years. | Only the far-edge figures are tuned (far_share). The near ones are independent, but they come from the same paper and it isn't Nordic. |
| 5 | **Johansson 1996**, Trees 10:223-230, on canopy density and irradiance in 20-40-year-old birch stands | Springer: **paywalled** (subscription) | **Relative PAR under birch stands of both species in Sweden, aged 20-40,** against stem density and basal area. The abstract gives r 0.54-0.67. It is the only Nordic below-canopy light source found. | No. It needs the maintainer's access. |
| 6 | **Lapinjärvi TLS** (Luke, released 2019) | CC BY 4.0 data, per the knowledge base; not opened tonight | **18 plots in southern Finland:** height to the crown base per tree, DBH and height, with silver birch coded. It's a check on crown ratio and height to the live crown. | No |
| 7 | **Kalliovirta & Tokola 2005**, Silva Fennica 39(2) | Open (CC BY-SA); read before, in the knowledge base | **Finnish NFI birch, both species, n 2,282, managed:** crown diameter against DBH and height, mean 3.3 m. It's a stand-grown crown width check. | No |
| 8 | **Karlsson et al. 1998**, Silva Fennica 32(3) | Open | **Natural birch regeneration on abandoned farmland:** densities from the figures, about 5,000-87,000 /ha in young stands. A check on seedling and young-stand density. | No. Its birch is mostly B. pubescens. |
| 9 | **Tallo database** (Jucker et al. 2022) | CC BY 4.0 data | **B. pendula** crown radius, height and DBH. | Named in the species file as a check kept out of tuning. |
| 10 | **Finnish permanent sample plots 1985-95** (Luke) | CC BY 4.0 data, in Finnish | About 3,000 plots on a national grid, measured three times: survival and growth. | No. Mostly managed. |

**Top 5:**
1. The Estonian chronosequence (Uri 2012 and Varik 2009)
2. Dahlgren Lidman 2021's unthinned control at 42
3. Starikova 2025, 33 to 111 years
4. Fedorov's near-source stands
5. Johansson 1996 for light, which is paywalled

No open Nordic or Baltic source for light under birch was found tonight. Hagemeier 2019b is German, and already the target.

---

## 5. Openly licensed photos

**First, the current nine are already openly licensed.** I checked each on the Commons API tonight:

| Licence | Photos |
|---|---|
| CC BY-SA 4.0 | Oslo (Ryan Hodnett); Hallinden, Tuntorp and first snow (W.carter) |
| CC BY-SA 3.0 | Meilen (Maplan) |
| Public domain | Gullmarsskogen 1, 5 and 6 (W.carter); Russia (Игоревич) |

`reference/CREDITS.md` already credits them. So a public copy can keep them with that file, and the 1280 px downscales of the CC BY-SA photos stay CC BY-SA. Whether to keep or replace them is the maintainer's call (DECISIONS 100).

**The shortlist,** 14 photos, all from Wikimedia Commons:
- **How they were chosen:** licence, size and description from the Commons API. Each was looked at as a thumbnail, and none was downloaded.
- **Species:** each follows the uploader's description or its *Betula pendula* category. Each was checked only by eye at thumbnail size.
- **Preference:** CC0 and public-domain photos come first, since they need no share-alike.

| Kind | File (commons.wikimedia.org/wiki/File:…) | Author | Licence | Size (px) | What it shows |
|---|---|---|---|---|---|
| Stand interior | Birch_grove_at_Myrstrigen.jpg | W.carter | **CC0** | 4925×3283 | Leafless *B. pendula* grove, Brastad, Lysekil, Sweden, April 2020 |
| Stand interior | Birch_forest_Gullmarsskogen_3.jpg | W.carter | **Public domain** | 5203×3648 | Leafless stand interior with wood anemones, Lysekil, April 2017 (same stand as the current 1, 5 and 6) |
| Stand interior | Birch_forest_Gullmarsskogen_9.jpg | W.carter | **Public domain** | 3535×5303 | Same stand, portrait, April 2017 |
| Stand interior | Birch_trees_in_Finland.JPG | SeppVei | **CC0** | 3648×2736 | Dense, even stand of white stems in leaf, Finland, July 2011 |
| Stand interior | Birchwood_Slavnoe_2012_G1.jpg | George Chernilevsky | **Public domain** | 5184×3456 | Leafless silver birch wood on snow, Ukraine, March 2012 (not Nordic) |
| Nordic forest | Forest_by_Sognsvann_-_Oslo,_Norway_2020-08-04_(02).jpg | Ryan Hodnett | CC BY-SA 4.0 | 5201×3467 | Birch-rich forest edge in leaf, Oslo, August 2020 |
| Solitary | Lonely_tree_of_birch.jpg | Øyvind Holmstad | CC BY-SA 4.0 | 4000×6000 | Leafless lone birch in snow against the sky, Norway, February 2021 (for Meilen) |
| Solitary | B._pendula,_Koivu_Birch_end_of_Sept.jpg | Abc10 | CC BY-SA 4.0 | 2200×3301 | Lone weeping birch in a barley field, in mist, Uusimaa, Finland, September 2017 |
| Solitary | Lonely_birch_(14616433241).jpg | YuJeen from Riga | CC BY 2.0 | 5184×3888 | Young lone birch in leaf in a field near Riga Airport, Latvia, July 2014 |
| Solitary | 20120924Betula_pendula1.jpg | AnRo0002 | **CC0** | 1875×2500 | Lone windswept birch in leaf, Germany, September 2012 (not Nordic) |
| First snow | Birch_trunks_in_snow_and_sunshine.jpg | W.carter | CC BY-SA 4.0 | 3186×3186 | Silver birch trunks the day after the first snow, Brastad, November 2016 (for brastad_sweden_first_snow) |
| First snow | Snow_on_birch_at_Sågvägen,_Brastad_2.jpg | W.carter | CC BY-SA 4.0 | 3500×4674 | Lone birch under new snow, Brastad, January 2023 |
| Winter, solitary | Vinterbjörk.jpg | Floozy Jesters | CC BY-SA 3.0 | 2336×3504 | Frosted lone birch in a town, Umeå, Sweden, February 2011 |
| Nordic forest, winter | Snowy_forest_next_to_Sågvägen_in_Tuntorp.jpg | W.carter | CC BY-SA 4.0 | 4973×3315 | Snowy birch forest edge, Tuntorp, Brastad (for tuntorp_sweden) |

---

## 6. Wording fixes the maintainer approved (Q35, Q33, Q31, Q30)

No number, band or species value changed. I checked by parsing:
- `species/betula_pendula.yaml` loads identical to HEAD.
- `labels.yaml` changed 5 notes, with no status or value changed.
- `targets.yaml` differs from the tag only in text fields and the two `mode` labels below.

The CRLF files were edited by bytes, splitting and joining on `\r\n`, and are still CRLF.

| Approved | File | Change |
|---|---|---|
| **Q35, Repola "natural too"** | `reference/targets.yaml` | `live_crown_ratio.managed_stand_empirical` and `foliage_biomass`:<br>- `mode: [managed]` becomes `[natural, managed]`.<br>- `measures` and `text` now say most stands were naturally regenerated and mixed with B. pubescens. This rests on final check (a)'s reading of Repola; I couldn't recheck it tonight.<br>- The key name stays, because `tools/tree_table.py` reads it.<br>- Both targets are `scoring: info`, so no PASS or FAIL can move. |
| **Q35, the wind line** | `reference/targets.yaml`, `species/betula_pendula.yaml`, `labels.yaml` | `critical_turning_moment.measures`, the anchorage comment and four anchorage label notes now say "my line through two published averages, not a published regression". The targets file also says what the line is fitted to (Tables 1-2) and that the paper's own model (Table 3) isn't it. |
| **Q33, sdi_max 763** | `species/betula_pendula.yaml`, `labels.yaml` | The notes now say:<br>- 763 is Aosaar 2016's naturally afforested stand.<br>- It isn't the highest seen: Martinik's age-18 row gives 766.<br>- Lee 2025 is from planted forests. Its full text is open in Jukuri, so "full text not opened" is gone.<br>- the maintainer kept 763.<br>- Hagemeier's basal areas are in doubt (Q32). |
| **Q31, seedling root:shoot** | `reference/targets.yaml` | A comment, and in `measures`: the band is worked out from Konopka et al. 2023's equations, not printed. |
| **Q30, Baltic band** | `reference/targets.yaml` | The description now names its real source (section 3), and the old "abandoned farmland" wording is corrected. |

**What the tag means for these edits:**
- Scoring reads `reference/targets.yaml` at the tag `targets-approved` (bb3048c), through `reference/betula_pendula/accuracy.yaml`.
- So every edit above is in the working copy only. No verdict changes, and no scorecard or report text changes.
- `test_birchs_targets_are_read_through_the_approved_tag`, which asserts the read comes from the tag, is unaffected.
- The edits, including the two widened `mode` labels, take effect only if the maintainer moves the tag. Until then, reports keep quoting the old wording, as with DECISIONS 97.
- I didn't move or create any tag.

---

## Needs the maintainer

1. **Hemery 2005 Table 1.** ScienceDirect wants a CAPTCHA, so please open it yourself. Also:
   - The DOI fix, to 10.1016/j.foreco.2005.05.016, waits for your OK.
   - The author's own graph points to crown_frame's cap being 5-8 % wide.
2. **Q32:** keep Hagemeier's figures as printed, with the note proposed in section 2?
3. **Q30 follow-up:** narrow the Baltic band to ages 14-45 and a top of 4.4, as its source prints? That tightens the target.
4. **Move `targets-approved`** to carry tonight's wording? That's your call; nothing scores differently until you do.
5. **Paywalled, needing your access:** Eriksson 1997, Niemistö 1995a/b, Hynynen 2010 (blocked by Oxford's bot check) and Johansson 1996 (light).
6. **Out-of-scope fixes, proposed but not made:**
   - Laitakari's year: printed 1934, the target says 1935.
   - Liu & Evans' Eq. 2 sign comment: the HTML prints "+".
   - Fedorov's far-edge ages: 19-22, not 21-24.
   - Zeltins' double tops: a mean over clones.
   - Donis' "a young stand": really 99 stands of both birches.
   - Hansen's Eq. 9: cite it, and close the units VERIFY.
   - Hagemeier's LAI includes admixed species.
7. **Photos:** the current nine are already CC BY-SA or public domain. Keep them, credited, or swap in the shortlist?
