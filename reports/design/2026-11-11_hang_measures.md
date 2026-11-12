Model: Fable 5.2 (claude-fable-5-2)

# Hang measures: how much a birch hangs, measured the same way on the model and on real photos

2026-11-11, second version, after an independent check failed the first. The instrument for the hang track. Branch `hang-measures`, from master `ce44058`. It measures and recommends; it adopts nothing and changes no growth code.
CONFIRMED = I ran it or read it today. SUSPECTED = inferred, not checked.

- Model runs, on the server at commit `1dc00bc`, today's defaults, seeds 1-10, read at 10, 20, 30, 50 and 60: `node_hang_open3` (open-grown), `node_hang_stand3` (stand-grown).
- Photos: the nine in `reference/`, measured on the owner's PC. Only numbers left it: `reference/betula_pendula/hang_photo_numbers.json`.
- Every model number, seed by seed: `reports/design/2026-11-11_hang_measures_model.json`.

## What the check found, and what changed

| The check found | Status | What was done |
|---|---|---|
| The model was read whole; each photo only inside its boxes, which cut the lower crown | CONFIRMED, and it was the main fault | The model is now read through each photo's own window, on a picture drawn as tall as the photo's tree (section 2). The whole-tree reading is a side column |
| "By 20 the model is 0.22 above the young photo" was an artefact | CONFIRMED. Withdrawn | In that photo's window the model at 20 reads 0.37 (seeds 0.34-0.41) against 0.32: 0.05 over, less than the photos' own spread of 0.09 |
| The gap was overstated by 0.05-0.13 in the open | CONFIRMED: the window lowers the model by 0.10 / 0.09 at 50 / 60 (single trees and photos: 0.05-0.15) | Gaps restated photo by photo (section 5). At 50 / 60 the model is 0.27-0.37 / 0.31-0.41 over each photo, not 0.42 / 0.45 over their mean |
| The settings list left out what steers and bends a twig | CONFIRMED | 14 rows added (section 7). Of the settings named, two are not read with today's defaults and one is not set in the species file; that is shown |
| H5 cannot tell hanging wood from upright wood | CONFIRMED | A scoring rule, in code and tested: H5 is never ranked alone (section 9) |
| The model's reading moves with picture scale | CONFIRMED: 833 px reads 0.04 under 1,200 px; 1,473 px reads 0.02 over | Gone from the comparison: each photo is met at its own scale |
| The camera view was not matched | Was SUSPECTED. Now tested | Drawn from a ground camera, the open-grown model reads 0.00-0.02 higher at 1 tree height away (single trees -0.03 to +0.05), 0.00-0.01 at 2 |
| The photo-like copy used a guessed blur | Was SUSPECTED. Now measured | Each photo's blur is read from its own thick edges. Given it, the open-grown model moves by -0.01 on average (Meilen, the softest: -0.04 at 50); a stand tree by -0.03 at 50 / 60 (Russia: -0.08) |
| Found while fixing: the Oslo tree's base was set at the roof line behind the stem (0.70 of the picture's height). The stem meets the ground at 0.833 | CONFIRMED, my error | Corrected. Oslo's tree is 1,473 px tall, not 1,217. Its direction readings are unchanged; its width, widest point, frame and fringe changed (section 3) |

## Summary

1. **Hanging has numbers.** Seven measures from a tree's geometry (`tools/hang_measure.py`), and one picture instrument that runs unchanged on a leafless photo and on a leafless picture of the model (`tools/hang_photo.py`). 31 tests on made-up trees and drawn lines with known answers pass on the server.
2. **The model's open-grown tree is almost all hanging wood.** At 50 / 60: 88 / 89 % of all branch length hangs, 90 / 92 % of the leaves sit on hanging wood, and 83 / 90 % of wood 10-20 mm thick hangs. Of wood over 20 mm, 26 / 29 % hangs. (Unchanged: geometry, not pictures.)
3. **Against photos, each read over the same part of the tree at the same scale** (share of fine-twig length within 20 degrees of vertical):

| Photo (solitary) | Photo reads | Model at 20 | 50 | 60 |
|---|---|---|---|---|
| Oslo | 0.31 | 0.42 | 0.64 | 0.68 |
| Meilen | 0.23 | 0.43 | 0.60 | 0.64 |
| Hallinden (young) | 0.32 | 0.37 | 0.59 | 0.64 |

   - At 50 / 60 the model is 0.27-0.37 / 0.31-0.41 over each photo. The lowest seed in any window is 0.56 / 0.61; the highest photo is 0.32. Lines pointing every way alike would read 0.22.
   - At 20 it is 0.05-0.20 over. Against the one young photo it is 0.05 over: no difference can be claimed there.
4. **Stand trees:** in the windows of three photos of groups and edges the model reads 0.53-0.56 / 0.52-0.57 at 50 / 60 against 0.26-0.35: 0.18-0.29 / 0.17-0.31 over. This is the weaker comparison, and against one photo (Russia) it nearly closes: 0.10 / 0.09 with that photo's softness, nothing on the strict reading.
5. **The habit sets in at 11-13 years** in the open (9-14 in a stand): from then on over a tenth of the leaves hang. By 20 it is 74 % (open) and 65 % (stand). At 10 the tree is a 3 m pole with 6 % hanging.
6. **The strands are cords.** A twig's own hanging spray has 1.14 / 1.17 ends at 50 / 60, where 1 means it never branches; 88 / 85 % are single strands. The longest is 5.8 / 6.7 m, 0.33 / 0.35 of tree height.
7. **What nine photos can carry:** the direction share for old solitary trees (two photos, one low in detail), one young tree, and outline width for four. They cannot give H1-H4 or H6. Tip direction, traced run length and the fringe read too weakly to score (section 6).
8. **No file under `treegen/` changed**, so growth is unchanged. Tests: section 8.

## 1. The rule, and the seven measures

**Hangs:** an internode hangs when it points more than 30 degrees below level, so it drops by more than half its own length. The stem never counts. In code it is `HANG_DZ = -0.5` in `tools/hang_measure.py`, the engine's own `HANGING_DZ` (`treegen/growth.py:65`); a test holds the two equal. CONFIRMED: over all 100 trees-at-an-age the two rules differ on 0 internodes, and the longest run equals the engine's own.

| # | Measure | How it is read | Real-tree counterpart today |
|---|---|---|---|
| H1 | Share of branch length that hangs: all, and by wood diameter (under 5, 5-10, 10-20, over 20 mm) | every living internode off the stem | none; laser scans could give it for wood of 1 cm and more (not opened by this track) |
| H2 | Share of leaves on hanging internodes | leaves at each node | none |
| H3 | Hanging run over tree height: mean, 90th percentile, longest | unbroken hanging length from where a branch first passes 30 degrees below level to an end beyond which nothing hangs; runs under 0.2 m left out | the picture's traced run (weak); the audit's by-eye 0.07-0.12 typical, 0.20-0.25 longest |
| H4 | Ends per hanging spray | a spray is all the hanging wood below one such start; given for all sprays and for those that start on wood under 5 mm, the twigs' own | none |
| H5 | Share of fine-twig length within 20 degrees of vertical | the picture instrument, through a photo's window; its twin from the nodes says how much of it points down | the same code on photos |
| H6 | First age a tenth of the leaves hang, and first age from which they do every year | H2, every year | young photos: one today |
| H7 | Crown width over height; height of the widest tenth over height | level side view, 2nd to 98th percentile of branch nodes in each tenth | the picture's outline on photos |

## 2. The picture instrument

- **What it reads.** Fine lines: anything up to about 3 pixels across that stands out from what is beside it. It uses a published line test (Steger 1998) at a scale of 1 pixel: strong curvature across the line, its centre within the pixel, brightness turning round across it. Lines are thinned to centre lines, and each centre pixel gives a direction.
- **Not colour, not light.** Brightness only (a JPEG keeps colour at half detail, which tilts directions); dark on light and light on dark alike; every strength is a share of the picture's own contrast. CONFIRMED by test: white twigs on black, a dim flat exposure and a tinted copy read the same within 0.01.
- **The same part of the tree.** Each photo is read inside boxes set by eye, which leave out the ground, buildings and other trees, and so often the lower crown (`reference/betula_pendula/hang_photo_frames.json`). Those boxes are restated in tree heights, sideways from the foot of the stem and upward from it (`window_of`). That window is laid on the model's picture along the model's own stem line, foot to top, on each side of the tree in each of two views: four readings a tree. CONFIRMED by test: one function lays the window on the photo and on the model, and a picture read as a photo and as the model gives the same numbers.
- **The same scale.** Against a photo the model is drawn as many pixels tall as that photo's tree (776-1,571). Wood is as wide as it is; a twig narrower than a pixel darkens it by the share it covers (`tools/hang_render.py`). CONFIRMED by test: a quarter-pixel line takes a quarter of the light.
- **What it gives.** Near-vertical share (H5); near-level share; tip direction where one end of a traced line is free and the other joins other wood; the traced hanging run behind tips that point down; outline width and widest point.
- **What it cannot tell.**
  - Hanging from standing upright: a twig straight up and a twig straight down read alike. The geometry twin tells them apart on the model; nothing does on a photo (section 9, rule 2).
  - Depth: a twig pointing at the camera looks short and steep.
  - Scale: every length is a share of the tree's height in the frame. Three photos have no top in frame and give directions only.
  - Wood under about 0.1 pixel, or hidden behind other wood.
  - Whose twig it is where trees overlap. A far stem is an upright line.
  - The tree's base and top, and what is not birch: set by eye on each photo.
- **Checks.**
  - CONFIRMED: drawn lines at 0, 10, 30, 45 and 90 degrees are read in the right direction at full length; twig ends are told as down, and as up when the picture is turned over.
  - CONFIRMED: on the whole model the picture's reading follows its twin from the nodes (r = 0.95 over 100 trees-at-an-age; it reads 0.07 lower). Inside the windows, at 20 and over: r = 0.84-0.94. At 10 a window holds little but the leader, which is thin enough to read as a fine upright line and which the twin leaves out as stem (r = 0.74 open, 0.11 stand).
  - CONFIRMED: **softness.** How soft a photo is was read from the photo: the distance over which brightness rises across the edges of its thick wood (69-279 edges in each of the six photos with a window). As a blur, the median edge gives 0.40-1.12 pixels, the sharpest quarter 0.29-0.72. The model's picture was given the heavier figure, the photo's grain and its JPEG quality, and read again through the window. It moved by -0.01 on average in the open (single trees -0.06 to +0.04) and by -0.03 at 50 / 60 in a stand (Russia, the softest at its scale: -0.08; at 20 that photo's softness raises the model by 0.12). The copies read 0.44-1.14 pixels by the same function, against the photos' 0.40-1.12. Grain is under one grey level in every photo and mostly does not survive the copy's JPEG (the copies read 0.000-0.008 of contrast, the photos 0.000-0.005); the line test asks for 0.04, so it matters neither way.
  - CONFIRMED: **camera.** Every photo was taken from the ground, looking up; the model is drawn level, from far away. Drawn instead from an eye 1.6 m up, 1 and 2 tree heights from the stem, looking at the middle of the tree, the open-grown model reads 0.00 to +0.02 and 0.00 to +0.01 higher (single trees -0.03 to +0.05). A stand tree reads between 0.01 higher and 0.04 lower from 1 height away (the 0.04 at 60), and within 0.01 from 2. The photos' own distances are not known.
  - SUSPECTED: its accuracy on real twigs. There is no photo with known twig directions to test it on.

## 3. The nine photos

Numbers only. "Strict" asks twice the line strength. "Window" is the part of the tree the photo's boxes cover, in tree heights above the foot of the stem. "Blur" is from the median edge; in brackets, the sharpest quarter.

| Photo | Kind (`reference/CREDITS.md`) | Near vertical | Strict | Near level | Tips told | Down | Up | Width over height | Widest at | Tree (px) | Line found (px) | Window | Blur (px) | JPEG quality |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| oslo_norway | solitary | 0.314 | 0.261 | 0.168 | 105 | 0.41 | 0.24 | 0.50 | 0.45 | 1,473 | 106,742 | all above 0.47; left of the stem from 0.30; a strip at the far left from 0.20 | 0.69 (0.32) | 87 |
| meilen_switzerland_solitary | solitary | 0.233 | 0.236 | 0.199 | 68 | 0.28 | 0.41 | 0.46 | 0.35 | 833 | 9,706 | all above 0.34; all but the right end from 0.27 | 1.12 (0.72) | 99 |
| hallinden_sweden | solitary, young | 0.324 | 0.339 | 0.141 | 132 | 0.36 | 0.39 | 0.55 | 0.65 | 1,386 | 45,851 | above 0.53 (0.56-0.59 on the right); a band on the left from 0.33 to 0.45 | 0.40 (0.29) | 87 |
| tuntorp_sweden | clump by a road | 0.307 | 0.347 | 0.161 | 112 | 0.41 | 0.32 | 0.46 | 0.35 | 1,170 | 67,337 | above 0.35 | 0.72 (0.47) | 87 |
| brastad_sweden_first_snow | stand-grown group | 0.257 | 0.264 | 0.153 | 73 | 0.23 | 0.42 | - | - | 1,571 | 107,703 | above 0.62 | 0.49 (0.31) | 87 |
| russia_birch_forest | stand edge | 0.350 | 0.470 | 0.129 | 57 | 0.32 | 0.49 | - | - | 776 | 16,994 | above 0.30 | 1.05 (0.47) | 90 |
| gullmarsskogen_stand_1 | dense stand, from inside | 0.393 | 0.438 | 0.076 | 172 | 0.33 | 0.47 | - | - | - | 162,089 | none: no base or top in frame | 0.80 (0.38) | 87 |
| gullmarsskogen_stand_5 | dense stand, from inside | 0.407 | 0.469 | 0.064 | 200 | 0.33 | 0.55 | - | - | - | 128,923 | none | 0.60 (0.36) | 87 |
| gullmarsskogen_stand_6 | dense stand, from inside | 0.418 | 0.476 | 0.069 | 169 | 0.37 | 0.46 | - | - | - | 126,661 | none | 0.69 (0.36) | 87 |
| **solitary, 3** | mean (range) | 0.290 (0.233-0.324) | 0.279 (0.236-0.339) | 0.170 (0.141-0.199) | 102 | 0.35 (0.28-0.41) | 0.35 (0.24-0.41) | 0.50 (0.46-0.55) | 0.48 (0.35-0.65) | - | - | - | 0.74 (0.44) | - |
| **group or edge, 3** | mean (range) | 0.305 (0.257-0.350) | 0.360 (0.264-0.470) | 0.148 (0.129-0.161) | 81 | 0.32 (0.23-0.41) | 0.41 (0.32-0.49) | 0.46 (one) | 0.35 (one) | - | - | - | 0.75 (0.42) | - |
| **dense, from inside, 3** | mean (range) | 0.406 (0.393-0.418) | 0.461 (0.438-0.476) | 0.070 (0.064-0.076) | 180 | 0.34 (0.33-0.37) | 0.49 (0.46-0.55) | - | - | - | - | - | 0.70 (0.36) | - |

- Oslo carries catkins. Hallinden is in hoar frost, which thickens its twigs. Meilen is 750 pixels wide and soft: the instrument finds its limbs, not its twigs (9,706 px of line against 45,851-107,703).
- Tuntorp is several stems together. Brastad and Russia hold overlapping trees, so no outline is read. From inside Gullmarsskogen, far stems are thin upright lines, which lifts near-vertical; with no base or top in frame those three have no window, and nothing of the model is matched to them.
- Grain is at most one grey level in every photo with open sky (0.000-0.005 of its contrast), under an eighth of what the line test asks for (0.04). It does not matter here.
- **Oslo, corrected.** With the base where the stem meets the ground, its width over height is 0.50 (was 0.61), its widest point 0.45 (was 0.35), and its boxes end at 0.20-0.47 of tree height (was 0.03-0.36). The first version's "Oslo's fringe reaches down to 0.20" is withdrawn: on all four whole-tree photos the lowest upright twigs read where the boxes end, so the fringe says nothing.

## 4. The model, from its geometry

Means over 10 seeds, (lowest-highest). Heights are by design. "10 mm and up" is the wood a laser scan would show. These are the first version's numbers: the trees were grown again and every value came out the same (section 8).

| Set | Age | Height (m) | H1: branch length that hangs | under 5 mm | 5-10 mm | 10-20 mm | over 20 mm | 10 mm and up | H2: leaves on hanging wood |
|---|---|---|---|---|---|---|---|---|---|
| Open | 10 | 3.0 | 0.09 (0.02-0.16) | 0.09 | 0.00 | - | - | - | 0.06 (0.01-0.11) |
| Open | 20 | 8.5 | 0.81 (0.79-0.84) | 0.87 | 0.62 | 0.31 | 0.08 | 0.28 (0.22-0.32) | 0.74 (0.71-0.76) |
| Open | 30 | 12.7 | 0.88 (0.87-0.89) | 0.94 | 0.84 | 0.63 | 0.14 | 0.49 (0.46-0.52) | 0.86 (0.85-0.87) |
| Open | 50 | 17.6 | 0.88 (0.85-0.89) | 0.91 (0.88-0.93) | 0.94 (0.93-0.95) | 0.83 (0.80-0.85) | 0.26 (0.22-0.29) | 0.68 (0.65-0.72) | 0.90 (0.87-0.91) |
| Open | 60 | 19.2 | 0.89 (0.87-0.91) | 0.92 (0.91-0.93) | 0.94 (0.92-0.95) | 0.90 (0.86-0.92) | 0.29 (0.24-0.36) | 0.78 (0.74-0.81) | 0.92 (0.90-0.93) |
| Stand | 10 | 3.7 | 0.10 (0.01-0.23) | 0.11 | 0.00 | - | - | - | 0.07 (0.01-0.17) |
| Stand | 20 | 10.6 | 0.71 (0.68-0.76) | 0.78 | 0.54 | 0.29 | 0.11 | 0.27 (0.10-0.34) | 0.65 (0.58-0.69) |
| Stand | 30 | 15.8 | 0.77 (0.74-0.80) | 0.86 | 0.65 | 0.28 | 0.00 | 0.20 (0.16-0.25) | 0.75 (0.72-0.77) |
| Stand | 50 | 21.8 | 0.77 (0.69-0.86) | 0.86 (0.78-0.93) | 0.76 (0.71-0.86) | 0.47 (0.39-0.65) | 0.04 (0.02-0.07) | 0.31 (0.23-0.46) | 0.78 (0.73-0.86) |
| Stand | 60 | 23.7 | 0.74 (0.64-0.83) | 0.83 (0.75-0.91) | 0.77 (0.67-0.85) | 0.48 (0.32-0.63) | 0.04 (0.01-0.13) | 0.30 (0.18-0.43) | 0.76 (0.70-0.82) |

| Set | Age | H3: run over height, mean | 90th percentile | Longest | Longest (m) | H4: ends per spray, twigs' own | Single strands, twigs' own | Ends per spray, all | H7: width over height | Widest at |
|---|---|---|---|---|---|---|---|---|---|---|
| Open | 10 | 0.116 | 0.124 | 0.125 | 0.38 | 1.00 | 1.00 | 1.00 | 0.23 | 0.40 |
| Open | 20 | 0.159 | 0.240 | 0.297 | 2.52 | 1.80 | 0.49 | 5.30 | 0.33 | 0.44 |
| Open | 30 | 0.145 | 0.223 | 0.289 | 3.66 | 1.26 | 0.77 | 3.29 | 0.35 | 0.56 |
| Open | 50 | 0.133 (0.119-0.143) | 0.239 (0.218-0.250) | 0.328 (0.282-0.351) | 5.77 (4.96-6.17) | 1.14 (1.08-1.22) | 0.88 (0.81-0.93) | 2.06 | 0.38 (0.36-0.42) | 0.60 (0.45-0.75) |
| Open | 60 | 0.136 (0.113-0.151) | 0.250 (0.213-0.269) | 0.347 (0.303-0.381) | 6.65 (5.87-7.24) | 1.17 (1.12-1.27) | 0.85 (0.78-0.90) | 1.93 | 0.38 (0.35-0.40) | 0.61 (0.45-0.75) |
| Stand | 10 | 0.097 | 0.122 | 0.129 | 0.48 | 1.03 | 0.97 | 1.03 | 0.20 | 0.45 |
| Stand | 20 | 0.122 | 0.186 | 0.232 | 2.46 | 1.39 | 0.71 | 4.32 | 0.18 | 0.44 |
| Stand | 30 | 0.071 | 0.112 | 0.164 | 2.60 | 1.51 | 0.62 | 2.79 | 0.17 | 0.48 |
| Stand | 50 | 0.062 (0.049-0.090) | 0.102 (0.090-0.135) | 0.148 (0.134-0.176) | 3.24 (2.93-3.66) | 1.22 (1.11-1.28) | 0.81 (0.77-0.89) | 2.13 | 0.21 (0.19-0.22) | 0.68 (0.65-0.75) |
| Stand | 60 | 0.056 (0.041-0.073) | 0.099 (0.072-0.121) | 0.143 (0.112-0.187) | 3.39 (2.66-4.31) | 1.19 (1.11-1.30) | 0.83 (0.75-0.89) | 1.88 | 0.21 (0.19-0.22) | 0.73 (0.65-0.85) |

- **H6.** A tenth of the leaves first hang at 8.6 years (6-13) in the open and 9.8 (5-14) in a stand, but a seedling with a dozen leaves can pass the line for one year. They hang every year from 11.9 (11-13) and 11.6 (9-14). Leaves on hanging wood at 10, 12, 15, 20: 0.06, 0.13, 0.39, 0.74 (open); 0.07, 0.13, 0.30, 0.65 (stand).
- **At 20 "ends per spray, all" is high** because whole limbs hang: a hanging limb is one spray with all its twigs. That is why the twigs' own sprays are given apart.
- **Mean run in metres** at 50 / 60: 2.34 / 2.59 (open), 1.35 / 1.33 (stand). The 90th percentile: 4.20 / 4.79 and 2.22 / 2.33. The full audit's unchecked 79 / 77 % of leaves and 1.38 m for stand trees are CONFIRMED close: 78 / 76 % and 1.35 / 1.33 m.
- **Longest strand, open, 5.77 / 6.65 m** is over the v1 record's 5.2 / 6.1 m. SUSPECTED cause: the limb settings changed after v1 (DECISIONS 107). No hanging wood is pressed against the ground at these ages (0 m in every tree).

## 5. Model against photos, photo by photo

Each row is the model read through that photo's window, on a picture drawn as tall as that photo's tree. Means over 10 seeds, (lowest-highest seed); each seed is the mean of four readings. The whole-tree row is not matched to anything: it is what the first version compared.

**Near-vertical share: open-grown model against the three solitary photos**

| Photo | Tree (px) | Photo reads | Model 10 | 20 | 30 | 50 | 60 |
|---|---|---|---|---|---|---|---|
| Oslo | 1,473 | 0.31 | 0.35 (0.29-0.45) | 0.42 (0.38-0.45) | 0.54 (0.53-0.57) | 0.64 (0.59-0.66) | 0.68 (0.65-0.70) |
| Meilen | 833 | 0.23 | 0.39 (0.34-0.46) | 0.43 (0.39-0.45) | 0.52 (0.49-0.55) | 0.60 (0.57-0.62) | 0.64 (0.62-0.67) |
| Hallinden (young) | 1,386 | 0.32 | 0.40 (0.33-0.55) | 0.37 (0.34-0.41) | 0.49 (0.45-0.54) | 0.59 (0.56-0.61) | 0.64 (0.61-0.66) |
| Whole tree, 1,200 px, not matched | 1,200 | - | 0.31 (0.24-0.37) | 0.54 (0.51-0.57) | 0.65 (0.64-0.66) | 0.71 (0.69-0.73) | 0.74 (0.71-0.76) |

**The same, with the gap and the side readings.** "Strict" is the photo's, then the model's. "Soft" is the model's picture given the photo's measured blur and grain. "Ground" is the model drawn from a ground camera. "Twin" is the geometry's own share of the wood inside the window, and how much of it points down.

| Photo | Age | Photo | Model in its window | Gap | Strict | Whole tree, same scale | Whole tree, 1,200 px | Soft, in window | Ground, 1 height away | 2 heights | Twin in window | of which down |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Oslo | 10 | 0.31 | 0.35 | +0.04 | 0.26; 0.35 | 0.29 | 0.31 | 0.36 | 0.36 | 0.35 | 0.21 | 0.07 |
| Oslo | 20 | 0.31 | 0.42 | +0.10 | 0.26; 0.41 | 0.55 | 0.54 | 0.41 | 0.43 | 0.42 | 0.46 | 0.91 |
| Oslo | 30 | 0.31 | 0.54 | +0.22 | 0.26; 0.55 | 0.67 | 0.65 | 0.53 | 0.57 | 0.55 | 0.71 | 0.97 |
| Oslo | 50 | 0.31 | 0.64 | +0.32 | 0.26; 0.66 | 0.73 | 0.71 | 0.64 | 0.65 | 0.64 | 0.79 | 0.98 |
| Oslo | 60 | 0.31 | 0.68 | +0.36 | 0.26; 0.70 | 0.76 | 0.74 | 0.68 | 0.68 | 0.68 | 0.82 | 0.98 |
| Meilen | 10 | 0.23 | 0.39 | +0.16 | 0.24; 0.39 | 0.35 | 0.31 | 0.40 | 0.40 | 0.39 | 0.20 | 0.11 |
| Meilen | 20 | 0.23 | 0.43 | +0.20 | 0.24; 0.43 | 0.52 | 0.54 | 0.42 | 0.44 | 0.43 | 0.52 | 0.94 |
| Meilen | 30 | 0.23 | 0.52 | +0.29 | 0.24; 0.52 | 0.61 | 0.65 | 0.49 | 0.54 | 0.53 | 0.77 | 0.98 |
| Meilen | 50 | 0.23 | 0.60 | +0.37 | 0.24; 0.61 | 0.67 | 0.71 | 0.56 | 0.63 | 0.61 | 0.81 | 0.98 |
| Meilen | 60 | 0.23 | 0.64 | +0.41 | 0.24; 0.66 | 0.70 | 0.74 | 0.61 | 0.66 | 0.65 | 0.84 | 0.99 |
| Hallinden | 10 | 0.32 | 0.40 | +0.08 | 0.34; 0.40 | 0.29 | 0.31 | 0.40 | 0.41 | 0.40 | 0.16 | 0.08 |
| Hallinden | 20 | 0.32 | 0.37 | +0.05 | 0.34; 0.36 | 0.55 | 0.54 | 0.37 | 0.38 | 0.37 | 0.39 | 0.90 |
| Hallinden | 30 | 0.32 | 0.49 | +0.17 | 0.34; 0.50 | 0.67 | 0.65 | 0.49 | 0.51 | 0.50 | 0.65 | 0.96 |
| Hallinden | 50 | 0.32 | 0.59 | +0.27 | 0.34; 0.61 | 0.72 | 0.71 | 0.60 | 0.60 | 0.60 | 0.75 | 0.97 |
| Hallinden | 60 | 0.32 | 0.64 | +0.31 | 0.34; 0.66 | 0.75 | 0.74 | 0.64 | 0.64 | 0.64 | 0.79 | 0.98 |

**Near-vertical share: stand-grown model against the three photos of groups and edges**

| Photo | Tree (px) | Photo reads | Model 10 | 20 | 30 | 50 | 60 |
|---|---|---|---|---|---|---|---|
| Tuntorp | 1,170 | 0.31 | 0.45 (0.35-0.53) | 0.40 (0.39-0.43) | 0.52 (0.50-0.54) | 0.56 (0.51-0.60) | 0.55 (0.47-0.57) |
| Brastad | 1,571 | 0.26 | 0.62 (0.54-0.77) | 0.34 (0.30-0.36) | 0.40 (0.36-0.44) | 0.55 (0.51-0.59) | 0.57 (0.49-0.60) |
| Russia | 776 | 0.35 | 0.49 (0.40-0.56) | 0.44 (0.41-0.48) | 0.51 (0.49-0.53) | 0.53 (0.47-0.57) | 0.52 (0.47-0.53) |
| Whole tree, 1,200 px, not matched | 1,200 | - | 0.39 (0.32-0.45) | 0.53 (0.50-0.58) | 0.54 (0.52-0.56) | 0.56 (0.51-0.60) | 0.55 (0.47-0.58) |

| Photo | Age | Photo | Model in its window | Gap | Strict | Whole tree, same scale | Whole tree, 1,200 px | Soft, in window | Ground, 1 height away | 2 heights | Twin in window | of which down |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Tuntorp | 10 | 0.31 | 0.45 | +0.15 | 0.35; 0.45 | 0.39 | 0.39 | 0.46 | 0.45 | 0.45 | 0.20 | 0.09 |
| Tuntorp | 20 | 0.31 | 0.40 | +0.10 | 0.35; 0.45 | 0.53 | 0.53 | 0.43 | 0.45 | 0.42 | 0.43 | 0.85 |
| Tuntorp | 30 | 0.31 | 0.52 | +0.21 | 0.35; 0.51 | 0.54 | 0.54 | 0.52 | 0.53 | 0.52 | 0.65 | 0.96 |
| Tuntorp | 50 | 0.31 | 0.56 | +0.25 | 0.35; 0.53 | 0.56 | 0.56 | 0.54 | 0.54 | 0.55 | 0.71 | 0.96 |
| Tuntorp | 60 | 0.31 | 0.55 | +0.24 | 0.35; 0.52 | 0.55 | 0.55 | 0.53 | 0.51 | 0.53 | 0.69 | 0.95 |
| Brastad | 10 | 0.26 | 0.62 | +0.37 | 0.26; 0.62 | 0.36 | 0.39 | 0.62 | 0.60 | 0.62 | 0.16 | 0.00 |
| Brastad | 20 | 0.26 | 0.34 | +0.08 | 0.26; 0.36 | 0.54 | 0.53 | 0.34 | 0.31 | 0.33 | 0.19 | 0.47 |
| Brastad | 30 | 0.26 | 0.40 | +0.15 | 0.26; 0.42 | 0.56 | 0.54 | 0.41 | 0.41 | 0.41 | 0.45 | 0.91 |
| Brastad | 50 | 0.26 | 0.55 | +0.29 | 0.26; 0.55 | 0.58 | 0.56 | 0.56 | 0.55 | 0.55 | 0.71 | 0.96 |
| Brastad | 60 | 0.26 | 0.57 | +0.31 | 0.26; 0.57 | 0.57 | 0.55 | 0.57 | 0.54 | 0.56 | 0.69 | 0.95 |
| Russia | 10 | 0.35 | 0.49 | +0.14 | 0.47; 0.50 | 0.45 | 0.39 | 0.51 | 0.49 | 0.49 | 0.19 | 0.11 |
| Russia | 20 | 0.35 | 0.44 | +0.09 | 0.47; 0.51 | 0.52 | 0.53 | 0.56 | 0.47 | 0.45 | 0.48 | 0.88 |
| Russia | 30 | 0.35 | 0.51 | +0.16 | 0.47; 0.50 | 0.52 | 0.54 | 0.51 | 0.52 | 0.52 | 0.66 | 0.95 |
| Russia | 50 | 0.35 | 0.53 | +0.18 | 0.47; 0.49 | 0.53 | 0.56 | 0.45 | 0.51 | 0.52 | 0.67 | 0.94 |
| Russia | 60 | 0.35 | 0.52 | +0.17 | 0.47; 0.47 | 0.52 | 0.55 | 0.44 | 0.47 | 0.50 | 0.66 | 0.93 |

**The other picture measures, in the same windows**

| Photo | Measure | Photo | Model 10 | 20 | 30 | 50 | 60 |
|---|---|---|---|---|---|---|---|
| Oslo | Near level | 0.17 | 0.08 | 0.11 | 0.09 | 0.06 | 0.05 |
| Oslo | Tips pointing down | 0.41 | 0.13 | 0.70 | 0.72 | 0.71 | 0.70 |
| Oslo | Tips pointing up | 0.24 | 0.71 | 0.11 | 0.10 | 0.13 | 0.18 |
| Oslo | Traced run over height, 90th percentile | 0.010 | 0.067 | 0.041 | 0.042 | 0.044 | 0.042 |
| Oslo | Width over height | 0.50 | 0.22 | 0.32 | 0.37 | 0.39 | 0.39 |
| Oslo | Widest at | 0.45 | 0.56 | 0.52 | 0.54 | 0.62 | 0.62 |
| Oslo | Fine line found (px) | 106,742 | 1,912 | 17,074 | 40,623 | 67,740 | 74,241 |
| Meilen | Near level | 0.20 | 0.10 | 0.10 | 0.08 | 0.05 | 0.04 |
| Meilen | Tips pointing down | 0.28 | 0.19 | 0.70 | 0.72 | 0.67 | 0.68 |
| Meilen | Tips pointing up | 0.41 | 0.57 | 0.10 | 0.10 | 0.15 | 0.19 |
| Meilen | Traced run over height, 90th percentile | 0.021 | 0.081 | 0.045 | 0.038 | 0.051 | 0.048 |
| Meilen | Width over height | 0.46 | 0.24 | 0.35 | 0.39 | 0.41 | 0.41 |
| Meilen | Widest at | 0.35 | 0.52 | 0.42 | 0.49 | 0.59 | 0.59 |
| Meilen | Fine line found (px) | 9,706 | 1,360 | 11,453 | 20,044 | 29,441 | 31,844 |
| Hallinden | Near level | 0.14 | 0.09 | 0.12 | 0.10 | 0.07 | 0.05 |
| Hallinden | Tips pointing down | 0.36 | 0.12 | 0.64 | 0.67 | 0.68 | 0.66 |
| Hallinden | Tips pointing up | 0.39 | 0.73 | 0.18 | 0.16 | 0.20 | 0.23 |
| Hallinden | Traced run over height, 90th percentile | 0.015 | 0.056 | 0.039 | 0.038 | 0.036 | 0.037 |
| Hallinden | Width over height | 0.55 | 0.19 | 0.28 | 0.35 | 0.41 | 0.40 |
| Hallinden | Widest at | 0.65 | 0.62 | 0.59 | 0.61 | 0.65 | 0.67 |
| Hallinden | Fine line found (px) | 45,851 | 1,366 | 9,311 | 25,684 | 48,346 | 53,514 |
| Tuntorp | Near level | 0.16 | 0.11 | 0.12 | 0.07 | 0.06 | 0.05 |
| Tuntorp | Tips pointing down | 0.41 | 0.17 | 0.58 | 0.68 | 0.65 | 0.59 |
| Tuntorp | Tips pointing up | 0.32 | 0.55 | 0.17 | 0.13 | 0.16 | 0.21 |
| Tuntorp | Width over height | 0.46 | 0.20 | 0.19 | 0.18 | 0.22 | 0.23 |
| Tuntorp | Fine line found (px) | 67,337 | 1,793 | 8,786 | 16,630 | 16,899 | 14,671 |
| Brastad | Near level | 0.15 | 0.05 | 0.17 | 0.12 | 0.07 | 0.06 |
| Brastad | Tips pointing down | 0.23 | 0.10 | 0.44 | 0.63 | 0.69 | 0.64 |
| Brastad | Tips pointing up | 0.42 | 0.81 | 0.27 | 0.14 | 0.13 | 0.15 |
| Brastad | Fine line found (px) | 107,703 | 1,056 | 2,990 | 9,589 | 24,843 | 24,544 |
| Russia | Near level | 0.13 | 0.11 | 0.11 | 0.06 | 0.04 | 0.04 |
| Russia | Tips pointing down | 0.32 | 0.28 | 0.60 | 0.60 | 0.59 | 0.50 |
| Russia | Tips pointing up | 0.49 | 0.48 | 0.18 | 0.20 | 0.27 | 0.33 |
| Russia | Fine line found (px) | 16,994 | 1,366 | 5,085 | 7,421 | 7,312 | 6,411 |

What the tables say:
- **Open-grown, 50 and 60.** The model reads 0.27-0.37 / 0.31-0.41 over each photo, read over the same part of the tree at the same scale. The photos span 0.09; the seeds span 0.05-0.07 inside a window. The lowest seed in any window (0.56 / 0.61) is 0.23 / 0.29 over the highest photo (0.32). Strict, soft and ground-camera readings agree within 0.04. CONFIRMED as a measurement.
- **What the window did.** It lowers the model by 0.10 / 0.09 at 50 / 60 (single trees and photos: 0.05-0.15) and by 0.14 at 20 (0.08-0.21): the curtains under the window are the model's most upright wood. The first version's gap of 0.42 / 0.45 was that much too large.
- **At 20** the model is 0.10 over Oslo, 0.20 over Meilen and 0.05 over Hallinden, the one young tree (about as tall as the power pole beside it, SUSPECTED 8-10 m; the model is 8.5 m). The first version's "0.22 above the young photo" is withdrawn. 0.05 is inside the photos' spread and inside the seeds' own range (0.34-0.41 against 0.32).
- **At 10** the model reads 0.35-0.40 in the windows, 0.04-0.16 over the photos. That is no likeness and no hang either: it is a 3 m pole whose upright wood is its leader and rising twigs (7-11 % of the twin's upright wood points down, and 9 % of branch length hangs). This is why H5 is never ranked alone (section 9).
- **Is a photo just missing its twigs?** Not Oslo or Hallinden: the instrument finds 106,742 and 45,851 px of fine line in them, against 67,740-74,241 and 48,346-53,514 in the model at 50 / 60 through the same windows at the same scale. Meilen yes: 9,706 against 29,441-31,844. Meilen's reading is of limbs.
- **Tips.** Photos: about as many down as up (0.28-0.41 down, 0.24-0.41 up). Model at 60, same windows: 0.66-0.70 down, 0.18-0.23 up. But the whole model picture made photo-like (the first version's guessed blur) reads 0.56 / 0.35, so about half of that gap is picture quality. Too weak to score.
- **Traced run.** A photo's twig is traced in pieces a dozen pixels long (crossings, buds, haze), so it reads 0.010-0.022 on every photo. Not a length. H3 has no photo counterpart but the audit's by-eye figures (0.07-0.12 typical, 0.20-0.25 longest, about ±30 %): against them the model's open tree at 50 / 60 has a mean of 0.13 / 0.14, a 90th percentile of 0.24 / 0.25 and a longest of 0.33 / 0.35.
- **Outline.** In the same windows the model is narrower: 0.39-0.41 of tree height against 0.46-0.55 (the project's hand reading was 0.53-0.76), and widest higher up than two of the three: 0.59-0.67 against 0.35, 0.45 and 0.65.
- **Stand.** 0.53-0.56 / 0.52-0.57 against 0.26-0.35: 0.18-0.29 / 0.17-0.31 over at 50 / 60. The lowest seed in any window (0.47 / 0.47) is 0.12 over the highest photo (0.35). At 20 the model is 0.08-0.10 over each photo and its lowest seed (0.30) is under the highest photo. At 60 a stand tree's whole crown sits inside all three windows, so the window changes nothing (0.00); at 50 it lowers the model by 0.01 (Brastad's window starts at 0.62: up to 0.07); at 20 by 0.14. This comparison is weaker: one model tree alone against several real trees overlapping. Against Russia it nearly closes: given that photo's softness the model reads 0.45 / 0.44 against 0.35, and on the strict reading 0.49 / 0.47 against 0.47. Russia's frame holds other stems. The three photos from inside a dense stand (0.39-0.42) have no window and are not compared.

## 6. What the photos can and cannot support

- **Nine photos, six places.** Five are from one district by one photographer. No tree's age or height is known. None is a level view from far away: all look up from the ground.
- **Open-grown: three** (Oslo, Meilen, Hallinden). **Young: one** (Hallinden, also one of the three, and in frost). No young stand tree. No stand tree alone.
- **Whole tree, outline readable: four** (the three solitary and the Tuntorp clump). Two more have tops in frame but crowns that overlap. Three have no tops.
- **They can support:** "fine wood in the upper half to two thirds of an old solitary birch has only a mild lean to vertical, 0.23-0.31" (two photos), "the model's reads 0.60-0.68 there at 50 / 60", and "the model's crown is narrower". The gap is 3 to 4.5 times the photos' spread, so it does not turn on which photo is used.
- **They cannot support:** a target to two decimals; anything about the young habit (one tree, and at 20 the model is within 0.05 of it); the lower crown, which every frame cuts; H1-H4 and H6; real hanging lengths; stand trees singly.
- **What was tested and no longer stands between the two:** the part of the tree read, the picture's scale, the photo's softness, the camera's view (section 2).
- **What could still flatter the model's gap.**
  - A photo's twigs are lighter than its darkest wood, so they are fainter there than in the model's black-on-white picture. SUSPECTED small: asking twice the line strength (strict) moves the model by +0.01 to +0.02 and the photos by -0.05 to +0.02.
  - The frames, bases and tops were set by one reader, once. A window 0.05 of tree height lower would read more of the model's curtains.
  - A photo cannot say whether upright wood hangs or stands. In the model 97-99 % of it hangs at 50 / 60.
- **What works the other way:** far stems and overlapping trees raise a photo's reading (Russia, and the dense-stand photos).
- **Needed:** leafless photos of solitary trees of known age and height, 2,000 pixels or more, from a level distance, with the lower crown clear of clutter; several young trees (5-15 years); and H1 on the laser scans.

## 7. The settings that control hanging

All in `species/betula_pendula.yaml`; labels from `reference/betula_pendula/labels.yaml` or, where there is no label row, from the species file's own note. The audit asks for softness radius, hanging share and twig shoot length to be varied together. The last column says what happens to every other setting then: all are held at today's value, and each arm's record should name them.

**Settings that make wood soft, long and unbranched**

| Setting | Line | Now | Label | Read at | What it does | When the three are varied |
|---|---|---|---|---|---|---|
| `mechanics.pendulous_radius` (softness radius) | 603 | 0.012 m | TUNED, "against the look" (labels:108) | `mechanics.py:103`; `growth.py:972-980, 2694` | Wood is half soft at 24 mm across. Scales stiffness, posture control, and a new shoot's pull to its set-point and to light | varied |
| `crown_frame.hanging_share` (hanging share) | 1839 | 0.35 | TUNED, "against the look", "no birch value"; no label row | `growth.py:2546-2549` | A twig heading straight down makes this share of a level twig's shoot | varied |
| `crown_frame.twig_shoot_max_m` (twig shoot length) | 1810 | 0.5 m | TUNED, the look and open leaf area (labels:457) | `growth.py:2322, 2435, 2543` | Longest yearly shoot of anything finer than a limb: 0.5 x 0.35 = 0.175 m a year straight down. Also how far a twig may pass its limb's tip | varied |
| `mechanics.pendulous_sharpness` | 604 | 4.0 | VERIFY (labels:109) | the same as the radius | How sharply wood goes from soft to stiff | held |
| `mechanics.pendulous_radius_limb` | 607 | 0.0025 m | TUNED, "by eye only"; no label row | `mechanics.py:105`; `growth.py:979, 2444-2455, 2699` | Limbs on the stem and named forks are stiff from about 5 mm | held |
| `crown_frame.twig_end_buds` | 1842 | 1 | a test switch (2 is option J); no label row | `growth.py:1014-1020` | With 1, a strand only lengthens | held |
| `resource.gravimorphism` | 151 | 1.0 | VERIFY (labels:22) | `growth.py:968, 1802-1803` | A side bud on a hanging shoot gets 5 % of its share: strands don't branch | held |
| `crown_frame.full_crown_spur_years` | 1856 | 12 | TUNED, the look; no label row | `growth.py:1269` | Short shoots die at this age in a full crown: bare cords | held |
| `crown_frame.limb_sag_deg` | 1850 | 45 | TUNED, the look; no label row | `growth.py:1327-1330` | A limb's posture target sinks as its wood ages | held |
| `crown_frame.open_lai_max`, `crown_lai_max` | 1817, 1815 | 5, 7 | TUNED; no label rows | `growth.py:1960` | How much leaf the frame holds. What can't go up or out goes on hanging twigs | held |
| `crown_frame.earned` | 1837 | true | the switch; no label row | `growth.py:2320-2322, 2553` | Twigs stop a shoot past their limb's tip; no side shoot ends above the leader of three years ago | held |
| `mechanics.youngs_modulus_shoot`, `_wood` | 584, 580 | 2.5, 10 GPa | VERIFY (labels:105, 104) | `mechanics.py:108-109` | Stiffness of soft and of stiff wood | held |
| `mechanics.reaction_wood_coefficient`, `sine_law_saturation_deg` | 587, 596 | 0.012, 10 | VERIFY (labels:106, 107) | `mechanics.py:149, 161` | How fast stiff wood rights itself | held |
| `mechanics.wood_density`, `leaf_mass` | 574, 577 | 850 kg/m3, 0.2 g | VERIFY (labels:102, 103) | `mechanics.py:113-114` | The load that bends a shoot | held |
| `pipe_model.tip_radius`, `spur_radius` | 621, 623 | 1.0, 0.8 mm | VERIFY (labels:113, 114) | the pipe model | How thick a twig is, so how soft | held |
| `shoot.stop_at_ground` | 97 | true | no label row | `growth.py:840, 1233, 2716` | A strand stops at the ground | held |

**Settings that steer a twig or bend it** (added after the check)

| Setting | Line | Now | Label | Read at | What it does | When the three are varied |
|---|---|---|---|---|---|---|
| `tropism.setpoint_angle_deg` | 565 | 0, 43, 45, 65 degrees from vertical for the stem and orders 1, 2, 3 and up | VERIFY; "higher orders VERIFY" (labels:98-101) | `growth.py:2649-2652, 2739` (a new shoot's aim); `1318-1319` (the posture target in the bending) | A twig of order 2 aims 45 degrees from vertical and of order 3 and up 65: both rising. Limbs and forks use their own drawn angle instead | held |
| `tropism.gravitropism_per_m` | 548 | 2.0, 3.5, 2.0, 0.5 per m, the same orders | TUNED for the stem only, against 144 traced stems; orders 1-3 unsourced (labels:94-97) | `growth.py:2648-2651, 2700, 2750` | The pull of a new shoot towards its aim. For every branch it is multiplied by the softness factor (`growth.py:2700`), so a thin twig gets almost none of it | held as a value; its effect on twigs moves with the softness radius |
| `tropism.phototropism_per_m` | 534 | 0.8, 0.8, 1.2, 1.5 per m | VERIFY (labels:90-93) | `growth.py:2647-2650, 2703, 2750` | The pull towards light. With the earned frame, for order 2 and up it is multiplied by the softness factor (`growth.py:2703`) | held as a value; the same |
| `tropism.phototropism_smoothing_m` | not in the species file | none | no label row | `growth.py:2706, 2732-2738` | Would smooth the light's direction along a shoot. Off: the species file does not set it | held (off) |
| `architecture.direction_noise_per_sqrt_m`, `direction_noise_correlation_m` | 521, 526 | 0.126, 0.3 m | VERIFY (labels:88, 89) | `growth.py:2704-2705, 2741-2749` | A shoot's random wander, as smooth arcs. Not scaled by softness: the softest twig still wanders | held |
| `architecture.branch_angle_deg` | 510 | 43, 42, 48 degrees for orders 1, 2, 3 and up | VERIFY; only the first has a source (labels:82-85) | `growth.py:1607-1609` (the direction a side shoot starts in); `2211` (how far a fork spreads) | The angle at which a new side shoot leaves its parent | held |
| `architecture.sympodial_deviation_deg`, `sympodial_bend_length_m` | 514, 518 | 8 degrees, 0.1 m | VERIFY (labels:86, 87) | `growth.py:2707-2712, 2752-2760` | Each year's continuing shoot starts 8 degrees off, bent in over its first 0.1 m | held |
| `architecture.distichous_jitter_deg` | 505 | 25 | VERIFY (labels:81) | `growth.py:1601-1602` | Scatter of side buds around a level twig: which way a side shoot starts | held |
| `mechanics.substeps`, `max_rotation_per_step` | 610, 611 | 4, 0.25 rad | VERIFY, "model guard" (labels:110, 111) | `mechanics.py:115-116, 127-144` | A year's new load is put on in 4 steps, and no internode turns more than 0.25 rad a step: 1 rad (57 degrees) a year at most | held; they cap how fast softer wood can droop |
| `mechanics.sine_law` | 595 | true | no label row (its saturation angle is VERIFY, labels:107) | `mechanics.py:160-163` | Posture correction goes with the sine of the lean, in full from 10 degrees | held |
| `crown_frame.angle_mean_deg`, `angle_sd_deg`, `angle_min_deg`, `angle_max_deg` | 1752-1755 | 43.2, 10.4, 15, 80 | sourced, Zeltins et al. 2018 (labels:444-447); never retuned | `growth.py:2156-2162` (each limb's angle is drawn); `2100-2110` (`_frame_setpoints`); `2668-2669, 1325-1326` | A limb's own aim, for its shoots and for its posture | held |
| `resource.reiteration.setpoint_angle_deg` | 196 | 12 | TUNED, the look (labels:32) | `growth.py:2109, 2674` | The aim of a limb that becomes a second top | held |
| `crown_frame.twig_overshoot` | 1797 | 1.0 | TUNED, the look; no label row | `growth.py:2324` only | How far twigs may pass a limb's reach. NOT READ today: with `earned: true` the line before it is used instead (`growth.py:2320-2322`; the file's own note at 1831) | held; no effect |
| `crown_frame.steep_limit` | 1792 | 0.5 | VERIFY, "a guess" (labels:454) | worked out at `growth.py:2393`, used only at `2401` | Would let a steep limb grow longer to reach as far. NOT READ today: line 2401 is the branch for `earned: false` | held; no effect |

**Tuned together.** CONFIRMED from the git history: the hang values were all set on 2026-11-07, in the Crown 2 round, in one working list (`cases/crown2.txt`), each judged by eye with the others at that hour's values.
- 07:55 (`7ff47af`, the commit that made hanging twigs lengthen slowly): softness radius 0.012, with the limb radius 0.0025 already in the list.
- 08:26 (`77e2bdc`): twig shoot length 0.5.
- 12:20 (`ddccca1`): hanging share 0.35 and `full_crown_spur_years` 12.
- 15:31 (`bfb0737`): `limb_sag_deg` 45 and `open_lai_max` 5, with `crown_lai_max` 7 from 08:39.

So softness radius, hanging share and twig shoot length must be varied together, as the audit asks. Two things follow from the second table:
- A softer or stiffer radius does not only bend wood: it also sets how much of the two pulls (to the aim, to light) a twig keeps. An arm that moves the radius moves three things at once. To tell them apart needs a switch, which is a code change for the hang track, not this one.
- A twig's aim (45 or 65 degrees from vertical) is unsourced. If stiffer twigs come out at an odd angle, that value is the first suspect, not the softness.

## 8. Checks, and what was not done

- **Growth code.** CONFIRMED: `git diff ce44058` touches no file under `treegen/`. The branch adds `tools/hang_measure.py`, `hang_photo.py`, `hang_render.py`, `hang_run.py`, `tests/test_hang_measure.py`, two number files in `reference/betula_pendula/`, and this report with its data file. No golden run was needed.
- **Measuring changes nothing.** CONFIRMED by test: a tree measured every year has the same yearly stats as one left alone.
- **It repeats.** CONFIRMED: the same ten open-grown and ten stand trees have now been grown at three commits (`b3a5072`, `4f0be37`, `1dc00bc`). All 7,690 values of each set that the second and third runs both hold are identical, so the whole-tree and geometry numbers of the first version stand as printed.
- **The photos' numbers.** CONFIRMED: after the instrument changed, every number of the first version came out the same for eight photos, and for Oslo all that do not depend on its base.
- **Tests.** 31 in `tests/test_hang_measure.py`, 8 of them new: the window's arithmetic; that a photo is read through the function that lays its window on the model; that the numbers file holds each photo's window as its frame gives it; that a picture read as a photo and as the model gives the same numbers, and differs from the whole; the ground camera; the softness and grain measure; the H5 rule. Full suite on the server at `1dc00bc`, the commit the runs used: 441 passed, 1 skipped, and the 4 that always fail there (no `.git`, no `.python-version`). The final commit adds this report and its data file; the full suite was run on it again, and that result is in the hand-over.
- **The files moved.** `hang_photo_frames.json` and `hang_photo_numbers.json` are now in `reference/betula_pendula/`, which is copied to the server; `reference/` itself is not. The model cannot be read through a window the server does not have.
- **Not done.** H1 on the laser scans (that folder is closed to this track). No hang arm was run. `tools/tree_table.py`, the scorecard and the targets were not touched, so lean runs still write 0 for hanging there. Photo frames were set by one reader, once; the stem's foot and top were added by the same reader today. The camera's distance in each photo is not known, so two were tried. The three dense-stand photos are not matched to the model.

## 9. Recommendations, for the hang track to decide

1. **Score every hang arm on these, at 10, 20, 30, 50 and 60, open and stand:** H1 by class (above all 10-20 mm, and 10 mm and up), H2, the twigs' own sprays (H4), H6 "from then on", and the picture's near-vertical share in each photo's window. `tools/hang_run.py run ... --set key=value` gives them all, in about 190 seconds a stand tree and 410 an open-grown one; `tools/hang_run.py matched LABEL` prints the model against each photo.
2. **A scoring rule: H5 is never ranked alone.** The picture's near-vertical share cannot tell hanging wood from wood that stands upright. An arm counts as closer to the photos only if all four hold, photo by photo:
   - its near-vertical share in the photo's window is nearer the photos' range (0.23-0.32 open, 0.26-0.35 stand) than the baseline's;
   - H1, the share of branch length that hangs, falls;
   - the upright wood that points down falls (the twin's share in the window times its "of which down");
   - the upright wood that points up does not rise, as a share of the wood seen or in metres.

   It is `closer_on_h5` in `tools/hang_measure.py`, tested, and `tools/hang_run.py closer BASELINE ARM` prints it. A setting that turned hanging twigs upright passes the first three and fails the fourth.
3. **Never compare a whole-tree reading with a photo.** `hang_run.py` keeps it as a side column only.
4. **Use the photos as a reference range, not a target, until the owner approves one,** and only for trees of 30 and over: 0.23-0.32 for open-grown trees and 0.26-0.35 for groups and edges, read through each photo's window. Today's defaults read 0.59-0.64 / 0.64-0.68 and 0.53-0.56 / 0.52-0.57 at 50 / 60. The photos say nothing firm about a tree of 20 or younger.
5. **Leave tip direction, traced run and the fringe out of any score.** Keep them as side readings.
6. **Get more photos first** (section 6), and put H1 on the scans. One question would settle most of it: does real wood 10-20 mm thick hang? The model says 83 / 90 % of it does in the open and 47 / 48 % in a stand, at 50 / 60.
7. **When `tools/tree_table.py` is free again,** have it call `tools/hang_measure.py` and write null, not 0, where a run kept no geometry.
