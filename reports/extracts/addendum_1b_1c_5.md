# Addendum (4 Nov): tasks 1b, 1c, 5, checked against the PDFs only

**Scope.** This session has the 7 research PDFs, not the model repository. So nothing here touches the species file, `KNOWN_ISSUES.md`, `targets.yaml` or `tools/scorecard.py`. The parts that need the repo are marked **NEEDS REPO** and have not been done.
QUOTED = copied from the paper; COMPUTED = my working, shown.

---

## 1b. Alpha provenance

From the papers: Aosaar et al. 2016 contains no photosynthesis, light, LAI, GPP or radiation data, and no parameter equal to 4.8. The string "4.8" appears only inside 14.8 (N-budget residual) and 11.48 (stemwood N demand), both in Table 4, p. 8. The nearest derivable ratio is tree NPP ÷ foliage mass = 13.02 / 2.81 = **4.63 yr⁻¹** (COMPUTED). Full detail is in `paper_extracts.md` §1.

**NEEDS REPO** (not done):
- `git log -S "4.8"` on the species file.
- Reading `KNOWN_ISSUES.md`.
- Adding `VERIFY` to alpha's comment (comment only).
- Judging how much of the calibration depends on alpha.

---

## 1c. Height target check

### Elfving 2010, p. 58: confirmed (QUOTED, checked against the page image)
> "Those functions concerns top height increment over total age except for birch and spruce. For birch the equation gives height development above breast height as function of age at breast height."

The birch parameters on the same page (Table 1) are asi = 7, beta = 394 and b2 = −1.3870. The equation is:
d = β·asi^b2; r = [(H1−d)² + 4·β·H1·A1^b2]^0.5; H2 = (H1+d+r) / [2 + 4·β·A2^b2/(H1−d+r)].
So H is **height above 1.3 m** and A is **age at breast height**. This is an offset in *both* height and age.

### Elfving's own conversion (p. 59 figure, COMPUTED from the PDF's vector data)
The p. 59 figure plots "Top height, m" against "**Total** age, years" for all species. I digitised the birch curve (dash pattern .42/.14, matched to its legend entry):

| Total age (yr) | 5 | 10 | 20 | 30 | 40 | 50 | 60 | 80 | 100 |
|---|---|---|---|---|---|---|---|---|---|
| Birch top height (m) | 1.31 | 2.74 | 6.71 | 10.44 | 13.53 | 16.07 | 17.98 | 20.83 | 22.74 |

- Every species curve passes 16.07 m at age 50, so the figure uses a common reference site.
- The birch curve is reproduced to **within 0.06 m at every age from 10 to 100** by: total height = H_above-bh(A_total − 5) + 1.3.
- Reading the equation raw as total height at total age misses by up to 0.84 m (7.55 vs 6.71 m at age 20).
- **Conclusion:** Elfving adds 1.3 m and about 5 yr to breast height when plotting birch on a total scale.
- The report's own birch time-to-breast-height rule is T13 = 150/SIS (p. 56, QUOTED), which gives 5 yr at SIS = 30.

### Size of the error if a target reads the equation as total height at total age (COMPUTED)
Corrected = H_ab(A − T13) + 1.3, against naive = H_ab(A). The site curve is set by height above breast height at bh-age 50 (H50ab). T13 = 5 yr.

| H50ab | Diff at age 20 | Diff at 30 | Diff at 40 | Diff at 50 | Diff at 60 |
|---|---|---|---|---|---|
| 15 m | −0.54 | −0.28 | +0.01 | +0.26 | +0.46 |
| 20 m | −1.28 | −0.58 | −0.06 | +0.30 | +0.55 |
| 25 m | −1.87 | −0.67 | +0.03 | +0.43 | +0.68 |

(diff = corrected − naive, in m.)

If the targets were built the naive way, they are **too high before about 40 yr** (up to about 1.9 m at 20 yr) and **slightly too low at 50–60 yr**. The result is sensitive to T13. At H50ab = 20: T13 = 4 gives −0.73 / +0.71 at 20 / 60 yr; T13 = 7 gives −2.41 / +0.22.

**NEEDS REPO** (not done):
- Check how `targets.yaml` and `tools/scorecard.py` build and compare heights.
- Report the corrected 20–60 yr bands from the actual target definitions.
- Draft the `targets.yaml` fix for approval.

The conversion above is the recipe to apply.

---

## 5. Sourced self-thinning, mortality, ingrowth and maximum-age candidates (proposal only, nothing adopted)

**Hynynen 1993: not accessible.** It is not in `birch-data/papers/` and was not downloaded.

### Candidate A: Söderberg (1986) self-thinning basal area (Elfving 2010, App. 11, **p. 63**, scanned table, QUOTED)
ln G = 2.5225 − 18.612/(T+10) − 765.295/(T+10)² + 0.04798·SI(G) + 0.05589·SI(T) + 0.6717×10⁻⁴·N − 0.2864×10⁻⁸·N² + 0.7204·GP − 0.4879·GP² + 0.1062·LP − 0.2073·LP²

| Symbol | Meaning |
|---|---|
| G | basal area, m² ha⁻¹ |
| T | total age, yr |
| SI(G), SI(T) | spruce or pine site index in m (the unused one is set to 0) |
| N | stems ha⁻¹ |
| GP | spruce share of BA |
| LP | broadleaf share of BA |

Fit: 532 periods on 82 unthinned yield plots; R = 0.87, s_f = 0.15. Heureka defines relative density as actual BA ÷ this G and blends mortality functions by it (p. 63).

**Caveats:**
- Birch enters only through LP. Its standard errors are **184.8% (LP) and 97.8% (LP²)**, so the birch effect is not statistically determined.
- Plot species are not stated.
- Pure birch (LP = 1) gives a factor of e^(0.1062−0.2073) = 0.904 (COMPUTED).

Pure-birch values, G in m² ha⁻¹ (COMPUTED; SI(T) = pine site index, used because Heureka indexes birch on pine SI, p. 9):

| SI(T) | T | N = 800 | N = 1500 | N = 3000 |
|---|---|---|---|---|
| 24 | 20 | 10.4 | 10.9 | 11.8 |
| 24 | 40 | 23.0 | 24.0 | 26.1 |
| 24 | 60 | 29.7 | 31.0 | 33.7 |
| 28 | 40 | 28.8 | 30.0 | 32.6 |
| 28 | 60 | 37.2 | 38.8 | 42.1 |

(The full grid is in the CSV.) ln G rises with N up to N = 11 727.

**Cross-check against observed birch (COMPUTED):** at Aosaar's stand (T = 17, N = 2733) the function gives 8.9 / 11.1 / 13.9 m² ha⁻¹ at SI(T) = 24 / 28 / 32. The **observed G was 20.9** (Aosaar Table 3). At T = 13, N = 7670 it gives 6.4–10.0 against 20.1 observed. As a cap, it would badly under-predict young, fertile birch.

### Candidate B: observed self-thinning trajectory (Aosaar et al. 2016, Table 3, **p. 7**, QUOTED)
- Natural silver birch on fertile former farmland; one 0.03 ha plot.
- N fell from 11 633 to 2733 trees ha⁻¹ between ages 8 and 17.
- G plateaued at about 20 m² ha⁻¹ (20.1, 21.3, 20.7, 20.5, 20.9 at ages 13–17).
- Annual losses: 35% of trees at age 15 and 26% at 16 (p. 6).

This is a direct empirical self-thinning target, but it is n = 1 plot.

### Supporting functions (Elfving 2010, QUOTED)

| Function | Page | Equation / values | Notes |
|---|---|---|---|
| Söderberg self-thinning mortality | 63 | annual BA share m = 0.0232 + 0.60949/(T+10) − 12.5903/(T+10)² + 3.317e−4·G − 0.01006·ln G + 1.73e−4·SI(G) + 1.56e−4·SI(T) − 0.0130·GP + 0.0119·GP² + 0.0189·LP − 0.0174·LP² | R 0.40; mean 0.0079 |
| Bengtsson 1978, deciduous (north) | 64 | % of volume per yr = 1.005 − 0.0843·D + 0.00176·D² − 0.000174·A + 0.0000591·A² | D 7–30 cm, A 30–120 yr; reduce by 40% |
| Bengtsson 1978, deciduous (south) | 64 | 0.46 − 0.02·D + 0.0046·A | reduce by 25% |
| Fridman & Ståhl 2001, birch tree mortality | 65 | graph only; p(5 yr) = 0.326, 0.208, 0.135, 0.094, 0.062, 0.044 at dbh 5, 10, 15, 20, 25, 30 cm (COMPUTED, digitised) | lat 60, alt 300, pine stand with BA 20; <10 cm extrapolated |
| Maximum age, birch | 67–68 | ln AMAX = 4.6246 − 0.02192·SIS + 0.1742·ln n (use n = 10 000); p(dead by age A) = 1/(1+exp(10 − 12·A/AMAX)) | AMAX ≈ 300 yr at SIS 24 (COMPUTED) |
| Ingrowth diameter, birch (Wikberg 2004) | 62 | ln d (mm) = 3.5579 + 1.8171·INV5BA + 0.0179·SI | INV5BA not defined; occurrence and passage models are graphs only (pp. 60–61) |

**Not a candidate:** Liziniewicz 2022's Korf asymptote (b1 = 91.34 m² ha⁻¹) describes total BA production in *thinned* plantations, so it is not a self-thinning limit.
