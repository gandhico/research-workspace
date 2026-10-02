# Gate-gain and conductance audit — completed 2026-09-11

## Bottom line

The frozen tracking improvements reproduce. However, the new evidence does not establish a CMG-specific performance advantage. In the canonical regime, conductance modulation is largely hidden from the readout. A constant non-neural activity basis with the same PES update slightly outperforms canonical CMG in X2 Full3 and CF2 Hardstep and substantially outperforms it in X2 Roll. We found conductance-sensitive operating regimes, but none surpassed the canonical CMG controller; some were worse than PD.

The useful contribution is a bounded, allocation-aware online-PES residual and its continuous CMG/Nengo realization, with an unusually explicit mechanism audit. It is not currently defensible to claim that conductance modulation, biological complexity, or neuron-specific expressiveness causes the principal tracking gains.

## Completed scope and what was not run

71 new, deterministic, 45-second MuJoCo runs at h=0.0005 s: 53 direct CMG, 8 Nengo CMG, 3 paired-linear/PES, 3 constant-basis/PES, and 4 PD anchors. No hardware was accessed.

The original 148-case full factorial was staged down because concurrent research workloads made the first batch expensive. The completed main stage covers X2 Full3 and CF2 Hardstep at G={1,1000,100000,1000000}, both chi settings, with eight Nengo checks. X2 Roll has the full six-gain curve {1,100,1000,10000,100000,1000000}. The 24 intrinsic-regime development runs and three constant-basis controls were declared in their separate plan files. These are not hidden replacements for the frozen ten-cell table. Hard45 and Yaw360 were not included in this new sensitivity study.

## Gain sensitivity

Mean quaternion-angle error reduction relative to the freshly rerun PD, direct backend, chi=1, gamma=2, canonical input bias=.75. Learning coefficient and authority were held fixed.

| Gain G | X2 Roll | X2 Full3 | CF2 1.5x Hardstep |
|---:|---:|---:|---:|
| 1 | 0.0003% | 56.7401% | 18.4602% |
| 100 | 0.0323% | Not run | Not run |
| 1,000 | 0.2712% | 56.0361% | 18.3430% |
| 10,000 | 0.8653% | Not run | Not run |
| 100,000 — frozen setting | 17.3642% | 56.5582% | 18.3715% |
| 1,000,000 | 57.7622% | 56.9703% | 18.3844% |

The largest absolute chi-on/off change in relative mean error across these canonical-gamma pairs is only 0.000168%. This is operational insensitivity, not zero conductance. No statistical significance or universal optimum is claimed.

Gain strongly matters for Roll, which stays on a low-gate operating branch. By contrast, Full3 and Hardstep activate persistent high-gate states and are much less gain-sensitive. At fixed eta, changing G also changes feature excitation and effective learning bandwidth; it is not a controlled comparison of representational capacity.

![Gain sweep](C:/Research/papers/ACC2027_Gate_Residual_Control/experiments/gate_gain_sweep_2026-09-11/analysis/gain_sweep.png)

## The simple-control comparison

All controls below share W0=[I,-I], eta=.0008, leak=1e-6, teacher=clip(-8 e_q), beta=.5, weight/output limits, initial conditions and rotor allocation. Features differ. None of the simpler comparators was separately optimized.

| Case | PD mean (rad) | Canonical CMG reduction | Paired-linear/PES reduction | Constant-basis/PES reduction |
|---|---:|---:|---:|---:|
| X2 Roll | .050565 | 17.3642% | .7267% | **57.7792%** |
| X2 Full3 | .303275 | 56.5582% | 6.7037% | **56.9784%** |
| CF2 Hardstep | .426182 | 18.3715% | 1.5035% | **18.3844%** |

Use `analysis/all_completed_cases.csv` for full-precision values; rounded table entries are explanatory.

Paired-linear features are [max(u0/ell,0),max(-u0/ell,0)]. Constant features are six ones and contain no neuron dynamics. Their success is not a causal comparison of equal-bandwidth controllers: their excitation is different. It nevertheless disproves necessity of CMG dynamics for those three observed improvements.

![Simple control comparison](C:/Research/papers/ACC2027_Gate_Residual_Control/experiments/gate_gain_sweep_2026-09-11/analysis/simple_basis_comparison.png)

## What the internal states actually show

In canonical X2 Full3, raw gate r>.9 occupies 97.70% of unit-samples, mean conductance/leak c*tau=7.083, and activity reaches its ceiling in 98.19% of unit-samples. All six activities are identically one from t=2.02 s onward. Thus the previous generic explanation “the conductance is tiny” is wrong for this case. It can be tiny in Roll: operating regimes must be distinguished.

With gamma=2, v>=0 and r>=.5 imply sigmoid[50(v-1+2r)]>=.5. The convex gate step preserves this region. Once r is near one, conductance changes voltage but the strongly positive gate argument and clipped readout obscure that change. chi=0 still retains the base conductance 120*r^2; it does not remove CMG dynamics.

For constant activity a_bar and inactive weight projection, z=W a_bar satisfies exactly:

    z_(k+1) = (1-lambda_W) z_k
              + eta ||a_bar||^2 [y*_k - clip(z_k,-1,1)].

If readout clipping is also inactive, this is a first-order filter of the target. For six unit activities the pole is .995199 and the equivalent time constant is about .104 s. The recorded X2 Full3 decoder obeys this recursion after t=2.02 s to within 8e-16. Constant-basis controls obey it from startup. This is an exact conditional direct-backend reduction, not a blanket equivalence for varying features, projected weights or the Nengo teaching delay. See `MECHANISM_DERIVATION.md` for the full derivation.

## Conductance-sensitive regimes: informative, not better

Under an identical 16-second current ramp .75 -> 2 -> .75, changing gamma from 2 to .5 makes the mean absolute raw-gate difference between chi=0 and chi=1 rise from about 0.000016 to 0.243. This is a time-aligned state difference, affected by changes in oscillation timing; it is not a 0.243 shift in the time-averaged gate level. It demonstrates neuron-state sensitivity under matched input, not a tracking advantage or a timestep-convergence result.

![Matched-input states](C:/Research/papers/ACC2027_Gate_Residual_Control/experiments/gate_gain_sweep_2026-09-11/analysis/conductance_regimes.png)

Changing gamma alone in nominal tracking mostly leaves the weaker-feedback neurons poorly excited. A declared follow-up increased input bias from .75 to 1.0. For gamma=.5, G=3, bias=1:

| Mission | chi=0 reduction vs PD | chi=1 reduction vs PD | Interpretation |
|---|---:|---:|---|
| X2 Full3 | 17.8332% | 14.7711% | Modulation changes tracking but is worse than chi=0 and canonical CMG. |
| X2 Hardstep | -3.3217% | -3.6233% | Both are worse than PD. |

At G=1, bias=1 on Hardstep, chi=1 improves error by .3241% relative to chi=0, but both remain worse than PD. It would be misleading to promote that relative win as a useful controller improvement.

Every development pair, including the lower-bias and gamma=0 ablations, is in `analysis/conductance_pairs.csv`. None improves on canonical CMG in its matched mission. We therefore recommend reframing, not claiming that a superior conductance regime has been found.

## Code/data validation and limitations

- 90,000 plant steps per run. Aggregate tracking metrics use every step; plant/interface CSV traces retain every tenth step (5 ms). This distinction matters when recomputing means.
- 67 full-rate neural/basis archives (0.5 ms), including exact direct pre-update weights and increments. The four PD runs have no neural archive because no neural controller exists.
- Direct gate, membrane and PES update replay agrees within floating-point roundoff. All inspected neural values are finite. Canonical controller/model-interface source hashes are checked across runs.
- Eight Nengo/direct mean comparisons agree to a maximum relative difference of 1.128e-7. This is selected numerical agreement, not universal backend equivalence.
- The canonical runner's summary uses a suffix test that mislabels direct-online-pes as Nengo. Analysis corrects the descriptive backend label using the explicit wrapper field. Control calculations are unchanged. Original raw outputs remain available.
- Linear/constant archive gate/voltage slots are placeholders, not neuron measurements. Actual features are in `activity`. The biased-input wrapper records actual currents and corrects the canonical CSV diagnostic current fields for its new encoding.
- The neuron-family normalization issue, ground-truth noise scoring, motor lag, and sampled-data stability certificate remain unresolved experimental/theoretical extensions; this sweep does not fix them.

## Recommendation for the paper

Include the small constant-basis table, the exact reduced recursion, and a concise gain/development summary. Keep the full sweep plots and all development outcomes in this supporting audit. Preserve the original ten nominal results at G=1e5 and label new tuning separately. Do not hide the stronger non-neural control.

The manuscript is more rigorous after these changes, but its CMG-specific novelty claim is weaker. The next discriminating experiment should compare CMG with a classical dynamic residual at matched effective bandwidth, authority and teacher—not simply run more neuron families at unequal activity scales. A benefit under motor lag, true-state sensor noise or time-varying disturbances would be meaningful only with those controls matched.

## Reproduction

In PowerShell, set:

```powershell
$py = 'C:\Research\papers\ACC2027_Gate_Residual_Control\.venv\Scripts\python.exe'
$audit = 'C:\Research\papers\ACC2027_Gate_Residual_Control\experiments\gate_gain_sweep_2026-09-11'
& $py "$audit\reproduce_study.py" --jobs 2
& $py "$audit\regime_probe.py"
& $py "$audit\analyze.py"
& $py "$audit\finalize_audit.py"
```

The exact 71 case definitions are stored in `reproduction_cases.json`; the dispatcher selects the original appropriate wrapper for each. Completed cases are reused, avoiding overwriting frozen results. To regenerate from scratch, copy the audit's .py/.md/.json files (including reproduction_cases.json) to a separate directory immediately under the project's experiments folder, without results/analysis outputs, and use that directory as $audit. For the original extended 148-case plan, `sweep.py --jobs 2` runs missing cells, but that full factorial is not represented as complete here. Do not confuse it with this 71-run staged study; its larger output set would require a separate final count check.

The analysis Python is the project environment because the bundled document runtime lacks Matplotlib. Dependencies and exact source hashes are retained in the per-case manifests and final freeze manifest.
