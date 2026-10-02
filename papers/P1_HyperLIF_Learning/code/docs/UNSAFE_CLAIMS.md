# Unsafe Claims — do NOT make these yet (Phase 0)

1. **No accuracy / task claims.** No dataset is wired yet. Nothing can be said about N-MNIST,
   SHD, CIFAR10-DVS, or any benchmark performance.

2. **Do NOT claim Adaptive HyperLIF beats LIF / HyperLIF.** The triage exists precisely to test
   this honestly; LIF is the standard baseline and the prior HPC evidence is comparability, not
   dominance.

3. **Do NOT claim the origin / `delta_reset` helps.** It is implemented and changes dynamics; its
   *benefit* is untested. Same for adaptive `event_threshold` in this harness.

4. **Do NOT claim full-network surrogate-BP is stable in general.** It is finite at short
   horizons here; long-horizon / near-solution training will need truncation, clipping, and the
   annealed surrogate. Treat unclipped long-horizon BPTT as unvalidated.

5. **Do NOT compare against the originally reported 98.13% / 91.02%.** Those were a surrogate-LIF
   pipeline (see the audit). The only valid "original" baseline is the original architecture
   **re-run inside this harness**.

6. **Do NOT report any number without** dataset / tier / split / seed and the dynamics metrics
   (events/sample, stability) alongside accuracy.
