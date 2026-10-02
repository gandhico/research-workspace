# Insights, Status & Future Work

> **Session handoff — 2026-06-10.** Where the project stands, what we learned, how to
> run it, and what to do next. Phase map: [`../CLAUDE.md`]. HyperLIF survey:
> [`10_neuromorphic_hyperlif.md`]. Julia↔Quanser: [`11_julia_quanser_bridge.md`].

## Where we are now
**Classical baseline complete offline. Neuromorphic layer built + validated. 79 tests pass.**

Done:
- **Scaffold (P1):** single-source-of-truth `config/`, four composable interfaces (`Model`/`Backend`/`Controller`/`Application`), functional `OfflineBackend`.
- **Models (P3):** `helicopter_2dof` (+`linear_2dof`), `pitch_only`, `yaw_only`, `half_rotor` (NotValidated). SOTA-validated vs 3 IEEE papers.
- **Data migration (P2):** 36 recorded CSVs → `data/raw_logs/` (M1–M3 + hardware).
- **IO / state estimation (P4):** encoders, IMU bias (reproduced *exactly* from the M1 log), ZOH, gyro-vs-encoder estimator (gyro 58.6× smoother).
- **Identification (P5):** ARX/DARX reproduces **Table II to 2 d.p.** + the one-step/free-run split; excitation, validation, ss-realize.
- **Control (P7):** PD, LQR, LQG, MPC, backstepping, SMC, NMPC (+yawboost), all on measured Δt; offline ranking matches **Table IV** (PD best pitch).
- **Neuromorphic (P10):** HyperLIF neuron core; `HyperLIFResidualController` (registered `hyperlif`); `NeuromorphicIdentifier` (reservoir); **Python e-prop `EpropSNN` — finite-difference-validated**.

Not yet (none block tomorrow's neuromorphic work):
- **P6 backends:** QLabs virtual-twin + HIL hardware (hardware needs the Quanser SDK — not installed).
- **P8** regulation-under-disturbance application · **P11** `compare.py` figures · **P9** full docs pass.

## The runners — yes, all four are in `runners/`
```bash
python runners/run_control.py            # close the loop (model × mode × controller × application); flags or --config YAML
python runners/run_identification.py     # fit ARX/DARX, reproduce Table II + one-step/free-run
python runners/run_benchmark.py          # sweep all controllers, Table-IV-style comparison
python runners/run_state_estimation.py   # reproduce Ref-1 IMU calibration + pitch-rate comparison
```
Examples:
```bash
python runners/run_control.py --controller hyperlif                       # neuromorphic residual (any registered controller works)
python runners/run_control.py --controller backstepping --estimator aero2 # gyro estimator in the loop
python runners/run_control.py --config configs/experiments/helicopter_offline_pd_tracking.yaml
```
The `hyperlif` controller drops into `run_control`/`run_benchmark` (registered). The **e-prop**
is used via the API (`from aero2.control.neuromorphic import EpropSNN`) and `tests/test_eprop.py` —
**no dedicated runner yet** (a `run_eprop.py` / trained-identifier comparison is a good next add).

## Insights
### Classical
1. **Timing is inseparable from control** — PD only became strongest after derivative filters used the *measured* Δt (~380 Hz, not commanded 500). Enforced via `Backend.dt_actual()`.
2. **One-step vs free-run** — ARX/DARX are strong local predictors, weak free-run simulators; reported separately, never averaged.
3. **Yaw is the unresolved axis** — breakaway/stiction + coupling; model-based controllers under-track yaw; yawboost adds motion without fixing error → sign/mapping/phase suspect. Kept visible.
4. **Conservative model-based controllers** — LQR/LQG/MPC avoid saturation but under-drive vs tuned PD.
5. **Model fidelity vs SOTA** — the project uses a deliberately *simplified* model (sinθ restoring, no Coriolis/centrifugal, cosθ on the yaw input) vs the canonical Quanser dynamics; inertias + negative `K_yp` confirm it **is** the Aero2. Code = truth, not changed (`02_modelling.md`). Open question: `sinθ` vs gravity `cosθ`.

### Neuromorphic (new)
6. **Gate `r∈[0,1]` is a bounded, smooth residual feature** → "PD + gate residual" (`HyperLIFResidualController`); `blend=0` ≡ PD exactly.
7. **Honest first results** — the fixed-weight gate residual slightly *degrades* PD on the ideal offline plant (PD near-optimal; the +7.35% source result was a *noisy MuJoCo quadrotor*, harder regime). Pure HyperLIF reservoir identifier fails (−11.6%); hybrid matches ARX (96.95%) but the linear lags carry it → **gates add ~nothing without learning.**
8. **Python e-prop is validated as an architecture** (not tuned results): `gate_exact` ψ = exact gate Jacobian (2e-10); readout gradient exact; hidden e-prop gradient ≈ BPTT (**cos 0.97**, after the per-synapse **membrane-eligibility** fix — was 0.22 with a naive trace); it trains.
9. **Regime is decisive** — paper-scale HyperLIF (`G_base=800, α=50`) is stiff/near-binary (great for classification, e.g. 3-bit parity; gates latch 0/1). For graded **regression/control use a soft `HyperLIFParams`**. The operating point sets e-prop gradient fidelity (METHODS §7).
10. **Process readiness** — modelling + control are Python-portable *now*; the strong identification learning is Julia (APEX / gate-eligibility). We replicated the e-prop core in Python; heavy training can stay Julia and export weights.

### Julia ↔ Quanser (`11_julia_quanser_bridge.md`)
11. **No native Julia binding.** Bridge via **PythonCall/juliacall** (easiest: Julia policy as a `Controller` called from our Python runner) or **`ccall` to the HIL C lib** (most native). QLabs (`qvl`) + HIL are Python. **Real prerequisite: install the Quanser SDK** (not installed here).

## Blockers / prerequisites
- **Live hardware/twin:** Quanser SDK not installed (no `quanser` pkg → no `hil.dll`); QLabs needs the QLabs app + `qvl`. Step 0 for any live work.
- Everything else runs **offline** against the migrated recorded data.

## Future directions — start here tomorrow
**Theme: make the gates *trained*, then test where HyperLIF should win (harder regimes / yaw).**
1. **Train the gates with e-prop.** Wire `EpropSNN` into (a) a trained `NeuromorphicIdentifier` (one-step predictor vs ARX on identical splits) and (b) a trained HyperLIF residual/controller (vs PD/SMC on Table-IV metrics). Add `run_eprop.py` + a neuromorphic comparison.
2. **Harder regimes** (where robustness pays): enable offline sensor noise (`OfflineBackend(measurement_noise=True, quantize=True)`), then the QLabs twin, then hardware. **Target the yaw axis** specifically.
3. **Tune encoding/blend per axis** (`blend`, `gate_gain`, `scale`, soft-vs-paper neuron) — sweep.
4. **Remaining classical:** P6 backends (QLabs → HIL), P8 regulation/disturbance app, P11 `compare.py` figures, P9 docs pass.
5. **Optional:** high-fidelity `helicopter_2dof_hifi` canonical model as a physics-grounded reference plant for the SNN comparison (`02_modelling.md` open item).
6. **Julia/APEX (CUDA)** for heavy offline SNN training → export weights to the Python `EpropSNN`, deploy via Python Quanser I/O.

## Pointers
- Phase map + live status: `../CLAUDE.md`
- HyperLIF survey + Aero2 integration map: `10_neuromorphic_hyperlif.md`
- Julia↔Quanser bridge options: `11_julia_quanser_bridge.md`
- Model fidelity vs SOTA: `02_modelling.md` · Benchmark targets (Table II/IV): `09_benchmarking.md`
