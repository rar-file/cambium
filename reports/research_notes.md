# Research notes for later milestones (campaign)

What research subagents read and reported during M1, kept so later milestones don't need to repeat it. These are subagent reports: each still has to be opened again before it is cited as a target or in a change (PROTOCOL.md section 3), and checker A re-opens them.

## The 11 values the page doesn't support (not changed in M1; inputs to M2 and M3)

The maintainer, 2026-11-06: don't change them in M1. What each page actually says:

| # | Value | In the file | What the page says | Goes to |
|---|---|---|---|---|
| 1 | `resource.apical_dominance` | 0.62 | Palubicki et al. 2009, Sec. 4.2, Fig. 7: "parameter lambda are 0.46, 0.48, 0.50, 0.52, 0.54", synthetic trees. 0.62 is outside that; no birch value exists | M3a |
| 2 | `resource.apical_control_young` | 0.60 | Same page: outside that range. Brown et al. 1967 and Wilson 2000 (abstracts) give the concept, no numbers | M3a |
| 3 | `resource.apical_control_old` | 0.50 | Same page: 0.50 is the "not biased" case, not a value for old birch | M3a |
| 4 | `resource.maintenance_per_internode` | 0.5 | Perttunen 2008 thesis, Eq. 18, p. 23: R_Mi = k_i W_i, by tissue mass, with P and M "first summed up for the whole tree". Not charged per internode as resource flows | M2 |
| 5 | `light.foliage_weight.late_leaf_season_fraction` | 0.5 | Tenkanen et al. 2020, pp. 6, 11: timing only ("elongates through the season and produces new late leaves"; on 5-13 June long-shoot leaves "were not present or were too small"). Miyazawa & Kikuzawa 2004 abstract: timing only, B. grossa. No fraction in either | M2 |
| 6 | `pipe_model.exponent` | 2.5 | Eloy 2011, p. 1: "1.8 < D < 2.3 for a large number of species"; no Betula. The comment's only reason is "the brief asked" | M3 |
| 7 | `pipe_model.huber_path_exponent` | 0.283 | Mencuccini et al. 2019, accepted manuscript p. 19: "Hv tend to remain relatively constant from twig to trunk base". Sellin & Kupper 2006 abstract: "HV increased basipetally within a crown", branch level, no exponent. Not used at the default stem theory stage 2 | M3b |
| 8 | `hydraulics.xylem_conductivity` | 4.0 | Klepsch et al. 2018, Zhang et al. 2018, Gonzalez-Munoz et al. 2018: branch P50 about -1.8 to -2.0 MPa. That's a different trait; no opened page gives a conductivity of 4.0 | M2 |
| 9 | `hydraulics.psi_stomata_open` | -1.0 | Sellin et al. 2014, Table 2 and text: "no threshold level". -1.0 is the branch potential where stomatal conductance is about 0.06 and water-use efficiency turns; it's already 0.086 of 0.145 at leaf -1.26 | M2 |
| 10 | `hydraulics.psi_stomata_closed` | -2.0 | Sellin et al. 2014, Table 2: no closure value. At leaf -1.91 and -2.10 stomatal conductance is 0.046 and 0.060, still 25-32 % of pre-cut | M2 |
| 11 | `hydraulics.psi_turgor_loss` | -2.1 | Hannus et al. 2021, Results and Table 2: mean -2.47 (+-0.03); subsp. pendula -2.32 to -2.94; -2.07 only in subsp. mandshurica | M2 |

## M3a: lateral-bud density control (Sievanen et al. 2018)
- **Source:** Sievanen, Raumonen, Perttunen, Nikinmaa & Kaitaniemi 2018, Ann. Bot. 122:423-434, doi:10.1093/aob/mcy082, full main text at PMC6110348. Supplement (Table S1) not reached.
- **Species:** Scots pine only: 4 trees, ages 8, 16, 25, 33, near Helsinki. The form could transfer by analogy; the parameters can't.
- **Formulation:** Eq. 11, N = 1 + fN(Wf) x fc(af). N is the number of new lateral buds a flushing bud creates. fN is a step function of the mother shoot's needle mass (Fig. 7, p15-p18). af is the needle area density in the bud's perception cone; the cone height is fixed at 0.5 m and its opening angle was optimized.
- **Curve fc:** Fig. 8C, described as "typical": 1 up to af = p19, falling linearly to p21 at af = p20, reaching 0 at af = p22, on an axis of 0-10 m2/m3. The text names only "p19, ..., p21".
- **Values:** no fitted values are printed: "we were not particularly interested in values of the parameters"; identifiability was not tested.
- **Caveat for this model:** BUDVIEW alone scored -11 with the extended Borchert-Honda model (+19 with LIGNUM, +17 with VIGOR; Table 3). EBH+BUDVIEW+BOOST scored 0.0394 against EBH+BOOST 0.0396 (Table 1), about 0.5 %. So the gain on top of EBH+BOOST is small.
- **Consequence:** the parameters would have to be calibrated under the campaign's calibration rule, with published ranges for bounds. None is printed, which is a problem for that rule.

## M3b and M3c: crown
- **Lintunen 2013,** doi:10.14214/df.165, Table 3 p. 23, confirmed: first-order branches 102.0 (7.0) cm long, 5.2 (0.3) per 10 % of crown length, 73 B. pendula next to B. pendula. Ages 4-32 and heights 2-17 m are site means, not tree ranges. Finland 60-63 N, mixed stands, MT sites. Read in full, so usable for a target under pre-approval (b).
- **Ilomaki et al. 2003,** doi:10.1139/x03-164: abstract only, full text blocked. "proportion of stem in aboveground biomass increased from 80% to 96% when the slenderness index increased"; "mean length (weighted by basal area) of branches correlated linearly with crown length". 30-year-old monocultures, three spacings. Not read in full, so it can't become a target under pre-approval (b).
- **LIGNUM form,** J. Perttunen 2008, TKK Report A102, thesis summary, https://sal.aalto.fi/publications/pdf-files/rper09.pdf: Eq. 3 p. 17, P - M = dWn + dWo + dWr, P - M > 0; Eq. 18 p. 23, R_Mi = k_i W_i; Eq. 21 p. 26, P - M = G; Eq. 23 p. 27, G(lambda) = dWn(lambda) + dWo(lambda) + dWr(lambda). Text layer was garbled; symbols decoded, not seen rendered. P and M are "first summed up for the whole tree".
- **Palubicki et al. 2009:** lambda illustrated at 0.46-0.54 only (Sec. 4.2, Fig. 7, p. 4).

## Spread between seeds (node, 30 seeds, default species file, 2026-11-06; `out/bench/node/spread.md`)

Sets the margin for M2's cut rule, and shows how far seed 1 can be from typical.

| Age | Height, mean and SD (m) | Lowest-highest | DBH, mean and SD (cm) | LAI, mean and SD | Leaf area SD | Crown ratio, mean and SD |
|---|---|---|---|---|---|---|
| 15 | 12.14, 0.42 | 10.85-12.87 | 12.04, 0.66 | 1.76, 0.55 | 33 % | 0.51, 0.16 |
| 20 | 14.80, 0.52 | 13.35-15.72 | 14.50, 1.01 | 2.25, 0.62 | 28 % | 0.59, 0.13 |
| 30 | 19.64, 0.70 | 18.35-20.48 | 19.98, 1.08 | 2.55, 0.45 | 18 % | 0.69, 0.10 |
| 50 | 25.20, 0.65 | 23.60-26.64 | 28.09, 1.67 | 3.20, 0.40 | 13 % | 0.73, 0.09 |
| 60 | 26.93, 0.76 | 24.96-28.27 | 30.59, 2.00 | 3.35, 0.37 | 11 % | 0.70, 0.13 |

Seed 1 on this PC: height 26.11 m at 60 and LAI 2.95, both low against these means. The mean height at 60 is above the corrected band's top edge (26.73 m), though seed 1 is inside it. So a verdict on seed 1 alone may not hold for the typical tree. Worth raising with the maintainer: the adoption gate is scored on seed 1.

## The model is chaotic (node, 28 runs, 2026-11-06; `out/bench/node/noise_floor.md`)

Four parameters, each changed by 1 to 7 parts in a million, seed 1. None of the 28 came out the same as the default. Any movement is the model's own chaos, not an effect.

| Age | Height: largest move, SD | DBH | Leaf area | Crown ratio | Diffuse light |
|---|---|---|---|---|---|
| 30 | -6.1 %, 2.7 | +11.2 %, 4.6 | +28.1 %, 9.1 | -21.1 %, 8.9 | +26.4 %, 9.3 |
| 50 | +5.7 %, 2.4 | -11.4 %, 4.7 | -13.4 %, 4.9 | -15.6 %, 6.9 | +15.3 %, 5.4 |
| 60 | +5.6 %, 2.2 | -9.1 %, 3.3 | +11.5 %, 3.8 | -14.9 %, 6.5 | -9.4 %, 4.1 |

On the screen's own measure (largest change in height, DBH, leaf area or carbon at 30, 50, 60), these tiny changes give a median of 10.8 % and at most 28.1 %. An effect in the single-seed screen below that can't be told from noise.

- **Pairing helps only partly:** at 60 the tiny-change spread is close to the seed spread for height (2.2 % against 2.8 %), and smaller for DBH (3.3 against 6.5), leaf area (3.8 against 10.9) and crown ratio (6.5 against 18.1). The 2-standard-error rule measures what's left.
- **The node's seed 1 isn't the PC's seed 1:** height at 60 is 26.51 m against 26.11 m. Rounding differences between chips grow the same way, which is why every comparison stays on one machine.
- **Thread-count rounding moved results far less (0.03 %),** so divergence depends on the size of the disturbance.

## M2a: is there a direct source for alpha? (subagent, 2026-11-06; files in the scratchpad's research_m2a folder)

**Answer: no direct source in anything readable.** No paper read gives seasonal carbon per m2 of fully lit birch leaf, or a full set of Amax, respiration and light response for Nordic B. pendula. So alpha goes down the calibration route. In physical terms 4.8 is 976 g C per m2 of leaf per season in full light (4.8 x 0.305 / 0.0015).

| Quantity | Value | Source | Read level | Species, site |
|---|---|---|---|---|
| Saturated net photosynthesis | Provenance means about 13.3-16.4 umol/m2/s (read by eye from Fig. 3a; text gives 3.12 between 66N and 61N); at 1800 umol photons, 400 ppm | Tenkanen et al. 2020, 10.1093/treephys/tpz124 | Full (accepted manuscript) | B. pendula, 3rd-season plants, watered common garden, Joensuu, summer 2013 |
| Maintenance respiration | ~8 nmol CO2/g/s; about 0.53 umol/m2/s at SLA 15 | Oleksyn et al. 2000, 10.1007/PL00009768 | Abstract | B. pendula |
| Stand light-use efficiency | NPP/APAR 0.93 g/MJ; birch LAI 5.9; 92 % of PAR absorbed | Molchanov 2000, 10.1093/treephys/20.17.1137 | Abstract | B. pendula, 41 years, southern taiga |
| Stand NPP | 7.35, 7.94, 8.47 t C/ha/yr at ages 13, 32, 45 | Varik thesis, Estonian University of Life Sciences, PDF pp. 42-43 | Full for this table | B. pendula, fertile sites, Estonia |
| Global radiation, May-Sep | Norrkoping 2469 MJ/m2 (2180-2664); Stockholm 2442 (2134-2684) | Persson 2000, SMHI RMK 89, PDF pp. 71, 73 | Full | Sweden |
| PAR / global | 0.48 (SD 0.02) | Grimenes & Thue-Hansen 2019, 10.1007/s00704-019-02869-x | Abstract | Norway plus 7 Nordic stations |
| Scaling forms | Rectangular hyperbola f_L = (gamma phi + 1)^-1 (Peltoniemi 2015 p. 157); LIGNUM P = eta_c x I, proportional to intercepted radiation (Perttunen 2008 thesis) | as named | Full for these parts | Pine; no birch values |

**Bounds for a calibration (the subagent's arithmetic; recheck before use):**
- **Leaf route:** gross Amax 13.8-15.5 with SMHI light gives 1110-1390 g C/m2/season, alpha 5.5-6.8. Uses assumptions that aren't from sources (quantum yield 0.05-0.06, curvature 0.7-0.9, 4.57 mol/MJ, a sine-shaped day), with no temperature or leaf-phenology limit, so an upper limit.
- **Stand route, Varik:** alpha 5.15-5.35. **Stand route, Molchanov at Swedish PAR:** alpha 2.7-3.75.
- **Overall:** alpha about 2.7-6.8; 4.8 sits inside. The stand routes aren't independent of the model: their 0.3375 mean light comes from the run at alpha 4.8, and they use the file's CUE 0.45 and SLA 15.
- **What 976 implies:** an effective seasonal Amax of 10.65 umol/m2/s, 69-77 % of the measured midsummer range. Plausible, not derived.
- **Caveat:** the model's carbon is linear in light, as in LIGNUM, while real leaves saturate. A canopy-fitted alpha is an effective slope, not a true full-light leaf value.

**Best sources still unread:** Uddling et al. 2005, Agric. For. Meteorol. 132:115, 10.1016/j.agrformet.2005.07.004: mature B. pendula, southern Sweden, net photosynthesis over 3 years; also Uddling's thesis, "Uptake of Ozone and its Impact on Silver Birch" (University of Gothenburg, GUPEA; bot-blocked, might open in a browser). Riikonen et al. 2005, 10.1093/treephys/25.5.621: seven-year-old trees, Finland.

## M2b: fertility and season length (subagent, 2026-11-06; files in the scratchpad's research_m2b folder)

**Fertility.** The only published Nordic mechanism read that includes silver birch and isn't a carbon multiplier:
- **CROBAS/PREBAS, Minunno et al. 2019,** For. Ecol. Manage. 440:208, doi:10.1016/j.foreco.2019.02.041 (publisher PDF deposited by the University of Helsinki, hdl:10138/310559). Eq. A10, p. 224: W_R = a_Rs W_F (fine-root mass from foliage mass, by site type s). "Site effects are described as an impact on the fine-root to foliage ratio"; "we ignore any other edaphic site effects ... as their role is smaller than that of below-ground allocation". Costs enter through G = (P_T - R_M)/(1 + c), with R_M including m_R W_R (Table A1). Site types OMT, MT, VT, CT.
- **Gaps:** birch a_Rs values aren't in that paper (Table 1 prints "-", cites Helmisaari 2007); the method is in Makela et al. 2016, doi:10.1016/j.foreco.2016.03.059, closed. It uses site type, not site index, and no map from one to the other was seen. So a_R(SI) would be calibrated. That it keeps the Eriksson shape is the subagent's inference, not stated by any source: the cost scales with foliage, which plateaus at canopy closure, while wood respiration keeps growing. Test it.
- **Rejected forms:** 3-PG f_N alone and PRELES beta alone: one multiplier at all ages (the phase 34 objection). Peltoniemi et al. 2015 and Tian et al. 2020, doi:10.1111/gcb.14992, adjust potential LUE that way.
- **Fallback:** 3-PG f_N = 1 - (1 - f_N0)(1 - FR)^n_fN and m = m_0 + (1 - m_0) FR, with FR from site index (Subedi 2015, Virginia Tech thesis, pp. 15-16, 24, Eq. 2.1). All values are for loblolly pine; its endpoints are an assumption; f_N is still multiplicative.
- **Direction supported by:** Makela et al. 2008 New Phytol., doi:10.1111/j.1469-8137.2008.02558.x, abstract: "Carbon allocation to fine roots decreases, allocation to wood increases, and allocation to foliage remains stable" with N. Steady state only.
- **CROBAS crown term, varies with age:** Eq. A1, p. 223: P = (1 - s_1 L_C) P_0 fAPAR, "reduction of photosynthesis with impaired water transport in the crowns"; s_1 prior for birch 0.015-0.06. Not tied to fertility.

**Season.**
- **PRELES f_S,** Peltoniemi et al. 2015, Boreal Env. Res. 20:151, p. 157: X_k is a first-order delay of temperature T_k with delay tau; S_k rises once X_k passes X_0; f_S reaches 1 at S_max. The printed Eq. 9 wasn't readable from the text layer: view journal p. 157 before coding it. Values are Scots pine only (p. 160: X_0 -3.57 to -2.72, S_max 18.5-19.5, tau 12.7-13.1 at Hyytiala). Tian et al. 2020: deciduous forests "needed higher temperatures to start" and longer delays; values not seen. No Betula values.
- **Budburst:** Hakkinen et al. 1998, doi:10.1093/treephys/18.10.707, abstract: thermal time from a fixed calendar date works for mature B. pendula, SE 2.4 d. Parameters not seen.
- **Measured dates, silver birch, Siljansfors 60.53 N, 2010-2020** (Swedish Forest Phenology, doi:10.5878/jbab-cy46, Tree_phases.csv; first day seen per year; subagent's table): bud burst median day 132 (116-141, 11 years); leaves unfolded 140 (122-150); full size 168 (155-181); colours begin 248 (233-263); 50 % yellowed 272 (252-284); 100 % yellowed 279; 50 % fallen 289 (259-296); 100 % fallen 298. Uppsala isn't a station. The model's season is day 130-273.

**Productivity ladder as a fit target (Liziniewicz et al. 2022, Table 6, p. 13).** MAI 6.0, 7.9, 10.5, 12.8 at SI 22, 25, 28, 32. These are model output from their simulation, not measurements: planted improved stock, 2200 trees/ha at age 10, three thinnings of 30 % of basal area, no mortality, rotations 60, 51, 45, 31 years, so not at a common age. SI 32 is outside their data (max 31.6). Their SI is "mean height of the 100 thickest trees per hectare at 50 years", by Johansson et al. 2013 curves, not opened, so it may not be on Eriksson's scale.

**Shape target, computed from the Elfving equation (subagent; recheck before use):**

| SI at 50 | H10 | H20 | H30 | H40 | H50 | H60 | H10/H50 | H60/H50 |
|---|---|---|---|---|---|---|---|---|
| 22 | 6.5 | 12.7 | 17.0 | 19.9 | 22.0 | 23.5 | 0.296 | 1.068 |
| 25 | 8.6 | 15.8 | 20.2 | 23.1 | 25.0 | 26.3 | 0.345 | 1.054 |
| 28 | 11.1 | 19.1 | 23.6 | 26.3 | 28.0 | 29.2 | 0.397 | 1.043 |
| 32 | 14.8 | 23.6 | 28.0 | 30.5 | 32.0 | 33.0 | 0.463 | 1.032 |

The SI 32 / SI 22 height ratio falls with age: about 2.28 at 10, 1.65 at 30, 1.45 at 50, 1.40 at 60. Any fertility term has to reproduce that.

## M2: carbon
- **SLA falls with age:** Rosenvald et al. 2013, 10.1007/s10342-012-0669-7, Fig. 3, as reprinted in the Varik thesis (PDF p. 114): SLA = 15 - 0.075 A, so 14.25 at 10, 12.75 at 30, 11.25 at 50, 10.5 at 60 (subagent's arithmetic). Lintunen 2013 p. 28: mean SLA 13.6 for B. pendula in southern Finland.
- **CUE falls with age and is not one value:** DeLucia et al. 2007 abstract: "CUE decreased with increasing age", 0.23-0.83, lowest for boreal forests. Collalti & Prentice 2019 (accepted manuscript): boreal 0.42 (n 48), temperate 0.48 (n 162), deciduous broadleaf 0.50 +- 0.13. Ryan et al. 1997 abstract: CUE 0.44 for aspen.
- **Inconsistency in the species file:** CUE 0.47 at lines 196 and 208, 0.45 at lines 116 and 201.
- **Liziniewicz 2022 and Aosaar 2016:** see reports/extracts/.
- **Age-10 leaf mass vs age-8 SLA:** Uri 2007's LAI 3.7 and SLA 15.0 imply 2.47 Mg/ha of leaves; Aosaar Table 3 gives 3.5 at age 8. Unresolved at abstract level.

## M4: stands and mortality
- **Dahlgren Lidman et al. 2024,** 10.1007/s11056-023-09971-z, Table 2 p. 163: seedling density per m2, Tierp and Vindeln, both birches pooled: mesic mineral soil 1.7 and 1.3 at year 1, 10.2 and 11.6 at year 2, 9.2 and 17.6 at year 3; mesic control 0-0.2. Heights not found.
- **Fridman & Stahl 2001:** in Elfving 2010 it's a graph only (pp. 64-65), drawn at 60 N, 300 m, no coefficients. Original paper not opened.
- **Bengtsson 1978 (Elfving p. 64):** deciduous. North: 1.005, D -0.0843, D2 0.00176, A -0.000174, A2 0.0000591. South: 0.46, D -0.02, A 0.0046. "reduced with 40 % in northern Sweden and 25 % in southern Sweden"; D 7-30 cm, A 30-120 yr.

## M5: old age and damage
- **Elfving 2010 pp. 67-68:** ln(AMAX) = b0 + b1 SIS + b2 ln(n) + b3 ln(LAT); birch n 4040, max age 240, max dbh 53, b0 4.6246, b1 -0.02192, b2 0.1742; "LAT was not significant and thus excluded", so no latitude term for birch. p = 1/(1 + exp(10 - 12 A/AMAX)). AMAX is evaluated at n = 10 000.
- **Krisans et al. 2022:** no tree table; data "available on request ... not publicly available". Fig. 2A plots individual points (could be digitised). Table 3: BBM_SF -18.7, Vstem 70.76, species -8.29, interaction 50.51, so a birch slope near 121 kN m per m3 (inference, aspen as reference). Trees about 87 years, de-topped before pulling.

## Access limits met
Publisher pages return HTTP 403 to automated fetches. Copies elsewhere aren't allowed (rule above). These stayed at abstract level or below and need a copy from the maintainer or a library:
- Hagemeier & Leuschner 2019, Forests 10:925: **now read from the publisher's HTML,** `reports/hagemeier2019b_publisher_reading.md`. It settles the light target's numbers, and K_PAR from measured transmission against litter LAI, so the double count with `light.woody_shade` looks real
- Ilomaki et al. 2003; Waring et al. 1998; DeLucia et al. 2007; Ryan 1991; Oleksyn et al. 2000; Ryan et al. 1997; Ostonen et al. 2007 (both); Perttunen et al. 1996; Uri et al. 2007; Granier et al. 2000; Barclay et al. 2000; Duursma & Makela 2007; Chen et al. 1997; Miyazawa & Kikuzawa 2004; Brown et al. 1967; Wilson 2000; Macdonald et al. 1984.

## Third-party copies
On the maintainer's decision of 2026-11-06, the JSTOR scan of Borchert & Honda 1984 and the web-archive copies (Hale et al. 2015, a Tokyo thesis abstract, three MDPI pages) were deleted, and rows that relied on them are marked unread in `reports/parameter_audit.csv`. Rule in `CAMPAIGN.md`: no papers from third-party copies (university scans, web archives, mirrors).

## Is the chaos the every-other-year pattern? (INFO for M3; the maintainer's lead, 2026-11-06)

`out/bench/node/noise_cycle.md`: 28 runs, **seed 1 only**, a parameter changed by 1 to 7 parts in a million, every year kept, on the node. The tool's alternation rule and its split into fast and slow parts are its own, for a diagnosis, not from a source.

- **Does divergence start at the first strong alternating year? No, earlier.** It passes 1 % in leaf area at a median of year 6, and 5 % at 6.5. The first strong alternating year comes at 8-14, median 10, and 14 in the default.
- **Do the runs show the same alternation, just out of step? Partly.** From age 20 on, the yearly swing in shoot length agrees with the default in 49 % of years, which is chance. Shifting by up to 3 years gives a median correlation of +0.53, but best-of-seven picks inflate that, and the best shift varies, with -1 the most common (10 of 28).
- **Is the divergence the see-saw? Mostly not.** About a third of the leaf-area divergence is fast (median 33 %, 11-82 %), and a 4-year mean barely narrows the spread: leaf area at 30, 9.06 to 8.25; at 60, 3.76 to 3.67; height at 60, 2.22 to 2.25.
- **So:** averaging over years won't remove the noise; averaging over seeds has to.
- **For M3, seen in the default's yearly table:** whole-tree on-off years. Shoot length made is 0.0 m in years 10 and 19 and 133.9 m in year 24. Leaf area falls from 28.1 to 14.6 m2 between years 18 and 19. Height increment switches between exactly 1.17 m and 0.00 m. The example tree's render looks the same way: a pole with separate tufts (`reports/renders/M1_example_seed5.png`).

## The six top-ranked values nobody had checked (M1, 2026-11-06)

Ranks from the node's 5-seed screen (`out/bench/node/screen5/ranking.csv`). Checked by a research subagent; rows in `reports/parameter_checks.csv`. Not changed in M1; inputs to M2 and M3, like the 11 above. Abstract-level findings could change with the full text.

| Rank | Value | Supported? | What the sources say |
|---|---|---|---|
| 2 | `hydraulics.conductivity_exponent` 0.7 | No | Conduits widen towards the base, in abstracts of Anfodillo 2006 and Olson 2014. No exponent, and they go by path length, the model by radius |
| 7 | `hydraulics.conductivity_reference_radius` 0.02 | No | No page gives a reference radius or a cap at 2 cm |
| 4 | `light.foliage_weight.early_leaves` 2.5 | Partly | Long shoots two early leaves (Kull 2003, B. pendula, Methods; Caesar 1983, B. papyrifera); 2-3 fits short shoots. No mean of 2.5. Clausen & Kozlowski 1965, the one cited, wasn't opened |
| 9 | `resource.reiteration.min_light` 0.8 | No | The comment itself says no published threshold was found |
| 12 | `resource.root_share_max` 0.6 | No | Direction only, in crops (Brouwer 1963). 0.6 is above the comment's own 25-40 %; Aosaar 2016 Table 4 gives 17.8 % below ground for a 10-year-old birch stand, by arithmetic on 2.32 of 13.02 Mg/ha/yr |
| 13 | `pipe_model.wood_volume_per_carbon` 1.2e-06 | No source exists | A unit size: 0.305 g C per unit by arithmetic on wood density 530 kg/m3 and carbon 0.48. The "calibrated" label overstates it: the calibration predates git, was made in rings mode, and can't be reproduced |

**For M2:** alpha's derivation passes through that 0.305 g C per unit, so alpha inherits this choice, and the screen's ranking may partly reflect that coupling (inferred).

**Citation corrections:** Anfodillo 2006 is New Phytol. 169:279, not Tree Physiol. 26:1415 (corrected in the species file's comment). Two Clausen & Kozlowski DOIs in `KNOWN_ISSUES.md` were wrong; only 10.1038/2051030a0 is right (Crossref).

**How they were read:** some through the fetch tool's summary (Kull, Barthelemy & Caraglio, Thornley's page), so recheck those wordings before citing them. PubMed abstracts and PMC XML through NCBI's documented E-utilities, and DOI metadata through Crossref's API, after the PubMed page returned a cookie notice: public, documented routes with default headers, the same content as PubMed and PMC. When a redirect to Nature or Springer was refused as a bot check, the subagent stopped and didn't retry. **Not opened,** and they'd settle these: Lintunen & Kalliokoski 2010, Sellin et al. 2008, Clausen & Kozlowski 1965, Aspelmeier & Leuschner 2006.
