Model: claude-opus-5-5 (Opus 5.5)

# C1: desk check of the crown space rule, on saved forests

2026-11-11. Step C1 of `reports/design/2026-11-11_plan.md` (section 4). Read only: no model run, no test, no server, no commit. This is the only file I wrote in the repository. CONFIRMED = I computed it from saved tree lists or read it in code today. SUSPECTED = I did not.

## Verdict: C1 FAILS

| Pass condition (plan section 4, not moved) | 50 | 60 | Result |
|---|---|---|---|
| 1. Summed allowed crown area over the ground at least 0.99 | 0.50 | 0.51 | **FAIL** at both ages, in 20 of 20 plots. CONFIRMED |
| 2. The neighbour changes the limit in at least 10 % of limb directions | 84 % | 84 % | Passes. CONFIRMED |
| 3. A published rule of this form opened and quoted | – | – | Partly. TASS (Mitchell 1975) has this rule. I quote it from García 2014, which I opened at the publisher. Mitchell 1975 itself is not opened, so the primary source is UNVERIFIED |

So C2 (`crown-space`) is not built. The literal rule halves the crown space at 50 and 60. If it were coded it would open the canopy, as P1 would have. That forecast is SUSPECTED.

## 1. The rule, exactly as tried

**Rule.** Each tree has 72 limb directions, 5° apart. Each limb sits at the height of the tree's longest limbs. In each direction the limb reaches either Hemery's radius or the distance to the nearest point where it enters a neighbour's crown at that height, whichever is shorter. The second limit replaces today's 0.575 x mean spacing. Hemery stays as the ceiling, as in the crown design.

**Today's rule (CONFIRMED in code).** It is `growth.py:2286-2292` with `plot.py:393-401`. Reach = min(Hemery radius, 0.5 x 1.15 x sqrt(plot area / living trees)), the same in every direction. `plot.spacing_min_height_share` is null, so every living tree counts.

**How I read a neighbour's crown at a height from the tree lists.** The saved fields are x, y, height, crown base, crown width and DBH.
- A tree's longest limbs sit at z = H - 0.65 x (H - crown base). That is `peak_depth`, with crown length as in `growth.py:2137`.
- Neighbour j's crown radius at height z is (crown width / 2) x the model's own profile at j's depth (H_j - z) / (H_j - base_j). The profile is `growth.py:2293-2299` with `top_share` 0.165, `peak_depth` 0.65, `base_share` 0.4 and `profile_power` 0.8. It is zero above j's top and below j's crown base.
- The limb runs from the stem along a ray. Its limit is where the ray first enters any neighbour's disc. Neighbours are taken at their nearest image, because the plot repeats at its edges.
- Hemery's radius is 0.5 x (0.932 + 0.177 x min(1.1 x wood DBH, 2.4 x H)). Wood DBH is the saved over-bark DBH turned back with the bark equation the tree lists used (`thinning.over_bark_cm`, `bark_double_mm`). A tree with no DBH gets 0.466 m, as in the code.
- The allowed crown area of a tree is pi x the mean over directions of reach². The plot's figure is the sum over its living trees, divided by the plot area.

**Assumptions where the lists say nothing.**
1. Crowns are round and centred on the stem. The saved width is the mean of the x and y extents of all living nodes (`growth.py:3149`). A crown off its stem or a lopsided crown is not seen. SUSPECTED: this overstates overlap.
2. The saved crown width is taken as the width at the widest point.
3. The neighbour's crown is the crown as saved, so one step of the rule from today's crowns. This is the "radius already passed" of the challenge. What the rule settles to over many years is not computed.
4. No live limbs below the crown base. Using the lowest live branch instead changes no figure in this report (checked).
5. No crown base was missing at 30-60 (0 of 20 plots).

**Data.** The 20 saved plots on today's defaults:
- `.claude/worktrees/agent-a44ce00ffda54f4a6/out/bench/ensemble/node_cd2_C` seeds 1-18, and `node_cd2_C2` seeds 19-20;
- tree lists at 30, 45, 50 and 60.

`node_f5_plots` (worktree `agent-a45137b46e1cc8267`) matches them in id, position, height, DBH, crown base and crown width for every living tree, in 80 of 80 plot-ages. CONFIRMED.

## 2. Results (20 plots, mean; plot range in brackets)

| Age | Living trees per plot | Today: allowed area / ground | Rule: allowed area / ground | Paired difference (SE) | Plots at 0.99 or more |
|---|---|---|---|---|---|
| 30 | 264 | 1.035 | 0.587 (0.54-0.64) | -0.449 (0.007) | 0 of 20 |
| 45 | 85 | 1.005 | 0.524 (0.44-0.61) | -0.481 (0.010) | 0 of 20 |
| **50** | 67 | **0.993** | **0.504 (0.44-0.60)** | -0.490 (0.010) | 0 of 20 |
| **60** | 47 | **0.990** | **0.512 (0.41-0.60)** | -0.478 (0.012) | 0 of 20 |

Today's 0.99 at 50 and 60 reproduces the challenge's figure. Using over-bark DBH in Hemery directly, as the challenge did, changes the rule's figure by 0.002-0.004.

| Limb directions at the depth of the longest limbs | 30 | 45 | 50 | 60 |
|---|---|---|---|---|
| **Limit differs from today's by over 5 % (gate: 10 %)** | 94.6 % | 86.7 % | **83.7 %** | **84.4 %** |
| Differs by over 1 % / over 20 % | 97.9 / 73.5 % | 91.9 / 67.6 % | 89.9 / 67.0 % | 89.7 / 66.6 % |
| Wider than today by over 5 % | 31.0 % | 22.2 % | 18.7 % | 20.0 % |
| Narrower than today by over 5 % | 63.6 % | 64.5 % | 65.0 % | 64.4 % |
| Size alone: differs by over 5 % from the same rule with every crown set to today's cap radius | 43.5 % | 40.3 % | 38.3 % | 38.4 % |
| Reach zero: the tree's stem is inside a neighbour's crown at its own limb height (share of trees) | 37.8 % | 37.5 % | 38.9 % | 37.0 % |
| Hemery is the limit: rule (directions) / today (trees) | 31.7 / 4.5 % | 31.7 / 25.4 % | 31.5 / 30.0 % | 31.9 / 30.0 % |

| Crown width allowed, rule over today, by height quartile (shortest to tallest) | 30 | 45 | 50 | 60 |
|---|---|---|---|---|
| Mean | 0.59, 0.57, 0.57, 0.61 | 0.53, 0.52, 0.56, 0.63 | 0.55, 0.50, 0.50, 0.63 | 0.57, 0.50, 0.52, 0.64 |

Reading:
- **The size test fires, unlike P1's.** In 38 % of directions at 50 and 60 the neighbour's own crown, not only where it stands, moves the limit by more than 5 %. The tallest quartile loses least. So condition 2 passes by a wide margin (CONFIRMED).
- **Why condition 1 fails.**
  - The saved crowns already fill the space. Their summed area is 0.95 / 1.02 of the ground at 50 / 60.
  - The mean crown radius is 0.95 / 0.99 of today's cap radius.
  - The mean distance to the nearest stem is 0.99 / 1.00 of that radius.
  - So the nearest neighbour's crown reaches almost to a tree's own stem. Under a rule that forbids entering it, 37-39 % of trees get no reach at their widest point, and the rest lose about half their crown area (CONFIRMED).
- **Condition 1 may be out of reach for any rule of this form.** A rule that forbids crowns to overlap can at most tile the ground at one height, which is 1.0. Round crowns pack to at most 0.91. Today's 0.99 includes the tuned 15 % overlap. SUSPECTED: only a contact rule that lets crowns interlock, or that turns the canopy into exact tiles, can reach 0.99.

**Information only: a variant formed after the literal result.** This is not the rule C1 tests, and it is not offered as a rescue. Where two saved crowns overlap at a tree's limb height, I split the stem gap in proportion to their radii, as a shared contact point in the spirit of TASS's tessellation. That gives 0.975 at 50 (paired -0.018, SE 0.005; 6 of 20 plots at 0.99 or more) and 0.990 at 60 (+0.001, SE 0.008; 12 of 20). It still misses condition 1 at 50. If the maintainer wants it tried, it is a new rule and needs its own written conditions before any read. It is invented (UNVERIFIED) as I wrote it.

## 3. Published rule

| Source | Opened? | What it says |
|---|---|---|
| García O. 2014. Can plasticity make spatial structure irrelevant in individual-tree models? Forest Ecosystems 1:16 | Yes. Open-access PDF from the publisher (link.springer.com, DOI 10.1186/s40663-014-0016-1) | p. 2 of 13: "In TASS, trees have a radially symmetrical potential crown shape with lateral crown expansion stopping at the points of contact, tessellating the plane on a horizontal projection (Figure 2a). The shapes move upward with height growth, modifying the tessellation, and possibly over-topping and eventually causing the death of the smaller trees." p. 3 of 13: "In TASS and in Strigul et al. (2008), the horizontal space is subdivided on an exclusive basis, with the tree having the largest influence function value taking all the resource (e.g., light) available at each point." pp. 2-3: "It is often observed that crowns do not interlock, especially at higher latitudes, and a direct interpretation of the models of Mitchell (1975) and Strigul et al. (2008) is then unrealistic (Fish et al. 2006; Goudie et al. 2009)." |
| Mitchell K.J. 1975. Dynamics and simulated yield of Douglas-fir. Forest Science Monograph 17 (SAF) | No. No copy at the publisher reachable by my tools; I did not use Chrome, since decision 9 is open | The primary rule. UNVERIFIED |
| Strigul et al. 2008; Goudie et al. 2009 (crown shyness, lodgepole pine) | No | Leads only |

What this means for C1:
- A rule of this form is published: lateral expansion stops at contact, in TASS. I have it second-hand from an opened, citable paper; the primary is unopened.
- TASS's contact is between two growing potential shells. It is exclusive, and the taller tree takes the overlap. That is closer to the information-only variant than to the literal rule tested here.
- Both are for conifers. No birch source was found.
- García's own caveat (crowns don't interlock, so a literal reading is unrealistic) bears directly on the 0.99 condition.

## 4. What I checked, and what I didn't

- CONFIRMED: today's rule in code (`growth.py:2240-2249`, `2282-2299`, `2132-2137`, `3149`; `plot.py:388-404`); the profile and Hemery values in `species/betula_pendula.yaml:1763-1786`; `tools/tree_list.py:29-36` (DBH over bark, crown width as the mean of the x and y extents).
- CONFIRMED: every number in section 2, from the saved tree lists, by scripts in my scratch folder (not in the repository).
- Not done: no growth was run, so what the rule does to light, LAI, height or spread is not known. The challenge's forecast, that less crown space opens the canopy, is SUSPECTED here too. Stand trees and open trees were not looked at; the plan keeps C2 to plots.
- No species value, target, test or tracked file was changed.
