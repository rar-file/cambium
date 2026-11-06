# Hagemeier & Leuschner 2019b: reading from the publisher's page

Read by Claude (chat) on 6 Nov 2026 for the maintainer (answers QUESTIONS.md Q6 in part).

**How it was read:** MDPI's own article pages, the abstract page and the full-text HTML at https://www.mdpi.com/1999-4907/10/10/925 and https://www.mdpi.com/1999-4907/10/10/925/htm. The fetch tool passes pages through a summarising step. Treat the quotes below as verbatim and the table values as transcribed. When the maintainer saves the PDF to `birch-data\09_light\`, check the table values against it. **No third-party copy was used.**

## Citation

Hagemeier, M. & Leuschner, C. (2019). Leaf and crown optical properties of five early-, mid- and late-successional temperate tree species and their relation to sapling light demand. *Forests* 10(10): 925. doi:10.3390/f10100925. Open access; the page metadata links CC BY (the version shown was 3.0).

## The light target (Results 3.2, Figure 5)

> "A median transmission of 14.8% was recorded in the B. pendula stands, with individual values varying between 6.4% and 19.8%."

- **Method (Methods 2.3):** paired quantum sensors, one in the open or above the canopy and one on the forest floor, at 110–241 points per stand. Readings were taken around noon (11:00–14:00), "exclusively on days with overcast sky", so they measure **diffuse light**. The forest-floor sensor was "attached to the end of a 2 m-long pole with a cardanic mounting". The sensor's height above the ground isn't stated.
- **For the model:** this matches the target already in targets.yaml (6.4–19.8%, median 14.8%), and the model's `subcanopy_diffuse_light_pct` is the like-for-like output (diffuse, below the canopy). The measurement height isn't given, so state the model's sampling height in the scorecard.

## Table 5 (means of the two birch stands)

| Species | LAI (m²/m²) | LAD sun crown (m²/m³) | LAD shade crown (m²/m³) | K_PAR | Clumping Ω |
|---|---|---|---|---|---|
| *Betula pendula* | 4.6 | 3.2 | 0.3 | 0.37 | 0.42 |

- The Results text gives Ω = 0.41 for *B. pendula*, while Table 5 gives 0.42.
- LAI comes from litter collection in 1998 and 1999 (Methods 2.2).
- K_PAR comes from I = I₀·e^(−K·LAI), using incident and transmitted PAR (Methods 2.3).
- **Check:** e^(−0.37 × 4.6) = 18.2% light, inside the band. To reach the median of 14.8%, LAI would need to be about 5.2 at K = 0.37. The paper's K is a two-stand mean, so expect some slack between the two.

## Table 2 (birch stands)

| Stand | Age (yr) | Basal area (m²/ha) | Stems/ha | Mean DBH (cm) | Mean height (m) | Birch share of stems |
|---|---|---|---|---|---|---|
| 1 | 45 | 25.2 | 880 | 19 ± 6 | 20 ± 3 | 85% |
| 2 | 67 | 28.5 | 420 | 25 ± 3 | 25 ± 3 | 98% |

**For the model (INFO, not targets):**
- Basal area is 25–29 m²/ha at 45–67 years. That's another real-stand figure well below the model's natural plot (52–62 m²/ha).
- Mean height is 20 m at 45 years (stand 1). The model's 20-seed stand tree is about 24 m at that age. That's a mean height against a single stand tree, so the comparison isn't like for like, but it points the same way as the height FAILs.

## Also in the paper (INFO)
- Minimum light demand of *B. pendula* saplings 50–90 cm tall: 21.0% relative light (Figure 6). Relevant to regeneration under a canopy.
- Minimum light demand of the lowest shade leaves: 21.0% for *B. pendula*. A possible check on how far down the crown leaves can survive (crown base, self-pruning).
