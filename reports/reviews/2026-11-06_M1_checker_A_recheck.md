Checker A's recheck, saved as it stands.

# Checker A recheck at `3c6bde7`

**Ruling: yes, the tag may move now.** All five tag items are done, and the new wording agrees with the sources. What's left is listed under "Doesn't hold the tag".

`targets.yaml` is identical at `881b5c0` and `3c6bde7`, and the tag is still at `41d18c1`. I edited nothing in the repo, ran no model and used no SSH.

## 1. `reference/targets.yaml`

A key-by-key comparison with the tag shows the only non-text changes are `target_mean` 4.59 to 4.5, `age_years` on the two Hagemeier items, and T13 replacing the 4 years. No `target_range`, `stand_range` or `range` value changed. In M1 section 2, all 208 rows have the same mean, SD, seeds, status and share as at `f45928e`, so these edits moved no verdict.

| Item | New wording | Source | Result |
|---|---|---|---|
| "Values above 20%" sentence | Gone; now "mature stands with a closed canopy (canopy closure > 0.9, Forests 10:265 p. 3), aged 45 and 67 (Table 3 there; Table 2 of Forests 10:925)" | 10:265 p. 3 "The stands had a closed canopy (canopy closure > 0.9)"; Table 3 ages 45, 67; 925 per the maintainer's reading | OK |
| "(Model-derived 12.6% removed)" | Gone | Not source text | OK |
| `var=0.063` | "residual variance 0.044, between-stand variance 0.0108, Table A1" | Repola p. 623: e6ki 0.044, u6k 0.0108 | OK |
| Repola `measures` and `text` (old 88, 93, 204) | "24 stands", unthinned and heavily thinned plots, three on peatlands | p. 607 "Three stands were on peatlands"; p. 608 "Unthinned and heavily thinned plots" | OK |
| "no stand age given" (old 89) | "stand age 11-97 years (Table 1)" | Table 1, p. 607: T 11 to 97 | OK |
| Niemisto title (old 98) | Longer title, DOI unchanged | Crossref title ends "(Betula pendula)" | Usable; see item 5 below |
| `dense_unmanaged_stand.measures` (old 100) | "0.29 is the minimum across all sample trees"; Niemisto marked unopened and unchecked | Repola Table 2: 0.29-0.96 | OK |
| Aosaar off the LAI band (old 23) | Removed | No hits for "LAI" or "leaf area" in the paper | OK |
| `sis_reading` | Cites pp. 9-10 and quotes "Pend. birch: Pub. birch function with SI = H100pine + 1.5" | Quote verbatim, p. 9 | OK; see item 6 below |

`mode: [managed]` is unchanged and goes to the maintainer in Q13.

## 2. `DECISIONS.md`: OK

- **Row 38** now reads "4.59 at the tag, 4.5 now".
- **Row 46** names the page and citation edits and points to M1 section 5 for the rest. "No band changed by these" agrees with my comparison.

## 3. `reports/milestone_M1.md`

**Section 5: OK, except one row (item 2 below).** Every other changed key has a row, and the closing statement on ranges agrees with my comparison.

**M1b: OK.** Line 342's widths (+0.31, +0.34, +0.30, +0.24, +0.19 m) agree with my recalculation, and it now says the band is stricter at the top edge and looser at the bottom.

**Section 1:** I recomputed the figures from saved outputs.

| Claim | Age 50 | Age 60 | Result |
|---|---|---|---|
| Stand tree over the height band | 25.286 against 25.124: 0.16 m | 27.069 against 26.733: 0.34 m | Right |
| Stand tree over the light band | 30.14 against 19.8: 10.3 points | 27.51 against 19.8: 7.7 points | Right |
| Plots over, on the curve | 28.88 against 25.12: 3.8 m | 30.59 against 26.73: 3.9 m | Right |
| Plots over, those trees' mean height | 27.92: 2.8 m | 29.41: 2.7 m | Right |
| Plots over the light band | 22.32: 2.5 points | 22.29: 2.5 points | Right |
| Plots' mean tree "inside the band" | 21.85 in 18.76-25.12 | 22.80 in 20.72-26.73 | Numbers right, but see item 3 below |

The tag margins at 40 and 50 (0.003 m and 0.03 m) are also right.

## 4. `reports/parameter_checks.csv`

- **Line 16: OK.** It now says r 0.94.
- **Line 52: OK.** It now carries the "Model value" note. Its status is still "sourced", while rows 46-51 say "borrowed"; the labelling rule is met, so that can stay.
- **Line 71: not right yet (item 4 below).**
- **Lines 5 and 9: they block nothing.** The scorecard reads neither, and their values and pages are right. Update them, and the same notes in `parameter_audit.csv`, at the next edit.

## Doesn't hold the tag

**Report edits, which can be made at any time:**
1. **Q15's "marked unread" isn't true of the LAI band.** `lai_baltic_chronosequence` (`targets.yaml:21-27`) has no such mark, and it still cites Uri's pp. 119 and 122 with no VERIFY. Varik 2015 is unopened too and isn't in Q15. This target is a scored PASS at all five ages, so the maintainer should get this right.
2. **One "before" in M1 section 5 is wrong.** The row naming `parameters` says "Eriksson's own parameter and age wording". The tag actually said "Model values from the R package forester... not yet checked against the paper's table", and `parameters` didn't change.
3. **M1 section 1's "the plots' mean tree is inside the band".** The target measures dominant height (`height_measure`), so a mean tree isn't its measure. Add a clause saying so, or the maintainer could read it as a partial pass.
4. **Line 71 still overstates the Brouwer reading.** The saved images are PDF pp. 33-37. PDF 33-35 are printed 37-39, the last three of the article's nine pages, and PDF 36 is printed 41, van Dobben's article. So "PDF pp. 33-36" includes another paper, and "all pages of the article as saved" reads as more than three pages. Those pages give no carbon share or ceiling, so the row's "no" stands; I can't show "water shortage favours roots" from them.

**Text in `targets.yaml`, for the next target change under rule a:**

5. **The Niemisto citation leaves off "(Betula pendula)".** This was my slip: my report shortened the title and the edit copied it. M1 section 5's "the paper's full title" is therefore slightly off. The DOI identifies the paper.
6. **`sis_reading`'s "pp. 9-10 put birch on the H100 pine scale".** Those pages are about "Functions for mean height development in young stands" (Section 2.2). Add that limit.
7. **The unread mark on `lai_baltic_chronosequence`** from item 1.

## After the move

- Add a DECISIONS.md row for the tag move.
- Update the rows waiting on me: 20, 29, 38, 39, 44 and 46.
- Rerun the scorecard on the saved outputs so section 2's headers name the approved tag.

**Limit on this ruling:** the light target is still checked against the maintainer's reading, not the paper, because the publisher returned HTTP 403 and I didn't retry.

The tag may move to `reference/targets.yaml` at `3c6bde7`.
