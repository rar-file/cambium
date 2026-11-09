# Known issues

## Phase 31: continuous replacement-leader tube, snow-buckling check, replacement-leader diagnosis, wind rule, and leaves diagnosis

**1. Continuous trunk tube across leader replacements** (`treegen/mesh.py`, commit `e6aab7a`).
- Where a browsed leader died and a lateral replacement leader took over (`tree.relay`), the mesher now splices the parent stem and the winning replacement leader into one continuous tube instead of capping the dead leader stub with a cone and starting the replacement leader with a branch collar.
- The white cone caps on browsed stems in the natural plot render are gone; slight narrowing remains at a couple of relay joins.

**2. Replacement-leader knees after moose browsing (diagnosis only; no model change).**
- **Primary bending exists for newly elongating leader internodes:** In `_grow_shoots` (`treegen/growth.py` lines 1334–1352), any axis in `self.leader_axes` gets `gsa = 0.0` (vertical), `eta = gravitropism[0] = 2.0 / m`, and is exempted from `pendulous_factor`.
- **Why the 0.3–0.71 m sideways knee and tree 73's loop still form:**
  1. **Bite depth removes the entire previous annual shoot (`birth >= t - 1`):** `_leader_damage(t)` (`treegen/growth.py` lines 270–297) kills 100% of the leader's `t - 1` shoot (0.7–1.1 m long), placing `base` at the top of 2-year-old wood (`birth == t - 2`). On 2-year-old wood, the upper lateral buds already broke in year `t - 1` (`lc = T.lat_child[c] >= 0`) while the leader was still alive. Thus in 34 of 34 leader replacements across the 29 browsed trees in `p26_nat`, the promoted replacement axis spent its actual first growing season (`t - 1`) elongating 0.50–0.86 m sideways (`dx_y1` median 0.28 m, max 0.71 m in tree 20 and 0.70 m in tree 73) as a plagiotropic `order = 1` branch (`gsa = 43°`, with `pendulous_factor` reducing primary gravitropism to ~0.02 /m and first-year self-weight bending it to 45–88°). When promoted in year `t`, that 1-year-old shoot is already woody (`birth == t - 1`): primary upward growth only starts at its distal tip (already 0.3–0.7 m off-axis), while the woody base can only lift at the secondary reaction-wood rate $C_{\text{rw}}\Delta r / r^2 \approx 0.29\text{ m}^{-1}\text{ yr}^{-1}$ (Alméras & Fournier 2009; Coutand et al. 2007). In tree 73, slow secondary lifting at the horizontal base rotates the already-vertical second-year extension inward past vertical, forming a loop.
  2. **Even a newly breaking bud (`_relay_buds`) turns too slowly in its first season:** It starts at `branch_angle_deg[0] = 43°` (`T.lat_dir`) and turns toward vertical at the mature stem's $\eta_0 = 2.0\text{ m}^{-1}$ (convergence length $L_c = 1/\eta_0 = 0.5\text{ m}$), running $(1 - \cos 43^\circ)/\eta_0 \approx 0.14\text{--}0.27\text{ m}$ sideways over its first 0.5 m before becoming vertical, and then takes full unbuttressed first-year self-weight bending (`r_prev = 0`).
- **Sources and proposed fix (not built yet):**
  - Moose winter browsing on *Betula pendula* clips the distal part of the current annual leader at a mean bite diameter of 2.2–4.0 mm (Danell, Huss-Danell & Bergström 1985, J. Appl. Ecol. 22:883; Bergström & Danell 1987, J. Appl. Ecol. 24:803; Shipley et al. 1998, Oecologia 114:421), removing ~20–35 cm rather than the entire 0.8–1.1 m shoot down to 2-year-old wood. Thus the replacement leader breaks in spring `t` from an axillary bud on the remaining `t - 1` shoot (`_relay_buds`), not a 1-year-old lateral branch.
  - Primary gravitropic reorientation of a released sub-terminal bud occurs within the primary growth zone ($L_{\text{gz}} \approx 3\text{--}10\text{ cm}$) with convergence length $L_c \approx 2\text{--}5\text{ cm}$, i.e. $\eta = 1/L_c \approx 20\text{--}50\text{ m}^{-1}$ (Bastien et al. 2013, PNAS 110:755), curving to vertical within the first 5–10 cm of its first flush (Chaar et al. 1997, Ann. Sci. For. 54:405; Wilson 2000, Am. J. Bot. 87:601).

**3. Offline snow-buckling check on the natural plot** (`tools/snow_buckling.py`, `out/bench/p26_nat`).
- Rayleigh cantilever buckling check (E = 10.7 GPa, fresh density 900 kg m⁻³, own winter weight plus the Finnish mean crown snow load of 5.35 kg m⁻², Lehtonen et al. 2014, Silva Fennica 48:1120) evaluated at the stored 5-year keyframes on the logged natural plot:

| plot year | trees alive (logged) | /ha logged | buckled by now under own weight | /ha left | buckled with mean snow load | /ha left |
|---|---|---|---|---|---|---|
| 20 | 98 | 1764 | 0 | 1764 | 0 | 1764 |
| 30 | 97 | 1746 | 0 | 1746 | 0 | 1746 |
| 40 | 96 | 1728 | 0 | 1728 | 2 | 1692 |
| 45 | 96 | 1728 | 1 | 1710 | 5 | 1638 |
| 50 | 95 | 1710 | 4 | 1638 | 10 | 1530 |
| 60 | 95 | 1710 | 12 | 1494 | 23 | 1296 |

- First snow-buckling failures occur at plot years 33–46 on slender trees with wood H/D 216–255 (e.g. tree 95 at year 33, H 13.8 m, DBH 5.8 cm; tree 76 at year 38, H 18.2 m, DBH 7.5 cm).
- Snow buckling alone brings stand density to 1638/ha at 45 (1530/ha at 50, 1296/ha at 60), far short of Hagemeier & Leuschner's 880/ha at 45.
- Nykänen et al. 1997 (Silva Fennica 31:193): stem breakage is the most common snow damage overall, small slender trees (high H/D) are most prone to bending, and birch tends to bend permanently under wet snow rather than snap.

**4. ForestGALES wind-load rule** (`species/betula_pendula.yaml`, `treegen/growth.py`, `treegen/plot.py`, commit `8705f92`; `enabled: false` by default).
- **Licence:** The `fgr` R package (Locatelli, Gardiner, Hale & Nicoll 2020, Forest Research) is licensed under GPLv3 with the Commons Clause v1.0, forbidding commercial use. No code from `fgr` was copied or translated; implemented strictly from the published equations and cited parameter values in Gardiner et al. 1997 (Forestry 70:233), Gardiner et al. 2000 (Ecol. Model. 129:1), Raupach 1994 (Boundary-Layer Meteorol. 71:211), Vollsinger et al. 2005 (Can. J. For. Res. 35:1238), Hale et al. 2015 (Environ. Model. Softw. 68:27), and Locatelli et al. 2017 (Environ. Model. Softw. 87:84).
- **Parameters:** ForestGALES birch (BI) green MOR 63 MPa, knot factor 1.0, streamlining $C = 1.9627$, $N = 0.881$ (capped at $u_h = 20\text{ m s}^{-1}$). Target outer-fibre wind bending stress $\sigma_{\text{target}} = 63 / 3.5 = 18.0\text{ MPa}$ (safety factor 3.5 against green MOR; Niklas & Spatz 2000, Trees 14:230; Mattheck & Kubler 1995).
- **Wind speeds tested on the seed-1 stand tree:**
  1. Frequent strong synoptic wind `12.0 m/s`: trees acclimate radial growth (thigmomorphogenesis) to recurring strong synoptic winds rather than the 50-year storm (Bonnesoeur et al. 2016, New Phytol. 210:850; Gardiner, Berry & Moulia 2016, Plant Sci. 245:94), and stem taper conforms to uniform bending stress at canopy-top winds of 10–12 m/s (Morgan & Cannell 1994, Tree Physiol. 14:49; ~98–99th percentile synoptic wind on the Swedish west coast, SMHI). Sizing for 12 m/s at 18 MPa ($SF = 3.5$) also provides a breaking safety factor of ~1.5 against a 25 m/s 50-year storm at 63 MPa.
  2. 50-year design wind `25.0 m/s`: Göteborg / west coast 10 m fundamental basic wind velocity (Boverket EKS / SS-EN 1991-1-4 National Annex; VERIFY for Lysekil).
- **Seed-1 stand tree results (each ring is the larger of the pipe need and the wind need, paid from the same LIGNUM carbon pool):**

| run | age | H (m) | DBH wood / over bark (cm) | H/D over bark | d/DBH at 0.1 / 0.3 / 0.5 / 0.7 / 0.9 H | Hansen 2023 taper | form factor (model / Hansen) | stem wood / Repola | branches / Repola | shoot C share (5-yr mean) | buckling: own / +5.35 / +30 snow |
|---|---|---|---|---|---|---|---|---|---|---|---|
| baseline (no wind) | 30 | 18.7 | 18.9 / 20.7 | 90 | 0.99 / 0.90 / 0.71 / 0.49 / 0.09 | 0.95 / 0.78 / 0.63 / 0.40 / 0.13 | 0.51 / 0.44 | 1.13 (142/126 kg) | 0.15 (3.3/22.5 kg) | 2.1% (2.1%) | 12.7 / 10.8 / 6.3 |
| baseline (no wind) | 50 | 24.2 | 25.0 / 27.4 | 88 | 0.99 / 0.89 / 0.71 / 0.50 / 0.08 | 0.92 / 0.75 / 0.60 / 0.39 / 0.12 | 0.51 / 0.41 | 1.18 (320/270 kg) | 0.18 (8.2/44.3 kg) | 4.1% (3.9%) | 9.4 / 7.6 / 4.1 |
| baseline (no wind) | 60 | 25.8 | 26.7 / 29.2 | 88 | 0.99 / 0.90 / 0.76 / 0.55 / 0.18 | 0.91 / 0.75 / 0.60 / 0.38 / 0.12 | 0.54 / 0.40 | 1.28 (411/322 kg) | 0.22 (11.1/51.6 kg) | 2.4% (3.4%) | 7.6 / 6.0 / 3.0 |
| frequent wind (12 m/s) | 30 | 19.1 | 19.5 / 21.3 | 90 | 0.98 / 0.83 / 0.67 / 0.39 / 0.09 | 0.95 / 0.78 / 0.62 / 0.40 / 0.13 | 0.46 / 0.44 | 1.01 (138/136 kg) | 0.20 (4.9/24.4 kg) | 5.1% (4.2%) | 13.6 / 11.2 / 6.2 |
| frequent wind (12 m/s) | 50 | 24.6 | 28.2 / 30.9 | 79 | 0.97 / 0.82 / 0.63 / 0.38 / 0.13 | 0.91 / 0.74 / 0.59 / 0.37 / 0.11 | 0.44 / 0.40 | 1.06 (355/335 kg) | 0.16 (10.3/64.0 kg) | 3.0% (2.7%) | 13.0 / 11.0 / 6.4 |
| frequent wind (12 m/s) | 60 | 26.2 | 29.3 / 32.1 | 81 | 0.97 / 0.85 / 0.71 / 0.51 / 0.18 | 0.91 / 0.74 / 0.59 / 0.37 / 0.11 | 0.50 / 0.39 | 1.23 (468/381 kg) | 0.22 (14.8/68.0 kg) | 2.2% (3.1%) | 8.1 / 6.5 / 3.4 |
| 50-yr wind (25 m/s) | 30 | 14.2 | 23.8 / 26.1 | 54 | 0.99 / 0.56 / 0.32 / 0.22 / 0.07 | 0.98 / 0.77 / 0.58 / 0.35 / 0.09 | 0.30 / 0.43 | 0.68 (99/146 kg) | 0.25 (16.4/64.8 kg) | 0.2% (0.9%) | 117.6 / 96.8 / 53.4 |
| 50-yr wind (25 m/s) | 50 | 17.6 | 32.2 / 35.4 | 50 | 0.97 / 0.66 / 0.56 / 0.45 / 0.19 | 0.95 / 0.73 / 0.54 / 0.32 / 0.08 | 0.39 / 0.39 | 1.01 (298/295 kg) | 0.42 (54.8/131.9 kg) | 1.7% (1.4%) | 36.4 / 33.8 / 25.5 |
| 50-yr wind (25 m/s) | 60 | 18.5 | 35.6 / 39.0 | 47 | 0.97 / 0.76 / 0.65 / 0.52 / 0.15 | 0.94 / 0.71 / 0.53 / 0.30 / 0.08 | 0.45 / 0.38 | 1.23 (442/359 kg) | 0.41 (68.6/165.9 kg) | 0.9% (1.2%) | 31.4 / 28.2 / 19.3 |

- **Why the mid-stem (`0.3–0.7 H`) matches Hansen at 30–50 under 12 m/s wind (`0.82 / 0.63 / 0.38` vs `0.74 / 0.59 / 0.37` at age 50), but thickens between 50 and 60 (`0.85 / 0.71 / 0.51`):**
  1. **Double-counting between `huber_path_exponent` (`c = 0.283`) and sapwood turnover (`0.014/yr`):** `c = 0.283` was calibrated without wind so that conducting sapwood + accumulated heartwood matched DBH at 1.3 m. With wind on, the wind rings grown before age 50 turn into non-conducting heartwood at `1.4%/yr`, while the pipe rule still demands `hv(l) * LA` of *conducting* sapwood on top of that heartwood. Once height growth slows after age 50, `a_wind` at the base barely grows (`DBH` +1.1 cm from 50 to 60), whereas in the mid/upper stem (`0.5–0.9 H`) `hv(l) * LA + old_wood` catches up to `a_wind` and forces ongoing sapwood-replacement rings.
  2. **Top-heavy leaf profile and no butt swell:** 82% of the model's leaf area at age 60 sits in `0.7–1.0 H`, and Hansen's DBH includes ~4–5% butt swell at 1.3 m that the model adds only in the mesher.

**5. Leaves diagnosis (no model change).**
- **New-shoot leaf lag in young trees (`out/bench/p29_path/1_stand`):**
  - **Source:** Silver birch is heterophyllous (Maillette 1982, J. Appl. Ecol. 19:203; Clausen & Kozlowski 1965, Can. J. Bot. 43:305): each extending long shoot bears 2–3 early (preformed) leaves at its base (`early_leaves: 2.5`) that flush in spring at budburst with the short shoots (full season), plus 1 late (neoformed) leaf per metamer (`new_leaf: 1.0`) that unfolds sequentially during June–July (~half season).
  - **Model gap:** `light_sources()` and photosynthesis in `step()` (`treegen/growth.py` lines 521, 644) run before `_grow_shoots` (line 884), so leaves on year-$t$ shoots are paid for in year $t$ and counted in `stats["leaf_area_m2"]`, but earn zero carbon until year $t + 1$.
  - **Carbon lost (`early + 0.5 * late` vs full `early + late`):**

| age | H (m) | DBH wood (cm) | photosynthetic LA (m²) | end-of-season LA (m²) | new-shoot LA: early / late (m²) | end / photo LA | fixed C actual | est. C lost: early + 0.5×late (full) | % potential C lost |
|---|---|---|---|---|---|---|---|---|---|
| 2 | 0.63 | 0.0 | 0.01 | 0.10 | 0.03 / 0.06 | 7.12× | 36 | 143 (222) | 80% (86%) |
| 4 | 2.98 | 1.0 | 0.71 | 2.92 | 0.62 / 1.59 | 4.10× | 1,505 | 2,987 (4,661) | 66% (76%) |
| 6 | 5.33 | 4.7 | 4.83 | 12.99 | 3.19 / 4.97 | 2.69× | 8,421 | 9,896 (14,225) | 54% (63%) |
| 10 | 9.62 | 7.5 | 9.59 | 13.61 | 1.89 / 2.13 | 1.42× | 12,468 | 3,849 (5,234) | 24% (30%) |
| 15 | 12.82 | 10.1 | 16.36 | 21.14 | 2.32 / 2.46 | 1.29× | 23,026 | 5,001 (6,734) | 18% (23%) |
| 30 | 18.69 | 18.9 | 54.06 | 52.16 | 0.00 / 0.00 | 0.96× | 55,288 | 0 (0) | 0% |
| 50 | 24.22 | 25.0 | 73.39 | 73.31 | 0.00 / 0.00 | 1.00× | 68,984 | 0 (0) | 0% |
| 60 | 25.79 | 26.7 | 75.11 | 76.16 | 0.74 / 0.31 | 1.01× | 73,394 | 874 (1,028) | 1% |

- **LAI and light at 2–5 m height (`out/bench/p26_nat` and `out/bench/p29_path/1_stand`) vs. Hagemeier & Leuschner 2019 (Forests 10(3):265 and Forests 10(10):925):**
  - Hagemeier & Leuschner 2019 measured mature *B. pendula* stands (age ~45–65) with mean LAI = 4.59 m² m⁻² (two stands: 3.6 and 5.4), $k = 0.37$, and under-canopy light 12.6% PAR (10.2–15.0%; pure leaf Beer-Lambert $\exp(-0.37 \times 4.59) = 18.3\%$, plus ~5% wood shading).

| stand | age | stems/ha | total LAI | LAI in 2–5 m | Beer-Lambert light at 5 m / 2 m ($k=0.37$) | 3D voxel light at 5 m / 3.5 m / 2 m | bottom-Q vs top-Q height (m) | bottom-Q vs top-Q bud light |
|---|---|---|---|---|---|---|---|---|
| natural plot (`p26_nat`) | 30 | 1746 | 4.12 | 0.059 | 0.22 / 0.22 | 0.23 / 0.23 / 0.23 (p10–p90 0.22–0.24) | 16.9 vs 19.3 (0.88×) | 0.33 vs 0.36 |
| natural plot (`p26_nat`) | 45 | 1728 | 4.13 | 0.017 | 0.22 / 0.22 | 0.23 / 0.23 / 0.23 (0.23–0.24) | 22.0 vs 23.9 (0.92×) | 0.34 vs 0.36 |
| natural plot (`p26_nat`) | 50 | 1710 | 3.98 | 0.014 | 0.23 / 0.23 | 0.25 / 0.25 / 0.25 (0.24–0.26) | 23.5 vs 25.1 (0.94×) | 0.33 vs 0.35 |
| natural plot (`p26_nat`) | 60 | 1710 | 3.99 | 0.009 | 0.23 / 0.23 | 0.25 / 0.25 / 0.25 (0.24–0.26) | 26.0 vs 27.0 (0.97×) | 0.36 vs 0.35 |
| single stand tree (`1_stand`) | 30 | 450 | 2.35 | 0.081 | 0.43 / 0.42 | ~0.42 | 18.7 | – |
| single stand tree (`1_stand`) | 45 | 450 | 3.17 | 0.089 | 0.32 / 0.31 | ~0.31 | 23.2 | – |
| single stand tree (`1_stand`) | 50 | 450 | 3.30 | 0.078 | 0.30 / 0.30 | ~0.30 | 24.2 | – |
| single stand tree (`1_stand`) | 60 | 450 | 3.43 | 0.056 | 0.29 / 0.28 | ~0.28 | 25.8 | – |

  - **Why lower limbs never shed and suppressed trees never get shaded:** Branch shedding requires bud light `< 0.21` (`shedding.light_per_leaf_threshold`) and short-shoot death requires `< 0.20`. With $k = 0.37$ and no wood shading, light at 2–5 m stays at 0.23–0.25 in the natural plot (`LAI = 3.98–4.13`, just below the $\ln(1/0.21)/0.37 = 4.22$ LAI needed to cross 21%) and 0.28–0.43 in the thinned stand tree (`LAI = 2.35–3.43`, because each tree has only 43–56% of Repola's foliage). Moreover, no tree in `p26_nat` has its crown at 2–5 m: without a mechanical wind cost on stem height, the bottom DBH quartile grew right into the upper canopy (`0.88–0.97×` top-quartile height) and receives `0.33–0.36` bud light.

**6. Citation verification (commit `f4cc832`).**
- Verified DOIs and sources for all 15 citations introduced in recent phases. Unconfirmed or extrapolated values marked with `VERIFY`:

| Citation | What we use it for | DOI / Source | Confirmed |
|---|---|---|---|
| Danell et al. 1985 (J. Appl. Ecol. 22:883) | Moose browsing bite diameter & biomass removal | `10.2307/2937382` | Yes |
| Bergström & Danell 1987 (J. Appl. Ecol. 24:803) | Moose bite diameter distribution in Betula | `10.2307/2403867` | Yes |
| Shipley et al. 1998 (Oecologia 114:421) | Ungulate cropping bite diameter mechanics | `10.1007/s004420050478` | Yes |
| Bergqvist et al. 2014 (Forestry 87:419) | Moose browsing height preference (0.3–3.0 m) | `10.1093/forestry/cpu007` | Yes |
| Mathisen et al. 2017 (BMC Ecology 17:12) | Birch mean leader bite diameter (2.16 mm) | `10.1186/s12898-017-0122-3` | Yes |
| Chaar et al. 1997 (Ann. For. Sci. 54:405) | Leader replacement & apical control release | `10.1051/forest:19970503` | VERIFY (Quercus/Pinus) |
| Wilson 2000 (Am. J. Bot. 87:601) | Primary bending & apical control mechanisms | `10.2307/2656989` | Yes |
| Bastien et al. 2013 (PNAS 110:755) | Universal stem gravitropic reorientation (L_gz, L_c) | `10.1073/pnas.1214301109` | Yes |
| Morgan & Cannell 1994 (Tree Physiol. 14:49) | Stem uniform bending stress under wind | `10.1093/treephys/14.1.49` | Yes |
| Niklas & Spatz 2000 (Trees 14:230) | Stem safety factor vs size (challenges constant stress) | `10.1007/s004680000078` | Yes |
| Bonnesoeur et al. 2016 (New Phytol. 210:850) | Thigmomorphogenesis acclimates to frequent wind | `10.1111/nph.13836` | Yes |
| Clausen & Kozlowski 1965 (Can. J. Bot. 43:305) | Heterophylly in birch (early vs late leaves) | `10.1139/b65-035` | Yes |
| Maillette 1982 (J. Appl. Ecol. 19:203) | Structural dynamics of birch bud populations | `10.2307/2403005` | Yes |
| Tenkanen et al. 2020 (Tree Physiol. 40:486) | Late leaf emergence and season fraction (0.5) | `10.1093/treephys/tpz124` | VERIFY (Alnus/deciduous) |
| SMHI west coast wind data / Boverket EKS | West coast synoptic & design wind (12 & 25 m/s) | SMHI Open Data / EKS 11 | VERIFY (Lysekil local) |

**7. Wind rule analysis and load sharing (rule kept off).**
- **Sourced wind speed and target stress:** Morgan & Cannell 1994 and Bonnesoeur et al. 2016 show stem allometry acclimates to frequent synoptic wind speeds (2.5–10 m/s), producing uniform bending stress. Standard synoptic wind is 5.0 m/s (or coastal frequent strong 12 m/s). ForestGALES (Hale et al. 2015) gives green MOR = 63 MPa for birch; working outer-fibre stress of 18.0 MPa assumes a constant safety factor of 3.5, though Niklas & Spatz 2000 show safety factors vary with tree ontogeny (`VERIFY`).
- **Canopy wind attenuation and load sharing:** Suppressed trees inside a canopy are sheltered. Raupach 1994 and Hale et al. 2012 establish that wind speed attenuates exponentially through the canopy profile: $u(z) = u(H) \exp(-\alpha (1 - z/H))$, with attenuation coefficient $\alpha \approx 2.0\text{--}3.0$. A suppressed tree of height $h < H$ feels winds attenuated by $\exp(-\alpha(1 - h/H))$, drastically reducing bending moment. The current `_wind_load_scale` does not yet model intra-canopy vertical decay.
- **Refitting $c$ postponed:** Refitting $c$ is deferred until foliage, light, and stand thinning are stabilized.

**8. New-shoot leaf accounting (`treegen/growth.py`, `species/betula_pendula.yaml`, commit `45d13c5`).**
- Early leaves (2.5 preformed leaves at budburst) are credited for the full season ($1.0$) in `light_sources`.
- Late leaves (neoformed leaves on extending long shoots) are credited in `_growth_factor` for a sourced season fraction $f_{\text{late}} = 0.5$ (`late_leaf_season_fraction`, Tenkanen et al. 2020, `VERIFY`), paying their own leaf maintenance and fine root carbon.
- **Seed-1 stand tree results (ages 10, 30, 50, 60):**

| age | H (m) | DBH wood (cm) | DBH over bark (cm) | H/D over bark | LA (m²) | Model foliage (kg) | Repola Eq. 12 (kg) | Ratio |
|---|---|---|---|---|---|---|---|---|
| 10 | 9.18 | 9.17 | 10.02 | 91.6 | 14.32 | 0.70 | 0.82 | 0.85 |
| 30 | 17.98 | 16.36 | 17.91 | 100.4 | 39.49 | 2.07 | 3.73 | 0.56 |
| 50 | 23.41 | 23.56 | 25.83 | 90.6 | 66.97 | 3.41 | 7.43 | 0.46 |
| 60 | 25.70 | 25.80 | 28.28 | 90.9 | 73.52 | 3.64 | 8.57 | 0.42 |

- H/D over bark remains within the 80–100 target band across mature ages (90–100), and height falls squarely within the Swedish site index band (H50 19.2–25.3 m, H60 21.1–26.9 m).
- **10-year dense regeneration canopy-closure test (44 trees, 44.4 m², 9900 stems/ha, bare ground, switch on):**

| year | trees alive | height median / max (m) | LAI (m²/m²) | under-canopy light (%) |
|---|---|---|---|---|
| 1 | 44 | 0.00 / 1.18 | 0.02 | 99% |
| 2 | 44 | 0.96 / 2.35 | 0.57 | 81% |
| 3 | 44 | 2.11 / 3.52 | 5.00 | 16% |
| 4 | 44 | 2.78 / 4.70 | 4.79 | 17% |
| 5 | 39 | 4.11 / 5.77 | 4.48 | 19% |
| 6 | 29 | 5.25 / 6.68 | 4.60 | 18% |
| 7 | 27 | 6.43 / 7.30 | 4.41 | 20% |
| 8 | 24 | 7.39 / 8.47 | 3.85 | 24% |
| 9 | 22 | 8.54 / 9.25 | 3.97 | 23% |
| 10 | 22 | 9.03 / 10.21 | 3.46 | 28% |

- Canopy closes at year 3 (LAI 5.00, light 16% < 21%), triggering self-thinning at year 5 (44 -> 39 -> 29 -> 22 by year 10).

**9. Moose browsing Part 1: bite diameter clipping (`species/betula_pendula.yaml`, `treegen/growth.py`, commit `a65253b`).**
- Leader damage clips browsed shoots to sourced bite diameter $2.2\text{ mm}$ (Mathisen et al. 2017: $2.16 \pm 0.15\text{ mm}$), removing the distal 10–35 cm of the current shoot rather than 100% of the shoot down to 2-year wood. Replacement leaders break from distal axillary buds on the $t - 1$ shoot.
- **Evaluation on 12-year natural plot (`--trees 25 --years 12 --seed 1 --mode natural`):**

| Metric | Baseline (full shoot killed) | Moose Part 1 ($d_{\text{bite}} = 2.2\text{ mm}$) |
|---|---|---|
| Browsed relay replacements | 34 | 23 |
| Median sideways run $dx_{y1}$ | 0.211 m | **0.041 m** (80.6% reduction) |
| Maximum sideways run $dx_{y1}$ | 0.729 m | **0.087 m** (88.1% reduction) |
| Minimum sideways run $dx_{y1}$ | 0.142 m | 0.017 m |

- **Why Part 2 is not needed:** Primary gravitropic reorientation is concentrated in the primary growth zone ($L_{\text{gz}} \approx 3\text{--}10\text{ cm}$, Bastien et al. 2013). Macroscopic $\eta_0 = 2.0\text{ m}^{-1}$ applies to whole stems. With Part 1, replacement leaders emerge from distal buds on the $t - 1$ shoot, keeping the lateral crook to $\le 8.7\text{ cm}$ (natural stem wobble). A special replacement turning rate is not required.

**10. Light diagnosis: woody shade, WAI, and density vs. per-tree foliage gap.**
- **Trunks and branches in light grid:** Trunks and branches currently cast 0 shade in the voxel light grid.
- **Projected wood area:** In `p26_nat` at age 60, the model's projected wood area is $\text{WAI} = 0.763\text{ m}^2\text{ m}^{-2}$. This matches Johansson 1999 (Swedish birch $\text{WAI} = 0.4\text{--}0.9\text{ m}^2\text{ m}^{-2}$) and Kucharik et al. 1998 / Gower et al. 1999 ($\text{WAI} \approx 0.5\text{--}0.8\text{ m}^2\text{ m}^{-2}$).
- **Light reduction:** Adding woody shade ($\Delta \tau_{\text{wood}} \approx \exp(-0.4 \times 0.763) \approx 0.74$) reduces under-canopy light at 2–5 m from 23–25% down to **15–18%**, below the 21% shedding threshold (`shedding.light_per_leaf_threshold: 0.21`), explaining why lower limbs and tufts fail to self-prune.
- **Stand density vs. per-tree foliage gap:**

| age | stems/ha (target) | LAI | per-tree LA (m²) | DBH over bark (cm) | Repola Eq. 12 (kg) | Model fol (kg) | Model / Repola 12 | Hagemeier & Leuschner (45 yr, 880/ha) |
|---|---|---|---|---|---|---|---|---|
| 30 | 1746 | 4.13 | 23.64 | 15.17 | 2.55 | 1.21 | 0.47 | – |
| 45 | 1710 (880) | 4.10 | 23.99 | 16.67 | 3.18 | 1.22 | 0.38 | 52.2 m² (~2.7 kg) |
| 50 | 1710 | 4.00 | 23.41 | 17.03 | 3.34 | 1.18 | 0.35 | – |
| 60 | 1710 (420) | 3.99 | 23.33 | 17.90 | 3.65 | 1.19 | 0.33 | – |

- Stand LAI in `p26_nat` (4.0–4.1) is 90% of Hagemeier & Leuschner's (4.59). At age 45, 1710 trees/ha share the canopy instead of 880 trees/ha ($1.94\times$ density), allocating only $5.85\text{ m}^2$ per tree vs $11.36\text{ m}^2$. Over 51% of the per-tree leaf area gap is purely geometric stand density. The rest is due to crowding-induced crown constriction (crown ratio 0.35 vs Repola mean 0.58).

## Phase 30: distance rule default; render artefacts, crown, foliage and stem mechanics diagnosed

**Default.** `pipe_model.huber_path_exponent` is 0.283: the Huber value rises tip to base with the leaf-weighted path length to the leaves supplied (corrected in campaign M1c: this credited the pattern to Mencuccini et al. 2019, which says the Huber value stays "relatively constant from twig to trunk base"; the pattern has no stem-level source), fitted to Konôpka and Repola over bark. All 20 tests pass.

**A. Hooks, loops and cones in the plot render** (p26 natural plot at 60). No model change.
- **All 29 living browsed trees continue their stem on a lateral replacement leader.** Its first internode leaves at a median 45° from vertical (34–50°).
  - In 10 trees it runs more than 0.3 m sideways in its first 2 m, up to 0.71 m.
  - That first-year knee thickened into the stem (10–16 cm now). Posture correction (rate ∝ dr/r²) cannot straighten it.
  - The big loop is tree 73: browsed in year 5, replacement born in year 4 at 1.8 m, leaving at 81–88° and running 0.68 m sideways before turning up. It is 13.5 cm thick now.
- **The losing replacement leaders do die.** Only 3 of 95 living trees keep an axis-0 stub off the winning stem. No axis below 4 m turns more than 300°.
- **The white cones are drawing artefacts.** Axis 0 ends where the browsed leader died, and the mesh caps it with a cone. The replacement leader starts as a branch with a collar instead of continuing the tube. Only 2 thick living tube ends below 4 m exist in the whole plot.

**C. Tufts on the single tree.** They are living, leafy small limbs, not dead ones.

| tree | age | H (m) | crown base by leaf share (m) | crown ratio | lowest live limb (m) | crown ratio by lowest live limb | live limbs below the crown base | per m below 0.5 H |
|---|---|---|---|---|---|---|---|---|
| radius rule (rendered) | 30 | 18.0 | 4.1 | 0.77 | 1.6 | 0.91 | 35 | 25.6 |
| radius rule | 50 | 22.5 | 9.1 | 0.60 | 1.6 | 0.93 | 139 | 21.0 |
| radius rule | 60 | 23.8 | 10.7 | 0.55 | 1.6 | 0.93 | 136 | 14.9 |
| distance rule (default) | 30 | 18.7 | 4.0 | 0.79 | 2.8 | 0.85 | 2 | 16.0 |
| distance rule | 50 | 24.2 | 8.5 | 0.65 | 2.8 | 0.89 | 64 | 14.5 |
| distance rule | 60 | 25.8 | 8.5 | 0.67 | 2.8 | 0.89 | 37 | 8.5 |

- Every limb below the crown base carries leafy short shoots, but each holds under 0.5 % of the tree's leaves (`stats.crown_base_min_leaf_share`). They are about 1.1 m long and 0.6 cm thick at 60.
- With about 360 limbs on a 24 m stem, the crown reads as tufts all down the stem. The 6 Nordic scans have about 68 first-order branches of 1 cm or more.
- Repola's Finnish stand sample has a crown ratio of 0.58 ± 0.14 (0.29–0.96). The model matches by its leaf-share definition (0.55–0.79) but not by lowest live limb (0.85–0.93).
- The small limbs are lit above the 21 % death light and pay their own upkeep, consistent with the stand floor light being too high (0.24 against 0.15 measured, phase 10).

**2. Leaf area check: a leaf problem for older trees** (`tools/foliage_check.py`).

| | age | DBH over bark (cm) | model LMA (g/m²) | foliage / Repola Eq. 12 | / A6 with model crown ratio | / A6 with crown ratio by lowest live limb |
|---|---|---|---|---|---|---|
| stand tree | 30 | 20.7 | 54 | 0.56 | 0.31 | 0.25 |
| stand tree | 50 | 27.4 | 52 | 0.47 | 0.44 | 0.23 |
| stand tree | 60 | 29.3 | 51 | 0.43 | 0.40 | 0.21 |
| natural plot (median) | 30 | 15.3 | 51 | 0.47 | 0.35 | 0.16 |
| natural plot | 50 | 17.1 | 51 | 0.35 | 0.62 | 0.14 |
| natural plot | 60 | 17.9 | 51 | 0.31 | 0.69 | 0.13 |

- **Older trees** carry about half of Repola's foliage, or less, for their DBH. With branches at 15–22 % of his and stem wood 1.13–1.28× at matched DBH and height (mostly taper), the crown is undersized.
- **Young trees, against Konôpka at the base diameter he measured:** the model has 3.8 / 3.0 / 1.6× his leaf area at D0 = 50 / 75 / 100 mm.
- **Two leaf sets.** The reported leaf area (stats) counts leaves on every node grown this year. Photosynthesis and the logged leaf dry mass count the leaves of nodes grown last year, one season later. In fast-growing young years the two differ about 3× (age 6: 13.0 against ~4 m²); by 30 they agree (52.2 against 54 m²). The reported leaf area is the one that matches this year's rings.
- The model's LMA (51–54 g/m²) is below the 67–68 behind Repola's and Konôpka's conversions.

**B and 3. Stem mechanics** (`tools/stem_mechanics.py`).
- **The stem is loaded only by the increment of its weight, and only through horizontal lever arms** (`mechanics.bend_and_correct`: this year's added wood and leaf mass, moment = arm × g). A vertical stem has no lever arm.
- **There is no axial compression or buckling, no wind and no snow.** Leader axes are stiff and corrected towards vertical by reaction wood at a rate set by the year's ring (C_rw dr/r²).
- **Uprightness costs nothing.** In LIGNUM mode the stress-floor wood (self-weight bending) is also added outside the pool, though it never binds.
- **Fresh density:** Finnish *B. pendula* basic density 512 kg m⁻³ (Heräjärvi 2004; 530 in Aosaar et al. 2016) × (1 + 0.72), with green sapwood moisture of 70–72 % for paper, sweet and yellow birch (Wood Handbook FPL-GTR-282, Table 4-1). That gives 880–910 kg m⁻³, so the model's 850 is 4–7 % low. No silver-birch green moisture content was found.
- **Green stiffness and strength:** Finnish silver birch 14.5 GPa and 114 MPa (Heräjärvi 2004, Wood Sci. Technol.), scaled by yellow birch's green-to-12 % ratios (10.3/13.9, 57/114; Table 5-3a), give 10.7 GPa and 57 MPa. The model uses 10 GPa.
- **Buckling:** Rayleigh estimate for a cantilever column with the stem's own EI(z), own weight and the crown's wood, winter. Snow on the crown's projected area: 5.35 kg m⁻² (the Finnish mean crown load, Lehtonen et al. 2014, Silva Fennica 48:1120) and 30 kg m⁻² (above which wet snow typically damages trees, Nykänen et al. 1997, Silva Fennica 31:193). Below 1 the stem buckles.

| tree | age | H (m) | DBH over bark (cm) | H/D | own weight | + 5.35 kg m⁻² | + 30 kg m⁻² |
|---|---|---|---|---|---|---|---|
| stand tree | 30 | 18.7 | 20.7 | 90 | 12.7 | 10.8 | 6.3 |
| stand tree | 45 | 23.2 | 25.9 | 90 | 9.4 | 7.5 | 3.9 |
| stand tree | 50 | 24.2 | 27.4 | 88 | 9.4 | 7.6 | 4.1 |
| stand tree | 60 | 25.8 | 29.2 | 88 | 7.6 | 6.0 | 3.0 |
| plot tree 76 | plot year 30 | 15.0 | 8.1 | 184 | 2.7 | 1.6 | 0.54 |
| plot tree 76 | plot year 50 | 21.4 | 8.3 | 260 | 0.65 | 0.36 | 0.12 |
| plot tree 76 | plot year 60 | 23.9 | 8.5 | 282 | 0.48 | 0.27 | 0.09 |

From plot year 50, tree 76 would buckle under its own winter weight, and under an ordinary snow load. The model stands it for free.

**The thin top and the steps** (B; the stand tree at 60):
- The leader grows in pulses. In many years it barely extends: years 37–39 at 0.84 H, 41–45 at 0.88–0.90 H.
- Rings build up on the last segment during a stall, and the next pulse starts at the tip radius. That gives the steps: d/DBH 0.129 → 0.073 at year 46 (radius rule), 0.162 → 0.073 at year 49 (distance rule).
- Below about 0.88 H the stem is too thick; above, too thin (0.07 against 0.11 at 0.9 H).
- Nothing mechanical requires the leader to be thicker: height costs only tip cross-section × length.

**What a wind-load rule would take** (not built). The constant-stress hypothesis (Metzger 1893; holds approximately above the butt swell for canopy-top winds of 2.5–10 m/s, Morgan & Cannell 1994, Tree Physiol. 14:49; mostly supported in Dean et al. 2002, Trees; disputed for some species) sets the diameter so that bending stress from wind on the crown is even down the stem: d(z) ∝ M(z)^{1/3}.
- **Its shape, with the model's own crown as the load** (drag in proportion to leaf area, uniform wind), against the model stem and Hansen taper:

| tree | age | d/DBH at 0.3 / 0.5 / 0.7 H: model | constant stress | birch taper |
|---|---|---|---|---|
| stand tree | 30 | 0.90 / 0.71 / 0.49 | 0.83 / 0.64 / 0.43 | 0.78 / 0.63 / 0.40 |
| stand tree | 50 | 0.89 / 0.71 / 0.50 | 0.83 / 0.65 / 0.41 | 0.75 / 0.60 / 0.39 |
| stand tree | 60 | 0.90 / 0.76 / 0.55 | 0.84 / 0.68 / 0.45 | 0.75 / 0.60 / 0.38 |
| plot tree 76 | plot year 50 | 0.92 / 0.86 / 0.78 | 0.89 / 0.77 / 0.60 | 0.82 / 0.69 / 0.48 |
| plot tree 76 | plot year 60 | 0.91 / 0.85 / 0.77 | 0.89 / 0.78 / 0.62 | 0.81 / 0.68 / 0.48 |

  In the top fifth of the stem the constant-stress profile tracks birch taper within about 0.01–0.02 of DBH, with no thin whip.
- **What it would need:**
  1. A wind load per crown element: drag area from leaf and branch area, a drag coefficient with streamlining, and a vertical wind profile with shelter in the stand. Birch parameters would come from wind-risk models such as HWIND/GALES (VERIFY sources).
  2. A target stress: a fraction of green MOR (57 MPa derived) with a safety factor. The existing self-weight stress floor uses 16 MPa.
  3. A reference wind speed. It sets the magnitude, not the shape, so it must be sourced or it becomes a free knob.
  4. Each ring is the larger of the pipe requirement and the stress requirement, paid from the same pool (unlike the current stress floor). Height then costs stem wood, because a taller stem with the same crown needs a thicker base.
  5. Optionally, a self-weight and snow buckling check.

**Parked:** butt swell and disused pipes, until limbs carry realistic wood.

## Phase 29: comparisons over bark; why the stem is cylinder-like; Huber value by path length (tested, off)

**Over bark.** The model has no bark, so its DBH is wood. `tools/bark.py` converts it with the birch double-bark model of Hansen et al. 2023 (with its 2024 correction; taperNOR coefficients). `tools/stem_compare.py` applies the conversion to every comparison with field DBH, and `tools/fit_huber_exponent.py` does too; b is unchanged.

| | age | H/D, wood DBH | H/D, over bark | same stem wood with birch taper, over bark |
|---|---|---|---|---|
| seed-1 stand tree | 30 | 91 | 83 | 73 |
| seed-1 stand tree | 50 | 83 | 76 | 62 |
| seed-1 stand tree | 60 | 83 | 75 | 59 |
| natural plot p26 (median) | 30 | 130 | 119 | 101 |
| natural plot | 50 | 155 | 142 | 113 |
| natural plot | 60 | 165 | 150 | 118 |

Over bark, stem wood is 1.18–1.35× Repola's (stand tree) and 1.35–1.54× (plot); living branches are 0.10–0.14 and 0.22–0.35 of his.

**Why the ring rule makes a cylinder-like stem.** Seed-1 stand tree, exact (the model's methods wrapped). Along the stem, relative to 1.3 m:

| age | z/H | wood | birch taper | ring need | = leaf area above | × Huber(r) | disused-pipe sapwood U, % of wood |
|---|---|---|---|---|---|---|---|
| 30 | 0.3 / 0.5 / 0.7 | 0.83 / 0.58 / 0.27 | 0.61 / 0.38 / 0.16 | 0.85 / 0.61 / 0.30 | 0.88 / 0.66 / 0.37 | 0.97 / 0.92 / 0.82 | 1 / 0 / 0 (10 at 0.05 H) |
| 50 | 0.3 / 0.5 / 0.7 | 0.83 / 0.56 / 0.28 | 0.56 / 0.35 / 0.14 | 0.86 / 0.61 / 0.32 | 0.89 / 0.67 / 0.39 | 0.97 / 0.91 / 0.82 | 3 / 2 / 1 (8 at 0.05 H) |
| 60 | 0.3 / 0.5 / 0.7 | 0.84 / 0.62 / 0.33 | 0.55 / 0.34 / 0.13 | 0.89 / 0.69 / 0.40 | 0.91 / 0.75 / 0.48 | 0.97 / 0.93 / 0.84 | 5 / 4 / 3 (10 at 0.05 H) |

- **The wood follows the ring need at every height.** The need is leaf area above × a Huber value that depends on radius. Along a bole whose radius barely changes, the Huber value hardly changes either: 0.91–0.93 of the breast-height value at mid-height. The leaf area above stays high to mid-height (66–75 %).
- **So the rule asks for 61–69 % of the breast-height cross-section at mid-height,** against 34–38 % in birch.
- **The radius exponent b stands in for the extra wood real stems carry at breast height,** but adds it wherever the stem is thick, inside the crown too.
- **Disused pipes:** shed branches' sapwood is only 6–11 % of the wood at the base and less above. The model's limbs are 10–14 % of Repola's, so shedding them retires little. It is not the main cause of the cylinder-like lower stem.
- **Butt swell is not modelled.** The curve has 1.03–1.11× the breast-height area at 0.05 H; the model has 1.00.
- **Mäkelä 2002 (Tree Physiol. 22:891)** derives birch-free stem taper from the pipe model with pipe reuse controlled by foliage dynamics, and later work in that line has pipes outlast their foliage and be reused. Immediate retirement of all a shed branch's pipes is not what that theory uses.

**Fix tested alone: Huber value by path length** (`pipe_model.huber_path_exponent`, off).
- The Huber value rises tip to base with the leaf-weighted path length l to the leaves each internode supplies: huber_value × (l / 0.14 m)^c. (Corrected in campaign M1c: this said the rise is from Mencuccini et al. 2019, New Phytol. 224:1544. That paper says the opposite, "Hv tend to remain relatively constant from twig to trunk base". The only birch support found is within the crown, Sellin & Kupper 2006.) The 0.14 m is half the 27.9 cm current-year shoots the twig value was measured on [OP22].
- Fitted to Konôpka and Repola over bark: c = 0.283. The same structured misfit as the radius rule remains: young trees have 2.3–1.6× Konôpka's leaf area, DBH 20–26 cm trees 0.7–0.6× Repola's.

| seed-1 stand tree | 30 | 45 | 50 | 60 |
|---|---|---|---|---|
| height, radius rule → path rule (m) | 18.0 → 18.7 | 21.4 → 23.2 | 22.5 → 24.2 | 23.8 → 25.8 |
| H/D over bark | 83 → 90 | – | 76 → 88 | 75 → 88 |
| form factor (birch taper) | 0.53 → 0.51 (0.44) | – | 0.53 → 0.51 (0.41) | 0.55 → 0.54 (0.40) |
| d/DBH at 0.3 / 0.5 H (taper) | 0.91, 0.76 → 0.90, 0.71 (0.78, 0.63) | – | 0.91, 0.74 → 0.89, 0.71 (0.75, 0.60) | 0.92, 0.79 → 0.90, 0.76 (0.75, 0.60) |
| stem wood / Repola, over bark | 1.18 → 1.13 | – | 1.26 → 1.18 | 1.35 → 1.28 |
| branches / Repola | 0.10 → 0.15 | – | 0.11 → 0.18 | 0.14 → 0.22 |
| CUE, path rule | 0.50 | 0.45 | 0.43 | 0.44 |

- The direction is right: thinner upper stem, more branch wood, and heights and H/D inside their bands.
- The taper barely moves. The breast-height data hold c near 0.28, which gives a Huber value at mid-height of ~0.76 of breast height's, where birch taper needs ~0.45–0.5.
- No single-exponent Huber rule calibrated at breast height puts enough of the stem wood at the base in this model.

## Click scatter, measured

You re-traced ten trunks blind on the three Gullmarsskogen photos, plus one on an iNaturalist photo. The tracer pointed at `reference/stem_traces_reclick.json`; the original traces are unchanged. Each new trace was matched to the old one by its base (6–41 px apart). For every click, the sideways offset from the other trace's line at the same height was measured, both ways (`tools/click_scatter.py`).
- **Click scatter:** σ ≤ 0.39 % of image height, 7.0 px on the render. A version less sensitive to outliers gives 0.32 %, 5.8 px. Real wobble between clicks adds to it, so it is an upper bound.
- **Against the earlier figures:** 0.63–0.77× the earlier single-trace upper bound of 9.1 px. The model comparisons assumed 0.5× (4.6 px).
- **Click counts:** the re-clicks used 8–12 clicks per trunk, against 3–8 originally.
- **Repeatability, median |old − new|:** off-line 0.58 percentage points, turning 7.0°, lean 0.4°, bends 1. The photos' lean (median 2.1°) is well above click noise.
- **Effect on the stem table (phase 26):** at 0.63–0.77× the model's matched-size stems sit between the 0.5× and 1× rows. Roughly: off-line 0.9–1.0 % against 1.74 %, turning 3.5–4.5° against 12.7°, lean ~0.85° against 2.1°. The model's stems stay straighter and more upright than the photos (stem traces parked until thinning works).

## Phase 28: diagnosis of spare sapwood, taper, bark and why no tree is suppressed

Diagnosis only; no model change. The tracer server gained `--traces <file>` for the re-click test.

**Switch from the logs** (natural plot p26, plot years 10–60, all trees). The switch's cost, the ring need at λ = 0, was not logged.
- In a year with new shoots the rings were paid in full, so the need is at most the rings actually laid (stored radii). Upkeep plus that bound is 0.80 of fixed carbon at the median and 0.85 at most; no year comes near a deficit.
- This holds by construction: when the pool covers the need, upkeep + need < fixed − root budget. The switch can bite only in years without new shoots.
- 23 tree-years had no new shoots. Only 4 trees had two or more in a row (95, 75, 38, 15), and they died under the existing rule at plot years 47, 39, 21 and 18. No surviving tree would have died with the switch on.

**Where the spare conducting wood comes from.** The seed-1 stand tree is exact: the model's methods wrapped, ledgers decayed with the sapwood. Spare = (1 − ss) × sapwood − Huber × leaf area beyond.

| age | where | sap | need | spare | of it: shed branches' sapwood | stress floor | foliage lost on living branches |
|---|---|---|---|---|---|---|---|
| 30 | stem at 1.3 m | 254.9 cm² | 252.2 cm² | 0 | – | – | – |
| 30 | whole tree | 247 dm³ | 251 dm³ | 0.6 dm³ (0 %) | 37 % | 0 | 63 % |
| 50 | stem at 1.3 m | 423.7 cm² | 398.8 cm² | 18.9 cm² (5 %) | 100 % | 0 | 0 |
| 50 | whole tree | 537 dm³ | 506 dm³ | 23.3 dm³ (4 %) | 81 % | 0 | 19 % |
| 60 | stem at 1.3 m | 445.6 cm² | 417.1 cm² | 22.2 cm² (5 %) | 100 % | 0 | 0 |
| 60 | whole tree | 638 dm³ | 600 dm³ | 29.6 dm³ (5 %) | 92 % | 0 | 8 % |

The suppressed plot tree (76: unbrowsed, germinated in year 3) was rebuilt from its export: sapwood from the stored radii, need from the stats leaf area. On the stand tree this rebuild matches the exact figures within 0.1 % for sapwood, 1.5 % for need and 3 cm² for spare.

| plot year (tree age) | DBH (cm) | sap at 1.3 m (cm²) | need (cm²) | spare (cm²) | shed branches' sapwood still counted (cm²) |
|---|---|---|---|---|---|
| 30 (27) | 7.5 | 34.8 | 31.5 | 2.8 | 22.1 |
| 50 (47) | 7.6 | 27.1 | 25.2 | 1.6 | 44.2 |
| 60 (57) | 7.8 | 25.7 | 21.7 | 3.7 | 52.3 |

- The surplus is shed branches' sapwood still counted as conducting: all of it at 1.3 m, and 81–92 % of the whole tree's at 50–60.
- Because of it, the need at λ = 0 is zero in a tree whose foliage has stopped growing.
- The suppressed tree's sapwood shrinks at the turnover rate and its foliage shrinks in step (8.2 → 5.6 m²). Its need stays near zero: it declines without ever running a deficit.

**Stem taper against Norwegian birch** (Hansen, Rahlf, Astrup & Gobakken 2023, Scand. J. For. Res. 38:413). Kozak 1988 form; birch coefficients and the double-bark model taken from the taperNOR R package 0.2.1. Matched under bark at 1.3 m to the model's DBH.

| | age | d/DBH at 0.1 / 0.3 / 0.5 / 0.7 / 0.9 H, model | taper curve | form factor, model / curve | model / curve volume | excess above 0.3 H |
|---|---|---|---|---|---|---|
| stand tree | 30 | 0.99 / 0.91 / 0.76 / 0.52 / 0.09 | 0.95 / 0.78 / 0.62 / 0.40 / 0.12 | 0.53 / 0.44 | 1.21 | 83 % |
| stand tree | 50 | 0.99 / 0.91 / 0.74 / 0.52 / 0.07 | 0.92 / 0.75 / 0.59 / 0.37 / 0.11 | 0.53 / 0.40 | 1.31 | 76 % |
| stand tree | 60 | 0.99 / 0.92 / 0.79 / 0.56 / 0.07 | 0.92 / 0.74 / 0.58 / 0.37 / 0.11 | 0.55 / 0.40 | 1.39 | 76 % |
| plot (median) | 30 | 0.99 / 0.95 / 0.88 / 0.63 / 0.12 | 0.96 / 0.80 / 0.66 / 0.44 / 0.15 | 0.62 / 0.46 | 1.34 | 88 % |
| plot | 50 | 0.99 / 0.95 / 0.89 / 0.82 / 0.27 | 0.93 / 0.78 / 0.65 / 0.44 / 0.15 | 0.70 / 0.44 | 1.59 | 87 % |
| plot | 60 | 0.99 / 0.95 / 0.89 / 0.82 / 0.32 | 0.92 / 0.78 / 0.64 / 0.43 / 0.15 | 0.70 / 0.43 | 1.63 | 86 % |

- The model's bole is nearly cylindrical to mid-height and its upper stem far too thick. The lowest tenth is 9–18 % thin, with no butt swell.
- Laid out on birch taper, the same stem wood would give DBH 21.9 / 31.5 / 34.8 cm (stand) and 16.5 / 19.9 / 21.1 cm (plot) at 30 / 50 / 60. H/D would be 82 / 71 / 68 and 110 / 121 / 127, against 91 / 83 / 83 and 130 / 155 / 165. All of these are wood diameters.

**Bark and density.**
- The model has no bark: its radius is wood, and the mesh paints bark on it. Model DBH is therefore under bark.
- Every DBH it was compared with is over bark: Repola, Hagemeier & Leuschner, Konôpka, and the Huber fit's DBH.
- Double bark at 1.3 m by the Norwegian model: 2.1 cm at a wood DBH of 19.7 cm, 1.1 cm at 13.9 cm. Repola's sample mean is 0.9 cm at DBH 16.5.
- Repola's stem wood excludes bark; his living branches include it.
- Model basic density is 530 kg m⁻³ (Aosaar et al. 2016, a 17-year Estonian stand). Fresh density in the mechanics is 850 (VERIFY).
- Corrected to over-bark DBH, model stem wood is 1.16–1.29× Repola's (stand) and 1.40–1.68× (plot). That is close to the model-to-taper volume ratios, so too little taper explains most of the heavy stems.
- Branches: 0.10–0.13 (stand) and 0.24–0.39 (plot) of Repola's.

**Why no plot tree is suppressed.**
- The light grid is not coarse: 0.10 m voxels against crowns 1.6–2.7 m wide.
- The shade blur is not the cause either. At the year-58 checkpoint, recomputing the light with the penumbra at 1×, 0.1× and 0× leaves the bottom quarter's leaf-weighted bud light at 1.01, 1.01 and 1.00 of the top quarter's.
- Light is even because the crowns are level. The bottom quarter by DBH grows as fast or faster in height (1.97 / 1.53 / 1.13 m per 5 years against 1.91 / 1.22 / 0.93 at 30 / 50 / 60). It closes from 0.84 to 0.94 of the top-quarter height, and its mean bud light (0.32–0.36) equals the dominants' (0.35).
- Height growth costs a suppressed tree almost nothing (tip cross-section × length), and nothing ties height to the stem.
- Uniform-column buckling height H_crit = 0.79 (E / ρg)^{1/3} D^{2/3} (Greenhill 1881), with the model's E 10 GPa and fresh density 850:
  - stand tree at 0.63–0.65 of it;
  - plot trees median 0.81 / 0.99 / 1.07 at 30 / 50 / 60, worst 1.04 / 1.48 / 1.56. Tree 76 is 23.9 m tall on 7.8 cm at 60.
  - For reference, the same formula gives 0.75–0.93 for Hagemeier & Leuschner's stand at 45 (DBH 19 cm over bark, 20–25 m).
- Starting density: 1800/ha, the first stage of the managed thinning table. Its source, Swedish practice [SS14], gives that as the density after pre-commercial thinning ("no more than 1500–2000 birches/ha by 6–7 m"). Natural regeneration starts far denser (the dense-regeneration test: 9900/ha).

## Phase 27: upkeep switch tested, regeneration and canopy closure, branch wood against Repola

**Upkeep switch** (`pipe_model.sapwood_replacement_is_upkeep`, off). It adds the rings that keep this season's foliage supplied (the LIGNUM ring need at λ = 0) to the upkeep in the natural-mode death test.
- Source: in the pipe model's carbon balance the growth that replaces senescent sapwood comes before foliage, and a tree that cannot pay it declines and dies (Mäkelä 1986, J. Theor. Biol. 123:103; IIASA WP-85-89).
- It changes no growth: the seed-1 stand tree is identical with it on and off.

| age | H (m) | DBH (cm) | H/D | CUE | upkeep / fixed, off | replacement rings / fixed | upkeep / fixed, on |
|---|---|---|---|---|---|---|---|
| 30 | 17.7 | 18.8 | 94 | 0.53 | 0.42 | 0.17 | 0.59 |
| 45 | 21.0 | 25.0 | 84 | 0.44 | 0.55 | 0.05 | 0.61 |
| 50 | 22.0 | 26.7 | 83 | 0.43 | 0.56 | 0.00 | 0.56 |
| 60 | 23.4 | 28.4 | 82 | 0.44 | 0.54 | 0.00 | 0.54 |

- The highest upkeep/fixed over ages 6–60 is 0.89 (age 28), with no deficit year.
- Once foliage stops growing, the conducting wood exceeds what this season's foliage needs, so the replacement need is 0. The tree's rings are all for new shoots' leaves.

**Regeneration, 8 years with the switch on** (resumed from the natural plot at 58, 95 trees):
- Shaded seedlings die. Of recruits old enough, the share alive was 1.00 after one and two seasons, then 0.06, 0.02 and 0.01 after three, four and five, and 0 of 481 after six. Before the per-leaf carbon fix every recruit survived.
- Causes: 936 failed to establish (no carbon two years running: their buds fall below the shoot survival light and the seedling loses its leaves), 5 died of deficit, 1 no carbon.
- None of the 95 established trees died in the 8 years. The switch did not start self-thinning.
- Peak memory 4.9 GB.

**Canopy closure, dense regeneration** (44 seedlings on 44 m², 9900/ha, bared ground, switch on). Ages 50 and 60 do not apply to this 10-year test.

| year | trees | height median / max (m) | LAI | light under the canopy |
|---|---|---|---|---|
| 4 | 44 | 1.76 / 3.05 | 1.18 | 69 % |
| 5 | 44 | 2.80 / 4.23 | 3.21 | 30 % |
| 6 | 44 | 3.96 / 5.40 | 5.15 | 13 % |
| 8 | 40 | 5.93 / 7.61 | 4.80 | 16 % |
| 10 | 35 | 7.61 / 9.56 | 4.42 | 18 % |

The canopy closes at 5–6 years (before: LAI 0.09 at 5 and 0.96 at 8), and self-thinning starts at 8.

**Stem-chain regression fixed.** The thickest-continuation rule of phase 26 also let an ordinary limb take over where it was thicker than the leader's top. In the seed-1 stand tree at 50–60 the chain left the leader at 19.7 m, so the stem's posture target went to a limb.
- Only leader axes (the stem and its replacement leaders) or the relay shoot may now take over.
- Seeds 1 and 3: the chain reaches the top at 30–60.
- 12-year natural plot: 31 of 33 browsed trees have DBH on the stem that carries the top. The other 2 are forks whose thicker stem is the shorter.
- Seed-1 stand tree now: H 18.0 / 21.4 / 22.5 / 23.8 m and H/D 91 / 84 / 83 / 83 at 30 / 45 / 50 / 60, CUE 0.52–0.44.

**Branch wood against Repola 2008** (model 1, at each tree's own DBH and height):
- Living branches (Eq. 9): ln y = −4.152 + 15.874 dS/(dS+16) − 4.407 h/(h+10).
- Stem wood (Eq. 7): ln y = −4.879 + 9.651 dS/(dS+12) + 1.012 ln h.
- Both with his bias corrections. dS rather than d in Eq. 9 is checked against his mean tree: 10.6 kg of branches on 73.6 kg of stem, as in his measured plot 4_11 (9.4 on 70.8).
- Model wood is π r² L × 530 kg m⁻³, wood only; Repola's branches include bark.

| | age | DBH (cm) | H (m) | branch wood, model / Repola (kg) | ratio | stem wood, model / Repola | branch : stem, model / Repola |
|---|---|---|---|---|---|---|---|
| stand tree | 30 | 19.7 | 18.0 | 2.7 / 19.8 | 0.13 | 1.40 | 0.02 / 0.18 |
| stand tree | 50 | 27.0 | 22.5 | 6.9 / 45.6 | 0.15 | 1.47 | 0.02 / 0.19 |
| stand tree | 60 | 28.8 | 23.8 | 9.8 / 53.0 | 0.19 | 1.57 | 0.02 / 0.18 |
| natural plot, median of trees | 30 | 13.9 | 18.1 | 1.9 / 5.9 | 0.31 (0.22–0.75) | 1.62 | 0.02 / 0.10 |
| natural plot | 50 | 15.6 | 24.3 | 2.6 / 6.6 | 0.39 (0.32–0.74) | 1.82 | 0.02 / 0.07 |
| natural plot | 60 | 16.3 | 26.5 | 3.3 / 7.0 | 0.47 (0.37–0.67) | 1.85 | 0.02 / 0.06 |

At matched DBH and height, the model carries 1.4–1.9× Repola's stem wood and 13–47 % of his branch wood.

**Which way each candidate moves carbon** (diagnosis only, nothing built):
- **Refit b, like for like:**
  - Young trees in the dense plot carry the same leaf area per DBH as the open-grown stand tree: 6.0 / 9.3 / 12.6 m² at DBH 2.4 / 3.9 / 5.4 cm, against Konôpka's 2.4 / 5.0 / 8.5. So b would not move.
  - Fitted to Repola alone, b is ~0.25 (misfit 0.077 against 0.106). No single b fits his shape: at b 0.25 the model's leaf area runs from 1.5× his at DBH 11 to 0.7× at 26.
  - b 0.25 moves carbon from rings to shoots, but only from 1–4 % to 4–6 % of the pool, and mostly into height: H/D 108 / 104 / 103 / 104 at 30 / 45 / 50 / 60 against 91 / 84 / 83 / 83. Limbs ≥ 1 cm still get 0–2 %.
- **Disused pipes:** shed branches' sapwood stops conducting below them, so the same foliage needs more ring. Carbon moves from shoots to rings.
  - On the stand tree's stem the shed limbs' base area is 13 % of the stem ring at 1.3 m in 46–50 and 28 % in 56–60 (none shed in 26–30).
  - Shoots would lose most of their 3–4 %, unless b were refitted lower to compensate.

**Photo lean and perspective** (signed lean against horizontal position, per photo):
- The iNaturalist photos show keystone: tops lean towards the centre, at −1.7 to −13.6° per half-width, R² 0.41–0.95.
- The three Gullmarsskogen stand photos show none: slopes are small and the wrong sign (+0.9 to +3.0, R² 0.03–0.21). The render's horizon row would imply a 17° upward tilt and 7.5° of keystone at the frame edge, so the photos behave as if taken level or perspective-corrected.
- Their mean signed lean is +2.1, +2.9 and −0.3°. That is camera roll or a real shared lean; the traces cannot tell them apart.
- Removing roll and keystone per photo, the median |lean| goes from 2.2 to 1.6° for all photos and from 2.1 to 1.9° for Gullmarsskogen. That is a lower bound, as it also removes any real shared lean. Model trunks at matched size: 0.8–0.9°.

**Click scatter, re-click set:** ten trunks on the three Gullmarsskogen photos, chosen to span straight to wobbly (off-line 0.44–4.69 %), 41–84 % of image height and 3–8 clicks. Trunk ids: tmvx5h57c137, tmvx5iaw2148, tmvx5ikyp149 (stand_5); tmvx59zso70, tmvx583zl57, tmvx5981k67, tmvx5al1n77 (stand_1); tmvx4zk1i51, tmvx4zcjz49, tmvx4yz4y46 (stand_6).

## Phase 26: natural plot with turnover, stem chain, short-shoot buds, stem traces per trunk

**Stem chain.** After browsing, the stem followed the first replacement shoot that grew, not the one that won. DBH was measured on a suppressed side stem: 3.7 cm, against 20 cm on the stem that carries the crown, with a crown ratio of 0.97. The chain now takes the main child unless a living lateral or the relay shoot is thicker. Plot tables below are re-measured from the timelines with this rule.

**Short-shoot buds.** A tip that could afford 0.1–1 metamer made a whole node with a dormant lateral bud. After age 30, 31–46 % of order-1/2 internodes on the seed-1 stand tree were under 1 cm, so buds and short shoots stacked at millimetre spacing. Such an increment now carries its leaf for one season and no axillary bud (`bud_fate.axillary_buds_below_one_metamer: false`).
- Sources: Ishihara & Kikuzawa 2009, Ann. Bot. 104:1195 (*B. grossa*: short shoots carry only their terminal bud); *B. papyrifera*, Can. J. Bot. 1984, doi:10.1139/b84-066 (long-shoot buds form in the axils of late leaves).
- Seed-1 stand tree: H/D 94 / 87 / 83 / 83 at 30 / 40 / 50 / 60 (was 86 / 76 / 75 / 75), heights 17.7 / 20.3 / 22.0 / 23.4 m.
- Twig clusters are thinner at 15: 863 order-2+ leafy buds against 1489, local leaf density p90 6.3 against 7.3 m² m⁻³. Survival of order-2 axes born at 7–10 rose from 59 to 70 %.
- Limbs did not change.

**What limits limbs: the carbon pool, not twig packing.**
- In the LIGNUM pool, rings take 95–99 % of each year's net shoot carbon (stem 92–98 %). New shoots and their leaves get 1–5 %, and at 30 the year's new internodes are a median 0.3 cm long.
- At 30 the stand tree's NPP goes about 59 % to stem wood, 1–2 % to branches and new shoots, 13 % to leaves and 27 % to roots.
- Under the fitted Huber rise, each new 15 cm² leaf commits ~4.7 g of ring wood down to the base, ~50× its own mass.
- Twig packing at the scale Hagemeier & Leuschner measured (leaf area per crown-envelope volume in 2 m layers, birch maximum ~3 m² m⁻³ at the top) was in range at 0.5–0.85 H in phase 11, and too thin in the top tenth. The 7 m² m⁻³ figure is leaf area within 0.25 m of twig buds, a finer scale without gaps, so the two are not comparable.
- Only 14–19 % of a twig bud's shade comes from its own 10 cm layer.
- Turnover and old-wood accumulation apply to limbs as to the stem; `wood_area` never falls, so a limb keeps the wood of twigs it has shed. The shed twig's sapwood still counts as conducting in the limb until it ages out at 1.4 %/yr; disused pipes (Shinozaki; CROBAS crown rise) are not modelled.

**Natural plot, seed 1** (re-measured with the corrected stem rule; turnover, short-shoot buds):

| year | N/ha | DBH (cm) | H mean / top quarter (m) | band | H/D median | BA (m²/ha) | leaf area / tree (m²) |
|---|---|---|---|---|---|---|---|
| 30 | 1746 | 13.8 | 18.1 / 19.6 | 13.4–19.7 | 130 | 27.3 | 23.6 |
| 45 | 1728 | 15.1 | 22.9 / 24.1 | 18.0–24.0 | 151 | 32.4 | 23.9 |
| 50 | 1710 | 15.5 | 24.3 / 25.4 | 19.2–25.3 | 155 | 33.9 | 23.3 |
| 60 | 1710 | 16.2 | 26.5 / 27.5 | 21.1–26.9 | 165 | 37.3 | 23.3 |

- Hagemeier & Leuschner: 880/ha, DBH 19 cm, ~25 m²/ha at 45; 420/ha at 67. The run before the bud rule (p25) was within 0.5 m of height and 8 of H/D of this one.
- **Self-thinning has not come back.** 5 of 100 trees died. Every tree reaches the canopy, all within 0.8× the top-quarter height. Suppressed trees pay about half their fixed carbon in upkeep and never run a deficit.
  - The rings that replace senescing sapwood are not part of upkeep in the death test. When the pool cannot pay them they are part-paid, with no consequence; hydraulics uses its own pipe area, not `sap_area`.
  - `pipe_model.sapwood_replacement_is_upkeep` (off, not yet tested) would count them.
- **Repola A6 does not hold in the plot.** The crown-ratio coefficient of the model's leaf area at given DBH is 0.01–0.10 (p25: −0.14 to −0.02), against 2.819. The trees carry about half the leaf area Eq. 12 gives for their DBH (23 m² against 32–47).
- CUE 0.48.

**Limbs against the 6 Nordic scans** (scans: 58 limbs > 2 cm, largest limb/stem p90 0.67, 869 m of branch wood ≥ 1 cm):

| | plot year 30, trees 15.5–19.7 m (29) | 50 (36) | 60 (36) |
|---|---|---|---|
| limbs > 2 cm | 2 (0–2) | 3 (2–5) | 3 (2–5) |
| largest limb/stem p90 | 0.92 (0.18–1.00) | 0.33 (0.18–0.94) | 0.92 (0.22–0.99) |
| branch wood ≥ 1 cm (m) | 9.5 (6–25) | 15 (8–36) | 20 (10–42) |

Medians, with the 10th–90th percentile across trees. Ratios near 1 are browsed trees, where a second replacement leader counts as a limb.

**Stem traces per trunk** (`model_traces_v2.py`, scratch): each tree's stem from one stored keyframe year. Model traces are kept only at the photo trunks' size in the frame, at least 41 % of image height (the Gullmarsskogen 10th percentile). The photo trees' sizes were not measured. Values are median (middle half; 10th–90th percentile) per trunk.

| traces | trunks | off-line % | turning ° | bends | lean ° |
|---|---|---|---|---|---|
| photos, all | 144 | 1.60 (1.07–2.70; 0.40–3.79) | 11.4 (4.6–20.5; 0.3–33.7) | 1 (0–2; 0–3) | 2.2 (1.0–4.1; 0.3–7.7) |
| photos, Gullmarsskogen | 54 | 1.74 (1.25–2.68; 0.70–3.45) | 12.7 (6.6–24.3; 4.8–41.0) | 1 (1–2; 0–4) | 2.1 (1.0–3.7; 0.4–5.7) |
| model 50, no scatter | 156 | 0.41 (0.20–0.69; 0.07–1.00) | 1.0 (0–1.9; 0–3.4) | 0 | 0.9 (0.4–1.4; 0.1–2.1) |
| model 50, 0.5× scatter (4.6 px) | 156 | 0.73 (0.41–1.12; 0.14–1.56) | 2.5 (1.0–6.5; 0–12.4) | 0 (0–1; 0–2) | 0.9 (0.4–1.5; 0.2–2.1) |
| model 50, 1× scatter (9.1 px) | 156 | 1.23 (0.69–1.91; 0.24–2.59) | 6.1 (2.1–14.0; 0–26.5) | 1 (0–2; 0–3) | 1.0 (0.5–1.7; 0.2–2.4) |
| model 60, no scatter | 190 | 0.34 (0.18–0.49; 0.07–0.70) | 0 (0–1.3; 0–2.1) | 0 | 0.7 (0.4–1.2; 0.1–2.0) |
| model 60, 0.5× scatter | 190 | 0.67 (0.38–1.03; 0.13–1.39) | 2.2 (0–6.3; 0–12.0) | 0 (0–0; 0–2) | 0.8 (0.4–1.4; 0.2–2.2) |
| model 60, 1× scatter | 190 | 1.20 (0.67–1.82; 0.24–2.45) | 5.8 (2.0–13.6; 0–25.1) | 1 (0–2; 0–3) | 0.9 (0.4–1.6; 0.2–2.3) |

- Trace lengths: model median 55 % (43–83), Gullmarsskogen 68 % (41–88). Trunk counts are tree copies in the tiled stand (95 trees).
- Even at the upper-bound scatter, the model's stems are straighter (off-line 1.2 against 1.7 %, turning 6 against 13°) and more upright (lean 0.9 against 2.1°) than the photos.
- The earlier close match (phase 17: 1.8 % off-line) came from short model traces: unmatched, the model's traces had a median 24–26 % of image height, against 61–68 % in the photos, and scatter weighs more on short traces.
- The click scatter scale 0.5 is an assumption: half the upper-bound estimate (9.1 px, residual of the 60 traces with 5+ clicks around a quadratic, which also holds real wobble). Measuring it needs the same trunks re-clicked by the same person.

## Phase 25: sapwood turnover back, b refitted by simulation

**Turnover.** Inner wood stops conducting at `sapwood_senescence_per_year` and is replaced by a new ring outside. The old wood stays in the stem (`wood_area`), and the requirement is on the conducting wood (`sap_area`).
- No count of conducting rings was found for birch. The rate is 1 / (rings that conduct) in mature diffuse-porous broadleaves whose sapwood is younger than the tree (Gebauer, Horna & Leuschner 2008, Tree Physiol. 28:1821, Table 1).
  - Those trees conduct through 40–88 rings, median 72, so the rate is 0.014 (0.011–0.025). VERIFY for birch.
  - Their conducting xylem is 62–85 % of basal area.
- Sievänen, Nikinmaa & Perttunen (1997, Silva Fennica 31:329) found that turnover at a fixed ring age and turnover controlled by foliage loss fit Scots pine equally well. The second kind is the crown-rise route (CROBAS, Valentine & Mäkelä 2005), not built.

**Refit.** The whole cross-section now depends on each tree's history. `tools/fit_huber_exponent.py` grows the seed-1 stand tree for each b and reads its leaf area where its DBH passes the data points, with equal weight per dataset: b = 0.312. One exponent cannot match both datasets:
- **Young trees (Konôpka, DBH 2.4–5.4 cm):** the model has 1.4–2.5× their leaf area.
  - The stand tree carries its crown to the ground when young: at year 5, 4.1 of 7.0 m² of leaf are below 1.3 m.
  - Its rings lag the requirement while that grows fastest, at years 4–7.
- **DBH 11 cm (Repola Eq. 12):** the model matches, with 1.15×.
- **DBH 20–26 cm:** the model has 0.6–0.7× Repola's leaf area, because old wood builds up.

**Seed-1 stand tree** (CLI, `--stand`):

| age | H (m) | DBH (cm) | H/D | leaf area (m²) | CUE |
|---|---|---|---|---|---|
| 20 | 13.6 | 15.3 | 89 | 31.7 | 0.51 |
| 30 | 17.2 | 19.9 | 86 | 52.2 | 0.55 |
| 45 | 20.2 | 26.8 | 75 | 71.9 | 0.47 |
| 50 | 21.2 | 28.2 | 75 | 76.5 | 0.46 |
| 60 | 22.6 | 30.1 | 75 | 77.9 | 0.44 |

Heights are inside the band at 45–60. The rings now take carbon that went into extension before. The natural plot has not been run: memory was short.

**Limbs against the 6 Nordic stand scans** (15.5–19.7 m, median): the scans have 58 limbs over 2 cm, a largest limb/stem ratio of 0.67 at the 90th percentile, and 869 m of branch wood at least 1 cm thick.
- The stand tree at 17–19 m (ages 30–40) has 0 limbs over 2 cm and 8–16 m of such wood. In phase 12 the same tree had 2 limbs and 18 m at 20.
- Under the Huber requirement a limb is as thick as its foliage needs. A limb carrying 0.5 m² of leaf is 1.2 cm thick, and one needs ~1.2 m² to pass 2 cm. In phase 12 the model's largest limbs carried 400–900 leaves (0.6–1.4 m²).
- So the deficit is still in how much each limb grows and carries (phase 12), and LIGNUM removed the counted-pipe floor that had kept limbs thicker.

## Phase 24: wood per leaf area fitted to Nordic birch; LIGNUM is the default

**What is built.** In LIGNUM growth, the ring requirement is now on the whole wood cross-section (`pipe_model.sapwood: false`). Birch has no distinct heartwood, so there is no sapwood turnover and no wood is counted twice. Wood per unit of leaf area beyond rises with radius: `huber_value` × (r / `tip_radius`)^b.

The one free quantity, b = 0.279, is fitted at breast height to two datasets at once, each weighted equally (`tools/fit_huber_exponent.py`):
- young trees: Konôpka et al. 2023;
- DBH 11–26 cm: Repola 2008, Eq. 12, at SLA 15 m²/kg.

Marklund 1988 has no birch foliage function. `growth: lignum` is the default, and all 20 tests pass. Two tests changed:
- radius ≥ counted pipes is now checked only in the ring modes;
- the chunked-mesh share of moved fillet vertices is 0.22 % for this shape.

**Result: H/D is not met.** Seed-1 stand tree: H/D 113 at 10, 99–104 at 30–45, 110 at 50 and 119 at 60.

Natural plot, seed 1, compared with the previous `rings` run:

| year | p24 (this phase) | c48m5 (rings, phase 22) | Hagemeier & Leuschner / band |
|---|---|---|---|
| 30 | 1692/ha, DBH 11.5, H 20.3, H/D 177, BA 18.6 | 990/ha, 15.6, 21.3, 137, 20.0 | band H 13.4–19.7 |
| 45 | 1566/ha, 12.2, 26.8, 219, 19.3 | 756/ha, 19.0, 30.6, 162, 22.5 | 880/ha, 19, ~25 m²/ha; band 18–24 |
| 50 | 1566/ha, 12.7, 28.6, 226, 20.5 | 720/ha, 19.9, 32.3, 163, 23.6 | band 19.2–25.3 |
| 60 | killed for low memory at 52 | 630/ha, 21.9, 34.8, 159, 24.9 | 420/ha at 67; band 21.1–26.9 |

**Cause.** The ring now only follows the foliage. With a fixed requirement, πr² = HV0 (r/r_tip)^b × LA, so r ∝ LA^(1/(2−b)). The stem thickens only while the leaf area beyond it grows.
- **Per-tree leaf area stays flat.** In the plot it is 22–24 m² from year 15 to 50: LAI stays at ~3.9, and only 13 of 100 trees die by 45, against 58 in c48m5.
- **Where the carbon goes.** DBH rises 2 cm in 35 years, and the net carbon goes into extension.
- **The model follows the fit.** The trees' leaf area for their DBH matches Repola Eq. 12 (21.9 m² at DBH 12.2).
- **Self-thinning nearly stopped.** Why is not yet diagnosed: it needs the checkpoint, about 3 GB to load.
- **Even at H&L's density, the fit falls short.** At 880/ha and LAI 3.8 it gives DBH ~15 cm, not 19. H&L's stand implies ~6.6e-4 m² of wood per m² of leaf at breast height.
  - That is what Repola's crown-ratio foliage model gives for short crowns. Eq. A6 is ln(foliage) = −20.856 + 22.320 dS/(dS+2) + 2.819 cr: at DBH 19 cm and cr 0.35 it gives ~36 m² of leaf, so ~7.9e-4.
  - Eq. 12 averages over the crown ratios in Repola's sample.

## Phase 23: one carbon pool for shoots and rings (LIGNUM), not yet the default

**What is built.** `pipe_model.growth: lignum`, following LIGNUM (Perttunen et al. 1996). Each year one growth factor λ scales every bud's shoot (λ × its Borchert–Honda share) so that the pool pays for:
- the new shoots' wood (tip cross-section × length);
- their leaves, late and early (built with the shoots; next season they pay maintenance but are not rebuilt);
- the sapwood rings the pipe model needs: `huber_value` of sapwood per unit of foliage beyond, after `sapwood_senescence_per_year` = 0.07 (LIGNUM, Scots pine; VERIFY for birch).

Together these equal the net shoot carbon. The one-unit-per-metamer cost is gone. It is off by default (`rings`), and all tests pass.

**Result: it hinges on sapwood per leaf area along the tree.** Seed-1 stand tree, alpha 4.8:

| Huber value | 10 y | 20 y | 40 y | 60 y |
|---|---|---|---|---|
| 1.24e-4 everywhere (current-year shoots, [OP22]) | H 10.0 m, DBH 5.3, H/D 188 | 19.1, 9.1, 211 | 26.8, 17.6, 152 | 29.7, 22.3, 133 |
| rising with radius to 8.3e-4 at 5 cm (stem base, see below) | 5.8, 12.0, 48 | 9.3, 18.2, 51 | 12.3, 27.6, 45 | 13.3, 36.2, 37 |

The acceptance range is H/D 80–100. Neither profile is sourced along its length.
- **Twig and stem values.** 1.24e-4 is measured at current-year shoots. Birch HV rises towards the base (Sellin & Kupper 2006, Trees 20:311; values not available).
- **Young silver birch, as a whole stem** (natural regeneration ≤ 15 years, Western Carpathians): 2.37 m² of leaf at a base diameter of 50 mm, ~4× that at 100 mm, so ~8.3e-4 m² of stem cross-section per m² of leaf (Konôpka et al. 2023, Plants 12:1607).
- **Double counting.** That is total cross-section. Using it as the sapwood need and adding heartwood on top (senescence 0.07) counts the wood twice. Birch is a sapwood tree with no distinct heartwood.

**Open.** A sapwood-per-leaf-area profile and turnover for birch: either from Sellin & Kupper's crown data, or set so that young trees reproduce Konôpka et al.'s base-diameter to leaf-area allometry (a measured relation, not heights).

## Phase 22: carbon from leaves, early leaves, alpha from sources, stem mechanics

**Carbon comes from leaves, not buds.** Carbon = alpha × Σ (leaf weight × light × stomatal opening), also in each branch's own balance. Leafless dormant buds fix none; a short shoot's cluster counts 2.5 leaves.

**Early leaves.** Long shoots already carried one late leaf per node. They now also bear their 2–3 early (preformed) leaves at their base (Clausen & Kozlowski 1965). An open sapling has 2.1 m² of leaf at 2.75 m and 5.0 m² at 2.90 m; 3–3.5 m FAHM silver birches had ~4.2 m² (root conductance over conductance per leaf area, Sellin et al. 2015).

**Alpha from sources: 4.8** (carbon of one reference leaf in full light per year).
- Source: a 10-year fertile Estonian stand, NPP 13.0 Mg/ha/yr with 2.81 Mg/ha of leaves (Aosaar et al. 2016), LAI 4.2 (SLA 15 m²/kg, Uri et al. 2007).
- At CUE 0.45 that is ~330 g C per m² of leaf, ~1080 model units. The natural plot fixes that at LAI 3.9–4.05 with alpha 4.8.
- Wood maintenance 0.5: CUE 0.42 (target ~0.45, provisional).

**Natural plot at alpha 4.8, before the stem mechanics fix (biomass from the wood geometry at 530 kg m⁻³):**

| age | N/ha | H mean | top 25 % | band | DBH | basal area | aboveground wood |
|---|---|---|---|---|---|---|---|
| 30 | 990 | 21.3 | 25.1 | 13.4–19.7 | 15.6 | 20.0 m²/ha | 106 t/ha |
| 45 | 756 | 30.7 | 32.9 | 18.0–24.0 | 19.0 | 22.5 | 187 |
| 50 | 720 | 32.3 | 34.5 | 19.2–25.3 | 19.9 | 23.6 | 213 |
| 60 | 630 | 34.8 | 36.9 | 21.1–26.9 | 21.9 | 24.9 | 264 |

**Budget or allocation?** Mainly allocation.
- **Girth matches closed silver-birch stands of similar density.** Hagemeier & Leuschner 2019 had 880/ha with DBH 19 cm and ~25 m²/ha at 45, 20–25 m tall.
- **Biomass is at the fertile end**, not far above it. Fertile Estonian Oxalis stands had 224 t/ha at 45 and 220 at 60 (Varik et al. 2011; Uri et al. 2012).
- **Height is ~10 m over, and H/D ~160** (those stands ~110–130).
- **Cause found: the net shoot carbon is counted twice.** The flow hands the whole pool to the buds (new shoots), and the rings are built from the whole pool as well (`wood_volume_per_carbon × _shoot_carbon`). Extension never competes with girth.
- **The metamer unit is not in grams.** It is P09's unit (one metamer, leaf included). Leaves are now charged separately, and a metamer's wood is far smaller than the 0.64 g a unit stands for. Open.
- **The budget is also too large for average Swedish sites**, since alpha comes from the fertile farmland stand. Nitrogen and season length: open.

**The stuck forked leader (step 3), fixed.** Replacement leaders were limbs in the mechanics: they had the pendulous factor (no stiffness or posture correction on thin wood) and the 43° set-point.
- On the seed-1 stand tree, after the year-9 browse, both fork tips drooped (dir_z down to −0.46). One stayed at 4–5 m for 18 years.
- Now the stem axes are orthotropic with the stem's set-point, and the leader grows 8.5 / 23.0 / 32.0 m at 14 / 30 / 45.
- The lone stand tree was only short because of this; it now races too (H/D ~150).

**Natural plot with the stem fix** (stopped by the low-memory guard at 55; stand means from the last checkpoint):

| age | N/ha | H mean | H max | DBH | LAI |
|---|---|---|---|---|---|
| 30 | 1278 | 22.6 | 26.0 | 14.6 | 4.01 |
| 45 | 864 | 31.0 | 34.9 | 18.8 | 3.97 |
| 50 | 828 | 32.8 | 37.6 | 19.6 | 3.94 |
| 54 | 720 | 34.7 | 39.7 | 20.8 | 3.94 |

LAI is ~4.0, close to the measured 4.6.

**Dense regeneration (one per m²) still does not close at 4–5 years.** LAI is 0.09 at 5 and 0.96 at 8; the median seedling is 0.04 / 0.28 / 0.52 m at 2 / 4 / 5.

## Phase 21: water through the fine roots, the field layer on bared soil

**Water uptake through the fine roots the tree pays for.**
- Fine-root length = fine-root mass (0.48 × leaf mass) × specific root length (90 m/g; silver birch short roots 80–97, Ostonen et al. 2007).
- Conductance per metre: 1.7e-7 kg s⁻¹ MPa⁻¹, from the root-system conductance of young silver birch (4.33e-4 kg m⁻² s⁻¹ MPa⁻¹ per leaf area) with 0.46 g fine root per g leaf in the same trees (Sellin et al. 2015), at the model's reference LMA.
- No calibrated value remains.
- In the plots the trees are no longer water-limited: stomata are 1.00 / 0.95 / 0.85 open at 30 / 45 / 60 (0.76 / 0.70 / 0.66 in phase 20).

**Field layer.** It is absent on bared mineral soil and grows back with a half-life of 4 years (Ring & Sikström 2024; VERIFY form).
- The first cohort grows on ground bared at year 0.
- Recruits are drawn on mineral soil or the organic layer in proportion to establishment.
- Sunny-gap seedlings grow 0.07 / 0.16 / 0.29 / 0.48 / 0.77 / 1.21 / 1.88 / 2.81 m at 1–8 years (1.24 m at 10 under a uniform field layer).
- Seedlings now get carbon in their first season, because uptake is set from that season's fine roots.

**Dense regeneration does not close its canopy at 4–5 years.**
- At one seedling per m² on bared ground: LAI 0.05 at 5 years, 0.64 at 8 (ground light 80 %), median height 0.42 m at 5.
- Without the field layer LAI was 0.17 at 5; without the leaf costs, 0.10.
- So neither is the cause: young trees carry too little leaf (a 0.8 m sapling has ~0.02 m², about a dozen leaves).
- For comparison, the FAHM silver birches were 3.0–3.5 m tall at ~4 years (planted on fertile former farmland; Sellin et al. 2015). Open.

**Alpha 6.2 → 5.2.** At 6.2 the natural plot's top quarter was 4–5 m above the band (31.4 m at 60). At 5.2:

| plot | age | N/ha | H mean | top 25 % | band | DBH | crown ratio | crown base | LAI | stomata |
|---|---|---|---|---|---|---|---|---|---|---|
| natural | 30 | 972 | 14.6 | 20.1 | 13.4–19.7 | 12.3 | 0.81 | 3.2 | 3.39 | 0.96 |
| | 45 | 612 | 20.5 | 25.0 | 18.0–24.0 | 16.2 | 0.63 | 8.1 | 3.26 | 0.93 |
| | 50 | 540 | 22.6 | 25.8 | 19.2–25.3 | 17.8 | 0.60 | 9.5 | 3.21 | 0.94 |
| | 60 | 522 | 24.0 | 27.0 | 21.1–26.9 | 19.0 | 0.54 | 11.4 | 3.35 | 0.90 |
| managed | 30 | 450 | 18.0 | 20.9 | 13.4–19.7 | 16.8 | 0.83 | 3.2 | 3.21 | 1.00 |
| | 45 | 432 | 22.7 | 25.3 | 18.0–24.0 | 18.9 | 0.71 | 7.0 | 3.34 | 0.95 |
| | 50 | 432 | 23.7 | 26.1 | 19.2–25.3 | 19.5 | 0.63 | 9.1 | 3.18 | 0.93 |
| | 60 | 414 | 25.4 | 27.3 | 21.1–26.9 | 20.8 | 0.58 | 10.8 | 3.20 | 0.88 |

- Mean heights are in the band. The top quarter is 0.1–1.3 m above its upper edge, as in phase 15.
- **CUE:** 0.37 natural, 0.40 managed.
- **A short shoot breaks even at ~26 % light** (21 % measured).
- **Stems** (noise-matched; photos off-line 1.60 %, turning 11.4°, lean 2.2°): natural 1.83 % / 8.6° / 2.6°, managed 1.80 % / 8.2° / 2.7°.
- **Natural density at 60 is 522/ha.** The closed silver-birch stands of Hagemeier & Leuschner 2019 had 880/ha at 45 and 420/ha at 67, so ~570/ha at 60. Phase 17 had 585/ha and phase 20 972/ha.
- **Ground light is 32 % at LAI 3.27 (natural, 55).** At alpha 6.2 it was 28 % at LAI 3.66. Lower alpha lowers both LAI and CUE.

**The 8-year regeneration test** (natural plot from 55, alpha 5.2):
- **Recruits:** 546 in the first year, every free cell, all on bared mineral soil. Bared soil is 3.1 % of the ground, but 6,500 seeds/m² still give ~36 one-year seedlings per m². None recruited under the field layer, where 32 % × 0.38 ≈ 12 % light is below 21 %.
- **Survival: 100 % after 7 seasons,** at 0.08 m. Published: ~20 % of paper birch germinants after 5 years; >50 % for mountain birch at 1–2 years; silver birch does not persist under a closed canopy.

**Cause: leafless buds fix carbon.** Carbon is alpha × the light of every bud, whatever leaves it carries. A dormant bud has leaf weight 0 yet earns alpha × Q, and a short shoot's 2.5 leaves count as one.
- A shaded recruit's income grows with its bud count (1 → 5 buds: 1.4 → 4.5 units).
- Its light falls (0.26 → 0.17) and its leaf costs stay flat, so it is never in deficit.

**Open: carbon per leaf.** Fixing this (carbon = alpha × leaf weight × light, for the tree and in each branch's balance) is saved as a patch, not applied.
- The canopy's carbon roughly doubles (short shoots carry 2.5 leaves), and the stand tree's CUE goes to ~0.6.
- It needs a full recalibration of alpha and maintenance.

**A stem bug it exposed:** a replacement leader (a lateral that took over after browsing) counts as a branch for the shedding rules. In a dense crown its leaf-weighted mean light can fall to the 21 % threshold, and the whole crown above it is shed (seed-1 stand tree, year 34). Fixed separately.

## Phase 20: leaves and fine roots cost carbon

### Step 1: leaf and fine-root costs

Leaves and fine roots were free. Every year each tree now pays (`resource.leaf_costs`):
- **Rebuilding its leaves:** this season's leaf dry mass (leaf area × LMA), plus growth respiration.
- **Leaf maintenance:** 0.79 g C per g per year (Oleksyn et al. 2000; season and temperature VERIFY).
- **Fine-root maintenance:** 0.93 g C per g per year (Ryan, Lavigne & Gower 1997), for fine roots weighing 0.48 of the leaves (Aosaar et al. 2016).

Grams are converted to model units through the wood the unit builds (1.2e-6 m³ at 530 kg m⁻³, so 0.64 g). Each branch's carbon balance also counts its own leaves.

**CUE 0.47 cannot be kept.** Leaf and fine-root respiration plus growth respiration take ~45 % of the fixed carbon on their own.
- Wood maintenance went 0.7 → 0.2, now ~10 % of the fixed carbon.
- The plots' CUE (all tree-years from age 20) is 0.38–0.40, as before (0.38–0.41).
- That is within the published 0.40–0.52 (boreal at the low end), at its edge.
- The weakest input is the leaf respiration's measurement temperature, which is not stated in the source.

**Death rule.** At first a tree died in its first deficit year, before it could shed the branches that did not pay. The natural plot lost 96 of 100 trees by 35. A tree in deficit now sheds its starving branches before the next flush, and dies only if it is still in deficit the next year. The plot also no longer crashes when its last tree dies.

**Alpha 5.6 → 6.2.**
- At 5.6 the managed plot's mean height fell just under the band at 60 (21.0 m), with crowns down to 1.9 m.
- At 7.0 the top quarter was 1–3 m above the band.
- At 6.2 a short shoot's leaves break even at ~22 % light, against the measured 21 % of the lowest birch leaves.

**Plots at 6.2** (seed 1; before = the phase-17 runs; band from Eriksson et al. 1997):

| | age | N/ha | H mean | top 25 % | band | DBH | crown ratio | crown base | LAI |
|---|---|---|---|---|---|---|---|---|---|
| managed, before | 30 | 450 | 19.6 | 21.2 | 13.4–19.7 | 18.3 | 0.81 | 3.9 | 3.61 |
| | 50 | 450 | 24.5 | 26.2 | 19.2–25.3 | 20.6 | 0.66 | 8.2 | 3.66 |
| | 60 | 450 | 25.9 | 27.3 | 21.1–26.9 | 21.6 | 0.64 | 9.4 | 3.70 |
| managed, now | 30 | 450 | 18.7 | 20.4 | 13.4–19.7 | 19.9 | 0.74 | 5.0 | 3.15 |
| | 50 | 450 | 22.7 | 24.1 | 19.2–25.3 | 21.2 | 0.72 | 6.4 | 3.12 |
| | 60 | 450 | 24.0 | 25.2 | 21.1–26.9 | 21.6 | 0.75 | 6.0 | 3.12 |
| natural, before | 30 | 1170 | 17.2 | 20.5 | 13.4–19.7 | 14.1 | 0.73 | 5.0 | 3.77 |
| | 50 | 765 | 23.4 | 25.5 | 19.2–25.3 | 17.4 | 0.60 | 9.7 | 3.62 |
| | 60 | 585 | 25.6 | 26.9 | 21.1–26.9 | 19.5 | 0.45 | 14.1 | 3.69 |
| natural, now | 30 | 1206 | 16.8 | 20.1 | 13.4–19.7 | 14.8 | 0.63 | 6.5 | 3.06 |
| | 50 | 1080 | 18.9 | 24.1 | 19.2–25.3 | 14.8 | 0.60 | 8.1 | 2.95 |
| | 60 | 972 | 20.0 | 25.3 | 21.1–26.9 | 15.3 | 0.62 | 8.2 | 2.95 |

**Stem metrics** (noise-matched, 4.6 px), now against before (photos: off-line 1.60 %, turning 11.4°, lean 2.2°):
- natural: off-line 1.89 % (1.68), turning 8.5° (7.5), lean 1.9° (2.0);
- managed: off-line 1.86 % (1.79), turning 8.4° (7.6), lean 2.6° (3.1).

**Still off:**
- The natural plot self-thins less (972/ha at 60, against 585 before).
- Its deaths: 35 of carbon deficit, 10 of no carbon, 1 failed to establish.
- LAI fell from ~3.7 to ~3.0–3.1.
- The managed crown base is 6 m at 60, against 9.4 m before.

### Step 2: ground light (diagnosis; the fix is open)

**The light model is not the cause.** Ground light (median over the plot, at 0.1 m) follows Beer–Lambert at the plot's own LAI to within ~2 points:

| plot | LAI | ground light | exp(−0.37 × LAI) |
|---|---|---|---|
| natural, phase 17 | 3.65 | 27.9 % | 25.9 % |
| natural, step 1 | 2.95 | 35.5 % | 33.5 % |
| managed, step 1 | 3.16 | 33.1 % | 31.1 % |

**Stems and branches.** Hagemeier & Leuschner took K_PAR = 0.37 from measured transmission against litter-trap (leaf-only) LAI. Woody shade is therefore already in K, and adding it would count it twice.

**The cause is leaf area.** Their stands measured 14.8 % at LAI 4.6. A canopy keeps leaves down to ~21 % light, which at K = 0.37 means LAI ≈ 4.2. The model's canopy stops near 33–35 %. Estonian silver-birch stands span LAI 2.5–4.4 (Uri et al.).

**Branch carbon balance limits the model's LAI.** From the managed year-55 checkpoint, 5 years:
- with it switched off, LAI climbs 3.1 → 3.55 and is still rising;
- with the 21 % light-per-leaf rule switched off, nothing changes.

**The starving branches are well lit.** Bud light is 0.40 (median), and they are order-2 limbs with ~33 buds at ~18 m. Fully watered, their own carbon would be 59 units against 7 (wood) + 34 (leaves). They starve because the trees are water-limited:

| | stomatal opening at 30 / 45 / 55 | root share at 55 |
|---|---|---|
| managed, phase 17 | 0.91 / 0.83 / 0.79 | 0.32 |
| managed, step 1 | 0.76 / 0.70 / 0.66 | 0.37 |

**Chain:**
1. Fine-root maintenance (step 1) comes out of the root share, which halves root building (~0.1 of the fixed carbon against ~0.2).
2. Root length per carbon (`root_segments_per_unit`, VERIFY) and uptake per root length were tuned when roots were free, so water uptake falls.
3. The stomata close, branches lose a third of their carbon, the well-lit limbs are shed, and LAI falls.

**Open.** The fix is to re-tune what the roots buy per unit of carbon, for which no source has been found. One option: let water uptake come from the same fine-root mass the tree now pays for (0.48 of leaf mass, via specific root length).

### Step 3: the field layer is on

`ground_vegetation` in the environment: LAI 2.5, height 0.5 m, extinction 0.43. Source: Aubin, Beaudet & Messier 2000, under 70-year white-birch stands.
- Understory LAI was 2.52, mostly below 50 cm, with k = 0.43 in the 5–50 cm stratum.
- Its transmission did not depend on the light reaching it.
- Quebec *Betula papyrifera* stands: VERIFY (transfer).

**Seedlings in the open.** With the field layer, a germinant at ~5 cm gets ~38 % light. Its tip can then afford 0.9–1.0 metamers a year, and under the 1-metamer rule it never grew (5 seeds, 8 years: 0 m). Seven tests failed at this step.

### Step 4: continuous tip extension

An axis tip now extends by l0 × v at any v ≥ `min_tip_extension` (0.1 metamer, 2.8 mm; VERIFY, a resolution floor). Below one metamer it makes a single shorter internode. The 3-metamer gate for lateral buds (long against short shoots) is unchanged. All 20 tests pass.

**Seedlings in the open with the field layer, median of 5 seeds (m):**

| year | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
|---|---|---|---|---|---|---|---|---|---|---|
| height | 0.02 | 0.05 | 0.09 | 0.14 | 0.21 | 0.30 | 0.43 | 0.62 | 0.77 | 1.24 |

Without the field layer (step 1) they were 0.08 / 0.22 / 0.45 / 0.82 / 1.39 m at 1–5 years.

**What it should be.** No sourced first-years height curve has been found; `reference.height.years_to_breast_height` = 4 is VERIFY. Dense natural birch regeneration closes its canopy at 4–5 years (Forests 12:599, 2021, citing Hynynen et al. 2010), which needs seedlings well over 1 m by then.

**The plots.** The run (field layer + continuous extension) was stopped by the low-memory guard at year 20–25. The first cohort was ~7 years behind: the tallest tree was 1.7 m at 10 and 12.3 m at 20, against 7.8 m and 18.3 m without the field layer.

**Likely cause.** The field layer is uniform. Birch establishes mainly where the ground was disturbed: bare mineral soil gives 18 % one-year seedlings per seed against 0.3 % on humus (Dahlgren Lidman et al. 2023), and there the field layer is absent at first and grows back. Open, needs a decision: tie the field layer to exposed mineral soil and its recovery.

## Phase 19: seedlings on stones, the no-carbon death, regeneration (first version)

**The 9 seedlings that never grew** (phase 18) had three causes, now fixed.
- **Stones reached the surface everywhere.** Stones now lie below a stone-free organic layer of 6 cm (4–10 cm on mesic till, Larson et al. 2023, Sci. Rep. 13:14909). They reach the surface only on `surface_stone_cover` of the ground (2 %, VERIFY).
- **A root tip meeting a stone tried three random deflections and then stopped.** It now turns sideways along the stone by the smallest turn that clears it: 30°, 60° or 90°, towards any of 8 sides (Massa & Gilroy 2003, Plant J. 33:435).
- **A tree with no absorbing root got a token uptake conductance of 1e-12.** It could fix a trickle of carbon forever. It now gets none: no water, no carbon.

**Death rule.** In either plot mode, a tree that fixes no carbon two years running dies. In its first 5 years this is logged as "failed to establish".

**Natural plot, seed 1, at 15 years:**
- All 9 seedlings now establish and grow to 6.0–11.0 m.
- Deaths: 1 of carbon deficit (year 14), 1 failed to establish (on a surface stone, year 3).
- The 97 trees alive in both runs moved by 0.15 m on average against the first reference.

**Regeneration** (`treegen/regeneration.py`; `tools/plot.py --regeneration`; values in `regeneration:` in the species YAML) works as follows:
- **Seed rain** from every tree past `maturity_years`, falling off with distance.
- **One-year seedlings per seed** depend on the seedbed: exposed mineral soil or the organic layer.
- **Light:** germinants below the 21 % light at which birch leaves die are lost.
- **Recruits:** at most one per 1 m cell per year, grown on as full trees.

Short test: the 55-year natural plot (13 trees, 585/ha), resumed and run 8 years with regeneration.
- **Seed rain** was 7,500–8,000 seeds/m² a year. Liu & Evans 2021 report up to 2,000–9,600 within 40–50 m of a seed tree.
- **Ground light** was 25–29 % everywhere under the 60-year canopy. That is above 21 %, so every free cell recruited in the first year: 212 recruits on 222 m². None followed, because every cell was then occupied.
- **Survival:** all 212 were alive after 7 seasons, at a median height of 0 m (max 0.18 m).
- **Published survival:**
  - paper birch on Alaskan clear-cuts: about 20 % of first-year germinants alive after 5 years (USDA Silvics);
  - mountain birch in Iceland: over 50 % after 1–2 years (Óskarsdóttir et al. 2025, Ecol. Appl. 35:e70115);
  - silver birch is shade-intolerant, and its seedlings do not persist under a closed canopy.

**Causes, open:**
1. **A shaded seedling never extends and never dies.** Its bud gets about 1.5 carbon units a year, and a long shoot needs 3. So it stays a single short shoot. It has no wood and so pays no upkeep, and it still fixes carbon, so neither death rule applies.
2. **Nothing shades seedlings below the canopy.** The field layer (herbs, grasses, dwarf shrubs) is off by default.
   - With it on, a seedling under 27 % canopy light would get about 7 % at 5 cm and lose its leaves.
   - But a seedling in full light would get only about 25 %, also short of a long shoot. So the field layer alone would stop all regeneration, the first cohort included.
3. **Browsing of small seedlings (voles, hares) after their first year** is not modelled. No source has been found yet.

**Not yet modelled:** old-age death, uprooting (root plates exposing mineral soil), and variation in the seed crop between years.

## Phase 18: speed (shared soil, compiled tree passes)

The workloads are timed one at a time on the same machine, one run each:
- a natural plot, seed 1, to 15 years (`tools/plot.py --no-mesh`);
- one stand tree to 30;
- 3 plot years from age 55 (resumed from a checkpoint).

| change | plot to 15 | stand tree to 30 | plot years 55–58 |
|---|---|---|---|
| before | 280 s (peak 1.8 GB) | 9.8 s | 31.8 s |
| 1. one shared soil per plot | 129 s (0.9 GB) | 9.6 s | 30.1 s |
| 2. bending and posture compiled | 79 s | 7.2 s | 19.8 s |
| 3. subtree sums compiled | **61 s** | **6.2 s** | **16.0 s** |
| overall | 4.6× | 1.6× | 2.0× |

**Change 1, the shared soil, changes results.** Before it, every tree in a plot rebuilt the whole plot's soil grid every year with its own seed, so the trees did not share stones or rootable depth.
- At 15, the 91 trees that grew in both runs moved by +0.2 % in mean height and +1.3 % in mean DBH (0.22 m per tree on average).
- Single trees are untouched (bit-identical).
- Part of change 1's 2.2× comes from 9 trees that no longer grow (below). Without them it is about 2×.

**Changes 2 and 3 do not change results.** Every array of every timeline and every per-year statistic is bit-identical to the run before each change. The numba kernels repeat the numpy expressions operation for operation.

**Seedlings on a stone never establish, and never die.** This is open.
- With private soils every stem sat on the corner of four stone cells, so the radicle always found a stone-free cell.
- In the shared soil 13 of 100 stems start above a stone (the top-soil stone fraction is 8–10 %). In 9 of them the radicle cannot get past it, and the tree stays at 0 m.
- The natural-mode death rule (carbon below upkeep) never removes these trees, because both are zero. They lower plot means (mean height at 15: 8.51 → 7.71 m with them included).
- A seedling that cannot root should fail to establish. This needs a rule before natural regeneration is added.

## Phase 17: noise-matched traces, stem gravitropism refitted on the plot

**Fair comparison.** The model's projected stems are now clicked like the hand traces:
- each trunk gets a click count drawn from the 144 hand traces (2–9, median 4);
- each click gets Gaussian scatter;
- each result is the mean of the medians over 60 random repeats.

**Scatter estimate.** The hand-trace scatter is estimated from the 60 traces with 5 or more clicks, as the residual around a quadratic: median 0.5 % of image height, which is 9.1 px on the render. This is an upper bound, because it includes real wobble and wobblier trunks got more clicks. The central case is half of it, 4.6 px.

**Fit.** Stem gravitropism was fitted on the natural plot (13 trees at 60) against lean, max off-line and total turning together. The loss is the sum of squared relative errors against the photos' medians:

| scatter | 1/m | 2/m | 3/m | 4/m |
|---|---|---|---|---|
| 2.3 px | 0.65 | **0.41** | 0.61 | 0.98 |
| 4.6 px | 0.81 | **0.14** | 0.20 | 0.41 |
| 9.1 px | 1.93 | 0.52 | 0.38 | **0.35** |

- The stem gravitropism is now 2/m (a convergence length of about 0.5 m), which is best at the central and low scatter.
- Heights are unchanged and in the band. The mean is 23.4 / 25.6 m at 50 / 60 in the natural plot and 24.5 / 25.9 m in the managed plot, against a band of 19.2–25.3 / 21.1–26.9 m.

**Noise-matched, 4.6 px** (medians, middle half in brackets):

| | Gullmarsskogen (54) | all photos (144) | natural 4 / 1 / 2 per m | managed 4 / 1 / 2 per m |
|---|---|---|---|---|
| max off-line, % | 1.7 (1.3–2.7) | 1.6 (1.1–2.7) | 1.3 / 2.7 / **1.7** (0.9–2.6) | 1.4 / 2.4 / **1.8** (1.0–2.6) |
| total turning | 12.7° (7–24) | 11.4° (5–21) | 6.1 / 10.7 / **7.5°** (3–15) | 6.6 / 10.5 / **7.6°** (4–16) |
| bends per trunk | 1 (1–2) | 1 (0–2) | 0.9 / 1.0 / **1.0** (0–2) | 1.0 / 1.0 / **1.0** (0–2) |
| mean bend | 8.5° | 8.4° | 6.8 / 7.9 / **7.0°** | 6.8 / 7.8 / **7.0°** |
| lean | 2.1° (1.0–3.7) | 2.2° (1.0–4.1) | 1.3 / 3.6 / **2.0°** (1.0–3.2) | 1.7 / 5.0 / **3.1°** (1.6–4.9) |
| forked | 0 % | 2 % | 0 / 0 / 7 % | 0 / 9 / 0 % |

- With scatter matched, the phase-15 stems (4/m) were already 80 % of the photos' off-line value and half their turning. The perfect-click comparison overstated the gap (0.5 % and 1°).
- At 2/m, off-line, bends and the natural plot's lean match.
  - Turning is still a third low (7.5° against 11.4°), but this depends on the scatter: at the 9.1 px upper bound the model gives 13.5°.
  - Lean in the managed plot overshoots (3.1°).

**Top breakage: no sourced rate.** No annual rate of snow or wind top breakage in Nordic birch was found:
- Donis et al. 2024 (*Forests* 15:275), young hemiboreal birch in Latvia: one freezing-rain and snow event damaged 31.0 % of trees.
  - 93.7 % of the damaged trees were bent, so only about 2 % were broken or uprooted.
  - After one season, 31.3 % had less bending and 8.2 % more. There is no return rate.
- Díaz-Yáñez et al. 2016 (*PLoS ONE* 11:e0161361), the Norwegian national forest inventory 1995–2014: birch was the most snow-resistant species. No breakage share is given for birch.
- *Snow damage to birch stands in Northern Moravia* (*J. For. Sci.* 2012): bending was predominant and breakage was at most 4 % of trees (not Nordic).
- Valinger & Fridman 1999 (*Environ. Manage.*): paywalled, not read.

Nothing was added. The documented damage in young birch is snow bending followed by partial recovery, not breakage, and it has no sourced frequency either.

## Phase 16: why the stems were straight

**Stem over time** (stem sections grown at ages 0–5, 5–10, 10–20 and 20–30, measured every 5 years to 60, 6 trees per plot):
- At the multi-metre scale, bends never formed. Each section was laid down almost straight (offset 0.02–0.07 %, turning 0.3–0.5°), then sagged slowly (to 0.4–0.9 % by 60). There were no bends of 4° or more at any age.
- Consecutive 5-year sections left the leader within 0.5–0.6° of each other (p90 1.2–3.7°), also when a neighbour within 3 m died (23 % of sections).

**Annual sympodial kinks** (seed 1, yearly):
- They form at 9.5° (median; p90 18°) and are straightened to 7.8 / 4.6 / 2.8 / 2.3 / 2.0° after 1 / 2 / 3 / 5 / 10 years. With posture control off they stay at 12–17°.
- The correction is within physics. It uses 1 / 11 / 15 / 7 % of what the new ring allows (C·Δr/r², Alméras & Fournier), at joint radii of 0.45 / 0.89 / 1.34 / 2.08 cm. Sections thicker than 2 cm already keep their shape (0.3° a year).
- These kinks are 0.6 m features in random directions, invisible to 4-click traces. Limiting the correction would change nothing there.

**The cause: the leader could not change course.**
- Leader gravitropism of 4 per m (no source) brought a deflected leader back on its target within 0.25 m of growth.
- Against phototropism of 0.8 per m, the leader could turn toward light by at most ~11°, typically 1–3°, and only for as long as the light stayed one-sided.
- Leader changes come only from browsing at 0.3–3 m. No sourced rates exist for top breakage higher up.

**Fix.** Stem gravitropism 4 → 1 per m (a ~1 m convergence length), and replacement leaders now use the stem's tropisms. (Refitted to 2/m on the plot in phase 17.)
- Calibrated on one observable, the lean of single stand trees (seeds 1–3 at 40: 0.8 / 1.6 / 2.1 / 2.6° at 4 / 2 / 1 / 0.5 per m; photos 2.1–2.2°). Height unchanged.
- In the plots, 5-year sections now change course by 1.6–1.8° (p90 3.7–5.0°), and bends develop over the years (offsets 1.3–1.7 % and 6–9° of turning by 60).

**Against the 144 hand traces** (4 clicks, `tools/stem_metrics.py`):

| median | Gullmarsskogen | all photos | natural before / after | managed before / after |
|---|---|---|---|---|
| max off-line, % | 1.7 | 1.6 | 0.5 / 2.2 | 0.7 / 1.8 |
| total turning | 13° | 11° | 1 / 7° | 2 / 6° |
| bends per trunk | 1 | 1 | 0 / 1 | 0 / 1 |
| mean bend | 8.5° | 8.4° | – / 6.3° | – / 6.9° |
| lean | 2.1° | 2.2° | 1.2 / 3.5° | 1.7 / 4.9° |
| forked | 0 % | 2 % | 0 / 0 % | 0 / 9 % |

- Off-line and bends are now in the photos' range; total turning is about half.
- Lean overshoots in the plots (3.5–4.9° against 2.1–2.2°), although it matched in the single-tree stands it was calibrated on. Plot trees grow next to real, uneven neighbours.
- Plot heights stay in the Swedish band (mean 19.6–19.7 / 23.4–23.5 / 25.2 m at 30 / 45 / 60).

## Stem straightness: hand traces against the model

- **Hand traces:** 144 trunks hand-traced with the Birch Stem Tracer (`tools/birch-stem-tracer.html`, served by `tools/serve_tracer.py`) on 23 photos: 54 trunks on the three Gullmarsskogen stand photos, 90 on iNaturalist whole-tree photos. Median 4 clicks per trunk; traces in `reference/stem_traces.json`.
- **Model:** the stems of the phase-15 plots, projected through the same camera as the photo-matched render and selected as the tracing instructions say (base in frame, not touching the edges, at least 15 % of the image height). Measured with the tool's own code (`tools/stem_metrics.py`), resampled to 4 evenly spaced clicks per trunk.
- Medians (middle half); bend threshold 4°:

| | Gullmarsskogen (54) | all photos (144) | natural plot (13 trees) | managed plot (10 trees) |
|---|---|---|---|---|
| max off-line, % of length | 1.7 (1.3–2.7) | 1.6 (1.1–2.7) | 0.5 (0.3–0.8) | 0.7 (0.4–1.0) |
| total turning | 13° (7–24) | 11° (5–20) | 1° (0–2) | 2° (1–3) |
| bends per trunk | 1 (1–2) | 1 (0–2) | 0 (0–0) | 0 (0–0) |
| mean bend | 8.5° | 8.4° | – | – |
| lean from vertical | 2.1° | 2.2° | 1.2° | 1.7° |
| forked | 0 % | 2 % | 0 % | 0 % |

- **Click scatter does not explain it.** A perfectly straight stem traced with 4 clicks of 2 / 4 / 6 px scatter measures 0.35 / 0.68 / 1.07 % off-line and 0 / 2 / 5° turning, with no bends.
- **The model's stems are 2–3× straighter than real birch and have no bends of 4° or more.** The traced model trunks are tiled copies of 13 and 10 trees.
- *Phase 17:* with the hand traces' own scatter added to the model's clicks, most of this gap was click scatter (see above).
- **Candidate causes**, the tool's list, not yet tested:
  - posture control correcting too fully;
  - too few leader changes;
  - light that does not shift as neighbours die.

## Phase 15: twig packing, short shoots, sub-branches

**Why twigs packed** (seed 1 at 15 and 25 years, second-order leafy buds):
- **Not the light grid.** Only 14–18 % of a twig bud's shade comes from its own 10 cm layer; reading the shade one voxel up raised bud light only from 0.29–0.33 to 0.31–0.38.
- **Not internode length.** Internodes are 2.5–3.1 cm on all orders, the birch value.
- **The long-shoot gate.** At 1 metamer (phase 14) every bud that could afford one or two metamers made a 1–2-node long shoot. That gave 12× as many third-order shoots and doubled the local leaf density (3.8 → 7.3 m² m⁻³ within 0.25 m).
- The gate is back at 3: birch laterals make either a short shoot or a long shoot of several nodes. Second-order shoots then survive (99 % after 5–8 years, against 53 %). But they stay small: 0.054 m² of leaf and 0.51 cm at 12 years.

**Why sub-branches stayed small.**
- Short shoots were sinks in the Borchert–Honda split: 73 % of the shoot resource went to them and was lost (years 15–30). The tips of sub-branches got almost nothing after their first year.
- Short shoots are now self-financing (`bud_fate.short_shoots_self_financing`, [M82]): they fix carbon with their own leaves and draw nothing. Release of short shoots into long shoots, uncommon in birch, no longer happens.
- Also tried: excluding every bud that will not grow from the split (`idle_buds_no_sink`). All resource then went to growing buds, and leaders raced ahead of their stems (whips, H/D ~190; CUE 0.34). Off.
- Heights left the band with the change, so `alpha` went 6.6 → 5.6.

**Managed plot (40 → 10 trees at 450/ha), limbs against the 6 Nordic scans** (scan counts are an upper bound: QSM overestimates thin branches, Demol et al. 2022, Silva Fennica):

| | scans, 15.5–19.7 m | phase 14 (gate 1), 30 y / 17.4 m | phase 15, 30 y / 20.1 m | phase 15, 60 y / 26.2 m |
|---|---|---|---|---|
| branches ≥ 1 cm, order 1 / 2 / 3 | 68 / 440 / 826 | 120 / 18 / 0 | 94 / 1 / 0 | 26 / 28 / 10 |
| sub-branches ≥ 1 cm per limb > 2 cm | 6.8 | 0.71 | 0.13 | 8.0 |
| limbs > 2 cm | 58 | 30 | 16.5 | 4 |
| largest limb / stem diameter, p90 | 0.67 | 0.29 | 0.28 | 0.64 |
| leaf area per second-order branch at 60 (median) | – | 0.013 m² | – | 0.094 m² |

- At 60 the limbs branch like the scans: 8 sub-branches ≥ 1 cm per limb, limb/stem ratio 0.64, crowns of a few large limbs.
- At the scans' height (20 m, year 30) the sub-branches have not thickened yet: they reach 1 cm about 30 years later than in the scanned trees.

**Natural plot at 60** (same setup): 585/ha (27 of 40 died); DBH 18.9 ± 3.4 cm; mean height 25.6 m, top quarter 27.0 m; LAI 3.72.
- Sky fraction 27 / 40 / 62 / 68 % at 5–15 / 15–25 / 25–35 / 35–45°, against the photos' 12–14 / 37–49 / 45–61 / 60–68 %. Phase 14 had 16 / 46 / 67 / 73 %.
- Crowns spread on longer limbs with fewer twig clusters.
- The low band is more open than the photos because the stand has fewer stems. Stems are still uniform grey.

## Phase 14: respiration, limb branching, whips and junction bulbs

**Respiration** (`resource.maintenance_per_internode`, `growth_respiration_coefficient`).
- Growth respiration: 0.25 g C per g C built (Ryan 1991; VERIFY).
- Maintenance is paid from the tree's pool before allocation. Charged along the flow instead (P09/LIGNUM), a realistic rate drained long limbs: 73 % of limb tips got under one metamer.
- Wood rings, shoots and roots are built from what remains.
- Calibrated to a carbon use efficiency of ~0.47 (Waring et al. 1998: 0.47 ± 0.04; Collalti & Prentice 2019: 0.46 ± 0.12): maintenance 0.02 → 0.7 per internode.
- `alpha` re-tuned 4.6 → 5.8 to the Swedish height curves it was tuned to before, now as gross carbon.
- Seed 1 stand: mean CUE 0.45–0.50 over 20–60, with a basal fork. Young growth is slower and the canopy closes later, so a fully lit low limb keeps up with the leader.

**Natural plot at 60, before and after** (40 trees at 1800/ha on 222 m², seed 1, every default on):

| | before | after |
|---|---|---|
| stems/ha | 1575 (5 of 40 died) | 810 (22 died) |
| DBH | 19.7 ± 8.8 cm, CV 45 % | 20.0 ± 3.5 cm, CV 18 %, Gini 0.10 |
| height mean / tallest quarter / max | 25.7 / 33.9 / 35.8 m | 18.7 / 20.9 / 22.2 m (band 21.1–26.9) |
| crown base | 8.5 m (0.29 H) | 5.5 m (0.28 H) |
| LAI | 4.33 | 3.80 |
| sky fraction 5–15 / 15–25 / 25–35 / 35–45° | 6 / 14 / 35 / 47 % | 16 / 46 / 67 / 73 % (photos 12–14 / 37–49 / 45–61 / 60–68 %) |
| forked / crooked at 60 | 0 / 31 % | 28 / 11 % (crown); 0 on the bole |

- Self-thinning now works.
- Overgrowth is gone; heights are now slightly low (mean below the band).
- Low limbs are not killed: relative crown base unchanged.
- The "1.3 m survivor" of phase 13 was a browsed tree 3.4 m tall whose stem record broke at the leader change, so it had no DBH. None is left.

**Limb branching against the 6 Nordic scans** (the managed plot, as the scans are probably managed stands; plot trees at 17.4 m, year 30):

| | scans | managed plot before (age 20) | managed plot after |
|---|---|---|---|
| branches ≥ 1 cm, order 1 / 2 / 3 | 68 / 440 / 826 | 60 / 23 / 0 | 120 / 18 / 0 |
| bifurcation N1/N2, N2/N3 | 0.18, 0.52 | 2.6, 23 | 6.3, 18 |
| sub-branches ≥ 1 cm per limb > 2 cm | 6.8 | 0.9 | 0.7 |
| limbs > 2 cm | 58 | 27 | 30 |
| largest limb / stem diameter, p90 | 0.67 | 0.32 | 0.29 |

- The long-shoot gate was not the cause. At 3 metamers (no source) it turned 42 % of the fresh lateral buds on limbs into short shoots. It is now 1, as in P09, and the gap did not close.
- The cause is shedding: of 112 k second-order shoots made by year 25 in the managed plot, 80 % died, at a median of 2 years. The survivors are 0.35 cm thick at 30; 1 % reach 1 cm.
- They die by the light and carbon tests inside dense twig clusters (phase 11: 7 m² m⁻³ of leaf within 0.25 m of a twig bud). Not fixed.
- TreeQSM probably over-counts thin branches, but not twentyfold.

**Whips.**
- The 34–36 m trees were browsed trees whose replacement leader (an order-1 axis) passed its old limb's physiological age to the laterals it grew. Those laterals lost vigour, and the leader took everything: 0.5–0.65 m of height a year at 0.1 cm of DBH (H/D up to 268).
- Laterals on any leader now start their own scaffold. The tallest tree is now 22.2 m.

**Bulbous bases.**
- Not the root ridges: on thin trees the main roots are 0.06–0.35 of the stem radius, so their ridges are small.
- The bulbs were browsing junctions at 0.3–1 m: a thick old stem stub, a replacement leader joining it with a 35 % branch collar, and fillet flaps.
- Fixes: the collar scales with 1 − branch/parent radius (none on a co-dominant junction), and a replacement leader's base is never thinner than the stem below it. One near tree in the render still shows fillet flaps.

## Phase 13: checkpoints, natural stands, stress-floor rings

**Checkpoints.** Every 5 years each plot tree's yearly history goes to disk, its arrays are trimmed, the plot is pickled and `plot.json` rewritten. Trees are exported as they leave the plot.
- A resumed run is identical to a straight one: stand statistics, every year's radii, keyframes and root history all match (checked at year 15 in both modes).
- The natural plot below peaked at 2.2 GB, against 5.5 GB for the 25-tree managed plot before.

**Natural mode** (`--mode natural`): no thinning; a tree dies when its own carbon no longer pays the upkeep of its living wood.
- The combined run: 40 trees at 1800/ha on 222 m², unthinned, every default on (browsing, buttresses, stress floor), 60 years.
- Area: 100 trees on the managed plot's 556 m² would need roughly 10 GB by 60.

| plot year | stems/ha | DBH | CV | Gini | tallest tree | LAI |
|---|---|---|---|---|---|---|
| 20 | 1800 | 13.5 ± 6.0 cm | 44 % | 0.22 | 18.3 m | 4.00 |
| 30 | 1710 | 16.2 ± 6.9 cm | 43 % | 0.23 | 24.5 m | 4.04 |
| 45 | 1665 | 18.2 ± 7.9 cm | 43 % | 0.24 | 29.3 m | 4.40 |
| 60 | 1575 | 19.8 ± 8.8 cm | 45 % | 0.25 | 35.8 m | 4.33 |

- **Spread:** wider than any published managed or planted stand (Romans 2023 Gini 0.09–0.13; Hagemeier & Leuschner 2019 CV 32 % at 880/ha). There is no measured DBH distribution for Gullmarsskogen; the photos show stems of every size.
- **Self-thinning is far too weak:** 5 of 40 trees died in 60 years, leaving 1575/ha.
  - Healthy trees fix 20–60 times their wood upkeep, so the rule kills only trees that have lost almost all their leafy buds.
  - One tree still under 1.3 m is alive at 60.
  - The light low in the stand is too high (phase 10: floor 0.24 against 0.15 measured), so suppressed crowns stay just above the 21 % death threshold.
- **Stem form:** 14 of 35 survivors were browsed. 31 % have a crooked stem above 1.3 m and 3–9 % a fork at 20–25 (published: 39–42 % with a stem defect at 22). Forks are gone again at 60. Largest branch / stem diameter: median 0.47 at 60.
- **Render:** framed like the photos, at the plot's true positions. Sky fraction 6 / 14 / 35 / 47 % by band (photos 12–14 / 37–49 / 45–61 / 60–68 %).
  - Stems of every size, thin suppressed ones among the dominants, and some crooked stems: closer to Gullmarsskogen than the thinned plot.
  - Still too dense, with uniform grey stems, and twigs clustered high in the crowns.
  - Several thin stems have bulbous bases, probably buttress ridges sized by roots that are large relative to a suppressed stem. To check.
- **Height:** the tallest trees reach 33–36 m at 60 in both plots, against 26.9 m at the top of the Swedish band. Dominants in a plot outgrow the single-tree stands (29–30 m).

**Stress-floor rings** (`pipe_model.stress_floor`): each ring is at least what keeps the self-weight bending stress under green MOR / safety factor.
- Green MOR 57 MPa: 114 MPa seasoned silver birch × the green/seasoned ratio of yellow birch (VERIFY). Safety factor 3.5 (Univ. Tokyo branch study). So 16 MPa.
- **It never binds.** In seed 1 at 20 the model's limbs carry 1.6 MPa at the base (median), 3.6 MPa at most; no internode reaches the limit. With the floor on or off: 2 limbs over 2 cm, limb/stem ratio p90 0.31, 18 m of branch wood at least 1 cm thick.
- The model's limbs are thin because they are light (the largest carry 400–900 leaves), not because the ring rule is too weak.
- The extra wood would not be charged to the carbon budget.

**Limbs against the 6 Nordic stand scans** (15.5–19.7 m):

| | scans (median) | thinned plot, age 20 | natural plot, trees at 15–20 m | seed 1 stand, age 20 |
|---|---|---|---|---|
| limbs > 2 cm | 58 | 27 | 4 | 2 |
| largest limb / stem diameter, 90th percentile | 0.67 | 0.32 | 0.31 | 0.31 |
| branch wood ≥ 1 cm | 869 m | 70 m | 34 m | 18 m |

The limb deficit is in growth (limb length and the shoots each limb carries), not in strength.

## Phase 12: the plot to 60, Nordic stand scans, iNaturalist photos

**The 25-tree plot to 60** (seed 1, every default on: browsing, buttress flare).
- It grew all 60 years in 1688 s.
- Memory: peak 5.5 GB, not the 3–3.5 GB estimated. Each tree's history (keyframes every 5 years, radius samples) grows by about 3.5 MB a year once the stand has thinned to 25 trees.
- Claude Code's low-memory guard stopped it during the export, after 16 trees, with a 17th written in part (timeline, stats and crown mesh). The other 8 survivors and `plot.json` were never written.
- The layout, germination years and vigour factors were rebuilt exactly from the plot seed, and checked: every tree's last year = 60 − germination year.
- Stand rows for all 25 trees come from the log. Tree-level numbers come from the 17 exported trees (export follows tree id, not size).

| plot year | stems/ha | DBH, all 25 trees | CV | tallest tree | LAI |
|---|---|---|---|---|---|
| 10 | 1800 | 6.1 ± 3.0 cm | 50 % | 7.3 m | 2.33 |
| 15 | 1008 | 15.7 ± 3.0 cm | 19 % | 13.1 m | 3.32 |
| 20 | 450 | 22.3 ± 2.6 cm | 12 % | 18.0 m | 2.94 |
| 30 | 450 | 28.1 ± 3.6 cm | 13 % | 24.4 m | 3.60 |
| 40 | 450 | 31.4 ± 3.6 cm | 11 % | 27.9 m | 4.09 |
| 50 | 450 | 33.9 ± 3.6 cm | 11 % | 31.7 m | 4.26 |
| 60 | 450 | 35.9 ± 3.7 cm | 10 % | 36.5 m | 4.29 |

The 36.5 m tree is one of the 8 that were not exported. The 17 exported trees top out at 31.8 m, so it cannot be examined.

**Diameter distribution against published stands** (17 exported trees):

| | age | stems/ha | DBH / QMD | spread |
|---|---|---|---|---|
| model plot | 30 | 450 | QMD 27.3 cm | Gini 0.052, CV 9 % (13 % over all 25) |
| model plot | 33 | 450 | QMD 28.5 cm | Gini 0.052 |
| Romans 2023 (SLU MSc), Skräddarbo, planted 1989, fenced | ≈33 | 1233–2056 at 19 years, one later thinning of unrecorded intensity | QMD 14.2–17.7 cm | Gini 0.09–0.13 |
| model plot | 45 | 450 | 32.7 ± 3.6 cm (all 25) | CV 11 % |
| Hagemeier & Leuschner 2019 (Forests 10:925), Germany | 45 | 880 | 19 ± 6 cm | CV 32 % |
| model plot | 50 / 60 | 450 | 33.9 / 35.9 cm (all 25) | CV 10.5 / 10.3 % |
| Hagemeier & Leuschner 2019, Germany | 67 | 420 | 25 ± 3 cm | CV 12 % |

- **Spread:** at 50–60 it matches the German stand of similar density (12 %). At 30–45 it is about half the published spread: thinning from below to 450/ha by 16 m removes the small trees, and the survivors stay within ±20 % of each other.
- **Size:** at matched density, DBH is about 40 % above the German stand (35.9 cm at 60 against 25 cm at 67). Height is above the Swedish band too (below).

**Forks and crooks.**
- None of the 17 crop trees lost a leader, so none is forked or crooked at age 20, 25 or 60 (the stem is the leader axis; crooks are bends of 10° or more between 0.5 m chords above 1.3 m).
- About half of all trees should have been browsed once. Unbrowsed survivors by chance would have a probability of about 0.48^17 ≈ 4 × 10⁻⁶.
- So thinning from below removed every browsed tree: a browsed tree loses about 2.3 m of height by age 22 and falls behind.
- Single-tree stands (20 seeds, browsing on / off):

| age | forked | crooked | H on / off |
|---|---|---|---|
| 22 | 20 % / 0 | 45 % / 0 | 15.9 / 18.2 m |
| 50 | 20 % / 0 | 45 % / 0 | 27.6 / 27.8 m |
| 60 | 25 % / 0 | 45 % / 0 | 30.5 / 29.4 m |
| published | 38.6–41.7 % with a stem defect at 22 (Viherä-Aarnio & Velling 2008) | | |

**Height against the Swedish band** (Eriksson, Johansson & Kiviste 1997, site index H50 20–26 m; total age = breast-height age + 4):

| age | band | single trees, browsed | single trees, unbrowsed | plot crop trees (mean / max) |
|---|---|---|---|---|
| 22 | 10.0–15.6 m | 15.9 m | 18.2 m | – |
| 50 | 19.2–25.3 m | 27.6 m | 27.8 m | 28.7 / 30.1 m |
| 60 | 21.1–26.9 m | 30.5 m | 29.4 m | 30.4 / 31.8 m |

- The site curves come from real, browsed stands. Browsing closes 2.3 m of the gap at 22 but nothing at 50–60: browsed trees catch up by about 50.
- In the plot, the browsed trees were thinned out, so the crop trees are the unbrowsed ones.
- The gap at 50–60 (2.3–3.6 m above the top of the band) is not browsing. It is left for the nitrogen and growing-season phase.

**Persistent basal limbs in the plot.**
- Some crop trees keep living limbs from their first 2–7 years at 0.1–2 m, with 5–35 living short shoots each at 60 (tree 003: 15 limbs below 3 m; 063: 5; 013: none).
- The light low in the stand stays above the 21 % death threshold: the model's floor light is 0.24, against 0.15 measured (phase 10).
- The early-germinated crop trees also had smaller neighbours while young.
- This is the base-limb problem of the open-grown trees, now in the plot. Not fixed this round (no new mechanisms).

**Photo-matched winter render of the plot.**
- The plot's 17 exported trees laid out at random at 450/ha (true positions incomplete), framed as before.
- Sky fraction 9 / 15 / 36 / 47 % at 5–15 / 15–25 / 25–35 / 35–45°. The clone stand had 12 / 19 / 43 / 56 %; Gullmarsskogen has 12–14 / 37–49 / 45–61 / 60–68 %.
- It still reads as a plantation: straight, smooth, parallel grey stems of similar size and no forks or crooks. Twigs sit in clusters at the crown tops. The photos show leaning and crooked stems of every size, forks, and long ascending limbs.

**Nordic stand-grown scans (FOR-species20K): 6 of 30 so far.**
- 30 silver-birch TLS scans were chosen from `../tree-data/for-species20k` (GPL-3.0, read only): the Junttila (Finland) and Luke (Natural Resources Institute Finland) sets, trees 15.5–29 m tall with at least 0.6 M points.
- Not chosen: Liang_2018 (94 trees) is too sparse (median 47 k points), REMBIOFOR is Polish, VanDeBerge is the Belgian hedgerow set already used.
- Branch models were built with TreeQSM in Python (PyTLidar 1.0.1, GPL-3.0), in a separate scratch environment (Python 3.12) outside the repo. Clouds were thinned to at most 1 M points (voxel 0.4–1.5 cm), with TreeQSM's own automatic patch sizes.
- Scan outputs stay outside the repo and are used only as comparison numbers. No scan geometry enters the generator.
- Only 6 trees finished (15.5–19.7 m):
  - one failed on a PyTLidar index error in its stem-top search (12829);
  - one QSM run grew to 8.4 GB and brought the machine to 0.4 GB free (12827), so the batch was stopped;
  - 23 trees are still to run.
- Metric definitions as for the Belgian scans and the model: base diameter = the smaller of the branch's first two cylinders; ratio = branch / stem diameter at the attachment for branches > 2 cm below 0.8 H; angle = TreeQSM branch angle to the parent; low limbs = first-order branches > 2 cm below 0.5 H.

| | Nordic scans, 15.5–19.7 m (median, p10–p90) | model plot trees at 20 (17.5 m) | model plot trees at 30 (23.4 m) |
|---|---|---|---|
| DBH | 17.7 cm (13.3–19.4) | 22.0 cm | 27.4 cm |
| first-order branches > 2 / 5 / 10 cm | 58 / 3 / 0 (29–68 / 1–26 / 0–2) | 27 / 0 / 0 | 41 / 0 / 0 |
| largest branch / stem diameter, max | 0.95 (0.90–1.34; values > 1 are QSM artefacts) | 0.38 | 0.35 |
| the same, 90th percentile | 0.67 (0.57–0.73) | 0.32 | 0.30 |
| branch angle, low / mid / top third | 58 / 48 / 68° | 44 / 51 / 55° | 44 / 49 / 47° |
| limbs > 2 cm below 0.5 H (of which within 45° of the stem) | 5 (2–16), ascending 2.5 (0–8) | 18, ascending 10 | 14, ascending 5 |
| branch wood ≥ 1 cm diameter | 869 m (482–1319) | 70 m | 130 m |

What the Nordic scans say so far:
- The model has about a tenth of the branch wood of 1 cm and more of a real stand birch of the same height. It has half the limbs over 2 cm, and its biggest limbs are half as thick relative to the stem (90th-percentile ratio 0.32 against 0.67).
- This is the same gap as against the Belgian hedgerow trees (phase 10), now confirmed on Nordic stand trees.
- The model's low limbs are not too few at 20: it has more limbs over 2 cm below 0.5 H than the scans (18 against 5). The difference is in the crown above.
- The scans' lowest branch over 2 cm sits at 0.03–0.46 H (median 0.04). TLS records dead branches and understorey too, so this needs the scans' point clouds checked before it is used.
- Six trees, all in the shorter half of the selection, are a preliminary sample.

**iNaturalist photos.**
- 13 of the 43 silver-birch `whole_tree` photos in `../tree-data/inat-photos` show the whole tree (crown top and stem base in frame). They are listed in `reference/CREDITS.md` with author, licence and link, and read from that folder, not copied.
- 3 are leafless (#22 park tree, #24 edge group, #40 dying with a dead top); 10 are in leaf.
- Nearly all are open-grown or edge trees: crowns reach far down the stem through long ascending limbs with an even veil of twigs. The model's stand trees are bare to about 0.6 H, with clustered twigs at the top.
- The like-for-like model is the open-grown mode, which is on hold.

## Phase 11: leader damage, a plot of real competitors, winter crowns, root buttresses

**Leader damage** (`leader_damage`, on by default).
- Moose browsing: 16.8 %/yr of leaders between 0.3 and 3 m (Bergqvist, Bergström & Wallgren 2014, Silva Fennica 48:1077, southern Swedish young birch stands).
- The leader's last annual shoot dies; the two uppermost buds or young laterals within 0.5 m take over with the stem's vigour and posture target. Forks and crooks emerge from growth.
- No published yearly rates were found for late frost, snow or wind breakage of the top, so they are not included.

Stand seeds 1–20 at 22 years:

| | forked | crooked | leader losses / tree | H |
|---|---|---|---|---|
| no damage | 0 % | 0 % | 0 | 18.2 m |
| moose browsing | 20 % | 45 % | 0.8 | 15.8 m |
| published | 38.6–41.7 % with a stem defect (fork or vertical branch) at 22, local Finnish provenances (Viherä-Aarnio & Velling 2008, Silva Fennica 42(5)) | | | |

**Plot of real competitors** (`treegen/plot.py`, `tools/plot.py`).
- 100 trees at 1800/ha on 556 m² (25 at 450/ha after thinning), each its own simulation.
- One periodic light field from all trees' leaves; each tree's soil-water field also holds the others' absorbing roots.
- Trees differ in seed, germination year (0–3, weights 0.4/0.3/0.2/0.1; VERIFY) and a lognormal growth factor on carbon gain (SD 0.06; VERIFY).
- Thinned from below to the programme density by dominant height.
- Memory: about 290 MB peak for one stand tree at 60, so a 25-tree plot (100 trees until the first thinning) was estimated at 3–3.5 GB and fits at full resolution.
- Both full runs reached year 15 and were stopped there:
  - the 25-tree run (403 s, peak 2.3 GB) was stopped by hand when another program took 7.9 GB and system commit reached 26.7 of 27.2 GB;
  - a 20-tree rerun (226 s, peak 1.7 GB) was stopped by Claude Code's low-memory guard.
- **Plot results to 60 are pending a run on a quiet machine** (the 20-tree run needs about 3 GB at 60, plus about 0.8 GB more while each tree is exported). The 20-tree run gave the same picture as the 25-tree one: at 15 years 990/ha, DBH 15.7 ± 2.9 cm (CV 19 %), LAI 3.34.

| year | stems/ha | DBH mean ± SD | CV | LAI |
|---|---|---|---|---|
| 10 | 1800 | 6.1 ± 3.0 cm | 50 % | 2.33 |
| 15 | 1008 (thinned from below) | 15.7 ± 3.0 cm | 19 % | 3.32 |

Against the clone stand (20 single-tree stand seeds, round-10 defaults), whose DBH CV is only 2–6 % at every age because every neighbour is a copy:
- DBH spread, published: Gini 0.09–0.13 (≈ CV 16–23 %) in a planted, fenced Swedish silver birch spacing trial at about 33 years (Skräddarbo, Sala; Romans 2023, SLU MSc thesis); CV 32 % (45 years, 880/ha) and 12 % (67 years, 420/ha) in two German stands (Hagemeier & Leuschner 2019, Forests 10:925, Table 2).
- The plot's 19 % CV after the first thinning is in that range.

**Sparse winter crowns: the cause was the render.**
- The round-10 stand render drew the central 20 trees with hero meshes and the 8 surrounding copies with `tree_reduced.glb`. That mesh drops every branch under 1.09 cm radius (50k of 440k triangles), so every tree beyond the patch had no twigs at all.
- Re-rendered with hero meshes for every tree in view to 120 m, framed like the photos (level camera; Sony RX100 at 10.4 mm, f = 1513 px; horizon row from the farthest stem bases), the stand gets the fine-twig haze of the photos.

Sky fraction by elevation angle, one classifier for photos and renders (blue-dominant pixel; render sky painted in the photos' measured sky colour):

| elevation | Gullmarsskogen 1 / 5 / 6 | model, matched render |
|---|---|---|
| 5–15° | 12.8 / 13.5 / 12.1 % | 11.9 % |
| 15–25° | 37.4 / 48.5 / 39.5 % | 19.0 % |
| 25–35° | 45.0 / 61.3 / 53.8 % | 42.9 % |
| 35–45° | 60.0 / 67.9 / – % | 55.6 % |

The model is now as dense as the photos, or denser, at every elevation. The round-10 measure (bands from the top of differently framed images) was confounded by framing and is withdrawn. In leaf (same framing, plain leaf cards) the canopy is closed: sky fraction 7 / 1 / 5 / 17 %. The photos are leafless, so there is no summer reference.

Still different in the matched render:
- the model stems are all alike, straight, grey and thicker;
- the photos show long, ascending limbs lower on the stem, crooks and forks, and stems of every size;
- the model reads as a plantation of clones.


Structure checked against measurements (seed 1 stand):
- Crown leaf-area density by 2 m layer (leaf area / crown-envelope volume, as Hagemeier & Leuschner 2019, Forests 10:265, measured it; their birch fit 0.142 + 2.91 x^9.02):

| age | 0.5–0.85 H | top tenth |
|---|---|---|
| 30 (22 m) | 0.18–1.54 (fit 0.14–0.79) | 1.82 (fit 1.74) |
| 45 | 0.10–1.04 (fit 0.15–0.88) | 0.58–0.81 (fit 1.7–3.3) |
| 60 | 0.06–0.55 (fit 0.14–0.82) | 0.55–0.70 (fit 1.5–2.7) |

- Twig lifespans after age 30: order-2 axes shed at a median 10–15 years, order 3+ at 8.
- Every shed branch failed the light test (none the carbon test, apart from 7 after age 45).
- In the dense phase (10–20 years, 1800/ha, stand LAI 3.1–3.5) twigs die at 2–3 years, at bud light 0.13–0.19. That is ordinary self-pruning under a closed young canopy.
- At 30–60 years, LAI 3.5–4.0 (measured 3.6 and 5.4) and the leaf area per layer is in the measured range. Only the top tenth of the crown is too thin.

**Young-stand LAI by age** (20 clone-stand seeds, mean and range; Estonian stands aged 14–45: 2.5–4.4):

| age | 10 | 12 | 15 | 18 | 20 | 25 | 30 | 40 | 50 | 60 |
|---|---|---|---|---|---|---|---|---|---|---|
| LAI | 3.55 | 3.87 | 2.73 (2.12–3.49) | 3.05 | 1.80 (1.32–2.28) | 3.23 | 4.05 | 4.09 | 4.37 | 4.55 |
| stems/ha | 1800 | 1800 | 1000 | 1000 | 450 | 450 | 450 | 450 | 450 | 450 |

- The low values come right after each thinning: the programme removes 44 % and then 55 % of the stems.
- The 2.2 at 15 quoted in phase 10 was seed 1 alone.
- The plot (real competitors) had LAI 3.32 at 15, after its first thinning.

**Base flare follows the roots** (`geometry.root_flare_mode: buttress`).
- Each main structural root (a root leaving the stem/taproot axis below ground) raises a ridge on the stem at its own azimuth.
- The ridge stands out by the root's radius at the ground line, spans the arc the root covers on the stem, and fades smoothly upwards. The largest root's ridge reaches the uppermost root collar: 0.4862 DBH[cm] + 0.4979 H[m] cm for birch (Laasasenaho 1982; relative SE 44 %), 29 cm at DBH 29 cm / H 29 m. Smaller roots' ridges stay proportionally lower.
- Seed 1 stand at 60 has 7 main roots, 1.4–5.6 cm in radius. Mesh sections against each mesh's own radius at 1.3 m:

| height | old bell | buttress ridges |
|---|---|---|
| 0.02 m | +32 % all round | mean +11 %, ridges to +33 %, troughs −3 % |
| 0.10 m | +40 % | mean +12 %, ridges to +28 % |
| 0.30 m | +27 % | +5 % |
| 0.50 m | +15 % | +3 % |

- The uniform bell remains as the fallback for meshes without roots.
- Not sourced: ridge width and height in proportion to root size (VERIFY). The ridges are modest because the model's main roots are thin: their cross-sections at the collar sum to 280 cm², against 742 cm² of stem.

**Numbers at 50 and 60** (20 clone-stand seeds, round-10 defaults: no browsing; these are the trees in the stand renders):

| age | DBH | H | crown base | LAI |
|---|---|---|---|---|
| 50 | 29.5 ± 1.4 cm | 27.8 m | 14.8 m | 4.37 (3.48–5.16) |
| 60 | 31.6 ± 1.6 cm | 29.5 m | 16.9 m | 4.55 (3.46–5.71) |

With browsing on, the trees are about 2.4 m shorter at 22. Runs to 60 with the combined defaults (browsing, buttresses, plot) were not made in this round (memory).

**Still open after phase 11:**
- The plot to 60: DBH distribution, fork and crook shares among real competitors, and plot renders.
- Forks: 20 % of browsed stand trees at 22, against 39–42 % with a stem defect in Finnish trials. Late frost, snow and wind breakage are missing for want of sourced rates.
- The near-fork ratio (largest branch / stem diameter) in the scans is 0.72–0.91; in the model it is 0.36 (stand) and 0.45 (open) at 17 m.
- Long, ascending limbs low on the stem, as in the photos, are missing. Stand limbs stay short and their twigs sit in dense clusters (leaf-area density about 7 m² m⁻³ within 0.25 m of a twig bud at 12–16 years).
- The top tenth of the crown carries too little leaf area (0.55–0.8 against 1.5–3.3 m² m⁻³ measured).
- Reduced meshes have no fine twigs (see README). A distant tree needs the hero mesh or twig cards.

## Phase 10: limb death, limb wood, stand renders

**What killed limbs** (seed 1 stand, every first-order limb shed after age 30, logged at death):
- Of 138, 111 died of light at 0.19–0.20, and they were young (median 11–18 years) and high (0.80–0.84 H), in the shade of the reiterated head.
- Old lower limbs were mostly not shed. They went leafless: short shoots died at a fixed age of 8 years (`spur_lifespan`, unsourced), and limbs whose meristems had aged could not make new ones.

Death now comes from light and carbon, and ageing only lowers vigour:
- short shoots and branches die below 21 % light, the measured light of the lowest birch shade leaves (Hagemeier & Leuschner 2019);
- a branch whose own leaves no longer fix enough carbon to pay the upkeep of its wood is shed (`shedding.carbon_balance`);
- short shoots have no fixed lifespan.

Seed 1 stand at 60: crown base 0.65 → 0.53 H, LAI 2.95 → 4.05 (measured 4.6), light at the lowest leaves 0.35 → 0.24 (measured ~0.21), floor 0.36 → 0.24 (measured 0.15).

**Limb wood.** The ring allocation does what Pressler and the pipe model say:
- every living node with leaves beyond it adds a ring each year, at one constant ring area per unit leaf area (2.46e-5 m²/m² at age 25);
- wood never decreases, so the wood of shed twigs stays;
- 127 of 219 limbs at 25 are held at the pipe-model floor.

Stand limbs are thin because each carries little foliage. At 17 m the stand tree has 36 m² of leaves over 164 limbs (median share 0.2 %, largest 4.6 %); the open-grown tree has 315 m².

First-order branches by base diameter at about 17 m:

| | 1–2 / 2–3 / 3–5 / 5–10 / >10 cm | largest branch / stem diameter |
|---|---|---|
| scans, 16–19 m (4 hedgerow birches) | 6–17 / 5–23 / 14–35 / 8–36 / 1–6 | 0.72–0.91 |
| model, open-grown, 17.2 m | 66 / 21 / 21 / 21 / 0 | 0.45 |
| model, stand, 17.5 m | 32 / 6 / 0 / 0 / 0 | 0.36 |

- The open-grown model, the like-for-like match for hedgerow trees, matches the scans from 2 to 10 cm.
- Missing in every mode: limbs over 10 cm and near-forks (largest branch near the stem's diameter).
- In the stand, young-stand LAI is low: 2.2 at 15 years and 1.6 just after the thinning to 450/ha, against 2.5–4.4 in Estonian stands. That leaves too little foliage per limb.
- Carbon-balance death also halves the number of limbs over 2 cm at 60 (67 → 26–36): old limbs whose wood costs more upkeep than their few leaves fix are shed.

**Stand seeds 1–3 at 60:**
- crown base 0.53 / 0.31 / 0.64 H (stand photos 0.32–0.6);
- LAI 4.05 / 4.65 / 3.46 (measured 4.6);
- H/D 100 / 90 / 99;
- DBH 29.3 / 33.1 / 29.7 cm;
- lean 2.1 / 2.7 / 2.5°;
- no base twigs (lowest live branch 7.9–12.5 m).

**Stand render.** 20 seeds at 450 stems/ha, viewed from the forest floor at eye level and framed like the Gullmarsskogen photos (the patch is repeated around itself, at reduced detail, to fill the background); a summer version uses plain leaf cards at the stored short shoots.

It reads as a birch stand at first glance: many slender pale stems, crowns high, a fine-twig haze above.

Against the photos:
- the crowns carry much less fine twig mass;
- stems are smoother and straighter (no crooks);
- stems are thicker for their height;
- the stand is thinned to 450/ha, while Gullmarsskogen is an unmanaged reserve with more stems.

## Phase 9: light in the stand, stem lean, laser-scan branch reference

**Stand light, against measurements.** Hagemeier & Leuschner 2019 (Forests 10:925) measured two closed *B. pendula* stands (45 and 67 years, 880 and 420 stems/ha, 20–25 m):
- forest-floor PAR 14.8 % (6.4–19.8 %);
- lowermost shade leaves at ~21 %;
- LAI 4.6, K_PAR 0.37, clumping index 0.42.

Neighbour shade in the model was already leaf area along the light path: neighbours are copies of the focal tree's leaves, not volumes. What was off was the shade per leaf area. The model used k = 0.5 (spherical leaves); it now uses the measured 0.37.

| seed 1 stand, age 60 | k 0.5 | k 0.37 (default) | measured |
|---|---|---|---|
| bud light, crown top | 0.68 | 0.70 | ~1 |
| bud light, mid crown | 0.31 | 0.34 | – |
| bud light, lowest leaves | 0.34 | 0.35 | ~0.21 |
| stand floor, 1.5 m | ~0.35 | 0.36 | 0.15 (0.06–0.20) |
| LAI | 2.18 | 2.95 | 4.6 |
| lowest live branch | 0.17 m | 6.7 m | – |

- The measured coefficient raises LAI by a third and kills the seedling-era base twigs; seed 3 keeps one.
- The floor is still twice as bright as measured, because LAI is still lower. The lowest leaves sit at 35 % light, well above the 21 % at which birch shade leaves die, yet the crown base stays at 0.65 H. Lower limbs die of meristem ageing (`branch_aging_years` 20, with inheritance), not of shade. That is the next lever for crown base and LAI.

**Stem lean.** Posture control was already growth-limited (rate ∝ C ṙ/r², Alméras & Fournier). It removed every lean because it always aimed at vertical. Seed 1 stand at 60, lean from base to top:

| posture control | lean |
|---|---|
| none (upper bound of the lean forces) | 4.4° |
| sine law, no saturation | 0.6° |
| sine law, full above 10° | 0.27° |
| same, half the reaction-wood asymmetry | 0.30° (limbs sag to 65°) |
| same, plus stem posture target tilted towards the crown's light (default) | 1.2° (seeds 1–3: 1.2–2.0°) |

- The leader also turns towards the brighter side of its own crown (`tropism.stem_crown_phototropism`). Its posture target inside the crown tilts by phototropism over gravitropism (0.8/4.0) times the crown's light asymmetry (whole-tree phototropism, Loehle 1986).
- The stem's 4/m gravitropism has no source (VERIFY). Lowering it to 1–2/m did not change the lean.

**Laser-scan branch reference.** 11 leaf-off hedgerow *B. pendula* with TreeQSM models (Van Den Berge et al. 2021, Zenodo 10.5281/zenodo.4487116, CC BY 4.0), each averaged over its 10 QSM repetitions. Note: TreeQSM's `FCB` often points at a branch's second cylinder; the first one is `CiB[0]`. Branch base diameters use the smaller of the first two cylinders, since the first is often inflated where it enters the stem.

| first-order branches | scans (5.5–19 m) median (range) | model age 20 (17 m) | model age 60 (30 m) |
|---|---|---|---|
| > 2 / 5 / 10 cm | 27 (15–94) / 6.2 (2–38) / 0.1 (0–5.8) | 7–18 / 0 / 0 | 67–69 / 2–4 / 0–1 |
| largest branch / stem diameter | 0.93 (0.72–0.95) | 0.32–0.36 | 0.57–0.64 |
| 90th percentile of that ratio | 0.81 (0.54–0.95) | 0.30–0.35 | 0.16–0.19 |
| insertion angle, low / mid / top third | 64 / 63 / 68° | – / 52–55 / 53–55° | 50 / 47 / 46° |
| own length / H, low / mid / top third | 0.11 / 0.11 / 0.09 | – / 0.13–0.14 / 0.10–0.11 | 0.13 / 0.12 / 0.10 |

- Angles and lengths are close.
- The model's limbs are far too thin: no branch over 5 cm at 17 m, where scanned birches of that size carry 11–38. The largest limb is a third of the stem's diameter, where the scans show near-forks.
- Hedgerow trees are more open-grown than stand trees, so part of the gap is expected. Most of it is not: limb wood is too small.

**FOR-species20K** (Zenodo 13255198; licence on the record: GPL-3.0-or-later; not downloaded):
- 735 *Betula pendula* in the development metadata: 171 TLS, 366 ULS and 198 MLS;
- from Puliti a/b (518), Liang 2018 (94), Junttila (43), NIBIO (39), REMBIOFOR (24), Van Den Berge 2021 (8), Weiser 2022b (7) and Luke (2);
- 1.5–30 m tall (median 13.9 m);
- point clouds only, no QSMs. The data are in `dev.zip` (25.4 GB).

## Phase 8: architecture against photographs (stand, open)

Matching the reference photos (`reference/`, Wikimedia Commons, comparison only) is now the main acceptance test; the numbers are a range check.

**Metrics** (fractions of tree height H; photos digitised by hand on a grid, about ±0.03; the model's width and widest point come from its eye-level render, the rest from its geometry):

| metric | stand photos (Brastad ×2, Russia) | solitary photos (Oslo, Meilen, Hallinden) | dense stand (Gullmarsskogen) | model before | model now, seeds 1–3 |
|---|---|---|---|---|---|
| crown width / H | 0.22–0.25, 0.43 | 0.53–0.76 | (tops out of frame) | 0.19 | 0.19–0.23 |
| widest point | 0.64–0.75 | 0.44–0.58 | – | 0.62 | 0.34, 0.95, 0.91 |
| crown base | 0.32–0.6 | 0.20–0.43 | – | 0.72 | 0.61–0.64 |
| major limbs | 3–5 | 4–7 | – | 1 | 4–5 |
| leader | forks in the top 20 % | lost or forked at 0.43–0.85 H | – | dominant, spire | nominal (0.1 m above the next axis) |
| stem lean | 1–3° | 4–11° | 0–5°, median ~3° | 0° | 0° |

**What changed:**
- **Base artefacts.** These were living seedling-year limbs at 0.2–1.5 m, kept alive because shade faded with depth below the canopy (`light.shadow_decay_length` 30 m). Stands now keep their shade below the canopy (`stand.shadow_decay_length`). On the lattice layout the lowest live branch rises from 0.17 to 6.6 m. With random neighbours, a few small twigs survive in gap light (q ≈ 0.3).
- **Random neighbours** (`stand.layout: random`). Hard-core random positions at the scheduled density, relative sizes with CV 0.10, random turns. Light is now uneven, but stems stay straight; see below.
- **Reiteration** (`resource.reiteration`). Loss of dominance is detected once the tree is past 30 and the leader's yearly growth is below half its peak. From then on, the most vigorous well-lit first-order limb in the upper three quarters of the crown becomes a reiterated complex every 5 years: partly rejuvenated, with an orthotropic axis.
  - Literature: Barthélémy & Caraglio 2007; Millet, Bouchard & Édelin 1999, where grey birch keeps a hierarchic architecture, loses dominance into short forks at maturity, and has at most two total reiterates; and the ARCHI "duplication" concept.
  - The thresholds have no published values. A vigour bar relative to the leader was cliff-like: 0.45 gave 13–63 complexes and a broom on a pole, 0.55–0.7 gave none. The sequential rule with a 5-year interval (calibrated to the photos' 4–7 major limbs) gives 7 complexes and 4–5 major limbs.
  - The spire top is gone in all three seeds, replaced by an irregular head. But the complexes sit at 0.63–0.89 H, and the crown below is still a fishbone of short limbs.
- **Stem lean is not solved.** Stems were exactly vertical because posture control removed any deviation every year. A sine-law correction (`mechanics.sine_law`, off) gives at most 0.9° of lean, and it makes limbs sag to 67° (57–60° with saturation at 10°) against the measured 43°.
  - The deeper cause: nothing pushes the stem. At the top of the canopy the leader's phototropism sees open sky in every direction, and the stem's gravitropism (4/m, VERIFY) removes the sympodial deflections within each year.
  - Candidates for next time: leader phototropism from the sky view, or a weaker stem gravitropism with sources.

**Range check, stand seeds 1–3 at 50 / 60:**
- Height 27.3–27.7 / 28.8–29.5 m: still over the band by about 2–2.6 m (nitrogen and season missing).
- DBH 23.5–26.1 / 25.0–27.9 cm.
- H/D 106–118: above the 80–100 target.
- LAI 2.18–2.90: seed 1 below the 2.5 published minimum. Less light reaches the lower crown now that shade no longer fades.

## Phase 7: the carbon budget (seed 1)

Several results pointed to one cause: the tree was short on carbon. The changes, tested one at a time and then combined on seed 1, are now defaults. Carbon is in model resource units (about one metamer each).

| step | change | stand at 60: H / DBH / H/D / LAI / carbon |
|---|---|---|
| – | phase-6 defaults | 22.8 / 15.7 / 145 / 2.51 / 18.9k |
| 1 | own-shoot shade excluded from bud light | 24.4 / 17.0 / 144 / 2.65 / 21.0k |
| 2 | Huber fix (additive sapwood, 1.24e-4) alone | 17.6 / 13.7 / 128 / 2.11 / 16.8k |
| 2 | Huber fix + root uptake ×2 | 25.5 / 21.1 / 121 / 3.55 / 32.5k |
| 1+2 | combined | 26.0 / 21.9 / 119 / 3.33 / 32.7k |
| 1+2+3 | + full rings | 21.6 / 27.7 / 78 / 1.62 / 16.6k |
| 1+2+3 | + full rings with the pipe floor | 26.9 / 30.6 / 88 / 3.38 / 31.9k |
| 4 | + limbs inherit stem age, 43 deg limbs | 31.8 / 29.8 / 106 / 3.32 / 25.3k |

- **Own-shoot shade** is subtracted exactly: the light propagation is linear, so its impulse response gives the shade a shoot's own leaves cast. It is only about a quarter of the shade on outer buds (surface q 0.65 → 0.71). Still, carbon rose 50 % open and 11 % stand at 60.
- **Huber value:** hydraulics had merged leaf pipes with the branching exponent 2.5. That made conducting area 4× the published value at the shoots and made it fall toward the stem. It now counts additive pipes, 1.24e-4 m² of xylem per m² of leaf (Õunapuu-Pikas et al. 2022), capped by the wood.
- **Root uptake:** Sellin's 5-year saplings put the whole-tree conductance gap in the roots, which took 85–93 % of the sapling's water-potential drop. Root uptake per metre is now calibrated to Sellin's soil-to-branch conductance (2.28 mmol m⁻² s⁻¹ MPa⁻¹).
  - Sapling ψ_top is now −0.87 to −0.94 MPa (Sellin: −1.07), and stomatal opening at 60 is 0.80–0.85.
  - Sapling K_T is still about half Sellin's (0.57 against 1.15). Transpiration per leaf area is also half (0.48 against 0.92 mmol m⁻² s⁻¹).
- **Full rings** collapsed the crown not because of the budget but because of stiffness. Rings gave limbs only their leaf-area share of wood, about 40 % thinner than the pipe model, so 6–10× less stiff. At age 40 the limbs pointed down. The floor "wood is never thinner than the pipes it carries", already used on the stem in stem-rings mode, fixed it.
- **The twin top** came from meristem ageing. A limb born at 45 near the top counted its age from zero, so it was 2.4× as vigorous as the 45-year-old leader and overtook it by 1.1–1.4 m at 60, in every run checked. Limbs now inherit the stem's physiological age at birth (Barthélémy & Caraglio 2007), and the leader stays on top. The stand tree then overshoots the height band by about 5 m. See "Next phase" for nitrogen and season.
- **Limb angles:** the old 25 deg set-point was chosen to hit a crown width, and stiff ring-grown limbs held it exactly (median 25 deg), which gives the poplar look. Insertion and set-point are now the measured 43 deg (Forests 9:52, 2018). The realised median is 43 deg with the angle alone and 54 deg with inheritance, where weaker limbs bend further.

## Next phase: what holds boreal height growth back (open)

The phase-7 carbon fixes put stand seed 1 at the top of the Swedish height band at 60: 26.9 m against 21.1–26.9 m (Eriksson et al. 1997). The open-grown tree overshoots it: 30.0 m with steps 1 and 2. No height limit was added.

The model has a water limit only. Boreal tree growth is mainly held back by two things it does not have yet:
- **Nitrogen.** Most Nordic forest soils are nitrogen-limited.
- **A short, cold growing season.** Shoot extension and cambial activity stop with temperature and day length.

Both belong in the environment and the carbon budget, not a height cap.

## Open-grown trees: on hold (base limbs)

Open-grown trees are on hold, since most of the forest is stand-grown. In open ground, the seedling-era limbs attached in the first metre stay dominant: they are never shaded out (see "Open-grown crown reads as a bottle brush"). Neither branch autonomy nor the herb layer fixed this. No more batches will be spent on it until stand mode is settled.

## Open-grown crown reads as a bottle brush (open)

A mature open-grown silver birch has a handful of dominant ascending limbs, an
open inner crown and most of its foliage on the outer shell. The model's crown
at 60 years has many limbs of the same size instead.

**Diagnosis** (phase-3 model, 10 seeds, age 60; `stats.json` → `scaffold`):

| | model | mature birch |
|---|---|---|
| living first-order limbs | 285–318 | a few dominant ones plus small ones |
| limbs over 5 cm / over 10 cm | 43–59 / 0–1 | a handful over 10 cm |
| five largest limbs | 8–9 cm each | dominant limbs much thicker than the rest |
| leaf share of the 5 biggest limbs | 13–17 % | most of the crown |
| leaf share in the inner 40 % of crown radius | 18–23 % | low (open interior) |
| leaf share in the outer shell (≥ 60 % radius) | 44–47 % | most |
| leaf area by height | even from 30 % to 100 % of height | concentrated in the upper crown |

**What was tried** (seed 1, age 60; height band 21.1–26.9 m):

| run | change | height | limbs | > 10 cm | top-5 leaf share | inner / outer |
|---|---|---|---|---|---|---|
| E0b | none | 21.4 | 305 | 0 | 15 % | 21 % / 45 % |
| E1 | branch ageing 20 → 60 y | 17.2 | 329 | 4 | 25 % | 23 % / 57 % |
| E3 | E1 + old apical control 0.50 → 0.42 | 10.7 | 238 | 4 | 43 % | 14 % / 65 % |
| E4 | shade death 0.20 → 0.30 | 20.0 | 135 | 2 | 21 % | 19 % / 50 % |
| E5 | E4 + branch ageing 35 y | 17.3 | 154 | 2 | 22 % | 21 % / 56 % |
| E6 | E5 + old apical control 0.46 | 13.2 | 131 | 5 | 35 % | 12 % / 72 % |
| E7 | E4 + stem ageing 45 → 70 y | 21.0 | 169 | 2 | 19 % | 19 % / 49 % |
| E8 | shade death 0.35 | 19.1 | 95 | 4 | 26 % | 16 % / 57 % |
| E9 | E5 + gravimorphism 1.0 → 1.6 | 18.7 | 187 | 3 | 20 % | 22 % / 53 % |
| E10 | E9 + stem ageing 70 y | 19.6 | 228 | 4 | 21 % | 23 % / 52 % |

Every variant either changes little or starves the leader. Limbs and the leader
draw on one shared Borchert–Honda pool. Stronger shade death cuts the limb count
in half, but vigour never concentrates in a few mid-crown limbs. Whenever limbs
keep their vigour longer, the oldest, lowest limbs win and the leader loses.

**Branch autonomy** (Sprugel, Hinckley & Schaap 1991) is implemented and
switched off (`resource.branch_export_fraction: null`). With it, each limb lives
on its own carbon, exports a fraction to the stem and is shed when it cannot pay
its upkeep; water stays shared. One batch (export 0.1, 0.2 and 0.35, and with
shade death 0.30):

- The leader holds: height 24–26 m at 60, inside the band.
- But foliage moves to the bottom. The biggest limbs sit 0.1–3 m up and 77–97 % of the leaf area is in the lowest 40 % of the height. Limbs born on the leader are self-funding from their first year, so they never establish. In a stand, the tree overshoots to 29.6 m with a crown ratio of 1.0.

**Branch autonomy with young-limb import** (`resource.young_limbs_import`) was
tried next. A young limb draws its Borchert–Honda share from the stem pool until
its own carbon covers what it drew the year before; then it runs on its own
budget. Two batches on seed 1 at age 60. The first ran autonomy alone (C1a, C1b);
the second ran it with pre-dawn turgor and the ground-contact, root-avoidance and
taproot fixes (X1, X2):

| run | export | height | 5 biggest limbs attached at | top-5 leaf share | leaf share at 30–70 % of height |
|---|---|---|---|---|---|
| base | – | 21.1 | 5–13 m | 14 % | 52 % |
| C1a | 0.1 | 19.8 | 0.1–0.9 m | 46 % | 57 % |
| C1b | 0.2 | 20.5 | 0.1–10 m | 28 % | 43 % |
| X1 | 0.1 | 19.0 | 0.1–0.9 m | 39 % | 57 % |
| X2 | 0.2 | 20.1 | 0.1–1.0 m | 23 % | 54 % |

- Young-limb import does let the mid crown develop: leaf share at 30–70 % of height rose from about 20 % without import to 54–57 %.
- But the dominant limbs are still seedling-era branches attached in the first metre. They become self-funding early and are never shaded out in an open field. They ascend from the base, so the rule that kills branches lying in the ground layer does not catch them.
- The leader also drops below the height band.
- Autonomy stays off. A likely next step is shade from the herb layer (ground vegetation) on foliage in the first metre: open-grown birch self-prunes those first branches in its first decade, and the open-field light model has nothing that does it.

**Herb layer, then autonomy with young-limb import** (phase 6). The field layer
is a Beer–Lambert layer 0.6 m tall with leaf-area index 3 and extinction 0.4
(`environments/sweden_open_field.yaml` → `ground_vegetation`, Monsi & Saeki
1953). Light at height z is multiplied by exp(−0.4 · 3 · (1 − z/0.6)). Seed 1:

| run | mode | height 50 / 60 | DBH 60 | 5 biggest limbs attached at (60) |
|---|---|---|---|---|
| base | open | 20.4 / 21.6 | 29.7 | 5–12 m |
| herb layer | open | 14.5 / 16.9 | 26.1 | 4–9 m |
| herb layer + autonomy | open | 14.4 / 16.4 | 23.7 | 0.7–1.3 m |
| base | stand | 20.1 / 21.9 | 17.1 | 13–18 m |
| herb layer | stand | 13.9 / 15.9 | 15.2 | 8–12 m |
| herb layer + autonomy | stand | 15.2 / 17.1 | 13.3 | 9–11 m |

- The herb layer alone does not deform the crown, but it holds the seedling back for about 8 years, and the tree ends 5–6 m below the height band.
  - Its first leaves sit inside the layer at 10–30 % light, so its first-year carbon is a fraction of the open-field value.
  - A real birch seedling on an unmown field also grows slowly, so the direction is right. Height at 50–60 then depends on the seedling years, which have no calibration data here.
  - The seedling died at first: its radicle stopped counting as an absorbing root after 3 years, before any lateral had grown. Living root tips now always absorb.
- With autonomy on top, the seedling-era base limbs still win in open ground. The five biggest limbs at 60 are attached 0.66–1.33 m up and carry the crown.
  - These branches start inside the herb layer but grow out of it within a few years. Above 0.6 m they are in full light and self-funding again.
  - The herb layer shades a branch only while it is young. Real birch sheds these limbs over decades as the crown above shades them, and in the model the open crown above never shades them enough.
- Both stay off (`ground_vegetation.enabled: false`, `branch_export_fraction: null`).

## Combined defaults (phase 6): 3 seeds, ages 50 and 60

The defaults are now:

- sun/shade leaves on (absolute bud light);
- 15 cm² reference leaf;
- xylem conductivity 4;
- stem rings;
- smooth twig arcs (sympodial bend 0.1 m, correlated noise 0.3 m);
- the herb layer and branch autonomy off.

Means over seeds 1–3 (min–max), with the phase-5 defaults in brackets:

| | open 50 | open 60 | stand 50 | stand 60 | published |
|---|---|---|---|---|---|
| height (m) | 21.5 (20.4) | 24.1 (21.3) | 20.5 (20.2) | 22.6 (22.0) | 19.2–25.3 at 50, 21.1–26.9 at 60 |
| DBH (cm) | 21.2 (26.0) | 24.9 (29.3) | 14.0 (15.8) | 15.7 (17.2) | open 30–50 at 60; stand 25–30 |
| crown width (m) | 7.3 (8.1) | 8.7 (9.4) | 5.2 (5.6) | 5.2 (5.7) | from DBH: 4.4 / 5.0 open, 3.2 / 3.5 stand |
| leaf area (m²) | 241 (289) | 278 (304) | 51 (53) | 57 (50) | – |
| LAI | 6.3* | 5.2* | 2.31 | 2.55 | stands 2.5–4.4 (EE), 3.6–5.4 (DE) |
| top leaf ψ midday (MPa) | −1.61 (−1.83) | −1.66 (−1.97) | −1.38 (−1.46) | −1.40 (−1.50) | −1.0 to −1.3 well watered |
| form factor (Laasasenaho) | 0.52 (0.46) | 0.52 (0.46) | 0.62 (0.49) | 0.63 (0.49) | – |
| d 1.3 / 50 % / 75 % height (cm) | 21.2 / 15.6 / 10.5 | 24.9 / 18.5 / 12.2 | 14.0 / 11.7 / 8.7 | 15.7 / 13.4 / 10.1 | – |
| mean hanging twig (m) | 0.88 (0.92) | 1.06 (1.20) | 0.0 (0.12) | 0.20 (0.11) | – |

\* For open-grown trees LAI is leaf area per crown projection.

- **Height** is in the band in every run.
- **DBH fell further below the published bands.** The 15 cm² leaf brings more self-shade and less leaf area per crown volume.
- **Open-grown stems are now too full** (form factor 0.52 against 0.46). The stand stems are still poles.

## Stand trees

- **DBH is too low:** 15.7 cm at 60 with the phase-6 defaults (17.2 in phase 5, about 20 earlier) against 25–30 cm. The neighbours are copies of the focal crown, so they grow with it, and density follows the Swedish programme [SS14]; the schedule did not change DBH. The crown is too sparse (about 60 m² of leaves). Its leaf area per unit of basal area (0.19 m²/cm²) is lower than the open tree's (0.36), so the trunk is not thin for its foliage. In the mid crown the BH resource per bud is close to zero (v ≈ 0.03).
- **Expansion now follows pre-dawn water potential** (soil minus 0.0098 MPa/m of height), and midday water potential only closes stomata. Seed 1 at age 60:
  - Open-grown: the upper crown now weeps (401 hanging twigs against 2, mean 0.76 m) and height stays in the band (21.3 m). But the bigger upper leaves transpire more, so midday leaf water potential drops to −2.0 MPa, stomatal opening falls from 0.71 to 0.60, and DBH falls from 35.3 to 29.5 cm.
  - Stand: DBH falls from 20.0 to 17.6 cm and leaf area from 59 to 54 m². There are still no hanging twigs in the stand's upper crown.

## Anchorage (resolved)

Phase 5 tried to get overturning resistance from the simulated root plate. The rule for the plate radius mattered more than anything else, since resistance grows with the cube of the radius. No rule landed in the published range: the end of the taper zone gave 5× too little in open trees and 14× too little in stands. The taper zone stays as the root data have it (2.2 × DBH), so the visible root shape follows the roots, not the anchorage figure.

The **critical turning moment** is now computed the way ForestGALES does it: an empirical regression of tree-pulling moments on stem size.

- **Regression:** M = 101 kN m per m³ of stem volume. This is a least-squares fit through the origin to the silver-birch pulling means of Krišāns et al. 2022: 0.67 m³ → 46.9 kN m and 1.43 m³ → 154.3 kN m.
- **Rooting depth:** the deepest root within 1.5 m of the stem (capped by the soil), divided by the 0.85 m depth of the uprooted plates in Krišāns et al., clipped to 0.5–1.2.
- **Root asymmetry, per wind direction:** half of the moment comes from windward root tension (Coutts 1986). That half scales with the windward roots' tension capacity relative to their mean over all directions.

It is reported in `stats.json` → `anchorage.critical_turning_moment` and on the USD Roots prim (`treegen:criticalTurningMoment*`). Seed 1, against M = (25–38) kN m/m³ × H × DBH² (the scaling of the same pulling data):

| | weakest direction – mean (kN m) | H × DBH² range (kN m) |
|---|---|---|
| open 40 | 22–43 | 23–36 |
| open 60 | 57–81 | 47–72 |
| stand 40 | 11–20 | 9–13 |
| stand 60 | 21–39 | 16–24 |

The mean runs at or a little above the H × DBH² range. The stand stems carry too much volume for their DBH (form factor 0.66 against 0.48, see Stem form), and the regression is on volume.

## Sun and shade leaves (phase 6)

Each short shoot takes its leaf size and LMA from its light (`light.sun_shade`):

- LMA = 50.5 + 38.7 q^3.3 g m⁻². This is the vertical LMA profile of adult birch in Hagemeier & Leuschner 2019, with relative light q in place of relative height.
- Leaf size goes as 15 cm² × (60.8 / LMA), so every leaf has the same dry mass. The 15 cm² reference leaf and 60.8 g m⁻² mean shoot LMA are from Õunapuu-Pikas et al. 2022: 167 cm² of leaf on a 27.9 cm current-year shoot.

Both are stored per short shoot in the timeline.

**On the absolute exposure, the gradient was unstable.** Seed 1, LMA in the top 10 % of height against the lowest decile of leaves:

| run | age 50 | age 60 |
|---|---|---|
| sun/shade alone, 12 cm² leaf | 62 / 54 | 83 / 55 (top leaves 8.8 cm², lowest 13.4 cm²) |
| combined (15 cm² leaf, k_s 4, stem rings, twigs) | 57 / 57 | 56 / 59 |

In the combined runs even the outermost leaves came out as shade leaves. Leaves within 0.25 m of the top of their 0.5 m column averaged q 0.67 and LMA 62, and the top metre of the tree averaged LMA 59.

- **Cause:** the model's bud exposure tops out at about 0.6–0.7 even on the crown surface, because each bud sits in the shade of its own shoot cluster (leaf-area density 5–6 m² m⁻³ in occupied 10 cm voxels near the top).
- **Feedback:** shade leaves are larger, so they cast more shade, which makes more shade leaves. Near q = 1 the size response is steeper than 1:1, so the top of the crown can flip between a sun state and a shade state from year to year.

**What was tried** (seed 1, combined settings):

- **Exposure relative to the 99th percentile of the year's bud exposures** (`sun_reference_percentile: 99`): no better. The top 10 % of height averaged LMA 60 against 65 low in the crown (open, age 60). The best-lit 1 % of buds are isolated tips already near q = 1, and the bulk of the outer shell stays at about 0.5.
- **The same reference applied to the shoot and branch light thresholds:** no material change; stand LAI was 2.6.
- **Not yet tested:** leaf traits from the light reaching the shoot from above (`sun_shade.light: above`). This is shade from one voxel up, without the shoot's own cluster, the way LMA–light relations are measured (canopy openness at the shoot). The test run was stopped when the machine ran low on memory.

**State:** sun/shade leaves are on and stored per short shoot. They span the published LMA range (51–83 against 50–89 g m⁻²), but the vertical gradient is flat, or slightly inverted in open-grown crowns.

## Stand leaf-area index (phase 6)

LAI = leaf area × stems per hectare. Published values for mature birch:

- 2.5–4.4 in Estonian silver-birch stands aged 14–45;
- 3.6 and 5.4 in two German birch stands (Hagemeier & Leuschner 2019).

| | age 50 | age 60 |
|---|---|---|
| model (3 seeds, combined defaults) | 2.31 (2.26–2.34) | 2.55 (2.51–2.60) |

That is at the bottom of the Estonian range and below the German stands. The same local over-shading that flattens the sun/shade gradient limits it. Short shoots die below 20 % light, the published shade-leaf light demand. If the canopy top sat at q = 1 with k = 0.5, that threshold would allow an LAI of ln 5 / 0.5 = 3.2. The model's outer shell starts at about 0.6, so the canopy fills only to about 2.4.

A calibration through the light model's VERIFY parameter for leaf spread (`light.leaf_spread` 0.06 → 0.10 m) was queued but stopped with the memory shortage. The stand DBH deficit (15.7 cm at 60) follows from the same small crown.

## Stem form and annual rings (phase 6)

There are three ways to grow radii (`pipe_model.growth`):

- `pipe` recomputes every radius each year from the pipes to the current foliage, plus disused pipes.
- `rings` lays down the year's wood (a share of the shoot carbon) as rings on every internode, in proportion to the leaf area beyond it (Pressler; LIGNUM).
- `stem_rings` keeps the pipe model for branches. On the stem, each internode in the crown adds the growth of its pipe area, and one below the crown base adds the crown-base ring (Pressler). This is the default now.

The comparison below uses the Laasasenaho (1982) birch volume function: V = 0.011197 d^2.10253 0.986^d h^3.98519 (h − 1.3)^−2.659 dm³, as implemented in the `forester` R package. Its form factor is V / (basal area × height). The taper-curve polynomial coefficients for birch could not be found outside the 1982 monograph.

Seed 1, age 60 (diameters in cm, form factor in brackets against Laasasenaho):

| run | mode | d 1.3 m | d 50 % height | d 75 % height | form factor | leaf area |
|---|---|---|---|---|---|---|
| pipe (old) | open | 29.7 | 19.1 | 11.1 | 0.45 (0.43) | 315 m² |
| stem rings | open | 29.5 | 18.8 | 11.0 | 0.46 (0.43) | 306 m² |
| full rings | open | 25.8 | 12.0 | 5.7 | 0.34 (0.45) | 56 m² |
| pipe (old) | stand | 17.1 | 14.9 | 11.3 | 0.66 (0.48) | 53 m² |
| stem rings | stand | 17.8 | 15.2 | 11.5 | 0.64 (0.48) | 53 m² |
| full rings | stand | 16.6 | 9.9 | 4.8 | 0.42 (0.48) | 28 m² |

- **Open-grown taper is already close to Laasasenaho** (0.45 against 0.43), with any method.
- **The stand stem is a pole:** d at 75 % of height is 2/3 of DBH, and the form factor is 0.66 against 0.48. Stem rings barely change it: DBH rises 0.7 cm.
  - The cause is that stand foliage hardly grows after canopy closure (50–57 m² from age 35 on in the phase-5 run). The pipe model then adds stem wood only through the disused pipes of shed branches, which also thickens the upper stem.
  - Rings would thicken the lower bole only if each year's ring were larger than the year's growth of pipe area, that is, if wood were laid down from carbon rather than from new foliage. That is the full-rings method.
- **Full rings starve the twigs.** With a fixed wood volume per unit carbon, the finest shoots get rings far thinner than their pipes. Twigs end up too thin to hold their foliage, and the crown collapses to 56 m² (open) and 28 m² (stand) of leaves. Making it work needs a separate allocation of carbon between twig extension and stem rings, which the model does not have.
- **Ring widths per year** are in the timeline (`shoot_ring_node`, `shoot_ring_count`, `shoot_ring_width_m`, and the same for roots) for every internode thicker than 1 cm, with the year of each ring.

## Twigs (phase 6)

The wiggle in fine hanging twigs did not come from direction noise. On seed 1 (open, 60), 40 % of fine-twig internodes are year joints: an annual shoot has only about 2.5 internodes. Each year joint takes the sympodial deviation (8°) as one kink.

- Correlated direction noise alone (an Ornstein–Uhlenbeck process along the shoot, 0.3 m correlation length) changed nothing visible.
- **The fix** spreads the sympodial deviation as a curvature over the first 0.1 m of the new shoot (`architecture.sympodial_bend_length_m`), together with the correlated noise.
- The median turn per internode on hanging twigs fell from 7.8° to 3.4°, and the median sinuosity from 1.022 to 1.016. Height, DBH and leaf area changed by less than 1 %.

## Hydraulics check (phase 6)

Seed 1, age 60, against published silver-birch values. "Shoot" is a branch tip carrying 120–250 cm² of leaves, about a current-year shoot (Õunapuu-Pikas et al. 2022: 167 cm²).

| quantity | model, k_s 2 (old) open / stand | model, k_s 4 (default) open / stand | published | source |
|---|---|---|---|---|
| Huber value, shoot (sapwood / leaf area) | 5.7 / 5.8 × 10⁻⁴ | 5.0 / 5.2 × 10⁻⁴ | 1.24 × 10⁻⁴ | Õunapuu-Pikas et al. 2022, Forests 13:594 |
| Huber value, stem at 1.3 m | 0.75 / 1.2 × 10⁻⁴ | 0.65 / 0.97 × 10⁻⁴ | – | – |
| leaf-specific conductivity, shoot (kg m⁻¹ s⁻¹ MPa⁻¹) | 2.1 / 2.4 × 10⁻⁴ | 3.5 / 4.2 × 10⁻⁴ | no birch value found | – |
| whole-tree leaf-specific conductance (mmol m⁻² s⁻¹ MPa⁻¹) | 0.28 / 0.26 | 0.32 / 0.27 | 1.15 (young trees) | Sellin et al., PMC3976162 |
| midday ψ, top leaves (MPa) | −1.96 / −1.49 | −1.68 / −1.39 | −1.0 to −1.3 well watered; −1.9 to −2.1 severe deficit | Sellin et al., PMC3976162 |
| P50, branches (MPa) | none: stomata shut at −2.0 | same | −1.8 (pneumatic), −2.0 (centrifuge); −1.80 | PMC6025199; Klepsch et al. 2018 |

- **Midday ψ was clearly off.** With k_s 2, a well-watered open tree held its top leaves at −2.0 MPa. That is the branch P50, and silver birch only reaches it in severe drought. Doubling k_s to 4 (inside the 1–5 range for diffuse-porous wood) gives −1.7 open and −1.4 in the stand.
- **Whole-tree conductance is still about 4× too low** (0.3 against 1.15). The published figure is for young trees, so it is not directly comparable.
- **The Huber value at the shoot is 4× too high.** The pipe model gives every short shoot a fixed pipe (`spur_radius` 0.8 mm). The model compensates a too-high Huber value with a too-low k_s, so leaf-specific conductivity is probably about right. Changing either needs a measured birch LSC.
- **k_s 4 alone overshoots height:** 29.1 m open and 28.2 m in the stand at 60, against a band of 21.1–26.9 m. In the combined defaults the larger leaves pull it back.
- **There is no embolism model.** Stomata shut at −2.0 MPa, so leaves never pass the branch P50.

## Other

- Limbs that reach the ground layer now stop, and a branch lying there dies. Nodes coming back to the trunk below 3 m fell from 95 to 32 on seed 1 (open), but not to zero.
- Roots near the collar avoid the stem and each other and turn at most 30° per 5 cm segment. Segments heading back to the stem fell by about half in open-grown seed 1 (2435 → 1031) but rose in the stand run (314 → 454). Sharp kinks fell only slightly (3.8 → 3.2 % of collar segments).
- Blender is not installed on this machine. The shaded previews come from the built-in rasterizer (exact rasterization, supersampling, sky and sun light; no shadows).


## Phase 32: Citation re-verification, matched moose test, juvenile growth & long shoot diagnosis, and woody shade

**1. Re-verified citations (triple-checked by independent research subagents):**
- Resolved the DOI collision in Phase 31 (Danell 1985 vs Maillette 1982).
- Debunked the "FAHM" 2.29 m seedling claim (hallucination; real clearcut Swedish/Finnish regeneration sourced).
- Clarified Johansson 1999 (biomass only; optical WAI 0.4–0.9 comes from Kucharik 1998 and Gower 1999).
- Clarified Hale 2012 (turning moment TC; canopy wind decay is Cionco 1972 / Raupach 1994).
- Sourced $k_{\text{wood}} = 0.40$ from four peer-reviewed forestry optics papers.

| Source | Journal / Ref | True DOI / Identifier | Claim / What we use it for | Confirmed |
|---|---|---|---|---|
| Danell et al. 1985 | Ecology 66:1867–1878 | `10.2307/2937382` | Moose browsing on birch twigs; biomass removal vs diameter | Yes |
| Bergström & Danell 1987 | J. Ecol. 75:533–544 | `10.2307/2260432` | Winter moose browsing distribution on Betula shoots | Yes |
| Shipley et al. 1998 | Can. J. Zool. 76:1722–1733 | `10.1139/z98-110` | Pruning mechanics & ungulate bite diameter | Yes |
| Bergqvist et al. 2014 | Forestry 87:419–428 | `10.1093/forestry/cpu007` | Moose browsing height preference (0.3–3.0 m) | Yes |
| Mathisen et al. 2017 | BMC Ecology 17:12 | `10.1186/s12898-017-0122-3` | Moose bite diameter ($2.16 \pm 0.15$ mm, 100% moose on juvenile *B. pubescens* in Norway) | VERIFY (for *B. pendula*) |
| Chaar et al. 1997 | Can. J. For. Res. 27:1614–1621 | `10.1139/x97-128` | Decapitation & apical control release (*Ann. Sci. For.* was ghost citation) | Yes |
| Wilson 2000 | Am. J. Bot. 87:601–607 | `10.2307/2656846` | Apical control & primary branch righting mechanics | Yes |
| Bastien et al. 2013 | PNAS 110:755–760 | `10.1073/pnas.1214301109` | Universal gravitropic rod reorientation ($B = L_{\text{gz}}/L_c \approx 2.0\text{--}5.0$) | Yes |
| Morgan & Cannell 1994 | Tree Physiol. 14:49–62 | `10.1093/treephys/14.1.49` | Uniform stem bending stress under wind ($2.5\text{--}10.0$ m/s) | Yes |
| Niklas & Spatz 2000 | Trees 14:230–240 | `10.1007/s004680050008` | Mechanical safety factors decrease with tree size | Yes |
| Bonnesoeur et al. 2016 | New Phytol. 210:850–860 | `10.1111/nph.13836` | Radial acclimation responds to peak storms rather than daily breezes | Yes |
| Clausen & Kozlowski 1965, 1966 | Nature 205:1030; Can. J. Bot. 44:827 | `10.1038/2051030a0`, `10.1139/b66-096` | Birch heterophylly (preformed early vs neoformed late leaves) | Yes |
| Maillette 1982 | J. Appl. Ecol. 19:203–218, 219–238 | `10.2307/2403005`, `10.2307/2403006` | Birch bud population dynamics (>80–90% short shoots in mature crown) | Yes |
| Tenkanen et al. 2020 | Tree Physiol. 40:198–214 | `10.1093/treephys/tpz124` | Late leaf emergence sequence & season fraction ($f_{\text{late}} \approx 0.5$) | Yes |
| Johansson 1999 | Biomass Bioenergy 16:223–238 | `10.1016/S0961-9534(98)00075-0` | Birch stand dry biomass; stem dimensions in Sweden | Yes |
| Kucharik 1998 / Gower 1999 | Agric. For. Meteorol. 91:69; Rem. Sens. Env. 70:29 | `10.1016/S0168-1923(98)00064-1`, `10.1016/S0034-4257(99)00056-5` | Optical WAI for boreal deciduous stands ($0.4\text{--}0.9\text{ m}^2/\text{m}^2$) | Yes |
| Hale et al. 2012 | Eur. J. Forest Res. 131:203–213 | `10.1007/s10342-010-0448-2` | Turning moment coefficient $TC$ for birch under wind | Yes |
| Cionco 1972 / Raupach 1994 | Bound.-Layer Meteorol. 3:255, 71:211 | `10.1007/BF02033923`, `10.1007/BF00709229` | Canopy exponential wind decay profile $u(z)=u(h)\exp(-\alpha(1-z/h))$ | Yes |
| Granier 2000, Barclay 2000 | Agric. For. Meteorol. 100:291, 100:255 | `10.1016/S0168-1923(99)00151-3`, `10.1016/S0168-1923(99)00091-X` | Deciduous woody extinction factor $k_{\text{wood}} \approx 0.40$ | Yes |
| Duursma & Mäkelä 2007 | Tree Physiol. 27:859–870 | `10.1093/treephys/27.6.859` | Stand woody attenuation coefficient $k_w = 0.40$ | Yes |

**2. Moose test validity (matched 12-year baseline vs Part 1):**
- Previous test was rerun with exact matching baseline and Part 1 on current code (25 trees, 12 years, seed 1, natural mode):

| Metric | Baseline (full shoot killed) | Moose Part 1 ($d_{\text{bite}} = 2.2\text{ mm}$) | Reduction |
|---|---|---|---|
| Total browsed replacements | 25 | 23 | - |
| Median lateral crook $dx_{y1}$ | 0.382 m | **0.041 m** | **89.2%** |
| Maximum lateral crook $dx_{y1}$ | 1.072 m | **0.087 m** | **91.9%** |
| Mean lateral crook $dx_{y1}$ | 0.559 m | **0.045 m** | **91.9%** |

- **Conclusion:** Moose Part 1 alone eliminates large crooked offsets: the lateral crook is held to $\le 8.7\text{ cm}$ (natural stem waviness). Moose Part 2 (special leader righting rule) is officially dropped.

**3. Young-tree growth diagnosis and sourced fertility/temperature plan (diagnosis only):**
- Real clearcut naturally regenerated heights in Sweden/Finland (Johansson 1999; Niemistö 1995; Valkonen et al. 2002; Hynynen et al. 2010):
  - Age 2: $0.15\text{--}0.35\text{ m}$
  - Age 5: $1.2\text{--}1.8\text{ m}$
  - Age 10: $4.5\text{--}6.0\text{ m}$
  - Canopy closure in dense clearcut regeneration: age 4–6 years.
- Model juvenile growth: with leaf fix, height reaches 2.11 m at year 3 (canopy closes at year 3, target 4–6) and 4.11 m at year 5.
- **Why the model is $1.5\text{--}2\times$ fast:** Current photosynthesis operates at unconstrained maximum fertility ($\alpha = 4.8$, fertile agricultural field, Aosaar et al. 2016) and standard daylight hours without growing-degree-day (GDD) or temperature limits.
- **Sourced plan for Open Issue 3 (Fertility & Temperature Limits):**
  - Do not artificially downscale juvenile growth.
  - Implement Swedish site-index allometry ($H_{50} = 18\text{--}30\text{ m}$, Eriksson et al. 1997 / Skogsstyrelsen):
    1. Thermal constraint: scale growing season length and maximum daily assimilation via GDD ($> 5^\circ\text{C}$ sum, e.g. 1100–1300 day-degrees for southern boreal Sweden; Bergh et al. 1998, *Tree Physiol.* 18:23).
    2. Nutrient/fertility scalar $\phi_{\text{site}} \in [0.6, 1.0]$: maps stand soil class (poor till vs fertile loam) directly to canopy assimilation $\alpha = 4.8 \times \phi_{\text{site}}$, matching the site curves without tuning.

**4. Mature long shoots count and carbon allocation diagnosis (seed-1 stand tree):**
- Evaluated metamer extension per growing axis across mature ages:

| Age | Growing Axes | Long Shoots (>1 metamer) | Short / Single-Metamer Shoots | Median Increment | Max Increment (Tree-Wide) | Active Spurs |
|---|---|---|---|---|---|---|
| 10 | 721 | 650 (90.2%) | 71 (9.8%) | 0.110 m | 0.478 m | 1,536 |
| 20 | 153 | 1 (0.7%) | 152 (99.3%) | 0.005 m | 0.052 m | 4,943 |
| 30 | 470 | 0 (0.0%) | 470 (100.0%) | 0.004 m | 0.029 m | 9,358 |
| 40 | 799 | 0 (0.0%) | 799 (100.0%) | 0.006 m | 0.033 m | 11,440 |
| 50 | 953 | 142 (14.9%) | 811 (85.1%) | 0.014 m | 0.169 m | 14,664 |
| 60 | 622 | 0 (0.0%) | 622 (100.0%) | 0.004 m | 0.011 m | 16,213 |

- **Diagnosis:**
  - Real mature birch crowns are overwhelmingly short shoots (>80–90%, Maillette 1982).
  - The model matches this dominance, but dips to strictly 0 long shoots at 30, 40, and 60.
  - **Mechanism:** In mature trees, conducting sapwood ring construction (Huber distance rule + 1.4%/yr sapwood turnover) consumes 95–99% of the net shoot carbon pool. The remaining pool distributed across hundreds of competing buds yields growth factor $v \approx 1.0$, exactly hitting the 1-metamer (4 mm) threshold for terminal bud survival as a short shoot. Reiterations (e.g. at age 50) temporarily concentrate carbon to produce 142 extending shoots.

**5. Woody shade implementation & results (`light.woody_shade.enabled`):**
- Built woody shade attenuation in voxel light grid (`treegen/light.py`, `species/betula_pendula.yaml`, `treegen/growth.py`, `treegen/plot.py`, commit `9a4a91f`).
- Default: `enabled: false`, $k_{\text{wood}} = 0.40$.
- **Stand floor light check on Year-58 Plot Checkpoint (`out/bench/p26_nat/checkpoint.pkl`, 95 trees, plot WAI = 0.741):**
  - Height 2.0 m: Baseline 24.1% $\to$ **Woody Shade 18.5%** [Hagemeier & Leuschner target 10–15%].
  - Height 3.5 m: Baseline 24.0% $\to$ **Woody Shade 18.7%**.
  - Height 5.0 m: Baseline 23.9% $\to$ **Woody Shade 19.0%**.
  - Confirmed: Under-canopy light drops cleanly below the 21% shedding threshold.
- **Seed-1 stand tree growth alone to age 60 (tested alone, woody shade ON vs Baseline OFF):**

| Run | Age | H (m) | DBH over bark (cm) | H/D over bark | Lowest live limb (m) | Crown ratio | Total 1st-order limbs | Small limbs (<1 cm / <2 cm) | Foliage (kg) | / Repola Eq. 12 | / Repola A6 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Baseline | 10 | 9.36 | 10.02 | 93.4 | 7.00 | 0.25 | 87 | 79 / 87 | 0.48 | 0.58 | 0.79 |
| Woody shade | 10 | 9.43 | 9.83 | 96.0 | 6.54 | 0.31 | 86 | 81 / 86 | 0.45 | 0.58 | 0.66 |
| Baseline | 30 | 18.01 | 18.45 | 97.7 | 8.91 | 0.51 | 131 | 102 / 127 | 2.16 | 0.55 | 0.61 |
| Woody shade | 30 | 19.09 | 18.43 | 103.6 | 6.54 | 0.66 | 171 | 140 / 171 | 2.21 | 0.56 | 0.41 |
| Baseline | 50 | 23.57 | 26.14 | 90.2 | 8.91 | 0.62 | 168 | 109 / 155 | 3.45 | 0.46 | 0.45 |
| Woody shade | 50 | 24.94 | 24.57 | 101.5 | 6.54 | 0.74 | 132 | 75 / 125 | 2.94 | 0.43 | 0.30 |
| Baseline | 60 | 25.71 | 28.52 | 90.1 | 8.91 | 0.65 | 142 | 98 / 127 | 3.74 | 0.43 | 0.41 |
| Woody shade | 60 | 26.44 | 27.09 | 97.6 | 6.54 | 0.75 | 142 | 82 / 131 | 3.33 | 0.41 | 0.29 |

- **Observations:** On a single stand tree thinned down to 450 stems/ha (4.7 m tree spacing, LAI ~2.8), the under-canopy light remains > 25% even with woody shade, so the lowest limb does not self-prune higher. In contrast, in dense multi-tree plots (LAI ~4.1), woody shade drops floor light from 24% to 18.5%, triggering self-thinning.

**6. Upkeep switch comparison on dense young regeneration:**
- Evaluated 10-year dense regeneration stand (9,900 stems/ha, 44 trees, 44.4 m², seed 1) with upkeep switch OFF vs ON:
- Results: Tree survival counts, heights, LAI, and light are **100% identical** across all 10 years (44 alive at yr 3, LAI 5.05, light 15%; 41 at yr 5; 32 at yr 6; 23 at yr 10).
- Conclusion: Thinning in young stands is driven purely by light starvation (< 21%) following canopy closure, not wood maintenance.



## Phase 33: Combined natural plot (p33_nat), carbon budget deconstruction, young growth vs Swedish site curves, and wind acclimation resolution

**1. Combined natural plot run (`out/bench/p33_nat`, Task 1):**
- Setup: 100 trees initial, 23.6 m square plot (555.6 m²), seed 1, natural mode, 60 years. Leaf fix ON, moose browsing part 1 ON (leader clipped to 2.16 mm bite diameter), woody shade ON ($k_{\text{wood}} = 0.40$), wind rule OFF, upkeep switch OFF.
- Simulation runtime: 1,342 s, peak memory 5,007 MB.

| Metric | Year 30 | Year 45 | Year 50 | Year 60 | Reference / Target |
|---|---|---|---|---|---|
| Living Stems ($N/\text{ha}$) | 94 (1,692/ha) | 90 (1,620/ha) | 88 (1,584/ha) | 84 (1,512/ha) | Natural self-thinning |
| Cumulative Deaths | 6 (5 died, 1 failed) | 10 (9 died, 1 failed) | 12 (11 died, 1 failed) | 16 (15 died, 1 failed) | Woody shade accelerates thinning (+11 vs p26_nat) |
| DBH under bark (cm) | 12.80 ± 3.68 (0.4–21.8) | 14.82 ± 4.13 (0.5–25.6) | 15.37 ± 4.18 (0.5–26.6) | 16.38 ± 4.52 (0.5–26.9) | Model wood diameter |
| DBH over bark (cm) | 14.00 ± 4.04 (0.4–23.9) | 16.23 ± 4.53 (0.5–28.1) | 16.83 ± 4.59 (0.5–29.1) | 17.93 ± 4.96 (0.5–29.5) | Hansen et al. 2023 over-bark |
| Height mean (m) | 18.29 | 23.24 | 25.10 | 27.15 | Stand mean |
| Top 25% Height (m) | 20.09 | 25.09 | 27.32 | 29.94 | Dominant canopy height |
| Eriksson 1997 band (m) | 13.44–19.67 (SI24=17.50) | 18.06–24.30 (SI24=22.20) | 19.20–25.31 (SI24=23.27) | 21.05–26.87 (SI24=24.93) | Swedish birch SI20–SI26 band |
| Basal Area over bark (m²/ha) | 28.23 | 36.12 | 37.86 | 41.13 | Boreal natural birch stands |
| H/D over bark (stand mean) | 130.6 | 143.2 | 149.1 | 151.4 | Mean H / Mean DBH_ob |
| H/D over bark (individual mean) | 144.7 | 156.4 | 161.3 | 163.8 | Arithmetic mean of H/D |
| Live Crown Ratio | 0.56 | 0.42 | 0.37 | 0.35 | Hynynen 2010 target ≥0.50 (dense natural) |
| Plot LAI | 3.413 | 3.470 | 2.764 | 3.535 | Hagemeier & Leuschner 2019 (2.5–4.5) |
| Mean Foliage dry mass (kg) | 1.08 | 1.14 | 0.89 | 1.17 | Model leaf dry mass / tree |
| Foliage vs Repola Eq. 12 | 0.47x | 0.36x | 0.26x | 0.30x | Repola 2008 Eq. 12 (DBH only) |
| Foliage vs Repola A6 | 0.36x | 0.41x | 0.32x | 0.41x | Repola 2008 A6 (DBH + Crown Ratio) |
| Sub-canopy Light (2.0–5.0 m) | 24.1% – 24.5% | 22.8% – 23.2% | 28.9% – 29.3% | 21.2% – 21.8% | Hagemeier & Leuschner 2019b: 6.4–19.8 %, diffuse light on the forest floor, sensor height not stated (corrected in campaign M1; the model reads 1.0–2.0 m). Not the same heights or the same light as this row, and every value here is above that range. (Corrected in campaign M1d; this cell said "Hagemeier 10–15% (approaching target)".) |

- **Mortality Diagnosis:**
  - 16 total deaths across 60 years. 1 seedling failed to establish at year 3 (`failed to establish`, Tree 82).
  - 15 trees died from light starvation and negative carbon balance (`died`): Tree 15 (yr 8), Tree 76 (yr 17), Tree 95 (yr 19), Tree 75 (yr 29), Tree 94 (yr 30), Tree 64 (yr 32), Tree 17 (yr 38), Tree 05 (yr 39), Tree 35 (yr 41), Tree 21 (yr 46), Tree 86 (yr 48), Tree 18 (yr 51), Tree 83 (yr 51), Tree 33 (yr 52), Tree 26 (yr 53).
  - All 15 natural deaths occurred in shaded, carbon-starved trees across a range of sizes: 1 juvenile sapling (Tree 15, yr 8, final H 0.30 m, DBH 0.00 cm), 13 sub-canopy suppressed poles (final heights 4.5–23.8 m, DBHs 1.1–12.6 cm), and 1 mature codominant tree (Tree 18, yr 51, final H 25.68 m, DBH 17.91 cm) whose crown thinned in the dense canopy until upkeep exceeded carbon assimilation two years running.
  - Deaths rose from 5 in p26_nat to 16 in p33_nat. p33_nat changed several things at once (it combines the leaf fix, moose browsing and woody shade, on later code than p26_nat), so the rise can't be credited to woody shade alone. Light at 2–5 m stayed above 21 % at all four ages in the table above (21.2–29.3 %). (Corrected in campaign M1d; this line said woody shade "successfully reduced under-canopy light below the 21% compensation threshold, tripling natural self-thinning mortality".)

**2. Carbon budget diagnosis (seed-1 stand tree, Task 2):**
- Annual carbon balance evaluated on seed-1 stand tree with woody shade enabled to age 60:

| Age | GPP | WoodMnt | LfBld | LfMnt | RtMnt | Net Pool | Shoot Extension | Sapwood Rings | Ring % of Pool | CUE (NPP/GPP) |
|---|---|---|---|---|---|---|---|---|---|---|
| 10 | 9,151 | 1,131 | 6 | 767 | 434 | 3,008 | 1,097 | 3,572 | 118.8% | 0.519 |
| 20 | 23,130 | 3,938 | 1,663 | 2,902 | 1,640 | 8,819 | 0 | 8,819 | 100.0% | 0.507 |
| 30 | 42,764 | 7,517 | 3,404 | 5,708 | 3,225 | 15,337 | 174 | 15,150 | 98.8% | 0.492 |
| 40 | 51,281 | 7,822 | 3,337 | 5,411 | 3,058 | 21,155 | 794 | 20,926 | 98.9% | 0.541 |
| 50 | 58,965 | 11,556 | 5,121 | 7,425 | 4,195 | 19,295 | 749 | 19,191 | 99.5% | 0.480 |
| 60 | 62,706 | 14,726 | 5,725 | 8,583 | 4,850 | 17,764 | 435 | 17,401 | 98.0% | 0.440 |

- **Sapwood Ring Allocation Deconstruction:**
  - Huber distance rule ($hv = hv_0 (\ell / \ell_{\text{ref}})^c$, $c = 0.283$) accounts for **54%–86%** of total ring wood demand: 85.9% at age 20 (7,575 / 8,819), 80.4% at age 30 (12,181 / 15,150), 77.1% at age 40 (16,131 / 20,926), 65.4% at age 50 (12,546 / 19,191), and 53.7% at age 60 (9,339 / 17,401).
  - Sapwood turnover replacement ($1.4\%/\text{yr}$) takes **13.5%** at age 20 rising monotonically to **45.6%** at age 60 (7,927 / 17,401).
  - New leaf sapwood demand is negligible (**~0.6%–1.4%**, 51–291 units).
  - Stem vs Branch partitioning: **95.4%–98.9%** of all ring carbon is deposited in the main stem; branches receive only **1.1%–4.6%**. Combined with ring priority over shoot elongation, branch tips are starved of carbon, explaining why mature branches produce 0 long shoots and stop expanding.
- **Pulsatile Leader Growth:**
  - Observed, not explained: height growth does not advance at a steady 0.28 m/yr. It advances via intermittent flushes (phase 40: why the whole tree grows long shoots only every other year is not diagnosed; corrected in campaign M1d, this line began "Solved the leader growth paradox"): Yr 23 = 0.845 m (33 metamers), Yr 27 = 1.175 m (47 metamers), Yr 29 = 0.790 m, Yr 31 = 0.675 m, Yr 35 = 0.855 m, Yr 38 = 0.693 m, Yr 43 = 0.505 m, interspersed with resting single-metamer short-shoot years (0–4 mm).
- **Lowest Live Limb Persistence (6.54 m):**
  - Axis 4279 (born year 8) survives to year 60 (age 52) with 133 internodes and 229 leaves.
  - In a managed stand thinned to 450 stems/ha (4.7 m tree spacing), lower canopy light remains at 78%–161% of open sky, far above the 21% shedding threshold. The limb fixes surplus carbon annually and never starves.

**3. Young-tree growth shape diagnosis vs Swedish site-index curves (Task 3):**
- Normalized height $H(t) / H_{50}$ across ages 5 to 60 compared to Eriksson, Johansson & Kiviste (1997) Hossfeld IV curves:

| Total Age | Model Stand H (m) | Model $H(t)/H_{50}$ | E97 SI20 $H(t)/H_{50}$ | E97 SI24 $H(t)/H_{50}$ | E97 SI26 $H(t)/H_{50}$ | E97 SI28 $H(t)/H_{50}$ | Periodic Annual Increment (m/yr) | E97 SI26 PAI (m/yr) |
|---|---|---|---|---|---|---|---|---|
| 5 | 5.76 | **0.231** | 0.079 | 0.071 | 0.070 | 0.069 | **1.15** | 0.09 |
| 10 | 9.43 | **0.378** | 0.196 | 0.222 | 0.240 | 0.260 | 0.73 | 0.86 |
| 15 | 13.77 | 0.552 | 0.336 | 0.387 | 0.417 | 0.448 | 0.87 | 0.90 |
| 20 | 15.96 | 0.640 | 0.472 | 0.532 | 0.565 | 0.598 | 0.44 | 0.75 |
| 25 | 17.07 | 0.684 | 0.593 | 0.653 | 0.684 | 0.712 | 0.22 | 0.60 |
| 30 | 19.09 | 0.765 | 0.700 | 0.752 | 0.777 | 0.800 | 0.40 | 0.47 |
| 40 | 23.16 | 0.929 | 0.872 | 0.899 | 0.911 | 0.922 | 0.41 | 0.34 |
| 50 | 24.94 | **1.000** | **1.000** | **1.000** | **1.000** | **1.000** | 0.18 | 0.22 |
| 60 | 26.44 | **1.060** | 1.097 | 1.072 | 1.061 | 1.053 | 0.15 | 0.16 |

- **Diagnosis:**
  - At ages 0–5, the model grows at 1.15 m/yr, reaching 5.76 m (23.1% of $H_{50}$), whereas Swedish birch takes 4 years just to reach breast height (1.3 m) and reaches only 1.76 m (7.0% of $H_{50}$).
  - Above age 25, the curves converge tightly: at age 30, model is 19.09 m vs E97 SI26 19.67 m (97%); at age 50, 24.94 m vs 25.31 m (98.5%); at age 60, 26.44 m vs 26.87 m (98.4%).
  - **Sourced Explanation of Juvenile Slowdown:**
    1. *Weed & Field Layer Competition:* Understory graminoids (*Deschampsia*, *Calamagrostis*) and ericaceous shrubs strongly intercept light and monopolize soil mineral nitrogen (Valkonen 2000; Hynynen et al. 2010). The model provides unconstrained nutrients and full open light to germinants.
    2. *Root Establishment Fraction:* Natural seedlings allocate a high share of photosynthate to establishing deep taproots and laterals before vertical stem elongation (Laitakari 1935; Niemistö 1995).
    3. *Ground Microclimate & Frost:* Night inversions, ground frosts, and cold soils retard spring shoot elongation near the ground (Bergh et al. 1998, 2003).
    4. *Herbivory:* Heavy cropping by voles, hares, and deer repeatedly clips juvenile leaders under 1.5 m (Hynynen et al. 2010).

**4. Literature & Citation Verification (Task 4):**

| Citation | What we use it for | True DOI / URL | Confirmed | Notes |
|---|---|---|---|---|
| Niemistö 1995 (Scand. J. For. Res. 10:245) | Spacing & yield of silver birch | `10.1080/02827589509382890` | Yes | Top height is invariant to spacing (400–3,100/ha) in juvenile birch (ages 2–10). |
| Niemistö 1995 (Scand. J. For. Res. 10:235) | Crown & branch properties of birch | `10.1080/02827589509382889` | Yes | Measured stands 11–22 yr. Self-pruning initiation at stand height 4.5–5.5 m (ages 6–8) synthesized with Mäkinen et al. 2003 and Hynynen et al. 2010. |
| Valkonen, Ruuska & Siipilehto 2002 (For. Ecol. Manage. 166:227) | Overstory retention & seedling suppression | `10.1016/S0378-1127(01)00668-5` | VERIFY (Pinus) | Studied Pinus sylvestris overstory retention (5–10 m suppression radius); extrapolated to Betula. Clearcut birch regeneration (5,000–20,000/ha) is general Nordic silviculture (Sarvas 1948, Hynynen 2010). |
| Hynynen et al. 2010 (Forestry 83:103) | Birch silviculture in Northern Europe | `10.1093/forestry/cpp035` | Yes | Live crown ratio target ≥50%; cleaning/PCT before dominant height reaches 5–7 m. |
| Bergh, McMurtrie & Linder 1998 (For. Ecol. Manage. 110:127) | Temperature & nutrition scalars on forest NPP | `10.1016/S0378-1127(98)00280-1` | Yes | Caught phantom citation (Tree Physiol. 18:23 did not exist). Correct FEM 110:127 and Bergh 2003 FEM 183:327 (Betula pendula). |
| Eriksson, Johansson & Kiviste 1997 (Scand. J. For. Res. 12:149) | Swedish birch Hossfeld IV site-index curves | `10.1080/02827589709355396` | Yes | Sourced paper. Table quotes anamorphic equation ($m=1.480, c=405.0$); codebase and diagnostics use polymorphic Kiviste model (treegen/reference.py, asi=7, beta=394, b2=1.387). |
| Bonnesoeur et al. 2016 (New Phytol. 210:850) | Thigmomorphogenesis wind frequency filtering | `10.1111/nph.13836` | Yes | Minimal Effective Strain threshold ($\epsilon_{\text{MES}} \in [0.04\%, 0.15\%]$) filters out daily 3–5 m/s breezes; responds to 11–22 m/s gusts. |
| Morgan & Cannell 1994 (Tree Physiol. 14:49) | Uniform stem bending stress under wind | `10.1093/treephys/14.1.49` | Yes | Uniform stress taper profile is invariant over 2.5–10 m/s; 15–20 m/s storms cause large deflection that concentrates stress at stem base. |

- **Resolution of Wind Acclimation:**
  - Daily breezes (3–5 m/s) do not trigger secondary thickening because strains fall below the MES threshold ($\epsilon < 0.04\%$) and trigger accommodative desensitization (Coutand & Moulia 2000; Frost 2003; Telewski 2006).
  - 50-year design storms (20–25+ m/s) cannot physiologically guide annual cambial growth because they occur decades apart and deflection (>50%) breaks uniform stress (Morgan & Cannell 1994).
  - Frequent synoptic storms / gusts (10–14 m/s, return period 1 week to 1 year) exceed the MES threshold, triggering cambial stimulation (+79% growth rate, +76% to +156% radial wood).
  - Designing stems to maintain working stress $\sigma_{\text{target}} \approx 18\text{ MPa}$ under recurring 12 m/s winds automatically provides safety factor $SF \approx 1.5$ against a 25 m/s storm.
  - Canopy wind load sharing: wind decays exponentially inside the canopy ($u(z) = u(h_c) e^{-\alpha(1-z/h_c)}$). A suppressed tree with $z/h_c = 0.5$ receives $<10\%$ of the aerodynamic drag force of a canopy-dominant tree, sheltering suppressed stems until thinning.


## Phase 37 & 38: Stem Theory Stage b Default, Taper, Leader Alternations, and Carbon Accounting Corrections

**1. Stem Theory Stage b Adopted as Default (`pipe_model.stem_theory.stage: 2`).**
- **Architecture**: Plain pipe model below the live crown base ($c = 0$, $b = 0$, $A_s(z) = A_s(H_c)$), surplus sapwood retired to heartwood (`crown_rise_heartwood`), coupled with the mechanical wind envelope (frequent synoptic wind $u_h = 12.0\text{ m/s}$ at canopy top, target bending stress $\sigma = 18.0\text{ MPa}$, and exponential within-canopy wind speed decay $u(z) = u(h_c)\exp[a(z/h_c - 1)]$ with $a = 2.0$ from Inoue 1963 / Cionco 1972).
- **Changes** (corrected in phase 40; the original wording used banned words without scorecard support): the empirical path-length exponent ($c = 0.283$) is no longer used on the stem (stage ≥ 1 sets $b = c = 0$, `treegen/growth.py`). Seed-1 stand-tree height at 50 and 60 is 25.02 m and 26.11 m. Those values lie inside the Eriksson et al. 1997 SI20–SI26 band of 19.20–25.31 m and 21.05–26.87 m (scorecard PASS, `out/bench/p40_default/scorecard.txt`, phase 40). They are below the SI26 curve itself, so this does not match SI26. Stem wood is 1.01–1.14 × Repola 2008 at 30–60 (`out/bench/p40_default/stem_compare.txt`); there is no approved target for it. The claim that the form factor is "stabilized" gave no numbers and is withdrawn.
- **Open problems with stage b** (items 2–4 and section 2 corrected in phase 40 against `out/bench/p40_default/stem_compare.txt`; the original run behind them was not saved under a known path):
  1. *Leader Alternation Persists*: Height increments still oscillate heavily between burst and stall years (e.g. 1.175 m at yr 24 followed by -0.001 m at yr 25; 0.721 m at yr 34 followed by 0.027 m at yr 35).
  2. *Mid-stem taper*: the stem is thicker than the Hansen et al. (2023) under-bark taper at 0.3 / 0.5 / 0.7 H by 11 / 8 / 10 % at 40, 12 / 12 / 16 % at 50 and 14 / 15 / 22 % at 60 (the original "12–20 %" held at 50 only).
  3. *Branch wood*: living branch wood / Repola (2008) is 0.12 / 0.17 / 0.15 / 0.12 / 0.11 at 20 / 30 / 40 / 50 / 60. The original "0.16–0.27 in baseline" has no saved run, and its mechanism ("the wind bending moment allocates additional carbon to the lower trunk") was asserted, not tested.
  4. *Form factor*: Hansen et al. (2023) taper gives an under-bark form factor of 0.47 at 20 and 0.39–0.44 at 30–60; the model stem gives 0.45–0.47 (the original "0.46–0.48" has no saved run).

**2. Withdrawal of Phase 36 Ring Decomposition.**
- The Phase 36 ring-carbon decomposition table (claiming 44.2% was spent on sapwood senescence replacement) is **formally withdrawn**.
- *Reason*: The Phase 36 report assumed an invented turnover rate of 5%/yr (0.05). In reality, the codebase uses `sapwood_senescence_per_year: 0.014` ($1.4\%/\text{yr}$, Gebauer et al. 2008). At 0.014/yr, lifetime turnover replacement requires only 6.5% of net shoot carbon, not 44%.
- *Phase 40 note*: no phase 36 report or table was saved (only `scratch/task1_turnover_share.py`), so neither the 44.2 % nor the 6.5 % figure can be recomputed; both are unverified.

## Phases 34–36 (reconstructed in phase 40 from git history and saved files)

These phases were run by another agent and left no notes. What follows comes from the commits, the files they changed, `scratch/` timestamps and DECISIONS.md. **The phase boundaries cannot be reconstructed:** the commit messages carry no phase numbers. DECISIONS.md (the maintainer's numbering) places the light-target change in phase 36 and the crown-ratio limit in phase 37. The commit times below are 2 Nov 2026.

| Time | Commit | What changed | Default | Status now |
|---|---|---|---|---|
| ~03:00–03:12 | (scratch only: `apply_accounting_fix.py`, `verify_exact_carbon.py`) | Investigation of the late-shoot carbon bookkeeping | — | Not reconstructable beyond the scripts |
| 07:41 | `aa96c05` | `reference/targets.yaml` created | — | Rewritten with checkable condition labels in `7c70674` |
| 07:42 | `efc93c3` | Late-leaf carbon is added to the carbon totals (`carbon["shoot"]`, `["root"]`, upkeep, CUE) | changes reporting only | Kept (round-39 audit: bookkeeping only) |
| 08:05 | `592f7da` | Crown-rise heartwood: sapwood below the rising crown base is retired to heartwood (`pipe_model.crown_rise_heartwood`) | off; forced on by stem theory stage ≥ 1 | Active through stage 2 |
| 08:24 | `d9c9b90` | Citation fixes in targets.yaml and KNOWN_ISSUES.md | — | — |
| 08:56 | `24886b0` | Light-under-canopy target widened from 10–15 % to the measured 6.4–19.8 % (median 14.8 %); crown-ratio targets split into managed and dense | — | Approved by the maintainer (DECISIONS.md row 5, phase 36) |
| 09:18 | `49b3dac` | Field-layer competition for seedlings (Nilsson & Örlander 1999) | off | Not re-checked in phase 40 |
| ~09:44 | (scratch: `task1_turnover_share.py`) | Ring-carbon decomposition that assumed a 5 %/yr sapwood turnover | — | **Withdrawn** in the phase 37 & 38 notes (the code uses 0.014/yr) |
| 09:53 | `a0c1b49` | Dense-stand crown ratio 0.30–0.45 limited to ages 11–22 | — | Approved by the maintainer (DECISIONS.md row 6, phase 37) |

Commits between these phases and phase 39, which the phase 37 & 38 notes do not list. The phase is inferred: DECISIONS.md puts the stage-b default in phase 38, and output names such as `out/bench/p38_germ_*.json` point to phase 38.

| Time | Commit | What | Default | Phase |
|---|---|---|---|---|
| 12:27 | `f6ecda0` | Stem theory stages a and b implemented | off | 37 (inferred) |
| 13:18 | `72ce4e5` | Stage b made the default | on | 38 (DECISIONS.md row 7) |
| 14:24 | `42c2c2e` | Seedling germination option | off | 38 (inferred from `p38_germ_*` outputs) |
| 14:36 | `236c2d4` | Konôpka et al. 2023 citation corrected in targets.yaml | — | 38 (inferred) |
| 14:37 | `35b6484` | VERIFY tags on germination parameters | — | 38 (inferred) |

No scorecard existed in phases 34–36, so none of their results carry PASS/FAIL. Saved run outputs from these phases could not be identified in `out/`.

## Phase 39 (reconstructed in phase 40)

Round 39 ran out of usage before its notes, before/after tables and checker pass. The commits:

| Time | Commit | What | Default | Status now |
|---|---|---|---|---|
| 15:11 | `46099bd` | PROTOCOL.md added | — | Amended by the maintainer (`98c9810`, `31cb4cb`) |
| 15:17 | `32bbe54` | `tools/scorecard.py` | — | **Withdrawn as it stood.** It filled in a light value of 22.0 % for runs named `p38_nat`, hard-coded its ranges and invented tolerances (audit, `reports/claude_audit.md`). Replaced in `e0b8d10` and `f291a99`. Every PASS/FAIL produced before `e0b8d10` should be disregarded. |
| 15:50 | `ab046e6` | Published Borchert–Honda option (`bud_fate.borchert_honda_published`) | off | Tested alone in phase 40 |
| 16:03 | `aeb2d68` | Soil-water bucket option | off | Its invented pieces replaced in phase 40 (`9885e03`) |

Test runs saved by round 39: `out/test_bh_pub`, `out/test_swb_norm` and `out/test_swb_dry`. These were made with the round-39 code and options; the phase 40 runs supersede them.

## Phase 40: published Borchert–Honda tested, run outputs, soil water to BILJOU, germination and branch audits

All runs are the seed-1 stand tree, 60 years. Each option was tested in a species copy that differs from `species/betula_pendula.yaml` in the named option only. The exception is the copies made before `9885e03` (`p40_bhpub`, `p41_germ`), which also carry the older, inactive soil-water block (the option is off there). The full report is `reports/phase40.md`.

**1. Published Borchert–Honda (`bud_fate.borchert_honda_published`, off), alone.**
Answer: it does not remove the see-saw, which gets larger.
- **The split:** the extended Borchert–Honda model of Palubicki et al. 2009, a computer-graphics model formulation adapted to light (Borchert & Honda 1984 not opened): v_m = v λQ_m / (λQ_m + (1−λ)Q_l). Code: `treegen/growth.py:906-910`.
- **What the option changes:** λ = `resource.apical_dominance` (0.62, VERIFY; Palubicki et al. illustrate 0.46–0.54) at every node (`:893-894`), and gravimorphism and scaffold vigour are left out of the bud pull (`:870-873`).
- **What still shapes the split:** the water factor φ, the upkeep, spurs as non-sinks (`short_shoots_self_financing`, `:878-883`) and the no-axillary-bud rule (`:886`). Transport attenuation is not set in the species file, so it has no effect (`:904`).
- **Run:** `out/bench/p40_bhpub/1_stand` against `out/bench/p40_default/1_stand`; tables in `out/bench/p40_bhpub/leader_compare.txt`. "Increment" below is the yearly change in tree height.

| | default | published BH |
|---|---|---|
| height 50 / 60 (m) | 25.02 / 26.11 | 25.00 / 27.35 |
| scorecard height 20 / 30 / 40 / 50 / 60 | FAIL / FAIL / FAIL / PASS / PASS | FAIL / PASS / PASS / PASS / FAIL |
| stand LAI 50 / 60 (target 3.6–5.4) | 2.99 / 2.95 FAIL | 2.59 / 2.61 FAIL |
| height increment yrs 21–60: mean / SD (m) | 0.273 / 0.248 | 0.320 / 0.355 |
| mean change from one year to the next (m) | 0.272 | 0.502 |
| years with increment < 0.10 m (of 40) | 14 | 15 |
| years with no new long shoot anywhere on the tree (whole run) | 1 (year 17) | 10 (18, 23, 29, 32, 34, 36, 38, 40, 44, 46) |
| living branch wood / Repola at 50 / 60 | 0.12 / 0.11 | 0.12 / 0.22 |

- **Render:** `out/renders/p40/stand_tree_seed1_age60_default_vs_bhpub.png`. With BH on, the top quarter of the crown is a bare leader, one large limb sits mid-crown, and the lower crown still has bands.
- **Likely mechanism, not tested:** the default lowers apical control on established branches from 0.60 to 0.50 with age (`apical_control`, `:445-448`). BH keeps 0.62 everywhere, so more of each split goes to the main axis. That fits the taller tree (27.35 m) and the smaller leaf area. Why the whole tree grows long shoots only every other year is **not diagnosed**.

**2. Run outputs (output only; `bc4387d`).**
Answer: done. Every stand-tree and plot run now saves `subcanopy_light_pct` per year, plus `run_manifest` and `options`.
- **Light:** the mean of exp(−s/C) over every column of the stand cell at 1.0, 1.5 and 2.0 m (`treegen/light.py:224`, `:270-285`). This is the model's weighted sky-and-sun light, **not diffuse-only**, whereas the target measures diffuse PAR.
- **Manifest:** git commit and tracked-changes flag, species and environment files with SHA-256, and the options switched on (`treegen/params.py:38-98`; `cli.py`; `tools/plot.py`).
- **Growth unchanged:** `p40_default_v2` and `p41_germ_v2` match p40_default and p41_germ in every per_year value and timeline array.
- **Light values:** default 30.1 % at 50 and 29.6 % at 60; germination 30.1 % / 30.1 %. The target is 6.4–19.8 %, but this is **not scored**: tools/scorecard.py reads only a run-level value (decision for the maintainer).
- **Manifest caveat:** these runs were made before their code was committed (`git_tracked_changes: true`).

**3. Germination option (audit only).**
Answer: no published relation between leaf size and height, age or node was found for young Betula. The leaf-size ramp `min(max(0.20 + 0.80·H/1.30, 0.20), 1)` (`treegen/growth.py:1236-1242`) is an invented scaling function.

| Parameter (used at) | Source status |
|---|---|
| `seed_dry_mass_mg` 0.21 (`growth.py:796`) | Cited papers not opened. USDA Woody Plant Seed Manual, Betula, Table 4: ~0.19 mg per cleaned de-winged seed (range 0.09–0.30). VERIFY |
| `germination_respiration_fraction` 0.35 (`:797`) | Cited sources not opened; no Betula source found. VERIFY |
| `hypocotyl_height_m` 0.015 (`:136`) | No source. VERIFY |
| `first_year_effective_leaves` 0.20 (`:227`) | Its own comment calls it calibrated. Konôpka et al. 2023 has no first-year data. VERIFY |
| `juvenile_scale_bh_m` 1.3, `min_juvenile_scale` 0.20 (`:1238-1239`) | No source. VERIFY |
| `cotyledon_area_cm2` 0.05, `initial_taproot_depth_m` 0.02 | Not used by the code |

VERIFY flags were added to the comments in the species file; no value changed. Options for the leaf ramp are a decision for the maintainer (`reports/phase40.md`).

**4. Soil-water option (`9885e03`, still off).**
Answer: the invented pieces were replaced. The option has no effect on growth with Uppsala rain, even in 2018.

| Invented (round 39) | Now |
|---|---|
| transpiration factor 0.25 + 0.75·min(1, LAI/3) | Tmax = r·PET, r = 0.125·LAI up to 0.75 (Granier, Bréda, Biron & Villette 1999, Eq. 2, p. 271: the relationship the authors adopted) |
| monthly step with a half-month rain midpoint | BILJOU's daily balance (Eq. 1) with each month's rain and PET spread evenly over its days |
| open-grown "LAI" = min(3.5, leaf area / 10) | leaf area over the crown projection, as `measure()` defines LAI |
| drought = rain × 0.5, PET × 1.2 | the actual 2018 rain at Uppsala 97520 (SMHI) |

- **Kept:** the linear decline of T below REW 0.4 (Granier 1999 p. 271; Sopharat et al. 2015 Eqs. 9–10).
- **Unsourced (VERIFY), stated in the code:**
  - carbon cut by the season's T/Tmax (`treegen/growth.py:787-791`);
  - the season starts at field capacity on 1 May;
  - no 30-day rise of r after budburst;
  - no interception term (BILJOU's is a daily-rain equation);
  - the 75 mm water capacity.
- **Result:** the lowest REW is 1.0 every year in the normal year, and 0.566 in 2018 (age 59; 0.578 at 50, 0.580 at 60). That is above 0.4, so T/Tmax = 1.0 and growth is identical to the default (`out/bench/p40_swb_norm`, `p40_swb_dry`).
- **Why, in numbers:** at LAI 2.99, Tmax = 0.374·PET = 30 / 37 / 39 / 26 / 11 mm for May–Sep. The normal rain of 39 / 61 / 57 / 74 / 49 mm exceeds that every month. May–Sep 2018 was 272 mm against 280 mm.

**5. Branch mechanics (design only).**
Answer: the sources support sizing wood by self-weight in principle, and the model already does it. A load rule would not add branch wood: the limbs are already thicker than their load needs. The shortfall against Repola is limb length and number, not thickness.
- **Already in the model:** the stress floor (`pipe_model.stress_floor`, on; `treegen/growth.py:1853-1858`, `:1888-1890`, `_stress_area` `:1907`) sizes every living internode, branches included, to carry the fresh wood (850 kg/m³) and leaves beyond it at 57/3.5 = 16.3 MPa.
- **Largest limbs at 60:** recomputed the floor's way, leaves and actual lever arms included (`out/bench/p40_default_v2/limb_moment_calc.txt`). The largest limb has 1.51 kg of fresh wood and 1.05 kg of leaves, its load centre 0.56 m out, so M = 14.2 N·m. The uniform-stress radius is (4M/(π·16.3 MPa))^(1/3) = 10.4 mm; its actual base radius is 20.3 mm. The next four limbs need 6.5–8.1 mm.
- **Shortfall:** the tree has 687.7 m of living branch holding 6.8 kg. Repola's 65.0 kg on that length would need a mean radius of 7.53 mm instead of 2.44 mm (`branch_wood_calc.txt`). The longest limbs reach only 1.3–1.8 m sideways.
- **Floor switched off** (`out/bench/p40_nofloor`): branch wood / Repola is 0.12 / 0.16 at 50 / 60 (10.6 kg at 60), and height is 25.0 m at 60. The floor's extra wood is not charged to carbon, so switching it off changes the whole tree's growth path. Why that leaves more branch wood is **not diagnosed**.
- **Sources:**
  - McMahon & Kronauer 1976 (elastic similarity): not opened.
  - Niklas 1992 and 1994 (books): not opened. Niklas 1999 (abstract only): safety factors inside one Robinia crown vary with branch age.
  - Jirasek, Prusinkiewicz & Moulia 2000 (opened): computes deflection only, with diameters from the pipe model. No wood is sized by load.
  - Minamino & Tateno 2014: under self-weight, Japanese beech branches fit uniform stress (index 0.97 ± 0.02); Nikko fir deviates (0.88 ± 0.02).
  - No silver-birch branch constants were found.

**6. White patches at stem bases.**
Not done: the cause lies entirely in mesh and render code, but a fix needs a value or method with no source yet (options in `reports/phase40.md`).
- **Mesh:** the root ridges (`treegen/mesh.py:309`, `:347`) tilt the base upward. On tree_053 of `out/bench/p38_nat_mesh`, stem faces have an area-weighted mean up-component of +0.135 at 0.1–0.2 m (90th percentile +0.37), against 0.00 above 0.3 m (`out/renders/p40/white_patch_check.txt`).
- **Render:** `_shade` (`treegen/preview.py:292-299`) lights every surface with full sky and a sun at 56.5° elevation, with no canopy shadowing. `_colours` (`:312-321`) gives every thick stem the same near-white. A sun-facing face tilted to +0.32 (the ridge-sector mean) renders at 0.804 against 0.620 for a vertical face, 30 % brighter.
- **Normals:** they point outward; checker B measured at least 99.7 % per tree in all 78 trees. Not a growth-model issue.

**7. Notes.**
Answer: notes for phases 34–36 and 39 were written from git history and saved files, and the unsupported claims in the phase 37 & 38 notes were corrected. What could not be reconstructed is marked.

## Campaign M1: foundations, 2026-11-06

The Birch v1 campaign replaces round-by-round briefs; `CAMPAIGN.md` is where to resume, and `reports/milestone_M1.md` is the full report. No model calculation changed.

- **Verdicts come from ensembles on one machine:** 20 trees and 5 plots on the node (`reports/rebaseline_M1.md`). A single seed can move like a new tree on a change of a few parts per million.
- **Alpha 4.8** is a one-point model calibration (commit `c3fd2dc`), not a published value, and its origin doesn't reproduce exactly. Flagged VERIFY.
- **Height band:** T13 = 150/SIS (Elfving 2010 p. 56) replaces a fixed 4 years, with a stand-in for SIS. Plot top height is on a Naslund curve (Elfving p. 58; the curve is the maintainer's choice). At the approved tag the stand tree passes at 40 and 50 by 0.003 m and 0.03 m; at master it fails.
- **Run outputs:** `subcanopy_diffuse_light_pct` per year; manifests fingerprint uncommitted code where git exists.
- **Audit:** `reports/parameter_audit.csv`, 274 values, 71 looked at, 15 not supported by the page. Screen: 77 of 160 values within the noise at 5 seeds (`out/bench/node/screen5/`, `screen20/`).
- **`light.woody_shade` looks like a double count** against `light.extinction_coefficient`: K_PAR comes from measured transmission against leaf-only LAI (`reports/hagemeier2019b_publisher_reading.md`). Not changed. For M2 and M3. **Confirmed 2026-11-09** (Forests 10:925 read at the publisher): section 4.2 says K_PAR takes in "the area of twigs and branches in the radiation beam", so the model's wood shade counts the wood twice. Tested on branch v1-young-light.
- **Open:** the Niemistö file in `birch-data` is the wrong paper; stands in three targets differ from the sources' (QUESTIONS.md Q13, Q15).

## Campaign M1: citations corrected, 2026-11-06

Crossref shows `10.1139/b65-035` is Loman 1965 on basidiomycetes and `10.1139/b66-096` is Edwardson 1966 on plant viruses, so the Clausen & Kozlowski DOIs marked "Yes" above are wrong. Crossref has the Nature paper at `10.1038/2051030a0`, and Kozlowski & Clausen 1966, Can. J. Bot., at `10.1139/b66-097`; one search found no 1965 Can. J. Bot. paper by them. Anfodillo 2006 is New Phytol. 169:279, not Tree Physiol. 26:1415.

## Campaign M2: found, 2026-11-06

- **Fresh laterals' leaves aren't charged.** `_leaf_costs` waives next spring's clusters on fresh side buds (`treegen/growth.py:1325`), saying they were built with the shoot, but `_growth_factor` charges only one late leaf per node and the tip's cluster (`:1606-1608`). **Superseded (2026-11-09):** `growth.py:1325` and `:1606-1608` now point at other code (`_pay_roots` and `_leaf_path_length`). The waiver is at `growth.py:1452-1455` and the charges at `:1782-1783`, at 8fd4fdb. `resource.leaf_costs.charge_fresh_laterals` charges them; it's off by default. Q23.
- **`0386ce7` is output-only with wood shade on, not off.** Every golden run is identical. Two wood-off ensembles at `f45928e` and `3f3d687`, same seeds, differ on all 20 seeds from about year 6-7; `0386ce7` lengthens the grid when wood is off, and it's the likely cause (inference). `out/bench/ensemble/m2_linked.txt`.
- **The model's k with no wood sits below its input.** Implied k is about 0.345 at 50-60 from an input of 0.37, on trees and plots; with wood on, 0.39-0.40. Neither is the paper's 0.37. The offset is about the 2 points in the phase 17-20 table above. Q21.
- **Plots barely thin.** About 1,480-1,660 stems/ha at 60 at alpha 4.8, and basal area over bark 62-67 m2/ha, against Repola Table 1's top of 32.3. M4. `out/bench/ensemble/m2_validation.txt`. **Superseded (2026-11-09):** v1 plots have 520 (470-570) stems/ha and 25.7 m²/ha at 60 (`node_v1_plots`); see Birch v1 below.
- **`tools/plots_identical.py` walks the first folder's plots:** give a partial control first, or it reports the others missing.
- **Plots' thickest trees run taller than a stand tree at the same alpha.** At 60, the thickest 100 per hectare are 2.0-6.8 m over; the average plot tree is +0.95, -2.15, -4.54 m at alpha 3.0, 3.5, 4.8. So trees and plots want different alphas (row 76). Why isn't established: it may be selection, or crowding. M4.
- **`base_trees` is a low draw for LAI:** 3.09, 3.27 at 50, 60, against 3.36, 3.46 on seeds 21-40. Its verdicts stand, but every row paired with it inherits that (row 77).
- **The Baltic LAI band's papers print no LAI** (Q26).
- **`tools/m3_wood.py` and `tools/m2_validation.py` used wood-only diameters against over-bark sources until `tools/bark.py` went in** (row 80).

## Birch v1 (reset), 2026-11-09

The reset's one full check (PROTOCOL section 10). The full report is `reports/birch_v1_final.md` on `reset-integration`. The three reviews are on master: `reports/reviews/2026-11-08_final_check_a_sources.md`, `2026-11-09_final_check_b_numbers.md` and `2026-11-09_final_check_c_rules.md`. The hand-worked figures (young crown ratio, "46 of 55", k, the paired ±) are recomputed in `reports/birch_v1_workings.txt` in Cambium-int.

### What v1 is

- **Defaults switch, d5f0ea3.** The 52 settings of `cases/crown2_with_roots_speed.txt` and the two forest changes became the species defaults: 48 values changed, 4 were already set. The golden runs before (8c2c496, settings by hand) and after (d5f0ea3, defaults) are identical: 225 files, 0 differ (`Cambium-int/out/bench/golden/node_gold_v1pre`, `node_gold_v1post`).
- **On by default since then:**

| Part | Setting | What it does |
|---|---|---|
| Crown frame, earned | `crown_frame.enabled`, `crown_frame.earned` | Limbs earn their reach and place by their leaf area against the limbs around them (`growth.py` `_frame_earned`). Reach is capped at Hemery's crown (`growth.py:2196-2205`) |
| Height driver | `height_driver.enabled` | The leader grows up to the Eriksson 1997 site-index curve (SI 23). Height is by design |
| Damage | `damage.enabled`, with `old_age`, `wind` and `snow` | Old age (Elfving 2010), wind (Kitenberga 2021), snow |
| Paid roots | `roots.paid.enabled` | The root share's carbon pays for fine roots and root wood (`growth.py` `_pay_roots`) |
| Forest change 1 (359bea4) | `plot.height_follows_dominants` | Plot heights follow the dominants' vigour |
| Forest change 2 (359bea4) | `mortality.vigour.relative_size_slope` 3.263 | Slow-ringed trees above the stand's Dg die less of "suppressed" (Maleki & Kiviste 2016 Table 3, DERIVED; `thinning.py:147-152`) |

- The rest of the 48 values are crown, shedding, stem and speed settings: `git show d5f0ea3`.
- **Forests need more than the defaults.** `mortality.enabled` and `plot.natural_start.enabled` stay false in the species file. `tools/forest.py` sets both (lines 44-46), and turns regeneration on with `--regeneration` or `--spread` (lines 67-68). The forest results depend on all three.

### Open issues

Runs in `Cambium-int/out/bench/ensemble/`: plots `node_v1_plots` (20), young plots `node_v1_young` (20, to 22), stand trees `node_v1_treesR` (20), lone trees `node_v1_openR` (8), old plots `node_v1_200` (3).

| Issue | v1 | Real | Cause, as far as known |
|---|---|---|---|
| Young crown ratio | 0.92 / 0.96 / 0.94 / 0.93 at 11 / 15 / 20 / 22 (young plots) | 0.30-0.45 at 11-22 (Niemistö 1995, unopened; read through targets.yaml) | Tuned after v1, not fixed (crown fix C, DECISIONS 105, 107: chase and limb_shoot_floor_m TUNED against Konopka 2023's young leaf area for height): crown ratio at 15 m 0.58 (20 plots), compared by stand height as the maintainer decided; by age the young plots still read 0.94-0.97 at 11-15, because the site grows slower than the source stands |
| Young crown base | At 13.5 m tall: lowest live branch 0.8 m (0.2-1.8), crown base 1.6 m (0.5-2.9); 0 of 20 in 5-7 m (stand trees) | 5-7 m at 13-15 m tall (Hynynen & Niemistö 2009) | Tuned after v1, not fixed (crown fix C, TUNED, DECISIONS 107; the 5-7 m figure isn't an approved target): lowest live branch on 13-15 m plot trees 5.36 m, 62 % in 5-7 m. **Stand trees still miss it:** the fresh run on the defaults (node_f5_trees, 38ce58e, 20 seeds, reports/birch_fresh_run_2026-11-09.md) reads 0.89 m (0.31-2.26) at 13-15 m tall, age 25, 0 of 20 in 5-7 m. The plot figure is read on stems 13-15 m tall under a taller canopy, not on the dominants the source describes |
| Baltic LAI | 4.54 at 50 (40 % of plots inside), 4.36 at 60 (85 %): FAIL at 50 by 0.04, PASS at 60 (report section 3). Under 2.5 at 6-14, over 4.5 at 18-54, peak 5.63 at 27: outside in 46 of 55 years | 2.5-4.5 at 6-60; its source is in doubt (Q30) | Crown fix C (DECISIONS 107): 4.51 at 50 (0.01 over), 4.29 at 60; young LAI now 5.1-5.3 at 20-22, further over. Source found: Varik, Aosaar & Uri 2009 (Q30) |
| Light near the top of the range | Plots 18.5 at 50, 19.0 at 60; stand trees 16.2, 16.4 | 6.4-19.8 %, median 14.8 % | Tied to LAI through k: light follows LAI at k about 0.37-0.40. Light at the median needs LAI about 5.1, which fails the Baltic band. LAI 4.5 gives light of about 18.7 % at 50 and 18.0 % at 60. The forest changes raised light at 50 by 0.83 ± 0.26 points (paired, 20 seeds). Tuned against |
| Leaf size | Sized by light: 0.0015 m² × 60.8 / LMA, so 10.2-18.1 cm² (`growth.py:1414-1426`); earlier look runs measured means of 17-17.8 cm². The stats' steady 15.0 cm² is an artefact: `growth.py:3117` counts every leaf at 0.0015 m² | 11.9 ± 5.7 cm² (Konôpka & Pajtík 2026, trees aged 4-20) | Leaves come per node. Smaller leaves at the same count gave 7-9 cm thicker stems |
| Leaf density at the top | 0.19 / 0.22 | their fit's 1.97 | Untouched |
| Double tops | 0 of 20 (strict) | 35 % (Zeltins 2018) | Cause unknown. The end-bud rule applies only to axes finer than the stem (`growth.py:995-1001`). Second tops are drawn per tree at Zeltins' 0.349 (`growth.py:2052-2053`) and through reiteration, and don't last |
| Hanging strands, lone trees | Longest 5.2 / 6.1 m; p90 at 60 4.1 m (3.9-4.3) | About 2-4 m in photos, judged by eye | p90 sits at the top of the photo range |
| No early deaths in young plots | None of the trees in a 9,000/ha plot die in their first 5 years | Real young stands lose stems at this stage | Trees on the height curve stay under 1.3 m for the first years. Self-thinning and background death act at any size, but self-thinning can't start until stems past 1.3 m make the stand dense (`thinning.py:105`), "suppressed" needs a stem diameter (`thinning.py:144`), and the carbon rule kills none |
| Young roots | A 6-year tree has one root axis, 10 cm long. Collar roots at 14 sum to 0.69, under Kalliokoski's lowest stand (0.86) | Laitakari 1934 p. 182: small trees (DBH under 5 cm) "may have only 2-3" main roots | Fixed after v1 (DECISIONS 106): 2 collar roots on small stumps, collar sum passes |
| Small trees' uprooting by rounding | Root strength is saved at 0.01 kNm steps (`roots.py:855-857`); by the report, damage reads those, so an 8-year tree's uproot chance comes out 1.0 or 0.0006 | | Fixed on master after v1: damage reads unrounded moments (DECISIONS 99) |
| Old trees' carbon death | After 120 years, first-generation trees die of carbon shortfall, losing their crowns from below. 30-90 per ha still stand at 200 (3 plots, indicative) | No source gives a rate. Stands persist to 121-150; typical maximum age about 100, sometimes 150 (abstracts) | Per-internode upkeep is untested at those ages |
| Foliage strands in stands | Single strands | Clumped sprays in photos | Option J (two end buds, d278fd4) gave sprays and was dropped on light and young LAI. The choice is closer than first said (Q37) |

### Corrections to earlier reports (PROTOCOL 5)

| Wrong claim | Where | What's right |
|---|---|---|
| Lone trees' crown width agreeing with Hemery was a check | Master log 19:51 (8.55 / 9.32 m against 8.70 / 9.52), and to the maintainer | It holds by design: crown_frame caps a limb's reach at Hemery's crown (`growth.py:2196-2205`). It's INFO, not a test (checker (a) finding 7). Height under the curve is by design too |
| A 5.2 m crown base (lowest live branch) at about 14 m tall, 13 of 20 inside 5-7 m | `reports/tree_handover.md:79` | That was the Tree agent's older crown. v1 has 0.8 m (0.2-1.8), 0 of 20 inside. The line is marked superseded there (c811354) |
| "29 % of leaf area in the outer 75-100 % of radius against 44 % of plan area", and the axis-order figures (1,173 twig axes, 28 m of limb, 2.3 short shoots per m on limbs) | Master log 19:21; the first was passed to the maintainer as a fact | Withdrawn at 19:40. The radius was against the whole tree's one radius, so a tapering crown reads thin far out at the top anyway. The order figures were wrong on trees that lost a leader. At 20:02, "curtains inside the crown" was withdrawn for the stand |
| Elfving's old-age logistic read as a yearly rate: 0.34 % at 100 and 1.92 % at 140 | Said at 03:30 on 2026-11-08, as the master log's correction names it; the 03:30 entry itself doesn't hold the numbers | It's the share dead by an age. The yearly hazard is 0.012 % at 100 and 0.066 % at 140 (correction in the master log). `thinning.py`'s old age made the same misreading, about 25-29 times the source's hazard (checker (a) finding 1). It ran only with damage's old age off, which the final runs don't use. It now uses `damage.old_age_hazard` (`thinning.py:122-128`, merged at a0f4880) |
| "The new line brings light inside the limit" (19.7 %) on the older crown | An earlier reading, named in the master log at 16:00 on 2026-11-08; told to the maintainer | Partly weather. Weather shared a random stream with the trees' draws, so a seed's storms differed by run, and runs weren't paired. Weather has its own stream since ae1a2e1 |
| The model's young LAI is "near the band anyway" | QUESTIONS.md Q30's recommendation | Outside the Baltic band in 46 of its 55 years: under it at 6-14, over it at 18-54. Corrected in Q30 on master |
| `birch-data/01_shoot_dynamics/Ryynanen_Vihera-Aarnio_1995_Crown_structure_birch.pdf` is Ryynänen & Viherä-Aarnio 1995 | The file's name, and birch-data's `catalogue.csv`, which still lists it so | It's Hytönen 1995, on Salix (master log 07:31). No line in this repository cites it |
| `birch-data/02_branch_architecture/Niemisto_1995_Crown_branch_properties_silver_birch.pdf` is Niemistö 1995 | The file's name; known since M1 (Q15, the M1 notes above) | It's Tuomela & Kanninen 1995, on Eucalyptus microtheca in Kenya (Silva Fennica 29(3):217-224; checker (a) finding 3). Niemistö 1995 itself has been read only to its abstract (master log 07:31), so the phase 33 table's "Yes" for it can't rest on this file |

Stale lines above, marked superseded and kept: M2's "1,480-1,660 stems/ha at 60", and M2's `growth.py:1325`.
