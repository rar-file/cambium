# Public repository audit: github.com/rar-file/cambium through a stranger's eyes

Model: Fable 5.2 (`claude-fable-5-2`). Date: 2026-11-11. Read only.

**What I read.** The public copy at its tip `d0de191` (the commit GitHub serves), the live repository through read-only `gh` calls, PyPI's public file lists, and the design files present today (`reports/design/2026-11-11_*.md`: three read, all six searched). I viewed seven of the README's nine pictures.
**What I did not do.** No model run, no tests, no build, no install. Where a point rests on something I did not run, it says so. File paths are in the public copy unless said.

## Verdict

1. The science notes are honest and the engineering is real. Tests pass on GitHub every night, and the wheel is built and run on Python 3.12, 3.13 and 3.14.
2. The public face is not professional yet. It reads as a private lab notebook that went public two days ago, behind a glossy front page.
3. The front page promises more than the project's own reports support, and its pictures show the faults the owner sees.
4. A stranger cannot tell which model "0.9" is. There is no release and no version tag, and the defaults changed three times after the first public commit.
5. Most fixes are small: 16 of the 19 findings are under a day each.

**Score: 4.5 out of 10.**

## The front page against the project's own numbers

From `reports/birch_fresh_run_2026-11-09.md`: 20 forest plots and 20 single stand-grown trees on the shipped defaults.

| What the README says (lines 122-128) | Age 50 | Age 60 | Published | Kind |
|---|---|---|---|---|
| "close": height, plot top height, m | 21.39 | 23.14 | 21.95 / 23.75 (the curve) | By design: the model follows the curve |
| "close": stem wood over Repola (single trees, not forests) | 0.96 | 1.03 | 1.00 | Reported, never scored |
| "close": light under the canopy, % | 18.2 | 19.5 | 6.4-19.8, median 14.8 | Tuned against; 0.3 under the top at 60 |
| "still open": branch wood over Repola | 1.26 | 1.33 | 1.00 | Open |
| "still open": spread of stem diameters, SD over mean | 0.15 | 0.15 | 0.32 at 45 | Open: the forest is too even |
| named for young forests only: Baltic leaf area index | 4.51, fail | 4.29, pass | 2.5-4.5 | Fails at 30 and 50 |

## Findings, most serious first

Each: id (severity, effort, status), then where, what and why, and the fix. S is under a day, M a few days, L weeks.

**P01 (high, S, CONFIRMED). The front page says more than the evidence.**
- Where: `README.md:7, 32, 61, 73, 78, 121-127`; the GitHub description ("checked against real forests").
- What: "Trees that grow themselves", "not presets", "close to the published figures", "young crowns now match real stands". The project's own reports say height is the curve in 1,200 of 1,200 seed-years, crown reach is capped by a formula or by spacing, 92 of 381 labelled values are sourced and 212 are unchecked estimates, and the 5.4 m reading "flatters the model". The validation track (`reports/design/2026-11-11_validation.md`, section 4) lists twelve such lines with corrected wording. I agree with it and do not repeat it.
- Why: a forester who checks one claim and finds it soft stops trusting the rest, and never reaches the honest reports.
- Fix: take the validation track's wording into the public README. Change the description to "compared with". Add to "Still open": hanging strands too long, and no test the model was not tuned on passes yet.

**P02 (high, S, CONFIRMED). `pycambium` is not on PyPI, and nobody holds the name.**
- Where: pypi.org/pypi/pycambium/json returns 404 (today); `docs/site/index.md:23`, `docs/site/install.md:6`, `README.md:116`, `pyproject.toml:6`.
- What: the docs tell people to `pip install pycambium`. It fails. Anyone can register the name and ship their own code to people who follow Cambium's instructions.
- Fix: publish 0.9.x to PyPI now, from a release workflow with trusted publishing. Until then the docs say `pip install .` from a clone.

**P03 (high, S, CONFIRMED). "0.9" is not one model: no release, no version tag, no changelog since launch.**
- Where: no GitHub releases; tags are `birch-v1`, `campaign-*`, `targets-approved`; `pyproject.toml:7`; `CHANGELOG.md:6`; commits `6914d25`, `da99e3d`, `8488d99`.
- What: the species defaults and `treegen/growth.py` changed in three syncs after the "first public release" commit `c3df8f4`. The version stayed 0.9.0 and the changelog has no entry for them. An installed wheel records the version and the species file's hash, not the commit.
- Why: the promise is "same seed, same tree". Two people on "0.9" get different trees and cannot cite which.
- Fix: bump the version with every change to defaults or growth code, tag `v0.9.x`, publish a GitHub release, write the changelog entry. Stamp the commit into the wheel at build time so every manifest carries it.

**P04 (high, M, CONFIRMED). The docs site is not ready to switch on, and its link is dead in four places.**
- Where: rar-file.github.io/cambium returns 404 and Pages is off; `pyproject.toml:54`, `CITATION.cff:10`, `mkdocs.yml:3`, `.github/ISSUE_TEMPLATE/config.yml:4`.
- What: the build passes (`mkdocs build --strict` in CI) and the pages on growing trees, forests and game engines are clear. But: (a) the index and install pages give `pip install pycambium`; (b) `how-real.md` gives birch v1's numbers, not the shipped defaults, and contradicts the README on young crowns and roots; (c) it says some tests "fail on purpose", and none fail now; (d) `mkdocs.yml:6` and `docs/site/contributing.md:60` use branch `main`, the repo has `master`, and the `blob/main/SECURITY.md` link returns 404; (e) `viewer.md` is an empty "coming soon" page in the menu.
- Why: "How real is it" is the page a scientist reads first. It must describe the model they install.
- Fix: build `how-real.md` from the fresh run by script. Fix (a), (c), (d). Drop the viewer page. Then set Pages to "GitHub Actions" and run the docs workflow by hand.

**P05 (high, M, CONFIRMED by viewing). The first pictures show the faults.**
- Where: `docs/media/hero2_a.webp`, `twigs2.webp`, `root_flare_60.webp`, `forest2.webp`, `autumn.webp`, `bark_20.webp`; `reports/renders/look_unreal_ages_whole.png` (`README.md:23, 58, 71, 76`).
- What I saw: the hero birch is a column of strands hanging almost to the grass, with a purple-brown cast. It reads as a weeping willow. The twig close-up is soft and shows flat, angular leaves on long bare strings. The root-flare shot has a dark gap between the stem and its roots. "Inside a birch wood" is an open meadow of poles with tufts on top. The autumn background is a row of equal trees with a flat top. The "Made for games" picture is a debug render on grey ground, labelled 2.2 million triangles. `bark_20` is mostly out-of-focus leaves.
- Why: this is the owner's far too pendulous, used as the headline. `KNOWN_ISSUES.md` measures it (longest strands 5.2 m at 50 and 6.1 m at 60, against about 2-4 m in photos; single strands where real birch has sprays). The README's "Still open" leaves it out.
- Fix: stop leading with a known fault. Re-shoot the root flare once the gap is closed, replace the debug render, and name the hanging strands under "Still open". The cause is model work; see the last section.

**P06 (medium, S, CONFIRMED). Working notes sit at the top level.**
- Where: `PROTOCOL.md`, `DECISIONS.md`, `QUESTIONS.md`, `WORKER.md`, `run_worker.bat`, `cases/`, `reports/claude_audit.md`.
- What: the root has 22 files and 11 folders. Five are rules and logs of the AI-assisted build, in its own words: "the builder", "checkers", "three fresh subagents", "tell the Claude session", "the node", "campaign", "M1", "P0", "the reset", "Cambium-int", "the master log".
- Why: a visitor cannot tell the project from its process. The logs are worth keeping, because they show how each value was decided. They do not belong beside README and LICENSE.
- Fix: move them to `notes/` with a one-page index that explains the words. Keep one short AI policy at the root if wanted.

**P07 (medium, S, CONFIRMED). `KNOWN_ISSUES.md` is not a list of known issues.**
- Where: `KNOWN_ISSUES.md` (2,201 lines, 219 KB); `README.md:130` sends readers there.
- What: it opens with "Phase 31", a diagnosis of moose-browsed leaders. The faults that hold today start at line 2147.
- Fix: a new one-screen file: each open fault, the model's figure at 50 and 60, the real figure, the source. The old file becomes `notes/development_log.md`.

**P08 (medium, S, CONFIRMED). Private workflow files and server details were published.**
- Where: `tools/node/` (35 files, 22 of them one-off queues in `runs/`), `tools/node_*.sh`, `tools/worker.py`, `reports/reviews/2026-11-06_node_disk_*.md` and `_p0_merges_*.md`; `DECISIONS.md:41, 85`; `QUESTIONS.md:107`; `reports/milestone_M2.md:566`; `reports/reviews/2026-11-06_node_disk_rereview.md:96`.
- What: scripts for the owner's batch server. The named lines carry the server's account names, a process id and the run account's home-folder path. I searched the tree for host names, addresses, keys and passwords and found none.
- Why: no use to a stranger, and account names are detail an attacker would otherwise have to guess.
- Fix: add these paths to the publish tool's drop list and the account names and path to its private strings. They stay in the pushed history unless it is rewritten (P09).

**P09 (medium, S, CONFIRMED). Every public commit carries a personal email address.**
- Where: `git log` of the public copy, 512 of 512 commits; the publish tool's sync step sets it.
- What: the author address is a personal webmail address, not GitHub's no-reply one. Commit titles also mislead: `c09e900` is titled as a README change and alters 35 lines of `treegen/growth.py` and the species defaults.
- Why: the address is open to harvesting and cannot be removed without rewriting history.
- Fix: switch the sync step to the account's GitHub no-reply address now. Decide once whether to rewrite the two-day-old history; with 1 star and 0 forks this is the cheapest moment. Name model changes in the sync commit's title.

**P10 (medium, S, CONFIRMED). The repository is heavy, and most of the weight is unused.**
- Where: GitHub reports 141 MB; `docs/media/` 39 MB; `reports/renders/` 24 MB.
- What: ten media files, 35 MB, are referenced by nothing (`growth2`, `turntable2`, `wind`, `seasons2`, `growth_unreal`, `hero`, `forest` `.webp`; `growth`, `turntable`, `seasons` `.gif`). History holds 96 MB of media from 21 README commits in one day. xarray's whole repository is 56 MB.
- Fix: delete the ten files. Keep small stills in the repo and attach videos to the release. If history is rewritten for P09, drop the old media in the same pass.

**P11 (medium, S, CONFIRMED from PyPI's file lists; not run). Install fails on platforms the metadata claims.**
- Where: `pyproject.toml:21-23, 37-39`; `.github/workflows/tests.yml` (Ubuntu only). See the table in the next section.
- Fix: say which platforms work, in the README and the classifiers. Add Windows and macOS to the `package` job. Later, make `usd-core` an optional extra.

**P12 (medium, S, CONFIRMED). The quick start has five slips.**
- Where: `README.md:95-114`.
- What: (a) "Results land in `out/`", but `cambium` writes to `cambium_out/<species>_seed<n>_<open|stand>` (`cambium/cli.py:104`). (b) No word on time or memory. The docs say a 60-year lone birch takes several minutes and a few GB. The "small forest" starts 1,600 trees and, by the project's own timing, takes about half an hour on one core (`reports/cpp_port_plan.md:102-129`; not run here). (c) `tree.stats.to_csv()` with no path writes nothing. (d) Line 95's `&&` is an error in Windows PowerShell 5.1, and cmd.exe passes the `# ...` comments to pip (known shell behaviour; not run). (e) `.python-version` pins 3.14.7, so pyenv users on 3.12 or 3.13 get an error inside the folder.
- Fix: correct the folder, add one line of timings, give `to_csv` a path, put one command per line with no trailing comments, and start with a 25-year tree.

**P13 (medium, S, CONFIRMED). Standard files contradict each other or the repository.**
- `CHANGELOG.md:13-14` says the nine reference photos are not in the repository. They are (`reference/*.jpg`, 8.4 MB), and the README says so. `CHANGELOG.md:8` says "The package is still `treegen`".
- `SECURITY.md:5` names a "latest release". There is none. `SECURITY.md:9-11` relies on private vulnerability reporting, which is off (API: `enabled: false`).
- `CODE_OF_CONDUCT.md:40` gives no private way to report, only a profile link.
- `CITATION.cff`: title and version differ from the README's BibTeX (`README.md:147-154`); `url` is the dead docs link; no `date-released`, no DOI.
- `README.md:129-130` says an independent review is in `reports/`. It is not in the public copy; it is only cited (`reports/birch_fresh_run_2026-11-09.md:3`).
- `.github/ISSUE_TEMPLATE/new_species_or_source.yml:3` uses a label, `species-data`, that the repo does not have. `docs/site/contributing.md:11` says a plain issue is fine; `config.yml:1` turns blank issues off.
- `treegen/__init__.py:6` says version 0.1.0.
- Fix: one editing pass, then a test that checks version strings and links agree.

**P14 (medium, S, CONFIRMED). GitHub settings are mostly at their defaults.** See the settings table.

**P15 (medium, M, CONFIRMED). The wheel installs two top-level packages whose names belong to other PyPI projects.**
- Where: `pyproject.toml:62`; PyPI's `cambium` 1.0.0 (a static site generator) and `treegen` 0.1 (rooted-tree enumeration).
- What: installing pycambium beside either one overwrites files without warning. The engine's scripts are loaded by file path with `sys.modules` swaps (`cambium/_engine.py:44-68`), which the 2026-11-09 review already called fragile.
- Fix: move the engine inside the package (`cambium/engine/`), and make `cli.py` and the two tools real modules. Do it before the first PyPI upload if it can be done in days.

**P16 (low, S, CONFIRMED). Dependencies are stated three ways.** `requirements.txt` lacks pillow. `requirements.lock` has `pypdf` (used by no code), no hashes, and a Windows-only package. `pyproject.toml:13` says the lower bound is NumPy 2.5; line 35 says `numpy>=2.0`. CI never tests the lowest versions. Fix: one source (pyproject), a lock made from it, and a lowest-versions CI job.

**P17 (low, S, CONFIRMED). "Bit for bit" is promised more strongly than the docs allow.** `README.md:114`, `cambium/cli.py:38` and `cambium/__init__.py:14-15` promise the same bits. `docs/site/install.md` says processors can differ in the last bits. Fix: "the same tree on the same machine and library versions" everywhere.

**P18 (low, S, CONFIRMED). The README's four videos live outside the repository.** They are GitHub attachment links (32 MB). They load on github.com for an anonymous visitor (checked). They will not show on PyPI, where `README.md` is the project page and its relative pictures break too. Fix: a short text-first README for PyPI, or absolute links.

**P19 (low, S, CONFIRMED). Docs and tools written for the owner's own setup.** `docs/unreal.md` (482 lines) documents the owner's game's folders and scripts. `tools/` has 144 files; the package uses two. `docs/adding_a_species.md` is outside the site's menu. Fix: fold the general Unreal notes into the site, move the rest to `notes/`, and split `tools/` into `tools/` (supported) and `tools/research/`.

## First run on Windows, macOS and Linux

Each command in the quick start exists with those arguments: `cambium grow` (`--species --seed --years --forest --export glb`), `cambium forest` (`--seed --years`), and in Python `grow`, `height_m`, `dbh_cm`, `stats.to_csv`, `export`. `python cli.py --stand` and `tools/plot.py --save-at` exist as the docs and `SECURITY.md` say. The wheel carries the species, environment and target files (`pyproject.toml:67-74`), and CI proves it by running `cambium grow --export glb` from outside the checkout.

| Platform | `pip install .` | Why |
|---|---|---|
| Linux x86-64 or ARM64 (glibc), Python 3.12-3.14 | Works: CI builds and runs it | |
| Windows x64 | Should work, never run in CI | Wheels exist for every dependency. The pasted first line fails (P12d) |
| macOS, Apple silicon | Should work, never run in CI | Wheels exist |
| macOS, Intel | Fails | numba 0.68.1 and llvmlite 0.50.0 have no Intel macOS wheel |
| Windows on ARM | Fails | usd-core 26.11 has no wheel |
| Alpine Linux (musl) | Fails | numba, llvmlite and usd-core have no musl wheels |
| Python 3.11 or older | pip refuses with a clear message | `requires-python >=3.12,<3.15` |

## GitHub settings

| Setting | Now | A professional project |
|---|---|---|
| Topics | None | 5-8, such as tree-growth-model, forestry, procedural-generation, gltf, unreal-engine |
| Website | Empty | The docs site |
| Releases | None; five internal tags | `v0.9.x` with notes and the wheel |
| Default branch | `master`; three links assume `main` | `main`, or fix the links |
| Pages | Off | On, from the docs workflow |
| Discussions | Off, and blank issues are off | On, for questions |
| Private vulnerability reporting | Off | On: `SECURITY.md` depends on it |
| Secret scanning, push protection | Off | On: free for public repositories |
| Branch protection | None; tests failed on 5 of 20 pushes on launch day | Require the tests check |
| Social preview picture | None | The hero |
| Dependabot | Off | On, for Actions and pip |

## Against three well-run scientific Python projects

Read today through the GitHub API.

| | xarray | pvlib-python | scikit-image | Cambium |
|---|---|---|---|---|
| Default branch | main | main | main | master |
| Website set, topics | Yes, 6 | Yes, 5 | Yes, 3 | No, 0 |
| Latest release | v2026.09.0 | v0.16.1 | v0.26.0 | None |
| Working logs at the root | None (`design_notes/`) | None | None | 5 files |
| Docs | `doc/`, hosted | `docs/`, hosted | `doc/`, hosted | `docs/site`, not hosted |
| Repository size, MB | 56 | 119 | 84 | 141 |

xarray keeps AI rules at its root too (`AGENTS.md`, `AI_POLICY.md`): short files a contributor can use. That is the model for `PROTOCOL.md`.

**What to remove, rename or rewrite, in order.**
1. Settings, minutes: vulnerability reporting, secret scanning, push protection, topics; the no-reply address in the sync step (P09, P14).
2. Rewrite the README's claims, quick start and "Still open", and the description (P01, P12).
3. Release: version bump, tag, changelog entries, GitHub release, PyPI upload (P02, P03).
4. Remove: ten unused media files, `tools/node/` and the node and worker helpers, `run_worker.bat`, `WORKER.md`, `reports/claude_audit.md`, the node and merge reviews, `pypdf` (P08, P10, P16).
5. Rename: working notes into `notes/`; old `KNOWN_ISSUES.md` to `notes/development_log.md` with a new short one; `master` to `main` (P06, P07).
6. Rewrite the docs pages and the standard files, then switch Pages on and set the website (P04, P13).
7. Re-shoot the hero, root flare, forest and games pictures (P05).
8. Restructure: engine inside `cambium`, `usd-core` optional, CI on Windows and macOS (P11, P15).
9. Decide on a history rewrite: address, old media, server details (P08-P10).

## What is genuinely good

- **CI is real.** Nightly full tests are green. The wheel is built, installed and run on three Python versions from outside the checkout.
- **The Status paragraph is honest.** It names open faults and says height is by design. Few projects do.
- **Captions say what is model output** and what is scenery or a shader effect.
- **The labels.** Every labelled value says sourced, derived, tuned or unchecked, and `cambium species` prints the counts.
- **The community files exist and are thoughtful.** Issue forms ask for the seed, command and version, and for sources at the publisher. The pull request template asks for results at 50 and 60.
- **The secret scan was clean:** no host name, address, key or password in the tree.
- **The reference photos are credited** one by one, with licence and source.
- **The docs pages are clear and complete** for a small interface, and the build passes in strict mode.

## On the four design tracks

I do not disagree with any of them. Two notes from the public side.
1. None of the six design files present today takes on the look the owner named first. I searched them all: "hanging" appears once, as a "must not break" row. The strands need their own measured target, because they are what every visitor sees first (P05).
2. The validation track's corrected wording must land in the publish tool's public README, and both the README and `how-real.md` should be built from the same fresh-run numbers. Today three public pages give three different accounts of the young crowns.

## Not checked

Installs on Windows and macOS (read from wheel lists only). The videos' content (only that they load). `bark_06.webp` and `bark_60.webp`. `CITATION.cff` against a validator. The Unreal notes.
