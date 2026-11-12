# Limbs design: the challenge

## In short

1. **The census holds.** I recomputed it from the limb logs with my own code and every main figure matches to the stated rounding: 64.7 / 51.1 / 45.4 living limbs at 30 / 50 / 60; thickest 3.8 / 7.0 / 8.3 cm; branch wood 1.13 / 1.48 / 1.78 of A3 as plain means (the design's 1.12 / 1.47 / 1.76 are log-scale means). Two things it leaves out: **8 to 13 of the "living limbs" carry almost no leaf** (under 0.05 m², all under 1 cm), and **median life is 18.3 years counted as last year minus birth year**, not 19.3.
2. **"The model's stand limbs are too thick" holds** for Heräjärvi 2001, which I read at the publisher: the thickest sound knot in the 12-18 cm stem section averages 41 mm. Two of the other three supports are weaker than stated. Stener's knot sizes pool pruned with unpruned trees. The "base area over the sapwood its leaves ask for" row compares a limb's base with a shoot-tip Huber value. And Heräjärvi's steep "vertical branches" reach 47-70 mm in that same section, so the gap is "too many thick limbs" more than "the thickest is twice too thick".
3. **The scan comparison has a third flaw, beside the one the design found.** The scans count dead branches; the model counts only living ones. At the scans' height (age 35) the model has 30.0 living limbs over 2 cm, plus 16.7 that died in the last 10 years at over 2 cm. That is 46.7 against the scans' 58, before any correction for the software's error. This supports the design's point that the scans can't show the limbs to be thin. **The look audit's "largest limb 0.27-0.29 of the stem" is the thickest limb over the diameter at breast height** (7.0 / 25.5 and 8.3 / 28.6 cm). That is not the scans' measure, which is taken at the joint.
4. **Part R's desk reading is not of the rule as written.** The rule takes q_L as light with 1 = open sky. The desk script used a stand-in: each limb's own carbon per leaf area over the tree's 90th-percentile limb that year, capped at 1. On the tree's own mean bud light, the open-sky scale is about 0.67 / 0.63 of that stand-in at 50 / 60. On that scale, A3 after a run reads about 0.69-0.81 at 50, at or under the band's low edge. So **whether the 0.30 rate can stay depends on a choice the design never made**. With the stand-in, a run would read about 0.93 / 1.09, inside the band.
5. **The forecast can't tell R from a flat rate.** Tests 1 and 2 are passed by the flat 0.15 run (2: 0.80 / 0.79, against a threshold of 0.75). Test 3 is failed at 60 by the flat 0.15 run (limbs over 5 cm 14.1 to 8.1, −43 %), and probably by R too: on both flat arms the desk method leaves about half as many limbs over 5 cm as the runs grew. The "comparison with the flat arms" is won by whichever rate is tuned closest to the band, not by the mechanism.
6. **R doesn't do what the owner asked: fewer, thicker, forking limbs.** Worked by hand through ten years of seed 1's upper crown, it thins every limb whose leaves are not the tree's best lit. The tree's biggest limb loses 29 % of its ten-year wood gain on the stand-in light and 43 % on open-sky light. A declining limb stops thickening. Nothing forks and nothing becomes fewer. The design says this itself. But its line "the thickest are well lit, so they thin least" is wrong for the thickest limb: its leaves read 0.52-0.67 of the best-lit limbs' light from year 48 on.
7. **Verdict: pass for the smallest build only: the logging-only count of open-grown trees, with one log column added (each limb's light as the shedding test reads it).** Part R should not be offered to the owner as "branch wood inside the band at today's rate" until q is defined and the desk reading is redone with that column. The rate question (flat 0.15 / 0.20, already run) is the owner's, as decision 6(b), and needs no new code.

2026-11-12. Challenger: Opus 5.5 (ID `claude-opus-5-5`). Branch `limbs` at `85ae47f`; code read at that commit (identical to `2fd46f0` but for the design file). Read only, except this file. No run, test or render. Data: the fetched `node_t2_kt`, `node_b_r10/15/20` stand trees (20 seeds each, to 60), read with new scripts kept in the session's scratch folder outside the repository; I reused none of the designer's scripts and read one (its desk script) to see how part R was read. CONFIRMED = computed by me from those files, read by me in the code, or read by me in the publisher's text. SUSPECTED = inference, desk arithmetic, or read through the fetch tool's summary. Tables give the mean over 20 seeds and (the SD over seeds).

## 1. The census, recomputed (CONFIRMED)

| Measure | 30 | 35 | 50 | 60 | Design |
|---|---|---|---|---|---|
| Living limbs; per m of crown | 64.7 (3.2); 5.68 | 67.5 (3.5); 5.57 | 51.1 (2.5); 4.50 | 45.4 (3.1); 4.21 | same |
| of which under 0.05 m² of leaf (all under 1 cm) | 13.0 (2.6) | – | 10.1 (1.8) | 8.0 (1.6) | not stated |
| Base, cm: median; 90th; thickest | 1.25; 3.14; 3.78 | 1.68; 3.84; 4.70 | 2.77; 5.68; 6.96 (0.54) | 3.20; 6.41; 8.26 (0.82) | same |
| Limbs over 2; 5; 7.5 cm | 23.1; 0; 0 | 30.0; 0.2; 0 | 29.1; 10.9 (2.8); 0.15 | 27.5; 14.1 (3.2); 1.6 | same |
| Limb over stem at the joint, all: median; 90th; largest | 0.37; 0.52; 0.71 | 0.38; 0.57; 0.74 | 0.49; 0.69; 0.85 | 0.55; 0.76; 0.89 | same |
| The scans' reading (over 2 cm, below 0.8 H): 90th; largest | 0.46; 0.53 | 0.52; 0.63 | 0.59; 0.67 | 0.64; 0.73 | same |
| Own-axis length, m: median; 90th; longest | 1.14; 2.35; 2.98 | 1.34; 2.79; 3.85 | 2.07; 4.03; 5.75 | 2.17; 4.20; 6.32 | same |
| Age, years: median; 90th; oldest | 9.3; 15.4; 18.2 | 11.6; 18.5; 20.9 | 15.5; 25.1; 28.7 | 17.7; 29.9; 34.7 | same |
| Largest limb's share of leaf; limbs holding half | 7 %; 11.3 | 7 %; 11.8 | 9 %; 9.5 | 13 %; 7.4 | same |
| Branch wood, kg; over A3 (plain mean) | 14.1; 1.13 | 28.7; 1.27 | 64.4 (11.9); 1.48 | 88.9 (16.7); 1.78 | 1.12; 1.26; 1.47; 1.76 (log-scale mean) |
| Limbs dead in the 10 years before, last base over 2 cm | 12.0 | 16.7 (2.5) | 17.7 | 10.1 | not counted |

- Lives: 142.7 (3.5) limbs made in 60 years, 97.3 dead by 60. Life (last year alive minus birth year): median 18.3, 10th-90th 14.2-26.9. The design's 19.3 (15-28) counts one year more. Of the deaths with a carbon reading, 99 % had own carbon under upkeep in their last year.
- Limb A of seed 1 is as described: born year 32 at 16.08 m; 8.28 cm on an 11.46 cm stem at 60; 14.7 m² of leaf (18.6 % of the tree's); 14.65 kg; 70.3 % of its year-60 ring carbon replaced sapwood. On the stand-in light it reads 1.0 at ages 2-3, 0.6-0.9 until year 47, then 0.52-0.67. On every year's record its base is 1.3-3.0 times the sapwood its leaf asks for (CONFIRMED). On the stand-in light, A is never one of the best-lit limbs after year 47.
- **The leafless limbs.** These are named buds that never grew a crown: 0.2-0.6 cm, under 0.05 m² of leaf, alive for ten years or more (seed 1 has nine above mid-crown at 50). They make the 10th-percentile base of 0.3 cm. Every count compared with Lintunen's 5.2 per 10 % of crown, or with Heräjärvi's knots a metre, includes them. Counting limbs with leaf only: 51.7 / 41.0 / 37.4.

## 2. The scans, like for like

| Point | The design | What I found |
|---|---|---|
| Thin wood read too thick | +73 % under 2.5 cm, from Demol 2022 | Holds as a diameter bias on two leaf-off ash trees, TreeQSM, cylinders down to 2.5 mm (fetch tool's summary of the publisher's page, SUSPECTED). Carrying it to other scans, another scanner and other settings is a reading, as the design says |
| Dead branches | not addressed | The scans include them (`KNOWN_ISSUES.md`: the lowest branch over 2 cm at a median 0.04 of height, where no stand birch has a living one). The model's comparisons count only living limbs. With limbs dead in the last 10 years added (SUSPECTED window: Mäkinen 2002's abstract puts overgrowth 7-10 years after death), over 2 cm at 35 is 46.7 against 58. Branch length at 1 cm and over would rise too |
| Height the ratio is read at | the same rule: over 2 cm, below 0.8 H, at the joint | Holds. The model's trees at 35 (17.8 m; 18.0 cm wood at 1.3 m, about 19.7 over bark) are a little stouter than the scans' (17.7 cm, presumably over bark) |
| The audit's K6 figure | "largest 0.27-0.29 of the stem against 0.67" | 0.27 / 0.29 is the thickest limb over the stem at 1.3 m (7.0 / 25.5 and 8.3 / 28.6). Over the stem at its own joint the same limb reads 0.72. K6's look ("none near the stem's size") is about limbs against the lower stem. That is what real forks and second tops give, not a limb's ring |

So the scans can't carry "too few, too thin". Nor can they show the opposite. **Required:** the scan row and the K6 figure should be restated with dead branches and the measure's definition. The design's step 2 SUSPECTED reading ("about 40 limbs against 58") should add the dead ones.

## 3. The diagnosis in the code (CONFIRMED at `85ae47f`)

- Every line the design cites says what it says. I checked limb births (`growth.py:2198-2234`: a gap of max(0.73 × crown / 52, 0.15 m) ± 30 %), the envelope (`_frame_goal`, 2341-2358), the sapwood turnover (`_sapwood_loss`, 2516-2528, with branch × min(0.02 / r, 1)) and its two callers (1802 and 2930). I also checked the ring (`ring = max(hv × la_tot − keep, 0)`, 1910), the compiled copy taking `keep` as an input (`fast.py:181, 221`), the light test (842-844: leaf-weighted light at the limb's first node, only for limbs past `min_branch_age`) and the carbon test (1128-1149).
- **The ring is one cause of thickness among several,** as the design says ("births by stem length, the paid-first shoot, the shared envelope and the age clock"). Two it doesn't weigh:
  - the shedding test's upkeep counts internodes, not wood (`upkeep = mu × count of living internodes beyond + leaf cost`, `growth.py:1126` and `1141`). A thinner limb costs its owner nothing less, so a ring rule can't change a limb's life through upkeep. That fits the flat arms' unchanged life (19.3-19.4 years);
  - `crown_frame.sapwood_kept` 0.3 (`growth.py:1792-1796`) keeps asking for 30 % of the sapwood of last year's lost leaf. That adds ring to declining limbs, and it is labelled TUNED against stem size.
- The "base area 2.6-4.8 times the sapwood its leaf asks for" uses the current-year-shoot Huber value (1.24e-4) at a limb's base. Sellin & Kupper 2006 (abstract, quoted in the species file) say the Huber value rises towards the base within a birch crown. **So that row is not evidence of "too thick"** until the base's own value is known. The comparison with "branches are mostly all sapwood" mixes two things: wood that conducts, and wood the model's shoot-tip ratio asks for.

## 4. Sources reopened

| Source | The design took | What I found | Read how |
|---|---|---|---|
| Heräjärvi 2001, Silva Fennica 35(4): 469-485 | 41 mm thickest fresh knot where the stem is 12-18 cm; 5 knots a metre; vertical branches 47-160 mm | Holds. The method: the thickest knot of each type per 2 m section, flush-delimbed, from stump to the 12 cm diameter (p. 473). The figure: "the thickest fresh knot in the small-sized log section of silver birch was, on average, 41 mm" (p. 479), a mean over trees of each tree's thickest. 5 knots a metre counts all types. Stands 70-90 years old (Table 1); dominant 26-30 cm, codominant 21-23 cm (Table 4, strata 1-2). **Not in the design's reading:** knots grow with tree size ("When the size of the tree was taken into account, the differences ... practically disappeared", p. 479), and vertical branches in that section reach 47-70 mm as stratum means (p. 481). So a model limb of 5-7 cm is not unknown on real trees. What the paper does not show is 11-14 of them in one tree | Publisher's PDF, text layer, read by me. CONFIRMED |
| Demol et al. 2022, Silva Fennica 56(1): 10550 | Under 2.5 cm +73 %, over 10 cm +4 % | Holds: a diameter bias. Two ash trees, leaf-off | Fetch tool's summary. SUSPECTED |
| Stener et al. 2017, Silva Fennica 51(2): 1713 | Fresh knots below 3 m, 12.1 and 10.8 mm; angle 42° and 41° | Table 3 **pools pruned and unpruned trees** (pruned to 3 m at 9-10 years). Cut at 9-10, the pruned trees' knots pull the means down. "All knots were described as fresh." Taken from cake-slice samples, not the surface. So it is no like-for-like test of the model's limbs on the lowest 3 m | Fetch tool's summary. SUSPECTED |
| Gailis et al. 2020, Silva Fennica 54(2): 10220 | Double leaders 6-12 % at 10 | 6-12 % is a range over trials; the record is binary, made at 10 (Table 2 also lists 14); not defined | Fetch tool's summary. SUSPECTED |
| Zeltiņš et al. 2018, Forests 9: 52 | 34.9 % double tops at 40; angle 43.2°; projection 2.9 m | Not reopened: the publisher refused the fetch tool (HTTP 403). The design itself labels the trees grafted clones. **So "forks are real in stands too, a third of trees by 40" (summary point 5) carries a grafted-clone figure into a stand claim.** It should say grafted clones | Not read. SUSPECTED |
| Sone et al. 2005 | "The form of part R" | Not reopened (PubMed showed only a cookie notice). On the design's own reading of the abstract (ring per leaf area "goes with" the branch's light), that is a correlation in nine young maples. **The straight line λ ∝ q is the designer's step.** "Its one advantage is that its form has a source" overstates it | Not read |
| Niemistö 1995a, Mäkinen 2002, Lintunen 2013, Viherä-Aarnio & Velling 1999, Ilomäki 2003, Sellin & Kupper 2006, Nikinmaa 2003, Lehnebach 2018, Minamino & Tateno 2014 | as in the design | Not reopened | – |

Nothing in the design is labelled "sourced" that is plainly the designer's own step, except the straight-line form above. Its values table says "borrowed from maple", and its summary should match. Other borrowings are labelled: Demol (ash), Sone (maple), Nikinmaa (Scots pine), Lintunen used beyond his sizes. One more nuance: the model's thickest at 50-60 is compared with "about 4.1 cm on old trees", and the design rightly calls that a floor (SUSPECTED 4-6 cm).

## 5. Part R, worked through

**Ten years by hand, seed 1's upper crown, 50 to 60** (CONFIRMED arithmetic on the limb log, the effect SUSPECTED). The cut each year is replaced ring carbon × (1 − q) × 5.088e-4 kg. q is the designer's stand-in ("rel"), or that × 0.65, near the open-sky scale at 50-60 ("abs").

| Limb | Base 50 → 60, cm | Leaf 50 → 60, m² | q (rel) over the ten years | Wood gained 50-60, kg | Cut, rel; abs, kg (share of the gain) |
|---|---|---|---|---|---|
| A, z 16.1, the thickest | 5.23 → 8.28 | 7.4 → 14.7 | 0.65 → 0.54 | 11.29 | 3.27 (29 %); 4.85 (43 %) |
| z 16.3, leaf falling | 4.48 → 5.81 | 4.8 → 3.1 | 0.47 → 0.34 | 1.14 | 1.10 (96 %); 1.37 (over 100 %: no ring) |
| z 18.2 | 2.18 → 4.52 | 1.6 → 3.2 | 0.95 → 0.49 | 1.38 | 0.38 (28 %); 0.63 (46 %) |
| z 19.2, the best lit | 1.85 → 5.03 | 1.4 → 5.2 | 1.00 → 0.77 | 2.34 | 0.27 (11 %); 0.68 (29 %) |

- What R does: a declining limb's ring stops, as Mäkinen's abstract describes. Every other limb thickens less, the biggest by a third or more. It makes no limb thicker, no fewer limbs, no fork. "Fewer thick limbs" yes; "fewer, thicker, forking" no.
- **The spec and the desk differ.** The rule (section 4 of the design) takes q_L "as the shedding test reads it ... 1 = open sky". The desk script uses own carbon per leaf area over the tree's 90th percentile that year, capped at 1. Under that stand-in a quarter of every year's best limbs read 1 by construction, so they lose nothing. I compared it with the tree's mean bud light (stats `carbon.mean_bud_light`, absolute): the absolute scale is 0.84 / 0.78 / 0.67 / 0.63 of the stand-in at 30 / 40 / 50 / 60 (SD 0.04-0.06). This is SUSPECTED, since the bud mean includes the stem's well-lit buds. If q is open-sky light:
  - stand limbs lose much more than the desk says;
  - open-grown limbs, whose leaf-weighted light is under 1 wherever leaves shade each other, are thinned too. That breaks "open-grown: no change (under 0.01)", and with it the tuned `branch_sapwood_thick_m` (set against the thickest open limb, 16 cm on a 44 cm stem).
- **Double counting.** I found none in carbon. The compiled ring code takes `keep` as given. Upkeep counts internodes, not wood, so a thinner limb is not kept alive longer through upkeep. Light would then enter four places: the shoot share, the shedding line, leaf traits, and the ring. That is a compounding, not a double count. In the wood mechanics a thinner shaded limb bends more (load / r⁴) and rights itself less (ring / r²). That is new: the flat arms thin all limbs evenly, while R thins the shaded ones more. With the stand-in, the swinging lit limbs of the height-faults note (second tops and forked upper limbs) are untouched. With open-sky light they thin, and their swings grow.
- **Free numbers.** The design says none are new. In fact five choices are unmade or unsourced:
  1. whether q is absolute or relative, and if relative, the reference (the desk used the 90th percentile);
  2. q for limbs younger than `min_branch_age`, which the shedding test doesn't read;
  3. q for fork axes, reiterated limbs and a second top (on the leader's axes they take the stem's rate);
  4. the straight-line form;
  5. s, which "would be retuned".
  None has a birch source.

## 6. Branch wood: does the census support the claim?

The desk method itself can be checked: apply it with a flat q to the 0.30 control and compare with the 0.15 and 0.20 arms that were actually run (CONFIRMED arithmetic):

| On today's stems, A3 log-scale mean | 30 | 50 | 60 | Limbs over 5 cm at 50; 60 |
|---|---|---|---|---|
| Desk, flat 0.15 | 0.82 | 0.91 | 1.04 | 1.8; 3.8 |
| Run, flat 0.15 (`node_b_r15`) | 0.77 | 0.86 | 0.95 | 3.0; 8.1 |
| Desk, flat 0.20 | 0.92 | 1.10 | 1.28 | 4.5; 8.0 |
| Run, flat 0.20 (`node_b_r20`) | 0.89 | 1.04 | 1.18 | 6.3; 10.1 |
| Desk, R with the stand-in (the design's figures, reproduced) | 0.81 | 0.98 | 1.19 | 2.5; 5.4 |
| The same, corrected by the flat arms' run/desk (0.94-0.97; 0.95; 0.91-0.92) | about 0.77 | about 0.93 | about 1.09 | about 4; about 10 |
| Desk, R with q × 0.8 | 0.75 | 0.85 | 1.02 | 1.2; 3.6 |
| Desk, R with q × 0.6 | 0.69 | 0.73 | 0.84 | 0.5; 2.4 |

- With the stand-in, A3 after a run is about 0.93 / 1.09: inside the band, nearer its middle than the design's "about 0.85 / 0.95". The design over-corrects for the thicker stem. A3 rises 22 % between stem diameters of 28.6 and 31.1 cm at 60 (50.3 to 61.5 kg), so part of any "fix" on this row is the stem getting thicker, not the branches getting lighter.
- **With q as the rule defines it** (open sky), scale about 0.65-0.8 over the years the cut builds up, A3 reads about 0.69-0.81 at 50 after the same correction, at or under the band's 0.76. **If so, the 0.30 rate would have to rise, not stay.** Plainly: the census can't settle it, because the limb log holds no light reading. The design's "the rate need not move" holds only for a relative q, which its rule text does not say.
- **The desk underestimates the big limbs that remain** by about a factor of two on both flat arms, so its "limbs over 5 cm: 2.5 / 5.4" is likely about 4 / 10 in a run.

## 7. What it breaks (from the 0.15 arm as proxy, CONFIRMED where read; SUSPECTED for R)

| At 50; 60 | Control (0.30) | Flat 0.15 run | R (SUSPECTED) |
|---|---|---|---|
| Stem wood at 1.3 m, cm | 25.5; 28.6 | 27.6; 31.1 | between, nearer 0.15 on open-sky q |
| LAI, stand trees | 4.73; 4.60 | 4.87; 4.91 | +0.1 to +0.3; more on open-sky q |
| Crown ratio at 60; lowest live branch at 60, m | 0.46; 12.6 | 0.49; 12.0 | about the same as 0.15 |
| Living internodes (thousands); run time, s | 57.4, 54.9; 76 | 61.1, 59.4; 81 | +6-8 %; +6 % |
| Limbs; median life | 51.1, 45.4; 18.3 y | 51.2, 46.5; same | no change expected (upkeep doesn't count wood) |

- Forest plots: the Baltic LAI row already fails by 0.01 at 50, and freed carbon builds leaf. A forest fail is likely, as the design says.
- Top height and the curve: the leader's height is unchanged in the flat arms, so no effect is expected. The height-faults swings are untouched with the stand-in, and larger with open-sky q (section 5).
- The forecast is one a run could contradict. But as section 8 shows, the run could contradict the tests while the mechanism works.

## 8. The falsifying tests

| Test | Flat 0.15, run or desk | Separates R from a flat rate? |
|---|---|---|
| 1. Two thirds of the cut on limbs over 20 years old | desk 0.74 / 0.90 | No: the wood is in old limbs, so any cut is |
| 2. Upper over lower half at equal length at least 0.75 | run 0.80 / 0.79 (0.20: 0.74 / 0.75; 0.10: 0.86 / 0.85; control 0.65 / 0.67; 14-19 seeds have both groups; SD 0.10-0.16) | No: it moves with any lower rate. R's desk 0.82 / 0.83 is 0.02-0.04 from flat 0.15 |
| 3. Limbs over 5 cm fall by more than half, over 2 cm by under 10 % | run −72 % / −43 %: fails at 60 | No; and R probably fails it at 60 even if it works (section 6) |
| 4. Count, 90th length, life within 2 paired SE | holds on all flat arms | No |

**Required:** a test only R can pass. Inside one run, a limb's ring per unit of leaf should rise with that limb's light, slope above zero by more than 2 SE, where today's slope is near zero. Or: at matched A3, the thickest limb where the stem is 12-18 cm and the count over 5 cm should be lower under R than under a flat rate, by more than 2 paired SE. Hand measurements test those; the band's middle does not.

## 9. The smallest build, what to cut, what to ask

**Build first (pass): the logging-only count.** It changes no growth and needs no owner choice beyond running it:

1. Add one column to the limb log: each limb's leaf-weighted light as the shedding test reads it (`ratio` at `growth.py:843`, already formed when `shedding.log_limbs` is on). Optionally add whether the limb is a fork axis or reiterated.
2. Prove switch-off: stand trees seeds 1-3 with the log on against `node_t2_kt`, `--switched shedding.log_limbs`, identical.
3. Then 10 open-grown trees to 60 with the limb log on, one tree timed first.

With that column, part R's desk reading can be redone on real q (absolute and relative), for stand and open trees, before anyone writes R.

**Cut from the design until then:**
- part R's A3 and size figures as "at today's rate" (sections 4-5 and summary point 4);
- "the form has a source";
- "forks are real in stands too" without "grafted clones";
- the base-over-sapwood row as evidence of thickness;
- tests 1-3 as tests of the mechanism.

**Ask the owner before any model build:**
1. The measurements say stand limbs are too thick and too many thick ones, which is the opposite of "thicker". **Is "fewer, thicker, forking" about the open-grown tree and the winter look?** The look audit's K6 measure is limb over stem at 1.3 m, which forks and second tops change and a ring rule doesn't.
2. **Forks:** on both of the model's readings it has none at 10 and 1-2 of 20 at 40, against 6-12 % (progeny trials) and 35 % (grafted clones). The reading need not be chosen first. May a fork rule be designed and tested on both?
3. **Branch wood (decision 6(b)):** the flat 0.15 and 0.20 arms already exist. At 50 / 60, 0.15 reads 0.86 / 0.95 of A3 and 0.20 reads 1.04 / 1.18; the thickest limb is 6.0 / 7.0 and 6.4 / 7.4 cm, against Heräjärvi's 4.1. Choose one, keep 0.30, or wait for R with a defined q?
4. The scan row in step B's rule: restate it with dead branches and the software's error, or drop it?
5. Papers: Mäkinen, Ojansuu & Niemistö 2003 (branch models for planted silver birch) is the one that would set both count and size. May it be bought?

## What I checked, and what I didn't

- CONFIRMED: all census figures in section 1 recomputed from `limbs.json`, `stats.json` and `tree.json` of `node_t2_kt`, and A3, thickest, over 5 cm and the scans' reading for `node_b_r15` and `node_b_r20`. Also: test 2 on four arms; the desk method with five variants of q; the light-scale comparison; limb A and the upper crown of seed 1, 50-60; run seconds and internode counts from `runs.csv` and `stats.json`. Code read at `85ae47f` at the lines named. Heräjärvi 2001: the publisher's PDF, text layer (pp. 470-481, Tables 1, 2, 4).
- SUSPECTED: Demol 2022, Stener 2017 and Gailis 2020, read through the fetch tool's summary of the publisher's page. The absolute light scale (a tree mean bud light, not a limb's). The dead-branch window of 10 years. Every effect of R.
- Not done: the fork shares and double-top counts (not in the limb log); Zeltiņš 2018 (HTTP 403); Sone 2005 (PubMed showed a cookie notice); every other source in the design; open-grown limbs (no record).
