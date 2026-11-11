# Audit: is anything unsafe or leaking

2026-11-11. Reviewer: Fable 5.2 (`claude-fable-5-2`), independent, read only. **Score for this area: 6 / 10.**

## In short

1. **Nothing secret is public or stored.** No key, token, credential or environment file is in either repository, in any commit or in the working folders.
2. **The public history is clean of what the owner listed:** old address, real name, the game's name, the server's host name, network addresses, key file names and PC paths. Checked two ways.
3. **Two kinds slipped through and are public now:** the names of the server's two accounts, and one home-folder path on the server. The real risk is low. It still breaks the owner's rule.
4. **The leak guard is weaker than it looks.** Its scan can't pass any more, nothing makes it run, and it only knows strings it has been given. A new kind of private detail goes straight through.
5. **The install name in the docs is free for anyone to take on PyPI.**
6. **GitHub's own safety settings are mostly off.** The workflows themselves are sound.

This report holds no model results, so it has no table by age.

## What I did

- Ran the pipeline's own scan once on the public copy: 512 commits, 5 tags, 1,419 blobs, 66 patterns.
- Read every object in the public copy myself, reachable or not (3,497 objects), by kind of data: address shapes, network addresses, home paths, SSH options, key headers, token shapes, credentials, host-name shapes, session links. Also the metadata of every image, and of the four README videos as GitHub serves them.
- Did the same secret search on the private repo (4,788 objects) and the working folders.
- Dry run of the next sync, in memory, nothing written: the pipeline's rules applied to the private tip, to today's uncommitted reports and to the overlay, then checked.
- A probe: made-up private details passed through the rules and the scan, in memory.
- Read `publish.py`, `rules.py`, `sync.py`, `scan.py`, every script under `tools/node`, the two workflows, and each place that loads a saved file.
- GitHub settings by read-only API calls. PyPI's public API for the package name and every pinned version.
- Not done: no login to the server, no model runs, no tests, no build of the public copy.

## What is good

- **Scan result:** 640 lines, none of them a private string. 638 are expected paths, 1 is the remote, 1 is local leftovers (finding S02).
- **My own search agrees.** In all public objects the only address shapes are the commit address the owner chose, the co-author address and a test placeholder. The only network address is loopback. Key paths are placeholders.
- **No forced push has ever happened** on GitHub (one branch creation and 25 plain pushes). One leftover commit in the local public clone was never pushed (GitHub answers "no commit found").
- **Images and videos carry nothing private.** No location data, no text chunks, no paths. The reference photos keep their photographers' camera tags and are credited. The videos hold only encoder settings.
- **The next sync is clean today.** The dry run gives 0 hits on the pipeline's list across 298 text files, 15 uncommitted reports (this one included) and 25 overlay text files.
- **The private repo has no remote** and holds no secrets either. The server key itself is in neither repository. In the public copy, the host, the account and the key's path come from three environment variables.
- **Code:** YAML is read with `safe_load` everywhere. No `shell=True`. Every subprocess call passes a list. `np.load` keeps pickle off. `SECURITY.md` is honest about saved states.
- **Server scripts:** no `sudo` anywhere, every kill is limited to the run account, jobs run at nice 19 with idle disk priority, SSH runs in batch mode with host-key checking left on and no agent forwarding. `submit.sh` and `cancel.sh` check labels against a character list and quote arguments properly. `submit.sh` refuses to upload if the copy holds an image.
- **Workflows:** `pull_request`, never `pull_request_target`. Read-only token by default. No stored secrets. Time limits. The Pages permissions sit only on the deploy job. One collaborator, no deploy keys, no webhooks.

## Findings, most serious first

### S01. The package name the docs tell people to install belongs to nobody. High. Effort S. CONFIRMED
- Where: public `docs/site/install.md:6`, `docs/site/index.md:23`, `README.md:116`, `pyproject.toml:6`. PyPI's JSON and Simple APIs both answer 404 for `pycambium` (checked today; a control name answers 200).
- What: the docs say `pip install pycambium`. The name is unregistered.
- Why: anyone can register it and ship their own code to people who follow Cambium's instructions. It costs an attacker five minutes.
- Fix: register and publish 0.9 now, from a release workflow with trusted publishing, with two-step login on the PyPI account. Until then the docs say "install from a clone". The public-face audit found the same (its P02); I agree with it.

### S02. The privacy scan can no longer pass, and nothing makes it run. High. Effort S. CONFIRMED
- Where: `scan.py:56-58` (any remote is a hit), `scan.py:92-101` (the three cleaned logs are excused only if the release commit is the tip; 26 commits now sit above it), `publish.py:64-67` against the overlay's `docs/media` and reference photos. `sync.py` never calls the scan. The public clone has no pre-push hook.
- What: I ran it. Exit status 1, 640 hits, every one expected. It will say the same after every sync.
- Why: a real leak would be one line among 640, and the exit status is always "failed". The last check before a push now depends on someone reading the list closely each time.
- Fix: make the expected state pass: allow the one known remote; excuse the re-added logs in any commit from the release commit on; list the overlay's media and credited photos as allowed. Then make `sync.py` run the scan and refuse to commit on a hit, and add a pre-push hook that runs it. `git gc --prune=now` clears the 6 leftover objects.

### S03. Both nets only know strings they have been told. High. Effort M. CONFIRMED
- Where: `rules.py:97-244` (exact strings and one host-name shape), `publish.py:51-62` (ten exact file names dropped, one of them a dated daily report), `publish.py:118-126` (a binary or non-UTF-8 file passes unchanged, silently), `scan.py:118-123` (binary files are searched for a few long literals in raw bytes only).
- What: the probe, with made-up details:

| Made-up detail written into a report | Rewritten | Scan flags it |
|---|---|---|
| A new server's host name, or a domain | no | no |
| A Linux or macOS home path | no | no |
| A new person's name; a new game title | no | no |
| An IPv6 address; a phone number | no | no |
| Newer GitHub token shapes; a PyPI token; an SSH public key | no | no |
| A new line of chat in quotes; a credential written as prose | no | no |
| An IPv4 address; an e-mail address; a classic token; a key header; a credential as key=value | no | yes |
| This PC's home path in a UTF-8 file | yes | clean |
| The same path in a UTF-16 file (what older PowerShell redirection writes) | no | no |
| The same path inside a gzip file | no | no |

- Why: reports are written every day, by agents, about servers, people and the game. The answer to "would a new kind of private detail be caught?" is no. Tomorrow's daily report would also be published, because only one date is on the drop list. Today's audit files already carry short phrases from the owner's messages, which the project decided not to publish; nothing can see that.
- Fix: (1) fail closed on file type: publish only listed extensions, and stop on archives, UTF-16 and non-UTF-8 files; (2) drop by pattern (`reports/daily_*.md`), not by date; (3) add the missing kinds to the scan: unix home paths, IPv6, newer token shapes, SSH public keys, phone numbers, name-at-host shapes, quoted speech after "said" or "wrote"; (4) at each sync, print every new capitalised name and host-like word since the last sync, for one human look; (5) turn on GitHub's push protection as a second net (S06).

### S04. The server's account names and one home path are public. Medium. Effort S. CONFIRMED
- Where: public `DECISIONS.md:41,85`, `QUESTIONS.md:102-104`, `reports/milestone_M2.md:566`, `reports/reviews/2026-11-06_M2_checker_C.md:112`, `..._M2_grid_corrections_review.md:10,22,147,168`, `..._M2_grid_corrections_rereview.md:45`, `..._node_disk_report.md:30`; the home path at `reports/reviews/2026-11-06_node_disk_rereview.md:96`, in history since `b85d479`.
- What: the names of the admin account and the run account, on twelve lines in seven files, and the run account's home folder once in an eighth. Process numbers too.
- Why: the owner's rule was that the server's user must not appear. No host name, address or key is with them and login is by key, so the real risk is low. It shows the lists miss a whole kind: they only catch a name directly followed by an at sign.
- Fix: add rules for the two names in code marks and for unix home paths; correct the overlay copies by hand. The lines are also in pushed history. Removing them means rewriting history and a forced push. I'd fix the tip and accept the history. That is the owner's call.

### S05. Hand-kept overlay copies go public untouched, and drift without warning. Medium. Effort S. CONFIRMED
- Where: `publish.py:395-400` copies every overlay file as it is. `overlay_base.txt` tracks 13 files, but not `DECISIONS.md`, `QUESTIONS.md`, `PROTOCOL.md` or `README.md`. `sync.py:15,35` commits the typed message as it is. Commits made straight in the public clone (the README ones) skip the rules too.
- What: the files most likely to hold private text are the ones kept by hand with no check. Proof of the leak path: the account names in S04 sit in the overlay's `DECISIONS.md` and `QUESTIONS.md`. Proof of drift: the private `QUESTIONS.md` has Q40; the public one doesn't, yet public `DECISIONS.md` row 108 cites it.
- Why: every new row or question needs a person to re-edit the copy by hand. The shortcut is to paste the private file over it.
- Fix: build the three logs each sync from the private files, through the rules plus a small patch file per log. Pass overlay text and the sync message through the rules as well. Record a base hash for every overlay file. Put the pipeline folder under local version control; today it is not a repository, so a change to the rules leaves no trace.

### S06. GitHub's safety settings are off. Medium. Effort S. CONFIRMED (API, today)
- What: no branch protection and no ruleset on `master`, so a forced push or a deletion is allowed. Secret scanning and push protection: disabled. Dependabot alerts and security updates: disabled. Code scanning: not set up. Private vulnerability reporting: disabled, while `SECURITY.md:9-11` sends reporters to it, so that link is a dead end. Actions: any action allowed, pinning by hash not required. Two-step login on the account: UNVERIFIED, the API doesn't say.
- Why: one bad command from an agent can rewrite public history. A token pushed by mistake would not be stopped. A reporter with a real problem has no private channel.
- Fix: a ruleset on `master` (no forced pushes, no deletion, the tests required on pull requests); switch on secret scanning with push protection, Dependabot alerts and private vulnerability reporting. All are free for a public repository.

### S07. Saved states are pickles, loaded with no guard in five places. Medium. Effort M. CONFIRMED
- Where: `treegen/checkpoint.py:34-36` (`cli.py --resume-state`), `treegen/plot.py:548-553`, `tools/game_export.py:219-221`, `tools/tree_list.py:94-100` (its help text calls the folder "read only"), `tools/cpp_cost.py:1065`. The middle two tools ship inside the wheel.
- What: loading a pickle runs whatever code it holds. `SECURITY.md` says so plainly. Nothing in the code warns or limits it.
- Why: growing a forest is slow, so people will want to pass saved states around, and the README promises a ready-made birch pack. A state from a stranger is a program.
- Fix: now, an unpickler that only allows the project's own classes, NumPy arrays and plain containers, and one warning line at load. Later, a data-only format (arrays plus JSON) for anything meant to be shared. Never ship the birch pack as a pickle.

### S08. Four node scripts paste unchecked arguments into the server's shell. Medium. Effort S. CONFIRMED by reading
- Where: `tools/node/fetch.sh:8-10` (checks only the label's first letters, then puts it inside single quotes in the remote command), `fetch_examples.sh:6` and `fetch_side.sh:5` (all arguments pasted in), `status.sh:5` (first argument pasted in). `fetch_examples.sh:13` and `fetch_side.sh:8` also reuse file names sent back by the server.
- What: a quote, a semicolon or a space in a label becomes a command on the server. `submit.sh:24-28,46` and `cancel.sh:6-9` already do it properly.
- Why: no outsider can reach this. The callers are agents that build labels from text, on a server shared with other services. One stray character should end in "bad label", not in a command.
- Fix: one `check_label` function in `env.sh`, called by every script; a digits-only check in `status.sh`. Also: the public `submit.sh:31-33` and `side_deploy.sh:8-9` name a file the public copy doesn't have, so both stop with an error for anyone else (checked: `git archive` exits 128).

### S09. On the shared server, the other services are protected by two loops that nothing starts or checks. Medium. Effort S, plus one admin step. Scripts CONFIRMED; effect on the other services SUSPECTED
- Where: `tools/node/mem_guard.sh:5-21`, `tools/node_disk_guard.sh:8-11,27-31`, `tools/node/slots.sh:10`, `tools/node/status.sh`, `PROTOCOL.md` section 6 against `DECISIONS.md` row 89.
- What: the memory guard stops the largest job under 14 GB free. The disk guard pauses jobs under 8 GB, then exits and must be restarted by hand. Neither is started by `submit.sh` or `slots.sh`, and `status.sh` doesn't say whether they are alive. The 40 GB limit is per process, not for 16 workers together. No job marks itself as the first to go when memory runs out, and there is no swap. The fetch scripts' `tar` and `split` on the server double a folder on disk with no free-space check, and the disk guard can't pause them. The protocol still says 8 or 14 runs at once; the scripts use all 16 cores.
- Why: if a guard has died, the kernel decides what to kill, and it may pick one of the other services.
- Fix, no admin needed: the job wrapper writes 1000 to its own `oom_score_adj`; `claim` refuses to start unless both guards are alive; `status.sh` prints their state; the fetch packers get `nice`, `ionice` and a free-space check; bring section 6 in line with row 89. Better, one admin step for the owner: a memory, CPU-weight and task limit on the run account's slice and a disk quota, so the kernel enforces what the loops only watch.

### S10. Dependencies and actions are pinned by name, not by content. Low. Effort S. CONFIRMED
- Where: `requirements.lock`; `.github/workflows/tests.yml:28,31,36,53,71`; `docs.yml:24-30,47`; `run_worker.bat:13`.
- What: the lock pins 24 exact versions with no hashes and is installed without `--require-hashes`. It is a freeze of one Windows environment: it holds a Windows-only package and `pypdf`, which no code imports. `build`, `hatchling` and `mkdocs-material` are unpinned in CI. The four actions are GitHub's own, pinned by major version tag. There is no Dependabot file.
- Checked today on PyPI: all 24 pins exist, none withdrawn, no advisory listed for any pinned version. `colorama` (test-only, Windows) has had no release since 2022; `cycler` since 2023; `six` since 2024. Stable, worth a yearly look.
- Fix: build the lock from `pyproject.toml` with hashes (`pip-compile --generate-hashes` or `uv lock`), drop `pypdf`, add Dependabot for pip and for actions, pin actions by commit hash.

### S11. Logins on the PC reach further than the work needs. Low. Effort S. Token CONFIRMED; key SUSPECTED
- What: the GitHub login that agent sessions use can write to every repository of the account, with workflow and gist rights. Publishing needs one repository. The server key works with no prompt (the scripts run in batch mode), so any process on the PC can act as the run account. I did not inspect the key.
- Fix: a fine-grained token for the one public repository. On the server, limit the key in the account's authorised-keys file: no port, agent or X11 forwarding.

### S12. The stem tracer's local page server accepts writes from any web page. Low. Effort S. CONFIRMED by reading
- Where: `tools/serve_tracer.py:77-91,110`.
- What: it listens on loopback only, which is right. Its save route checks neither the Origin nor the Host header and reads a body of any size. While it runs, a page open in the same browser can overwrite the traces file.
- Fix: refuse a request whose Origin isn't the server's own; require a JSON content type; cap the body.

### S13. Small points. Low. CONFIRMED unless marked
- `treegen/export.py:302-307,370` follows a file reference inside a `.gltf` to any path, not only the file's own folder. Read only, no network. Keep it inside the folder.
- The private repo and the pipeline folder appear to exist only on the PC. SUSPECTED: I can't see a backup.
- Public `docs/unreal.md` and `tools/unreal/game_route.py` still describe the game's own script and folder names. Public `reports/P0_performance.md:35` and `reports/cpp_port_plan.md:70` name the server's processor core type. The owner may not mind; neither was on the list.

## What a stranger's pull request can run

Their own code, in the quick tests, on GitHub's runner: read-only token, no secrets, 30 minutes at most, and a first-time contributor needs approval. The worst case is wasted runner time. This is the normal, acceptable setup. The nightly run and the deploy job only run on `master`.

## The design tracks

I read the design files present today. None touches this area and I don't disagree with them here. Their text passes the dry run; the owner's name in them is rewritten by the existing rules.

## Suggested order

1. S01, S06: an hour each, and they close the two ways a stranger could do harm.
2. S02, then S04 and S05: the scan passes again, the tip is corrected, the logs are generated.
3. S03: the scan learns kinds, and unknown file types stop the sync.
4. S08, S09 before the next large batch on the server. S07 before any saved state is shared.
