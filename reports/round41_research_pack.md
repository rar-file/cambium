# Round 41 research pack

Prepared 3 Nov 2026 by Claude (chat review), for the round 41 agent.

**How to use this file.** These are checked leads, not citations. Each source below was looked up on the publisher's or an indexing page, and the Repola numbers were recomputed from the PDF itself. PROTOCOL.md section 3 still applies: open each source yourself before citing it. Anything marked "abstract only" was read from the abstract, not the full paper.

**Do not use** anything from the `birch` "research lab" folder (birch.zip, made by another agent on 3 Nov). It was checked and found to be largely fabricated: 24 of its 69 DOIs do not exist, and its "equation registry" contains invented sample sizes and fit statistics.

---

## 1. Repola 2008: checked against the PDF

Repola, J. 2008. Biomass equations for birch in Finland. *Silva Fennica* 42(4): 605–624. doi:10.14214/sf.236

- **Local copy:** `papers\repola_2008_silva_fennica_236.pdf` (20 pages). Read numbers from it; don't copy it into the repo.
- **Variables:** d = DBH (cm), dS = 2 + 1.25 d (cm), h = height (m), cl = living crown length (m), cr = crown ratio (cl/h). Output in kg dry mass.

### Equations and coefficients

All are natural-log models. To correct for the log-scale bias, add (σu² + σe²)/2 to the intercept (p. 610). Dead branches use the empirical factor c instead.

| Component | Equation | Form | b0 | b1 | b2 | b3 | σu² | σe² | N | Table |
|---|---|---|---|---|---|---|---|---|---|---|
| Stem wood | 7 | b0 + b1·dS/(dS+12) + b2·ln h | −4.879 | 9.651 | 1.012 | | 0.00263 | 0.00544 | 127 | 4 |
| Living branches | 9 | b0 + b1·**dS**/(**dS**+16) + b2·h/(h+10) | −4.152 | 15.874 | −4.407 | | 0.02733 | 0.07662 | 127 | 4 |
| Dead branches | 10 | b0 + b1·**dS**/(**dS**+16), then × c (c = 2.0737) | −8.335 | 12.402 | | | | | 127 | 4 |
| Foliage | 12 | b0 + b1·dS/(dS+2) | −29.566 | 33.372 | | | 0.000 | 0.077 | 21 | 4 |
| Living branches, crown version | A3 | b0 + b1·dS/(dS+12) + b2·h/(h+12) + b3·cl | −5.067 | 14.614 | −5.074 | 0.092 | 0.01508 | 0.05663 | 127 | A1 |
| Foliage, crown version | A6 | b0 + b1·dS/(dS+2) + b2·cr | −20.856 | 22.320 | 2.819 | | 0.0108 | 0.044 | 21 | A1 |

### Findings to know before comparing

1. **Eqs. 9 and 10 use dS, even though the printed equations show d.** Repola's own worked example (Tables 7 and 8, pp. 616–617) only reproduces with dS:

   | Plot | Living branches: Table 8 | with dS | with d | Dead branches: Table 8 | with dS | with d |
   |---|---|---|---|---|---|---|
   | 4_11 | 11.4 kg | 11.5 | 3.4 | 0.7 kg | 0.71 | 0.27 |
   | 357_11 | 25.8 kg | 26.1 | 8.6 | 1.4 kg | 1.38 | 0.58 |

   Using d would understate real branch wood about 3×. The phase 27 agent reached the same conclusion by a different route.

2. **The foliage equations are only valid for DBH 11–26 cm** (p. 617), and rest on 21 trees. Today's stand tree is 28.6 cm over bark at 50 and 31.6 cm at 60, so foliage-vs-Repola at 50–60 is an extrapolation. Prefer the leaf-area targets there, and report Repola foliage at 50–60 as indicative only.

3. **Repola recommends A3 and A6 for crown components** (p. 618): adding the crown variable cuts the between-stand variance.

4. **Like-for-like caveats:**
   - Repola's branch biomass includes bark (p. 608); the model's branches have none.
   - Use DBH over bark (tools/bark.py), as the project already does.
   - About 34% of Repola's sample trees are downy birch (B. pubescens).
   - The data are Finnish, mostly southern, on mineral soils, and include thinning experiments. Stands were aged 11–97 years; trees were 2.5–38 cm DBH.

### Worked values for today's default stand tree

For checking an implementation. Model values are the phase 37 stage b figures, which are the current default (p40_default heights match).

| Age | DBH over bark | H | Crown ratio | Stem wood: model / Eq. 7 | Branches: model / Eq. 9 / A3 | Foliage: Eq. 12 / A6 |
|---|---|---|---|---|---|---|
| 30 | 20.6 cm | 19.97 m | 0.61 | 133.7 / 133.3 kg (1.00) | 3.4 / 20.7 / 22.7 kg (0.16 / 0.15) | 4.96 / 5.53 kg |
| 50 | 28.6 cm | 25.02 m | 0.69 | 326.8 / 300.8 kg (1.09) | 6.1 / 49.4 / 67.8 kg (0.12 / 0.09) | 8.72 / 10.11 kg* |
| 60 | 31.6 cm | 26.11 m | 0.70 | 422.2 / 369.7 kg (1.14) | 6.8 / 64.7 / 90.9 kg (0.11 / 0.07) | 10.08 / 11.46 kg* |

\* Outside the foliage equations' valid DBH range.

These reproduce the stem and branch ratios reported in phases 37–38, so the earlier Repola comparisons were computed correctly.

---

## 2. Shoot dynamics (task 1)

- **Maillette, L. 1982. Structural dynamics of silver birch. I. The fates of buds; II. A matrix model of the bud population.** *Journal of Applied Ecology* 19.
  - DOIs: part II is 10.2307/2403006 (BES Applied Ecology Resources record); part I is probably 10.2307/2403005 (confirm).
  - Abstract only: **three mature, open-grown trees, 4–10 m tall, in North Wales.** Bud fates are related to leaf dynamics, heterophylly, flowering and shoot elongation. Part II is a matrix model of bud production applied to the same three trees.
  - **Caveat:** open-grown, small sample. Compare it with an open-grown run, or label the comparison open-grown versus stand-grown.
  - Paywalled (JSTOR).

- **Lintunen, A. & Kaitaniemi, P. 2010. Responses of crown architecture in *Betula pendula* to competition are dependent on the species of neighbouring trees.** *Trees* 24: 411–424. doi:10.1007/s00468-010-0409-x
  - Abstract only. Stand-grown birch, 3D-digitised shoots and branches, with neighbours within 5 m.
  - Long-shoot "growth vigour" (new long-shoot growth relative to existing branch length) was highest next to other birches.
  - Next to birch or pine, birch invested more in short shoots, densely placed on short branches.
  - Responses depended on tree ontogeny and on position in the crown.
  - **The best lead for stand-grown long/short shoot behaviour.**

- **Kaitaniemi, P. & Lintunen, A. 2010. Neighbor identity and competition influence tree growth in Scots pine, Siberian larch, and silver birch.** *Annals of Forest Science* 67: 604. doi:10.1051/forest/2010017 (free access)
  - Finnish stands, trees 4–35 years old, at 60–63°N.
  - In birch, competition shortened 1-year-old shoots and reduced ring width.
  - Branch number per crown length showed no significant effect.

- **Lintunen, A. 2013. Crown architecture and its role in species interactions in mixed boreal forests.** *Dissertationes Forestales* 165. doi:10.14214/df.165 (open PDF, CC BY-NC-ND)
  - The summary says that under competition birch makes fewer and smaller branches, with a longer leafless part of each branch.
  - It also says that in young birches the main branches' share of total biomass grew at the stem's expense as competition increased. This seems to point the other way from Ilomäki et al. 2003 (section 3), so read both before using either.
  - It includes **Lintunen, Sievänen, Kaitaniemi & Perttunen 2011, "Models of 3D crown structure for Scots pine and silver birch grown in mixed forest", *Can. J. For. Res.* 41: 1779–1794** (corrigendum 42: 2153). That paper is from the LIGNUM group: probably the closest published LIGNUM-style birch crown parameterisation. Worth obtaining.

---

## 3. Allocation: relevant to rings taking ~97% of shoot carbon

- **Ilomäki, S., Nikinmaa, E. & Mäkelä, A. 2003. Crown rise due to competition drives biomass allocation in silver birch.** *Can. J. For. Res.* 33: 2395–2404. doi:10.1139/x03-164
  - Abstract only. 30-year-old planted birch monocultures at three initial spacings.
  - Total branch cross-sectional area was linear in stem cross-sectional area at the crown base (a pipe-model check for stage b).
  - Foliage mass correlated with stem basal area at the crown base.
  - Basal-area-weighted mean branch length was linear in crown length (a branch-reach target candidate).
  - The stem's share of above-ground biomass rose from **80% to 96%** as slenderness (H/D) increased.
  - The authors say the results support functional-balance theory and conflict with the "priority principle" of allocation. Relevant to the ring-first allocation order.
  - **Quick check:** at age 30 the model tree has 133.7 kg stem wood against 3.4 kg branch wood, so the stem share is about 97–98% before foliage is counted. That's above even the most slender trees in Ilomäki's range, while the model tree is only moderately slender. Confirm like for like first (bark in stem and branches, their slenderness range) using the full paper.
  - Note: the fabricated birch.zip cites a garbled version of this paper (wrong co-author, wrong DOI x03-117).

- **Oleksyn, J., Żytkowiak, R., Reich, P.B., Tjoelker, M.G. & Karolewski, P. 2000. Ontogenetic patterns of leaf CO2 exchange, morphology and chemistry in *Betula pendula* trees.** *Trees* 14: 271–281. doi:10.1007/PL00009768
  - Abstract only. It covers leaf development through the season, not leaf size against plant height or age, so **it will not source the juvenile leaf-size rule** (round 40 decision 4).
  - It does report that expanding leaves can run a positive carbon balance before they're fully developed. That supports the round 31 decision that new-shoot leaves earn carbon in their first season.

---

## 4. Crown width or branch reach for stand-grown birch (task 2 leads)

| Lead | What it offers | Access |
|---|---|---|
| Ilomäki et al. 2003 (above) | Mean branch length against crown length, 30-year stand birch | CJFR, paywalled |
| Lintunen et al. 2011 CJFR 41: 1779 | 3D crown structure models for birch in mixed stands | CJFR, paywalled |
| Kalliovirta & Tokola 2005, *Silva Fennica* 39(2), doi:10.14214/sf.386 | Finnish NFI stand trees including birch; predicts DBH from crown width and height | Open, CC BY-SA 4.0 |
| Hemery et al. 2005 | Open-grown only, already INFO | Paywalled |

- Kalliovirta & Tokola predict DBH from crown width, not the other way round. Inverting their regression is not a valid crown-width model. Use it only if the paper reports crown-width data or summary statistics for birch.
- Propose any target under "Proposed targets" for the maintainer's approval (PROTOCOL.md section 2).

---

## 5. Papers for the maintainer to obtain

All paywalled. Try ResearchGate, or email the authors.

1. Maillette 1982, parts I and II (J. Appl. Ecol. 19)
2. Ilomäki, Nikinmaa & Mäkelä 2003 (CJFR 33: 2395)
3. Lintunen et al. 2011 (CJFR 41: 1779, plus its corrigendum)
4. Lintunen & Kaitaniemi 2010 (Trees 24: 411)

The open Lintunen 2013 dissertation PDF (dissertationesforestales.fi/pdf/1949) may summarise items 3 and 4.
