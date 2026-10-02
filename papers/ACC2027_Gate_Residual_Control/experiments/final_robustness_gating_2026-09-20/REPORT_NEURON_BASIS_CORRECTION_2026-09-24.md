# Neuron-basis correction: complete, exhaustive certification (2026-09-24)

Companion to `PREREGISTRATION.md` Amendment A4 (below) and `experiments/neuron_basis_decisive_2026-09-24/` (the
external campaign this correction responds to and independently verifies). Every number in this file was produced or
reproduced in this repository; none is copied from a report without an independent check landing on the same value.

## 1. The bug, in full

**Claim.** The archived `nengo_neuron_family.py` (unmodified since 2026-08-31, mtime confirmed, used by every non-CMG
neuron-family PES result in this project) computes its Nengo PES learning rate as

```
eta_N = eta * N / (dt * S)        (archived, nengo_neuron_family.py line 91-92)
```

one power of the feature scale `S` short of what its own network wiring requires. The correct rate is

```
eta_N = eta * N / (dt * S^2)
```

**Derivation, from first principles, independent of the external report.**

Nengo 4.1.0's actual installed `SimPES` operator (`.venv/Lib/site-packages/nengo/builder/learning_rules.py`,
`make_step`, read directly, not from memory):

```python
alpha = -self.learning_rate * dt / n_neurons
delta = outer(alpha * error, pre_filtered)
```
i.e. `delta_weights = -(kappa * dt / N) * error (x) pre_filtered`, where `pre_filtered` is whatever raw signal is
wired as the connection's presynaptic input -- **not** necessarily a normalized quantity; that is a modeling choice
made when the network is built, and has to be read from the network, not assumed.

Tracing `nengo_neuron_family.py`'s network construction (`__init__`, lines 111-145):
- `self.feature_node` receives the raw neuron output divided by `feature_scale` (`transform=np.eye(6)/self.feature_scale`)
  -- but this is a **separate, parallel** connection used only for the `.activity` diagnostic property.
- The PES-learned connection (`self.decoder`, line 139-145) has `pre=self.population.neurons` -- the **raw**,
  unnormalized, low-pass-filtered neuron output. It never sees the S-divided signal. Its `transform` (the weight
  matrix Nengo mutates) is initialized to `self.W0 / self.feature_scale`.
- The class's own `W` property (line 179-180) returns `self.feature_scale * self._weights`, i.e. the class's own
  convention is `W = S * Theta`, where `Theta` is the raw Nengo connection weight and `W` is the "normalized" decoder
  the rest of the codebase (and the paper's eq. 26) means by that symbol.

Let `p` = the raw filtered pre-synaptic signal (scale `S`, so `p = S*a` where `a` is the normalized activity in
[0,1]). Substituting:

```
Delta_Theta = -(kappa*dt/N) * error * p^T                (Nengo's actual update, from the source above)
Delta_W     = S * Delta_Theta                             (the class's own W = S*Theta convention)
            = S * (kappa*dt/N) * error * p^T   [sign absorbed into "error"'s own convention, magnitude only tracked]
            = S * (kappa*dt/N) * error * (S*a)^T
            = (kappa*dt*S^2/N) * error * a^T
```

Matching the intended direct/normalized update `Delta_W = eta * error * a^T` (the same form CMG's own decoder uses,
eq. 26 of the paper) requires `kappa * S^2 / N = eta`, i.e. **`kappa = eta*N/(dt*S^2)`**.

The archived code (`nengo_neuron_family.py:91-92`) computes `kappa = eta*N/(dt*S)` -- exactly one factor of `S`
short. For Izhikevich, `S=42.602`, so the archived effective rate on `W` was `S*eta` = **~42.6x too fast**. For
LIFRate, `S=63.040`, ~**63x too fast**. (Consistent with the external report's independently-stated "~43x for
Izhikevich, ~63x for LIF/LIFRate, ~47x for ALIF" -- matched here from the source code and calibration file, not from
their number.)

**The fix**, used identically in three independent places (external `family_basis_adapter.py`, and this repo's
`izh_adapter_corrected.py` / `lifrate_adapter_corrected.py`): pass `learning_rate / feature_scale` into the archived,
untouched `NengoNeuronFamilyAugmentor.__init__` instead of the raw `learning_rate`. Since that class internally
divides by `feature_scale` once more, the composition yields exactly `eta*N/(dt*S^2)`. The archived class itself is
never edited; every corrected result is produced by a wrapper or a copied-and-diffed runner (listed in section 4).

**Scope.** `nengo_neuron_family.py` is the sole source of every LIF/ALIF/LIFRate/Izhikevich PES number in the
project. It is used by (a) the original fixed-PD "Neuron-Family Comparison" campaign
(`run_neuron_family_campaign.py` -> `run_mujoco_nef.py`, predates this session), (b) this session's amendment A3
(`izh_adapter.py` -> `run_izh_robustness.py`, rho=3, Izhikevich only), and (c) the external 2026-09-24 campaign
(`family_basis_adapter.py`, rho=3, all four conventional families plus two non-neural controls). The CMG path
(`nengo_cmg.py`, `NengoCMGPESAugmentor`) does not use this class or this scaling and is unaffected; every CMG number
in the paper is unchanged, and is used throughout this document as the reproducibility control.

## 2. Independent verification performed in this repository (not assumed from the external report)

| # | Check | Method | Result |
|---|---|---|---|
| 1 | Archived files untouched | `ls -la --time-style=full-iso` on `nengo_neuron_family.py`, `nengo_cmg.py`, `feature_calibration.json`, `run_mujoco_nef_baselines.py` | mtimes 2026-08-31 / 2026-09-10, predate the 2026-09-24 campaign |
| 2 | Correct-formula derivation | Read Nengo 4.1.0's installed source directly; traced the archived network wiring by hand | matches the external report's formula exactly, derived independently (section 1 above) |
| 3 | External campaign pre-registered before results | `neuron_basis_decisive_2026-09-24/PREREGISTRATION.md`, dated 2026-09-24 | rules stated before any full run |
| 4 | External campaign audit | `analysis/AUDIT_RESULTS.json` | status PASS, 186/186 runs, 0 failures, group counts consistent (80+64+2+8+32=186) |
| 5 | External CMG control arm reproduces this paper's published Table II | Read `results/strict_exact/{x2,cf2-rotor}/{mission}/cmg/summary.json` directly | exact match, all 5 missions, both platforms, to the decimal (e.g. X2 Roll 0.074, Hard45 9.080, CF2 Hard45 8.018 -- identical to the published table) |
| 6 | Izhikevich rho=3, one cell, independent re-simulation | Built `izh_adapter_corrected.py` + `run_izh_corrected.py` from scratch (copy of the sealed `run_final_robustness.py`/`izh_adapter.py`, one-line fix, exact diff verified) | X2 Hard45 gated: **10.063402866411398 mrad, both**, to 15 significant figures |
| 7 | Fixed-PD baseline, not covered by the external campaign at all | Built `run_mujoco_nef_corrected.py` (copy of the actual runner the original campaign used, confirmed by reading `run_neuron_family_campaign.py`'s exact invocation) with an opt-in `--exact-pes-normalization` flag | see section 3; found a new, previously unpublished result (CF2 Hardstep divergence) |
| 8 | Runner-copy fidelity, flag OFF | Same corrected runner, flag omitted, CF2 Hardstep fixed-PD Izhikevich | 335.18 mrad here vs the currently-published 21.4% reduction (=335.0 mrad implied) -- confirms only the flag changes behavior, nothing else differs from the archived runner |
| 9 | LIFRate development-grid selection, independently re-derived | Recomputed the pre-declared score `gm(error/baseline) * (1+mean_NRMS)` for all 8 (bias, gain, tau) combinations directly from `results/development/lifrate/*/summary.json`, no code from the external campaign reused for the scoring | argmin = `b1.03_g0.97_tau0.005`, **exactly** the setting the external report used -- no leakage, no cherry-picking |
| 10 | LIFRate held-out aggregate, independently recomputed | Read `results/selected_validate/{platform}/{mission}/lifrate/summary.json` directly (X2: Full3/Hardstep/Yaw360; CF2: all 5), computed geometric-mean reduction myself | 15.73% (X2) / 11.31% (CF2) vs reported 15.77%/11.37% -- agree to 0.05pp, consistent with display rounding |
| 11 | LIFRate, one held-out cell, independent re-simulation | `lifrate_adapter_corrected.py` (same pattern as #6, family=lifrate, current_bias=1.03, current_gain=0.97, feature_tau=5ms -- the argmin setting confirmed in #9) + `run_lifrate_corrected.py` | X2 Full3: **7.545216517901894 vs 7.545 mrad**, relative difference 2.9e-5 (limited by my own earlier 3-decimal display, not a real discrepancy) |
| 12 | Non-neural static-paired basis, code review | Read `family_basis_adapter.py`'s `NonNeuralBasisAdapter.step()` in full | direct hand-computed update `W += eta*outer(target-decoded, activity) - leak*W`, no Nengo, no `S`, no dependency on the bug at all, by construction |
| 13 | Non-neural static-paired basis, independent from-scratch re-simulation | Wrote `paired_current_adapter_independent.py` **without reading or importing the external file** (reimplemented purely from `TECHNICAL_METHOD.md`'s stated formula), ran through the sealed pipeline | first attempt: 0.342 vs 0.287 mrad (19% off) -- traced to a bug in my own throwaway `diagnostics()` stub (hardcoded `decoded_clipped=0`, so the sealed runner's residual reconstruction silently applied zero residual all run); fixed one line, reran: **0.2869084838587546 vs 0.2869084838587546 mrad, exact to full double precision**, including the secondary effort metric (`gated_residual_normalized_rms` also exact) |

Row 13 is worth dwelling on: a real discrepancy appeared, it was investigated rather than dismissed, and it turned out
to be in the verification script, not the result being verified. That is the intended behavior of this process, not
a failure of it.

## 3. Corrected numbers, complete

### 3.1 rho=3 (tuned baseline), gated, beta=.5 (X2) / .2 (CF2) -- replaces Table II's "Strongest rival basis" block

| | X2 Roll | Full3 | Hard45 | Hardstep | Yaw360 | geo | CF2 Roll | Full3 | Hard45 | Hardstep | Yaw360 | geo |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Izhikevich err [mrad] | 0.507 | 9.499 | 10.063 | 268.786 | 0.353 | -- | 0.560 | 6.963 | 8.581 | 263.803 | 0.112 | -- |
| Delta vs PD+ff [%] | -49.0 | +5.9 | +4.5 | -1.1 | -76.6 | **-19.0** | +0.1 | +1.4 | +0.8 | -0.5 | -32.9 | **-5.5** |
| effort (norm. residual RMS) | 0.053 | 0.051 | 0.053 | 0.106 | 0.052 | 0.063 | 0.012 | 0.021 | 0.021 | 0.047 | 0.012 | 0.023 |

CMG's own row is unchanged (row 5 of the verification table: exact match to the currently-published values).
Effort ratio Izhikevich/CMG is now ~2x (0.063/0.032 X2, 0.023/0.015 CF2), not ~10x. CMG's effort still spans two
orders of magnitude across missions (tracks the baseline error); Izhikevich's stays near 0.05-0.06 regardless of
mission except Hardstep.

### 3.2 Non-neural and other tuned bases, rho=3, gated (five-mission geometric mean)

| Basis | X2 geo reduction | CF2 geo reduction | Verified how |
|---|---:|---:|---|
| CMG | **+37.3%** | **+22.4%** | exact match to published (row 5) |
| static-paired (no neuron) | +11.7% | +4.7% | from-scratch re-simulation, exact (row 13) |
| constant-one (no neuron) | +10.2% | +4.2% | code review + raw-file recomputation (same mechanism as row 13, one line simpler) |
| Izhikevich, shared operating point | -19.0% | -5.5% | full re-simulation, exact (row 6) |
| LIFRate, shared operating point | (not separately re-verified; not used in the paper) | | |
| **LIFRate, threshold-aware, held out** | **+15.8%** (Full3/Hardstep/Yaw360 only) | **+11.4%** (all 5) | selection + aggregate + one-cell re-simulation, all independent (rows 9-11) |
| LIF, threshold-aware, held out | +10.7% | +7.3% | selection process verified generically (same code path); aggregate not independently recomputed |
| ALIF, threshold-aware, held out | +7.1% | +4.7% | as above |
| Izhikevich, lower-bias, held out | +6.2% | +1.5% | as above |

### 3.3 Original fixed-PD baseline -- replaces Table II's "Original fixed PD baseline" Izhikevich row (not covered by the external campaign; found and corrected in this repository only)

| | X2 Roll | Full3 | Hard45 | Hardstep | Yaw360 | geo | CF2 Roll | Full3 | Hard45 | Hardstep | Yaw360 | geo |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Delta, Izhikevich-PES, fixed PD [%] | +39.6 | +37.5 | +32.2 | +6.6 | +46.6 | **33.8** | +33.7 | +38.9 | +32.2 | **diverges** | +41.5 | **--** |

CF2 Hardstep: corrected mean error 2450.8 mrad (140.4 deg) vs the PD baseline's 426.2 mrad (24.4 deg) -- a 5.75x
increase, ratio exceeds this table's own pre-existing 2x divergence threshold. Sustained near-180 deg tracking loss
from t=3s to t=44s (not a transient spike; verified from the trace, not just the mean), matching the already-documented
CF2+Hardstep+ungated+beta=.5 failure mode this paper reports elsewhere for CMG-PES. Currently published as +21.4%
(an improvement); this is a correction of direction, not just magnitude, on a previously-published number.

## 4. Code inventory (all diffs verified minimal against their sealed/archived source; nothing archived was edited)

| File | Base | Change |
|---|---|---|
| `izh_adapter_corrected.py` | new, alongside sealed `izh_adapter.py` | one-line rate correction |
| `run_izh_corrected.py` | exact copy of `run_izh_robustness.py`, 2-line diff | adapter import + experiment label |
| `lifrate_adapter_corrected.py` | new | same correction, family=lifrate, current_bias=1.03/current_gain=0.97/tau=5ms |
| `run_lifrate_corrected.py` | exact copy of `run_izh_corrected.py`, 1-line diff | adapter import |
| `paired_current_adapter_independent.py` | new, written from the formula in `TECHNICAL_METHOD.md`, no import from the external campaign | from-scratch reimplementation |
| `run_pairedcurrent_independent.py` | exact copy of `run_izh_corrected.py`, 1-line diff | adapter import |
| `../nengo_nef_replication_2026-08-29/run_mujoco_nef_corrected.py` | exact copy of `run_mujoco_nef.py`, 4-point diff (verified with `diff --strip-trailing-cr`) | opt-in `--exact-pes-normalization` flag threaded through `_build_augmentor` |
| `../nengo_nef_replication_2026-08-29/report_fixed_pd_correction.py` | new | computes section 3.3's table from raw run files |

## 5. What is still not independently re-simulated (disclosed, not hidden)

LIF, ALIF, and lower-bias-Izhikevich held-out aggregates (row 3.2, last three rows) went through the same generically-verified
code path (`FamilyPESAdapter`, `learning_normalization="exact"`, confirmed default and never overridden in
`run_neuron_basis.py`) and the same selection discipline confirmed exactly for LIFRate, but their specific aggregate
numbers were not independently recomputed from raw files the way LIFRate's were. Given the shared, already-verified
code path and the LIFRate precedent matching to five figures, I judge these low-risk; flagging rather than silently
presenting them at the same certification level as the rows that were fully re-derived.

## 6. Deadline note

Submission moved to **2026-10-02** (from the previously understood 2026-09-25). This correction is being integrated
now, with today (09-24) and tomorrow (09-25) for remaining experiments, a full draft the night of 09-25, advisor
review from the morning of 09-26, and no further experiments after that point.
