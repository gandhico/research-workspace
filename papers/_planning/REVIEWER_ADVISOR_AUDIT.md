# Reviewer and Advisor Audit

Date: 2026-07-19

Sources consulted:

- TNNLS final decision and reviews: `tmp/tnnls_denied.txt`, extracted from `A_HyperLIF_denied_TNNLS.pdf`.
- Advisor email: `tmp/mail_outlook_2.txt`, extracted from the Outlook PDF.
- Existing audit: `TNNLS_REJECTION_AUDIT_AND_STRATEGY.md`.
- Research roadmap: `C:\00_Research_\Neural_Networks_and_Learning\RESEARCH_ROADMAP.md`.
- Learning paper evidence: `08_HyperLIF_Architectures`.
- Nengo paper evidence: `04_Adaptive_HyperLIF_Nengo\05_Adaptive_HyperLIF_Nengo_Paper`.
- Control paper evidence: `C:\00_Research_\Neuromorphic_Embodied_AI\01_HyperLIF_Gate_Residual\v2_clean`.

## Reviewer Concerns Converted to Requirements

| TNNLS concern | Current evidence | Remaining requirement |
|---|---|---|
| Practical advantage over existing SNN methods was unclear. | P1 now has temporal-task gains, gate-state readout, sparse-efficiency operating points, and architecture transfer. | Make the central claim practical and measurable: temporal state plus sparse efficiency. Stop claiming exact gradients eliminate surrogate training. |
| Novelty vs continuous RNNs and smooth gated systems was unclear. | HyperLIF preserves spike/reset semantics, event counts, gate readout, and Nengo/NEF compatibility. | Add a formal comparison table against coRNN, UnICORNN, LEM, Izhikevich/SRM, PLIF, GLIF, ALIF/LSNN, and surrogate-LIF. |
| Theory relied on simplifying assumptions. | P2 has exact parity, DB onset, fixed-point validation, and stable stepping. | Present theory as bounded propositions plus numerical validation. Do not oversell flux-balance as universal. |
| Biophysical claims were not supported. | Current evidence is computational and biologically inspired, not biophysically validated. | Remove "biophysical" from titles and abstracts unless real membrane-trace or HH/Izhikevich validation is added. |
| Experiments were MLP-only. | P1 includes feedforward, convolutional, recurrent, delay, and deep convres evidence/negative result. | Keep convres as a bounded negative/limitation unless dense full-data results improve. |
| No multi-seed statistics. | P1 has 5-seed sweeps; P2 has deterministic parity and capability matrices. | Every main learning/control result needs mean plus standard deviation or confidence intervals. |
| Baselines not contemporary enough. | LIF and ALIF are present; some control baselines are present. | Add PLIF or GLIF/learnable-threshold LIF for P1; strengthen robotics baselines for P3. |
| Theory not tied to ML benefit. | Gate readout, structural blindness, sparse efficiency, and control residuals now tie `r(t)` to function. | Put empirical mechanism before heavy theory in P1; reserve theory depth for P2. |

## Advisor Guidance Converted to Strategy

The advisor response asks for a publishing strategy: what to combine, what to separate, what order, and whether to use arXiv.

Recommended strategy:

- Combine the original TNNLS theory only where it supports P1 and P2.
- Separate P1 and P2 because reviewers for ML learning and Nengo/reference methods will expect different evidence.
- Separate P3 only if the control manuscript is strengthened with multi-seed, energy, ablation, and cross-platform results.
- Keep P4 conditional. It should not dilute P3 until learned/adaptive gate control is independently validated.
- Use arXiv after claims are corrected, not as a repository for a rejected-paper revision.

## Non-Negotiable Claim Discipline

Safe:

- HyperLIF provides a decodable continuous gate state that LIF structurally lacks.
- HyperLIF can improve temporal-task learning under controlled budgets.
- HyperLIF/Adaptive can move the accuracy-vs-spike-rate operating point.
- HyperLIF and Adaptive HyperLIF have exact Python-vs-Nengo parity under the stable stepping implementation.
- NengoCore custom-neuron compatibility is demonstrated; accelerated/hardware backends require custom kernels or are unsupported.

Not safe:

- Adaptive HyperLIF universally beats LIF.
- Exact differentiability removes surrogate-gradient needs.
- The old TNNLS N-MNIST/DVS numbers are real Adaptive HyperLIF results if they came from a surrogate-LIF path.
- The model is biophysically validated.
- Gate-state residual improvements are caused by the Adaptive mechanism when gate mode makes Adaptive inert.

## Missing Work That Matters Most

1. P1: Julia/APEX validation on byte-identical caches.
2. P1: at least one contemporary neuron baseline beyond LIF/ALIF.
3. P1 and P3: statistical reporting and failure counts.
4. P2: update IEEE manuscript with latest capability, PES, and backend findings.
5. P2: NEF ensemble-level validation for the calibrated HyperLIF candidate.
6. P3: connect the controller implementation to the Nengo/NEF reference path.
7. P3/P4: prove when Adaptive HyperLIF is active, not merely present.

