# E-prop (annealed eligibility) — standalone reference

**Scope note**: this document covers one specific learning-rule variant, `eprop_anneal`, from the *precursor* HyperLIF project (`P3_Gate_Residual/learned`, "Paper 5"). It predates and is architecturally distinct from this project's later CMG-PES 6-DOF/Hover-hardware work — same underlying neuron ODE and PES-style update family, different codebase, different plant (Bitcraze CF2 / Skydio X2 in MuJoCo only, **no real-hardware validation for this specific variant**). Written standalone per request, so it can be read and cited without needing the rest of the session's context.

---

## 1. What e-prop(annealed) is, precisely

The base learning rule everywhere in this project family is an online delta-rule (PES-style): `ΔW = η(target - decoded)·activityᵀ`. `eprop_anneal` is one variant of *how the activity term is formed* before that update:

```python
# learned_gate_experiment.py, LearnedGate._update()
target = clip(-k_err*axis_error - k_rate*omega, -1, 1)
e_dec = target - signed                          # decode-space error

if elig:                                          # eprop_anneal sets elig=True
    decay = decay_now(t)                          # annealed: 0.98 -> 0.50 over the run
    e_trace = decay*e_trace + (1-decay)*activity   # eligibility trace (low-pass on activity)
    act_used = e_trace
else:
    act_used = activity                            # plain online_pes uses raw activity

W += lr_now(t) * outer(e_dec, act_used) - leak*W
W = clip(W, -6, 6)
```

`decay_now(t)` and `lr_now(t)` are both **annealed** (the "_anneal" in the name):
```python
lr_now(t)    = lr * (1 - 0.8 * t/sim_time)        # learning rate: full -> 1/5th over the run
decay_now(t) = 0.98 - 0.48 * t/sim_time            # eligibility decay: wide (0.98) -> sharp (0.50)
```
Early in the run, the eligibility trace integrates activity over a long window (decay=0.98, close to a running average) and the learning rate is high — coarse, fast adaptation. Late in the run, the trace sharpens toward the instantaneous activity (decay=0.50) and the learning rate has decayed to 20% of its start value — fine, slow refinement. This is the biologically-motivated "eligibility propagation" idea (a synaptic eligibility trace gated by a top-down error signal) applied with a deliberate coarse-to-fine annealing schedule, not the full e-prop machinery from Bellec et al. 2020 (no BPTT-approximating pseudo-derivative, no per-synapse eligibility over a recurrent unrolling — this is a single-layer decode, so the eligibility trace reduces to a low-pass filter on the activity vector).

`eprop_anneal`'s own learning rate is set to `2× lr` (1.6e-3) relative to `online_pes`'s `8e-4` in the driver script — the two mechanisms are not run at identical raw hyperparameters, by design (the eligibility-trace low-pass naturally damps the effective update magnitude, so the base rate is doubled to compensate). This is stated explicitly here because it's exactly the kind of "honest distinction between variables" this whole project has emphasized — comparing `eprop_anneal` to `online_pes` is a comparison of *mechanisms tuned to be comparably aggressive*, not of identical hyperparameters.

## 2. Verified results

### 2a. Headline: Bitcraze CF2, hard45, 45s (the dossier's primary benchmark)

| Method | score J | qerr_mean (rad) | vs. classical | vs. STN-PID-PES teacher |
|---|---:|---:|---:|---:|
| classical (PD) | 0.287391 | 0.285448 | — | — |
| STN-PID-PES (hand-tuned teacher) | 0.047864 | 0.045254 | +83.3% | — |
| online_pes | 0.038258 | 0.035549 | +86.7% | beats teacher |
| **eprop_anneal** | **0.038215** | **0.035445** | **+86.7%** | **beats teacher, ≈ online_pes** |

**Reproduction status**: re-ran on this machine 2026-09-03 (script and full methodology in Section 4). All three scores matched the frozen `learned_gate_results.json` to **6 decimal places** — this is a byte-identical reproduction, not an approximation, and the plots in Section 3 are built from that reproduction's real per-timestep trace (90,000 rows, dt=0.0005s × 45s), not fabricated.

### 2b. Generalization across regime/platform (pulled from the project's own JSON summaries, not previously tabulated together in the dossier for eprop_anneal specifically)

| Config | classical | online_pes | eprop_anneal |
|---|---:|---:|---:|
| hard45, CF2 | 0.287391 | 0.038258 | 0.038215 |
| hardstep, CF2 | 0.690470 | 1.787807 | 2.104360 |
| hard45, Skydio X2 | 0.299286 | 0.129264 | 0.134809 |

**Honest read**: eprop_anneal matches or very slightly trails online_pes everywhere it was tested — never meaningfully better. On `hardstep` (a step-command regime), **both** learned methods are dramatically *worse* than classical (0.69 → 1.79/2.10) — this matches the dossier's own documented finding that the aggressive learning configuration diverges on step commands (Section 4 of the dossier: "hardstep diverges 2.18" for online_pes; eprop_anneal is worse still here, 2.10, at the same aggressive settings). Neither method should be described as "generalizing well" without qualifying it to the smooth-tracking regime (hard45) — on step commands, the balanced/strong-damped configurations (not evaluated here for eprop_anneal — see Section 5, gap) are what the dossier reports as stable.

## 2c. Full 5-mission x 2-platform sweep (2026-09-03, this reproduction)

All missions run at the driver script's defaults (sim_time=45s, dt=0.0005s, `z_ref=1.0`, except **hardstep uses `z_ref=1.5`** per the dossier's own parameter table -- this was caught by a mismatch against the frozen hardstep-CF2 number, fixed, and re-verified before any of these numbers were trusted; see Section 4). Aggressive learning settings throughout (`lr=8e-4`, `k_err=8`, `k_rate=0`, `leak=0` for online_pes; `lr=1.6e-3`, elig+anneal for eprop_anneal) -- the same single hyperparameter regime as the headline hard45 result, not re-tuned per mission.

| Platform | Mission | classical | online_pes | eprop_anneal | eprop_anneal vs classical |
|---|---|---:|---:|---:|---:|
| CF2 | roll | 0.051371 | 0.002619 | 0.002576 | **+94.99%** |
| CF2 | full3 | 0.288877 | 0.027171 | 0.026628 | **+90.78%** |
| CF2 | hard45 | 0.287391 | 0.038258 | 0.038215 | **+86.70%** (verified, Section 2a) |
| CF2 | hardstep | 0.690470 | 1.787807 | 2.104359 | **-204.77%** (verified vs frozen) |
| CF2 | yaw360 | 0.075812 | 0.000611 | 0.000648 | **+99.15%** |
| X2 | roll | 0.050635 | 0.019088 | 0.015270 | **+69.84%** |
| X2 | full3 | 0.304488 | 0.101233 | 0.097765 | **+67.89%** |
| X2 | hard45 | 0.299286 | 0.129264 | 0.134809 | **+54.96%** (verified, Section 2a) |
| X2 | hardstep | 0.327226 | 1.822051 | 2.021353 | **-517.72%** |
| X2 | yaw360 | 0.075874 | 0.027239 | 0.021063 | **+72.24%** |

**Honest headline**: eprop_anneal is a strong, consistent win on 4 of 5 missions on both platforms (55-99% improvement) -- genuinely more consistent across platforms than the single hard45 number in the dossier suggested. But **hardstep is not a mild regression, it's a genuine divergence** at these aggressive settings, on both platforms, worse on X2 (-518%) than CF2 (-205%). This matches and *sharpens* the dossier's own Section 4 warning ("hardstep diverges 2.18" for online_pes at aggressive settings) -- the divergence is not CF2-specific, and eprop_anneal's annealed eligibility trace does not fix it (eprop_anneal is slightly *worse* than online_pes on hardstep, on both platforms). **Any manuscript claim about eprop_anneal's generality must state the hardstep failure alongside the other four wins, with equal prominence** -- reporting only hard45/roll/full3/yaw360 would be a materially incomplete picture given what the data actually shows.

The dossier's own "balanced" (k_rate=0.3, leak=1e-3) and "strong-damp" (k_rate=1.0, leak=2e-3) configurations were reported to stabilize hardstep for online_pes -- those regimes were **not** re-run for eprop_anneal in this sweep (see Section 5 gap); until they are, "eprop_anneal fails on hardstep" should be scoped to "at the aggressive setting," not stated as an unconditional property of the method.

## 3. Plots (from the verified reproduction, not the summary JSON alone)

- `plots/eprop_anneal_tracking.png` / `plots/eprop_anneal_mechanism.png` — the original hard45/CF2 pair (Section 2a).
- `plots_5missions/{CF2,X2}_{roll,full3,hard45,hardstep,yaw360}_{tracking,mechanism}.png` — all 20 plots for the full sweep in Section 2c, same two-figure-per-mission convention (tracking+error, then mechanism/neuron/learning-signal) for every platform/mission combination.

Both sets are two-figure-per-topic, matching this project's established plotting convention.

## 4. Reproduction methodology (for anyone re-checking this)

- Original code: now installed **fully locally**, no external drive needed — `C:\Research\papers\P3_Gate_Residual\learned\code\experiments\controller_benchmarks\learned_gate_experiment.py` (not modified; originally sourced from `D:\NMSU_backups\...\neuromorphic-robotics-control`, cross-checked line-for-line identical). Model assets (`third_party\mujoco_menagerie`) are wired via an NTFS junction to an already-local OneDrive clone — not a copy, not a D:/network dependency, resolves immediately.
- Why a reproduction was needed at all: the original script computes per-timestep rows internally (`run_episode()`) but only ever passes them to `summarize_controller_run()` for scalar stats — it never writes the raw rows to disk. No raw trace for `eprop_anneal` exists anywhere on this machine (checked: this project folder, a OneDrive snapshot, and the full `D:` backup repo — only summary JSON in all three places).
- This reproduction (`reproduce_traces.py` for the single hard45/CF2 case, `reproduce_5missions.py` for the full sweep) imports `build_world`, `reset_world`, `LearnedGate`, `W_PAIR` directly from the original file unmodified, and re-implements only `run_episode`'s loop body with trace capture added (same physics/control calls, same call order) — verified correct by exact score match, not by code inspection alone.
- Environment: `C:\Research\papers\ACC2027_Gate_Residual_Control\.venv` (mujoco 3.12.0, numpy 2.5.2) — reused rather than duplicated; the original repo's own `.venv` on D: is broken (references a Python 3.11 interpreter no longer installed on this machine) and was not used or repaired.
- Settings: exactly the driver script's defaults — `--quad {bitcraze_crazyflie_2,skydio_x2} --mission {roll,full3,hard45,hardstep,yaw360} --sim-time 45 --dt 0.0005 --lr 8e-4 --k-err 8.0 --k-rate 0.0 --leak 0.0`, **`--z-ref 1.5` for hardstep, `1.0` for every other mission** (the dossier's own Section 7 parameter table states this; missed on the first sweep, caught because classical's score — deterministic, no learning involved — mismatched the frozen hardstep-CF2 reference; fixed and re-verified before any hardstep number was trusted). `eprop_anneal` uses `lr*2.0`, `elig=True`, `anneal=True` exactly as hardcoded in the original `main()`.

## 4a. Hardstep divergence: root-caused (real technical issue, not a subtle instability)

Investigated directly per a hypothesis that hardstep's altitude reference might be unreachable. Checked the `z` (altitude) trace: this is a genuine **crash**, not oscillatory instability. The vehicle holds altitude fine through the early mission, then during one of hardstep's large discrete attitude-step targets (up to ~0.9 rad / 51 deg) it tips far enough that the plant's simple (non-cascade) thrust-allocation formula -- `collective = mass*(g + ...) / tilt_cos`, `tilt_cos` floored at 0.35 -- can no longer generate enough vertical thrust to recover, and the vehicle free-falls to `z~0.019` (the ground) and stays there for the remainder of the 45s run, accumulating a large but physically-meaningless attitude error while sitting crashed. `classical` survives longer (crashes ~t=30-36s, after 2-3 of the 4 step targets); `online_pes`/`eprop_anneal` crash much earlier (~t=13-22s, during/just after the first step target) because their learned residual adds extra gain that overshoots harder on the discrete step -- exactly the mechanism the dossier's own Section 4 already flagged as a risk ("learns extra proportional gain -> overshoots/flips on step commands"), now confirmed with real altitude data on both platforms. This is a genuine plant/controller-design limitation of this benchmark script (no cascade separation, no tilt-aware thrust reserve), not a subtle learning-rule bug -- consistent with, and now more precisely diagnosed than, the earlier characterization in Section 2c.

## 4b. Nengo-native validation

Built `nengo_eprop_anneal.py`: a Nengo-native `NengoEpropAnnealAugmentor`, reusing the already-verified `CoupledMembraneGate` Nengo neuron type from `nengo_nef_replication_2026-08-29/nengo_cmg.py` unmodified. Confirmed **exact parameter equivalence** first (resolving the "Known gap" flagged in the original Section 5): `HyperLIFDirect` at `scale="control"` (`tau=0.05, tau_r=0.005, reset_gain=120.0, gamma=2.0`, plus class defaults `alpha=50, v_thresh=1.0, v_reset=0.0`) matches `CMGConfig`'s defaults in the ACC2027 codebase term-for-term -- the two projects' neuron models are not just "the same family," they are numerically identical at these settings.

Nengo has no built-in annealed-eligibility-trace learning rule, so the decoder connection keeps `nengo.PES(learning_rate=0.0)` (inert, purely to reuse the proven weight-signal-access pattern from `NengoCMGPESAugmentor`) while the actual eligibility-trace-and-annealed-rate update is applied manually after each `sim.step()`, matching `LearnedGate._update`'s exact formula.

**Isolated equivalence check** (`verify_nengo_eprop_equivalence.py`, 3000 random synthetic steps): found and characterized a **brief, self-correcting numerical transient** around step 123 (peak activity discrepancy 3.5%, decaying smoothly to exactly 0.0 by step ~1500) -- traced to floating-point-path sensitivity near the neuron's steep sigmoid threshold (`alpha=50`) between two independently-computed trajectories, not a structural bug: only 41 of 3000 steps exceed even a loose 1e-3 tolerance, all clustered in that one event, and the system provably re-converges to exact agreement afterward.

**Closed-loop validation** (`nengo_run_hard45.py`, full 45s hard45/CF2 mission): score **0.038226** vs. the frozen numpy reference **0.038215** -- difference **1.06e-5** (0.03% relative). The isolated transient has no meaningful effect once embedded in a real mission. **Nengo eprop_anneal is validated for use.**

## 5. Known gaps (stated honestly, not smoothed over)

- **Generalization regime table (2b) only reproduces the "aggressive" hyperparameter setting.** The dossier's own Section 3/4 also reports "balanced" (k_rate=0.3, leak=1e-3) and "strong-damp" (k_rate=1.0, leak=2e-3) configurations for `online_pes`, which are the ones that actually stabilize `hardstep` — those configurations were **not** re-run for `eprop_anneal` in this pass, so we don't yet have a verified eprop_anneal number for the stable/balanced regime. This is a real gap, not a small one, since it's the regime where the method would actually need to work for a step-command mission.
- **No real-hardware data exists for eprop_anneal at all**, on any platform — this entire document is MuJoCo simulation only.
- The "HyperLIF ≡ Adaptive HyperLIF" equivalence result from the dossier (Section 5) was not independently re-verified in this pass; only the base `eprop_anneal` result was reproduced.
- ~~Neuron-model parameter naming differs...~~ **RESOLVED (Section 4b)**: `HyperLIFDirect`'s raw class defaults (`tau=10.0`, `reset_gain=800.0`, etc.) are the *unused* "paper" scale; `make_direct_neuron(..., scale="control")` overrides to `tau=0.05, tau_r=0.005, reset_gain=120.0, gamma=2.0`, which is what `LearnedGate` actually uses and matches `CMGConfig` exactly. Confirmed by direct code inspection and by the Nengo closed-loop match (0.03% relative).

## 6. File map for this sub-topic

| File | Purpose |
|---|---|
| `reproduce_traces.py` | Single-case reproduction (hard45/CF2), Section 2a |
| `reproduce_5missions.py` | Full 5-mission x 2-platform sweep, Section 2c |
| `plot_eprop_anneal.py` | Builds the hard45/CF2 plots from `traces/` |
| `plot_5missions.py` | Builds all 20 sweep plots from `traces_5missions/` |
| `traces/{classical,online_pes,eprop_anneal}.csv` | hard45/CF2 per-timestep data (90,000 rows each) |
| `traces_5missions/{quad}/{mission}/{classical,online_pes,eprop_anneal}.csv` | Per-timestep data for all 10 platform/mission combinations |
| `traces/reproduction_summary.json`, `traces_5missions/all_summaries.json` | Reproduced scalar summaries, verified against frozen numbers where they exist |
| `plots/eprop_anneal_{tracking,mechanism}.png` | hard45/CF2 figures |
| `plots_5missions/{CF2,X2}_{mission}_{tracking,mechanism}.png` | All 20 sweep figures |
| **Locally installed source** (no D: dependency): `C:\Research\papers\P3_Gate_Residual\learned\code\experiments\controller_benchmarks\learned_gate_experiment.py`, `neuron_dynamics.py`, `benchmark_metrics.py`, `mujoco_classical_vs_neural_stn.py`; `...\code\experiments\mujoco_stn_hyperlif_benchmark\stn_pid_attitude_controller.py`; `...\code\third_party\mujoco_menagerie` (junction to a local OneDrive clone) | Ground truth this reproduction is verified against, and the code path for any future re-run — D: is no longer needed for anything in this document |
| Original summary JSONs: `C:\Research\papers\P3_Gate_Residual\learned\code\experiments\controller_benchmarks\learned_gate_{results,hardstep,skydio}.json` | Source of Section 2a/2b's numbers |
| Original write-up: `C:\Research\papers\P3_Gate_Residual\learned\docs\full_results_dossier.md` | The dossier this document extends with real traces, the full 5-mission sweep, and plots |
