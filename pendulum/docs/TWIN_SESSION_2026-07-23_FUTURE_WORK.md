# Qube3 Digital-Twin Session — Results & Future Work

**Date:** 2026-07-23 (overnight session, final session on the returned machine)
**Platform:** Quanser Qube Servo 3 + pendulum, QLabs digital twin (`0@tcpip://localhost:18923`)
**Scope:** equilibrium control (Python + Julia), LED instrumentation, HyperLIF gate
residual with the MuJoCo learned-gate architecture, disturbance-rejection benchmark.

> **Read this first if you are resuming on a new machine.** Everything below is
> backed up under `D:\NMSU_backups\Backup\00_Research_\Neuromorphic_Embodied_AI\`.

---

## 1. COMPLETED AND VALIDATED

### 1.1 Equilibrium control — FROZEN v1
`results/twin/FROZEN_v1_20260723/` (see `VALIDATED.md`, SHA256 manifest included).

Energy swing-up (Quanser law) + LQR balance, in **both** languages, reproducible:

| Metric | Python / PAL | Julia / Bridge 2 |
|---|---:|---:|
| First capture | 4.04 s | 4.03 s |
| Longest hold | 15.96 s | 15.97 s |
| Balance fraction (final 2 s) | 1.000 | 1.000 |
| α RMS (tail) | **1.06°** | 1.24° |
| Realized rate | 500.0 Hz | 500.0 Hz |
| Amplifier faults / stalls | 0 / 0 | 0 / 0 |

Both gain sets validated and equivalent on the twin:
`twin` = `[-1.000, 26.72, -0.8269, 2.214]` · `code` = `[-1.2247, 24.9044, -0.6877, 3.1321]`
(capture 4.04 s vs 3.78 s; RMS 1.06° vs 1.07°).

**This closes the Julia bridge V2/V3 rung for the Qube3** — `VALIDATION_STATUS.md`
previously listed Qube3 V2 as "scene pending". It is now live and validated.

### 1.2 Gate-residual neuron comparison in steady balance — THE KEY RESULT

Fixed-gate residual, blend 0.25, 25 s runs. Uses the **same neuron code as the
MuJoCo campaign** (imports `neuron_dynamics.make_direct_neuron` from
`neuromorphic-robotics-control`), so the comparison is apples-to-apples.

| Neuron | α RMS | vs baseline | mean gate activity |
|---|---:|---:|---:|
| *baseline (no residual)* | 1.236° | — | — |
| **adaptive_hyperlif** | **1.064°** | **−13.9%** | 0.918 |
| **hyperlif** | **1.085°** | **−12.2%** | 0.834 |
| lif | 1.241° | +0.4% | **0.9998 (saturated)** |
| izhikevich | 1.240° | +0.3% | **0.0000 (silent)** |

**Interpretation.** Only the gate helps. LIF saturates its gate at ~1.0 and
Izhikevich never opens it; neither carries usable information, and both land on
baseline. HyperLIF and Adaptive HyperLIF both improve, and are again near-equal —
consistent with the Adaptive≡HyperLIF boundary result.

This is the campaign's central claim (`CAMPAIGN_STATUS` contribution #2)
**reproduced on a third substrate**: MuJoCo quads → Qube hardware → Qube twin.

### 1.3 LED instrumentation
LED is **full RGB, continuous floats 0.0–1.0**, write channels `[11000, 11001, 11002]`.

| State | Color |
|---|---|
| idle / shutdown | RED `[1,0,0]` |
| settling (waiting for rest) | YELLOW `[1,1,0]` |
| swing-up | BLUE `[0,0,1]` |
| centring | CYAN `[0,1,1]` |
| balancing | **continuous gauge** GREEN→RED ∝ \|α\|/20° |

---

## 2. TWO PLATFORM BUGS FOUND (do not lose these)

### 2.1 Encoders zero at whatever pose the pendulum is in
`pal.products.qube.__QubeServo.__init__` calls
`set_encoder_counts(READ_ENCODER_CHANNELS, ..., zeros)`. **`raw` therefore always
reads 0.0000 at construction, regardless of the physical pose.**

Consequence: `alpha = wrap(raw - pi)` is correct **only if the pendulum is hanging
at rest when the script starts**. Runs launched immediately after a previous run
(which left the pendulum upright) inherit a zero at the TOP and the entire
convention inverts — the controller then regulates to hanging and behaves wildly.

**Fix implemented:** settle first, record the resting raw angle, and use
`alpha = wrap(raw - REST_RAW - pi)`. Correct from any starting pose.

### 2.2 Tachometer has a persistent offset — speed-based rest detection is impossible
At complete rest the pendulum tachometer reads **−0.061 rad/s**, and the motor
tachometer reads the same magnitude. A naive "at rest when |speed| < 0.05" test
can therefore **never** fire; it always times out.

**Fix implemented:** detect rest from **position stability** — max−min of the raw
angle over a 1.5 s sliding window < 0.5°.

### 2.3 Pre-existing convention bug in the repo (unchanged, flagged)
`src/servo_pendulum_snn/controllers.py::QuanserBalanceController` uses
`alpha = wrap_to_pi(raw)` with **no −π shift** and `theta = -motorPosition`.
On the twin that law regulates to the **hanging** position. It is only correct when
the encoder is zeroed while the pendulum is held upright (the hardware convention),
which is how the June hardware trials were run — **those results are unaffected**.
Do not reuse this class for twin work without the shift.

---

## 3. NOT COMPLETED — FUTURE WORK

### 3.1 Disturbance-rejection benchmark (highest priority)
`runners/twin_perturbation_benchmark.py` — mechanism works, **comparison is not valid yet.**

The protocol (swing-up → centre the arm → 6 identical voltage impulses of 2.5 V ×
0.12 s every 4 s → measure peak \|α\| and recovery time) executes correctly, logs
per-impulse events, and the baseline survives 6/6 with peak ≈5.0° and recovery
≈0.06 s. **But runs are not matched**, so cross-variant numbers cannot be compared:

* some runs centred, others timed out with the arm pinned at the ±135° hard stop;
* one swing-up took 90 s;
* starting arm position differs between runs, which dominates the transient response.

Numbers obtained (⚠️ **unmatched single runs — hypothesis only, not a result**):

| Config | peak \|α\| | recovery | RMS (perturbed) | arm at start |
|---|---:|---:|---:|---|
| baseline | 5.01–5.10° | 0.059–0.068 s | 1.40–1.61° | ±135° / centred |
| fixed_gate hyperlif | 7.41° | 0.069 s | 2.65° | −108° |
| fixed_gate adaptive | 6.71° | 0.142 s | 3.13° | limit |
| fixed_gate izhikevich | 7.35° | 0.067 s | 1.88° | −135° |

These *hint* that the residual at blend 0.25 **worsens transient rejection** even
though it improves steady-state RMS — a genuinely interesting possibility (the gate
helps regulation but adds lag under impulse) — but it must be re-measured properly.

**The blocker is arm centring, and it is a protocol problem, not a code problem:**

* `KC_SW = 1.0` → swing-up reliable (4–10 s) but the arm parks at the ±135° limit.
* `KC_SW = 1.75–3.0` → better centring but swing-up becomes slow (90 s) or fails.
  The centring term fights the energy pump.

**Proposed fix (~20 min):** decouple the two objectives.
1. Swing up at `KC_SW = 1.0` (known reliable).
2. Add a dedicated **RECENTRE** phase after capture: pure LQR with a slowly ramped
   θ reference (`theta_ref: theta_now → 0` over ~5 s) rather than a large static
   gain, with a generous budget (~15 s) and an explicit pass/fail gate.
3. Only start perturbing once `|θ| ≤ 25°` is actually achieved; **abort and retry
   the run otherwise** rather than falling through on timeout.
4. Enforce a settle-to-rest pause between runs (the settle detector now works).
5. Repeat each config ≥3 times and report mean ± std.

### 3.2 Learned gate (online_pes / eprop_anneal) — encoding is saturating
Learned methods gave **no improvement** (online_pes 1.274°, eprop_anneal 1.236° vs
baseline 1.236°). Diagnosis: mean gate activity 0.83–0.92 across **all six units** —
the gate is nearly saturated, so `signed = W @ act` can only shift a constant
offset and cannot discriminate between inputs. `W` duly collapsed toward uniform
values (`[-0.075, -0.075, -0.039, -0.075, -0.074, -0.077]`).

This is the **same saturated-gate regime** the MuJoCo gate-gain sweep identified,
reached from the opposite direction: there the gate had to be *pushed into*
saturation (G→1e5) to help the fixed decode; here saturation *destroys* the
learned decode's information.

**Future work:**
* Lower `CURRENT_BIAS` (0.75) and/or `CURRENT_GAIN` (1.25) so the six units sit in
  the gate's sensitive band rather than above it. Sweep bias ∈ [0.0, 0.75].
* Reduce `GATE_GAIN` from 1e5 — the fixed decode wants saturation, the learned
  decode wants graded activity. **These two requirements are in direct conflict and
  that tension is itself a publishable observation.**
* Verify differential activity before trusting any learning result: log
  `act.std()` per step; if it is ~0, the learner cannot work by construction.

### 3.3 Blend architecture on an unstable plant
MuJoCo uses `v = (1-b)·v_pd + b·v_neuron`, which at b=0.5 halves the PD backbone —
the diagnosed "half-PD detuning". On a quadrotor that is survivable; on an
**inverted pendulum** (unstable equilibrium) it is far riskier. This session used
b = 0.25 only. Future work: sweep b ∈ [0.05, 0.5] and find where the pendulum
destabilises, and compare against the *additive bounded* residual used in the
June hardware trials (`residual_limit = 0.75 V`, `residual_blend = 0.25`), which is
a different and probably safer architecture for this plant.

### 3.4 Other open items
* **Julia parity for the residual** — only the equilibrium controller has a Julia
  twin; `twin_hyperlif_residual.py` has no Julia counterpart yet.
* **Hardware transfer** — everything here is twin-only. The bridge V4 hardware rung
  needs the Quanser SDK and the physical rig at the lab bench.
* **Aero2** — untouched this session. The Aero2 HIL paper remains the single
  largest undrafted asset (22 conditions of real data, no draft).

---

## 4. FILE MAP

| Path | Contents |
|---|---|
| `runners/twin_diagnostic.py` | safe no-voltage diagnostic; LED test; convention resolver |
| `runners/twin_swingup_balance.py` | **validated** Python swing-up + LQR balance |
| `runners/twin_hyperlif_residual.py` | gate residual + learned decode + LED gauge |
| `runners/twin_perturbation_benchmark.py` | disturbance protocol (**needs §3.1 fix**) |
| `results/twin/FROZEN_v1_20260723/` | frozen validated version + SHA256SUMS |
| `results/twin/` (5 files) | diagnostic + swing-up runs |
| `results/twin_residual/` (18 files) | neuron comparison runs |
| `results/twin_perturb/` (30 files) | perturbation runs (unmatched, see §3.1) |
| `17_Julia_Quanser_Bridge/julia/qube3_twin_equilibrium.jl` | Julia parity version (LEDs included) |
| `17_Julia_Quanser_Bridge/julia/qube3_twin_swingup_balance.jl` | your earlier script, untouched |

## 5. HOW TO RESUME

```powershell
# QLabs must be running with the Qube Servo 3 PENDULUM scene (port 18923 open)
Test-NetConnection localhost -Port 18923 -InformationLevel Quiet

cd <repo>\07_ServoPendulum_SNNs
.\.venv\Scripts\python.exe .\runners\twin_diagnostic.py 6                        # sanity
.\.venv\Scripts\python.exe .\runners\twin_swingup_balance.py 20 500 100 10 twin 1
.\.venv\Scripts\python.exe .\runners\twin_hyperlif_residual.py fixed_gate hyperlif 25 0.25

cd <repo>\17_Julia_Quanser_Bridge\julia
julia --startup-file=no .\qube3_twin_equilibrium.jl 20 500 100 10 twin 1
```

**Always let the pendulum come to rest between runs** — the settle detector handles
it, but back-to-back launches are the single most common cause of a failed run.
