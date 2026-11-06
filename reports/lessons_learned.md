# Lessons so far, in case we restart

Written 2026-11-06, mid-reset, on the maintainer's point that the worst case is a new project built on what we've learned. These are my judgements from this project, not measured results. Update it as the reset goes on.

## Worth carrying over

| What | Where |
|---|---|
| Targets, with pages and conditions | `reference/targets.yaml`; note the Baltic LAI band has no LAI behind it (Q26) |
| Papers and notes on what they do and don't say | `birch-data`, `reports/research_notes.md`, `reports/birch_knowledge_base.md`, `reports/extracts/` |
| Scoring on many seeds, on one machine | `tools/scorecard.py`, `tools/ensemble.py`, `tools/gate.py` |
| Measures of a tree against real data | `tools/m3_wood.py`, `tools/m3_branches.py`, `tools/m3_crown_compare.py`, `tools/m2_validation.py`, `tools/bark.py` |
| Why the current model flips and stalls | `DECISIONS.md` rows 76-84, `reports/milestone_M2.md` |
| Node setup and its limits | `tools/node_queue_lib.sh`, `tools/node/`, `PROTOCOL.md` section 6 |

## What I'd do differently

1. **Settle the goal first.** "Looks and measures right for a game" and "every value traced to a source" lead to different models. We found the clash after 40 phases and a day of campaign.
2. **Check that the rules let the model change.** The campaign's rules asked for sourced equations, while the model's bud-level values have no birch sources. So no default changed in a day of work. If a day passes with no change to the tree, stop and ask why.
3. **Start from whole-tree and stand data.** Published curves already give height, wood and stand density. Use them as the frame, and let bud-level rules decide shape, competition and what dies.
4. **Avoid hard on-off switches, and give the tree some carbon carry-over from the start.** Stomata shutting at one value, rings paid first, a 3-node threshold and a 21 % death line combine to flip whole years and make the model chaotic. This is my reading; the carry-over hasn't been tested.
5. **Look at a render after every real change.** The numbers can look close while the tree is still a pole with tufts.
6. **Use many seeds, and more than one draw, from day one.** One seed misled me more than once, and M1's 20 seeds were a low draw for leaf area.
7. **Check means for outliers, and check units.** Two seeds with a changed stem made branches look too long. Wood-only diameters against over-bark sources made stems look too heavy.
8. **Build for species and the game from the start:** species as data, bark and opacity ageing, and the export format, rather than adding them later.
9. **Keep reviews in proportion:** checks at milestones and before adoption. Six review rounds in a day found real errors, but they don't change the tree.
10. **Say early when something's stuck.** I kept running tests inside a blocked setup instead of raising it. That cost the most.
