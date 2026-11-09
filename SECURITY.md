# Security policy

## Supported versions

Only the latest release of Cambium (currently 0.9) gets fixes.

## Reporting a problem

Please don't open a public issue for a security problem. Report it privately through GitHub's
[private vulnerability reporting](https://github.com/rar-file/cambium/security/advisories/new) for
this repository, to the maintainer, rar-file. Say what an attacker could do, and how to reproduce it.

You'll get an answer within two weeks. Once a fix is released, the advisory is published with credit
to you, unless you'd rather not be named.

## What to know when using Cambium

- Species and environment files are YAML read with `yaml.safe_load`; they can't run code.
- Saved model states and plot checkpoints (`.pkl` files, from `cli.py --save-at`, `tools/plot.py` and
  `tools/game_export.py --state`) are Python pickles. Loading one can run any code it holds: only load
  files you made yourself or got from someone you trust.
- Cambium makes no network connections.
