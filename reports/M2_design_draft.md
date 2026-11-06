# M2 design (draft, written before any M2 run)

Status: a draft on the `p0-perf` branch. It waits for the screen's ranking, and the numbers it can't yet have say "not set". The cut rule's numbers go into DECISIONS.md before any run.

Every source below is a research subagent's reading (`reports/research_notes.md`). Each must be opened again before it's cited in a change or a target.

## 1. The one finding so far that shapes it

**There's no direct source for alpha** in anything readable, so alpha goes down the calibration route (PROTOCOL.md section 9). Parameters with a direct source aren't calibrated.

**The CROBAS fertility mechanism fits a value the model already has.** Minunno et al. 2019 Eq. A10 (W_R = a_Rs W_F) sets fine-root mass from foliage mass by site type. The model already has that ratio: `resource.leaf_costs.fine_root_to_leaf_mass`, 0.48 (and `roots.fine_root_uptake.fine_root_per_leaf_mass`, 0.46, for uptake). So a fertility option may need no new carbon pool, only that ratio as a function of site index. Whether that keeps the Eriksson curve's shape is the subagent's inference, not a source's claim, and is the first thing to test. Not calculated yet.

**Height and leaf area are fitted together, never height alone (the maintainer, 2026-11-06).** The trees are too tall, mostly when young, and have too few leaves. Lowering alpha would likely fix height but worsen leaf area. So:

- Every fit scores height and leaf area at once, and no candidate is chosen on height alone.
- If no alpha fits both, M2 reports that the problem is how carbon is shared out, which is M3's work, and doesn't force the fit.
- Light isn't counted as a third failure. It follows leaf area (`tools/light_lai_link.py`), so the two are reported as linked.

## 2. What gets calibrated

| Parameter | Why | Bounds | Status |
|---|---|---|---|
| `resource.alpha` | No direct source | About 2.7-6.8 (leaf route 5.5-6.8; stand routes 2.7-3.75 and 5.15-5.35; subagent's arithmetic, to recheck; some inputs aren't independent of the model) | Certain |
| Fine-root ratio by site index | Eq. A10 has no birch values in what's readable | Not set: only 0.46-0.48 seen, at one site type | If the option is built |
| Others | Only those the screen ranks as influential and that have no direct source | From published ranges only | Not set: waits for the ranking |

Values on the audit's unsupported list that may turn out influential: `maintenance_per_internode`, `late_leaf_season_fraction`, `xylem_conductivity`, `psi_stomata_open`, `psi_stomata_closed`, `psi_turgor_loss`. Where a direct source exists (for example turgor loss, Hannus et al. 2021), the fix is the source's value through the adoption gate, not calibration.

## 3. Fit and validation stay separate

| Fit against | Conditions to respect |
|---|---|
| Eriksson height curve, shape across site indices (Elfving 2010 p. 58, height above breast height on breast-height age, T13 as in targets.yaml) | Ratio of SI 32 to SI 22 heights falling with age: about 2.28 at 10, 1.65 at 30, 1.45 at 50, 1.40 at 60 (to recheck) |
| Liziniewicz 2022 MAI ladder, Table 6, p. 13: 6.0, 7.9, 10.5, 12.8 at SI 22, 25, 28, 32 | Their simulation's output, not a measurement. Planted improved stock, thinned, no mortality, rotations 60, 51, 45, 31 years. SI 32 is outside their data. Their site index may not be on Eriksson's scale (Johansson 2013 unread) |
| Repola 2008 stem wood, Eq. 7 at over-bark DBH | Finnish, 34 % downy birch; bias-corrected |

| Validate against (not used in the fit) | Conditions |
|---|---|
| Aosaar 2016 NPP split, Table 4 | One fertile stand, age 10; roots partly assumed |
| Repola 2008 Table 1 basal area, 2.7-32.3, mean 19.2 m²/ha | Range check; some thinned, some mixed |

**The ladder needs a like-for-like volume.** MAI there is harvested volume over rotation, on their thinning schedule. A stand tree follows the species' own thinning table, so the comparison needs thought before it's a score, and may have to be a plot. Not calculated yet.

## 4. Method

1. **Every candidate is judged on seed averages,** never on one seed (PROTOCOL.md section 2). The model is chaotic: a change of a few parts in a million moves height by up to 6 % and leaf area by up to 28 %. Seed spread, measured on the node at 30 seeds: height SD 0.42 m at 15, 0.70 m at 30, 0.76 m at 60; LAI varies by about 30 % at 15 and 11 % at 60. Number of seeds per candidate at each stage: not set.
2. **Sample:** a Latin hypercube over the parameters in section 2, inside their bounds, with a fixed, recorded seed. Size: not set, it depends on how many parameters survive.
3. **Successive halving:** every candidate to 15; those whose seed average isn't clearly failing continue to 30; then to 60.
4. **Continue, don't restart:** a survivor resumes from its saved state at 15 or 30 (P0 A4), only once the hash proof has passed. Lean mode, the result cache and parallel light runs apply throughout.
5. **Finalists:** rerun at 20 seeds on the same machine as the rest of M2 (the node), paired with the baseline; an effect only counts above 2 standard errors. Judge them with the gate in PROTOCOL.md section 9 (`paired.band_move`): no target further from its band by more than 2 standard errors, and at least one closer.
6. **Label** the result "calibrated" in the species file, with the fit and the validation.

## 5. The cut rule

**Written in DECISIONS.md before running. Its numbers aren't set until the ranking and the seed spread are in.**

- A candidate is cut only on its seed average, never on one seed, and only if that average is far outside its target band: outside by more than a margin, which is well above the standard error of that average.
- Early ages are noisy (LAI varies about 30 % at 15), so at stage 15 only height counts for cutting.
- Height is the only metric with a band at all three stages. The approved target applies from age 20, so a band at 15 would be the same curve extended, not an approved target; it's used for cutting only, and only with the wider margin.
- Nothing is cut for being merely in the wrong half of the sample: "successive halving" here means cutting clear failures, not a fixed half.
- **Check on the rule:** a small random sample of cut candidates still runs to 60, to see whether any would have passed. Sample size: not set.
- Report how many were cut at each stage, and the check's result.

## 6. Run budget

Count a run as "full" if it reaches 60. Over 300 full runs: propose an emulator instead of running them. An estimate of the cost per stage waits for the profile.

## 7. Season length

Not designed yet. The readable form is PRELES f_S (Peltoniemi et al. 2015, p. 157), but its printed equation has to be viewed before coding it, its values are for Scots pine, and it needs temperature data the model doesn't have. Measured silver-birch dates exist (Siljansfors: bud burst day 132, leaves full size 168, 50 % fallen 289), against the model's day 130-273, which sets only the sun path today. It lowers yearly carbon at all ages, so heights have to be rechecked with it on.

## 8. Things that could change this design

- The screen may rank few parameters as influential, which makes a small sample enough, or many, which makes the emulator question arrive sooner.
- The profile may show early years are cheap, so stage 15 costs little (not measured yet).
- The second PC's golden hashes decide whether it can carry runs that count, or only exploration.
