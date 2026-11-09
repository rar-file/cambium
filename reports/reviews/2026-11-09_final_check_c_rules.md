# Final check (c): rules and completeness, on reports/birch_v1_final.md at 8fd4fdb

A fresh checker (PROTOCOL 7c) ran on 2026-11-09 and made no edits. Count: 15 FIX, 2 ASK MAINTAINER, 6 OK. Its findings are below, condensed, with every item kept.

## Builder's response

All 15 FIX items are accepted:
- Report wording (items 1, 8-15) is fixed in birch_v1_final.md.
- Workings: a script recomputes the hand-worked numbers, and its output is saved (item 2).
- A completeness section covers spread, bark, branch fall, species, export and memory (item 3).
- KNOWN_ISSUES.md gets a birch v1 section with the corrections (item 4).
- DECISIONS rows 93 onwards log the adoptions (item 5).
- The test edits get a separate review, the 4 environment tests run in a real clone, and golden is re-proved after the last merge (item 6).
- docs/unreal.md and cpp_port_plan.md are brought in line with row 91 (item 7).

The ASK MAINTAINER items: 16 is added to Q37, 17 becomes Q38.

## FIX

1. **Leaf size is wrong in the report.** With sun and shade leaves on, size is 0.0015 × 60.8/LMA, so 10.2-18.1 cm² (growth.py:1414-1426). The steady 15.00 is a stats artefact (3116-3117). Measured means were 17-17.8 cm², so the gap to 11.9 is probably bigger. This started at checker (b)'s item 19.
2. **Hand-worked verdicts with no saved workings, and template sections missing.** The plot top-height PASS, the young crown-ratio FAIL, the paired ± figures, "46 of 55", k and "LAI 5.1" have no script or output saved. Missing sections: a summary of 5 lines or fewer, answers, changes made, checker results, corrections, decisions.
3. **The reset isn't answered in full.** Missing:
   - forest spread (575 m by 45, far_share 0.005 → 0.003 after the plots, storm gaps that don't refill: 3 of 373);
   - bark and ageing (stages, fissures, thickness, peeling, black base, autumn);
   - branches landing on the ground (row 91);
   - more species (427 settings not in the schema, plots single-species, pine and spruce dominate the game area);
   - the game export (tested in a separate project; fails on v1, being fixed; do real roots reach it, row 88?);
   - live growth memory (38-43 MB per tree, about 140 trees per GB, against 4,222 birches in reach).
4. **KNOWN_ISSUES.md stops at M2.**
   - Nothing on the reset or v1.
   - Missing corrections: open width reported as a check; the 5.2 m crown base; foliage figures withdrawn at 19:40; the old-age misread at 03:30; the shared weather stream (ae1a2e1); Q30's "near the band".
   - Stale lines remain: 1,480-1,660 stems/ha, and growth.py:1325.
5. **Adoptions not in DECISIONS.md (rows end at 92):** the d5f0ea3 defaults switch; the forest fixes adopted on 3 plots; H kept over J; the server-only handover; the targets.yaml citation edit without moving the tag.
6. **Tests.**
   - Say that the 4 environment failures include the approved-tag and scorecard tests, last passed on the PC at ae1a2e1.
   - final-fixes-b edits existing tests. tests/ is fixed and never loosened, so list the edits and have them confirmed.
   - final-fixes-b edits game_unreal.py, so golden needs re-proving after the merge.
   - The three checks ran on three versions.
7. **DECISIONS 91 not honoured in docs:** docs/unreal.md:245 (stages from a library) and cpp_port_plan.md:455 ("the shared far look").
8. **Double tops:** the end-bud rule applies only to axes finer than the stem (growth.py:995-1001). Second tops are drawn at Zeltins' 0.349 (2052-2053) and through reiteration, so the cause is unknown. "Zeltins, unopened" contradicts labels.yaml:444/448 and log 02:49.
9. **Browsing:** leader browsing (leader_damage) is on by default; only twigs_browsed is 0.
10. **"Mortality only acts on trees past 1.3 m"** doesn't match the code. Self-thinning and background death apply with no diameter; only "suppressed" needs one. Self-thinning can't start until stems past 1.3 m make the stand dense.
11. **Height "less when short of light, water or carbon":** Test A found the curve held height in 1,200 of 1,200 seed-years. Say how often, or call it close to scripted.
12. **Look values by taste:** about 29 of 58 TUNED look lines say "by eye", 10 cite photos; leaves.yellow_lift is set for the maintainer's autumn yellow. Say most look values were set by eye on renders.
13. **Open trees:** spare carbon goes to the stem only up to 2.4 cm per m of height. Stand trees have a leaf cap too (crown_lai_max 7). The Hemery cap holds at a stem of at most 2.4 cm × height. In stands, reach also stops at 1.15 × half the spacing.
14. **"The final settings became the defaults":** mortality.enabled is false; tools/forest.py switches on self-thinning, natural start and regeneration. Say forests depend on those.
15. **Minor.**
    - The old-forest sources are abstract-only and unchecked.
    - "Its FIX items are fixed" overstates finding 3: the birch-data PDF can't be fixed, and "fixed" is a restricted word.
    - The render paths are relative, live only in a worktree, and are at d9d4ce1. Copy them to reports/renders.

## ASK MAINTAINER

16. **H against J by row 92.** J is closer on basal area (23.1 / 25.2 against real 25.2 / 28.5), Dg at 60, and crown ratio at 30 (0.62 against Repola's 0.58; H 0.69). H is better only on young LAI. Light is noise and the photos are split. Q37 should list all of these.
17. **Node use beyond "submit/status/fetch":**
    - cancel.sh;
    - mem_guard.sh (kills origin's biggest job under 14 GB free);
    - clearing stale locks;
    - deletions logged;
    - 21 of 16 cores at the maintainer's request;
    - one memory breach (7 GB against the 8 GB floor);
    - jobs now overlap, where row 89 said one at a time.
    The maintainer should confirm.

## OK

18. TUNED labels all say what they were tuned against. No value with a direct source was retuned. (mortality.vigour is tuned against model behaviour.)
19. Targets not loosened: one citation page range only; tests/ only additions on reset-integration; PROTOCOL changed only in f659fc5.
20. Height from the curves: on at SI 23, marked by design.
21. The limb curve set-point moves with wood age. The load bend still applies, so "not from mechanics" is slightly strong.
22. The old-age path in thinning is zeroed with damage's old age on.
23. Standing rules: tree-data only read by a pre-reset tool; no keys; no photos in out/; nothing heavy on the PC after 16:35.

**Not done:** the test edits, recomputing numbers, opening sources, the game untouched, every look provenance line.
