# Contributing to Cambium

Pull requests are welcome. A pull request is merged only once the maintainer approves it.

## What a change needs

- **Tests pass.** Run `python -m pytest` before you open the pull request, and say in it what you ran and where.
  Add tests for new behaviour. Never delete a test or make one looser.
- **Targets are never loosened.** `reference/targets.yaml` holds the measured values the model is judged against;
  the approved version is the git tag `targets-approved`. A change that makes a result pass by widening a band,
  dropping a condition or removing a target won't be merged. Proposing a new or corrected target is fine: give the
  value, the source, the page or table, and the conditions it was measured under.
- **Every value cites its source.** A value in `species/*.yaml` names where it comes from: the paper with its page,
  table or equation, and a DOI. Read the source at the publisher, on PubMed Central (PMC), or in the authors' own
  repository. Copies on third-party sites don't count, and abstracts or search summaries aren't a reading.
- **Tuned values say so.** A value with no direct source may be tuned, but it is labelled `TUNED` and says what it
  was tuned against (which target, data set or photo, and how). Values worked out from a source are labelled
  `DERIVED`, with the working. Values not yet checked keep the `VERIFY` flag.
- **New behaviour is an option, off by default,** tested alone against the current default on the same seeds, with
  a before/after table at ages 50 and 60 where they apply. `PROTOCOL.md` has the full working rules.
- **No third-party code or images under unclear or incompatible licences.** Published equations and values with
  citations are fine. Photos added to the repo must be openly licensed and credited (`reference/PHOTOS.md`).

## Licence

By submitting a contribution you agree that it is licensed under the Apache License 2.0, as section 5 of
[LICENSE](LICENSE) says.
