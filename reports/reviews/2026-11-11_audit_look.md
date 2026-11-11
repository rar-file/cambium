Model: Fable 5.2 (claude-fable-5-2)

# Audit of the look: why the birch reads as too pendulous

2026-11-11. Read only. Nothing was grown, tested or rendered. I viewed the project's own pictures and the reference photos, read the code and the species values, and opened sources at their publishers.
CONFIRMED = I checked it in a file, a picture or an opened source. SUSPECTED = inferred. UNVERIFIED = a source I could not open.

## Verdict

1. **The owner is right.** The open-grown tree reads as a garden weeping birch, or a larch when young, not as a wild silver birch.
2. **The hang is written in, not grown.** Every twig is told to be soft until it is 24 mm thick, to ignore gravity and light, and to make one unbranched strand. The frame stops twigs going up or out, so down is the only free way.
3. **The value that does it was tuned by eye towards more hang.** The file's own note says the older value "hung only at their ends". That is what the sources describe.
4. **Nothing measures it.** The only figure is the longest strand, judged against photos by eye. The owner said less pendulous before, and that was set aside without a number.
5. **Length is the smaller fault.** The longest strands are about 1.5 times too long. What reads as far too pendulous is how much of the crown hangs, how straight it hangs, and that it starts at age 14.
6. **Stand trees at 60 are fine at a distance.** Young bark and leaves are good close up. The engine's bending method is a real published one.

**Score for this area: 4 out of 10.**

## What I looked at

- Public pictures: hero2_a, twigs2, forest2, autumn, bark_06, bark_20, bark_60, root_flare_60. hero2_b is not in the public media folder.
- Plain renders on master: v1_open_30_60, v1_stand_60, look_ages_whole (an older crown, not v1).
- The showcase's open-grown tree at ages 4, 10, 14, 20, 30, 40 and 60, and its winter frame.
- Reference photos: Oslo, Meilen, Hallinden, Tuntorp, Brastad, Russia. Not the three Gullmarsskogen ones (tops out of frame).

## Trait by trait

Photo figures marked "my eye" are shares of tree height read off the picture, about ±30 %.

| Trait | Real birch | Model, open-grown | Model, forest | Wrong at |
|---|---|---|---|---|
| Crown outline | Young: broad, upswept, twiggy (Hallinden). Mature: uneven dome, width 0.53-0.76 of height, widest at 0.44-0.58 (project's own reading, KNOWN_ISSUES.md:1452-1453) | 10: a leafy pole. 14-20: narrow cone, like a larch. 30-40: flat-sided column, about 0.45-0.5 of height. 60: wider, still flat-sided | 60: a mop in the top third, fine at a distance. Young trees in forest2: level whips | 10-40 open; young forest trees |
| Main limbs | 3-7 big forked limbs, rising 30-60° from vertical, some near the stem's thickness; ends arch over | Dozens of thin straight limbs, evenly spaced, 60-90° from vertical low down | Thin straight sticks at about 45°. Biggest limb 0.27-0.29 of the stem against 0.67 in Nordic scans | all ages |
| Where shoots hang | Outer branchlets only. Young trees: twigs point up and out | 14: limb tips hook down. 20: curtains inside. 30: curtains from every limb, to the ground in the plain render. 60: curtains 4-6 m | Single strands under each limb | from 14 |
| Hanging length / tree height | Typical 0.07-0.12, longest 0.20-0.25 (Oslo, Meilen, my eye); under 0.05 in stand photos | 90th percentile 0.22, longest 0.30-0.32 | not recorded | 30-60 |
| Form of the hanging part | Branched, feathery sprays of thin leafy twigs | Unbranched straight cords, vertical, red-brown, about 60 % of their length leafless | The same | all ages |
| Structure showing | White limbs show through a light crown | In leaf, curtains hide the limbs. In winter, a rain of vertical lines | Clear stems, fine | 30-60 open |
| Leaves | 3-7 cm long (JRC atlas); 11.9 ± 5.7 cm² (project record) | 10.2-18.1 cm², mean about 17. Good shape close up (bark_06); flat angular cards in twigs2 | The same | all ages |
| Bark | Brown when young, then white with lenticels, then dark and fissured (JRC atlas) | 6 and 20: good. 60: a grey crumpled sheet, not black rugged plates; a black seam shows above the root flare | The same | 60 |

**The numbers that exist** (lone trees, 8 seeds, v1; KNOWN_ISSUES.md:2181; heights are my arithmetic, curve × 0.8):

| Measure | Age 50 | Age 60 | Photos |
|---|---|---|---|
| Tree height, by design (m) | 17.6 | 19.0 | - |
| Longest hanging strand (m) | 5.2 | 6.1 | about 2-4, by eye (project) |
| Longest, share of height | 0.30 | 0.32 | 0.20-0.25 (my eye) |
| 90th percentile strand (m) | not recorded | 4.1 (3.9-4.3) | - |
| 90th percentile, share of height | not recorded | 0.22 | typical 0.07-0.12 (my eye) |
| Share of leaves on hanging runs | not recorded | not recorded | - |

No hanging figure exists for ages 10-30, for stand trees, or for plots. The fresh-run report has no hanging row at all.

## The cause in the model

All CONFIRMED by reading the code. "yaml" is `species/betula_pendula.yaml`.

1. **Softness by thickness** (yaml:603, `pendulous_radius: 0.012`; `treegen/mechanics.py:40-43`, `103-110`, `148-149`). One factor s(r) scales both a shoot's stiffness and its power to hold its angle. It is TUNED "against the look" (`reference/betula_pendula/labels.yaml:108`). The note at yaml:1717 says the old 0.006 "sprayed outward, and hung only at their ends".

| Wood diameter | Twig axis, 0.012 (now) | Twig axis, 0.006 (before v1) | Limb axis, 0.0025 |
|---|---|---|---|
| 2 mm | 0.005 % | 0.08 % | 2.5 % |
| 6 mm | 0.4 % | 5.9 % | 67 % |
| 10 mm | 2.9 % | 33 % | 94 % |
| 16 mm | 17 % | 76 % | 99 % |
| 24 mm | 50 % | 94 % | 100 % |

   - A twig 10 mm thick has 3 % of its posture control and a stiffness of 2.7 GPa against wood's 10 (yaml:580, 584).
   - Which wood is stiff is set by what the axis is called, not by physics. A side axis on the stem, or a named fork, is stiff from about 5 mm (yaml:607; `treegen/growth.py:2443-2455`). Any other axis stays soft to 24 mm.
2. **Twigs cannot steer** (`growth.py:2693-2703`). A new shoot's pull towards its set-point is multiplied by the same factor, read from the thickness of the twig it grows on. With the frame on, its pull towards light is too. The comment says it: "thin twigs turn neither up nor to the light, so they hang". There is no age or vigour term, so a sapling's twigs are as soft as an old tree's.
3. **Down is the only free direction.** Twigs may not pass their limb's tip by more than one shoot (`growth.py:2301-2327`: "free to grow down, along or inward"). No side shoot may end above where the leader was three years ago (`growth.py:2553-2556`). The crown may still hold 5 to 7 m² of leaf per m² of frame (yaml:1815-1817). That leaf can only go below the limbs.
4. **Strands never stop** (`growth.py:2545-2549`; yaml:1810, 1839). A twig heading straight down still grows 0.5 × 0.35 = 0.175 m a year, for as long as it has light. A 4.1 m strand is about 23 years of that; 6.1 m is about 35 (my arithmetic). `stop_at_ground: true` (yaml:97) is there because strands reach the ground.
5. **Strands never branch** (`growth.py:1013-1020`, `1802-1803`; yaml:151, 1842). Only the end bud of last year's shoot may make a long shoot. On a hanging shoot the side buds' share is cut to 5 %. The comment: "so curtains are single strands, not brooms".
6. **Bare cords** (yaml:1854-1856). Short shoots die at 12 years in a full crown. The file says that leaves about 60 % of an open tree's twig length leafless.
7. **First-year droop is real physics, and fine.** A level 0.5 m shoot, 2 mm thick, at 2.5 GPa with one 0.2 g leaf per 2.5 cm, bends about 64° at its tip; a 0.25 m shoot about 8° (my arithmetic, simple beam formula; the model's sub-steps give less). So long thin shoots should droop. The fault is steps 1 to 5: the wood never recovers, never branches and never stops.
8. **Every input to the bending is unchecked.** Wood density, leaf mass, both stiffness values, the reaction-wood constant, twig and spur radius are all VERIFY (`labels.yaml:102-114`).

## What the literature says

Opened by me:
- **Vakkari 2009**, EUFORGEN technical guidelines for *Betula pendula* (the programme's own PDF): "fairly narrow crown and drooping outer branchlets". Trees rarely pass 30 m.
- **Beck, Caudullo, de Rigo & Tinner 2016**, European Atlas of Forest Tree Species, pp. 70-73 (the EU research centre's own PDF): its branches "characteristically droop", where downy birch's "grow upwards or horizontally". Bark brown when young, then silvery-white with lenticels, then dark and fissured. Leaves 3-7 cm.
- **Lintunen 2013**, Dissertationes Forestales 165 (publisher's PDF), Table 3, 73 silver birches next to birch, ages 4-32: first-order branches 5.2 (0.3) per 10 % of crown, 102.0 (7.0) cm long, 53.0 (5.5) short shoots per branch; this year's long shoots are 0.19 (0.09) of total branch length. Text, p. 26: branch angle "decreased with increasing height within the crown"; at one height a longer branch has a smaller angle; long shoots are more and longer towards the top, longest on the main branches. No angle in degrees is given there.
- **Alméras, Costes & Salles 2004**, Annals of Botany 93:455 (publisher's abstract only; apricot): what separates upright from bent shoots is "the length/diameter and the load/cross-sectional area ratios"; "Wood elasticity does not play an important role".
- **Trozzi 2024**, Plant Physiology 195:1097 (PMC; peach): the weeping habit "results from altered auxin gradients", a fault in the response to gravity.
- **University of Helsinki's release** on Salojärvi et al. 2017: the garden weeping birch 'Youngii' "had a truncated LAZY gene". So the fully weeping birch is a mutant that cannot respond to gravity. Rule 2 above gives every twig that fault.
- **Gailis et al. 2020**, Silva Fennica 54(2):10220: branch angle scored in classes; no means.

UNVERIFIED (not opened; do not cite as checked):
- Salojärvi et al. 2017, Nature Genetics 49:904, the paper itself (cookie wall).
- Zeltins et al. 2018, Forests 9:52, the 43.2° branch angle (refused, 403). The project's label already says the angle is not defined there.
- Mäkinen, Ojansuu & Niemistö 2003, Forest Science 49:301: branch-angle models for planted silver birch.
- Kull, Tulva & Vapaavuori 2003, Annals of Botany 91:559: counts of long and short daughter shoots at four crown positions, 9-year-old trees. Abstract only; the counts would test rule 5.
- The Russian shoot-bending study behind the 2.5 GPa (cookie wall). Maillette 1982 and Atkinson 1992 (not tried; paywalled).
- From what age a birch weeps. Garden floras say young trees are upright; I opened no source that gives an age. The Hallinden photo shows it.

**Gaps.** I found no published length or diameter of pendulous birch shoots, and no birch twig stiffness. Angle by order and age exists only as Lintunen's direction of change, the unopened models, and the project's own scan readings (58 / 48 / 68° and 64 / 63 / 68° low / mid / top, KNOWN_ISSUES.md:1209, 1431).

## How to measure hanginess

Numbers first, then photos. All of these are read from geometry or from a fixed tracing rule, never by taste.

| # | Measure | On the model | On real trees | Exists today |
|---|---|---|---|---|
| H1 | Share of branch length pointing over 30° below level, by thickness (under 5, 5-10, 10-20, over 20 mm) | from the nodes | from the laser-scan branch models the project already used (wood of 1 cm and more) | no |
| H2 | Share of leaves on hanging runs | `tools/tree_table.py:243` | - | computed, never reported |
| H3 | Hanging run over tree height: mean, 90th percentile, longest | `growth.py:3035-3048` | traced on leafless photos, 20 sprays a tree, from where the twig passes 30° below level to its tip | model side only |
| H4 | Tips per hanging run (does a strand branch) | from the nodes | counted on the same traces | no |
| H5 | Share of thin-twig pixels within 20° of vertical, leafless | winter render, same framing | the six leafless photos, same code | no |
| H6 | First age at which H2 passes 10 % | yearly stats | young photos | no |
| H7 | Crown width and widest point over height | stats | KNOWN_ISSUES.md:1452-1453 | yes |

- H1 on scans is the strongest test. It asks directly whether real wood 1-2 cm thick hangs. The model's rule says it does.
- H3 on photos must use the stem-trace method: the model's render is clicked the same way, and click scatter is measured.
- Report every measure at 10, 20, 30, 50 and 60, open-grown and stand.

## Candidate fixes, best grounded first

1. **Measure first** (no model change). H1-H7 on today's defaults and on photos and scans. S.
2. **Softness back to twig scale.** Arms at 0.012 (now), 0.006 (the old value) and 0.003, read on H1-H6. Grounds: "drooping outer branchlets"; the file's own note on 0.006. It stays TUNED, but against a measure. It was last tried under an older frame, so the result is not known. S.
3. **Give twigs back their response to gravity** (`growth.py:2700-2703`): let a new shoot's pull depend on its own vigour, not on its parent's thickness. Grounds: only the mutant cultivar lacks it. M.
4. **One stiffness law.** Stiffness by tissue age only; posture control for all wood, limited by ring growth as the code already has it (Alméras & Fournier's form). Slender slow twigs then hang and vigorous ones hold, with no radius setting. Grounds: Alméras 2004. M.
5. **Twig turnover, and sprays.** Hanging shoots shorten with twig age and old twigs are shed; two end buds (option J, kept at its commit). Check against Lintunen's 0.19 and 53. Grounds: measured, but on trees aged 4-32. M.
6. **Open the fence outward** where there is light. Design logic only; belongs with the crown track. M.
7. **Fewer, thicker, forking limbs**, against the scans. L.

Not recommended: tuning `hanging_share` again. It has no birch value.

Rule to fix now: pick the arm closest on H1-H6, provided light and leaf area at 50 and 60 hold; then photos.

## Findings, most serious first

| id | Severity | Where | What is wrong | Why it matters | Fix | Effort | Status |
|---|---|---|---|---|---|---|---|
| K1 | critical | yaml:603; `mechanics.py:103-110,148-149`; `growth.py:2693-2703`; `labels.yaml:108` | Twigs are soft to 24 mm and cannot respond to gravity or light; the value was tuned by eye towards more hang | It is the direct cause of the owner's complaint, and gives every twig the weeping cultivar's fault | Fixes 2-4 | M | CONFIRMED |
| K2 | high | `growth.py:2301-2327`, `2553-2556`; yaml:1815-1817 | The frame blocks up and out; leaf area can only go down | Curtains are where the crown stores its leaf, so softer settings alone may not cure it | Fix 6, with the crown track | M | CONFIRMED in code; size SUSPECTED |
| K3 | high | `growth.py:2545-2549`, `1013-1020`, `1802-1803`; yaml:1839, 1842 | Strands grow 0.175 m a year for decades and never branch | Cords of 4-6 m, 20-35 years old, where real twigs are short, branched and shed | Fix 5 | M | CONFIRMED |
| K4 | high | KNOWN_ISSUES.md:2181; DECISIONS.md rows 92, 95; `reports/tree_handover.md:153`; `reports/overnight_log.md:310` | No measured target for hanging. One loose figure, "by eye". The hanging crown was kept over the spray crown on light and leaf area, which don't measure habit | "Numbers first" cannot work for this trait; the owner's remark was set aside with no number | Fix 1; add H1-H7 to the report | S | CONFIRMED |
| K5 | high | showcase frames at 10, 14, 20; no age term in `mechanics.py` or `growth.py:2688-2703` | A 10-year open tree is a pole; 14-20 a larch; tips hang from 14 | Young trees are what a player sees most as a forest grows | Crown track (agreed) plus fixes 3-4 | M | CONFIRMED by pictures; cause part SUSPECTED |
| K6 | high | winter frame, v1_stand_60; KNOWN_ISSUES.md:1203-1211; branch-wood design section 3 | Fishbone frame: many thin straight limbs, none near the stem's size | No birch silhouette without big forked limbs | Fix 7 | L | CONFIRMED |
| K7 | medium | yaml:1854-1856; hero2_a, twigs2 | About 60 % of open twig length is leafless: bare red cords | Reads as dead or unfinished close up | Comes with fix 5 | M | CONFIRMED |
| K8 | medium | `labels.yaml:102-114` | Every input to bending is VERIFY | The hang cannot be called physics while its inputs are guesses | Open the stiffness source; measure twig and shoot diameters | M | CONFIRMED |
| K9 | medium | `reference/betula_pendula/labels.yaml` | 13 look settings have no label row: hanging_share, twig_end_buds, limb_sag_deg, fork_leaf_area_m2, full_crown_spur_years, pendulous_radius_limb, open_lai_max, peak_depth, base_share, profile_power, reach_scatter, spacing_overlap, crown_lai_max | The README says every value is labelled | Add the rows | S | CONFIRMED |
| K10 | medium | KNOWN_ISSUES.md:2178; twigs2 | Leaves about 17 cm² against 11.9; angular cards at mid distance | Coarse foliage; known | As planned; check the leaf mesh at that distance | M | CONFIRMED |
| K11 | low | public `docs/media/root_flare_60.webp`, `bark_60.webp` | Old bark is grey and sheet-like; a black seam above the flare | Visible in a showcase picture | Fix the seam; darken and roughen the old base | S | CONFIRMED |
| K12 | low | `reports/renders/look_ages_whole.png` | Shows an older crown (tufts on a pole), not v1 | Misleads a reader of master | Re-render or remove | S | CONFIRMED |
| K13 | low | `reports/design/2026-11-11_crown_light.md:14, 246` | Holds a home-folder path and the owner's first name | It is due to be published | Strip before publishing | S | CONFIRMED |

## On the four tracks under way

- **Crown extent and low branches:** I agree. Its rule 10 (twigs stop 0.5 m past the limb tip) is half of K2. Read H1-H6 in the same arms, since twig habit changes how leaf packs and so light.
- **Branch wood:** I part-disagree with retuning the 0.30 rate down on its own. Total branch wood is over Repola, but the biggest limbs are less than half as thick as scans show. Cutting wood evenly thins them further. Judge any arm on limb size spread too, not the total alone.
- **Earned size differences, and validation targets:** no conflict. Add H1-H7 to the independent targets.

## What is good

- **Honesty.** The long strands, single strands and big leaves are listed as misses, in the repo and on the public page (`docs/site/how-real.md:99, 103`). Each tuned value says "against the look".
- **A measure already exists** in code and is deterministic (`growth.py:3035-3048`, `tools/tree_table.py:234-243`).
- **The bending method is real**: load added on the bent shape each year (Jirasek et al. 2000), posture control limited by ring growth (Alméras & Fournier 2009). The engine can grow a hang; its inputs and switches are the problem.
- **Option J was kept**, so a spray arm is cheap to rerun.
- **Stand trees at 60 read as birch.** Bark at 6 and 20, leaf shape close up and autumn colour are convincing.
- **Reference photos are credited** and used for comparison only.

## Not done

No model numbers were recomputed: the v1 hanging figures are from the project's record. Photo figures are by eye. Seven sources could not be opened and are marked.
