# PROTOCOL.md: fixed working rules

The rules every change to the model was made under, and still is. Only the maintainer changes this file. Read it in full at the start of every round of work and give its git hash in the round's report. If a round's brief conflicts with this file, stop and ask. "The builder" is whoever changes the code in a round; the checkers are separate reviewers who see only the outputs, diffs and sources.

## 1. Fixed files (never change without the maintainer's approval)
- PROTOCOL.md
- reference/targets.yaml (the approved version is git tag "targets-approved")
- tests/ (never loosen or delete a test; adding tests is fine)
- tools/scorecard.py
- Default values in species/betula_pendula.yaml (new options are always off by default)
- outside data folders such as `tree-data` (never change them; scans there are GPL-3.0 and for comparison only)

## 2. Targets
- Use only targets in the approved targets.yaml, and only within their stated conditions (age, stand type, scenario).
- PASS/FAIL comes only from tools/scorecard.py run on saved outputs. Paste its output unchanged. Never write PASS/FAIL by hand.
- Verdicts come from an ensemble of seeds run entirely on one machine: 20 seeds for single trees, 5 for plots. The verdict is the ensemble mean against the target band. Report the spread and the share of seeds inside the band next to it. One seed alone is not a verdict.
- A miss is reported as a miss. Never call a miss "close", "approaching" or "sufficient" without the number and the target next to it.
- You may propose a new or changed target (value, source, page/table, conditions) under "Proposed targets". It is not used until the maintainer approves it and the tag is moved.

## 3. Sources
- Every parameter has a source (paper, page/table/equation, DOI) or the VERIFY flag.
- Open a source before citing it. Search summaries don't count.
- Values taken from other simulation models are labelled as model values, not measurements.
- Never copy code from GPL, non-commercial or unclear-licence sources. Published equations and values with citations are fine.

## 4. Changes
- Diagnose before changing anything. State the mechanism in words, with file:line references.
- Fixes must follow a published formulation; quote the equation. No invented fractions, bypasses, clamps or scaling functions to force a behaviour.
- Never tune a parameter to hit a number. If a correct mechanism makes results worse, the fault is elsewhere: find it.
- Every change is a new option, off by default, tested alone against the current default, with a before/after table. Combined tests and plots only when the brief asks.
- Compare an option with the baseline on the same seeds (paired). An effect only counts if the paired difference is larger than 2 standard errors.
- Commit each step separately. All tests must pass.

## 5. Honesty
- Every number in a report comes from a saved output or script; give the path.
- Never describe code you haven't read this round; give file:line.
- Never present predicted numbers without the calculation. Otherwise write "not calculated".
- Answer every task item in its own section, starting with "Answer:". If you can't, write "Not done:" and why.
- Don't use the words matches, solved, fixed, eliminates, perfect, fully, definitively or confirmed unless the scorecard or a quoted source backs that exact claim.
- If an earlier report was wrong, say so and correct KNOWN_ISSUES.md.

## 6. Machine
16 GB machine for now (one stick). One heavy run at a time. Light runs (single trees, under 1 GB each) may run in parallel within the free-memory floor. Heavy runs (plots, mesh exports) stay one at a time. Check free memory in a separate call before every launch, and don't launch if that would leave less than 4 GB free. Never detach a process to dodge the memory guard. A restart from year 0 with the same code and seeds is allowed any number of times, on any machine; log each one. Any other restart of a killed run, such as resuming from a save file, is allowed once, after finding and fixing the cause; log it. When 32 GB is installed, the 8 GB / two-run rule returns.

Every comparison (a screen, a calibration, a milestone's verdicts) runs entirely on one machine, recorded in its manifest.

Node (a cloud server: 16 ARM cores, 94 GB; other services run there): batch runs only. Use only a dedicated user with no admin rights, reached over SSH with its own key (`tools/node/README.md`). Never use the server's admin account unless the maintainer asks. Before each batch, check the CPU used by every process that isn't ours, averaged over a minute: if it's above 1 core, run at most 8 at once; otherwise at most 14. Leave at least 8 GB free, and run at the lowest priority (nice 19). Work only in the run account's own folder. No system-wide installs, no open ports, no changes to anything else on the node. Ask the maintainer before anything that needs admin rights. Copy code at a fixed commit over SSH, never through a public site, and only the data the runs need. Never change tree-data.

## 7. Every round
1. Read PROTOCOL.md, the latest phase in KNOWN_ISSUES.md, and the git log since the last round.
2. Plan: list the subtasks, which run in parallel, and which wait for a heavy run.
3. Research subagents run in parallel and never edit the repo. Each returns: the claim, page/table/equation, DOI or URL, and whether it applies to silver birch in Sweden.
4. Only the builder (main agent) edits code and runs models.
5. Three fresh checker subagents. They see only the outputs, diffs, sources, PROTOCOL.md, targets.yaml and KNOWN_ISSUES.md:
   a. Sources and targets: re-open every source; diff targets.yaml against the tag "targets-approved"; confirm every target used is approved and used within its conditions.
   b. Numbers and consistency: recompute every figure from saved outputs; rerun scorecard.py; compare claims with earlier phases; check every summary word against the numbers.
   c. Rules and completeness: check every rule in this file; confirm every task item was answered with mechanisms explained in words; confirm every statement about the code matches the code.
6. Fix what the checkers flag. The builder may not overrule a checker; anything unresolved goes to the maintainer as a decision.
7. Write the phase notes in KNOWN_ISSUES.md, save the full report as reports/phase<NN>.md, commit both, then stop.

## 8. Report template (always these sections, in this order)
1. Summary (5 lines at most, plain words)
2. Scorecard (scorecard.py output, unchanged)
3. One section per task item, each starting with "Answer:"
4. Changes made (commit, what, on or off by default, before/after)
5. Proposed targets (if any; not in use)
6. Checker results (what each caught, what was fixed, what's unresolved)
7. Corrections to earlier reports
8. Decisions for the maintainer (numbered, each with options and a recommendation)

Reports are read by people who don't code: keep them short and plain, with tables. Every table includes ages 50 and 60 where relevant.

## 9. Campaign mode
- Keep going. After each step, update CAMPAIGN.md and move to the next. Don't stop to ask unless a hard stop applies.
- Hard stops: stop, write the reason in CAMPAIGN.md, and report. They are:
  - anything irreversible (deleting data or git history, force-pushing, touching tree-data);
  - a licence question you can't settle;
  - a change to a fixed file that isn't covered by the pre-approvals below;
  - the same blocker failing twice;
  - a contradiction between sources, or with PROTOCOL.md, that you can't resolve.
- Blocked doesn't mean stopped. If a milestone is blocked, record why and continue with the next milestone that doesn't depend on it.
- Each milestone follows the same path:
  1. Diagnose: the mechanism in words, with file:line references.
  2. Build changes as options, off by default, quoting the published formulation and page.
  3. Test each option alone against the current default, on the same seeds as the ensemble baseline.
  4. Combine them and test again.
  5. Run the three checkers.
  6. Write reports/milestone_MN.md using the PROTOCOL.md report template, including renders.
  7. Apply the adoption gate.
  8. Run git tag campaign-MN-done.
- Adoption gate (pre-approved). An option becomes the default only if ALL of these hold:
  1. it follows a published formulation (equation quoted, page given) and adds no invented numbers;
  2. all tests pass;
  3. on the scorecard's ensemble verdicts, no approved target goes from PASS to FAIL against the ensemble baseline (for corrections, see below);
  4. no target gets significantly worse: further from its band by more than 2 standard errors (paired seeds);
  5. all three checkers pass.
  Corrections of documented errors don't need to improve anything. If one makes a target significantly worse, or takes it from PASS to FAIL, don't revert it: put it in QUESTIONS.md, because it may be exposing a hidden second error.
  A new option added to improve the fit must improve at least one target by more than 2 standard errors. If a sourced new option looks significantly worse on a row, rerun the option and the baseline once on new seeds, with no change between; it's blocked only if the same row is worse again.
  After every adopted model change, rerun the same tiny-change noise test on the node and report whether the model got steadier or wilder.
  Log every adoption in DECISIONS.md as "auto-adopted under the campaign gate". If a sourced, correct new option fails item 3, item 4 or the improvement rule, don't adopt it and don't tweak it until it passes. Put it in QUESTIONS.md, look for the fault elsewhere (PROTOCOL.md section 4), and continue.
- Pre-approved target changes (an exception to the fixed-file rule):
  a. correcting an existing target so it matches its source's exact definition (quote and page; checker A confirms);
  b. adding a new target from a source read in full, with the exact page or table and its stated conditions (checker A confirms).
  For every target change: show before and after in the milestone report, add a DECISIONS.md entry, and move the targets-approved tag. Never loosen a target to make a result pass.
- Calibration (pre-approved). Only for a parameter with no direct source:
  - set its bounds from published ranges;
  - fit it against several independent patterns at once;
  - validate on data not used in the fit;
  - label it "calibrated" in the species file, with the fit and the validation.
  Never calibrate a parameter that has a direct source.
- Checkers: three fresh subagents per milestone (sources and targets; numbers and consistency; rules and completeness), as in PROTOCOL.md section 7. The builder may not overrule a checker. Unresolved items go under "Decisions for the maintainer", and you continue.
- Renders in every milestone report:
  - the example tree, the seed closest to the ensemble median, at ages 10, 30 and 60;
  - from M4 onward, also the plot view next to the Gullmarsskogen photo.
  Full meshes only.
- If a session has to end: finish the current step, commit, write the exact next action in CAMPAIGN.md, and stop. The next session resumes from there.

## 10. The reset, 2026-11-06

Where this differs from the sections above, this wins. The aim: a model that matches real life and spreads like a real forest, with more species over time and every aspect of a tree's ageing, for a game. CHANGELOG.md says what changed with it.

- A value with no direct source may be tuned, labelled `TUNED` in the species file with what it was tuned against. Values with a direct source keep it.
- Height may follow the published site-index curves, instead of emerging from carbon.
- One full check at the end replaces a review after every step.
- Targets aren't loosened. Measured and guessed stay marked apart. Standing rules on the node, tree-data, third-party copies, reference photos and keys are unchanged.
