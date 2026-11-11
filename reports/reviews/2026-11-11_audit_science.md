Model: Fable 5.2 (claude-fable-5-2)

# Science audit: the parts the design tracks don't cover, 2026-11-11

Read-only review at master `b84ab90`. Area: roots, water, mechanics, damage, mortality, regeneration, seasons and the look, the site.

How it was done:
- I read the code, the species file and the site file myself. No growth, tests or renders were run.
- Saved runs read: `node_v1_200` (3 plots to 200 years) and `node_v1_treesR` (20 stand trees), both birch v1, in the integration checkout's `out/bench/ensemble/`. The fresh run's files (`node_f5_*`) aren't on this PC, so my water and carbon figures are v1's, before crown fix C and the young-root fix.
- The weather stream is plain seeded random numbers (`damage.py:59-70`, `483-488`). I re-drew it for seeds 1-200. It matches the storm years logged in the three saved plots exactly.
- CONFIRMED = checked in code or saved data. SUSPECTED = not checked. Outside claims I couldn't open are marked UNVERIFIED. Sources opened today are at the end.

## Verdict in plain words

1. The code here is coherent, the units are right where I checked them, and the labels are honest. That part is professional.
2. **Pendulous is built in.** One number set by eye (12 mm) switches off stiffness, straightening and turning for nearly every twig. Nothing measured stands behind it.
3. **Old forests aren't ready to show.** A cap drops about half the storm damage due on old trees; the three saved plots drew half the storms they were due; big old trees are immune to three death rules; the young layer's density is a memory setting.
4. **At 50 and 60 water does nothing** (stomata 98 % open), and no value in my area has been screened on today's model. The saved screen is older than v1.
5. Damage and mortality are the best-sourced blocks. Roots, water and mechanics are mostly unchecked.

**Score: 5 / 10.** Sound mechanisms and honest labels, against one confirmed fault in the storm rule, an old-forest result that rests on three lucky seeds, and too many values nobody has tested.

## Read from saved runs

Stand trees, v1, 20 seeds, mean (`node_v1_treesR`):

| Measure | Age 30 | Age 50 | Age 60 |
|---|---|---|---|
| Stomatal opening (1 = fully open) | 0.994 | 0.988 | 0.983 |
| Water potential of the top leaves, MPa | -1.70 | -1.48 | -1.44 |
| Share of fixed carbon sent to the roots | 0.269 | 0.254 | 0.256 |
| Wood upkeep as a share of fixed carbon | 0.214 | 0.227 | 0.226 |
| Living internodes | 29,400 | 57,800 | 55,600 |

Old plots, v1, 3 plots of 1,000 m², seeds 1-3 (`node_v1_200`). The last two columns are my sums from the species values and the saved tree lists:

| Age | First generation alive per ha | Its death rate since the row above, % a year | Old-age chance that year, % | Share of due storm hits the patch rule delivers |
|---|---|---|---|---|
| 50 | 770-790 | – | 0.0014 | 100 % (no tree list; from plot means) |
| 60 | 520-550 | 3.7 | 0.0021 | 100 % |
| 100 | 230-280 | 1.8 | 0.012 | 81-85 % |
| 150 | 90-140 | 1.5 | 0.10 | 46-59 % |
| 200 | 30-90 | 1.3 | 0.74 | 42-70 % |

- First-generation deaths after year 60, all three plots (142): suppressed 47, self-thinned 46, wind 25, carbon shortfall 13, old age 6, background 5.
- Storm years in 200 years: 4, 2 and 8 for seeds 1, 2, 3. The setting gives 10 on average (seeds 1-200: mean 10.0, range 2-18).

## Findings, most serious first

### H1. The hanging look is set by one number chosen by eye. High. CONFIRMED in code; size of the effect SUSPECTED. Effort M
- **Where:** `species/betula_pendula.yaml:597-607`, `1838-1842`; `treegen/mechanics.py:40-43`, `103-110`, `149`; `treegen/growth.py:966-980`, `2688-2703`.
- **What:** `pendulous_radius` 0.012 m is TUNED "against the look". Below it a side axis loses five things at once: wood stiffness (down to a quarter), straightening by reaction wood, its pull up against gravity, its turn to the light, and its share by direction. The factor is 0.06 at 6 mm radius and 0.5 at 12 mm. Only limbs on the stem are exempt (2.5 mm, "by eye only"). So side wood up to about 2.4 cm thick is treated as partly or fully soft. Twigs also only lengthen from one end bud (`twig_end_buds: 1`), which gives single strands.
- **Why it matters:** this is the owner's first complaint. KNOWN_ISSUES already has lone trees' strands at 4.1 m (p90) and 5.2-6.1 m (longest) against "about 2-4 m in photos, judged by eye". DECISIONS 92 parks the owner's less pendulous until photos decide. No measurement backs any of these numbers. Thin shoots are already flexible through r⁴; the extra softening is a choice.
- **Fix:** measure first. Use the TreeQSM scans already in use (Van Den Berge et al. 2021): share of wood below the horizontal by diameter class, 1-3 cm. Measure hanging runs on scaled photos with the model's own definition (`growth.py:3035-3037`). Then split the five roles: stiffness by the wood's age, the reaction-wood limit as it stands, turning by shoot vigour. Server arms at 0.012, 0.006 and 0.003, paired seeds.

### H2. Storm damage is cut off for old trees. High. CONFIRMED in code; sizes are my sums. Effort S
- **Where:** `treegen/damage.py:157-162`, `552-574`.
- **What:** a storm puts 90 % of its damage in patches on 15 % of the ground, so a tree in a patch gets about 6 times its chance. The chance is then capped at 1. Once a tree's 5-year chance passes about 4 %, the rest is simply lost. The comment says "the stand's expected damage is unchanged". That holds at 50 and 60 and fails after about 100 (table above).
- **Why it matters:** wind is the main thing that should take old birches. The cap removes about half of it at 150.
- **Fix:** when the cap binds, widen the patch or add patches until the due damage is delivered. Add a test that summed chances equal the uncapped sum.

### H3. The 200-year result rests on three storm-poor seeds. High. CONFIRMED. Effort M (server)
- **Where:** `reports/birch_v1_final.md:81-94`; `node_v1_200`.
- **What:** seeds 1-3 drew 14 storm years where 30 were due. Seed 2's two storm years equal the fewest among seeds 1-200.
- **Why it matters:** "first-generation trees survive to 200" is partly luck, on top of H2 and H4.
- **Fix:** fix H2, then run at least 10 seeds, and report storm years beside survival.

### H4. Big old trees are immune to three death rules. High. CONFIRMED. Effort M
- **Where:** `treegen/thinning.py:86-92`, `94-100`, `138-152`; `species/betula_pendula.yaml:1247-1249`.
- **What:**
  - The size weight falls from 0.33 at 5 cm to 0.04 at 30 cm and is run on as a straight line beyond the table. A 45 cm tree gets about 0.01.
  - "Not suppressed if bigger than the stand's mean" uses the mean of every stem past 1.3 m. With a young layer the mean is 10-18 cm and veterans are 44-51 cm, so their hazard is multiplied by about 0.0015 or less. It is the same fault as the spacing rule: seedlings counted in a stand mean.
  - Vigour is ring width in mm. A big tree with thin rings adds as much wood as a small tree with wide ones. Before the fix old trees died as "suppressed"; after it they can't, once a young layer pulls the mean down.
- **Why it matters:** after 60 the first generation's death rate falls with age (1.8, 1.5, 1.3 % a year). EUFORGEN gives silver birch as "capable of living up to 150 years". No rule makes old stems weaker: the stem's breaking strength doesn't change with age.
- **Fix:** judge vigour by basal-area growth; take the mean over canopy trees only; replace the straight-line run-on with a sourced large-tree term, or label it a guess.

### H5. Inside a stand, the young layer's density is a memory setting. High. CONFIRMED on saved plots. Effort M
- **Where:** `treegen/regeneration.py:336-340`; `species/betula_pendula.yaml:1193-1196`.
- **What:** seed rain is 13,000-25,000 per m² a year. Where the canopy rule lets seedlings in, 63-108 are due per m² a year. One recruit per 2 m cell is allowed, and none in a cell that holds a tree. So recruits (about 9 a year per plot at 100-150) are just the cells that came free: recruits alone fill 168-236 of the 250 cells at 150.
- **Why it matters:** the 11 sourced seed, spread and seedbed values don't matter in a stand. Two tuned settings (`establishment_light`, `canopy_lai_max`: three numbers) and the cell size decide everything. The file says the cell is "memory, not biology".
- **Fix:** let many seedlings start and die by a published early-survival rate. This is the same gap as "no early deaths" in KNOWN_ISSUES.

### M1. The only sensitivity screen is older than the model. Medium. CONFIRMED. Effort M (server)
- **Where:** `out/bench/node/screen5/ranking.csv`, `screen20/ranking.csv` (2026-11-06); `tools/sensitivity_screen.py:41-45`.
- **What:** it ran before v1 switched on the height curve, crown frame, damage and paid roots. It has no `damage.` or `mortality.` row, skips plots, was saved at × 1.25 only, and ranks partly by height, which is now by design. It put four water values in the top 11. Today stomata are 98 % open.
- **Fix:** run it again on today's defaults, stand trees and plots, × 0.8 and × 1.25, 20 seeds. Rank on DBH, basal area, stems, LAI, light and crown ratio at 30, 50 and 60.

### M2. Water does nothing at 50 and 60, and there is no weather. Medium. CONFIRMED. Effort S to say so, L to change
- **Where:** `treegen/growth.py:877-879`, `907`; `environments/sweden_open_field.yaml:72-73`; `species/betula_pendula.yaml:1340-1391`, `1907-1908`.
- **What:** soil water is one constant (-0.05 MPa) every year; the rain option is off. Stomata stay 98-99 % open, so the root share sits at its minimum. `transpiration_max` 3.0e-5 is twice the 1.6e-5 its own comment cites. The midday balance is applied to the whole year's carbon.
- **Why it matters:** every year is the same year, so rings carry no climate. A user would expect drought to matter. The top leaves sit at -1.4 to -1.7 MPa, inside the closing range, so a modest change could wake this part up.
- **Fix:** say it plainly in the docs. For 1.0, either add year-to-year weather and test it, or call water "off in practice".

### M3. Root carbon isn't a budget. Medium. CONFIRMED in code; size SUSPECTED. Effort S
- **Where:** `treegen/growth.py:942`, `1280`, `1370-1386`.
- **What:** the root share buys root length, then the same carbon pays for fine roots and root wood. What is left is logged as "rest" and dropped. The log isn't saved, so no run reports it. Yet all of it counts as production in carbon use efficiency. My rough sum at 60: a third to a half of the root share is left over.
- **Why it matters:** a quarter of all carbon goes below ground on an unchecked value (`root_share_min` 0.25), and the upkeep rate was tuned to an efficiency that counts the leftover as growth.
- **Fix:** save the rest each year; report it at 50 and 60; leave it out of production.

### M4. Wood upkeep is charged per internode, not per living wood. Medium. CONFIRMED. Effort M
- **Where:** `treegen/growth.py:929-930`; `species/betula_pendula.yaml:197-208`.
- **What:** a 2 mm twig internode and a 30 cm trunk internode cost the same. It is 23 % of fixed carbon at 50 and 60.
- **Why it matters:** it decides which limbs are shed and when old trees die of carbon (13 of 59 first-generation deaths after 100). The branch-wood track's arm A would inherit it.
- **Fix:** charge by sapwood volume or surface, then set the level against efficiency again.

### M5. One wood, three strengths; one bark, three rules. Medium. CONFIRMED. Effort S
- **Where:** `species/betula_pendula.yaml:574`, `733`, `773`, `899`, `979`, `1242`, `2050-2051`; `treegen/appearance.py:55-64`.
- **What:** breaking strength is 44 MPa where storms break stems, 57 for the stress floor and 63 where wind sizes the stem. Fresh wood density is 850, below the 887-1032 its own comment cites. Science sums use the full bark equation; the look uses 0.61 of it. At 25 cm of wood that is 2.4 cm of bark against 1.4 cm: 4 % in over-bark DBH, 7 % in basal area.
- **Fix:** one strength and one bark rule, each with its reason. Check the bark equation against the Finnish table at larger sizes.

### M6. Death causes are stacked, and storms fall just before 50 in half the plots. Medium. CONFIRMED; effect on verdicts SUSPECTED. Effort S
- **Where:** `treegen/thinning.py:21-22` against `153-157`; `treegen/damage.py:59-70`.
- **What:** the module says the background rate is what Heureka uses below the self-thinning line; the code adds it always. That rate is all causes; wind and snow are then added again. At 60, wind is about 0.54 % a year and background 0.15 % (my sums). Separately, 10 of plot seeds 1-20 have a storm in years 45-50, where 5 are due. The storm at 49 in plot 1 took 9 of 92 stems.
- **Why it matters:** LAI at 50 fails by 0.01 and light sits near its top. Both are read just after a storm in half the plots.
- **Fix:** report 50 and 60 by storm history; add seeds 21-40; give weather its own seed.

### M7. The site is a patchwork, and it has no labels. Medium. CONFIRMED. Effort S-M
- **Where:** `environments/sweden_open_field.yaml:5-12`; `species/betula_pendula.yaml:768-769`, `1002-1005`, `1921-1926`, `2045`, `2192`, `2361`.
- **What:** latitude and rain are Uppsala's, the design wind is the west coast's, storm odds are Latvia's, snow is southern Finland's, self-thinning is Estonia's, the leaf calendar is Siljan's. Leaves are out on days 130-273 for growth, 120-290 for the look and 118-286.5 for the game target. Thirteen of the site file's comments say VERIFY, and none of its values is in the labels file or the count of 417.
- **Fix:** one named site, one calendar read by all three, and labels for the site file.

### L1. Small points. Low. CONFIRMED
- `growth.py:371-372` says the bite diameter was measured on B. pendula; the species file says B. pubescens (`:879-883`).
- A "snow bend" changes nothing in the tree (`damage.py:345-346`): 94 % of snow events are a log line.
- Two shortcuts the file admits: a % of volume used per stem (`:1273-1275`), and root conductance counted with its axial path twice (`:1486-1487`).
- Outside my area, seen in passing: reports that may be published print a home-folder path (`reports/birch_fresh_run_2026-11-09.md:27`, `:44`, `:226`; `reports/design/2026-11-11_crown_light.md:14`). Check that the publish step strips it.

## 1. Part by part

Values: sourced / DERIVED / TUNED / VERIFY, my count of `labels.yaml`.

| Part | Logic | Units | Counted twice or forced | Values |
|---|---|---|---|---|
| Roots | Coherent: tips compete for soil water, shares, tropisms, stones | Right; fine-root conductance 1.7e-7 checks | Root sizes follow the stump by published ratios (by design); M3 | 3 / 4 / 4 / 45 |
| Water | Coherent balance; idle at 50 and 60 (M2) | Right | Soil always moist | 1 / 0 / 1 / 8 |
| Mechanics | Coherent: bending by the year's added load, reaction-wood limit | Right | Twig softness forced (H1) | 0 / 0 / 1 / 9 |
| Wind, snow | A measured chance of being hit; physics picks snap or uproot | Right | H2, M6 | damage: 26 / 4 / 17 / 4 |
| Old age | Right: a yearly chance worked from a share dead by an age | Right | No | in damage |
| Browsing | Leader only, 16.8 % a year at 0.3-3 m | – | No | 0 / 0 / 0 / 3 |
| Mortality | Local crowding, shared out by size and vigour | Right | H4, M6 | 9 / 3 / 10 / 1 |
| Regeneration | Seed rain, seedbed, light | Right; kernel means check | Saturated (H5) | 11 / 5 / 5 / 8 |
| Seasons, leaf colour, bark | Look only; growth reads none of it | Colour spaces handled | No | 9 / 15 / 181 (the project's count) |
| Site | Sun and sky from latitude; soil constants; no climate | Right | M7 | none labelled |

## 2. Which unchecked or tuned values matter at 50 and 60

| # | Values | Label | Why |
|---|---|---|---|
| 1 | `mortality.sdi_max`, `rate_at_max`, `shape`, the four `vigour` values | TUNED | Set stems/ha, so LAI, light and basal area. Never screened |
| 2 | `damage.wind.population_offset`, `storm_return_years`, `gap_*` | TUNED | One storm near 50 takes about a tenth of the stems |
| 3 | `pipe_model.stem_theory.wind_speed_m_s` 8, `wind_load.safety_factor`, strength 63 | TUNED, VERIFY | Size the stem's ring; ranks 13-14 in the old screen |
| 4 | `resource.root_share_min` 0.25 | VERIFY | A quarter of all carbon; the share sits on it at every age |
| 5 | `resource.maintenance_per_internode` 0.5 | TUNED | 23 % of fixed carbon |
| 6 | `hydraulics.transpiration_max`, `xylem_conductivity`, `conductivity_exponent`, `conductivity_reference_radius`, `psi_stomata_*` | VERIFY | Idle now but close to waking (M2); ranks 2-11 in the old screen |
| 7 | Site: `water_potential_mpa`, `diffuse_fraction`, `season` | VERIFY | Feed light and water; unlabelled |
| 8 | `mechanics.pendulous_radius`, `youngs_modulus_shoot` | TUNED, VERIFY | Posture moves leaves: DBH -4.6 % and +9.4 % in the old screen |

Safe to leave for numbers at 50 and 60:
- the look block (growth reads none of it);
- root tropisms, angles and avoidance (within noise in the old screen), and `roots.paid.*` (root size only);
- anchorage and the pit-and-mound values (uproot or snap, both fatal);
- regeneration's seed, spread and seedbed values (saturated; 0-0.1 recruits a year at 40-60);
- old age (0.002 % a year at 60) and snow (it acts on slender stems at 8-15 years);
- moose values (no effect in the old screen) and the three switched-off blocks.

## 3. Look values a published measurement could replace

| Value | Now | What could replace it | Status |
|---|---|---|---|
| `leaves.chlorophyll_ramp` below full green, `yellow_lift` | Linden, wild grape and soybean stand in; lift by eye | Hovi, Raitio & Rautiainen 2017, Silva Fennica 51(4) 7753: silver birch leaf reflectance and transmittance on 7 dates, 16 May to 7 October, open data | Opened |
| `leaves.season` days, `turn_spread_days`, the site's season | By eye | SLU's forest phenology: nine stages weekly since 2006, dormant bud to all leaves shed; silver birch at Asa and Tönnersjöheden (Langvall & Ottosson Löfvenius 2021, Int. J. Biometeorol. 65:381) | Paper opened; autumn dates are in the dataset: UNVERIFIED |
| Bark stage colours and the dark share | By eye | Juola, Hovi & Rautiainen 2022 dataset: 20 silver birch stems, 400-1000 nm, CC BY 4.0 | Dataset page opened; paper not |
| `leaves.inclination_deg` [30, 70] | By eye | The sourced profile already in the file (`game.unreal.leaf.angle_by_height`); use it in both exports | In the repository |
| `leaves.shape.aspect`, `petiole_m` | By eye | Kovacic & Nikolic 2005 Table 1, already used for leaf length | UNVERIFIED that it prints width and stalk |
| `pendulous_radius`, `pendulous_radius_limb`, `hanging_share` | By eye | Branch angle by thickness from the scans in use; photos with a scale for twigs | Not done (H1) |
| `mechanics.wood_density` | 850 | Tomczak et al. 2021 Table 3, as the file's own comment gives it | Not reopened |

No measurement was found for lenticels, peeling, moss, branch scars or when twigs turn white. They change no number. Leave them as art and say so.

## 4. Old forests: is the logic sound?

- **Old age:** the sum is right, and it reads one maximum age (278 years). But it barely acts: half the trees are dead of age at 231 rings. It is a national function for both birches.
- **Gaps:** the idea is sound (storm patches, bared soil, seedlings where light allows). The patch sizes are tuned with no target.
- **The result isn't sound yet:** H2, H3, H4 and H5 each bend it. A birch forest that replaces itself for 200 years with no other species is a what-if, not a forecast.

## 5. What a forest scientist would reject, and accept

Reject on first reading:
1. A pure birch forest renewing itself under its own canopy to 200 years (EUFORGEN: a pioneer of open, sunny sites; shade tolerance UNVERIFIED).
2. A death rate that falls as the trees age, and half the trees dead of age only at 231 rings.
3. No weather: every year alike, water never short, site quality fed in as a height curve.
4. Young-layer density set by a grid cell.
5. Wood upkeep per internode whatever its size.
6. Twig posture from one radius set by eye, and three strengths for one wood.
7. Storm size, timing and patches tuned with no target; a design wind of 8 m/s tuned to give the right stem.
8. A site put together from six regions.

Accept:
1. Self-thinning by local stand density with a birch slope and onset from a Finnish study, shared out among neighbours.
2. Wind hits from a 14,749-tree inventory model, kept inside its data range; snap or uproot by comparing the two moments.
3. The old-age hazard, now worked correctly from a share dead by an age.
4. Snow loads set against the buckling strength of the real stem.
5. Bending by each year's added load with a reaction-wood limit, and the sine law.
6. Water as pipes in series with the roots; fine-root conductance from measured saplings.
7. Root sizes from Finnish root excavations; seed crops, spread and seedbeds from named field studies.
8. Bark thickness, black-bark height, leaf optics and leaf angles from named measurements, each labelled.

## Where I disagree with other work

- **L2 (low, CONFIRMED; cause SUSPECTED). Seedlings don't shrink veterans' crowns in the saved lists.** The earlier review suspected it. Veterans' crown width (median) goes from 6-7 m at 100 to 10-13 m at 150 and 12-14 m at 200, while the spacing cap reads 2.3-2.7 m across at 150. At 200, eight of nine veterans in plot 1 are 16-59 % wider than Hemery's formula at their own stem. So Hemery is not "the ceiling everywhere", as the crown track says. Possible causes: old limbs settling outward (`limb_sag_deg` 45), leaning stems, new tops after breaks. The crown track's P1 is still right; it won't rescue old trees.
- **Branch-wood track, arm A:** it pays limb rings from the limb's carbon after upkeep. That upkeep is M4's flat charge. Fix M4 first, or read A with that in mind.
- **Too-even forest:** part of any spread is removed by who dies. The size weight takes small stems 8 times as often as 30 cm ones. The spread among the dead should be read too.

## What's genuinely good

- Every sum I checked has the right units: water flow, root conductance, bending, wind and snow moments, seed kernels.
- Old age was misread once, found by the project's own checker, and fixed with one maximum age for both paths.
- Weather has its own random stream, so two runs on a seed share storms. That is why I could re-draw it.
- Damage keeps a full log: every year's weather, every event, both moments. Few models can be audited this way.
- The species file admits what it is: "my line through two published averages", "memory, not biology", "by eye only".
- The look block lists a provenance line for every value and keeps growth from reading any of it.
- The public page already says old forests keep trees longer than the sources suggest.

## Sources opened today

Read through a fetch tool that summarises pages, so quotes are as it returned them.
- Hovi, Raitio & Rautiainen 2017, Silva Fennica 51(4) 7753, publisher's page.
- Langvall & Ottosson Löfvenius 2021, Int. J. Biometeorol. 65:381-391, PMC7900341.
- Juola, Hovi & Rautiainen 2022 stem bark dataset, Mendeley Data, 10.17632/pwfxgzz5fj.2 (the authors' deposit).
- EUFORGEN's silver birch page, citing Vakkari 2009 (the guideline's publisher).
- Not opened, so UNVERIFIED: Mõttus, Sulev & Hallik 2014 on birch leaves through a season; Elfving 2010, Kitenberga 2021 and the other sources named in the species file, which I took as the file gives them.
