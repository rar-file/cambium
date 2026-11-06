# Review: M2's apical grid, the two proposed corrections, queue 11, Q21

Fresh reviewer, 2026-11-06. Commits reviewed: `bb3f24b`, `a5530e1`, `bd4b7a2`. `73812b7` (row 67 only) landed while I worked and isn't in scope. Read-only, apart from this file. My scripts are in the session's scratchpad (`r1.py` to `r9.py`). I didn't connect to the node.

**Bottom line**

- **The numbers hold.** The grid table, control and six gate tables all rerun the same, apart from two cut lines. Every grid folder's `--set` values match its label. All are 20 seeds on the node at `3f3d687`. Nothing is adopted.
- **The readings don't all hold.** The biggest gap: wood shade off moves the model's k from about 0.40 to about 0.345, as far below the paper's 0.37 as it was above. Q21 doesn't say so, and its recommendation leans on a sentence that isn't true.
- **Two things need the maintainer:** wood off (Q21), and whether apical control belongs in M2 at all.
- **Three node items went unlogged:** 15 runs at once for 7.5 minutes, a live SSH session as the admin account, and a queue that ends about 0.5 GB above its own disk floor.

## The ten points

| # | Point | Verdict | Evidence |
|---|---|---|---|
| 1 | Did what was approved? | **ASK MAINTAINER** (wood off); **FIX** (rest); OK (rings ahead left out) | Row 62's lines were applied, and the tool agrees. But the stars row 62 asks for are dropped, "written before it was read" is too broad, and "inside its frame" ignores dominance 0.62. Row 66(a) loosens row 62. See A below |
| 2 | One seed, one run, within the noise? | **FIX** | 0.016 is 0.18 SE. Wood off's LAI "FAIL to PASS" at 50 is by 0.019, with 55 % of seeds inside. A same-setting twin reads 3.69, not 3.62. No plot noise run exists. New tables give no share of seeds. See B |
| 3 | Two failures really one? | **FIX** | Light follows LAI at a steady k on trees and plots. Wood on, k 0.39-0.40; wood off, 0.345. The report doesn't show this, and it splits one failure into two ("on trees LAI, on plots the death line"). See C |
| 4 | Wrong knob? | **ASK MAINTAINER** | Apical control is sharing, which the maintainer put in M3 (`CAMPAIGN.md:22`). At 60, young 0.50 lowers height by 0.74 m and LAI by 0.16 +- 0.06, the same trade as alpha. See D |
| 5 | Like for like? | **FIX** (the report's wording) | Trees OK: control identical. Plots: baseline at `68782d9`, options at `3f3d687`; the only plot control is at `f45928e`, and one plot is queued. Neither the daily report nor Q21 says so. See E |
| 6 | Machine idle? | PC and node now: OK, as far as I can see. **FIX** (record) | PC busy, 6.2 GB free. Node not checked live. Earlier: no runs at all from 15:51:32 until queue 11, and 5-10 of 14 places used from 15:09. The daily report has no figure. See F |
| 7 | Shared machines | **FIX** | Servers are safe at the floor; the queue may not be. Margin about 0.52 GB. Plus the 15 at once and the admin-account session. See F |
| 8 | Sources | **FIX**; bound goes with point 4 | Gate item 1 isn't met today by either correction: no equation with a page. The 0.46-0.54 bound is a list of illustrated values on synthetic trees. See G |
| 9 | Claims beyond the work? | **FIX** | Table numbers check out. Six statements go too far, and some lines are stale. Restricted words: none misused. See H |
| 10 | Guesses labelled? | **FIX** (small) | Q21's inference and guess are labelled. Unlabelled: "sharing moves height without costing leaves", "leaves respond to light, height to sharing", "on plots it follows the death line" |

## A. Point 1 in detail

**Row 62 as written: FIX.**

- **Stars dropped.** Row 62 says a verdict within about 0.2 m of an edge "counts as depending on the draw... and I report it as such". `m2_grid_table.txt` has the stars. The daily report's table (`daily:204-216`) drops them, and its note says only that F marks a height outside its band. So 13.52, 22.71, 25.07, 26.64 and the rest read as plain passes.
- **"Written before it was read" is too broad** (row 62; `daily:202`). Row 62 went in at 13:46:06, and the eight new settings were fetched at 15:58, so that part holds. But `m2_cc`, `m2_cc_young0.54` and `m2_cc_young0.50` were fetched at 13:43 and are quoted in the same commit, including "fails by 0.016". `daily:182` says it correctly: "before the rest is read". The lines themselves weren't bent, since they're the approved bands, but the claim should match.
- **"Inside its frame" doesn't hold for the closest setting.** Row 62 lists `apical_dominance` with bounds 0.46-0.54. Every candidate except the two dominance rows keeps dominance at 0.62, outside that bound (`species/betula_pendula.yaml:138`). The only settings with all three inside the bound reach 19.31 and 16.61 m at 60. So a pick of young 0.50 is a partial fit, and that should be said.
- **"No setting fits" means none of the nine run** (row 65). Young 0.46 with old 0.50 wasn't run, for instance.

**Row 66(a): it loosens row 62. FIX, before queue 11 is read.**

- Row 62 said "means of 20 seeds", and the answer was no. The rerun was added after that answer, and only for the near miss. PROTOCOL section 9 allows a rerun only for a sourced new option that looks significantly worse, to guard against a false block.
- In its favour: the lines are unchanged, it's one shot, the first 20 seeds still count, and it's written down in advance.
- It can still reverse the verdict with no change to the model. To reach 3.60 on 40 seeds, the fresh 20 need 3.616 or more. My rough arithmetic, assuming the lines are independent: about 40 % on that line and about 30 % on all lines. That's a guess at a chance, not a measurement.
- **Three things to write down first:**
  1. A verdict within the noise on LAI counts as depending on the draw, as height's does. Ensembles at the same or almost the same setting differ by 0.07-0.12 at LAI 50 (3.69 against 3.62; 3.21 against 3.09); the 40-seed SE is about 0.064.
  2. Whether plots can veto. 66(b) makes alpha pass on trees and plots, but 66(a) doesn't ask that of young 0.50, which is 2.49 and 3.00 m over on plots.
  3. A pick waits for the maintainer's answer on point 4.

**Keeping young 0.50 with rings ahead out of the pick: OK.** It's outside row 62's parameters, has no published rule, and Q18 is open. Two things are missing from the report, though (H7).

**Wood off as a "correction of a documented error": ASK MAINTAINER (Q21 is the right place).**

- It is documented: `KNOWN_ISSUES.md:773` and `:2128`, and `species/betula_pendula.yaml:356-370`. But `:2128` says "looks like", the species file says VERIFY, and Q21 itself says the paper doesn't state it.
- The label decides the outcome. `gate_nowood_plots.txt` says "These items: pass" only because `--kind correction` was chosen. Treated as a new option, four worse rows would mean a rerun, and a block if they repeat. The builder chose the label, and titles and tables already use it as fact ("Wood shade off is a correction", "The two corrections"). Say "proposed".
- **May the builder reverse row 3 alone? No.** Row 3 sits in the approvals log. The audit finds no approval behind it (`reports/claude_audit.md:62`), so the record conflicts, and only the maintainer can settle that. Q21 asks, which is right. But `CAMPAIGN.md:33` says "at M2's close, adopt the corrections that hold", with no wait for Q21, and `daily:5` says none of these questions blocks M2. **FIX both.**

## B. Point 2: noise

| Claim | What the data show |
|---|---|
| Young 0.50, LAI at 50 "no, by 0.016" | 3.584, SE 0.091, 11 of 20 seeds at 3.60 or more. Height at 20 passes by 0.09, SE 0.15, 55 % of seeds inside. Only 2 of 20 seeds meet every line at once |
| Wood off, LAI at 50 "FAIL to PASS" (Q21: "clean") | 3.619, 55 % inside. The same setting at `f45928e` reads 3.693 |
| Plot top height at 50 worse by 0.23 m | +0.231 +- 0.106, t = 2.18 on 4 degrees of freedom, per plot +0.21, +0.08, +0.52, -0.06, +0.41. It meets the 2 SE rule, but it's weak; at 60 it's 1.2 SE |
| Charge, plot light at 50 worse | +0.292 +- 0.144, t = 2.03. Two of the five plots carry it |
| Wood off, plot light worse by about 2 points | **Real:** +1.81 and +2.25, t 12.8 and 19.9, every plot moved by +1.57 to +2.65 |

- **Five plots is the rule, so that's fine.** But 2 SE on 5 seeds is a loose bar, and no tiny-change noise run exists on plots. Rows near 2 SE should say so.
- **Every comparison shares one baseline draw.** The report notes that 4.79 and 4.81 "sit together, off the baseline" (`daily:133`): LAI at 50 is 3.21 and 3.21 against 3.09; height at 60 is 26.82 and 26.87 against 27.07. It doesn't carry that forward. All rows paired with `base_trees` inherit that offset, in the direction of more LAI and less height.
- **A 2 SE test failed on a same-setting pair.** See E, on the two wood-off runs: 3 of 7 rows passed 2 SE.
- **PROTOCOL section 2** asks for the spread and the share of seeds beside each verdict. `m2_grid_table.txt` and the daily report's new tables have neither.

## C. Point 3: light follows LAI, and wood moves k

Implied k is -ln(light) / LAI, from ensemble means. "Gap" is the model's light minus exp(-0.37 LAI), in points. Recomputed from the per-seed folders.

| Setting | Age | LAI | Light (%) | Implied k | Gap |
|---|---|---|---|---|---|
| Trees, wood on (`base_trees`) | 50 | 3.094 | 30.14 | 0.388 | -1.69 |
| | 60 | 3.274 | 27.51 | 0.394 | -2.27 |
| Trees, wood off (`m2_nowood`) | 50 | 3.619 | 28.58 | 0.346 | +2.37 |
| | 60 | 3.818 | 26.58 | 0.347 | +2.23 |
| Trees, both (`m2_cc`) | 50 | 3.681 | 27.86 | 0.347 | +2.24 |
| | 60 | 3.852 | 26.35 | 0.346 | +2.30 |
| Plots, wood on (`base_plots`) | 50 | 3.769 | 22.32 | 0.398 | -2.48 |
| | 60 | 3.761 | 22.29 | 0.399 | -2.59 |
| Plots, wood off (`m2_plots_nowood`) | 50 | 4.114 | 24.12 | 0.346 | +2.30 |
| | 60 | 4.078 | 24.54 | 0.345 | +2.42 |
| Plots, both (`m2_plots_cc`) | 50 | 4.098 | 24.31 | 0.345 | +2.35 |
| | 60 | 4.060 | 24.79 | 0.344 | +2.52 |
| Plots, wood on, death lines 0.15 | 50 | 4.353 | 18.47 | 0.388 | -1.51 |
| | 60 | 4.353 | 18.25 | 0.391 | -1.73 |

Paired change in k with wood off: trees -0.045 +- 0.009 and -0.049 +- 0.005; plots -0.052 +- 0.002 and -0.055 +- 0.001. On plots, k stays at 0.391-0.399 across alpha 3.0-4.8 with wood on, and 0.343-0.346 across all wood-off sets.

**What it shows:**

1. **Neither setting sits on the paper's line.** Wood on is 1.7-2.6 points darker than exp(-0.37 LAI); wood off is 2.2-2.5 points lighter. The model's own output doesn't favour wood off.
2. **The paper's stand figures don't settle it either.** LAI 4.6 with its median 14.8 % gives k 0.415. Table 5 gives 0.37. The reading itself expects slack between them (`hagemeier2019b_publisher_reading.md:27`). At LAI 4.6 the model would give about 16.0 % with wood on and 20.5 % with wood off. Arithmetic only.
3. **"Worse on plots, clean on trees" is one mechanism, not two.** k falls by about 0.05 in both. On plots, LAI rises 0.32-0.35 and that doesn't make up for it, so light rises. On trees, LAI rises 0.53-0.54 and light barely moves (-1.56 +- 1.17, -0.93 +- 0.49). No hidden second error is needed to explain the direction. Q21's "second error" may still exist, but plain arithmetic explains the sign first, and Q21 doesn't give it.
4. **Wood off may close the light band inside row 52.** At k 0.345, 19.8 % needs LAI 4.69, above row 52's ceiling of 4.5. At LAI 4.5, light is 21.2 %. At k 0.37 it needs 4.38; at k 0.398, 4.07. So if k stays at 0.345, no plot can pass light and row 52's LAI together. The maintainer should see this in Q21 before choosing option (a). Arithmetic, not a run.
5. **"On plots it follows the death line" (`daily:183`) is a false split.** With the 0.15 lines, LAI goes to 4.35 and k stays near 0.39. The line moves LAI, and light follows LAI, as on trees.
6. **Q21's guess fits less well with wood off.** Q21 says plot light "sits near" the 21 % line. It does with wood on, at 22.3 %. The wood-off plots, which are the question, sit at 24.1-24.5 %. A second candidate belongs beside the guess: leaf-only k comes out at 0.345 against the input 0.37, an offset `KNOWN_ISSUES.md:765-771` already records at phases 17-20 (3.65, 27.9 %).
7. **LAI's pass on trees may lean on the same offset.** Inference: with wood off, leaves see more light than k 0.37 would allow, and that's part of why LAI rises.

**Height and LAI are linked too** (`daily:130`), and row 62 fits only those two. LAI is the tree's leaves times stems per hectare, and stems per hectare follows height. Dominance 0.50 shows it: LAI 3.58 at 50 from a tree with 37.9 m2 of leaves, at 946 stems/ha. That's the trap the last review found for apical x 0.75, and `daily:215` lists it unflagged.

## D. Point 4: apical control belongs to M3

- **The brief** (`CAMPAIGN.md:22`): if no alpha fits both, M2 reports that the problem is how carbon is shared out (M3's work) and doesn't force the fit. The brief's M2 calibrates alpha, against the Eriksson shape, Liziniewicz and Repola, and adds fertility and season. It doesn't mention apical control.
- **The repo's own notes place it in M3:** `reports/research_notes.md:11` ("M3a"), `reports/milestone_M1.md:430` ("Bears on the every-other-year pattern (M3)").
- **Row 62 was the builder's own decision.** It fits sharing parameters to height and LAI inside M2, which is close to what the maintainer ruled out.
- **Same trade as alpha.** Young 0.50 against `m2_cc`, paired: height -0.74 +- 0.14 and -0.74 +- 0.13; LAI -0.097 +- 0.061 and -0.159 +- 0.061; light +1.19 +- 0.69 and +1.49 +- 0.56; crown width -0.38 +- 0.20 and -0.48 +- 0.27 at 50 and 60. Crowns are already too narrow (`daily:185`).
- **It damps a pattern M3a hasn't explained.** Lag-1 goes from -0.74 to -0.39, and years under 2 cm from 27 % to 4 % (`m2_grid_alternation.txt`). M3a's lag hypothesis is still open. Q17 says the young excess may be `max_shoot_length`.
- **It removes the drop in apical control with age** (`species/betula_pendula.yaml:139-146`), which `daily:182` notes "needs thought".
- **The calibration rule isn't met as it stands:** the bound isn't a published range (G), and height and LAI aren't independent patterns (C).

**Proposed question for the maintainer:** may M2 pick apical values at all, or does M2 report the near miss and leave them to M3? My recommendation: leave them to M3. Queue 11's runs can stay as evidence.

## E. Point 5: like for like

| Item | Finding | Verdict |
|---|---|---|
| Trees, baseline | `base_trees` at `68782d9` (commit stated, row 35) equals `m2_base_3f3d687`: reran it, 20 seeds, 37,820 fields, 0 differences | OK |
| Grid | 11 sets, seeds 1-20, one machine, one commit; `--set` values in each manifest match the label | OK |
| Plots, baseline | `base_plots` at `68782d9`, options at `3f3d687`. Row 64's control is at `f45928e`. Between those two, plot code didn't change, only off options in `growth.py` and the read-out in `light.py`, so identity is likely. Not shown until 66(e) runs | Plan OK |
| Plots, report | `gate_*_plots.txt` show the two commits. The daily report's plot table and Q21 don't, and don't call the results provisional. `daily:135` still says the `--set` control "is queued" | **FIX** |
| 66(e)'s tool | `tools/plots_identical.py` walks the first folder's plots. Run as `base_plots m2_plots_base_3f3d687`, it reports plots 2-5 missing and says DIFFERENT. Give the one-plot folder first | Note |
| Source's stands | Q21 compares plot light with a band from stands of 880 and 420 stems/ha. The model's plots hold 1,566 and, with wood off, 1,660 at 45 (`m2_plots_corrections.txt`). Wood off moves density further away. Q13 notes the mismatch; Q21 doesn't. The crown-ratio row Q21 cites has the same doubt (Q13, Q15) | **FIX** |

**Two wood-off runs differ, and the report never says why.** `daily:150` gives LAI 3.69, 3.79, from `m2_diag_nowoodshade` at `f45928e`. `daily:172` gives 3.62, 3.82, from `m2_nowood` at `3f3d687`.

- Same setting, same seeds; 0 of 20 seeds equal. Height at 50: -0.284 +- 0.102. Height at 60: -0.208 +- 0.093. LAI at 50: -0.074 +- 0.035. That's 3 of 7 rows over 2 SE, far more than chance should give.
- The runs part at about year 6-7, and heights separate by year 15 (seed 1).
- The wood-on control is identical, so wood-off's path is what changed. The likely cause is the read-out mend `0386ce7`, labelled "output only" (`treegen/light.py:176-179`), which lengthens the grid when wood is off. That cause is my inference from the diff.
- The gate isn't harmed, because its option and baseline agree at `3f3d687`. But "output only" doesn't hold for wood-off runs, and this pair is a measure of real noise that nobody has used. **FIX: report it.**

## F. Points 6 and 7: machines

**Idle.** PC at 16:31: about seven runs, 6.2 GB free against a 4 GB floor. Node: `CAMPAIGN.md` says queue 11 is running; not checked live.

From `runs.csv` in queue 10: trees ended 15:09:51, plots ended 15:24:28 and 15:51:32. Places used: 8-10 of 14 until about 15:25, then 5, then none from 15:51:32 until queue 11 started. The script's copy here is timed 16:04. Q20's answer says it "sat idle until I looked", with no figure, and the daily report's "What went wrong" doesn't list it. **FIX: add it.**

**Disk: safe for the servers, tight for the queue.**

- 13 GB - (3 x 1.4 + 0.28) = **8.52 GB, about 0.52 GB above the floor,** before growth by other services and fetch packs. Tree sets are small: 2.2 MB per 20 seeds here.
- 1.4 GB looks right: free disk fell from 25,963 MB at 10:01:59 (`usage.log`) to about 13 GB over about ten plot sets. A small error or a world save would still reach the floor.

**At the floor** (`tools/node_disk_guard.sh`):

- The guard pauses every run-account Python, writes `guard_paused.txt`, and exits. Nothing is lost, and the servers keep their 8 GB.
- Paused plots keep their memory, up to about 67 GB with 10 plots at 6.7 GB, until someone resumes them. Nothing resumes them on its own.
- The queue's shell isn't paused, so anything it launches afterwards runs with no guard watching.
- Queue 11 doesn't look for `guard_paused.txt`, or check the guard is alive. So a stall could sit as quietly as Q20's did. I saw no check in its waiting scripts; I didn't read all of them.
- `ORIGIN_FLOOR_GB` in `tools/batch.py:39-45` is memory only, so the script's comment "the disk floor still applies" rests wholly on the guard. I can't tell whether it's running: the copy of `usage.log` here ends at 10:01:59.

**FIX:**

1. Confirm the guard is alive, and record it.
2. Have the waiting script report a pause.
3. Consider deleting your own leftovers, which row 34 allows. Fetched copies hold 67-69 MB per plot set, so most of the 1.4 GB isn't what verdicts read. `side_on_node.sh` also copied the golden runs into the side copy. I can't see from here what's safe to remove.

**Memory: OK.** Lowest free at any launch in queue 10 was 37.2 GB.

**15 runs at once, against a limit of 14, unlogged. FIX.**

- From about 14:42:36 to 14:50:11, `m3_plots_ahead_nowood` (5), `m2_plots_cc` (5) and `m2_cc_y54_o46` (5) overlapped, from `runs.csv`, ignoring overlaps under 2 s.
- The limit was 14: 9 trees and 5 plots ran just before.
- Likely cause (my inference): the trees' count ran while the plots were still starting, 3 s apart (14:42:13-25), so it saw 9 plots, not 10.
- Row 60 says "none of the later queues can repeat it". **Queue 11 has the same check-then-launch.** Harm was small, but it needs logging, and the next queue needs a lock.

**Live SSH session as the admin account. FIX: close it, log it, tell the maintainer.** PID 26524 on this PC, started 02:01:19: `ssh ... admin@node "while pgrep -f run_first_jobs.sh ..."`, still `Established` to port 22 at 16:31. PROTOCOL section 6 and row 27 say not to use the admin account unless the maintainer asks. It may be only a leftover wait, but it's an open session on the shared machine's admin account. I didn't touch it.

## G. Point 8: sources

| Item | Finding |
|---|---|
| Leaf charge, gate item 1 | **Not met.** No equation or page is quoted anywhere. `growth.py:1327-1329` and `species/betula_pendula.yaml:241` say "exploring". The logic holds by my reading: `:1608` charges one late leaf per node and one `early` per shoot; `:1325` waives fresh laterals; `:240-243` gives them `early` next spring. It adds no number. A published form may be at hand: `reports/research_notes.md:50`, Perttunen 2008, Eq. 3 p. 17, Eq. 21 p. 26. But that's a subagent's reading from a garbled text layer, and it doesn't say foliage is in the term. The docstring cites Perttunen 1996, which is unread (`daily:108`). It's also not in `KNOWN_ISSUES.md`: "documented" rests on a review note (N8) and `daily:165`. **FIX:** open it, quote it, log it. If no equation covers it, **ASK MAINTAINER** whether a carbon-balance correction satisfies item 1 |
| Wood off, gate item 1 | **Not met yet.** The removal adds no number, and what it removes has none opened: no page gives 0.40 (`species/betula_pendula.yaml:443-444`). But `I = I0 e^(-K LAI)` is a paraphrase (`hagemeier2019b_publisher_reading.md:26`), through a summarising fetch (`:5`), with a section and no page. The PDF isn't in `birch-data\09_light\`. Q21 labels the wood step as inference, which is right |
| 0.46-0.54 | Palubicki 2009 Sec. 4.2, Fig. 7, p. 4: "parameter lambda are 0.46, 0.48, 0.50, 0.52, 0.54", on synthetic trees (`research_notes.md:11, :51`). That's five illustrated values from a simulation paper, not a range and not birch: under section 3, a model value. It has one lambda; row 62 applies it to three parameters. Two defaults sit outside it. Row 62 flags it as weak. I don't think it meets "bounds from published ranges". `M2_design_draft.md:5` says such readings must be reopened before citing; I can't tell whether this one was. **Goes with D** |
| Third-party copies | None in this step's new text, as far as I can trace |
| Tuning | Row 62's lines weren't moved, and "I'm not moving the line for the 0.016" is right. But young 0.50 came from stepping towards height, on patterns that aren't independent. That's why D matters |

## H. Point 9: claims

**Checked and right:** every number in the daily report's two new tables, Q21's table, Q18's update, and rows 54 and 65, all against raw outputs. Q16's apical numbers match too.

| # | Statement | Problem |
|---|---|---|
| H1 | Q21: "a light reading that only passes by counting wood twice isn't a real pass" | Light fails either way: plots 22.3 % with wood on, band top 19.8 %. There's no pass to give up, and this is half the recommendation's reason |
| H2 | Q21: "The arithmetic follows the paper's method" | The method may support removing it, but the arithmetic of the outputs is neutral (C1, C2), and C4 is left out |
| H3 | `daily:219`: "0.54 takes 7.8 m off height at 60" | -7.76 is against `base_trees`, and includes young 0.50 and both corrections. Dominance alone, against young 0.50: **-6.98 +- 0.46** |
| H4 | Q16, `daily:151`: "sharing moves height without costing leaves" | True at 50 and 60. At 30, x 0.9 costs 6.19 +- 2.3 m2 and x 0.85 costs 18.29 +- 2.56 m2 (33 %). LAI at 30 under x 0.9 is -0.279 +- 0.10. It's one factor, with wood on |
| H5 | Q16: charging "lowers height by 0.47-0.79 m at every age and raises LAI at 50 by 0.23" | That's ages 20-60, wood on, against one baseline draw. Age 10 is -0.108 +- 0.066. **With wood off,** the state queue 11 runs in, it's -0.40, -0.42, -0.34, -0.15, -0.05 m (under 2 SE at 30, 50 and 60), and LAI +0.06 +- 0.07, +0.03 +- 0.06. LAI at 60 with wood on (+0.127 +- 0.092, under 2 SE) is left out. Plots show no effect on height or on LAI at 50 |
| H6 | `daily:199`: wood off makes "LAI better" on plots | The gate says "no change" and "Improved: none": both are inside the band. Light and LAI aren't a gain and a loss here, since k moved |
| H7 | `daily:220`, Q18: rings ahead with young 0.50 "the only row that meets the numbers" | True of means. Omitted: height SD at 60 is 2.40 m against 0.71; light SD 7.18 against 2.65; seed 6 collapses (17.84 m, LAI 1.72, 55 % light at 60); several seeds gain 5.5-7.7 m from 40 to 60, where most gain about 3. On plots, rings ahead with wood off raises height at 20, 30, 40 by +1.62, +1.51, +0.93 m (t 5-11). Queue 11's plots matter for that reason |
| H8 | `daily:198`: "Plots stay taller than stand trees" | Compares top height with a single stand tree: not the same measure (`daily:53`) |

**Stale:**

- `daily:135`, the control "queued"; `daily:150`, wood-off runs "queued on the PC"; `daily:181`, "Plots with each are running", contradicted by `daily:199-200`.
- `CAMPAIGN.md:38-39`.
- File references that no longer point at the code. `daily:165` gives `growth.py:1275-1277` and `:1551`; the code is now at `:1325-1329` and `:1606-1608`. `daily:158` gives `:1551-1556` and `:1566-1571`; `daily:147` gives `:661-664`, and wood is at `:707-724`. `daily:150` gives species lines 351-354 and 356-359; the text is at 356-370. PROTOCOL section 5 asks for file:line.

**Files altered on saving:** `gate_nowood_plots.txt` and `gate_both_trees.txt` have one line cut short. The first loses `site_index_curves (age 50)` from "Significantly worse". Q21 has that row, so nothing was lost in the report, but re-save them whole.

**Tool, `tools/m2_grid_table.py`:**

- Its logic is sound: verdicts from `evaluate_ensemble`, star at 0.2 m either side, LAI floor as row 62 states. The table reruns byte for byte.
- It prints "Fits by row 62? yes" for `y50_ahead`, which row 65 says is outside the rule, and row 65 cites that file as evidence.
- It doesn't check seed count, machine or commit. It omits spread and share.
- **FIX those. No number is wrong.**

**Row 66(b) can't pick.** Trees run 3.5-5.0; plots run 3.0, 3.5, 4.8. Only 3.5 and 4.8 overlap, and 66(b) needs one alpha to pass on both. 4.8 already fails. For 3.5, `m2_cc_a4.4` reads LAI 3.37 at 50 and height 13.95 at 20, both misses, and lower alpha has lowered LAI so far. So "pick nothing" is nearly certain. The rule is honest, but it should say that, given the disk these plots cost. **FIX.** Also: row 63 doesn't mention `m2_cc_y50_ahead`, and queue 11's comment on (d) wasn't updated with row 66(d).

## I. Other points

| Item | Verdict |
|---|---|
| Q21 raised, with options, and "don't revert" followed | OK |
| "I'm not moving the line for the 0.016" | OK |
| Rule committed before queue 11's results could exist (`a5530e1` at 16:04:55; no fetch yet) | OK as far as I can see; start time not checked on the node |
| Row 66(d)'s corrected wording: the gate's noise test still runs at each adoption | OK |
| Ages 50 and 60 in every new table | OK |

## Asks for the maintainer

1. **Q21, with the k table added.** Wood off moves k from about 0.40 to about 0.345, with 0.37 between them. If k stays there, light and row 52's LAI can't both pass. The method argues for removal; the outputs are neutral. Row 3's record conflicts with the audit, and only the maintainer can settle it. I'm not overruling the recommendation, only saying its stated reasons don't yet carry it.
2. **New question:** may M2 pick apical values, given "M3's work... doesn't force the fit", and does 0.46-0.54 count as a published range? Recommendation: no pick in M2.
3. **Conditional:** if no published equation covers the leaf charge, does a carbon-balance correction satisfy gate item 1?

## What I couldn't check

- **The node live:** whether queue 11 is running, the guard, actual free disk, when queue 11 started, the limit in the queue logs.
- **Hagemeier & Leuschner 2019b:** I tried mdpi.com once and got HTTP 403. I didn't look for another route, and no PDF is on disk. I worked from the reading in the repo.
- **Palubicki 2009:** not opened; worked from `research_notes.md` and the audit.
- **Queue 11's results:** not read, as asked.
- **Tests and the three checkers:** not run, and not part of this step.
