# Birch paper extracts (full-text reading)

Source folder: `birch-data/papers/` (7 PDFs). Every PDF was read in full: the text layer page by page, with tables and figures checked against rendered page images. Where the text layer had scrambled a table, values were rebuilt from word coordinates or read from the image. Three figures were digitised from the PDF's own vector data (stated where used).

**Conventions**
- Page numbers are PDF page numbers. Where the journal's printed page differs, it is given as "printed p.".
- **QUOTED** = copied from the paper. **COMPUTED** = derived by me, with the calculation shown.
- "not found" = searched the full text and it isn't there.
- Every value is also in `key_values.csv` (589 rows).

---

## 1. Aosaar et al. 2016. Biomass production and N balance, naturally afforested silver birch, Estonia

Silva Fennica 50(4) id 1628, 19 pp.

**Study context (QUOTED, pp. 1–2, 6).** Species: *Betula pendula* only. Site: Kambja, southern Estonia (58°14′N, 26°44′E). The stand regenerated naturally on abandoned agricultural land (Glossic Podzoluvisol, loamy sand, fertile, former arable land). It is unmanaged: it self-thinned and dead wood was left on site. The data come from **one square plot of 0.03 ha**. Stand ages were 8–17 yr (calendar 2004–2013), with mean height 6.6–16.0 m and mean DBH 3.2–9.9 cm. AGB was measured from 70 model trees in total (11, 10, 12, 10, 10, 10 and 7 per year).

### Can "alpha = 4.8" be traced to this paper? **No.**
- The paper has **no** photosynthesis, GPP, LAI, leaf area, radiation, PAR or light-use data. A search of the whole text for photosyn/GPP/NPP/LAI/leaf area/radiat/light/alpha/quantum/assimil/PAR finds no such terms. The only carbon flux is soil respiration (p. 9).
- The string "4.8" appears only inside **14.8** (the N-budget residual, kg N ha⁻¹ yr⁻¹, Table 4) and **11.48** (stemwood N demand, Table 4).
- The closest natural derived quantities (all COMPUTED) are:

| Quantity | Value | How |
|---|---|---|
| Tree NPP ÷ foliage mass (age 10) | **4.63** yr⁻¹ | 13.02 / 2.81 (Table 4) |
| Aboveground NPP ÷ foliage mass | 3.81 | 10.70 / 2.81 |
| Mean MAI, ages 12–17 | 4.73 Mg ha⁻¹ yr⁻¹ | (4.3+4.5+4.6+4.9+5.1+5.0)/6 |
| Tabulated MAI at age 15 | 4.9 | Table 3 (QUOTED) |

None of these is 4.8, and none is a light-use parameter. If the project needs 4.8, it must come from another source or be documented as a calibration choice.

### Stand table (Table 3, p. 7, QUOTED; Mg ha⁻¹ dry mass)

| Age | H (m) | D1.3 (cm) | N (ha⁻¹) | G (m² ha⁻¹) | Leaves | Branches | Twigs | Stemwood | Stembark | CAI | MAI |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 8 | 6.6±0.6 | 3.2±0.1 | 11633 | 11.3 | 3.5 | 3.0 | 0.6 | 20.4 | 3.7 | 7.4 | 3.0 |
| 9 | 7.6±0.5 | 3.8±0.1 | 11533 | 13.2 | 2.9 | 3.7 | 1.0 | 24.4 | 4.4 | 4.7 | 3.2 |
| 10 | 8.5±0.6 | 4.4±0.1 | 10200 | 15.2 | 2.8 | 3.9 | 0.7 | 30.8 | 5.0 | 7.0 | 3.6 |
| 11 | 9.3±0.7 | 4.7±0.1 | 9500 | 16.6 | 2.1 | 4.4 | 0.8 | 38.4 | 5.6 | 8.2 | 4.0 |
| 12 | 10.4±0.7 | 5.4±0.2 | 8300 | 18.7 | 3.7 | 5.0 | 1.5 | 44.6 | 6.8 | 7.4 | 4.3 |
| 13¹ | 10.9±0.8 | 5.8±0.2 | 7670 | 20.1 | 3.1 | 5.0 | 0.8 | 51.6 | 7.2 | 7.4 | 4.5 |
| 14 | 12.2±0.6 | 6.4±0.2 | 6567 | 21.3 | n.e. | 6.0 | 0.8 | 56.6 | 8.3 | 5.7 | 4.6 |
| 15 | 13.2±0.6 | 7.9±0.3 | 4233 | 20.7 | n.e. | 6.3 | 1.0 | 65.6 | 8.5 | 9.7 | 4.9 |
| 16 | 14.4±0.5 | 9.1±0.3 | 3133 | 20.5 | n.e. | 6.9 | 0.8 | 72.2 | 8.7 | 6.8 | 5.1 |
| 17 | 16.0±0.6 | 9.9±0.3 | 2733 | 20.9 | n.e. | 7.3 | 0.8 | 76.3 | 9.1 | 4.6 | 5.0 |

¹ Age-13 data from Uri et al. 2012. n.e. = not estimated. CAI and MAI are in Mg ha⁻¹ yr⁻¹.

Notes on the stand table:
- COMPUTED checks: (76.3+9.1)/17 = 5.02, so **MAI and CAI use stemwood plus stembark**, even though the caption says "stemwood". Leafless AGB at 17 = 7.3+0.8+76.3+9.1 = 93.5, matching the abstract's 94.
- Self-thinning removed 35% of living trees in 2011 (age 15) and 26% in 2012 (p. 6). Basal area levelled off at about 20 m² ha⁻¹.
- Stem volume at 17 yr was 161 m³ ha⁻¹; stemwood density 0.53 g cm⁻³ (p. 7).
- AGB allometry, Eq. 1 / Table 2 (p. 3): y = a·x^b, with y = tree AGB in g and x = DBH in cm. Values of (a, b): 2004 (142.19, 2.25); 2005 (125.17, 2.30); 2006 (114.13, 2.39); 2007 (123.18, 2.38); 2008 (88.494, 2.55); 2009 (136.03, 2.33); 2013 leafless (82.09, 2.60). R² is 0.98–0.99. The 2004–2009 values include leaves.

### Roots (QUOTED)
- Coarse root + stump biomass was 8.4 Mg ha⁻¹, about 43% of it stump core (p. 7, from Varik et al. 2015; the stand age is not stated).
- Fine-root biomass (<2 mm) was 1.4 Mg ha⁻¹ (p. 7).
- Stump and coarse-root production was assumed to equal **21% of aboveground woody production** (p. 4).

### NPP split and N, 10-yr-old stand (Table 4, p. 8, QUOTED)

| Component | Production (Mg ha⁻¹ yr⁻¹) | Biomass (Mg ha⁻¹) | N (%) | N store (kg ha⁻¹) | N demand (kg ha⁻¹ yr⁻¹) | Share of NPP (COMPUTED) |
|---|---|---|---|---|---|---|
| Leaves | 2.81 | 2.81 | 2.507 | 70.45 | 70.45 | 21.6% |
| Stemwood | 6.45 | 30.82 | 0.178 | 54.86 | 11.48 | 49.5% |
| Stembark | 0.56 | 4.99 | 0.532 | 26.55 | 2.98 | 4.3% |
| Twigs | 0.72 | 0.72 | 0.827 | 5.95 | 5.95 | 5.5% |
| Branches | 0.16 | 3.85 | 0.497 | 19.13 | 0.80 | 1.2% |
| Stump | 0.61 | 3.59 | 0.230 | 8.25 | 1.41 | 4.7% |
| Coarse roots | 0.82 | 4.77 | 0.473–0.622 | 25.99 | 4.45 | 6.3% |
| Fine roots | 0.89 | 1.35 | 0.655 | 8.98 | 5.83 | 6.8% |
| **Trees total** | **13.02** (above 10.70, below 2.32) | | | | **103.35** | |
| Herbs above / below | 0.12 / 1.68 | | 1.746 / 0.768 | 2.05 / 12.90 | 2.05 / 12.90 | |

N fluxes (kg ha⁻¹ yr⁻¹, Table 4):

| Flux | Value |
|---|---|
| Total plant N demand | 118.3 |
| Leaching | 0.92 |
| N₂O-N | 0.12 |
| N₂-N | 83.0 |
| Deposition | 6.4 |
| Net N mineralisation | 156.0 |
| Retranslocation | 45.0 (kg ha⁻¹) |
| Input − (demand + output) | 14.8 |

Other N and litter values (QUOTED):
- Aboveground NUE: 117 kg kg⁻¹ yr⁻¹ (p. 8).
- Leaf litter: 3.5 Mg ha⁻¹ yr⁻¹ (2004) and about 2.7 (2005–06). N flux via litter: 32 kg ha⁻¹ yr⁻¹ (p. 10).
- Leaf N retranslocation: 60% (2006) and 55% (2004) (p. 13).

**Annual aboveground NPP for other years (COMPUTED** with the paper's own method: leaves + twigs + Δbranches + CAI, p. 4). Values in Mg ha⁻¹ yr⁻¹: age 9 = 9.3; **age 10 = 10.7**, which reproduces Table 4's 10.70 and validates the method; age 11 = 11.6; age 12 = 13.2; age 13 = 11.3. Ages 14–17 can't be done because leaves were not estimated.

Cited values, not from this stand: fine-root production 1.4 and 1.3 Mg ha⁻¹ yr⁻¹ in 32- and 45-yr stands; leaf mass 2.0–3.5 Mg ha⁻¹ across 6–60-yr stands (p. 12).

---

## 2. Lintunen 2013. Crown architecture and its role in species interactions (Dissertationes Forestales 165)

**Are the original articles included? No.** The PDF has 55 pages: pp. 1–40 are the summary and pp. 41–55 are references. The five articles are listed on p. 5 but not reprinted:
1. Kaitaniemi & Lintunen 2010, *Ann. For. Sci.* 67: 604 (neighbour identity; pine, larch, birch).
2. Lintunen & Kaitaniemi 2010, *Trees* 24: 411–424 (B. pendula crown responses).
3. Lintunen & Kalliokoski 2010, *Tree Physiol.* 30: 1433–1447 (conduits).
4. **Lintunen, Sievänen, Kaitaniemi & Perttunen 2011, *Can. J. For. Res.* 41: 1779–1794**, plus a corrigendum in *CJFR* 42: 2153 (2012).
5. Lintunen et al. 2013, *CJFR* (light transmission).

Article IV's **LIGNUM parameters (Tables A1–A2, 20 predicted crown characteristics for birch) are not found** in this PDF. Only model *outputs* appear, in Figs. 5, 6 and 8, which I digitised below.

**Data context (QUOTED, pp. 14–16).**
- Design A: 5 even-aged mixed birch–spruce–pine stands near Hyytiälä (61°50′N, 24°18′E), with 4 birches per site. Birch age/height: site 1 13 yr/5 m (sapling, MT); site 2 29/13 (pole, MT); site 3 48/21 (mature, MT); site 4 36/19 (pole, OMT); site 5 32/12 (pole, VT). Stand BA was 4–30 m² ha⁻¹. The source's footnote letters for OMT and MT are swapped.
- Design B: **73 B. pendula** in 12 planted or experimental mixed stands, 60–63°N, all on MT (medium-fertility) sites. Birch ages 4–32 yr, heights 2–17 m.
- More than 200 digitised trees in total. The author says the results suit young, medium-fertility sites; trees taller than 20 m are poorly represented (p. 39).

### Neighbour effects on B. pendula (Table 3, p. 23, QUOTED; mean, 95% CI in brackets)

| Trait | Neighbour *Alnus* | Neighbour *Betula* | Neighbour *Pinus* | Neighbour *Larix* |
|---|---|---|---|---|
| Height growth (cm yr⁻¹) | – | 49.1 (7.9) | 54.3 (8.0) | 54.4 (10.0) |
| Growth vigour (long-shoot length ÷ branch length) | 0.14 (0.06) | 0.19 (0.09) | 0.11 (0.03) | 0.10 (0.07) |
| GO1 branch number per 10% of crown length | 3.8 (0.5) | 5.2 (0.3) | 5.8 (0.4) | 6.5 (0.3) |
| GO1 branch length (cm) | 75.3 (7.6) | 102.0 (7.0) | 101.2 (5.6) | 112.2 (10.1) |
| Short shoots per branch | – | 53.0 (5.5) | 46.5 (5.5) | 54.3 (9.5) |

**Competition responses (QUOTED, qualitative, p. 23).** Under heavier competition, B. pendula grew a longer, thinner stem with a shorter crown. Its main branches were fewer, shorter and thinner, it had longer shootless branch sections and fewer short shoots, but more current long shoots. Growth vigour fell with competition in older trees and rose in young trees.

### Model output for a 10-m birch (Fig. 5, p. 26). COMPUTED, digitised from PDF vectors
Inputs: H = 1000 cm, DBH = 10 cm, CH = 400 cm, age 20, CI6 = 3, CI7 = 10, CI9 = 0.2. The series start at 4 m, which fits CH being the crown-base height; that reading is my inference.

| Height in tree (m) | 4.0 | 5.2 | 6.4 | 7.6 | 8.8 | 10.0 |
|---|---|---|---|---|---|---|
| GO1 branch chord length (m) | 1.54 | 1.29 | 1.03 | 0.75 | 0.48 | 0.25 |
| GO1 branch base diameter (cm) | 1.47 | 1.20 | 0.97 | 0.78 | 0.63 | 0.52 |

Branch number per m of stem (dashed line, ±0.1, digitised at its own x-positions): 6.0 at 4.3 m; 6.3 at 5.0 m; 8.3 at 6.0 m; 9.9 at 7.0 m; 10.9 at 8.0 m; 12.5 at 9.0 m; 13.0 at 9.7 m.

**Shoots per branch axis (Fig. 6C, p. 27, COMPUTED, same tree):**

| Height (m) | 4.0 | 6.4 | 8.8 | 10.0 |
|---|---|---|---|---|
| Long shoots, GO2 | 2.15 | 2.66 | 3.32 | 3.70 |
| Long shoots, GO3 | 1.00 | 1.24 | 1.54 | 1.73 |
| Short shoots, GO2 | 6.83 | 6.96 | 4.90 | 3.36 |
| Short shoots, GO3 | 3.73 | 3.75 | 3.45 | 3.20 |

Short shoots typically carry 2 leaves and make up most of the foliage (p. 27, QUOTED). Branch angle decreases with height in the crown, and at a given height longer branches have smaller angles (p. 26). **Angle values: not found.**

### Biomass shares under competition (Fig. 8A, p. 29). COMPUTED from PDF vectors
The 10-m tree is simulated with DBH 11.6, 10.5 and 7.7 cm for low, medium and high competition. The y-axis runs 80–100% with an axis break.

| Share of aboveground dry mass | Low | Mid | High |
|---|---|---|---|
| Stem | 89.2% | 88.2% | 83.8% |
| GO1 branches | 3.9% | 4.2% | 5.5% |
| GO2–3 branches | 2.2% | 2.3% | 2.5% |
| GO4–5 branches | 0.6% | 0.5% | 0.5% |
| Foliage (all orders) | 4.2% | 4.7% | 7.6% |

The caption (QUOTED) says total crown dry biomass fell from 31 to 15 kg. It is unclear whether the stem is included.

### Other birch numbers (QUOTED)
- Mean SLA 13.6 m² kg⁻¹ (p. 28).
- Leaf angle becomes 53° more vertical from crown base to top (p. 28).
- LIGNUM leaf transmittance fixed at 0.06, with leaves modelled as triangles (p. 22).
- Conduit scaling coefficient 0.39 (p. 24).
- Maximum unshaded PAR 2055 MJ m⁻² per growing period (Fig. 9).
- **Crown width or radius values: not found.**

---

## 3. Yrttimaa et al. 2025. Evo TLS dataset (Silva Fennica 59(1) id 24066, data note)

- **Leaf condition: leaf-off.** Scans were made 22 Apr – 14 May 2024 with a Riegl VZ-400i (1550 nm, 600 kHz, up to 8 returns). Each plot had 9 scan positions about 16 m apart, upright plus tilted (Table 1, p. 3).
- **Plots:** 55 plots of 32 × 32 m at Evo, southern Finland (61°12′N, 25°07′E). They are regularly monitored plots set up in 2014, ranging from single- to mixed-species stands and from even-aged to multi-layered (p. 2).
- **Segmentation:** LIS TreeAnalyzer. Stems were found by a Hough circle fit in a 30-cm slice at **1.5–2.5 m** (not at 1.3 m). Points with reflectance < −2.5 dB or deviation > 3 were filtered out first. Trees were then grown upward by 3D Dijkstra region growing, allowing gaps up to 0.6 m, with a minimum tree height of 1.5 m (pp. 4–5).
- **Height** is "the vertical range of the tree's point cloud" (p. 5). **Crown diameter and projection area** are "determined from the properties of a polygon enveloping the tree point cloud projected onto the XY plane" (p. 5). Whether the diameter is the maximum width or an equivalent-circle value is **not stated**.
- **Accuracy:** crown-diameter and height accuracy are **not found**. The only accuracies given are: tree detection 90% overall versus field inventory; georeferencing < 3 cm; point accuracy 3 mm at 50 m (p. 7).
- **Birches: 989 trees coded "3 = Birches (Betula L. spp.)"**, so silver and downy birch are not separated. Species came from matching TLS trees to the 2014 field inventory. Trees with no species (1882) are buffer trees and trees under 5 cm DBH in 2014. In total 6320 trees were segmented, 115 per plot on average (range 30–369, buffer trees included) (Table 2, pp. 5–6).
- **Plot stand data (Table 2, p. 6), min–max (mean):**

| Attribute | Range (mean) |
|---|---|
| N (trees ha⁻¹) | 166–2080 (697) |
| G (m² ha⁻¹) | 4.9–50.9 (30.2) |
| V (m³ ha⁻¹) | 40.9–625.1 (324.0) |
| Dg (cm) | 16.9–45.2 (28.7) |
| Hg (m) | 11.8–31.5 (22.1) |
| Pine BA% | 0–99.9 (55.5) |
| Spruce BA% | 0–100 (26.7) |
| "Birch_BA%" (all deciduous trees) | 0–99.3 (17.8) |

- **Data:** DOI https://doi.org/10.23729/fd-5a800660-8bd8-35ef-ac9f-ac5c45f7fa77, licence **CC BY 4.0** (p. 7). Files: per-plot .laz 1.4 point clouds (ETRS-TM35FIN/EPSG:3067, N2000 heights, with extra fields `h` and `treeid`), a tree-attribute CSV and a plot-attribute CSV (Table 2). **Download steps: not found.** The paper gives only the DOI and a supplementary "Metadata of research data.pdf", which is not in the folder. Nothing was downloaded.
- **Caveats for use:** these are leaf-off birch crowns (branch envelope only), the species is Betula spp., and "stem diameter" is measured at the slice height, not at breast height.

---

## 4. Kalliovirta & Tokola 2005. DBH and age from height and crown width (Silva Fennica 39(2): 227–248)

**Data (QUOTED, pp. 3–5).** Finnish NFI permanent plots, 1995 measurements, covering the whole of Finland (managed forest). Crown width was taken as "the widest dimension of the crown", measured with a Kajanus tube. "Birch" is not split by species. Damaged and diseased trees were removed. The birch modelling set has **2282 trees**: 39, 871, 1190 and 182 in regions 1–4 (hemiboreal to north boreal). The validation set is 120 birches near Hyytiälä (Korpela 2004).

**Birch ranges (Table 1, p. 5 / printed 231, QUOTED):**

| Variable | Mean | SD | Min | Max |
|---|---|---|---|---|
| DBH (mm) | 115 | 56 | 6 | 532 |
| Height (dm) | 113 | 44 | 16 | 310 |
| Max crown diameter (dm) | 33 | 12 | 7 | 104 |
| Age (yr) | 48 | 20 | 3 | 148 |

**No equation predicts crown width.** Crown width is only ever a *predictor*. The birch equations are below (Eqs. 1–7, p. 6; Tables 4, 6, 10, 12).

DBH models: √d = b0 + bH·√h + bD·√dcrm [+ b3·x], with d in mm and h, dcrm in dm. Back-transform with d = f² + VAR.

| Model | b0 | bH | bD | b3 (variable) | VAR | RMSE |
|---|---|---|---|---|---|---|
| 9.1.3 (country) | −1.591 | 1.153 | – | – | 1.854 | 13.1% (15.0 mm) |
| 9.2.3 | −0.982 | – | 2.019 | – | 1.770 | 12.8% (14.7 mm) |
| **9.3.3** | **−3.341** | **0.700** | **1.143** | – | **1.000** | 9.6% (11.0 mm) |
| 9.4.3 | −0.656 | 0.805 | 1.056 | −0.00302 (temperature sum, °C d) | 0.838 | 8.8% (10.1 mm) |
| 1.3.3 / 2.3.3 / 3.3.3 / 4.3.3 (regional h + dcrm) | −6.978 / −4.250 / −3.420 / −3.770 | 0.972 / 0.804 / 0.741 / 0.886 | 1.271 / 1.028 / 1.107 / 1.108 | – | 1.019 / 0.780 / 0.787 / 1.185 | see CSV |

All 16 regional birch models are in the CSV.

COMPUTED check: at the birch means (h = 113, dcrm = 33), model 9.3.3 gives (−3.341 + 0.700·√113 + 1.143·√33)² + 1.000 = **114.8 mm**, against a reported mean of 115 mm. This confirms the linear-in-square-root form and the units.

Age models: ln(age) = b0 + bH·ln h + bD·ln dcrm, back-transformed as age = e^f·(1 + ½VAR).
- 9.5.3: 1.252 + 0.544 ln h
- 9.6.3: 2.225 + 0.454 ln dcrm
- 9.7.3: 1.264 + 0.371 ln h + 0.232 ln dcrm (VAR 0.144)

Validation (Table 7): the country h + dcrm model gives a birch bias of 4 mm (2%) and SE 21 mm (11%).

Inconsistency in the source: for region 4 birch, Table 5 lists the third variable as D9 (coefficient −0.806), while the text on p. 11 says "mean age". The coefficient's size matches the other D9 dummies (−0.738, −0.789).

---

## 5. Liziniewicz et al. 2022. Production of genetically improved silver birch plantations, S & central Sweden

Silva Fennica 56(1) id 10512.

**These are planted, genetically improved stands.** The 52 experiments were planted 1990–2010 at about 2500 trees ha⁻¹, on fertile forest sites and former farmland, with different breeding levels (pp. 1–3). There are 228 plots of 0.04–0.1 ha. All were thinned at least once: 7–56% of BA removed (mean 23%), at ages 11–26, usually three or fewer thinnings. Mortality was assumed negligible (p. 6). The models are only valid for initial stocking of **1800–2200 trees ha⁻¹** (p. 16).

**Data ranges (Table 1, p. 4, QUOTED), mean (min–max):**

| Variable | Unthinned periods (n = 301) | Thinned periods (n = 380) |
|---|---|---|
| Age (yr) | 21 (7–63) | 22 (11–59) |
| N (ha⁻¹) | 1506 (302–2850) | 987 (342–2160) |
| BA (m² ha⁻¹) | 12.8 (1.0–56.3) | 15.4 (4.4–50.5) |
| H0 (m) | 14.7 (5.0–24.5) | 15.5 (8.3–23.5) |
| SI (H100 at 50 yr, m) | 24.5 (11.7–31.6) | 23.9 (12.9–29.7) |

**Heights by age: not found** as a table or curve. Site index uses the Johansson et al. 2013 curves, which are not reproduced in the paper. Tree heights came from per-plot Näslund (power 3) functions whose parameters are not given.

**Starting BA function (Table 3, p. 10)** for 7–12-yr stands:
ln BA = −7.3193 + 0.2138·age + 0.0643·√N + 0.1555·SI. It explains 64% of variance, RMSE 0.38 m² ha⁻¹.

**BA projection (selected model, Korf BA1).** Equation (Table 2, p. 8): Y = b1·(Y0/b1)^((t0/t1)^b3). Parameters (Table 5, p. 12):
- b1 = **91.3397** (SE 6.2864)
- exponent = **0.7054** (SE 0.0296)
- RMSE 1.569, R² 0.9724

Labelling inconsistency in the source: Table 5 calls the BA1 parameters "b1 b2", but the Table 2 equation uses b1 and b3. Y is total stand basal area.

COMPUTED example: from 5 m² ha⁻¹ at 10 yr, BA at 40 yr = 30.6 m² ha⁻¹. In validation against Finnish trials (p. 12): RMSE 1.42 m² ha⁻¹, MAE 0.22, modelling efficiency about 93%, with growing over-prediction at longer horizons. Parameters of the other five candidate models are in the CSV.

**Volume from BA (Table 4, p. 12):** Vol/BA = −0.4044 + 0.4286·H_top + 0.0085·age (m). R² 0.94, RMSE 0.49 m.

**MAI by site index (Table 6, p. 13).** The simulation starts at 2200 trees ha⁻¹ at age 10, with 3 thinnings each removing 30% of BA and a 2.5% discount rate.

| SI (m) | MAI (m³ ha⁻¹ yr⁻¹) | Rotation (yr) | Thinning / final-felling volume (m³ ha⁻¹) | LEV (EUR ha⁻¹) |
|---|---|---|---|---|
| 22 | 6.0 | 60 | 93 / 269 | 479.6 |
| 25 | 7.9 | 51 | 66 / 337 | 1511.7 |
| 28 | 10.5 | 45 | 80 / 394 | 3103.2 |
| 32 | 12.8 | 31 | 108 / 287 | 5500.8 |

- COMPUTED: (108+287)/31 = 12.74, so MAI = total harvested volume ÷ rotation.
- The exact thinning ages are **not found**; the paper says only that thinnings came earlier at higher SI.
- The realized-gain clone trial (Table 7) reached up to 14 m³ ha⁻¹ yr⁻¹ (p. 15). Genotypes averaged +32% BA and +56% volume at 26 yr over the worst genotype.
- **Mortality function: not found**; the authors say none was included.

---

## 6. Elfving 2010. "Growth modelling in the Heureka system" (99-page report draft, dated 05/02/2010, in English)

**Birch height-growth curve (Appendix 9, p. 58, QUOTED):**
d = β·asi^b2; r = [(H1−d)² + 4·β·H1·A1^b2]^0.5; H2 = (H1+d+r) / [2 + (4·β·A2^b2)/(H1−d+r)]

Birch parameters: **asi = 7, β = 394, b2 = −1.3870.**
- For birch, the curve gives **height above breast height as a function of age at breast height**. For the other species it gives top height versus total age.
- Source data: Eriksson, Johansson & Kiviste 1997; 266 felled top-height trees in 155 stands, 43% *B. pendula* and 57% *B. pubescens*, with "no difference in growth pattern".
- COMPUTED example: H1 = 10 m at A1 = 20 gives H2 = 12.14 m at A2 = 25. The asymptote is 29.6 m.

**Top-height definition (p. 58, QUOTED).** "Top height is defined as the height according to the height curve at the mean diameter of the 100 by diameter largest trees per hectare."

**Is the H–D function for top height named? No (confirmed).** Appendix 9 says only "the height curve". The report's only established-stand height functions are Söderberg (1992) in Appendix 8 (p. 57). Separate birch functions exist for northern and southern Sweden, but **only the northern pine function's coefficients are printed**, and the report never links Appendix 8 to the top-height definition.

**Birch basal-area growth (Appendix 4, 2004 tree-level, Table 1, p. 34).** ID2 = exp(…), where ID2 is the 5-yr increase in d² (cm²). Coefficients:

| Variable | Coefficient |
|---|---|
| constant | 5.9648 |
| ln(d+1) | 1.2217 |
| BAL/(d+1) | −0.3998 |
| ln(a13+20) | −0.9226 |
| ost (standard tree) | 0.4772 |
| ln(G+3) | −0.2090 |
| (own-species BA share)^0.5 | −0.5821 |
| tsum (temperature sum/1000) | −0.5386 |
| 1/(tsum−0.3) | −0.4505 |
| 1/(coast km/10 + 3) | 0.8801 |
| rich (herb/grass type) | 0.3439 |
| fertris | 0.3844 |
| hu0t10 (thinned within 10 yr) | 0.1814 |
| kanteff | 0.2258 |
| lngrel | 0.1321 |

r² = 0.555. "Birch" here means *B. pendula*, *B. pubescens* and ssp. *tortuosa* together; the NFI did not separate them (p. 22). Pp. 16 and 49 say these tree-level functions underestimate growth by about 8–10% and are used only to *distribute* growth. An unpublished, superseded 2001 version (p. 27) is in the CSV.

**Stand-level BA growth, BEY2 (all species, p. 50).** iG5 = exp(0.366 − 0.5842·ln a + 8.374·barrdga − 0.0237·tdveg **− 0.3192·(birch share)² − 10.8034·birch share·exp(−0.01·(tsum−300))** + 0.5002·ln g − 0.00632·g0 + 1.376·sn/(sn+80) + 0.0627·veg − 0.0244·torvveg − 0.0498·moist − 0.1807·wet + 0.0109·sis + 0.0542·dikat + 0.1396·hu0t10 + 0.0567·hu10t30 − 0.06·pine share − 0.03·spruce share). The units are m² ha⁻¹ per 5 yr.

**Maximum density, Söderberg 1986 self-thinning BA (p. 63, scanned table, all species).**
ln G = 2.5225 − 18.612/(T+10) − 765.295/(T+10)² + 0.04798·SI(spruce) + 0.05589·SI(pine) + 6.717e−5·N − 2.864e−9·N² + 0.7204·GP − 0.4879·GP² + **0.1062·LP − 0.2073·LP²**
- LP is the broadleaf share of BA; birch enters only through LP.
- Data: 532 periods on 82 unthinned yield plots; R = 0.87.
- The paired self-thinning mortality function (annual share of BA) is in the CSV.

**Mortality.**
- **Bengtsson 1978, "deciduous" (p. 64)**, in % of volume per year:
  - North: 1.005 − 0.0843·D + 0.00176·D² − 0.000174·A + 0.0000591·A².
  - South: 0.46 − 0.02·D + 0.0046·A.
  - Valid for D = 7–30 cm and A = 30–120 yr. Reduce the output by 40% (north) or 25% (south).
- **Fridman & Ståhl 2001** birch tree-level 5-yr mortality: only a graph (p. 65). Digitised, COMPUTED: p = 0.326, 0.208, 0.135, 0.094, 0.062, 0.044 at dbh 5, 10, 15, 20, 25, 30 cm. Conditions: latitude 60, altitude 300 m, pine stand with BA 20 m² ha⁻¹ and Dg 20 cm. Values below 10 cm are extrapolated.
- **Maximum age (p. 67).** For birch, ln AMAX = 4.6246 − 0.02192·SIS + 0.1742·ln n. Birch data: n = 4040, observed max age 240 yr, max dbh 53 cm. Ageing mortality: p = 1/(1+exp(10 − 12A/AMAX)). COMPUTED: AMAX = 300 yr at SIS 24.

**Ingrowth (Wikberg 2004, pp. 60–62).** The ingrowth limit is 39 mm dbh. The models for occurrence, number and passage probability are shown **only as graphs (coefficients not found)**. The one birch table (Table 4, p. 62, scanned, with "d in mm!" handwritten): ln d of ingrowth trees = 3.5579 + 1.8171·INV5BA + 0.0179·SI, adj. R² 0.174. **INV5BA is not defined in the report.**

**Other birch functions (QUOTED):**
- Brandel volume, v in dm³, log10 form (p. 87):
  - South: −0.89359, 2.27954, −1.18672, 7.07362, −5.45175.
  - North: −0.44224, 2.47580, −1.40854, 5.16863, −3.77147.
- Time to breast height for birch: T13 = 150/SIS (p. 56).
- Young-stand mean height (p. 9) uses SI = H100pine + 1.5 for *B. pendula*. The printed b1 formula refers to itself ("−0.05331·b1²"), probably a typo for b0².
- Birch age at breast height in even-aged stands: function 7 (p. 54).

---

## 7. Karlsson et al. 1998. Natural regeneration of downy and silver birch on abandoned farmland, Sweden (Silva Fennica 32(3): 229–240)

**Context (QUOTED).**
- 29 successfully regenerated, uncleaned stands surveyed in 1991: 15 near Umeå (63°50′N, 5–135 m a.s.l.) and 14 near Växjö (56°53′N, 150–220 m) (pp. 2–3).
- Selection rules: at least 1000 birch stems ha⁻¹, at least 0.1 ha, birch at least 50% of volume.
- **Mostly downy birch:** 92% of birch stems in the north and 84% in the south. Silver birch exceeded 30% of stems in only three stands (p. 4).

**Stem densities, max stand ages and dominant heights: from raster figures only (COMPUTED read-offs; ±5000 stems and ±2 yr):**

| District / previous land use | Birch (all) stems ha⁻¹ | Max stand age (yr) |
|---|---|---|
| Umeå: potato field | ~52 000 (55 000) | ~7 |
| Umeå: ley | ~8 000 (13 000) | ~25 |
| Umeå: stubble | ~13 000 (14 000) | ~25 |
| Umeå: ploughed | ~15 000 (22 000) | ~12 |
| Umeå: top-soil removed | ~25 000 (40 000) | ~19 |
| Växjö: ley | ~5 000 (7 000) | ~43 |
| Växjö: stubble | ~87 000 (148 000) | ~7 |
| Växjö: ploughed | ~28 000 (30 000) | ~8 |
| Växjö: top-soil removed | ~18 000 (48 000) | ~27 |
| Växjö: ploughed + harrowed | ~16 000 (18 000) | ~17 |

Dominant heights in Umeå (Fig. 4) were about 0.9–7.3 m at about 5–23 yr. Dominant height = mean of the 2 largest trees in a 10-m-radius plot. "Stand age" = time since abandonment.

---

## Corrections to the knowledge base

**`birch_knowledge_base.md` does not exist** in `birch-data\` (searched the folder; it holds only `manifest.csv` and `papers/`). So no line-by-line comparison was possible. Instead, these are the places where the full texts contradict or add to the abstract-level metadata in the folder, and to claims likely to have been drawn from abstracts:

1. **"alpha = 4.8" (credited to Aosaar 2016): unsupported.** The paper has no photosynthesis, light, LAI or GPP data, and 4.8 cannot be derived from it (Section 1).
2. **Aosaar** is a single 0.03 ha plot. MAI and CAI include stembark despite being labelled "stemwood". Leaf mass was not estimated for ages 14–17. Roots are partly cited from Varik et al. 2015 and partly from a 21% assumption.
3. **Lintunen 2013**: the PDF is the summary only. The LIGNUM birch parameters (Lintunen et al. 2011, Tables A1–A2) and the corrigendum are **not** in the folder. All birch architecture numbers here are summary tables or digitised model outputs.
4. **Yrttimaa 2025**: the scans are **leaf-off**; "birch" means Betula spp. (989 trees); the stem diameter is not at 1.3 m; and no height or crown-diameter accuracy is reported. The "Birch_BA%" column is actually *all deciduous* trees.
5. **Kalliovirta & Tokola 2005**: there is no crown-width equation. Crown width is a predictor of DBH and age only, and birch species are pooled.
6. **Liziniewicz 2022**: the abstract says "6–10.5 m³ ha⁻¹ yr⁻¹", but Table 6 and the discussion go up to 12.8 (SI 32), and 14 in the clone trial. The Table 6 caption omits SI 32. The BA1 parameter labels are inconsistent (b2 vs b3). There is no height-by-age curve and no mortality.
7. **Elfving 2010**: the birch height curve is fitted to mixed *B. pendula* and *B. pubescens* data and works in **height above breast height vs breast-height age**. The H–D function used for top height is **not named** (confirms the earlier reading). The birch growth functions pool all birch species. The tree-level BA functions underestimate growth by about 8–10%.
8. **Karlsson 1998**: the data are predominantly **downy** birch and are given only in graphs.
9. **Sidecar JSON errors** (checked against the PDF title pages):
   - Yrttimaa 2025: the authors are Yrttimaa, Liikonen, **Erkkilä**, Vastaranta (the JSON lists Junttila, Saarinen, Holopainen).
   - Karlsson 1998: the authors are Karlsson, Albrektson, **Anders** Forsgren, **Lennart Svensson** (the JSON says Urban Forsgren and Rönnberg).
   - Aosaar 2016: the paper has 7 authors, including **Hardo** Becker, Gunnar Morozov and Martin Maddison (the JSON has 5 and says "Hardy").
   - Liziniewicz 2022: the paper has 9 authors (the JSON has 3).
   - Elfving 2010: the PDF is titled "Growth modelling in the Heureka system".
