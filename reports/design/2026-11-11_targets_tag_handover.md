# Moving the approved targets tag (V1 hand-over)

The maintainer runs this; no tag was touched by V1. The tag `targets-approved` is a lightweight tag on bb3048c. Run this after `honest-scorecard` is merged into master, from the main checkout, with the master commit that carries the merge in place of the placeholder:

```
git diff cc8c765 <merge commit> -- reference/targets.yaml
git tag -f targets-approved <merge commit>
```

The first command must print nothing: the targets file has not changed on the branch since cc8c765, so the merge commit must carry that same file. This holds whether the branch is merged as it is or rebased first (for example after tools-logging merges); if it prints anything, stop and do not move the tag. If the tag was ever pushed to the backup remote, it also needs `git push -f <remote> targets-approved`. That is the maintainer's call; V1 made no pushes.

What the move approves: `git diff targets-approved cc8c765 -- reference/targets.yaml` is 248 lines added and 15 removed.

## A) Already on master before V1

Made with the maintainer's earlier answers (17 lines added, 15 removed; commits 10fe6bf on 2026-11-08 and a1aa425 on 2026-11-09). Moving the tag approves these too:

1. Q30, `stand_canopy.lai_baltic_chronosequence`. The band's source is now Varik, Aosaar & Uri 2009 (LAI 3.2, 4.4 and 2.5 at 14, 32 and 45 years). The source, doi, citation, page_table and measures changed, the VERIFY comment was replaced, and conditions.text went from 'unthinned / natural self-thinning on fertile abandoned farmland' to 'natural stands on fertile forest land (Oxalis site type), southern Estonia, LAI measured at 14-45 years'. Band 2.5-4.5, ages 6-60, density and mode are unchanged.
2. Q35, a condition change: mode 'natural' was added to `stand_canopy.live_crown_ratio.managed_stand_empirical`, with its measures, a comment and conditions.text. Mode went from [managed] to [natural, managed].
3. Q35, a condition change: mode 'natural' was added to `tree_allometry.foliage_biomass`, with its conditions.text. Mode went from [managed] to [natural, managed]. Both of these rows are INFO, so no PASS or FAIL moves, but they now apply to natural plots where at the tag they did not.
4. Q35, `tree_allometry.critical_turning_moment`: measures now says the coefficient is 'my line through two published averages, not a published regression' (101 kN m per m3). Text only; it is INFO.
5. Q31, `juvenile_establishment.seedling_root_shoot_ratio`: a comment and measures now say the band is worked out from Konopka 2023's equations, not printed there. The band is unchanged.
6. 10fe6bf, `tree_allometry.carbon_fraction`: the citation's pages were corrected from 332-345 to 332-352.

## B) Added by V1

ce44058..cc8c765: 231 lines added, 0 removed; no band, number, unit, age or condition changed. The V1 commits after cc8c765 change no line of the targets file.

1. The header comment defines the kinds (by design, tuned against, seen, out of sample, independent) and the fields kind_reason, values_set, tied_to, stands, band_basis, source_opened (text with a date, or false) and matched. It also says only an independent row can print PASS under the seven-part rule. The scorecard reads source_opened more strictly than that comment says: text that starts with 'not' or 'false' is refused, whatever its case.
2. Every one of the 22 targets has a kind, a kind_reason, values_set, tied_to, stands and band_basis, and some have source_opened, matched or match_note. Kinds: 10 by design, 6 tuned against, 6 seen, 0 independent (22 targets). The ten by-design rows are dominant_height_invariance, site_index_curves, bark_thickness, crown_width_open_grown, wood_basic_density, carbon_fraction, critical_turning_moment, natural_clearcut_heights, field_layer and seedling_root_shoot_ratio. Ties are read both ways, and a tie that can't be read (a tied_to that isn't a list, or names no target) makes every independent row unclean.
3. Four new rows, all `scoring: info`: `stand_canopy.clear_stem_at_first_thinning` (seen, 5-7 m at 13-15 m tall), `stand_canopy.clear_stem_natural_plots` (tuned against), `tree_allometry.branch_biomass_repola` (tuned against) and `tree_allometry.stem_biomass_repola` (seen).

## Tell the maintainer

Two lines of `reports/design/2026-11-11_plan.md` are now wrong:

- line 12 says the header will read '0 of 0, or 1 of 1 at 50 at best';
- line 95 says 'At 50, 1 of 1 if Repola's foliage row applies'.

No target is labelled independent (the foliage row is seen, not independent), so the header reads 0 of 0 at 50 and 60 until a measured stand at those ages, opened at its source, is added as an independent target.
