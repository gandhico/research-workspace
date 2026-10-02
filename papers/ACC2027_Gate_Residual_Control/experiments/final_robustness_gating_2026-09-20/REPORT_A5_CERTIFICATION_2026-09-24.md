# Amendment A5 (controller-family portability): complete certification (2026-09-24)

Closes the experimental phase of the controller-portability study. Companion to `PREREGISTRATION.md` section 14 and
`REPORT_NEURON_BASIS_CORRECTION_2026-09-24.md` (the other closed study this session). Every number here was produced
in this repository; nothing is asserted without a check landing on it.

## 1. What was built, and why it needed no new control theory

`AdvancedBaseline` (`nengo_nef_replication_2026-08-29/run_mujoco_nef_baselines.py`, archived, unmodified, carried from
Gandhi's Aero 2 implementations) already implements LQR, backstepping, SMC, MPC (unconstrained finite-horizon), and
NMPC (grid receding-horizon) behind one interface: `torque(t, eq, omega, q_meas) -> tau0`. The sealed
`run_final_robustness.py` already imports and uses this class, hard-coding `args.baseline = "backstepping"`. Every
other property of the residual architecture (Prop. 1's boundedness and exact recovery, the paired-current encoding,
the PES decoder, the saturation-aware gate) is stated and proved for *any* `u0`; nothing in Sec. III-V assumes how
`u0` was computed. Consequently, extending Stage A (interface portability) to the other five families required no
new theory and no new controller code -- only making the already-hard-coded choice CLI-selectable, plus porting the
same file's own PID (conditional-integration, rotor-level anti-windup) path.

## 2. Code inventory (nothing archived edited; every diff exact and re-verified today)

| File | Base | Change | Verified |
|---|---|---|---|
| `run_controllers_gated.py` | exact copy of sealed `run_final_robustness.py`, 7 named patches | baseline family, bw_scale, rate_ff, model_ff, ki_factor/antiwindup, and the SMC/MPC/NMPC sub-parameters become CLI-selectable; PID path ported from `run_mujoco_nef_baselines.py`'s own `run()` | default flags reproduce the sealed runner exactly: summary metric match + 0-line trace.csv diff (section 3) |
| `run_campaign_a5.py` | new | 100-run driver (5 new families x 2 platforms x 5 missions x 2 arms) | one real bug found and fixed same day: the output-gate flag was applied unconditionally, breaking the classical (no-augmentor) arm; the CMG arm was unaffected throughout (it needs the gate) -- caught within 30s of first launch, not silently wrong |
| `run_campaign_a5_backstepping.py` | new | runs backstepping through the identical new pipeline instead of reusing old sealed data, for one uniform source across all six rows | all 20 cells match the sealed `run_final_robustness.py` data at **relative deviation 0.00e+00** (bit-exact), not just close (section 4) |
| `certify_beta0_recovery.py` | new | empirical check of Prop. 1(iii) (exact recovery at beta=0) for LQR, SMC, MPC, and NMPC (both of its anomalous missions) | all 5 cases: **relative deviation 0.00e+00** (section 5) |
| `analyze_a5.py` | new | builds the results table from the uniform pipeline (no longer mixes an old data source for one row) | -- |

## 3. Certification 1: the new runner's default behavior is byte-identical to the sealed one

With every new CLI flag omitted, `run_controllers_gated.py` and the sealed `run_final_robustness.py` were run on the
same cell (X2 Hard45, classical, 5s): the summary metric matched exactly and `diff` on the full 1001-row trace.csv
returned **zero differing lines**. This is the load-bearing check for everything that follows -- it means nothing
about the frozen ACC baseline changed by building this extension.

## 4. Certification 2: backstepping through the new pipeline reproduces the sealed data exactly, all 20 cells

`run_campaign_a5_backstepping.py` ran backstepping (classical and CMG-gated) through the *same* new pipeline the
other five families use, then diffed every cell against the already-published `results/final_nominal.csv`:

```
worst relative deviation across 20 cells (2 platforms x 5 missions x 2 arms): 0.00e+00
```

Every single cell, bit-exact. The A5 table (section 6) now has one uniform source for all six families, not five new
plus one reused.

## 5. Certification 3: exact recovery at beta=0 holds for the new families, empirically, including the anomalous one

Proposition 1(iii) is proved once, in general (Sec. V), for any baseline satisfying the stated assumptions --
`AdvancedBaseline` was never a special case requiring re-proof. This check confirms the *implementation* does not
violate that proof for controllers it was never run against before today:

```
family  platform  mission      classical      CMG beta=0    rel diff
lqr     x2        hard45      15.654757275   15.654757275   0.00e+00
smc     cf2-rotor hardstep   772.179640800  772.179640800   0.00e+00
mpc     x2        full3       18.259169930   18.259169930   0.00e+00
nmpc    x2        roll         0.386120410    0.386120410   0.00e+00
nmpc    x2        yaw360       3.949386716    3.949386716   0.00e+00
```

All five: bit-exact. NMPC's two cases were chosen deliberately -- Roll and Yaw360 are exactly the missions where
NMPC's beta>0 result was anomalous (section 6). The exact match here at beta=0 isolates that anomaly as a *dynamic
interaction of the learning residual at nonzero authority*, not an architectural or implementation violation: the
bounded-interface guarantee holds regardless of what happens when learning is switched on.

## 6. Full results (all six families, one pipeline, geometric mean over 5 missions)

| family | X2: baseline -> +CMG [mrad] | X2 Delta | CF2: baseline -> +CMG [mrad] | CF2 Delta |
|---|---|---:|---|---:|
| PD+ff (backstepping) | 4.544 -> 2.850 | **+37.3%** | 3.765 -> 2.921 | **+22.4%** |
| PID+ff (ki=.3, rotor anti-windup) | 3.725 -> 2.359 | +36.7% | 3.125 -> 2.427 | +22.4% |
| LQR | 4.634 -> 3.190 | +31.1% | 5.768 -> 4.478 | +22.4% |
| SMC | 6.275 -> 3.527 | **+43.8%** | 5.342 -> 3.919 | **+26.6%** |
| MPC (unconstrained) | 5.180 -> 3.450 | +33.4% | 6.401 -> 4.951 | +22.7% |
| NMPC (grid, 100 Hz) | 4.552 -> 4.731 | **-3.9%** | 3.544 -> 2.772 | +21.8% |

Full per-mission table: `results/A5_CONTROLLERS_RESULTS.md`. Findings (unchanged from the first pass, now on a fully
certified, uniform dataset):

1. **Attaches cleanly everywhere** -- no crash, no divergence, on all six families; exact recovery independently
   re-confirmed (section 5).
2. **SMC is the standout**: the only family where CMG gives a large win *on Hardstep specifically* (X2 +34.2%, CF2
   +12.2%, where every other family is flat-to-negative there), because SMC's own baseline is genuinely worse on
   Hardstep (866.9 mrad vs. backstepping's 265.9) -- there is real error left for the residual to remove.
3. **NMPC nets negative on X2** (-3.9%), driven by Roll (+3.8% vs. +59-78% everywhere else) and Yaw360 (-57.9%).
   Mechanism (plausible, not proved): NMPC holds its baseline for 20 simulation steps (100 Hz) while the residual
   updates every step, so it sees a staircase `u0` instead of the smooth signal every other family produces.
4. Unrelated to CMG: LQR and MPC both show a large *baseline* error on CF2 Hardstep (~2100-2200 mrad, ~8x
   backstepping's, rotor-sat 0.83-0.89) -- a linear-quadratic law meeting CF2's small torque limits on a step it
   was not designed for. CMG neither fixes nor meaningfully worsens it there (-0.7%/-1.8%).

## 7. Disposition -- experimental phase closed

Per `CONTROLLER_EXTENSION_DECISION.md`'s own recommendation and my independent agreement (both written before any A5
result existed), this is Stage A (interface portability) only. Stages B (matched-uncertainty/disturbance) and C
(controller-native residual redesign: PID rotor-level anti-windup already done here, but LQR/backstepping model-
mismatch cases, SMC boundary-layer/switching accounting, and true constrained MPC/NMPC integration remain undone) are
next-paper/journal scope, not this ACC submission.

**No further experiments are planned after this report.** Remaining work is entirely write-up: figures, tables, and
the manuscript, drawing on this report, `REPORT_NEURON_BASIS_CORRECTION_2026-09-24.md`, and the existing sealed
campaign's results.
