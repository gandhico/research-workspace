# Provenance note — CF2 intermittent-hover disturbance (study C)

2026-09-11. Concerns `C_cf2_hover/` and the paper sentence
*"Repeating the study on CF2 with the disturbance scaled by the inertia
ratio gives a 50.2% reduction."*

## What the runs actually used

Both runs record their arguments in `manifest.json`:

| run | created (UTC) | disturbance torque | schedule | mean error | max error | saturation |
|---|---|---|---|---|---|---|
| classical | 2026-09-05 20:02:10 | **0.00015 N m** | intermittent 5 s / 5 s | 0.1412 rad (8.1°) | 0.4818 rad (27.6°) | 0.0000 |
| nengo-nef-pes | 2026-09-05 20:02:36 | **0.00015 N m** | intermittent 5 s / 5 s | 0.0703 rad (4.0°) | 0.2655 rad (15.2°) | 0.0000 |

Reduction 50.2%. Neither run saturated, and peak errors are comparable to
the X2 study (18.8° / 11.3°), so **the comparison is valid** — both
controllers held attitude.

## What was wrong

1. **The driver disagreed with the runs.** `sweep_final_2026_09_05.py`
   line 131 read `"0.004",   # scaled to CF2 inertia` (file last modified
   2026-09-05 13:21 local; runs completed 14:02 local). 0.004 N m is 14× CF2's
   entire per-axis torque limit (≈0.00029 N m) and was never the value that
   produced these results. The most likely sequence is that the sweep had
   already started under an earlier version of the file containing 0.00015,
   and the literal was edited mid-run; a running Python process keeps the
   source it loaded. The exact order cannot be proven from the files, but
   the manifests settle which value produced the results. **Fixed
   2026-09-11:** the line now reads 0.00015, with this history in a comment.
2. **The paper's wording is inaccurate.** The inertia-scaled equivalent of
   X2's 0.15 N m is 0.15 × (J_CF2 / J_X2) = 0.15 × 3.945×10⁻⁴ =
   **5.9×10⁻⁵ N m**. The run used 2.5× that. Per axis, the multi-sine loads
   CF2 to **52 / 42 / 28%** of its torque limits, against **21 / 27 / 35%**
   for X2. Suggested replacement:
   > *"Repeating the study on CF2 with a 0.15 mN m disturbance, which loads
   > its axes to 28–52% of their torque limits (X2: 21–35%), gives a 50.2%
   > reduction."*

## Still affected

The advisor package built 2026-09-05 ships the old line (`0.004`) in
`share/advisor_2026-09-05/ACC2027_advisor_2026-09-05/code/nengo_nef_replication/sweep_final_2026_09_05.py`
and inside both zips. It has not been modified here, because copies have
already been shared. Rebuild and re-share the package, or send a note with
the corrected line, so study C is reproducible from it.
