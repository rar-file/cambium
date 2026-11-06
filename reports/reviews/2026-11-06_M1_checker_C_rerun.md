Checker C's re-ruling, saved as it stands.

# Checker C, re-ruling at `3c6bde7`

Read-only, no SSH. `tests/test_scorecard_targets.py` and `tests/test_gate.py`: 27 passed. Tree clean.

| # | Item | Ruling |
|---|---|---|
| 1 | Test edit | **OK. Yes, now no looser** |
| 2 | Gate INFO test | **OK** |
| 3 | M1 report | **FIX**, 4 small; the rest OK |
| 4 | CAMPAIGN.md "Now" | **FIX**, 3 small |

## 1. The test edit: yes, no looser

The edit in `8ecfca3`, together with `test_height_band_at_60_is_pinned`, is now no looser than what it replaced. Row 22's condition is met. The maintainer's acceptance now stands, apart from Q12, which is a separate matter.

- **The saved mutation result holds.** I reran `mut.py`, and its output is line for line `out/bench/m1/test_edit_mutation.txt`: numerator 150 passes the pin, 75 and 300 fail it.
- **`pinned()` checks only the band's text, so I went wider, with the full pin** (text and all four edge checks; `<scratchpad>\mut2.py`, in memory only). Each of these fails the pin, and the unchanged file passes:
  - numerator 140 or 160
  - SIS age 80 or 120
  - site-index range 19-26 or 20-27
  - reference age 45
  - beta 380
  - going back to a fixed 4 years
- **The original test is otherwise intact.** Since `8ecfca3`, the only line removed from this file is one import, widened.
- **It's stricter than the old test in one way.** There is now a FAIL below the low edge (20.60 m); the old test had none.
- **`test_plot_top_height_scored_on_elfvings_curve`: OK.** It goes through `evaluate_targets` at the definition in targets.yaml, and checks both the "Naslund curve" note and the value on the curve.

**Wording only, no effect on the ruling:** the pin's docstring says the old test "pinned neither low edge". The old text check did pin the low edge's number, through `lo` at 56.0. What it lacked was a FAIL below that edge.

Row 22 already read "no looser, with the pin" before this ruling; it now has this ruling behind it.

## 2. Gate INFO test: OK

`test_info_rows_are_left_out` exercises the filter at `tools/gate.py:100`. With that filter removed in memory, `per_seed` returns `a` and `b` instead of only `b`, so the test would fail. The unpaired half stays replaced by `test_a_target_scored_on_one_side_only_stops_it`. Q12 remains the maintainer's.

## 3. `reports/milestone_M1.md`

**OK:**
- "Not done:" in M1c.
- "Answer:" opens all 9 task sections, including the new re-baseline and top-height ones.
- The ranking table has height and LAI at 50 and 60; I spot-checked 3 rows against `out/bench/m1/figures.txt`.
- 11 + 4 is explained.
- Section 4's "Tests" sentence is accurate, and the missing commits are there.
- Section 5's title; section 8's table of Q11-Q15 (options in QUESTIONS.md).
- The other line references: `growth.py:807`, `:943`, `:979`, `:1593-1599`, `plot.py:108-109`, `:202-203`, `:1450-1451`.
- "fully" and "confirmed" are gone. "Solved" at line 325 is arithmetic, so it's fine.

**FIX:**
1. **Line 288:** `treegen/growth.py:1469-1471` still points at where the exponent is read. The switch-off is at `:1477-1478` (`if stage >= 1: b = c = 0.0`).
2. **Line 482:** "Light target's text matches the source" is the last restricted word. Use "follows".
3. **Section 6:** "Moved after checker A's recheck: see DECISIONS.md, the row for the tag" is past tense, but the tag is still `41d18c1`, no such row exists, and `campaign-M1-done` doesn't exist yet. Reword it until the move happens.
4. **Line 3** says Code `68782d9`, while the line references are at master; the `plot.py` ones differ between the two. Add a clause saying so.

## 4. CAMPAIGN.md "Now"

A cold resume now goes to the right steps; these three lines could still mislead.

**FIX:**
1. **"Current step"** still says "the three checkers are running". "Exact next action" and Status say they've reported.
2. **"Then, in order", item 3** says the same.
3. **Item 6 and action (2):** item 6 says the node's golden runs at `f45928e` are "recording", and action (2) goes straight to reading the sweep.
   - I found no saved result at that commit. The only `out/bench/node/golden_compare.log` is from 02:20.
   - The sweep's baseline is at `68782d9`, so action (2) should say: confirm the golden runs equal `node_a` before reading it.
