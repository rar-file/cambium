# Re-review: the fixes to M2's grid, corrections and Q21

Fresh reviewer, 2026-11-06. This is the one re-review allowed for this step. Commits reviewed: `a9b36e6`, `063dd94`. Two more landed while I worked: `e3b1dee` (validation, not reviewed) and `e93ecc6` (the k tests in Q21; I checked its figures only). **Line numbers are at `e93ecc6`.** Read-only apart from this file. I didn't connect to the node. My scripts and the lock sandbox are in the session's scratchpad, folder `rr`.

**Bottom line**

- **The numbers hold.** Q21's table, 4.69, 4.38, Q22's and Q23's figures, the season runs and the grid table all reproduce. Q23's quotes are exact to the thesis text.
- **Q25 isn't fit to send yet.** It has two statements that are wrong and one test that's narrower than it reads.
- **Q22 and Q21 each leave out a fact that cuts against how they're argued,** and Q22's option (b) reopens the second chance row 68 closed.
- **Five first-review items weren't done:** the leaf charge in `KNOWN_ISSUES.md`, `daily:161`, row 63, queue 11's comment on (d), and the tool-order note. `CAMPAIGN.md:33` says the FIX items are done; that isn't so.
- **The lock does its main job.** Its weak spots are a silent stall if the lock is left behind, and a disk check that doesn't do what its comment says. Neither threatens today's run.

## 1. The first review's items

| Item | State | Evidence |
|---|---|---|
| A. Stars dropped from the daily table | **Fixed** | `daily:236-250`; every cell agrees with `m2_grid_table.txt` |
| A. "Written before it was read" | **Fixed** | Row 62 (`DECISIONS.md:76`), `daily:236`. The diff touches only the heading; the lines are unchanged |
| A. "Inside its frame"; "none of the nine run" | **Partly** | Row 65, `daily:252`, `Q22:73` are right. `CAMPAIGN.md:33` still says "none fits inside its frame"; `QUESTIONS.md:160` "no apical setting fits" |
| A. Row 66(a): three things to write first | **Partly** | Row 68 has all three (`DECISIONS.md:82`). But row 66 (`:80`) still reads "fits only if the mean of all 40 seeds" with no pointer to row 68; `CAMPAIGN.md:33` says "Judge queue 11 by row 66"; and see N7 |
| A. Say "proposed" | **Partly** | Titles and tables do. `CAMPAIGN.md:33` "each correction", `QUESTIONS.md:73` "both corrections", `daily:253`, `daily:256` don't |
| A. `CAMPAIGN.md:33`, `daily:5`: no adopting before Q21 | **Fixed** | Both now wait on Q21 and Q23 |
| B. 0.016 given as SE | **Fixed** | Row 65, `daily:252`; I get 0.18 SE, 2 of 20 seeds |
| B. Wood off "clean" | **Fixed** | `QUESTIONS.md:98`; 3.62, 55 % inside, recomputed |
| B. Weak plot rows | **Fixed** | `daily:232` |
| B. All rows share one baseline draw | **Fixed** | `daily:234` |
| B. Spread and share beside verdicts (PROTOCOL section 2) | **Partly** | Grid table yes, though LAI's SD at 50 is dropped from `daily:238`, and LAI at 50 is the near miss. Plot table (`daily:222`) has neither, though `m2_plots_corrections.txt` has the spread |
| C. k table | **Fixed** | `daily:196-204`, `QUESTIONS.md:96`; all recomputed |
| C. One mechanism, not two | **Fixed** | `QUESTIONS.md:101` |
| C4. Light band may close | **Partly** | 4.69 and 4.38 are there. The review's 4.07 for wood on was dropped, and that changes the reading: N10 |
| C5. "Follows the death line" | **Partly** | Corrected at `daily:194`, but `daily:164` still ends "So on plots, light follows that line", and `:194`'s "my line here" points at text that's gone |
| C6. A second candidate beside the 21 % guess | **Partly** | `QUESTIONS.md:103` fixes "sits near" but still names only the 21 % line. `KNOWN_ISSUES.md:767-771` (no wood, about 2 points lighter than exp(-0.37 LAI)) isn't cited |
| C7. LAI's pass may lean on the k offset | **Fixed** by `e93ecc6` | `QUESTIONS.md:113`. I reran it: LAI -0.386 +- 0.075, -0.286 +- 0.052 |
| C. Height and LAI linked | **Fixed** | `daily:141`, `:254`, Q16 |
| D. Apical control in M2: ask the maintainer | **Fixed** | Q22 raised |
| E. Plots provisional | **Fixed** | `QUESTIONS.md:89`, `daily:220`, `:146`, row 68(6) |
| E. Source's stands | **Partly** | Stems/ha are in `QUESTIONS.md:99`. The crown-ratio row's own doubt (Q13, Q15) isn't |
| E. Two wood-off runs | **Partly** | Reported at `daily:234`, but "So the mend... holds with wood on... but not with wood off" and "The cause isn't established" contradict. Four other commits touch `treegen/` in that range. Say "something in `f45928e..3f3d687`, likely `0386ce7`, my inference" |
| E. `plots_identical.py` needs the one-plot folder first (a note) | **Not fixed** | No mention in `CAMPAIGN.md`, `DECISIONS.md`, `QUESTIONS.md` or the daily report. Given `base_plots` first, it says DIFFERENT (first review, E), so 66(e) can misread |
| F. Idle figures | **Partly** | Row 73, `daily:111`. "8-10 of 14 until about 15:25" has no start. From `runs.csv`: mostly 14 of 14 until 15:09:51 (a dip at 15:03), then 5 to 15:11:45, 10 to about 15:24, 5 to about 15:49, none from 15:51:32 |
| F. Guard alive | **Can't check** | Row 72 says so. The local `usage.log` ends at 10:01:59 |
| F. Waiting script reports a pause | **Partly** | Row 73 claims it. No such script is saved in `tools_local`, and `node_m2_queue11b.sh` doesn't look for `guard_paused.txt`: N31 |
| F. Delete leftovers | **Fixed** | Row 72; `node_swap_q11.sh` does what it says; 14,116 - 12,694 = 1,422 MB |
| F. 15 at once logged | **Fixed** | Row 70, row 60, `daily:109`; times recomputed |
| F. admin-account session | **Fixed,** as far as the builder may | PID 26524 is gone from this PC, and no SSH session to the admin account runs here. The orphan on the node I can't see. Q24 asks |
| G. Leaf charge: open and quote | **Fixed** | Q23; N14 |
| G. Leaf charge: log in `KNOWN_ISSUES.md` | **Not fixed** | Last touched 09:54, `48159fd`; no "charge" entry. Same for `0386ce7` not being output-only with wood off (PROTOCOL section 5) |
| G. Wood off, gate item 1 | **Fixed** | `QUESTIONS.md:87`, `daily:233` |
| G. 0.46-0.54 | **Fixed** | `QUESTIONS.md:75` |
| H1, H2, H3, H4, H6, H7, H8 | **Fixed** | Q21, `daily:254` (6.98 +- 0.46, recomputed), `daily:162`, `:232`, `:255`, `:231`, Q16, Q18 |
| H5. Leaf charge wording | **Partly** | Wood-off figures added, all right. Wood on's LAI at 60, +0.127 +- 0.092, is still left out of `QUESTIONS.md:59` and `:181` |
| Stale: `daily:135`, `:181` | **Fixed** | Now `:146`, `:192` |
| Stale: `daily:150`, "queued on the PC" | **Not fixed** | Now `daily:161`. `pc_nowood_a4.4` and `pc_nowood_a4.0` finished by 12:38. `daily:172` and `:173` look stale the same way |
| Stale: `CAMPAIGN.md:38-39` | **Fixed** | Both agree with row 54 and the daily report. `:42-43`, `:33` are stale: N16 |
| File references | **Fixed** | I checked `growth.py:240-243, 781, 952, 707-724, 1132-1160, 1325-1329, 1589, 1606-1608, 1624-1629` and `species/betula_pendula.yaml:356-370` |
| Gate files re-saved | **Fixed** | Reran `gate_nowood_plots.txt` and `gate_both_trees.txt`: byte for byte |
| Tool: `y50_ahead` read as a fit; spread, share | **Fixed** | Saved table reruns the same; `--outside` works |
| Tool: checks seeds, machine, commit | **Partly** | N24 |
| Row 66(b) can't pick | **Fixed** | Row 68(5) |
| Row 63 lacks `m2_cc_y50_ahead` | **Not fixed** | `DECISIONS.md:77`; `git show a9b36e6` doesn't touch it |
| Queue 11's comment on (d) | **Not fixed** | `node_m2_queue11.sh:64` still "ready for each correction if it's adopted". 11b drops the comment, so this one line is left |
| Point 10. Guesses labelled | **Partly** | "as my reading" added in Q16 and `daily:162`. `daily:164` isn't |

**Count, by row: 26 fixed, 14 partly, 5 not fixed, 1 can't check.**

## 2. New findings

### Q25

| # | Finding | Verdict |
|---|---|---|
| N1 | **"Sits inside Siljansfors's measured dates" is backwards** (`QUESTIONS.md:42`). Day 130-273 starts 2 days before bud burst (132) and ends 1 day after 50 % yellowed (272): `reports/research_notes.md:119`. It's within 1-2 days of the medians, and inside their ranges (116-141, 252-284), which Q25 doesn't quote. And this season "sets only the sun path today" (`reports/M2_design_draft.md:76`; `treegen/environment.py:106`, the only use), so the agreement says nothing about growth. Q25 should say that. Those dates are a subagent's table, also unsaid | **FIX** |
| N2 | **"(a)... The model stays one site, inside the site-index bands" is false** (`QUESTIONS.md:45`). At default, height is over its band at all five ages (`gate_nowood_trees.txt`, baseline column), and with both proposed corrections at 20, 30 and 60 (`gate_both_trees.txt`). Say "one site, near SI 26, over its band today" | **FIX** |
| N3 | **The fine-root test is narrower than it reads** (`:40`, `:46`). In the model the ratio moves only fine-root upkeep and water uptake (`growth.py:1333`, `:1656`, `:1252`). Building and replacing fine roots sits in the root share, 0.25-0.6, set by water stress and not by this ratio (`species/betula_pendula.yaml:265-271`). CROBAS's route is below-ground allocation (`research_notes.md:109`). So "makes no ladder" holds for what was run, not for CROBAS's mechanism, and (b)'s "knowing it makes no ladder" goes too far. It may not change the recommendation, but the maintainer should know. Also unsaid: the run has wood on, no leaf charge; Minunno is a subagent's reading (`M2_design_draft.md:5`), not reopened. "(c)... not obviously the shape" is an unlabelled guess | **FIX** |
| N4 | **The whole case against a season limit is an untested sentence** (`:42`). It's labelled "my reasoning", which is right. But leaf and fine-root upkeep are charged per season too (`species/betula_pendula.yaml:233`, `:246`; `growth.py:1332-1334`), so a shorter season isn't only alpha: it would lower carbon fixed and those two costs, and leaves' weight against wood changes with age. That also undoes "the one season term that does vary by age", which rests on nothing exhaustive. The PC is idle (`CAMPAIGN.md:30`). One run, about 10 minutes: alpha and both upkeep values x the same test value, against `pc_cc`. Run it, or say why not | **FIX** |
| N5 | Season figures otherwise right: -0.32, -0.36 at 5, 10; SI 28.3, 28.5 at 15 (`pc_cc` 28.2); lag-1 -0.75, 25 % against -0.76, 28 %; +0.19 at 20, +0.36 at 50. Fertility: SI 26.1 to 25.0, ratio 0.97-1.04. Left out at `daily:257`: crowns narrow significantly at 0.25 (-0.39 +- 0.15, -0.60 +- 0.25 at 50, 60), which supports "not the lever" | OK; add it |

### Q22

| # | Finding | Verdict |
|---|---|---|
| N6 | **Numbers right:** none of nine, 0.016, 10 %, -0.74 +- 0.13, -0.159 +- 0.061, 27 % to 4 %, 2.49, 3.00, about 7 m. "Crowns get narrower" is under 2 SE (-0.38 +- 0.20, -0.48 +- 0.27): give the figures | OK; small FIX |
| N7 | **Option (b) is what row 68 closed, and its label isn't available** (`QUESTIONS.md:79`). "Picks young 0.50 if the fresh seeds support it" is the second chance row 68(1) says it isn't, with "support" undefined. "Labelled calibrated" needs bounds from published ranges and independent patterns (PROTOCOL section 9), and `:75` says this isn't a range. The maintainer may overrule that, but (b) has to say so: "overrides row 68's no, and accepts 0.46-0.54 as a range" | **FIX** |
| N8 | **"The same kind of trade as lowering alpha" hides the main difference** (`:73`, `daily:253`). The first review said it too; by age it isn't so. Paired against `m2_cc`: young 0.50 lowers height by 0.96, 0.96, 0.87, 0.74, 0.74 m at 20-60; alpha 4.4 by 0.53, 1.10, 1.34, 1.39, 1.61 m. LAI at 50, 60: -0.097 +- 0.061, -0.159 +- 0.061 against -0.312 +- 0.078, -0.162 +- 0.071. So young 0.50 takes the most off when young, where the model is too tall, and alpha takes the most off when old: the shape problem in the maintainer's brief. At 50 it costs a third of alpha's LAI for half its height; at 60, the same LAI for under half. This is the best case for (b), and it isn't shown. The maintainer's own rule may still decide it, and I'm not changing the recommendation | **FIX** |

### Q21

| # | Finding | Verdict |
|---|---|---|
| N9 | **Table and arithmetic right.** k recomputed from seeds, all 12 cells. -ln(0.198)/0.345 = 4.694, /0.37 = 4.377. Paired k: -0.045, -0.049 on trees, -0.052, -0.055 on plots. `e93ecc6`'s k table agrees with `pc_kcheck.txt` and my rerun | OK |
| N10 | **"The outputs are neutral" holds for one question only** (`QUESTIONS.md:101`, `:123`). Against exp(-0.37 LAI), yes. On whether a plot can pass light and LAI together, no. At wood on's k 0.398, 19.8 % needs LAI 4.07, inside 3.6-4.5; at wood off's 0.345, 4.69, outside. The only plot set to reach both bands has wood on (lines at 0.15, a test value: 18.5, 18.3 %, LAI 4.35; `daily:204`). That doesn't make the double count right, but the maintainer should see it before choosing. Add 4.07, and limit "neutral" to the k distance | **FIX** |
| N11 | **(b) has gone stale and has no end** (`:119`, `:123`, `daily:20`). "The k runs below are in": they're in, and above. `daily:20` still says "while I test". What's left is Q19, which needs the maintainer. And since the input can't be calibrated (PROTOCOL section 9), no k result could end the hold by itself. Say what would | **FIX** |
| N12 | "Trees and plots are one mechanism" (`:101`) is an inference for k. Why LAI rises 0.53 on trees and 0.33 on plots isn't explained. Label it. `daily:194` "a steady k" holds at 50 and 60 and across settings, not across ages: wood off is 0.321, 0.336 at 20, 30 (`pc_kcheck.txt`) | **FIX** (small) |
| N13 | **Row 69:** the inference is labelled, and `e93ecc6` hedges it further. Arithmetic is unshown, but they're test values. Trees only: Q21's "light stays at 26-29 %" says nothing about plots, where the light question sits. Say so | OK; small FIX |

### Q23

| # | Finding | Verdict |
|---|---|---|
| N14 | **Quotes exact** to `rper09.txt` lines 1658, 1660, 1670, printed p. 26, with Report A102. Q23 should say what `daily:176` says: text layer, delta signs missing. **Code right:** `:1325` waives fresh laterals, `:1608` charges n late leaves plus one cluster per shoot, `:242` gives each fresh lateral a cluster next spring, `early_leaves` 2.5 (`species:424`). The growth mode is `lignum` (`species:607`) and a search of `growth.py` finds no store of carbon, so "no storage module" fits. "Adds carbon from nowhere" is loose: it skips a cost. Labelling is right: "my reading" | OK; small FIX |
| N15 | **Q23 and Q21 disagree** (`:59`, `:123`). "With wood off, the state I'd run it in", but Q21 recommends holding wood on. Take both recommendations and the charge runs with wood on, where height moves 0.47-0.79 m and LAI stays at 3.32, 3.40. Queue 11 and its noise runs only test the charge with wood off. Q23 should give both states without assuming, and `CAMPAIGN.md:33` should say what M2's report and M3 run on if Q21 and Q23 are still open. Figures: right | **FIX** |

### Record and consistency

| # | Finding | Verdict |
|---|---|---|
| N16 | **`CAMPAIGN.md`:** `:42-43` still say build the fertility option and "Read p. 157; decide build or park", against Q25's "Meanwhile" and `daily:281`. `:33` "about 13 GB" (row 72 has 14,116 MB), "Judge queue 11 by row 66", "its FIX items are done" | **FIX** |
| N17 | **Row 68's substance holds, and the timing checks.** Committed 16:58:16. No queue 11 label is in `out/bench/ensemble` even now. Files newer than 16:05 outside `pc_*`: two gate re-saves, the grid table, validation, wood tables, 11b. `node_swap_q11.sh` prints labels only. Row 68(1) and (4) stop the builder picking on the rerun. I can't see whether a log was read on the node, and the rerun had likely finished there by 16:58 | OK |
| N18 | **Restricted word:** row 70's last column, "logged; fixed from here on" (`DECISIONS.md:84`). No scorecard backs it, and N29-N31 show gaps. Say "changed from here on". Elsewhere: "matches" at `QUESTIONS.md:101` is a negative with numbers beside it, OK | **FIX** |
| N19 | **`daily:281` states the result before it's read:** "M2's report: alpha can't fit both", with queue 11's alpha runs unread, while Q16 (`QUESTIONS.md:185`) says they may change the answer. Add "unless queue 11 shows otherwise" | **FIX** |
| N20 | **Q18 hangs on a route Q22 removes** (`:158`, `:160`). "The apical route" is its reason, "if the apical grid doesn't hold up, I'll bring this back", and row 65 says it hasn't. Point to Q22. "Gets one rerun" should follow row 68 | **FIX** |
| N21 | **Numbers with no saved output** (PROTOCOL section 5). No file under `out/bench/ensemble` holds the node and plot k cells at both ages, 6.98, -0.159, the wood-off charge row, 55 %, seed 6's 17.84, or the per-plot figures. They check out by my rerun, but they rest on the first reviewer's scratch scripts. Save them, with a tool, and give the path in Q21-Q23 | **FIX** |
| N22 | **Rows 70-73, figures:** 14:42:36-14:50:11, 5+5+5, confirmed from `runs.csv` (the 16s are rounding, under 1 s). Trees' first start 14:42:24, plots' last 14:42:25, so the inferred cause fits. 02:00:51 to 16:33 is 14.5 h. The first review had the PC process at 02:01:19; "3 minutes" holds either way. The maintainer's 02:04 isn't on disk; commit `1394777` at 02:05:03 fits it. Row 72's arithmetic holds; its outcome I can't see | OK |
| N23 | **PC sets mix code fingerprints:** `pc_cc` has 3 inside it, `pc_k0.40_nowood` spans 3 commits. Harmless: no file in `treegen/`, `cli.py` or `species/` changed since `3f3d687`, the fingerprint covers the whole repo (`treegen/params.py:72-87`), and the manifests list only this review's file and two tools as uncommitted. But `tools/gate.py:76` would refuse these sets. Say so if they're ever cited | OK |

### `tools/m2_grid_table.py`

| # | Finding | Verdict |
|---|---|---|
| N24 | **Logic right,** and the daily table agrees cell by cell, apart from two hand-worded last cells ("no, by 0.016", "numbers yes, not picked"). **"Stops" overclaims.** It prints every row and verdict first, then adds "NOT LIKE FOR LIKE" and returns 1. Tested: mixed seeds, mixed machines and mixed commits are each flagged. **Not caught:** a table of only 5-seed sets exits 0 (row 62 says 20; `gate.py:39` has the number); a set with three code fingerprints exits 0, because it reads only `code_of(r)[0]`, where `gate.py:76` refuses. "As tightened by row 68" covers only row 68(2). Say "Warns", check for 20 seeds, and compare the whole code tuple or say why not | **FIX** |

### The lock script, `node_m2_queue11b.sh`

I ran it unchanged under `/usr/bin/dash` on this PC, with stubs for `ps`, `df`, `nice`, `sleep` and Python, in a sandbox. So this tests the shell's logic, not the node.

| # | Question | Finding | Verdict |
|---|---|---|---|
| N25 | Can two launches count the same places? | No, within the script. Every launch is under the lock. The 45 s is a fixed sleep, not "until the new workers show", as the comment says, but it's enough: workers start 3 s apart (`batch.py:102`, `runs.csv`), so 14 take 39 s, and the next reader's `ps` comes after a further 60 s inside `node_limit.py`. The memory check won't delay plots: lowest free at a plot launch was 62.7 GB, against about 43 needed | OK |
| N26 | Any other way over the limit? | A batch reads one low between seeds, for up to about 0.5 s (`batch.py:118-155`). From `runs.csv`, 1-2 % of the time in a tree batch. A launch reading then goes over by one. Small, and worth a line in row 70, which doesn't mention it. Reading `ps` twice a second apart and taking the larger closes it | OK; note |
| N27 | Does it count the first script's batches? | Yes: `ps -eo args` is machine-wide, and `--mark-done` wrappers are left out. Sandbox: 5 plots and 5 trees left over gave "4 at once", total 14 | OK |
| N28 | Deadlock? | None on normal paths. No wait holds the lock, and the lock was gone at the end | OK |
| N29 | Lock left behind? | **Yes, silently.** No trap, no time limit. A kill or a reboot while it's held (about 105 s per launch) leaves `launch.lock`, and `lock()` waits for ever with its error hidden. Tested with an existing lock: 40 s, 0 bytes of output, 0 launches. That's the quiet stall of Q20 again. Only `node_swap_q11.sh` clears it. Also: the `exit 1` at `:13` can never fire, because the pipeline's status is `tail`'s. A failed `node_limit.py` gives an empty L, which dash reads as 0 (tested), so it waits for ever. Non-numeric output kills the shell with the lock held (tested: "Illegal number"). `CAMPAIGN.md:33` makes this pattern the rule, so mend it before the next use: print a line after, say, 10 minutes waiting, and remove the lock on exit | **FIX** |
| N30 | Does the disk check do what its comment says? | **The reading works; the promise doesn't.** It reads free disk before waiting for places, perhaps an hour early. The second batch reads 45 s after the first starts, before its 1.4 GB is written, and neither counts the first script's plots still writing. Example: 10,700 MB passes both checks, then ends about 7,830 MB, under the 8,192 floor. And 8,192 + 1,024 + 1,434 = 10,650, not 10,600. **Today it's safe:** from 14,116 MB, even with all of a3.5, base, a3.0 and y50_ahead still to write, it ends at about 9,530, 1.3 GB over the floor, before any growth by the server's other services. Mend it for the next queue: read after the wait, and subtract what's in flight | **FIX** |
| N31 | Does QUEUE11_FINISHED wait for everything? | Yes, including the first script's batches. Sandbox: with a leftover that outlived everything 11b started, the marker came 1 s after it ended. `sh` being dash is fine. Two traps. A paused run stays in `ps`, so after a guard pause the loop spins with no message, and 11b never looks at `guard_paused.txt`. And any command line holding the text `ensemble.py`, such as a remote wait from the PC, keeps it open for ever: row 71's bug again. Print a line when the pause file exists, and don't put that text in a waiter | **FIX** |

### Can the maintainer answer these without reading code?

| Q | Answerable? | What's in the way |
|---|---|---|
| Q21 | Not quite | **k is never defined,** and "input k" and "implied k" carry the whole argument. One line would do it, and PROTOCOL section 5 needs the calculation anyway: "k is how fast light fades through leaves. Worked back from the model's output, k = -ln(light) / LAI. So 19.8 % light needs LAI = -ln(0.198) / k" |
| Q22 | Mostly | "Young 0.50" has no starting point (it's 0.60 now). "Old", "dominance 0.62" and "the lines" aren't explained |
| Q23 | Yes | P, M, G and W are undefined, but the next sentence says it in words. "A tip's cluster" and "late leaf" could use one plain line |
| Q24 | Yes | Clear, and one command. Small: if the node has rebooted since, that PID may be something else, so check first |
| Q25 | **No** | "0.24 to 1.44" has no unit or current value (fine-root mass per leaf mass, now 0.48). "Ladder", "height ratio", "reading SI 28.3", "at the low end", "CROBAS" and "PRELES" aren't explained. Say in words what a ladder is: taller at better sites, with the curve's shape kept |

**ASK MAINTAINER:** nothing new. Q21-Q25 stay with the maintainer, once the FIX items above are in. Q22's "Meanwhile" and row 68(4) agree, and so do Q21's, Q23's and `CAMPAIGN.md:33`, apart from N15.

## 3. What must still change

**Before the maintainer reads Q21-Q25:**

1. Q25: N1, N2, N3, and plain words. N4: run the season test, or say why not.
2. Q22: N7, N8, and the starting values.
3. Q21: N10, N11, N12, and define k.
4. Q23: N15, H5's LAI at 60, the text-layer note.

**In the record:**

5. `KNOWN_ISSUES.md`: the leaf charge; `0386ce7` not being output-only with wood off; the k offset at wood off.
6. Row 63 (`m2_cc_y50_ahead`); a pointer from row 66 to row 68; row 70's word; row 73's start time (15:09:51).
7. `CAMPAIGN.md:33` and `:42-43` (N16). Record the `plots_identical.py` order before 66(e) is read.
8. `daily:161`, `:164`, `:172`, `:173`, `:194`, `:234`, `:281`, and `:20`. `QUESTIONS.md:158`, `:160` (N20).
9. `node_m2_queue11.sh:64`.
10. Save the k cells and paired figures with a tool, and cite the path (N21).

**Before the next node queue:**

11. Lock: N29, N30, N31.
12. Tool: N24.

**Not needed for today's run:** queue 11b can carry on as it is.

## What I couldn't check

- **The node:** whether 11b is running, the guard, free disk, whether the lock is held, the orphan PID 960329, whether the first script's trees really reached `m2_cc_a4.0` before 16:33. If they didn't, 11b leaves a gap in row 66(b), so check that every label in row 66 has a folder when fetching.
- **Whether anything from queue 11 was read on the node** before 16:58. Nothing was fetched.
- **The waiting scripts** of row 73: not saved, so unseen.
- **The maintainer's 02:04 message:** not on disk.
- **Minunno 2019, Palubicki 2009, Hagemeier 2019b, Swedish Forest Phenology:** worked from `reports/research_notes.md` and the reading in the repo. Perttunen 2008: text layer only, not the rendered page.
- **`e3b1dee`:** not reviewed. **`e93ecc6`:** its figures only.
- **Queue 11's results:** not read.
