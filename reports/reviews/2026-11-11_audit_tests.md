Model: Fable 5.2, ID `claude-fable-5-2`

# Audit: do the tests and the release process hold up, 2026-11-11

Independent, read-only review at private master `b84ab90` and public master `d0de191`.

How it was done:
- I read `tests/` (369 test functions, 415 cases in CI), both workflows, `tools/golden.py`, `tools/worker.py`, the publish scripts and the reports in the brief.
- I read CI, tags and releases with read-only `gh` commands, and PyPI and the docs address with plain web requests.
- I ran no model, no pytest and no build. Two small reads: the saved fresh-run ensemble (`node_f5_trees`, 20 stand trees, code `38ce58e`, made on the server), and the publish folder's own scan of the public copy.
- CONFIRMED means I checked it myself. SUSPECTED means I did not.

## Verdict in plain words

1. The tests are good at one thing: proving that two ways of running give the same tree. They are honest and quick (4 to 8 minutes).
2. They do not notice when the tree itself changes. No test and no CI step holds any result at 50 or 60 in place.
3. The look the owner complains about is already measured by the project's own tool, and nothing scores it. About three quarters of a forest tree's leaves sit on shoots that hang.
4. "0.9" is not yet a release. There is no version tag, no GitHub release, no package on PyPI and no live docs site, and the defaults changed twice under the same number.
5. Publishing works, but its scripts are outside version control and the private repository has no second copy.

**Score: 5 out of 10.** The tests alone are about 6. The release process is about 3.

## Three tables

**1. What the only whole-tree test allows** (`tests/test_defaults.py:44-51`; one stand tree, seed 3). Today's values are the fresh run's means.

| Output | Today, age 50 | Today, age 60 | The test passes anywhere in |
|---|---|---|---|
| Height, m | 21.90 | 23.73 | 18.76-25.12 at 50, 20.72-26.73 at 60 |
| Stem, cm (over bark in the report) | 28.0 | 31.3 | 10-45 |
| LAI | 4.73 | 4.60 | 2-7 (approved band 3.6-5.4) |
| Crown ratio | 0.52 | 0.46 | 0.2-0.9 |
| Crown width, m | 5.77 | 6.35 | 1.5-12 |

**2. How much hangs.** Stand trees, 20 seeds, today's defaults, read from the `tools/tree_table.py` snapshots in `node_f5_trees`. "Hanging" is the tool's own rule: a shoot pointing more than 30 degrees below level. Mean (lowest-highest).

| Age | Leaves on hanging shoots | Mean hanging run, m | 90th percentile, m | Longest, m | Hanging runs per tree | Same run's `stats.json` |
|---|---|---|---|---|---|---|
| 30 | 75 % (66-77) | 1.12 | 1.79 | 2.62 | 798 | 0 |
| 50 | 79 % (73-86) | 1.38 | 2.25 | 3.31 | 1,088 | 0 |
| 60 | 77 % (62-85) | 1.38 | 2.43 | 3.51 | 958 | 0 |

**3. One seed on two machines** (`reports/P0_performance.md:119-147`; seed 1 stand tree, the defaults of 2026-11-06; PC / server).

| Age | Height, m | Stem, cm | Leaf area, m² | Diffuse light, % |
|---|---|---|---|---|
| 30 | 19.97 / 19.98 | 18.76 / 18.38 | 46.9 / 46.2 | 45.8 / 40.2 |
| 50 | 25.02 / 25.04 | 26.05 / 27.05 | 66.4 / 63.3 | 30.3 / 31.6 |
| 60 | 26.11 / 26.51 | 28.86 / 29.35 | 65.6 / 65.2 | 29.8 / 30.0 |

At year 17 the same seed carried 10.5 m² of leaf on one machine and 25.3 m² on the other. Over 20 seeds the means agree: LAI 3.30 / 3.09 at 50 and 3.37 / 3.27 at 60.

## What CI does

| Event | Jobs | Python | What runs | Time |
|---|---|---|---|---|
| Push to master, nightly 02:23 UTC, manual | all tests; package x 3; docs only if docs changed | 3.14.7 with the lock; 3.12, 3.13, 3.14 with the newest packages | 414 passed, 1 skipped; wheel built, a 5-year tree grown from it, 17 facade tests | all tests 4m20s to 8m17s; package 0m53s to 1m42s |
| Pull request | quick tests; package x 3 | the same | everything except the 43 listed slow tests and the Unreal export | never run: no pull request exists |

Left out everywhere: the golden runs, Windows, macOS and ARM, the 1 Windows-only test, lint, coverage, tests against the installed wheel, and the docs deploy.

## Findings, most serious first

### T1. No test or CI step pins any model result. High, CONFIRMED, effort M
- Where: `tests/test_defaults.py:44-51`; `tools/golden.py:42`; `.gitignore:14`; `.github/workflows/tests.yml`.
- What: the only whole-tree check at 50 and 60 is table 1. The other growth tests compare two runs with each other or check invariants (pipe sums, radii never shrink, height on the curve). Golden hashes go to the ignored `out/` folder. None is in the repository and no workflow reads one. After the young-roots and crown fix C merges the working log says a new recording was "queued"; I found no logged result.
- Why: a change can move leaf area, stem size or crown shape at 50 and 60 a long way and every test stays green. The published tables then describe a different model and nobody is told.
- Fix: the section "Catching a change to results" below.

### T2. The hanging look is measured, never scored, and lean runs print 0. High, CONFIRMED, effort S then M
- Where: `tools/tree_table.py:234-244`; `treegen/growth.py:3138-3144`, `3162-3165`; `species/betula_pendula.yaml:603-607`, `1839`, `1850`; `reference/targets.yaml` (no entry).
- What: table 2. The values behind it are labelled TUNED "against the look". There is no target, no scorecard row and no test. In lean runs, which every ensemble uses, `stats.json` writes 0 hanging twigs, where other skipped outputs are written as `null`.
- Why: the owner's first complaint cannot get better or worse in any check. A reader of `stats.json` would think nothing hangs. Whether 77 % is too much is UNVERIFIED: I found no measured figure in the repository.
- Fix: write `null` in lean runs, or compute it (one pass). Report the share of leaves on hanging shoots by crown third. Then find a measured band (twig angles traced on the reference photos, or a source opened at the publisher) and make it a target.

### T3. Forests, open-grown trees and the game export are untested at the ages that are used. High, CONFIRMED, effort M
- Where: `tests/test_forest.py:246-261`, `493`; `tests/test_speed.py:208-218`; `tests/test_treegen.py:19`; `tests/test_game_export.py:277`, `441`; `tools/golden.py:45-50`; `species/betula_pendula.yaml:1204`.
- What: no plot in the tests runs past 9 years. Published plots run to 60 with `mortality.enabled`, which is off by default and in none of the golden runs. No open-grown tree on the shipped defaults runs past 18 years (40 with altered crown settings, `tests/test_crown_frame.py:236`). The game export is tested at ages 6 and 8 with small textures. All four golden runs are seed 1, and none is open-grown.
- Why: stems per hectare, basal area and plot LAI at 50 and 60, the open-grown tree, and the meshes the game loads can all break unseen.
- Fix: add to the golden set an open tree to 60, a `tools/forest.py` plot to 30, a second seed and a game export at 30 with the shipped look. Run a 60-year plot nightly on the server.

### R1. One version number covers three sets of results, and no tag or release exists. High, CONFIRMED, effort S
- Where: `pyproject.toml:7`; public commits `6914d25` and `da99e3d`; the public `CHANGELOG.md`, 0.9 section; `gh release list` (empty); five tags, none a version.
- What: the release commit said no default changed. Two later pushes changed defaults (young roots, crown fix C). The version stayed 0.9.0. The changelog lists neither, still calls young roots future work, and says "the package is still `treegen`". `treegen/__init__.py:6` says 0.1.0.
- Why: nobody, the game included, can say which Cambium grew a given tree, or check out "0.9".
- Fix: bump to 0.9.1 at a commit whose tables match its defaults, tag it, and publish a GitHub release. Rule: any change to results bumps the version and gets a changelog line. Keep an "Unreleased" section.

### R2. The privacy scan cannot pass on the pushed copy, and nothing makes it run. High, CONFIRMED, effort S
- Where: the publish folder's `scan.py:56-58`, `92-101`; `sync.py`, which commits without calling the scan.
- What: I ran the scan, read-only: 640 hits, exit 1. All are structural: the remote, and files the sync commits add back (cleaned decision files, README media). No private string turned up in 512 commits and 1,419 blobs against 66 patterns, which is good. The last saved scan output covers 485 commits.
- Why: a real leak would be one line among 640, on a check that always fails. A push to a public repository can't be taken back.
- Fix: teach the scan the published layout so a clean copy exits 0. Make `sync.py` stop on a hit. Add a pre-push hook. Keep each scan's output.

### R3. The private repository has no remote, and the publish scripts are not under version control. High, CONFIRMED, effort S
- Where: `git config --get-regexp '^remote\.'` in the private repository gives nothing; the publish folder has no `.git`; its `overlay/` holds the public README, CHANGELOG and cleaned decision files.
- Why: the full history, the stripping rules and the source of the public README exist on one disk. One failure loses what the public copy is built from.
- Fix: a private remote, pushed after every merge. Put the publish folder in its own private repository. Move `CHANGELOG.md` into the private repository, so it is written with each change.

### X1. A seed is not a portable tree, and three sentences say it is. Medium, CONFIRMED (verdicts flipping is SUSPECTED), effort S then M
- Where: `cambium/__init__.py:14-15`; `treegen/threads.py:6`; public `README.md:35`; against `reports/P0_performance.md:119-147`.
- What: table 3. Same code, same seed: 216 of 225 files differ between the PC and the server. The cause was never separated (chip, Windows against Linux, maths library). I found no recheck on today's defaults, and plots were never compared. CI is a third kind of machine with no recording at all. `docs/site/install.md` is closer to the truth, but "last bits" undersells it.
- What depends on it: every published number comes from the ARM server, so an x86 user can match the means, not a seed. A verdict near a band's edge could flip (Baltic LAI at 50 fails by 0.012; light at 60 is 0.3 under the top). A seed picked for its look must be exported and kept from one machine. Golden hashes belong to their machine.
- Fix: correct the three sentences. Find the first array that differs in year 1 to name the cause. Then decide whether identity across machines is a goal; a later C++ port could only ever be checked statistically.

### C1. Pull requests skip the tests that matter, and master is unprotected. Medium, CONFIRMED, effort S
- Where: `.github/workflows/tests.yml:24`, `37`; `tests/conftest.py:36-38`, `58`; the branch API (`protected: false`); the publish folder's `sync.py`.
- What: the quick job leaves out same-seed identity and the default tree at 50 and 60, to save a few minutes. 6 of 24 runs failed and 4 were cancelled, all on master after the push; the failure I opened was a test kept failing on purpose. `sync.py` overwrites the public tree, so a merged public pull request is undone by the next sync.
- Fix: run everything on pull requests. Protect master with required checks. Mark a known failure `xfail(strict=True)`. Push each sync as a pull request. Write down how a public contribution gets back into the private repository.

### T4. Four tests check the machine, not the code. Medium, CONFIRMED, effort S
- Where: `tests/test_worker.py:31-38`; `tests/test_scorecard.py:12`; `tests/test_species_data.py:257-260`; `docs/site/contributing.md`.
- What: one needs Python 3.14.7 and every locked version exactly, one needs `.python-version`, and two need the `targets-approved` tag. They fail on the server's copy at every run, in a shallow clone or a ZIP, and for anyone who follows the documented `pip install -e ".[test]"`. Because of the first, the full suite cannot pass on 3.12 or 3.13, so those versions get 17 facade tests and a 5-year tree.
- Fix: a `reference_env` marker that skips elsewhere with a reason, and a CI step that fails if one was skipped there. Ship the approved targets as a file whose hash CI checks against the tag.

### C2. CI covers one kind of machine. Medium, CONFIRMED, effort S
- Where: `.github/workflows/tests.yml:25`, `42`, `60`; `pyproject.toml:21-23`.
- What: Ubuntu on x86-64 only. The package claims Windows, Linux and macOS. The reference machine is ARM Linux and the owner's PC is Windows. The one Windows-only test now runs nowhere.
- Fix: add `windows-latest`, `macos-latest` and `ubuntu-24.04-arm` to the package job. Run the full suite nightly on ARM. Add a linter and a coverage figure.

### R4. The install line and the docs address do not work. Medium, CONFIRMED, effort S
- Where: `https://pypi.org/pypi/pycambium/json` (404); the docs address in `pyproject.toml:54` and `CITATION.cff:10` (404; Pages is not switched on, and the one docs run skipped its deploy); private `README.md:14`; `docs/site/index.md:23`; `docs/site/install.md:6-9`.
- What: the public README is honest ("coming soon"). The docs pages and the private README say `pip install pycambium` works.
- Fix: publish to PyPI from CI with trusted publishing, or change the wording. Switch Pages on and rerun the docs workflow. Add a link check.

### T5. Approved targets and shipped targets differ, unguarded. Medium, CONFIRMED, effort S
- Where: `git diff targets-approved master -- reference/targets.yaml` (32 lines, in both repositories); `tools/scorecard.py:47`; the wheel's file list in `pyproject.toml`.
- What: two conditions changed from `[managed]` to `[natural, managed]`, with source text. The scorecard reads the tag; the wheel ships the working copy; no test compares them. Raised on 2026-11-09 and still open.
- Fix: move the tag through the normal approval, or revert. Add a test: the working copy equals the tag, or a tracked note lists what is pending.

### R5. Published tables rest on scripts and outputs that are not in the repository. Medium, CONFIRMED, effort M
- Where: `reports/birch_fresh_run_2026-11-09.md:27`, `44`, `226`; `tools/independent_checks.py`, `tools/carbon_ledger.py`, `tools/v1_workings.py`.
- What: three tables were read by scratch scripts. The run folders sit in an ignored folder. No test names these three tools, which made published numbers (69 of 99 tools are named by no test; most are one-off).
- Fix: move the reading scripts into `tools/`, each with a small fixture test. Attach the ensembles' stats and tree lists (a few MB) to every release.

### T6. Nothing fails when generation gets slower. Medium, CONFIRMED, effort S
- Where: `.github/workflows/tests.yml:37`, `54` (`--durations` only prints); `tools/golden.py:166` (seconds recorded, not tracked).
- Why: the owner calls generation slow. A change that doubles the time passes every check.
- Fix: keep seconds and peak memory for the golden runs in the tracked file. The server's nightly check fails beyond +25 %.

### C3. The package job tests the checkout, not the wheel. Low, CONFIRMED, effort S
- Where: `pytest.ini:2`; `tests/test_cambium.py:42-45`.
- What: `pythonpath = .` puts the checkout first, and the test that asserts "this is a checkout" passes there. The installed wheel gets one 5-year tree with a GLB export. `cambium forest` and the USD export never run from a wheel.
- Fix: run the facade tests from outside the checkout. Add a 5-year forest and a USD export to the smoke step.

### L1. Smaller points. Low, CONFIRMED, effort S
- `requirements.lock` has no hashes and holds `pypdf`, which the model doesn't use. `requirements.txt` lacks `pillow`, which `pyproject.toml` lists.
- `CITATION.cff` has no release date and no DOI. No test checks its version or the README badge.
- `tests/test_profile_run.py:17-33` asserts on sleep timings, so a busy runner can fail it.
- `cancel-in-progress` also cancels runs on master, so some commits get no result.
- The committer's e-mail address and local folder paths are hard-coded in the publish scripts.

## Catching a change to results

1. Track the hashes in git: `cases/golden/server.json`, with seconds, peak memory, library versions and the CPU kernel, and without the host name.
2. Add `tools/golden.py check FILE`. It reruns, compares, exits 1 on any difference, and prints the files that differ with tree60's height, stem, LAI and crown at 30, 50 and 60, before and after.
3. The server's file is the authority, because bits belong to their machine. Check it there on every merge to master. The four runs took 290 s in the P0 report.
4. In CI, first record the set on five nights to learn whether GitHub's machines agree with each other. If they do, track `cases/golden/ci.json` and check it on every push and pull request. If not, check a tracked table of 20-seed means at 30, 50 and 60 instead, failing beyond 3 standard errors.
5. Approval. A change either leaves the tracked file alone, which proves no result moved, or edits it in the same pull request. An edit needs the paired table at 30, 50 and 60 from `tools/gate.py`, a DECISIONS row, a changelog line and a version bump. A CODEOWNERS rule on `cases/golden/` and `reference/targets.yaml` makes the owner's approval a hard requirement.

## A release checklist

1. All four ensembles rerun at the release commit on the reference machine; every table regenerated by tracked tools.
2. The golden file updated in that commit; full tests green in CI and on the server.
3. One version source; `cambium.__version__`, `CITATION.cff` and the badge follow it, and a test checks them.
4. Changelog: "Unreleased" becomes the version, with "results changed: yes or no" and the table at 30, 50 and 60.
5. `targets-approved` equals the shipped targets.
6. The privacy scan exits 0 on the copy to be pushed.
7. An annotated tag `vX.Y.Z` on the public commit.
8. CI builds the sdist and wheel from the tag, runs `twine check`, installs the wheel on three systems, then publishes to PyPI.
9. A GitHub release: notes, the wheel, and the run data as a zip.
10. Docs deployed and links checked.
11. A DOI (Zenodo) and the release date in `CITATION.cff`.

## What is genuinely good

- **Bit-identity tests.** Lean against full, speed settings off and on, a resumed run against a straight one, the same seed twice: whole arrays compared, not samples.
- **`tests/test_speed.py:226-248`** pins the source text that the compiled kernels copy. That is a clever guard.
- **Published numbers as unit tests:** old-age, wind and snow rates and bark thickness against their sources (`tests/test_damage.py`, `tests/test_forest.py:183-204`).
- **The scorecard and the adoption gate are tested,** including "an INFO row is never PASS or FAIL".
- **Provenance.** Every run records its commit, uncommitted changes, machine, threads, library versions and file hashes. Random streams are seeded per subsystem. Nothing is cached between tests.
- **CI is real:** nightly, three Python versions for the wheel, green at 414 passed. The lock, the numba pin and the Python pin are themselves tested.
- **Golden runs were used properly by hand:** 225 files compared at each P0 merge and at the v1 defaults switch.
- **The public history is clean** by the project's own 66 patterns, and the public README says PyPI is "coming soon".

## On the four design tracks

I don't disagree with them. Two requests. Write each track's new check as a reported row and a tracked number before the model is changed. And add the hanging look as a fifth subject: none of the four takes it on, and the branch-wood track only guards it within +10 %.
