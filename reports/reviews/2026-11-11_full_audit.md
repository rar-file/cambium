Model: Fable 5.2 (claude-fable-5-2)

# Full audit of Cambium, 2026-11-11

Lead review. Eight areas were each reviewed by Fable 5.2 (`claude-fable-5-2`) and checked by `claude-opus-5-5`. This file joins them into one list. Private master at `ce44058`, public copy at `d0de191`. Read only: no growth, tests, renders or builds. This is the only file I wrote.

Marks: **C** the verifier confirmed it. **P** partly true, the verifier trimmed it. **V** found by the verifier, not the reviewer. **R** the reviewer's claim, with no second check. **L** I checked it myself today.

## Verdict

1. The owner is right on all three counts. The trees hang too much, generation is slow, and the project is not professional yet.
2. The hang is written in, not grown. One setting, chosen by eye, makes every twig soft until it is 24 mm thick and stops it steering. Nothing measures the result, and none of the four design tracks owns it.
3. Slow is three separate things: light for a single tree, plain Python for a forest, textures for an export. A stand tree grows to 60 in about a minute, but seeing it at four ages takes six.
4. This is an honest research model, not yet a product. No test holds any result in place, "0.9" is not a real release, the install name is unclaimed, and the front page says more than the evidence and leads with the hanging tree.
5. As a game asset it is unproven. No real-time frame has ever been timed, and the rule "every tree its own, near and far, cuttable" cannot be met with what is built.
6. What is good is real: honest labels, runs that repeat on one machine, green nightly tests, no secret in public, and an exact export. **Overall: 4.5 out of 10.**

## Scores

| Area | Score | Why |
|---|---|---|
| Does it look like a real silver birch | 4 | Hang set by rule and by eye; young trees read as poles or larches; limbs thin and straight. Stand trees at 60 and close-up bark are good |
| Generation speed and memory | 5 | Measured professionally, but still 1-2 minutes a tree and 50-55 minutes a forest, and a tested 1.5x sits unused |
| The rest of the science | 5 | Sound mechanisms and honest labels; old forests are not sound, water is idle, nothing is screened on today's model |
| Code quality | 5 | Works and repeats; one class of 3,113 lines, about 80 switches, silent fallbacks, the hot rules written twice |
| Tests, CI, reproducibility | 5 | Good identity tests and green CI; no result is pinned, the private repo has no automated tests, no real release |
| The public repository | 4.5 | Honest notes behind a front page that over-claims and shows the faults; no release, dead docs link |
| Security and privacy | 6 | No secret is public; the leak guard cannot pass and only knows strings it was given; the install name is free to take |
| Export and game readiness | 4 | The single-tree export alone is about 7; "ready for games" is about 2 |

## The numbers behind it

From the fresh run, the design plan and the eight reviews. I recomputed none of them.

| Measure | Age 50 | Age 60 | Real figure or target | Standing |
|---|---|---|---|---|
| Forest top height, m | 21.39 | 23.14 | 21.95 / 23.75 (the curve) | By design, not a test |
| Light under the canopy, % | 18.2 | 19.5 | 6.4-19.8 | Tuned against; 0.3 under the top at 60 |
| Forest leaf area index | 4.51 | 4.29 | Baltic band, top 4.5 | Fails by 0.01 at 50 |
| Stand branch wood over Repola A3 | 1.47 | 1.76 | 1.00 (band 0.76-1.31) | Open |
| Spread of stem diameters, SD over mean | 0.15 | 0.15 | 0.32 at 45 | Open: the forest is too even |
| Leaves on hanging shoots, stand trees, % | 79 | 77 | none measured | Never scored; reviewer's reading, not recomputed |
| Mean hanging run, stand trees, m | 1.38 | 1.38 | none measured | Never scored |
| Longest hanging strand, lone trees, m | 5.2 | 6.1 | about 2-4, by eye | Listed as a miss |
| Stomatal opening, stand trees (v1 run) | 0.988 | 0.984 | – | Water does nothing |
| Storm damage delivered, % of what is due | 100 | 100 | 100 | Falls to 81-85 at 100 and 46-59 at 150 |
| Time to grow a stand tree to that age, s | 40 | 58 | – | One server core; open-grown 122 s to 60 |
| Time to grow a 1,000 m² forest to that age, s | 2,726 | 3,275 | – | 6.5 GB at 60 |
| Time to export that one age, s | 81 | 83 | – | 81-96 % of it textures |
| Triangles, stand tree, nearest level | 2,023,679 | 2,208,447 | – | The next level is 16,000 |
| Independent scored rows that pass | 0 of 0, or 1 of 1 | 0 of 0 | – | The plan's own forecast |

## What the checking changed

**Refuted outright:** none. **Trimmed by the verifiers (P):**
- Look K2: twigs can also grow inward and along, so "down is the only free way" is too strong. The upward cap binds only near the top.
- Look K5: the age-by-age frames (10, 14, 20) could not be found by the verifier. The public hero's background trees do support it.
- Science H3: two of the three 200-year seeds are storm-poor, not three. The real shortfall is larger: 10 storms after year 40 where about 24 were due.
- Science H4: "immune" is too strong. Big old trees' suppression hazard is multiplied by 0.000002 to 0.10, and 47 did die suppressed after year 60.
- Science M3: root carbon is not spent twice. The leftover is dropped and still counted as production. Its size is unknown.
- Speed S4: `drop_dead` may already match bit for bit (decision 106), and it only acts in runs that cannot export.
- Code SW1 is medium, not high: the species file already explains three of the switches. Code SW3: the four bug-fix switches are tested.
- Public P02 and P08 are medium and low-to-medium: the README says "coming soon", and the account names are common defaults.
- Security S07: four unguarded pickle loads, not five. S08: the public scripts do not stop on a failed archive; they ship an empty one.
- Game G1: 16,000-triangle files for every tree already exist (about 7 GB), and the live-Python figure is too low (next list).

**Added by the verifiers (V), serious ones only:**
- The private repo, where all work merges, has no automated tests. CI runs only on the public copy, after the push.
- The wheel installs a top-level `treegen`, a name that already belongs to another project on PyPI.
- The sync step commits any stray file in the public clone without passing it through the stripping rules.
- The public export is a different exporter from the one that was timed. Nobody has timed it.
- Importing the library sets the whole process to one maths thread. Pip users get unpinned numpy and scipy, so a published seed may not give the published tree.
- Thick second-order branches (20 mm) are softer than 6 mm limbs. These are the forks that give a birch its outline.
- The hang settings were tuned together in one round, so one setting moved alone may be judged unfairly.
- Seedlings under 1.3 m cannot die of suppression, which is part of why the grid cell sets the young layer.
- A full tree that can be meshed or cut is 75.8 / 89.1 MB at 50 / 60, not 22 / 34-43 MB: about 320 / 376 GB for 4,222 birches.
- The command's own help calls the export "game-ready". The security policy points to a reporting channel that is switched off.

**No second check (R):** look K11-K13; science M6, M7, L1, L2; code R1, RNG1, P1, N1, U1, L1, H1; tests R4, T5, R5, T6, C3, L1; public P11-P19; security S11-S13; game G11-G14. I confirmed R4, P14 and R3 myself (last section).

## Top 20 issues

Ranked by how much each hurts the project being real and professional. S is under a day, M a few days, L weeks.

| # | Issue | Area | Severity | Effort | Fix | Mark |
|---|---|---|---|---|---|---|
| 1 | Twigs are told to hang: soft to 24 mm, no pull to upright or light, one unbranched strand growing up to 0.175 m a year for decades (K1, H1, K3) | Look | critical | M | Test softness at 0.012, 0.006 and 0.003 together with hanging share and twig shoot length, then let a shoot's gravity response follow its own vigour and let old twigs branch and be shed | C, L |
| 2 | Hang has no measured target and no owner; lean runs write 0 for it (K4, T2, G11) | Look, tests | high | S | Add the seven hang measures to the model, traced photos and laser scans, report them at 10, 20, 30, 50 and 60, write null not 0, and make hang the fifth design track | C |
| 3 | The game rule cannot be met as built, and every tree is grown in full (G1, speed S1) | Game, speed | critical | L | Decide the route, then grow trees ahead on the server, keep a skeleton and history of about 0.1 MB a tree, draw by distance, and switch a tree to live growth only when it is cut | P |
| 4 | Nothing has been measured in real time (G2) | Game | critical | M | Time 1, 50 and 500 trees in an empty project and in a packaged build, Nanite and plain, with wind and shadows | C |
| 5 | No test or CI step pins any result; golden hashes are untracked; the private repo has no automated tests (T1, code G1) | Tests | high | S then M | Track the server's golden hashes, add a check that fails on any difference, and run the full suite on every private merge | C, V |
| 6 | The front page over-claims and leads with the weeping tree; the command's help says "game-ready" (P01, P05) | Public | high | S | Land the corrected wording already approved, name the hang under "Still open", caption or swap the hero, and link the fresh run, not v1 | C, V, L |
| 7 | "0.9" is not a release: no tag, no release, defaults or growth code changed in four later commits, and none of the four ways in is live (R1, P03, P04, G7) | Public, tests | high | S | Bump to 0.9.1 at a commit whose tables match its defaults, tag it, publish a release, and make every change to results bump the version | C, L |
| 8 | The install name is unclaimed on PyPI, and the wheel installs `treegen`, which another PyPI project owns (S01, P02, P15) | Security | high | S then M | Publish under the install name from a release workflow now, and move the engine inside the `cambium` package | C, V, L |
| 9 | Old forests are not sound: a cap drops storm damage on old trees, big old trees nearly escape three death rules, a memory grid sets the young layer (H2-H5) | Science | high | M | Deliver capped storm damage through wider patches, judge vigour by basal-area growth over canopy trees only, replace the grid cell with early seedling deaths, then run 10 seeds to 200 | C, P, V |
| 10 | The leak guard: the scan always fails with 640 expected hits, nothing runs it, both nets know only listed strings, and the sync commits stray files (S02, S03, S05, R2) | Security | high | S then M | Make a clean copy exit 0, have the sync run the scan and stop on a hit or a dirty clone, add the missing kinds, and switch on GitHub push protection | C, V |
| 11 | One disk holds everything: the private repo has no remote and the publish tool is not under version control (R3, P1) | Tests, security | high | S | A private remote pushed after every merge, and the publish folder in its own private repository | C, L |
| 12 | Forest plots are slow: 23 % compiled, one core, 50-55 minutes and 6.5 GB each (S2, S7) | Speed | high | L | Compile shoots, roots, light reads and water in that order, then step a plot's trees in parallel | C |
| 13 | Seeing a tree is slow: exports are 81-96 % textures, and the public export path has never been timed (S3, G9, G10) | Speed | high | S | Lighter PNG compression, species atlases built once per export in both exporters, and a geometry-only quick look | C, V |
| 14 | The limb frame is a fishbone: many thin straight limbs, the largest 0.27-0.29 of the stem against 0.67 in scans; thick side branches are softer than thin limbs (K6) | Look | high | L | Fewer, longer-lived, thicker, forking limbs tested against the scans, and judge any branch-wood arm on limb sizes as well as the total | C, V |
| 15 | Young open-grown trees do not read as birch: a pole at 10, larch-like at 20, tips hanging from 14 (K5) | Look | high | M | Comes with rank 1's twig fixes plus young limb reach; render single frames at 10, 14 and 20 so it can be checked | P |
| 16 | The model is one class of 3,113 lines; a misspelt setting is silently ignored; the hot rules exist twice (code S1, SW2, D1) | Code | high | M then L | After rank 5: one strict loader, remove dead switches, one copy of the hot rules, then split the class as pure moves | C |
| 17 | No middle level of detail, and the hero tree is 10.3 million triangles (G3, G4) | Game | high | M | Add 200,000 and 64,000 levels and a leaf level by distance, mend the 16,000 level's cards, and give the nearest level an optional budget | C |
| 18 | A grown forest cannot be exported, and there is no collision, cut, stump or fallen branch (G5, G6) | Game | high | M | A forest export of every living tree's place, seed and age with a middle-level mesh, then trunk capsules and a cut call in Python | C |
| 19 | Forests, open-grown trees and the game export are untested at the ages that are used (T3) | Tests | high | M | Add an open tree to 60, a forest plot to 30, a second seed and an export at 30 to the golden set, and run a 60-year plot nightly on the server | C |
| 20 | A seed is not a portable tree, yet three sentences say it is; pip users also get unpinned libraries (X1, P17) | Tests, public | medium | S | Say "the same tree on the same machine and library versions", record library versions in every run, and check them at import | C, V |

Just below the line: water does nothing at 50 and 60 and there is no weather (M2, C); the only sensitivity screen is older than the model (M1, C); wood upkeep is charged per internode whatever its size, 23 % of fixed carbon at 50 and 60 (M4, C); one wood has three strengths and bark four rules (M5, C); a tested 1.5x for single trees sits unused (S4, P); GitHub's safety settings are off (S06, C, L).

## Quick wins, under a day each, in order

1. Claim the install name: publish 0.9.1 from a release workflow with trusted publishing. Until then every docs page says "install from a clone".
2. Switch on GitHub's push protection, secret scanning, private vulnerability reporting, Dependabot and a rule on the default branch. Use the no-reply address in the sync step.
3. Back up: a private remote for the private repo, and the publish folder under version control.
4. Mend the leak guard: a clean copy exits 0; the sync runs the scan and stops on a hit or on a dirty clone; add the two account names, unix home paths, IPv6 and newer token shapes; drop daily reports by pattern.
5. Track the server's golden hashes, with seconds and peak memory, and add `golden.py check`. Do this before the plan's step T1.
6. Measure hang: the seven measures in the tree table, null not 0 in lean runs, a hang row in every results report, at 10, 20, 30, 50 and 60.
7. Front page: the 23 corrected lines (approved in decision 110), hanging strands under "Still open", a caption under the hero, the fresh run as the evidence link, "game-ready" out of the command's help.
8. Quick start: the right output folder, one line of timings, a fast first command (15 years, or a stand tree), one command per line.
9. Tag 0.9.1 with a changelog entry and a GitHub release. Write the rule: a change to results bumps the version.
10. Export: PNG compression level 1-3, atlases once per export, a geometry-only option. Then time the public `cambium export`.
11. Run the golden check with `drop_dead` on. If every hash matches, call it lossless and ask the owner one line.
12. Add the missing test for `light_rows`. Keep the switch: it is the one measured gain for single trees. The code audit's advice to remove it is not taken.
13. Fix the storm cap behind a switch, with a test that summed chances equal the uncapped sum. It delivers 100 % at 50 and 60 today, so those ages should not move.
14. Add label rows for the 13 look settings and for the site file. Close wood density against its own cited source.
15. Check every command argument and the output folder before growing. Plain messages, exit 2.
16. Tooling: `.gitattributes`, a formatter and linter in `pyproject.toml`, one reformat-only commit, a lint job.
17. Correct stale sentences: "all off by default" in `fast.py`, the grid-size claim in the species file, the three "same bits on every machine" lines, the moose species comment.
18. A one-screen `KNOWN_ISSUES.md` with the model's and the real figure at 50 and 60. The old file becomes a development log under `notes/`.
19. Delete the 26 unused media files (54.6 MB) and drop the server scripts and one-off run queues from the public copy.
20. Server scripts: one label check for all, `pipefail`, and a start that refuses unless both guards are alive.
21. In the next control run's report, give 50 and 60 by storm history (half of plot seeds 1-20 have a storm in years 45-50; R).

## Big jobs, in order

1. **Hang, as a fifth design track (M, several rounds).** Measure on the model, photos and scans. Then a small factorial on softness radius, hanging share and twig shoot length. Then gravity response by a shoot's own vigour, one stiffness law, twig turnover and two end buds. Each is a switch, paired by seed, judged on the hang measures with light and leaf area at 50 and 60 holding. Photos come last.
2. **Limbs (L).** Fewer, thicker, forking limbs against the scans' size spread. Do it with the branch-wood step, not after it.
3. **The game route (L).** The owner's decision first. Then real-time timings, middle levels of detail, a stored skeleton with a run-time mesher, a forest export, collision and a cut call, and last the lighter far model.
4. **Code restructure (weeks).** Only after quick win 5. Strict parameter loader, dead switches removed, one copy of the hot rules, library code out of scripts, then the big class split as pure moves with the golden check after each.
5. **Fast forests (L).** Compile shoots, roots, light reads and water; step a plot's trees in parallel; a side store for dead nodes; a tolerance solver at a planned new baseline.
6. **Old forests (M).** Death rules, early seedling deaths in place of the grid cell, then 10 seeds to 200 with storm years printed beside survival.
7. **Carbon and water (M).** Upkeep by sapwood, the root leftover out of production, weather or a plain "off", and the sensitivity screen rerun on today's defaults for stand trees and plots.
8. **Release process (M).** Release workflow, CI on Windows, macOS and ARM, a lowest-versions job, the engine inside the package, a docs site built from the fresh run.
9. **Independent proof.** Measured stands at 50 and 60, opened at their source. Until then no release may claim an independent pass. The plan says this too.
10. **The C++ port waits** until the model's rules stop moving. Both the speed and game reviewers agree, and so do I.

## Decisions only the owner can make

The plan's own decisions were answered in decision 110. Top height is still open there. These are new.

1. **Hang.** Make it the fifth design track now, judged by measurements on photos and scans, not by taste? I recommend yes. This keeps decision 92 and finally gives it numbers.
2. **The hero picture.** Keep it with a caption that names the fault, or swap it for a less hanging view until the fix lands?
3. **The game rule.** Every tree keeps its own data and growth everywhere, its own shape wherever the eye can tell, and far trees are drawn coarse from their own stored skeleton. Yes or no? As written, decision 91 costs 140 GB or more by every route that exists.
4. **Real-time test.** An afternoon on the gaming PC, or another machine, to time trees in the engine. Nothing else can answer "is it ready for games".
5. **PyPI.** Publish 0.9.1 now to hold the name. It needs the owner's PyPI account with two-step login.
6. **Public history.** Rewrite it once to remove the personal address on every commit, the server's account names and 96 MB of old media? With 1 star and 0 forks this is the cheapest moment. If no, only the tip is fixed.
7. **Backup.** Where the private repo and the publish tool get their second copy.
8. **Speed settings.** `drop_dead` now, if the golden check shows the same bits. `light_rows` with the next new baseline; it changes rounding once, so a seed gives a slightly different tree from then on.
9. **Is "same seed, same tree on every machine" a goal?** Today it is not true (216 of 225 files differ between two machines). If it is not a goal, the wording changes and picked trees are kept from one machine.
10. **Old forests.** Show forests past 100 years, or label them a what-if until the storm rule, death rules and seedlings are fixed?
11. **Weather.** For 1.0: add year-to-year weather, or say plainly that water is off in practice?
12. **One named site.** Today's site mixes six regions. Which single place should it be?
13. **A draft preset** for looking only, never scored. It is faster and gives a different tree from a full run. Allowed?
14. **Old switches.** May dead and failed switches be deleted, with the rule "a switch is adopted or removed within one release"?
15. **Server.** One admin step to cap the run account's memory and disk, so the other services on it are safe.
16. **Public tidy-up.** Working logs into `notes/`, default branch renamed to `main`, and whether the game's script names and the server's processor type may stay in public docs.

## On the four design tracks

I don't dispute the tracks or the plan's order. Six points.
1. **The crown space rule failed its desk check today.** It allows 0.50 / 0.51 of the ground as crown at 50 / 60 against the 0.99 needed, so steps C2 and EC are not built. That frees about 5.5 server hours. It also means the look review's "let twigs go outward with the crown track" has nothing to ride on. Hang needs its own track.
2. **Add the hang measures to T1 and ten open-grown trees to T2.** The control runs then record hang at almost no cost. Run the hang arms before the branch-wood step: twig posture moves leaves and so light, and the tracks already share 0.3 points of light and 0.21 of leaf area index at 60.
3. **Golden hashes go into the repository before T1.** Every "bit-identical to the control" rule in the plan is checked by hand today.
4. **Branch wood.** I agree with the look reviewer. The total is over Repola, but the biggest limbs are under half the thickness scans show. The plan's limb-size guard must be binding. Arm A would also inherit the flat upkeep per internode (M4).
5. **Storm timing.** The plan's rules at 50 turn on 0.01 of leaf area index. Read 50 and 60 by storm history before judging any arm.
6. **Switches.** Each track adds one into the two largest functions. Give each an end date.

Two reviewers disagreed with earlier work, and I side with them: saved lists show seedlings do not shrink old trees' crowns (L2, R), and Hemery's formula is not the ceiling for old trees.

## What is genuinely good

- **Honesty.** Tuned values say so. The long strands, big leaves and even forest are listed as misses. The port plan says "don't port yet".
- **Repeatable runs and identity tests.** Lean against full, compiled against numpy, resumed against straight. Few projects have these.
- **CI is real.** Nightly runs were green on 2026-11-10 and 2026-11-11 (L). The wheel is built and run on three Python versions.
- **The engine can grow a hang.** The bending method is a published one. Its inputs and switches are the problem, not its physics.
- **Damage and mortality** are the best-sourced blocks, and the damage log made a full re-draw of the weather possible.
- **The export is exact.** Triangles come back from the engine one for one, and leaf area in the mesh equals the model's within 0.3 % at 50 and 60.
- **The speed work measures before it promises.** Six lossless settings gave about 2x on trees and 2.8x on plots.
- **Nothing secret is public.** Two independent searches of every public object agree.
- **Stand trees at 60 read as birch at a distance.** Young bark, leaf shape close up and autumn colour are convincing.

## What I checked myself, and what I did not

- **Checked (L):** the softness rule in `treegen/mechanics.py:103-109, 149`, `treegen/growth.py:2693-2703` and `species/betula_pendula.yaml:597-607, 1717, 1839, 1842`. The private repo has no remote. The install name returns 404 on PyPI, while `treegen` and `cambium` are taken. The public repository has no release, no Pages site, no branch rule, no topics, private vulnerability reporting off, and weighs 141 MB. The public hero picture: the lone birch is a column of long vertical strands with a purple-brown cast, and the trees behind are poles with drooping tufts. Decisions 91, 92, 95, 106 and 109-111, the plan and the crown desk check. The design files name hanging four times and never as a subject. The species file calls `drop_dead` not lossless (line 2384) while decision 106 says it matches bit for bit.
- **Not checked:** nothing was grown, timed or rendered by me. I opened no paper: every science claim carries its reviewer's own source marks, and the look review lists seven sources as UNVERIFIED. Items marked R had no second reader.
