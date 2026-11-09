## What this changes

<!-- What and why, in a few lines. Link the issue it closes. -->

## How it was checked

<!-- The tests you ran, and for anything that changes growth: the runs you compared (seeds, years, open or stand) and what moved, at ages 50 and 60 at least. -->

## Checklist

- [ ] Tests pass (`python -m pytest`; the quick part is `python -m pytest -m "not slow"`).
- [ ] Every new or changed value cites its source: publisher (DOI), PubMed Central or the authors' repository, with page or table.
- [ ] No target was loosened to make a run pass.
- [ ] Every TUNED value says what it was tuned against (the target, the runs and the commit).
- [ ] Values are labelled as sourced, DERIVED, TUNED or VERIFY in the species file and `reference/<species>/labels.yaml`.

Pull requests are merged with the maintainer's approval.
