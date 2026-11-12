# Death by standing: the build (part M)

2026-11-12. Builder: Opus 5.5 (ID `claude-opus-5-5`). Branch `death-by-standing`, made from `stand-structure` (bd59808) with master (90638e4) merged in. Design: `2026-11-12_stand_structure.md`, part M, and its challenge `2026-11-12_stand_structure_challenge.md`. Plan: `2026-11-11_plan.md`, sections 3, 4, 5 and 8. Owner's decisions: DECISIONS 110-117.

CONFIRMED means I checked it in code, on the report's page images or in saved data today. SUSPECTED means I did not. No arm has been run. Section 6 was written before any arm ran.

After the independent check (which passed the build), the same day: its fixes of words and records are made here, in the module's docstring, in the labels and in the species file's comments. No code path changed. Test 6 in section 7 is now one-sided; `by_odds`'s small overshoot is stated (section 1); the survival data's thinned share is no longer claimed (section 3); the line's own data limits are in a label (section 4); how an arm's rule is read is in section 8; what the rule means for runs with regeneration is in section 10. Master (0b49969: the stem-top records and the two thinning switches, the export fix, the hang tools) is merged in, and section 11 gives the checks on the merged code.

## In short

1. There is one new switch, `mortality.rule`. Its default is `crowding`, today's rule. With it off, nothing that grows changes: section 9 gives the server's checks, and section 11 the same checks on the code merged with master.
2. With `mortality.rule: birch_2002`, a plot tree's yearly chance of dying comes from Hynynen et al. 2002's survival model (Eq. 47). The silver birch self-thinning line caps the stems. These replace the crowding, suppressed and background hazards. Old age, snow, wind and the carbon rule stay as they are.
3. Over the line, deaths are raised one of two ways, chosen by `mortality.birch_2002.over_line`. `evenly` is the report's own rule (Eq. 61). `by_odds` is the design's own choice and is labelled an estimate.
4. The rule starts at stand age 12, as the height rule does. Before that, today's rule acts, unchanged. The survival data start at 17 years, so years 12-16 are extrapolated, and so are years 51-60. Each year's record lists the data limits the stand is outside.
5. The equation is coded as printed, including its sign change. Past DBH 16.7 cm, more larger neighbours make a tree *less* likely to die. In today's forest that covers 78 % of trees at 45, 94 % at 50 and 99.5 % at 60.
6. **What I expect (SUSPECTED):** in the model's young stand the line is already reached at about 12-15 years, because of the tangent under 12 cm. The line will then decide who dies for most of 23-60, as the challenge said. "Evenly" will be close to a lottery from about 25 on. "By odds" will remove the small trees. Basal area at 45-60 will probably pass the 28.5 m²/ha guard, and leaf area index at 50 will probably fail its row.

## 1. The formulas as coded (`treegen/death_by_standing.py`)

I read every equation below on the report's page images, pp. 21-24, 30-31, 50-51 and 53-58 (CONFIRMED). I pulled the scanned page images out of the PDF with a PDF library, and used the text layer only to find pages. I ran nothing from the file.

**Eq. 47, Table 32 (pp. 50-51), row "Deciduous, SC1-8":** the chance that a tree dies of within-stand competition during the coming five years.

    p5 = 1 / (1 + exp(x)),   x = a0 + a1·d_s + a2·RDFL + a3·d_s·RDFL
    a0 = 3.014, a1 = 0.1015, a2 = −9.313, a3 = 0.4073
    d_s = 2.0 + 1.25·d                     stump diameter, cm (Eq. 3 p. 22); d = DBH over bark, cm
    RDFL_i = Σ over trees j with d_j > d_i of ga_j   (Eq. 23 p. 31; all trees of the plot, each standing for 10⁴/area stems a hectare)
    ga_j = 1 / N(d_s,j),  ln N = 14.1979 − 2.2178·ln d_s    (Eqs. 20-21 pp. 30-31; silver birch, Eq. 50, Table 34 p. 53)

**The yearly hazard (DERIVED).** A five-year chance p5 is a constant hazard of h = −ln(1 − p5) / 5 a year. The code works it out as softplus(−x) / 5, which is the same number without rounding loss. A year's chance of dying is 1 − exp(−h). Five such years give p5 back.

**The line (pp. 53-58).** This is the maximum number of stems a hectare at the stand's mean stump diameter.

    D_g  = Σ w·d³ / Σ w·d²   (mean DBH weighted by basal area, p. 9), over trees with a DBH; w = each tree's chance of living the year under Eq. 47
    D_gs = 2.0 + 1.25·D_g                                (Eq. 52 p. 55)
    N_max = exp(14.1979 − 2.2178·ln D_gs)             for D_gs ≥ 12 cm   (Eq. 50, Table 34)
    N_max = N(12)·(1 − 2.2178·(D_gs − 12)/12)          for D_gs < 12 cm: the tangent at 12 cm (pp. 56-57); N(12) = 5,924.6/ha

**How the report applies it (p. 55, steps 1-6).** First Eq. 47 gives every tree its chance. Next the stems at the end of the 5-year step are counted after those deaths. Then D_gs at the end of the step is computed. If the stems are over N_max, every tree's stem number is multiplied by N_ratio = N_max / N (Eqs. 57 and 61, p. 58). One step may cut stems by at most 1.5 times what the line's own slope gives for the change in D_gs (p. 57). The report gives the reason for that limit: inventory plots, small or angle-gauge, whose stem numbers are imprecise.

**How the code applies it.** The model's step is a year, and deaths are drawn after the year's growth, damage and carbon deaths, as today. Each year:

1. Eq. 47 for every living tree, plus the old-age hazard as today (zero while `damage.old_age` is on, as it is for birch). The report also adds the two (Eq. 45).
2. N = the expected number of trees with a DBH that live the year: Σ exp(−h_i). D_g is weighted by the same chances, so the check sits where the report's does, at the end of the step after Eq. 47.
3. If N is over N_max (in trees on the plot), deaths are raised until the expected survivors equal N_max:
   - `evenly`: every counted tree's chance of living the year is multiplied by N_max / N (Eq. 61). That is one added hazard, ln(N / N_max), the same for every tree.
   - `by_odds`: every counted tree's five-year odds of dying, p5 / (1 − p5), are multiplied by one factor k. That is Eq. 47 with a0 lowered by ln k for every tree that year. k is found by bisection. It is not the same as multiplying every tree's yearly hazard by one factor (the design's row for M words it that way); the two differ for trees with a high chance of dying.
   - The two ways do not land in the same place. Both aim at the line read at the D_g before the raise. `evenly` raises every tree alike, so D_g does not move and the expected survivors land exactly on the line. `by_odds` takes mostly small trees, so D_g rises and the line, read again after the deaths, falls a little: the stand is left a little over it. On the control's 20 plots, made 10 % over the line by arithmetic, the check found it left at 1.001 / 1.008 / 1.013 / 1.009 / 0.997 of the after-death line at 20 / 30 / 45 / 50 / 60 (largest 1.017), so about 0-2 % over (the check's figures, CONFIRMED as arithmetic by the check; how large it is in a real run is SUSPECTED). On a made-up stand of two sizes it was 1.11. I chose to state this, not to iterate D_g until it settles: the overshoot is under the line's own scatter between stands (about 16 %, section 3), and an iteration would change which trees the arm kills for a gain inside that scatter. The next year's check starts from the stand as it is, so any overshoot is taken then if the line still binds.
4. One uniform random number a tree decides whether it dies. A second one, for each tree that dies, picks the cause in proportion to its hazards: "competition" (Eq. 47), "self-thinning line" or "old age".

There are two settings for the report's own procedure. Neither is used by default:
- `line_every_years`: 1, the yearly check. 5 gives the report's spacing.
- `line_cut_limit`: null. 1.5 gives a reading of the report's limit, not the limit itself. It holds expected survivors at no fewer than this year's counted stems less 1.5 times the line's fall since the last check. The report measures a step's whole fall from the stems at the step's start, so with `line_every_years: 5` the two differ by what Eq. 47 alone took in between.

**Shared with the height rule (`treegen/height_status.py`, H).**
- Functions used by both rules: the stump diameter (`stump_cm`), the line (`self_thinning_stems`), the growing space (`growing_space`) and RDFL (`rdfl`).
- Values read by both rules, from `plot.height_status.birch_2002`: `stump_a_cm`, `stump_b`, `self_thinning_b0` and `self_thinning_b1`. There is one copy, so the two rules can never read two different lines. The species file says so in both blocks.
- The two differences are deliberate:
  - H holds RDFL at the height data's 1.567 (Table 5). Survival does not, because the survival data's RDF range is not printed.
  - The line's D_g is weighted by the chance of living the year (the report's step 3). H's D_g is not weighted.

## 2. Decisions

| Question | Decided | Why |
|---|---|---|
| From when the rule acts | From stand age 12 (`start_age_years: 12`), with no top-height condition (`start_top_height_m: null`). It stays on once started. Before that, today's crowding, suppressed and background hazards act, unchanged | The design proposed 12 (its question 3), and 12 is H's own start. If M started at the data's 17 years or 12.3 m (about age 23 in the model), today's rule would remove H's late trees from 12 to 17-23. That is what stopped H in step E (25.8 % a year for the smallest fifth at 20-25). Years 12-16 lie outside the survival data and are labelled extrapolated. `--set mortality.birch_2002.start_age_years=17`, or `start_top_height_m=12.3`, starts the rule at the data |
| Order in the year | The deaths are decided at the end of the year, after growth, damage (snow, wind, old age) and the carbon rule, as today's rule is. The plot year (the stand's age then) is the age the start reads. The rule's first deaths come at the end of year 12. H's first status-set step is season 13 | This keeps the call where today's rule is, so the off path is untouched |
| A tree with no DBH (under 1.3 m) | It takes d = 0, so d_s = 2.0 cm by Eq. 3, and every tree with a DBH counts as larger (its RDFL is the stand's RDF). It is not counted in the line's stems, and the line never raises its hazard | The report's inventories count trees past breast height, and it handles smaller trees with a separate ingrowth model (pp. 31-32). Eq. 47 at d = 0 is an extrapolation: no diameter range is printed. It is harsh. Under a stand at RDF 1.02, such a tree dies at 66 % a year (section 2a). In today's forest (the control's 20 plots) 2 living trees have no DBH at 11 and none from 15 (the check's count). With regeneration on it would matter: section 10 |
| The random stream | The plot's own mortality stream, `mort_rng`, seeded [seed, 5381], which today's rule already uses. Each year: one uniform for every living tree, in the plot's order, then one more for each tree that dies, to pick its cause. Before the start, today's draw is unchanged | A run repeats exactly from its seed. The records take no random numbers |
| The sign change past DBH 16.7 cm | Kept as printed. The crowding term is (a2 + a3·d_s)·RDFL. It is negative while d_s < 9.313 / 0.4073 = 22.87 cm, that is DBH < 16.69 cm. Past that size, more larger trees make death less likely. Each year's record gives `flip_dbh_cm` and the share of stems past it | The report prints it; I did not refit it. The challenge's reading is that the data's thick trees were probably dominants with RDFL near 0, so this corner was likely never fitted (SUSPECTED). Its effect is small in absolute terms (section 2a: 0.063 % against 0.027 % a year), but under `by_odds` it makes the thickest fifth die faster than the fourth at 50-60 (the challenge: 3.1 against 2.4 % a year) |
| Over bark, rounding | DBH over bark (tools/bark.py), to 0.01 cm. Height to 0.001 m | The Finnish data are over bark. These are the values a tree list holds, so a record can be re-read from one |
| Whose line | The silver birch line for every tree | The survival data pool silver and pubescent birch; the report gives each species its own line. The model grows only silver birch |
| The yearly check | Each year, after growth | This is the yearly version of the report's end-of-step check. Checking every 5 years would remove five years of excess in one year, a pulse of deaths the light field would feel. `line_every_years: 5` is there for anyone who wants it |
| The 1.5-times limit | Off | Its stated reason, imprecise stem numbers from inventory plots, does not hold for a plot where every tree is counted. It also limits what the rule can take in the year it starts, if the stand starts over the line. K's stands are at 0.96 of the line at 11, and the one small check plot at 1.03 (sections 6 and 9), so the limit would act at most in the first year or two. `line_cut_limit: 1.5` turns it on |
| The neighbourhood's relative density in the yearly stats | Still computed and printed (`relative_density`), as a reading only. Under the new rule it kills no tree | The field keeps its meaning across arms |

### 2a. Trees worked by hand (from the report's coefficients; these are the unit tests' numbers, CONFIRMED)

| Tree | DBH, cm | d_s, cm | RDFL | x | p5 | Hazard a year | Chance a year |
|---|---|---|---|---|---|---|---|
| Small, nothing larger | 3 | 5.75 | 0 | 3.597625 | 0.026659 | 0.005404 | 0.54 % |
| Small, overtopped | 3 | 5.75 | 0.8 | −1.979195 | 0.878595 | 0.421725 | 34.4 % |
| Middling | 10 | 14.5 | 0.4 | 3.122890 | 0.042173 | 0.008618 | 0.86 % |
| Large, nothing larger | 20 | 27.0 | 0 | 5.754500 | 0.003158 | 0.000633 | 0.063 % |
| **Large, past 16.7 cm, with larger trees** | 20 | 27.0 | 0.5 | 6.596550 | 0.001363 | 0.000273 | **0.027 %: lower than with none** |
| Large | 30 | 39.5 | 0.2 | 8.378320 | 0.000230 | 0.000046 | 0.005 % |
| No DBH, under ten 20 cm trees on 100 m² | 0 | 2.0 | 1.019551 | −5.447552 | 0.995712 | 1.090370 | 66.4 % |

The past-16.7 cm tree, step by step: x = 3.014 + 0.1015 × 27 − 9.313 × 0.5 + 0.4073 × 27 × 0.5 = 3.014 + 2.7405 − 4.6565 + 5.49855 = 6.59655. With RDFL 0 the same tree has x = 5.7545. A larger x means a smaller p5.

The cap on an even stand, by hand: 150 trees of 20 cm on 1,000 m² (1,500 a hectare). D_gs is 27, so N_max is 980.82 a hectare, or 98.08 trees. Eq. 47 alone leaves 149.905 expected survivors.
- Evenly: an added hazard of ln(149.905 / 98.082) = 0.4242 a year.
- By odds: ln k = 7.7513. On an even stand both give each tree the same total hazard, ln(150 / 98.082) = 0.4248.

## 3. The limits of the paper's data, and where the model runs outside them

The survival data (p. 24, CONFIRMED on the page):
- five experiments, permanent plots in planted or naturally regenerated stands of silver and pubescent birch on fertile mineral soils;
- in the source's words, "Thinning experiments included untreated control plots." The page does not print how many plots were thinned and how many were controls. That most were thinned is the challenge's reading, an inference;
- one 5-year period from each stand: 7,427 trees, of which 476 died (6.4 %);
- plot mean age 17-50 years, dominant height 12.3-22.4 m, 370-3,051 stems/ha.
- Not printed: a diameter range, an RDF range, or the number of stands.
- The coefficients are for "Deciduous", every fertility class (Table 32).

The line's data (Tables 8 and 11, pp. 21 and 23, CONFIRMED on the pages):
- untreated control plots only, accepted only where stems had fallen in the period before;
- silver birch: 10 stands, 17 plots, 59 observations;
- age 15-109, dominant height 9.9-29 m, 572-6,484 stems/ha, D_g 7.4-25.5 cm, basal area 14.9-29.1 m²/ha;
- between-stand SD of ln N 0.160 (Table 34), so the line itself scatters by about 16 % in stems from stand to stand;
- under D_gs 10 cm the data are thin; the report uses the tangent below 12 cm for that reason (p. 57);
- these limits are now also in the label of `line_tangent_below_cm` and in the species file's comment on it. The cap first binds at about 12-15 years, at D_g about 3 cm and about 13,000 stems/ha: outside these data, on the tangent.

**Where the model runs outside them.** The first five rows are the control K's stands, 20 plots (`node_t2_k`), read with the rule's own functions with no feedback (CONFIRMED arithmetic). The last row is SUSPECTED.

| Limit | 12 (K at 11) | 15 | 20 | 30 | 45 | 50 | 60 |
|---|---|---|---|---|---|---|---|
| Age 17-50 | outside | outside | in | in | in | in | **outside** |
| Top height 12.3-22.4 m (approved; K's value) | outside (4.2) | outside (7.1) | outside (10.4) | in (15.2) | in (20.3) | in (21.4) | **outside (23.1)** |
| Stems 370-3,051/ha (K's) | outside (13,752) | outside (13,220) | outside (9,324) | in (2,640) | in (846) | in (667) | in (474) |
| Stems past DBH 16.7 cm, where the crowding term turns over (K) | 0 | 0 | 0 | 0 | 0.78 | 0.94 | 0.99 |
| The line's own data: D_g at least 7.4 cm, stems at most 6,484 (K) | outside | outside | outside | in | in | in | in |
| Under M (SUSPECTED) | as K | as K | stems higher, on the line | stems 4,000-5,500: outside | in | in | age and top height outside |

So:
- Under M, stems stay above 3,051/ha until D_gs passes 16.2 cm (D_g 11.3 cm). On K's growth that is about age 33-35; in a denser stand, later.
- In the arms the rule runs inside all three printed limits only from about 35 to about 50 (SUSPECTED).
- It always runs on a pure, unthinned, self-sown stand. The data are thinning experiments with untreated controls (the share of each is not printed), planted and self-sown.
- The records' `outside_data` field names, for every plot-year, which limits apply.

## 4. Sourced, derived and estimated (labels in `reference/betula_pendula/labels.yaml`)

| Value | Label |
|---|---|
| `a0` 3.014, `a1` 0.1015, `a2` −9.313, `a3` 0.4073 | **sourced**: Eq. 47 p. 50, Table 32 p. 51, read on the page image. Holds for deciduous trees pooled, all fertility classes, in the data above. The label states the limits and the sign change |
| `period_years` 5 | sourced, p. 50. The yearly hazard is DERIVED from it |
| `line_tangent_below_cm` 12 | sourced, pp. 56-57. Its label also holds the line's own data limits (Table 11 p. 23) and says the cap first binds outside them, on the tangent |
| `data_age_years`, `data_top_height_m`, `data_stems_per_ha` | sourced, p. 24. They only flag extrapolation in the records |
| `over_line` | A choice. `evenly` is the report's own rule (Eq. 61, sourced). `by_odds` is the design's own: an estimate with no source. The label says `by_odds` leaves the stand about 0-2 % over the after-death line (section 1) |
| `line_every_years` 1 | estimate: the yearly version of the report's 5-yearly check |
| `line_cut_limit` null | off; the report's value is 1.5 (p. 57). 1.5 here is a yearly reading of the report's limit, not the same limit (section 1) |
| `start_age_years` 12, `start_top_height_m` null | estimate: the design's proposal and H's start; outside the data's 17 years |
| The line's 14.1979 and −2.2178, the stump diameter's 2.0 and 1.25 | Unchanged, already sourced under `plot.height_status.birch_2002`. I read Eq. 3 on the page image (p. 22) today; its label still says the text layer only. Changing that label is left to the owner |

No existing species value changed. Each new name is in `treegen/names.py`, in order. No new value is TUNED.

## 5. Records (with `log.stand` on; none otherwise)

In `stand_log.json`, each row (a plot year) holds `death_rule` when `mortality.rule` is `birch_2002`. The file also holds `death_rule_what`, which describes every field. A default run's files are unchanged, because the key is written only when a row has the record.

- **Every year, before and after the start:**
  - the stems with a DBH a hectare, and the trees with none;
  - D_g, D_gs, RDF, the line's stems (`line_stems_ha`) and the share of the line held before the year's deaths (`line_share`);
  - the expected survivors under Eq. 47 alone;
  - the top height read, the share of stems past the sign change, and `outside_data`;
  - the deaths by cause.
- **Every year from the start:**
  - whether the line was checked and whether it bound;
  - the stems it allowed (`line_target_ha`);
  - the added hazard (evenly) or ln k (by odds);
  - the expected deaths the line added (`line_added_deaths_expected`) and the deaths drawn with the line as their cause (`deaths["self-thinning line"]`).
- **Per tree and year, from the start:** id, the DBH read, RDFL, Eq. 47's p5, the total hazard a year, the hazard the line added, and `raised` (1 where the line raised it). This adds about 2-3 MB a plot (SUSPECTED, from the tree-years).

## 6. What I expect, written before any arm ran (SUSPECTED throughout unless marked)

**A desk preview on K's own stands (CONFIRMED as arithmetic; reading it as a forecast is SUSPECTED).** This is the rule's own code on the 20 control plots' tree lists, with no feedback. Yearly deaths, %, by fifth of DBH, smallest first.

| Age | K's stems/ha | K's share of the line (tangent under 12 cm) | Eq. 47 alone, all | Eq. 47 alone, by fifth | With the cap: evenly / by odds, by fifth |
|---|---|---|---|---|---|
| 11 | 13,752 | 0.96 | 1.8 | 2.8 / 2.3 / 1.7 / 1.2 / 0.8 | under the line |
| 15 | 13,220 | **1.05** | 3.9 | 8.7 / 5.5 / 3.1 / 1.6 / 0.8 | 10.1 / 6.9 / 4.7 / 3.2 / 2.3; 11.6 / 7.6 / 4.5 / 2.4 / 1.2 |
| 20 | 9,324 | 0.87 | 4.6 | 11.2 / 6.2 / 3.2 / 1.6 / 0.7 | under the line |
| 25 | 5,078 | 0.64 | 2.9 | 7.4 / 3.8 / 2.0 / 1.0 / 0.5 | under the line |
| 30 | 2,640 | 0.65 | 1.5 | 3.9 / 1.8 / 0.9 / 0.5 / 0.3 | under the line |
| 45 | 846 | 0.83 | 0.09 | 0.25 / 0.08 / 0.05 / 0.04 / 0.03 | under the line |
| 50 | 667 | 0.86 | 0.04 | 0.11 / 0.03 / 0.02 / 0.02 / 0.02 | under the line |
| 60 | 474 | 0.95 | 0.01 | 0.02 / 0.00 / 0.00 / 0.00 / 0.01 | 0.2 / 0.2 / 0.2 / 0.2 / 0.2; 0.6 / 0.1 / 0.1 / 0.1 / 0.2 (some plots over) |

The line's own fall along K's diameter path is my arithmetic from the same line values: 3.0 % a year at 11-15, 3.2 % at 15-20, 5.8 % at 20-25, 12.6 % at 25-30, 8.8 % at 30-45, 5.4 % at 45-50 and 4.3 % at 50-60. A stand on the line must lose that much. The tangent explains the jump at 25-30: D_gs passes 12 cm there and the curve steepens.

**What this says, beyond the design and the challenge.**
- The model's young stand reaches the line much earlier than the design thought. It is at 0.96 of the tangent line at 11 and at 1.05 at 15. The design assumed about 25-30, and the challenge 25.
- So under M the line probably binds first at about 12-15. In the server's one small check plot it bound at 12 and 13 (section 9).
- It may then let go at about 16-22. There Eq. 47 alone, in a stand denser than K's, takes 4-6 % a year, more than the 3.2 % the line needs.
- It binds for good from about 23-27, when the line's need rises to 6-13 % a year.
- Eq. 47 alone therefore decides who dies only in years 12-13 and roughly 16-22. That is the window in which the small trees can linger. From about 25 to 60 the line decides, as the challenge said. Eq. 47 supplies about 40 % of the deaths at 30-35 and under 1 % at 45-60 (the challenge's figures).

**The arms.** Each cell is 30 / 45 / 50 / 60. Today's row is K, 20 seeds. The rest are forecasts. They take the design's own forecast and the challenge's correction: past about 25 the line, not Eq. 47, decides who dies.

| Arm | DBH SD over mean | Height SD on reported height, m | Stems/ha (share of the line at the year's end) | Basal area, m²/ha | LAI | Light, % | Top height, approved, m |
|---|---|---|---|---|---|---|---|
| Today (K) | 0.13 / 0.14 / 0.15 / 0.15 | 0.85 / 1.04 / 1.06 / 1.09 | 2,640 / 846 / 667 / 474 (0.65 / 0.83 / 0.86 / 0.95) | 18.9 / 24.0 / 24.7 / 26.8 | 5.44 / 4.79 / 4.51 / 4.29 | 16.0 / 17.5 / 18.2 / 19.5 | 15.2 / 20.3 / 21.39 / 23.14 |
| H + M, evenly | 0.17-0.25 / 0.14-0.20 / 0.14-0.19 / 0.13-0.18 | 1.3-2.2 / 1.3-2.0 / 1.3-2.0 / 1.2-1.9 | 4,000-5,500 / 1,000-1,800 / 800-1,400 / 500-950 (0.95-1.0 throughout) | 24-28 / 27-30 / 27-30 / 27-30 | +0.0 to +0.3 on K | −0.5 to −2 points | 50, 60: K's ±0.3, up to +0.9 as in E |
| H + M, by odds | 0.13-0.18 / 0.10-0.14 / 0.10-0.14 / 0.09-0.13 | 1.0-1.5 / 1.0-1.4 / 0.9-1.3 / 0.9-1.3 | as above | 25-29 / 28-30 / 28-30 / 28-30 | +0.0 to +0.3 | −0.5 to −2 | as above |
| M alone, evenly (information) | 0.12-0.15 / 0.12-0.15 / 0.12-0.15 / 0.12-0.16 | 0.85-1.0 / 0.95-1.15 / 0.95-1.15 / 0.95-1.2 | as above | 24-28 / 28-30 / 28-30 / 28-30 | +0.0 to +0.3 | −0.5 to −2 | K's ±0.3 |
| M alone, by odds (information) | 0.11-0.14 / 0.10-0.13 / 0.10-0.13 / 0.10-0.13 | 0.8-0.95 / 0.85-1.05 / 0.85-1.05 / 0.85-1.1 | as above | 24-28 / 28-30 / 28-30 / 28-30 | +0.0 to +0.3 | −0.5 to −2 | K's ±0.3 |

One of these is not a real forecast. For H + M evenly, the DBH spread ranges at 45 / 50 / 60 (0.14-0.20 / 0.14-0.19 / 0.13-0.18) contain today's 0.143 / 0.148 / 0.148, so a run can hardly contradict them (the check's point). Height SD, stems against the line, basal area and when the line binds are real forecasts.

Yearly deaths by fifth on the line. These are the challenge's figures, from K's stand scaled onto the line; they are not mine.
- By odds: 31 / 18 / 9 / 4 / 1.6 % at 30-35, 12.7 / 5.0 / 3.1 / 2.4 / 2.4 at 45-50, 8.7 / 3.5 / 2.5 / 2.4 / 3.1 at 50-60.
- Evenly: 19 / 12 / 9 / 7.5 / 7 at 30-35, about 5 in every fifth at 45-50 and about 4 at 50-60.

**Arm by arm.**
- **H + M, evenly.** H makes late and small trees short. Eq. 47 lets them live while the line is loose (12-13 and about 16-22). This is where the spread is made. Once the line binds, every tree carries the same added hazard, so the small ones are not singled out and they linger. But the dominants also die at 4-5 % a year at 45-60, much as today, so the lottery returns at the top. It is the only arm that might lift DBH spread at 45 and 50 past do-no-harm, and height SD at 45 past E's improvement test. It fails the "large trees safe" test at 45-60.
- **H + M, by odds.** The young window is the same. Once the line binds, the smallest fifth dies at 12-31 % a year, so H's laggards are removed. Spread then falls, as BIRCH's did. It will probably fail do-no-harm on DBH spread at 45 and 50 (0.143 / 0.148 less 2 paired SE). It passes "large trees safe" at 30-50 and is borderline at 50-60 because of the sign change.
- **M alone, either way.** Heights still follow the draw, so selection from below can only narrow the spread. Evenly keeps it near today's; by odds lowers it. Both are information about what M does without H.
- **Every arm with M.** Stems sit on the line, which the design meant to happen. The rows likely to fail:
  - **basal area** at 45-60, over the 28.5 guard: a stand on the line carries about 29 m²/ha at a spread of 0.15 (the design's arithmetic);
  - **LAI at 50**, already 0.01 over 4.5: more stems, more leaf;
  - **LAI at 60**, likely: 0.21 of room.
  - Light falls, which the light row allows.
- **Top height**, the approved one (DECISIONS 111: no lower beyond noise). I expect no fall. H keeps the dominants on the curve, and a denser stand's 100 thickest are a smaller, more selected share. It must be printed, at 50 and 60.
- **Turnover.** More stems at the same growth mean more stem wood dies. The design's "fast turnover" stays SUSPECTED, as the challenge said; M does not test it.

## 7. The tests a run must pass if the mechanism is right (restated as the challenge asked)

Read on H + M, each way. Each threshold is my estimate, set here before any run. "Before the line binds" means the plot-years whose record says `line_binds: false` after the start (12-13 and any later loose years). "After" means the years whose record says `line_binds: true`.

| Test | Read how | Must be true | Today (K) | Expected |
|---|---|---|---|---|
| 1a. Lingering, before the line binds | Trees that grew less than half the plot's mean diameter growth the year before (from the per-tree DBH in the records): their yearly death rate | At most half of today's rate for the same class, 28 % a year at 23-30. K's tree lists give no yearly reading before 22, so 23-30 is the only one | 28 % a year | Both ways: 10-20 % a year. Pass |
| 1b. Lingering, after it binds | The same class, the same rate | Evenly: at most 0.6 of today's. By odds: printed. By design it cannot pass, and that is said, not hidden | 28 % | Evenly 15-25 %: borderline. By odds over 25 %: fail |
| 2a. Large trees safe, before the line binds | The thickest fifth's yearly death rate over the smallest fifth's | At most half of today's ratio in the same period | 0.54 at 20-25 | About 0.06 (Eq. 47). Pass |
| 2b. Large trees safe, after it binds | The same ratio at 30-35, 45-50 and 50-60; and the dying tree's mean diameter over the plot mean | The ratio at most half of today's; the dying tree under 0.8 of the mean | 0.48 / 0.33 / 0.22; 0.96 | By odds: about 0.05 / 0.19 / 0.36 (borderline at 50-60, the sign change), and 0.6-0.8: pass to 50. Evenly: about 0.36 / 0.95 / 0.97, and 0.9-1.0: fail at 45-60 |
| 3. No catching up, on every tree that came up | Year-2 and year-3 germinants' mean DBH over year-0 germinants', at 15, 20 and 30, over every tree that came up: the living at their size and the dead at their last size (tree lists with their dead; the per-tree records from 12) | Does not rise by more than 0.05 from 15 to 30 | On survivors 0.49 → 0.79 for year 3 | H + M: flat or falling, pass. M alone: rises as today, fail; it doesn't touch growth |
| 4. Standing carries, not the draw | Rank at 20 against 45, 50 and 60 with the draw and germination year taken out | Over 0.3, but not counted as evidence for M: BIRCH already gives 0.35 / 0.35 / 0.26 | 0.03 / 0.00 / −0.05 | H + M: 0.3-0.5 |
| 5. Spread falls with age | DBH spread at 20 over 30, and 30 over 45, 50 and 60 | True | It rises after 30 | H + M evenly: probably. By odds: falls, but from a lower level |
| 6. Not over the line | Stems after the year's deaths over the line read after them, every year from 12 | One-sided: not over the line beyond noise (the draw's binomial noise, plus by odds' 0-2 % from section 1) in any year from 12. The line is only a cap: under it Eq. 47 acts alone and may take the stand well below it, as the check plot did (0.87 after the deaths of year 18). This checks the build, not the mechanism | 0.65 at 30 | The lower side is a forecast, not true by construction: about 0.95-1.0 once the line binds for good (about 23-27 on), lower in the years it lets go (about 16-22) |

## 8. Arms for the screen (not run). Each needs only `--set`, no further code

Every arm uses the command today's control forests are run with, stem tops recorded (`log.stem_tops`, from master 0b49969), plus the arm's settings: `tools/forest.py plots --label <label> --seeds 5 --years 60 --area 1000 --tree-lists 11,15,20,22,23,24,25,26,27,28,29,30,33,35,40,42,45,50,60 --set log.stand=true --set log.stem_tops=true`. The exact commands, run as the script and arguments of `tools/node/submit.sh <c> <label>` from a worktree at commit `<c>` of this branch (merged with master, so `log.stem_tops` exists), seeds 1-5. None has been run.

H + M, evenly:

    tools/forest.py plots --label node_m_hm_even_<c> --seeds 5 --years 60 --area 1000 --tree-lists 11,15,20,22,23,24,25,26,27,28,29,30,33,35,40,42,45,50,60 --set log.stand=true --set log.stem_tops=true --set plot.height_status.enabled=true --set 'plot.height_status.rule="birch_2002"' --set 'mortality.rule="birch_2002"' --set 'mortality.birch_2002.over_line="evenly"'

H + M, by odds:

    tools/forest.py plots --label node_m_hm_odds_<c> --seeds 5 --years 60 --area 1000 --tree-lists 11,15,20,22,23,24,25,26,27,28,29,30,33,35,40,42,45,50,60 --set log.stand=true --set log.stem_tops=true --set plot.height_status.enabled=true --set 'plot.height_status.rule="birch_2002"' --set 'mortality.rule="birch_2002"' --set 'mortality.birch_2002.over_line="by_odds"'

M alone, evenly (information):

    tools/forest.py plots --label node_m_m_even_<c> --seeds 5 --years 60 --area 1000 --tree-lists 11,15,20,22,23,24,25,26,27,28,29,30,33,35,40,42,45,50,60 --set log.stand=true --set log.stem_tops=true --set 'mortality.rule="birch_2002"' --set 'mortality.birch_2002.over_line="evenly"'

M alone, by odds (information):

    tools/forest.py plots --label node_m_m_odds_<c> --seeds 5 --years 60 --area 1000 --tree-lists 11,15,20,22,23,24,25,26,27,28,29,30,33,35,40,42,45,50,60 --set log.stand=true --set log.stem_tops=true --set 'mortality.rule="birch_2002"' --set 'mortality.birch_2002.over_line="by_odds"'

For example, the first on the server: `CORES=5 bash tools/node/submit.sh <c> node_m_hm_even_<c> tools/forest.py plots --label node_m_hm_even_<c> ...` with the rest of its line as above. The `--set` values in single quotes reached the server intact in the check plots (sections 9 and 11). With `log.stem_tops` each plot also writes `stem_log.json` and its tree lists a `stem_top_m` column; plot.json, `stand_log.json` and the trees are the same with it on or off (master's tests/test_stem_top.py).

The arms' settings alone:

| Arm | Its settings |
|---|---|
| H + M, evenly | `--set plot.height_status.enabled=true --set 'plot.height_status.rule="birch_2002"' --set 'mortality.rule="birch_2002"' --set 'mortality.birch_2002.over_line="evenly"'` |
| H + M, by odds | `--set plot.height_status.enabled=true --set 'plot.height_status.rule="birch_2002"' --set 'mortality.rule="birch_2002"' --set 'mortality.birch_2002.over_line="by_odds"'` |
| M alone, evenly (information) | `--set 'mortality.rule="birch_2002"' --set 'mortality.birch_2002.over_line="evenly"'` |
| M alone, by odds (information) | `--set 'mortality.rule="birch_2002"' --set 'mortality.birch_2002.over_line="by_odds"'` |

`evenly` is the default, but each arm names its way so the folder's settings say it. An arm's rule is read from `run_manifest.overrides` (and from each tree list's `run` and the `death_rule` record in `stand_log.json`), not from plot.json's `options`: `options` holds only on/off switches, so it shows `mortality.enabled` but neither `mortality.rule` nor `over_line`, which are text. For the same reason tools/switch_off.py does not list the rule among the options that differ. `plot.height_status.rule` has the same gap; it is not new. The control is K (`node_t2_k`, 20 seeds), whose seeds 1-5 pair with each arm. BIRCH (`node_e_s5_birch_6c0ebb6`) is H alone. One variant is information and not proposed: start at the data, with `--set mortality.birch_2002.start_age_years=17`.

Budget: plots to 60 under M will hold more stems at 20-40 than K's. Expect about +10 % in run time and memory, and up to 7.4 GB a plot (SUSPECTED; the challenge put it at 3,500 more tree-years). The per-tree records add about 2-3 MB a plot. `log.stem_tops` adds a row a year and a column to each tree list.

## 9. The switch off: checks (server, commit da97d6a)

All on the server at commit da97d6a (the build; this note's commit changes no code), each job on 1-2 cores. All CONFIRMED.

| Check | Job | Result |
|---|---|---|
| Full tests | `node_m_tests_da97d6a` | 4 failed, 610 passed, 1 skipped (12 min 45 s). The 4 are the known environment failures: test_scorecard_runs, test_birchs_targets_are_read_through_the_approved_tag, test_a_different_version_is_reported and test_this_pc_matches_the_lock_file. The 17 new tests all pass; the slowest takes 0.15 s. No existing test was edited |
| Golden runs | `node_m_gold_da97d6a`: `tools/golden.py record node_m_gold_da97d6a --check`, against the tracked `cases/golden_server.json` (untouched) | IDENTICAL on all eight: tree60 3, mesh30 13, plot25 76, regen10 133, open60 3, forest30 2, tree60_seed2 3 and export30 4 files |
| Switch-off rule, stand trees, seeds 1-3 | `node_m_trees_da97d6a` against `node_t1r_trees_395355d` | IDENTICAL: stats.json, and tree.json in all 997 values both sides have, for each seed. The options that differ are switches added since the control, all off or absent |
| Switch-off rule, plots, seeds 1-2 | `node_m_plots_da97d6a` against `node_t1r_plots_395355d` | IDENTICAL: plot.json for each seed, and the tree lists in all 311,190 (seed 1) and 316,638 (seed 2) values both sides have, over the 19 listed years 11-60 (45, 50 and 60 among them). The options that differ are switches added since the control, all off or absent. Each plot took about 57 minutes, peak 6.7 GB |
| A plot with the rule on (a check of the build, not a screen) | `node_m_smoke_da97d6a`: H + M on one 100 m² plot, seed 1, to 18 years, evenly and by odds | Both ran to the end, and `stand_log.json` holds the records and their description. Before 12, only today's causes: 1 "background" death at 4, 2 at 8, and "suppressed" deaths at 7-10 (2, 5, 3 and 1). The line bound at 12 and 13 (share of the line before deaths 1.077 and 1.064; evenly added 0.037 and 0.016 a year, by odds ln k 0.84 and 0.37; 4.9 and 1.9-2.0 deaths added, expected), then let go at 14-18: Eq. 47 alone took 6-9 % a year, more than the line's fall. The deaths' causes are "competition" and "self-thinning line" only. This is one small plot, so how it behaves on 1,000 m² is SUSPECTED, but it is what section 6 expects |

## 10. Not done, and limits

- No arm was run.
- The rule takes Eq. 47's coefficients for "Deciduous". They are fitted on silver and pubescent birch together, on thinning experiments with untreated controls (the share of thinned plots is not printed), with only 476 deaths. They have no printed diameter or RDF range.
- **Runs with regeneration (SUSPECTED until one is run).** No arm here has regeneration. With it on, the rule would kill almost every seedling and sapling. A tree with no DBH takes d = 0 and the whole stand's RDF as its RDFL, so under a stand at RDF 0.8 it dies at about 51 % a year, and at RDF 1.02 at 66 %. A 1 cm sapling dies at about 46 % a year. This holds anywhere on the plot, gap or not, because RDFL is read over the whole plot, not around the tree. The numbers are the check's arithmetic from the printed equation. What it means: a regeneration run under this rule would show almost no ingrowth, and that would come from applying Eq. 47 to trees the report never fitted it on (it handles them with a separate ingrowth model, pp. 31-32), not from the stand. Such a run needs its own rule for small trees first.
- Its sign change is kept as printed.
- The line's tangent under 12 cm and its use on a self-sown stand of 13,000 stems/ha at 11-15 years are the report's own handling. They are applied here outside the line's data (D_g under 7.4 cm, over 6,484 stems/ha).
- Old age stays as damage's (Elfving 2010), not the report's Eq. 48-49.
- The report's other birch models were not read for this build: basal-area growth, crown ratio and dominant height.
- The desk preview has no feedback: no growth response to more stems, and no light. The forecasts in section 6 are SUSPECTED.
- Every number taken from the challenge is marked as theirs. I re-read the report's equations and tables myself; I did not re-read the other sources the design cites.
- No unit test grows a tree. The plot path is tested on a plot built by hand with fixed trees (`tests/test_death_by_standing.py`). It checks that switched off it takes today's code path and draws, that before the start the rule kills as today, and that after the start it draws from Eq. 47 and the line. Whole plot runs with the rule on are only the server's small runs in sections 9 and 11.
- `by_odds` is not iterated to land exactly on the line it leaves behind (section 1); it is stated instead.
- The records' `outside_data` names only the survival data's three limits, not the line's own (those are in the labels and in `line_stems_ha`'s description).

## 11. The merge with master, and the checks on the merged code (server, commit b478972)

Master at 0b49969 was merged in at b478972 with no conflicts. Both sides kept exactly (CONFIRMED with git): in the four files both sides changed (treegen/plot.py, tools/forest.py, treegen/names.py, the species file) the merged file differs from master by exactly this branch's lines, and from this branch by exactly master's. The species file, the labels, treegen/plot.py, treegen/mesh.py, tools/tree_table.py, DECISIONS.md and QUESTIONS.md keep Windows line endings throughout. `cases/golden_server.json` is master's, byte for byte (the same sha256 here, at master and on the server's copy).

Where the death rule and master's changes meet (CONFIRMED by reading the merged code):
- **Stem-top records** (`log.stem_tops`). A plot year runs: growth, damage, then the deaths (today's rule or this one, both through `Plot._finish`), then the yearly stats, then `log.stand`'s row and the stem-top row. `_finish` keeps the stem top of every tree that goes, whatever killed it, so the death rule's deaths are recorded as any other. The stem-top row is read after the year's deaths, from the trees still living. tools/forest.py writes `stand_log.json` (with `death_rule_what` when the rule is on) and `stem_log.json` as two separate files, side by side.
- **The two thinning switches** (`stand.thinning_stays`, `stand.thinning_on_stem_top`). They change the height at which a tree's thinning schedule is read (`GrowthModel._schedule_height`) and which heights a managed plot's `_thin` reads. The death rule acts only in a natural plot's `Plot._self_thin`, which calls `_death_by_standing`, and reads only each tree's DBH and its yearly row's height (the highest living point, which neither switch changes). It reads no value either switch sets, and the switches read nothing the rule sets. A switch can reach the rule only by changing how the trees grow, which the rule then reads like any other stand.

| Check | Job | Result (all CONFIRMED, read by me) |
|---|---|---|
| Full tests | `node_m2f_tests_b478972` | 4 failed, 678 passed, 1 skipped (13 min 29 s). The 4 are the known environment failures: test_scorecard_runs, test_birchs_targets_are_read_through_the_approved_tag, test_a_different_version_is_reported and test_this_pc_matches_the_lock_file. The 17 death-rule tests and master's new tests (stem tops, golden, hang) pass. No existing test was edited |
| Golden runs | `node_m2f_gold_b478972`: `tools/golden.py record node_m2f_gold_b478972 --check` against master's `cases/golden_server.json` (untouched) | IDENTICAL on all ten: tree60 3, mesh30 13, plot25 76, regen10 133, open60 3, forest30 2, tree60_seed2 3, export30 4, unreal30 12 and usd_open30 10 files |
| Switch-off rule, stand trees, seeds 1-3 | `node_m2f_trees_b478972` (`tools/tree_table.py run --seeds 3 --years 60`) against `node_t1r_trees_395355d` | IDENTICAL: stats.json, and tree.json in all 997 values both sides have, for each seed. The options that differ are switches added since the control, all absent there and off here (the logs, the height rule's, the two thinning switches) |
| Small plots with the rule on and stem tops recorded (a check that the merged code runs and writes its records, not a screen) | `node_m2f_small_b478972`: one 150 m² plot, seed 1, to 30 years, H + M with `log.stand` and `log.stem_tops` on, tree lists at 11, 12, 15, 20, 25 and 30; three scenarios: `even` (evenly), `odds` (by odds) and `even_thin` (evenly, with both thinning switches on) | All three ran to 30 (about 4 minutes each). Each wrote `stand_log.json` with the rule's record in all 30 rows and `death_rule_what`, `stem_log.json` with 30 rows, and tree lists with the `stem_top_m` column. `run_manifest.overrides` names the rule and the way, as section 8 says. Before 12 only today's causes (9 "background", 11 "suppressed"); from 12 only "competition" and "self-thinning line" (evenly 132 and 22; by odds 130 and 25). The line bound at 12 (share before the deaths 1.117; evenly added 0.0696 a year, by odds ln k 1.29; 13.9 deaths added, expected, both), let go from 13 to 27, and bound again at 28-30 (evenly) and 29-30 (by odds). Stems after each year's deaths over the line read after them, from the per-tree records: never over 1.026 (by odds at 29) or 1.002 (evenly), and as low as 0.85-0.87 at 19-24, as the one-sided test 6 allows. At 30: 4,067 and 4,000 stems/ha, top height 15.85 and 15.84 m, basal area 29.8 and 30.1 m²/ha. `even_thin` ran with both switches on and the rule on, and is the same as `even` in every file (plot.json, stand_log.json, stem_log.json and every tree list, leaving out only the run's own metadata and options). In this plot the switches changed nothing at all; at 30 no tree stood over its stem's top by more than 0.3 m (`trees_over` 0) |

What this does not show: how the rule behaves on 1,000 m² and to 60 (the arms, not run); The `even_thin` run shows only that the code runs with both thinning switches on. Why they changed nothing there was traced by the merge's checker: in a plot tree the switches are read only in the soil water balance's leaf area (off in this plot) and in the tree's own yearly row, so in this plot they could not change anything. The small plot's tree lists also hold 4 "failed to establish" deaths before 12 and 1 "snow snap" from 12, from the carbon rule and damage, which act as before. Their own effect on stand trees and managed plots is master's, tested by master's tests, which pass here.
