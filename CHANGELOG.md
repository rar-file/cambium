# Changelog

Newest first. Dates are when the work landed on `master`. Decision numbers refer to `DECISIONS.md`; the reports
named are in `reports/`. Known faults are listed in `KNOWN_ISSUES.md`.

## 0.9 (2026-11-09): first public release

- **Published as Cambium**, under the Apache License 2.0 (`LICENSE`, `NOTICE`). The package is still `treegen`.
- **History kept, cleaned.** Private details, third-party photos and the working night logs were removed from every
  commit. The night logs are replaced by this changelog; `DECISIONS.md`, `QUESTIONS.md` and `PROTOCOL.md` appear
  at this release in cleaned form. Commits that only touched the removed files were dropped, so tags that pointed at
  one now point at the commit before it.
- **Reference photos left out for now.** The nine openly licensed Wikimedia Commons photos used for comparison
  while building aren't in the repository; they stay credited in `reference/CREDITS.md` and may be re-added
  (`reference/PHOTOS.md`). The stem tracer's built-in example is now a drawing.
- **Server scripts are generic:** `tools/node/` reads the server, account and key from `CAMBIUM_NODE_HOST`,
  `CAMBIUM_NODE_USER` and `CAMBIUM_NODE_KEY` (`tools/node/README.md`). The Unreal test reads the game's folder,
  process name and variable prefix from `CAMBIUM_GAME_DIR`, `CAMBIUM_GAME_PROCESS` and `CAMBIUM_GAME_ENV_PREFIX`.
- **After birch v1 (decision 99):** root strength is read unrounded (`anchorage.moments_unrounded`, on), so small
  trees' uprooting no longer depends on 0.01 kNm rounding. A floor of two collar roots for small stumps
  (`roots.paid.collar_roots_min`) is in the code, off by default: it made the collar sum worse.
- **Next, for 1.0:** young birch fixed (crowns that lift as the canopy closes, young roots, early deaths), and tests
  against published data the model was never tuned on.

## Birch v1 (2026-11-09, tag `birch-v1`)

The reset's one full check, with three independent reviews (`reports/birch_v1_final.md`,
`reports/reviews/2026-11-08_final_check_a_sources.md`, `2026-11-09_final_check_b_numbers.md`,
`2026-11-09_final_check_c_rules.md`).

- **New defaults (d5f0ea3, decision 93):** the 52 settings of `cases/crown2_with_roots_speed.txt` and two forest
  changes became the species defaults (48 values changed). The golden runs before and after are identical, 225 files.
  On by default since:
  - the crown frame: limbs earn their reach and place by their leaf area against the limbs around them;
  - the height driver: the leader grows up to the Eriksson 1997 site-index curve (SI 23);
  - damage: old age (Elfving 2010), wind (Kitenberga 2021) and snow, plus moose browsing of the leader;
  - roots that cost carbon (`roots.paid`): fine roots and root wood paid from the root share;
  - plot heights follow the dominants' vigour, and slow dominants aren't counted as suppressed (Maleki & Kiviste
    2016; decision 94).
- **Look:** bark that ages from red-brown to white to a black, fissured base, peeling and lenticels; leaves on
  shoots; autumn colour; limb atlas. About half the look's tuned values were set by eye on renders.
- **Game export:** `tools/game_export.py export --target unreal` writes what an Unreal project's import scripts
  read, with levels of detail, wind data in vertex colours and the model's own roots (`docs/unreal.md`).
- **Forests:** `tools/forest.py` grows plots with self-thinning (sdi_max 763, TUNED), seed rain and regeneration.
- **Results at 50 and 60 (forest-grown trees, 20 seeds):** height 21.9 and 23.7 m (by design), leaf area index 4.82
  and 4.68, light under the canopy 16.2 and 16.4 % (both tuned), stem wood 229 and 335 kg against Repola's 237 and
  316 kg.
- **Known faults at v1:** no independent check passes at 50-60; young crowns reach almost to the ground (crown ratio
  0.92-0.96 at 11-22, real 0.30-0.45); young leaf cover is outside the Baltic band in 46 of 55 years; young roots
  are too sparse; young trees don't die early; small trees' uprooting depended on rounding (fixed in 0.9).

## The reset (2026-11-06 to 2026-11-08)

The campaign's rules and the model's unsourced values blocked each other: by the end of M2 no default had changed.
The reset (decision 85, `PROTOCOL.md` section 10) changed how the work is done:

- A value with no direct source may be tuned, labelled `TUNED` with what it was tuned against; values worked out from
  a source are labelled `DERIVED`; values with a direct source keep it.
- Height may follow the published site-index curves instead of emerging from carbon.
- One full check at the end replaces a review after every step.
- Targets are never loosened.

New scope: forests that spread, more species over time (`species/_template.yaml`, `docs/adding_a_species.md`),
fitness for a game, and bark and opacity ageing. Every tree is its own tree, near or far, and can be felled and cut
(decision 91); `reports/cpp_port_plan.md` plans a later C++ port and measures what a tree-year costs. Choices
between candidates go by measured numbers first, then real photos, not by taste (decision 92). Batch runs moved to
a server, queued through `tools/node/` (decision 89).

## M2: calibration attempted (2026-11-06, tag `campaign-M2-done`)

- Height and leaf area were fitted together, never height alone. No value of alpha fits both, so nothing was
  adopted: alpha stays 4.8 (VERIFY), and fertility and season were parked (`reports/milestone_M2.md`).
- Found: fresh laterals' leaves weren't charged (a switch, off by default); the model's light extinction sits below
  its input; plots barely thinned; the Baltic leaf-area band's papers print no leaf area (`KNOWN_ISSUES.md`).
- Target text corrected in checker A's words; the `targets-approved` tag moved with it (decisions 77-81).

## M1 and P0: foundations and speed (2026-11-06, tag `campaign-M1-done`)

- **Verdicts from ensembles:** 20 trees or 5 plots on one machine, the ensemble mean against the target band, with
  the spread and the share of seeds inside; an effect counts only if the paired difference is over 2 standard
  errors (`reports/milestone_M1.md`, `reports/rebaseline_M1.md`).
- **One maths-library thread per run** as the standard, so results don't depend on the machine's thread count.
- **Scorecard:** reads the targets' condition labels; plot top height by Elfving 2010's definition on a Naslund
  curve; light also shown as the distance from the paper's median.
- **Light target** read from Hagemeier & Leuschner 2019b at the publisher: 6.4-19.8 %, median 14.8 %.
- **Parameter audit:** 274 values, 71 checked against their page, 15 not supported by it
  (`reports/parameter_audit.csv`); a sensitivity screen of 160 values.
- **P0, performance:** lossless speed-ups only, every one checked against golden runs: about 4.9 times the
  throughput, lean runs, a result cache, plots with no save files (`reports/P0_performance.md`).

## Campaign start (2026-11-05, tag `campaign-start`)

- Working rules for a campaign towards birch v1: memory rules, campaign mode, the adoption gate and pre-approved
  target corrections (`PROTOCOL.md` sections 6 and 9).

## Phases 17-40 (2026-11-01 to 2026-11-02)

Development before the campaign, a phase at a time; `KNOWN_ISSUES.md` has a section for each.

- **17-19:** stem gravitropism refitted; speed (one shared soil per plot, compiled tree passes); seedlings on stones,
  death after two years without carbon, regeneration (first version).
- **20-25:** leaves and fine roots cost carbon; water taken up through the fine roots the tree pays for; the field
  layer; one carbon pool for shoots and rings (LIGNUM); wood per leaf area fitted to Nordic birch.
- **26-31:** natural plots with turnover; sapwood, taper and bark diagnosed; Huber value by path length (off); a
  continuous replacement leader; a snow-buckling check; the wind rule.
- **32-33:** citations re-verified; moose browsing; woody shade on by default; young growth against Swedish site
  curves.
- **34-38:** the light-under-canopy target set to the measured 6.4-19.8 %; the dense-stand crown-ratio target limited
  to ages 11-22; stem theory stage b on by default.
- **39-40:** the published Borchert-Honda allocation tested; run outputs with light at the target's height and a run
  manifest; soil water reworked to published formulations (off).
- **Scorecard repaired** (2026-11-02): every target read from `reference/targets.yaml` at the `targets-approved` tag,
  with no invented values or tolerances.
