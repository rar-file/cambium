# Silver birch knowledge base

Version 2, 4 Nov 2026 (v1 was 3 Nov), compiled by Claude (chat), for the Cambium birch growth project. v2 adds full-text readings of seven papers (section 05, plus `reports/extracts/`) and corrects three v1 entries.

**What this is.** One place for the papers, data and equations the project needs, with each source checked on a publisher or index page and labelled with how far it was read. It's a lead list for agents, not a citation list: **PROTOCOL.md section 3 still applies** (open each source before citing it; targets only through the maintainer's approval).

**Not to be used:** the "birch research lab" folder (birch.zip, 3 Nov). It was largely fabricated.

**Sections**
1. 01: Crown, shoots, branches and allocation
2. 02: Stand dynamics, density, self-thinning and mortality
3. 03: Environment: water, fertility, temperature and phenology
4. 04: Open datasets and existing models
5. 05: Full-text findings (v2)

---

## New in v2 (read first)

- **Alpha = 4.8 has no traceable source.** Aosaar 2016 has no photosynthesis, light or LAI data and no 4.8. Round 41 task 1b traces it. (05-A)
- **The height target may be offset.** Elfving's birch curve is height above breast height against breast-height age, and the time to breast height is 150 / SI years (about 5.8 at SI 26, not 4). Round 41 task 1c checks it. (05-E)
- **Measured branch length for stand birch:** first-order branches about 1.0 m long, 5.2 per 10% of crown length, in 73 trees aged 4–32 and 2–17 m tall (Lintunen 2013, Table 3). (05-B)
- **A published NPP split** (Aosaar, age 10): leaves 22%, stemwood 50%, bark 4%, twigs and branches 7%, stump and coarse roots 11%, fine roots 7%. (05-C)
- **Too much basal area in the plot:** real Finnish birch stands have 2.7–32.3 m²/ha; the model plot has 52–62. (05-D)
- **Mortality and old-age functions** are available: birch 5-year mortality by DBH, deciduous mortality, and maximum age (about 300 years). (05-F)
- **Corrections:**
  - Varik 2011 is paywalled.
  - Klepacki 2017 is free to read but all rights reserved.
  - Aosaar is not an alpha source.

## Top findings from v1

1. **The trunk takes too much.** Ilomäki et al. 2003 report a stem share of above-ground biomass of 80–96% in 30-year-old stand birch, rising with slenderness. The model is at about 97–98% at age 30. (01-B1)
2. **Bud numbers need crown-density control.** In LIGNUM fitted to scanned trees, "control of growth by local density in the crown was important", best done by varying lateral bud number with local density (Sievänen et al. 2018). This bears directly on the every-other-year shoot pattern. (01-A6)
3. **Use Repola's equations correctly.**
   - Eqs. 9 and 10 use dS (checked against his own Table 8).
   - The foliage equations are valid only for DBH 11–26 cm, on 21 trees.
   - Branch weights include bark.

   The earlier stem and branch ratios check out. (01-C1; round41_research_pack.md)
4. ~~Alpha comes from an unusually fertile young stand~~ **Corrected in v2:** alpha can't be traced to Aosaar 2016 (see 05-A). Aosaar does still give a fertile young stand's natural self-thinning (about 11,600 falling to 2,700 stems/ha, ages 8–17). (01-C3, 02-A3)
5. **A real self-thinning line for birch exists:** Hynynen 1993 (41 unthinned Finnish plots; slope varies by species, intercept by site index). (02-A2)
6. **An open crown-width source exists:** the Evo 2024 TLS dataset has about 1,000 birches with crown diameter, height and stem diameter (CC BY 4.0). (04-D1)
7. **Productivity ladder by site index:** MAI 6.0, 7.9, 10.5 and 12.8 m³/ha/yr at site index 22, 25, 28 and 32 (Liziniewicz 2022, planted improved birch). (03-B2)
8. **Drought thresholds for birch:** leaf hydraulic conductance halves at about −1.2 MPa; stomata and water-use efficiency drop below about −1.0 MPa branch water potential (Sellin 2014). (03-A2)
9. **Stand biomass checks:** 39.9, 140.3 and 224.3 t/ha above-ground at 14, 32 and 45 years; LAI 2.5–4.4 (Varik 2011, Estonia). (02-A4)
10. **Oleksyn 2000 won't source the juvenile leaf-size rule.** It's about seasonal leaf development. (01-A7)

---

## Source register

"Read" shows how far each source was checked: Full = full text, Abs = abstract or index record, Title = title or listing only.

| Source | Topic | Read | Access / licence | Section |
|---|---|---|---|---|
| Repola 2008, Silva Fennica 42(4): 605 | Biomass equations | Full | Open | 01-C1 |
| Ilomäki, Nikinmaa & Mäkelä 2003, CJFR 33: 2395 | Allocation, branch length, pipe model | Abs | Paywalled | 01-B1 |
| Sievänen et al. 2018, Ann. Bot. 122: 423 | LIGNUM, bud density control (pine) | Abs | Check | 01-A6 |
| Lintunen & Kaitaniemi 2010, Trees 24: 411 | Stand birch shoots | Abs | Paywalled | 01-A2 |
| Kaitaniemi & Lintunen 2010, Ann. For. Sci. 67: 604 | Competition effects | Abs | Free | 01-A3 |
| Kull, Tulva & Vapaavuori 2003, Ann. Bot. 91: 559 | Sylleptic and long shoots | Abs plus parts | Open (PMC) | 01-A4 |
| Kaitaniemi, Lintunen & Sievänen 2020, Ecol. Model. 416 | Branch growth power laws | Abs | Paywalled | 01-A5 |
| Maillette 1982 I and II, J. Appl. Ecol. 19 | Bud fates (3 open-grown trees) | Abs | Paywalled | 01-A1 |
| Oleksyn et al. 2000, Trees 14: 271 | Leaf development | Abs | Paywalled | 01-A7 |
| Mäkinen, Ojansuu & Niemistö 2003, For. Sci. 49: 301 | Branch characteristics | Abs | Paywalled | 01-B2 |
| Mäkinen 2002, Trees | Stand density and branches | Title | Paywalled | 01-B3 |
| Lintunen et al. 2011, CJFR 41: 1779 | 3D birch crown models (LIGNUM group) | Title | Paywalled | 01-B5 |
| Lintunen 2013, Diss. For. 165 | Crown architecture thesis | Full (summary only; articles not included) | Open (CC BY-NC-ND) | 01-B6 |
| Kalliovirta & Tokola 2005, Silva Fennica 39(2) | DBH from crown width | Full | Open (CC BY-SA) | 01-B7 |
| Klepacki 2017, For. Res. Pap. 78: 171 | 4-year-old birch size | Full (tables) | Free to read, all rights reserved | 01-B8 |
| Aosaar et al. 2016, Silva Fennica 50(4): 1628 | Young-stand density, NPP split (not an alpha source) | Full | Open (CC BY-SA) | 01-C3 |
| Varik, Aosaar & Uri 2011, Forestry Studies 51: 5 | Stand biomass, LAI | Abs | Paywalled | 02-A4 |
| Sellin et al. 2012, Trees 26: 821 | Shoot hydraulics | Abs | Paywalled | 01-D1 |
| Hagemeier & Leuschner 2019a and b, Forests | LAI, light, density | (in project) | Open | 02-A1 |
| Hynynen 1993, SJFR 8: 326 | Self-thinning line | Abs | Paywalled | 02-A2 |
| Niemistö 1995, SJFR 10: 235 and 245 | Crown ratio, spacing | (in project) | Paywalled | 02-A5 |
| Karlsson et al. 1998, Silva Fennica 32(3) | Natural regeneration (mostly downy) | Full | Open | 02-A6 |
| Dahlgren Lidman 2022, SLU thesis | Natural regeneration, Sweden | Abs | Open PDF | 02-A7 |
| Elfving 2010, Heureka report | Height curves, top height, mortality, maximum age | Full | Open | 02-B2 |
| Dubois, Verkasalo & Claessens 2020, Forests 11: 336 | Birch review | Abs | Open (CC BY) | 02-B4 |
| Hynynen & Niemistö 2009, waldwissen | Managed practice | Full | Open | 02-C1 |
| Starikova et al. 2025, Baltic For. 31(2) | Old birch dynamics | Abs | Check | 02-D1 |
| Sellin et al. 2014, BMC Plant Biol. 14: 72 | Drought thresholds | Full (key figures) | Open (CC BY) | 03-A2 |
| Liziniewicz et al. 2022, Silva Fennica 56(1) | Productivity by site index | Full | Open (CC BY-SA) | 03-B2 |
| Junttila & Hänninen 2012, Tree Phys. 32: 337 | Budburst temperature | Abs | Paywalled | 03-C1 |
| Linkosalo et al. 2010, Agric. For. Met. 150: 1579 | Flowering model | Abs | Paywalled | 03-C3 |
| Evo TLS 2024 (Yrttimaa et al. 2025) | Crown diameter data, 989 birch | Full | Data CC BY 4.0 | 04-D1 |
| Lapinjärvi TLS (Luke) | Crown base, point clouds | Full (data description) | CC BY 4.0 | 04-D2 |
| Finnish permanent sample plots 1985–95 (Luke) | Survival and growth | Abs | CC BY 4.0 | 04-D3 |
| Wytham Woods TLS and QSMs (Calders et al.) | QSMs | Abs | CC BY 4.0 | 04-D4 |
| Norunda Drought-2018 product (ICOS) | 2018 drought | Abs | CC BY 4.0 | 03-A3 |

---

## Papers worth requesting (paywalled; ResearchGate or email the authors)

Highest value first:
1. Ilomäki, Nikinmaa & Mäkelä 2003
2. Hynynen 1993
3. Lintunen et al. 2011
4. Sievänen et al. 2018 (may be open via OUP)
5. Mäkinen, Ojansuu & Niemistö 2003
6. Lintunen & Kaitaniemi 2010
7. Maillette 1982 I and II
8. Eriksson et al. 1997
9. Söderberg 1992 (SLU report)
10. Junttila & Hänninen 2012

## Not yet covered (next version)

- Bark appearance and thickness growth from ring history.
- Leaf colour and optical properties (open spectral libraries).
- Windthrow (birch-specific critical wind speeds).
- Root architecture and seedling root:shoot (Konôpka et al. 2023 is in the project).
- Norway spruce, for after birch.


---
---

# 05: Full-text findings (added in v2, 4 Nov 2026)

On 4 Nov a separate Claude session read seven papers in full and wrote `reports/extracts/paper_extracts.md`, `key_values.csv` (659 rows, each with page, table and QUOTED or COMPUTED) and `addendum_1b_1c_5.md`.

**Spot-checks done in this chat:**
- Aosaar 2016 Table 3 and Table 4 against the publisher PDF: plot 0.03 ha; N 11,633 → 2,733; G 11.3 → 20.9; branches 3.0 → 7.3; stemwood 20.4 → 76.3; leaf production 2.81; tree NPP 13.02. **All exact.**
- Liziniewicz BA1 coefficients and the MAI ladder match my earlier reading.
- The Elfving top-height wording matches the earlier Claude Code reading.
- Elfving's "height above breast height" sentence and T13 = 150/SIS were **not** re-checked here (the PDF was too long to fetch). Round 41 task 1c checks them.

Use the extract files for exact values and page numbers. The points that matter most are below.

---

## A. The model's photosynthesis setting (alpha = 4.8) has no traceable source
- Aosaar et al. 2016 contains **no photosynthesis, light, LAI or GPP data**, and no 4.8. The nearest derivable ratio is tree NPP ÷ foliage mass = 13.02 / 2.81 = **4.63 per year** (age 10).
- **Action:** round 41 task 1b traces where 4.8 came from in the project history, and marks it VERIFY.

## B. Measured branch numbers for stand-grown silver birch
Source: Lintunen 2013, Table 3 (p. 23), from Lintunen & Kaitaniemi 2010. Design B: **73 *B. pendula*** in 12 planted or experimental mixed stands at 60–63°N, medium-fertility (MT) sites, ages 4–32, heights 2–17 m. Values are means (95% CI), for birch next to birch:

| Trait | Value |
|---|---|
| Height growth | 49.1 (7.9) cm/yr |
| Growth vigour (long-shoot length ÷ branch length) | 0.19 (0.09) |
| First-order branches per 10% of crown length | 5.2 (0.3) |
| First-order branch length | **102 (7) cm** |
| Short shoots per branch | 53 (5.5) |

- Under heavier competition, birch had fewer, shorter, thinner main branches, longer shootless sections and fewer short shoots, but more current long shoots (p. 23).
- **For the model:** a measured branch-length and branch-number check for young stand birch. Note: these trees are 2–17 m tall. The model's limbs reach only 1.3–1.8 m on a 26-m tree, which is about what a 10-m tree has in Lintunen's simulations (Fig. 5: chord length 1.54 m at the crown base). That suggests the model's limbs are too short for the tree's size. Treat this as a lead, not a target, until compared like for like.
- Figures 5, 6 and 8 are **LIGNUM model outputs**, not measurements. Don't use them as targets.

## C. A published NPP partition for silver birch (asked for since phase 33)
Source: Aosaar 2016, Table 4 (p. 8). One fertile, unmanaged stand, **10 years old**; tree NPP 13.02 Mg/ha/yr.

| Component | Share of tree NPP (COMPUTED from the table) |
|---|---|
| Leaves | 21.6% |
| Stemwood | 49.5% |
| Stembark | 4.3% |
| Twigs | 5.5% |
| Branches | 1.2% |
| Stump | 4.7% |
| Coarse roots | 6.3% (partly assumed: 21% of above-ground woody production) |
| Fine roots | 6.8% |

- **For the model:** compare the seed-1 tree's yearly carbon split at age 10 with this, like for like (a young, very fertile stand).

## D. Stand-level checks
- **Basal area:**
  - Repola 2008, Table 1: 24 Finnish birch stands aged 11–97 (some thinned, some mixed with conifers), G = 2.7–32.3 m²/ha, mean 19.2.
  - Aosaar 2016: G levels off at about 20–21 m²/ha from age 13 to 17, while N falls from 7,670 to 2,733.
  - Model natural plot p38_nat: **52–62 m²/ha at 45–60**, far above both.
- **Self-thinning:** Söderberg 1986's maximum basal area (Elfving 2010, about p. 63) is weak for birch: birch enters only through a broadleaf-share term with a 184.8% standard error, and it under-predicts young birch. Use it as INFO only.
- **Evo TLS (Yrttimaa 2025):** plot N 166–2,080/ha and G 4.9–50.9 m²/ha (mean 30.2), in mixed managed stands. Note: its "Birch_BA%" column means **all deciduous trees**.

## E. Height curve and time to breast height
Source: Elfving 2010, as reported by the extract; to be confirmed in round 41 task 1c.
- The birch curve (asi = 7, β = 394, b2 = −1.3870) gives **height above breast height against breast-height age**. It was fitted to 266 top-height trees, **43% *B. pendula*, 57% *B. pubescens***.
- The time to breast height for birch is **T13 = 150 / SIS years**, which is about 5.8 years at SI 26 (the project uses 4).
- **For the scorecard:** check that 1.3 m is added to the curve heights, and that the age shift is consistent with Elfving's rule.

## F. Mortality and old age (for open issue 4)
All from Elfving 2010.
- **Fridman & Ståhl 2001, birch 5-year mortality** (digitised from a graph, p. 65): 0.33, 0.21, 0.14, 0.09, 0.06 and 0.04 at DBH 5, 10, 15, 20, 25 and 30 cm. Conditions: latitude 60, 300 m altitude, a pine stand with G 20 and Dg 20. Values below 10 cm are extrapolated.
- **Bengtsson 1978, deciduous mortality** (p. 64), % of volume per year. Valid for D 7–30 cm and A 30–120 years; reduce the output by 40% (north) or 25% (south).
- **Maximum age** (p. 67): ln AMAX = 4.6246 − 0.02192·SIS + 0.1742·ln n. That gives about 300 years at SIS 24. Ageing mortality is p = 1 / (1 + exp(10 − 12·A/AMAX)). Birch data: n = 4,040, oldest observed 240 years.
- **Ingrowth:** Wikberg 2004 (pp. 60–62), mostly graphs only.

## G. Corrections from the full texts
- **Yrttimaa 2025:** leaf-off. Stem diameter was measured at a 1.5–2.5 m slice, not 1.3 m. No crown-diameter or height accuracy is reported. The crown-diameter definition (maximum width or equivalent circle) isn't stated.
- **Kalliovirta & Tokola 2005:** no crown-width equation; crown width is only a predictor. Birch n = 2,282; maximum crown diameter mean 3.3 m (range 0.7–10.4 m); DBH 0.6–53.2 cm; height 1.6–31 m. Crown width is "the widest dimension of the crown". Its data ranges can still bound a crown-width check.
- **Liziniewicz 2022:** valid only for initial stocking of 1,800–2,200 trees/ha. There is no mortality function and no height-by-age table.
- **Karlsson 1998:** mostly downy birch; densities come only from figures (about 5,000–87,000 stems/ha in young stands).
- **Harvester sidecars:** the authors are wrong in four JSON files (Yrttimaa, Karlsson, Aosaar, Liziniewicz). Trust the PDFs, not the sidecars.


---
---

# 01: Crown, shoots, branches and allocation

Part of the birch knowledge base (see 00_index.md). Compiled 3 Nov 2026 by Claude (chat).

**Read level:** "full text" means the paper itself was read; "abstract" means only the abstract or index record was read. Agents must open each source themselves before citing it (PROTOCOL.md section 3).

---

## A. Shoot and bud dynamics

### A1. Maillette 1982: Structural dynamics of silver birch, I and II
- **Citation:** *Journal of Applied Ecology* 19.
- **DOIs:** part II 10.2307/2403006; part I probably 10.2307/2403005 (confirm).
- **Access:** paywalled (JSTOR). **Read level:** abstract.
- **Says:** three **mature, open-grown** trees, 4–10 m tall, North Wales. Bud fates are related to leaf dynamics, heterophylly, flowering and shoot elongation. The leading bud "appears particularly important in determining growth and form". Part II is a matrix model of the bud population for the same three trees.
- **For the model:** the classic source for long/short shoot transition rates. But it's open-grown, with n = 3: compare against an open-grown run, not the stand tree.

### A2. Lintunen & Kaitaniemi 2010: competition and crown architecture
- **Citation:** *Trees* 24: 411–424. doi:10.1007/s00468-010-0409-x
- **Access:** paywalled. **Read level:** abstract.
- **Says:**
  - Stand-grown birch, 3D-digitised, with neighbours within 5 m.
  - Long-shoot "growth vigour" (new long-shoot length relative to existing branch length) was highest next to other birches.
  - Next to birch or pine, birch invested more in short shoots, placed densely on short branches.
  - Responses depended on ontogeny and on position in the crown.
- **For the model:** the best lead on stand-grown long/short shoot behaviour.

### A3. Kaitaniemi & Lintunen 2010: neighbour identity and competition
- **Citation:** *Annals of Forest Science* 67: 604. doi:10.1051/forest/2010017
- **Access:** free. **Read level:** abstract.
- **Says:**
  - Finnish stands, trees 4–35 years old, at 60–63°N, stand basal area about 10–25 m²/ha.
  - In birch, competition (CI1) shortened 1-year shoots (slope −0.04 ± 0.02) and reduced ring width.
  - Branch number per crown length showed no significant effect.
  - For birch, competition mattered more than neighbour species.

### A4. Kull, Tulva & Vapaavuori 2003: CO2 and O3 effects on silver birch crown structure
- **Citation:** *Annals of Botany* 91: 559–569. doi:10.1093/aob/mcg052
- **Access:** open (PMC4242242). **Read level:** abstract plus parts of the full text.
- **Says:**
  - Two clones in chambers, with long-shoot proportion analysed as a variable.
  - Sylleptic shoots (side shoots that grow in the same season as their parent): 28% in clone 4 and 20% in clone 80.
  - "Short shoots … were never sylleptic."
- **For the model:** a check on whether the model lets short shoots grow sylleptically. Young, chamber-grown trees, so use with care.

### A5. Kaitaniemi, Lintunen & Sievänen 2020: power-law estimation of branch growth
- **Citation:** *Ecological Modelling* 416: 108900. doi:10.1016/j.ecolmodel.2019.108900
- **Access:** paywalled. **Read level:** abstract.
- **Says:**
  - Silver birch, wide size and geographic range. Models of annual shoot length and total elongating length per branch, run dynamically, reproduced the crown profile and final basal branch size within field ranges.
  - Growth rate falls from the apex to the lowest branches.
  - Branching order affects elongation.
  - Thicker branches are more vigorous, at a given height.
- **For the model:** an empirical target for how long-shoot growth should decline down the crown.

### A6. Sievänen et al. 2018: LIGNUM and segmented TLS
- **Citation:** Sievänen, Raumonen, Perttunen, Nikinmaa & Kaitaniemi, *Annals of Botany* 122: 423–434. doi:10.1093/aob/mcy082
- **Access:** check (OUP). **Read level:** abstract.
- **Says:**
  - Scots pine, not birch: four trees scanned from sapling to maturity, LIGNUM parameters fitted by genetic algorithm.
  - The extended Borchert–Honda model performed best.
  - "Control of growth by local density in the crown was important for all shoot elongation formulations."
  - The best implementation **varied the number of lateral buds with local crown density**.
- **For the model:** directly relevant to round 41's hypothesis, where swings in bud number drive the every-other-year pattern. The published LIGNUM fix is density-dependent bud production.

### A7. Oleksyn et al. 2000: leaf CO2 exchange through the season
- **Citation:** *Trees* 14: 271–281. doi:10.1007/PL00009768
- **Access:** paywalled. **Read level:** abstract.
- **Says:** expanding leaves can keep a positive carbon balance before they're fully developed. It does **not** give leaf size against plant height or age.
- **For the model:** supports new-shoot leaves earning carbon in their first season. It can't source the juvenile leaf-size rule.

---

## B. Branches, crown size and crown width

### B1. Ilomäki, Nikinmaa & Mäkelä 2003: crown rise drives biomass allocation in silver birch
- **Citation:** *Can. J. For. Res.* 33: 2395–2404. doi:10.1139/x03-164
- **Access:** paywalled. **Read level:** abstract.
- **Says:**
  - 30-year-old planted monocultures at three spacings.
  - Total branch cross-sectional area was linear in stem cross-sectional area at the crown base.
  - Foliage mass correlated with stem basal area at the crown base.
  - Basal-area-weighted **mean branch length was linear in crown length**.
  - The stem's share of above-ground biomass rose from **80% to 96%** with slenderness.
  - The results support functional balance and conflict with the "priority principle" of allocation.
- **For the model:** a pipe-model check for stage b, a branch-reach target, and a stem-share check. The model's stem share at age 30 is about 97–98%.

### B2. Mäkinen, Ojansuu & Niemistö 2003: predicting external branch characteristics of planted silver birch
- **Citation:** *Forest Science* 49(2): 301–317.
- **Access:** paywalled. **Read level:** abstract.
- **Says:** models for crown ratio, self-pruning ratio (lowest dead branch height ÷ crown base height), number of living branches, total branches, thickest branch diameter, smaller-branch diameters, and **branch angle**, from routine stand and tree measurements. The models also worked on downy birch without major bias.
- **For the model:** sourced targets for branch number, thickest branch and branch angle. Get the full text.

### B3. Mäkinen 2002: effect of stand density on branch development of silver birch, central Finland
- **Citation:** *Trees* (volume and pages to confirm). Record at jukuri.luke.fi.
- **Access:** paywalled. **Read level:** title only (the repository blocked automated access).
- **For the model:** density effects on branch size. Confirm the citation first.

### B4. Niemistö 1995: crown and branch properties of silver birch
- **Citation:** *Scand. J. For. Res.* 10: 235–244. doi:10.1080/02827589509382889
- **Status:** already in targets.yaml (crown ratio 0.30–0.45, ages 11–22).

### B5. Lintunen et al. 2011: models of 3D crown structure for Scots pine and silver birch in mixed forest
- **Citation:** *Can. J. For. Res.* 41: 1779–1794, corrigendum 42: 2153. LIGNUM group.
- **Read level:** listed in the Lintunen 2013 thesis only.
- **For the model:** probably the closest published LIGNUM-style birch crown parameterisation. Get the full text.

### B6. Lintunen 2013: crown architecture in mixed boreal forests (PhD thesis)
- **Citation:** *Dissertationes Forestales* 165. doi:10.14214/df.165
- **Access:** open PDF (CC BY-NC-ND). **Read level:** full text of the 55-page summary. The five articles are **not** reprinted, so the LIGNUM birch parameters from Lintunen et al. 2011 aren't in it. Its measured branch numbers for stand birch are in 05, section B.
- **Says:**
  - Under competition, birch makes fewer and smaller branches with longer leafless parts.
  - In young birch, the main branches' share of biomass grew at the stem's expense as competition rose. This seems to point the other way from B1, so read both.
  - In dense stands, birch lets more light through the canopy than pine of the same height.
  - Conduit size shrinks from stem to branches to petioles.

### B7. Kalliovirta & Tokola 2005: DBH and age from height, crown width and stand data
- **Citation:** *Silva Fennica* 39(2), doi:10.14214/sf.386
- **Access:** open (CC BY-SA 4.0). **Read level:** abstract.
- **Says:** Finnish NFI trees, including birch. DBH predicted from crown width and height, with RMSE 7.3–14.9% of mean DBH.
- **For the model:** a possible source of crown-width data for stand birch. Don't invert the regression.

### B8. Klepacki 2017: height and crown of 4-year-old silver birch
- **Citation:** *Forest Research Papers* 78(2): 171–178. doi:10.1515/frp-2017-0019
- **Access:** free to read, but **all rights reserved** (no open licence; corrected in v2). **Read level:** full text (tables).
- **Says:**
  - **Planted** 4-year-old birch (2/0 stock) in north-east Poland.
  - Heights 0.61–2.05 m (fresh mixed coniferous site) and 0.37–1.17 m (fresh mixed deciduous site).
  - Crown diameter ≈ 0.082 + 0.567·h and 0.068 + 0.428·h (my reading of the table's variables), n = 30 each.
- **For the model:** a juvenile size check. Planted stock, so it isn't natural regeneration.

### B9. Hemery, Savill & Pryor 2005: crown width of open-grown trees
- Already INFO in targets.yaml. Open-grown only.

---

## C. Allocation and biomass equations

### C1. Repola 2008: biomass equations for birch in Finland
- **Citation:** *Silva Fennica* 42(4): 605–624. doi:10.14214/sf.236
- **Read level:** full text. Coefficients and checks are in reports/round41_research_pack.md.
- **Key points:**
  - Eqs. 9 and 10 use dS, verified against his Table 8.
  - The foliage equations are valid only for DBH 11–26 cm (N = 21).
  - Branch biomass includes bark.
  - Prefer A3 and A6 for crown parts.

### C2. Repola 2009: biomass equations for Scots pine and Norway spruce
- doi:10.14214/sf.184. Not birch: useful later for spruce.

### C3. Aosaar et al. 2016: biomass production and nitrogen balance of a naturally afforested silver birch stand, Estonia
- **Citation:** *Silva Fennica* 50(4): 1628. doi:10.14214/sf.1628
- **Access:** open (CC BY-SA 4.0). **Read level:** abstract.
- **Credited as the model's alpha (4.8) source, but that is not supported.** A full-text read (4 Nov) found no photosynthesis, light, LAI or GPP data in the paper, and no value of 4.8. The nearest derivable ratio is NPP ÷ leaf mass = 4.63. See 05, section A.
- **Says:**
  - The stand regenerated naturally on **abandoned fertile farmland**, aged 8–17 years.
  - Density fell from about 11,600 to about 2,700 trees/ha by self-thinning.
  - At 17: above-ground about 94 Mg/ha; stemwood about 76; branches about 7.3 plus twigs about 0.8. That's branches ≈ 11% of stemwood.
  - Stemwood current annual increment peaked at about 10 Mg/ha/yr at age 15.
  - Leaf production about 3 Mg/ha/yr.
  - Fine roots about 1.4 Mg/ha.
  - Tree N demand about 103 kg/ha/yr, about 68% to leaves.
- **For the model:**
  - Alpha comes from a young, very fertile stand, which supports open issue 3 (a fertility limit is needed for average sites).
  - The density figures give a natural self-thinning benchmark for young stands.
  - The branch:stem ratio is a check.

### C4. Varik, Aosaar & Uri 2011: biomass production in silver birch stands, Oxalis site type
- **Citation:** *Metsanduslikud uurimused / Forestry Studies* 51: 5–16. doi:10.2478/v10132-011-0073-y
- **Access:** **paywalled** (the publisher page needs a login; corrected in v2). **Read level:** abstract.
- **Says:**
  - Natural stands on fertile forest land, southern Estonia.
  - Above-ground biomass: 39.9 t/ha at 14 years, 140.3 at 32, 224.3 at 45.
  - Stem current annual production 4.7–7.5 t/ha/yr.
  - **LAI 2.5–4.4.**
- **For the model:** stand biomass targets at 32 and 45. Likely the origin of the "Baltic LAI 2.5–4.5" target.

### C5. Uri et al. 2012: Estonian silver birch chronosequence
- **Citation:** *Forest Ecology and Management*. doi:10.1016/j.foreco.2011.11.033 (the DOI resolves; title and content to confirm).
- **Read level:** none yet.

---

## D. Wood, hydraulics and leaves

### D1. Sellin et al. 2012: size-dependent leaf and shoot hydraulic conductance in silver birch
- **Citation:** *Trees* 26: 821–831. doi:10.1007/s00468-011-0656-5
- **Read level:** abstract.
- **Says:** shoot hydraulic conductance rose with the Huber value. Sun and shade leaves differ.

### D2. Ishihara & Kikuzawa 2009 (already in the project)
- **Citation:** *Annals of Botany* 104: 1195.
- **Says:** short shoots carry only a terminal bud.
- **Unverified:** I couldn't open the paper (PMC blocked automated access). From memory, the study species may be *Betula grossa*, a Japanese birch, not *B. pendula*. Confirm the species, and flag it in the species file if it isn't silver birch.

---

## E. Open questions this section raises

1. **Allocation order.** Ilomäki 2003 reports results conflicting with a "priority principle". Read the full text before redesigning ring-first allocation.
2. **Bud number and crown density.** Sievänen 2018 found that LIGNUM needs local-density control of lateral bud number. Test it against the every-other-year pattern.
3. **Stem share.** The model is about 97–98% stem at age 30, against Ilomäki's 80–96% range. Confirm like for like.
4. **Branch reach.** Mean branch length ∝ crown length (Ilomäki); branch number, thickest branch and angle (Mäkinen et al. 2003). Turn these into sourced targets once the full texts are in hand.

## Papers to request (paywalled)

Ilomäki 2003; Lintunen et al. 2011; Lintunen & Kaitaniemi 2010; Mäkinen, Ojansuu & Niemistö 2003; Mäkinen 2002; Maillette 1982 I and II; Kaitaniemi et al. 2020.


---
---

# 02: Stand dynamics, density, self-thinning and mortality

Part of the birch knowledge base (see 00_index.md). Compiled 3 Nov 2026 by Claude (chat). Read levels and rules are as in 01_crown.md.

---

## A. Density and self-thinning

### A1. Hagemeier & Leuschner 2019a and 2019b: German silver birch stands
- **Citations:** *Forests* 10(3): 265 (2019a) and *Forests* 10(10): 925 (2019b). doi:10.3390/f10030265 and doi:10.3390/f10100925
- **Access:** open (MDPI).
- **Already in targets.yaml:**
  - LAI 3.6–5.4 (mean 4.59);
  - light under the canopy 6.4–19.8% (median 14.8%), diffuse light;
  - one stand at 45 years with 880/ha, one at 67 years with 420/ha (INFO only);
  - extinction coefficient 0.37.
- **Note:** an earlier phantom citation (Funct. Ecol. 33: 1688) was removed in phase 35.

### A2. Hynynen 1993: self-thinning models for even-aged pine, spruce and birch
- **Citation:** *Scand. J. For. Res.* 8(3): 326–336.
- **DOI:** possibly 10.1080/02827589309382781. That DOI came from the fabricated birch.zip, so confirm it independently.
- **Access:** paywalled. **Read level:** abstract.
- **Says:**
  - 41 **unthinned** permanent plots in Finland.
  - Stem number is modelled against mean diameter (Reineke and the −3/2 rule).
  - **The slope differs by species**, and within a species the intercept varies with site index.
- **For the model:** the sourced self-thinning line for birch the project has been looking for. Get the full text and propose it as a target (maximum density against quadratic mean diameter), adjusted for site index.

### A3. Aosaar et al. 2016: naturally afforested silver birch stand, Estonia
- **Citation:** *Silva Fennica* 50(4): 1628. doi:10.14214/sf.1628
- **Access:** open (CC BY-SA 4.0). **Read level:** abstract.
- **Says:** natural regeneration on fertile abandoned farmland, **about 11,600 trees/ha at age 8, falling to about 2,700 at 17** by self-thinning. It is also the alpha source (see 01_crown.md, C3).
- **For the model:** a natural young-stand density trajectory. Useful for the parked "natural start density" issue and as a self-thinning check for the dense-regeneration test.

### A4. Varik, Aosaar & Uri 2011: silver birch stands on the Oxalis site type, Estonia
- **Citation:** *Forestry Studies* 51: 5–16. doi:10.2478/v10132-011-0073-y
- **Access:** **paywalled** (corrected in v2). **Read level:** abstract.
- **Says:** above-ground biomass 39.9, 140.3 and 224.3 t/ha at 14, 32 and 45 years. Stem current annual production 4.7–7.5 t/ha/yr. LAI 2.5–4.4.
- **For the model:** stand-level biomass checks at 32 and 45. Propose them as targets; they're not approved.

### A5. Niemistö 1995: spacing and yield of silver birch
- **Citation:** *Scand. J. For. Res.* 10: 245. doi:10.1080/02827589509382890
- **Says:** dominant height was independent of spacing (400–3,100/ha) in young stands. Already used in phase 33.

### A6. Karlsson, Albrektson, Forsgren & Svensson 1998: natural birch regeneration on abandoned farmland, Sweden
- **Citation:** *Silva Fennica* 32(3): 683. doi:10.14214/sf.683
- **Access:** open (CC BY-SA 4.0). **Read level:** full text (text only; the figures weren't readable).
- **Says:**
  - 29 established stands, with the inclusion threshold at ≥1,000 birch stems/ha.
  - **84–92% of the birches were downy birch.**
  - Site preparation raised density. Seed trees were within about 80 m.
- **For the model:** limited value, because it is mostly downy birch.

### A7. Dahlgren Lidman 2022: natural regeneration and management of birch (PhD thesis, SLU)
- **Citation:** *Acta Universitatis Agriculturae Sueciae* 2022:54. doi:10.54612/a.4bujj1inqv
- **Full text:** research.slu.se/files/19133304/fulltext.pdf (automated fetch failed; open it in a browser).
- **Read level:** abstract.
- **Says:**
  - Dry soils need site preparation; wet soils regenerate easily.
  - The silver/downy share varies with temperature sum.
  - Pre-commercial thinning strongly shapes dense birch–spruce mixtures.
  - The birch share declines with age after canopy closure in spruce mixtures.
- **For the model:** likely holds Swedish natural seedling densities and early heights. It is also the probable origin of the "Dahlgren Lidman 2023" first-year height cited in phase 37. Check that figure.

---

## B. Height and top height

### B1. Eriksson, Johansson & Kiviste 1997: Swedish birch site-index curves
- **Citation:** *Scand. J. For. Res.* 12: 149–156.
- **DOI:** 10.1080/02827589709355396 per earlier phases. The fabricated birch.zip gave …355406, so confirm.
- **Access:** paywalled.
- **Status:** coefficients confirmed via Elfving 2010 (Heureka report, Appendix 9, p. 58). Breast-height age is used, with total age = breast-height age + 4. The top-height definition is unconfirmed (row 15 of DECISIONS.md).

### B2. Elfving 2010: growth modelling in the Heureka system (SLU report)
- **Says:** birch top height is read from the stand height–diameter curve at the mean diameter of the 100 largest-diameter trees per hectare. This is the maintainer's approved option 1. It isn't yet implementable, because the height–diameter function isn't named.

### B3. Söderberg 1992: Swedish height functions (SLU, Dept. of Forest Survey, Report 52)
- Still needed to settle top height. Not found openly online.
- **THREC** (CRAN R package, Ogana & Arias-Rodil 2023) is **not** Söderberg. It is also **GPL-3**, so don't copy its code. Its "hdom" is the height of the single largest-diameter tree per plot, which is a different convention.

### B4. Dubois, Verkasalo & Claessens 2020: potential of birch for forestry in Western Europe (review)
- **Citation:** *Forests* 11(3): 336. doi:10.3390/f11030336
- **Access:** open (CC BY). **Read level:** abstract plus summary.
- **Says:**
  - Height growth is fastest early, drops sharply at 30–40 years, and is very low at 50–60.
  - Silver birch has a longer phase of fast growth than downy birch.
  - MAI is 5–10 m³/ha/yr; maximum CAI is 12–23 m³/ha/yr at about 15 years.
  - Vitality declines before 100 years. Heart discoloration and rot start at 60–70 years.
  - Crown expansion and stem growth are irreversibly shaped in the first 10 years in dense natural stands.

---

## C. Management practice (for managed mode)

### C1. Hynynen & Niemistö 2009: silviculture of silver birch in Finland (waldwissen.net)
- **Says** (planted stands):
  - 1,600 seedlings/ha.
  - First thinning at dominant height 13–15 m, to about 700/ha; second about 15 years later, to 350–400/ha.
  - Self-pruning clears stems to 5–7 m by the first thinning.
  - Live crown ≥50% for vigour.
  - Rotation 40–60 years; vitality declines before 100.
- **For the model:** a cross-check for managed mode (Skogsstyrelsen 2014), and a natural self-pruning height to compare with the model's lowest live branch.

### C2. Hynynen et al. 2010: silviculture of birch in northern Europe
- **Citation:** *Forestry* 83: 103–119. doi:10.1093/forestry/cpp035. Already used; crown ratio ≥0.50 is INFO.

---

## D. Mortality, old age and damage (for open issue 4)

### D1. Starikova et al. 2025: 50-year dynamics of old silver birch forests, Belavezhskaya Pushcha (Belarus)
- **Citation:** *Baltic Forestry* 31(2): id754. doi:10.46490/BF754
- **Read level:** abstract.
- **Says:**
  - Six permanent plots, natural birch stands 84–111 years old (in 2023), remeasured 1972–2023.
  - Birch stands moved to spruce, directly or via an aspen phase of about 20 years. Broadleaves came in after more than a century.
- **For the model:** the full text may hold birch survival rates at 80–110 years, for old-age death and the 200-year run.

### D2. Nykänen et al. 1997: snow damage factors
- Already in KNOWN_ISSUES (phase 31): stem breakage is the most common snow damage; small, slender trees are more prone to bending; birch bends rather than snaps.

### D3. Lehtonen et al. 2014: crown snow loads in Finland
- *Silva Fennica* (silvafennica.fi/article/1120). Already in the project.

### D4. Dubois et al. 2020 (B4)
- Reports drought-related birch mortality after 1976 and 2003 in England and Scotland. Useful later for the drought option.

---

## E. Open questions

1. **Self-thinning line:** get Hynynen 1993 and propose a sourced birch self-thinning target.
2. **Natural start density:** Aosaar 2016 gives about 11,600/ha at 8 years on fertile ground. Dahlgren Lidman 2022 likely has Swedish figures.
3. **Top height:** Söderberg 1992 is still missing.
4. **Old-age death:** look in Starikova 2025 and in yield-table literature for survival of birch past 80 years.

## Papers to request

Hynynen 1993; Eriksson et al. 1997; Söderberg 1992 (SLU report); Starikova et al. 2025 (full text may be open); Dahlgren Lidman 2022 (open: open it in a browser).


---
---

# 03: Environment: water, fertility, temperature and phenology

Part of the birch knowledge base (see 00_index.md). Compiled 3 Nov 2026 by Claude (chat). Read levels and rules are as in 01_crown.md.

---

## A. Water and drought

### A1. Granier, Bréda, Biron & Villette 1999: BILJOU water balance model
- **Status:** already adopted in round 40 for the soil-water option (off by default). The REW 0.4 threshold comes from Granier's work.
- **Open issue:** in round 40 the option had no effect even in 2018. Revisit after the crown fix: model trees with too few leaves transpire too little.

### A2. Sellin, Niglas, Õunapuu-Pikas & Kupper 2014: water deficit in silver birch under varying humidity
- **Citation:** *BMC Plant Biology* 14: 72. doi:10.1186/1471-2229-14-72
- **Access:** open (CC BY 2.0; data CC0). **Read level:** full text (key figures).
- **Says:**
  - 5-year-old saplings at the FAHM site, Estonia.
  - Leaf hydraulic conductance **halves at about −1.2 MPa** (branch water potential).
  - Water-use efficiency drops steeply once stomatal conductance falls to about 0.06 mol m⁻² s⁻¹, at branch water potential below −1.0 MPa.
  - Leaf water potential was about −1.05 MPa when well watered, −1.25 MPa under moderate deficit, and −1.9 to −2.1 MPa under severe deficit.
  - Soil water potential reached −180 kPa in July in the humidified plots.
- **For the model:** sourced birch thresholds for stomatal closure and hydraulic decline, to check the model's stomata against.
- **Note:** "FAHM" is a real site (Free Air Humidity Manipulation, Rõka, Estonia). The phase 32 claim that seedlings reached 2.29 m at age 2 there was traced to a misread, and was debunked.

### A3. Norunda (SE-Nor) ICOS station: 2018 drought data
- **Dataset:** "Drought-2018 ecosystem eddy covariance flux product from Norunda". doi:10.18160/B63T-N9V2
- **Covers:** 2014–2018. **Licence:** CC BY 4.0.
- **Station data:** raw daily meteo files also exist (ICOS licence CC BY 4.0; ICOS asks users to consult the station PI).
- **Caveats:**
  - Check that the product includes soil water content and at which depths; the landing page doesn't list variables.
  - Norunda is, to my knowledge, a mature **conifer** forest near Uppsala (confirm). Use its soil moisture as a regional 2018 drought record, not as birch-stand data.

### A4. SMHI open data: Swedish climate
- Daily precipitation and temperature for Uppsala and Lysekil, for driving the water balance and temperature sums.
- Licence believed to be CC BY 4.0 (confirm on opendata.smhi.se).

---

## B. Fertility, productivity and temperature (open issue 3)

### B1. Aosaar et al. 2016: the alpha source
- **Citation:** *Silva Fennica* 50(4): 1628. doi:10.14214/sf.1628. Open (CC BY-SA 4.0).
- **Says:**
  - The stand regenerated naturally on **fertile abandoned farmland**, aged 8–17.
  - Stem CAI peaked at about 10 Mg/ha/yr at age 15.
  - N demand about 103 kg/ha/yr; net N mineralisation about 156 kg/ha/yr.
- **For the model:** alpha = 4.8 comes from an exceptionally fertile, N-rich site. That supports building a fertility limit for average Swedish forest land.

### B2. Liziniewicz et al. 2022: production of genetically improved silver birch plantations, southern and central Sweden
- **Citation:** *Silva Fennica* 56(1): 10512. doi:10.14214/sf.10512
- **Access:** open (CC BY-SA 4.0). **Read level:** abstract plus key results.
- **Says:**
  - 52 experiments.
  - Basal-area model of Korf type.
  - Simulated MAI of **6.0, 7.9, 10.5 and 12.8 m³/ha/yr** for site index **22, 25, 28 and 32 m**, with rotations of 60, 51, 45 and 31 years.
  - Improved birch on average southern-Swedish forest sites: 6–10.5 m³/ha/yr.
- **Caveat:** planted, genetically improved stock, so it sits above natural stands.
- **For the model:** a productivity-against-site-index ladder for calibrating a fertility scalar, separate from the height curves.

### B3. Eriksson et al. 1997 site-index curves (see 02_stands.md, B1)
- The fertility scalar should reproduce these curves at different site indices without changing their shape. That's why phase 34 rejected a single multiplier applied at all ages.

### B4. Bergh et al. 1998 and 2003 (nutrition and temperature effects on NPP)
- Cited by agents in phase 33: *Forest Ecology and Management* 110: 127 and 183: 327.
- **Not verified here.** Re-open both before use.

### B5. Dubois et al. 2020 review (see 02_stands.md, B4)
- Silver birch tolerates warmer temperatures than downy birch. It notes drought mortality in the UK in 1976 and 2003.

---

## C. Phenology (growing season, budburst)

### C1. Junttila & Hänninen 2012: the minimum temperature for budburst in Betula depends on the state of dormancy
- **Citation:** *Tree Physiology* 32: 337–345. doi:10.1093/treephys/tps010
- **Access:** paywalled. **Read level:** abstract.
- **Says:** in *B. pendula* and *B. pubescens* seedlings, the minimum temperature for budburst rises during dormancy induction and falls during release. Short chilling suffices; longer chilling speeds budburst.
- **For the model:** a basis for a temperature-driven budburst date, giving season length.

### C2. "Effects of dormancy and environmental factors on timing of bud burst in Betula pendula"
- Luke record (jukuri.luke.fi/items/37e6b02f-…). Authors and journal not yet confirmed.
- Probably a Finnish budburst modelling paper. Find its full citation.

### C3. Linkosalo et al. 2010: double-threshold temperature-sum model for birch flowering
- **Citation:** *Agricultural and Forest Meteorology* 150: 1579–1584. doi:10.1016/j.agrformet.2010.08.007
- About flowering, not leaves. Low priority.

### C4. Maillette 1982 and Oleksyn et al. 2000 (see 01_crown.md)
- Heterophylly: early leaves flush at budburst; late leaves expand through the summer.

---

## D. Open questions

1. **Drought:** re-test the BILJOU option after the crown is fixed. Check the model's stomata against Sellin 2014's thresholds, and validate with Norunda 2018 soil moisture (confirm the variables).
2. **Fertility:** design a sourced fertility limit that keeps the Eriksson curve shape and reproduces the Liziniewicz MAI ladder by site index.
3. **Season length:** a budburst and leaf-fall model from Swedish temperature data (Junttila & Hänninen; find the Finnish budburst paper).


---
---

# 04: Open datasets and existing models

Part of the birch knowledge base (see 00_index.md). Compiled 3 Nov 2026 by Claude (chat). Read levels and rules are as in 01_crown.md.

**Licence rule (PROTOCOL.md section 3):**
- Datasets under CC BY can be used for calibration and comparison, with credit.
- Never copy code from GPL, non-commercial or unclear-licence sources. Published equations and values with citations are fine.
- Store downloads outside the repo (for example `birch-data\`), never in tree-data, and never commit them.

---

## A. Tree and stand datasets

| # | Dataset | What's in it | Birch? | Licence | Where |
|---|---|---|---|---|---|
| D1 | **Evo TLS, spring 2024** (Yrttimaa, Liikonen, Erkkilä & Vastaranta 2025, *Silva Fennica* 59(1): 24066, doi:10.14214/sf.24066) | 55 plots (32 × 32 m), 6,320 segmented trees, leaf-off TLS. Per tree: stem diameter, height, **crown projection area and crown diameter**. | **989 *Betula* spp. trees** (silver and downy not separated) | CC BY 4.0 | doi:10.23729/fd-5a800660-8bd8-35ef-ac9f-ac5c45f7fa77 |
| D2 | **Lapinjärvi TLS** (Luke, released 2019) | 18 plots on productive land, southern Finland. Point clouds (.laz); per tree: species, DBH, height (some), age (some), **crown base**, position; photos. | Silver birch is coded (3); count unknown | CC BY 4.0; cite Pitkänen, Raumonen & Kangas 2019 (ISPRS J. 147: 294–306) | mirrors.nic.funet.fi/index/geodata/luke/tls/2016/lapinjarvi/ |
| D3 | **Finnish permanent sample plots, 1985–86, 1990 and 1995** (Luke 2025, curator A. Lehtonen) | About 3,000 plots on a national grid, remeasured three times. Tree species, diameter, height, age, quality, damage; site type and management history. In Finnish. | Yes (national data) | CC BY 4.0 | doi:10.23729/fd-5dc47309-9d2e-3fd5-b12c-17e41e9824fe (Fairdata Etsin) |
| D4 | **Wytham Woods TLS and QSMs** (Calders et al.) | 876 segmented trees with optimised TreeQSM models, leaf-off, 42.8 GB. | **Species not stated: check before downloading** | CC BY 4.0 | doi:10.5281/zenodo.7307956 |
| D5 | **FOR-species20K** (already on the maintainer's PC) | TLS individual-tree scans | Yes | **GPL-3.0**: comparison only, never in outputs | tree-data folder (read-only) |
| D6 | **Norunda Drought-2018 flux product** | Eddy covariance and meteo, 2014–2018 | No (conifer site; confirm) | CC BY 4.0 | doi:10.18160/B63T-N9V2 |
| D7 | **SMHI open data** | Swedish daily weather | n/a | Believed CC BY 4.0 (confirm) | opendata.smhi.se |

**How each dataset could help**
- **D1** is the strongest open source found for a **stand-grown crown-width target**: crown diameter against height and stem diameter, for about 1,000 birches in managed southern Finnish forests. It is leaf-off, and silver and downy birch are mixed, so say so in any target.
- **D2** gives crown base heights for a self-pruning and crown-ratio check, and its point clouds could be QSM'd later.
- **D3** gives birch survival and growth over 10 years across Finland: a basis for mortality rates and diameter growth checks.
- **D4** has ready-made QSMs, but only if birch is present.

---

## B. Existing models (for ideas and equations, not code)

| Model | What it is | Relevance | Code licence |
|---|---|---|---|
| **LIGNUM** (Perttunen, Sievänen, Nikinmaa et al.) | Functional-structural tree model; the project's allocation is based on it | Core. Birch crown work by the same group (Lintunen et al. 2011; Sievänen et al. 2018) | Unknown: don't copy code; implement from papers |
| **CROBAS** (Mäkelä 1997, *Forest Science* 43: 7–24) | Pipe-model stand growth with crown rise | Crown rise, sapwood below the crown base | Implement from the paper |
| **ForestGALES / fgr** | Wind risk | Wind loads; birch drag and strength parameters | GPL-3 plus Commons Clause (non-commercial): **no code** (phase 31 decision) |
| **Heureka** (SLU; Elfving 2010) | Swedish forest planning system | Birch height curves and top height | Closed source; documentation open |
| **MOTTI** (Luke; Hynynen et al. 2002) | Finnish stand simulator | Birch growth, mortality and self-thinning models | Closed; equations in reports |
| **taperNOR** (CRAN; Hansen et al. 2023) | Norwegian taper and bark models | Already used for bark and taper | **Check its licence**; the equations from the paper are fine |
| **THREC** (CRAN; Ogana & Arias-Rodil 2023) | Swedish height-imputation models | Not Söderberg; not useful for top height | GPL-3: no code |
| **TreeQSM** (Raumonen et al.) | Builds QSMs from TLS | For turning D1, D2 or D5 scans into branch statistics | Check its licence before use |

---

## C. Suggested data pipeline (for a later round, on the maintainer's PC)

1. Download D1 (Evo) tree attributes only, not the point clouds, into `Downloads\birch-data\evo2024\`. Record the licence and citation.
2. Fit or summarise crown diameter against height and DBH for *Betula* spp. Propose a stand-grown crown-width target with its conditions (leaf-off, managed southern Finland, silver and downy mixed).
3. From D3, extract birch trees remeasured over 1985–1995. Compute 5-year survival and diameter growth by size class and stand density, as candidate mortality and growth checks.
4. Only after that, consider QSMs from D2 point clouds for branch-length distributions.


---
---

