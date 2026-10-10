# ACC paper revision note: neuron-basis claims

## Mandatory correction before the next advisor draft

The current v14 abstract and neuron-family discussion report Izhikevich losses
of 162%/79%, roughly tenfold effort, and LIF-family activity below 0.1%. Those
numbers came from the archived family adapter. They are not an equal-PES-rate
comparison because its feature-scale conversion implemented the normalized
update `S*eta`, not `eta`.

Do not retain those numbers as evidence of an intrinsic neuron-family
difference. They may be mentioned only as an archived implementation result,
and there is little reason to spend paper space doing so.

The corrected Nengo conversion is

```
p = S a,            Theta = W/S,
Delta Theta = eta_N dt/N (y*−s) p^T,
eta_N = eta N/(dt S^2),
```

which gives `Delta W=eta(y*−s)a^T`, identical to the CMG/direct update.

## Recommended compact paper result

Use one compact mechanism table, not the complete 186-run matrix:

| Activity basis | X2 geometric-mean reduction | CF2 geometric-mean reduction | Interpretation |
|---|---:|---:|---|
| CMG, strict shared map | **37.30%** | **22.42%** | strongest cross-mission basis |
| static paired, no neuron | 11.88% | 4.75% | PES helps, but instantaneous features do not match CMG |
| constant, no neuron | 10.34% | 4.29% | persistence alone is insufficient |
| LIFRate, strict shared map | 0.45% | -0.03% | common current map is below its useful operating regime |
| LIFRate, threshold-aware | 24.11% descriptive; **15.77% on held-out X2 missions** | **11.37% held out** | strongest conventional alternative |

The threshold-aware settings were selected on 15 s X2 Roll and Hard45,
confirmed on those missions at 45 s, then frozen. X2 Full3/Hardstep/Yaw360 and
all five CF2 missions were held out. LIF, ALIF, and low-bias Izhikevich also
became useful, with held-out X2 reductions of 10.72%, 7.12%, and 6.20%, and
held-out CF2 reductions of 7.34%, 4.69%, and 1.45%, respectively.

## Recommended abstract sentence

> With exactly normalized PES, CMG reduces the five-mission geometric-mean
> error by 37.3% on X2 and 22.4% on CF2, compared with 11.9%/4.8% for an
> instantaneous non-neural paired basis. A threshold-aware LIFRate basis is the
> strongest conventional alternative (15.8% on held-out X2 missions and 11.4%
> on held-out CF2), supporting persistent, temporally structured activity—not
> conductance modulation alone—as the operative CMG advantage.

Use this only if the page budget permits the validation protocol. Otherwise
keep the abstract focused on the primary CMG result and put the corrected basis
study in the experiments section or supplement.

## Recommended replacement for the neuron-family paragraphs

> We first held the paired-current encoder, six features, decoder
> initialization, direct-equivalent PES rate, leak/projection, residual
> authority, and saturation gate fixed. For conventional outputs with native
> amplitude `S`, exact Nengo normalization requires
> `eta_N=eta N/(dt S^2)`. Under this strict map, CMG produced 37.3%/22.4%
> five-mission geometric-mean reductions on X2/CF2; constant and instantaneous
> paired non-neural PES bases reached only 10.3%/4.3% and 11.9%/4.8%.
> Untuned LIF, ALIF, and LIFRate were nearly neutral because activity occupied
> only 3--4% of unit-samples, while tonic Izhikevich activity degraded the
> low-error missions.
>
> To distinguish neuron identity from operating point, we selected current
> bias/gain and feature-filter time constant on 15 s X2 Roll and Hard45 runs,
> confirmed at 45 s, and froze the settings before the remaining missions and
> CF2. Every family then became useful. LIFRate was strongest, reducing error
> by 15.8% on the three held-out X2 missions and 11.4% across all held-out CF2
> missions. It remained active almost continuously; thresholded spiking units
> improved the larger-error missions but were neutral near the error floor.
> CMG nevertheless retained the best complete-mission result at comparable
> residual effort. Together with the non-neural controls, this supports a
> persistent, bounded, temporally structured activity basis as the useful CMG
> property. Because the prior conductance switch remained numerically
> inactive, the result is not attributed to conductance modulation alone.

## Claims now supported

- PES residual learning is portable across CMG, LIF, ALIF, LIFRate,
  Izhikevich, and analytic bases when each representation has an appropriate
  operating point.
- CMG is the best tested cross-mission basis under the common residual
  interface; it is not the only useful basis.
- CMG's advantage is not reproduced by constant persistence or instantaneous
  paired encoding alone.
- The evidence points to persistent **and temporally structured** continuous
  activity. It does not isolate current-dependent conductance as causal.

## Claims to avoid

- “Only CMG can learn with PES.” False after threshold-aware tuning.
- “Spiking neurons intrinsically worsen the controller.” False; their strict
  operating point was poor, and tuned LIF/ALIF/Izhikevich improve held-out
  missions.
- “The conductance term causes the tracking gain.” Not demonstrated.
- “The five-mission tuned X2 number is fully held out.” Roll and Hard45 were
  used for selection; the honest held-out X2 statistic uses Full3, Hardstep,
  and Yaw360.

## Page-budget recommendation

For a 6--7 page ACC paper, retain the primary CMG table/figure, add the compact
five-row table above, and move the full mission-by-mission matrix, tuning grid,
and telemetry plots to the reproducibility package. This adds a mechanism
result without turning the paper into a neuron-model survey.
