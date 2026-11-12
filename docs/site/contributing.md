# Contributing

Cambium is open to contributions from game developers and scientists. Reports of things that look wrong, and better sources for values, are as welcome as code.

## Issues

Open an issue at [github.com/rar-file/cambium/issues](https://github.com/rar-file/cambium/issues):

- **Bugs:** what you ran (seed, years, species, settings), what you expected, and what you got. Include the version from `cambium --version`.
- **New species or source:** use the "New species or source" issue template.
- **Questions and ideas:** a plain issue is fine.

## Pull requests

Pull requests are welcome. They are merged only with the maintainer's approval. For anything large, such as a new species or a change to the model, open an issue first so the approach can be agreed before you start.

### Checklist

Every pull request must meet these:

1. **Tests pass.** The only failures allowed are the tests that are kept failing on purpose for a known fault (see below).
2. **Sources are cited** with a link others can open: the publisher's page, a PubMed Central (PMC) page, or the author's repository. Say where in the source (table, figure, page).
3. **Targets are never loosened.** A target is not widened, moved or dropped to make a run pass.
4. **Every TUNED value says what it was tuned against.**

New species and new sources go through the "New species or source" issue template first. See [Species and sources](species.md) for the labels and how to add a species.

## Run the tests

From a source checkout:

```
git clone https://github.com/rar-file/cambium
cd cambium
pip install -e ".[test]"
pytest -m "not slow"    # the quick tests, about two minutes; every pull request runs these
pytest                  # all of them, about ten minutes on one core; run on main and every night
```

For the project's own environment, use Python 3.14.7 and `pip install -r requirements.lock` first, as the automatic tests do.

To run one file:

```
pytest tests/test_species_data.py
```

Some tests read the git history and tags, for example the approved targets, so work in a full clone, not a shallow one. Some tests grow trees, so the whole suite takes a while.

Tests that mark a known model fault are kept failing on purpose, and their docstrings say so. Don't skip them or loosen them; they pass when the fault is fixed. See [How real is it](how-real.md#tests-that-fail-on-purpose).

## Changing the model

- A change to growth changes the trees. Check it on several seeds, at ages 50 and 60 and on young trees. One seed proves nothing.
- Say in the pull request which results moved, and by how much.
- If you change a value in a species file, update its label in `reference/<species>/labels.yaml`. A value whose label wasn't updated counts as unchecked.

**The golden check.** `cases/golden_server.json` holds the hash of every output of the golden runs (`tools/golden.py`), as the project's reference server recorded them, with its Python and library versions, its processor, and each run's seconds and peak memory. A change that should move no result is checked there: `python tools/golden.py record <label> --check` exits 0 only when every file hashes the same, and otherwise names each run or file that differs, is missing or is new. Hashes belong to the machine, so on your own computer record the runs before and after your change and run `python tools/golden.py compare <before> <after>`. A change that moves results updates the tracked file in the same pull request, with `python tools/golden.py track`.

## Conduct and security

Everyone taking part follows the [Code of Conduct](https://github.com/rar-file/cambium/blob/main/CODE_OF_CONDUCT.md) (Contributor Covenant 2.1). Report security problems privately, as [SECURITY.md](https://github.com/rar-file/cambium/blob/main/SECURITY.md) says, not as issues.

## Licence

Cambium is licensed under Apache-2.0. Contributions are accepted under the same licence.
