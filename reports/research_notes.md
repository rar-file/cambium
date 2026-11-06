# Research notes for later milestones (campaign)

What research subagents read and reported during M1, kept so later milestones don't need to repeat it. These are subagent reports: each still has to be opened again before it is cited as a target or in a change (PROTOCOL.md section 3), and checker A re-opens them.

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
- Hagemeier & Leuschner 2019, Forests 10:925 (decides the double count and the light target; open access; the maintainer is saving it to `birch-data\`)
- Ilomaki et al. 2003; Waring et al. 1998; DeLucia et al. 2007; Ryan 1991; Oleksyn et al. 2000; Ryan et al. 1997; Ostonen et al. 2007 (both); Perttunen et al. 1996; Uri et al. 2007; Granier et al. 2000; Barclay et al. 2000; Duursma & Makela 2007; Chen et al. 1997; Miyazawa & Kikuzawa 2004; Brown et al. 1967; Wilson 2000; Macdonald et al. 1984.

## Third-party copies
On the maintainer's decision of 2026-11-06, the JSTOR scan of Borchert & Honda 1984 and the web-archive copies (Hale et al. 2015, a Tokyo thesis abstract, three MDPI pages) were deleted, and rows that relied on them are marked unread in `reports/parameter_audit.csv`. Rule in `CAMPAIGN.md`: no papers from third-party copies (university scans, web archives, mirrors).
