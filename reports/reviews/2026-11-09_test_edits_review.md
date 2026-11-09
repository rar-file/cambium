# Review of test changes on reset-integration since 359bea4

On 2026-11-09 a fresh reviewer read the full diff of `tests/`: 10 files, commits 9b866ec, f88b4b9, b01cf56, 8aea202, 0556861 and 64b3fc2. It made no edits and ran no pytest.

**Result: 28 items (23 changed tests, 2 helpers, 3 new tests). 27 OK, 0 loosened, 1 ASK.**

Kinds of change:
- Tests now set the old default explicitly where they test the off path.
- Default assertions now assert v1's values.
- Floating-point tolerance is 1e-9 degrees (12° round trip).
- The thin/thick line moved from 1 cm to 5 mm. The scale moved; the rule `branch * min(thick/r, 1)` is unchanged.
- The old-age assertion was replaced by Elfving's formula at four ages, which is stronger.
- Tests needing dead trees or seed set grow the old model (BEFORE_V1, all 48 old values) or switch the height curve off as setup.
- The export test only gained checks.
- There are no skips or xfails, and the pytest settings are untouched.

**The ASK (row 15): test_roots_paid::test_with_carbon_to_spare_the_collar_sums_to_the_stump.**
- It now switches the height curve off, so it no longer checks the shipped model.
- On v1's defaults the collar sums to 0.69, against a 0.70 floor.
- **Builder's response:** a new test, `test_on_the_v1_defaults_the_collar_sums_to_the_stump`, checks the same rule on the shipped defaults. It's kept failing on purpose (DECISIONS 98), not skipped.

**Coverage gap, not loosening:** after test_root_pipes_continue_the_stem moved to paid roots off, nothing checks root pipe sums at junctions with paid roots on, which is now the default. Logged for after v1.
