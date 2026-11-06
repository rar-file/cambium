# What was done about the review of M1c, the audit merge and M2's start

The review is `2026-11-06_M1c_audit_M2start_review.md`. All of this is exploring: nothing has been adopted, and the species file's values are unchanged in master.

| FIX | What was done | Evidence |
|---|---|---|
| 1. `--set` control | Alpha 4.8 and 6.0 by `--set`, 20 seeds, on the node's code. 4.8 equals `base_trees` on every per_year value of all 20 seeds; 6.0 equals the screen's 240 saved values. Noise at 4.79 and 4.81: 3 of 42 cells over 2 SE, about what chance gives | `out/bench/ensemble/m2_controls.txt`, `m2_noise.txt`; `tools/ensembles_identical.py` |
| 2. Claims | Daily report, row 51, `CAMPAIGN.md` reworded; paired table and the 6.0 row added | `reports/daily_2026-11-06.md`; `tools/m2_alpha_report.py`; `out/bench/ensemble/m2_alpha_report.txt` |
| 3. Diagnose | Short-shoot light 0.21, wood shade off, both apical controls x 0.75, shoot cap 0.9 m, the shade thresholds at 0.15: 20 seeds, paired with `base_trees` | `out/bench/ensemble/m2_diagnosis.txt` |
| 4. Plots' rule | Row 52, committed in `48159fd` before any plot result was read. Plots at 3.5 and 4.0 judged by it: neither fits (row 54) | `git log`, `out/bench/ensemble/m2_plots_table.txt` |
| 5. Open window | Alpha 4.6, 5.0, 20 seeds. No value run fits | `out/bench/ensemble/m2_alpha_report.txt` |
| 6. Free slots | Queues within the limit; "What M2 can still do" in `CAMPAIGN.md` | `out/bench/node/m2_evidence/` |
| 7. Height reporting | The table shows position in band and the height band; `--ref` defaults to the tag; young ages in `tools/m2_shape.py`, as information | `tools/ensemble_sweep.py`, `out/bench/ensemble/m2_alpha_table.txt`, `m2_shape.txt` |
| 8. M2 draft | "Certain" gone; per-tree leaf area at stage 30; row 51 says it was logged after the run; 10 seeds to recheck | `reports/M2_design_draft.md`, `DECISIONS.md` row 51 |
| 9. M1c records | `parameter_checks.csv` lines 67-68 `not checked`, line 72 VERIFY; `where` column; rank row; `KNOWN_ISSUES.md`; counts now 25, 23, 13, 10 | `reports/parameter_audit.csv`, `reports/milestone_M1.md` |
| 10. Node evidence | First log lines, launch scripts and `usage.log` copied back | `out/bench/node/m2_evidence/` |

**Marked ASK MAINTAINER:** Q16, Q17 in `QUESTIONS.md`.

**Not done, and why:** the 5-seed per-seed LAI the review asks to copy back wasn't needed, because each lead got a 20-seed run instead.
