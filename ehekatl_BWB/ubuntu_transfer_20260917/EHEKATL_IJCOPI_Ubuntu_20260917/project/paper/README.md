# EHEKATL BWB optimization paper workspace

This directory is the paper-facing index for the EHEKATL BWB control research.
It does not replace the canonical controller code, raw logs, configuration
artifacts, or the stage-gated development record.

## Working research question

Why does an offline-optimal LQR provide only a small practical improvement in
X-Plane 12 when delay, hidden augmentation, constraints, operating-point drift,
and reload variability are present, and can regularized constrained
Data-Enabled Predictive Control (DeePC) close that implementation gap?

## Source-of-truth locations

- Raw X-Plane evidence: `../logs/` (immutable after collection)
- Frozen numerical artifacts and gates: `../configs/`
- Reproducible analysis and experiment code: `../scripts/`
- LQR runtime implementations: `../lqr/`
- DeePC work: `../deepc/`
- Authoritative stage record: `../docs/CONTROL_DEVELOPMENT_PROCESS.md`
- Paper research plan: `../docs/PAPER_RESEARCH_PLAN.md`
- Dataset allocation and hashes: `DATASET_REGISTRY.csv`
- Offline manuscript handoff: `../research_handoff_lqr_deepc/`

## Paper evidence rules

1. Every quantitative statement must map to a raw input, a frozen analysis
   method, and a generated result artifact.
2. Design, tuning, and held-out evidence remain distinct.
3. A safe execution pass is not a performance pass.
4. Failed gates remain visible and are never converted retrospectively into
   successful validation evidence.
5. Offline LTI datasets are labeled pre-X-Plane and never presented as flight
   logs.
6. Controller comparisons use common signals, constraints, operating points,
   disturbances, safety behavior, and statistical reporting.

## Current status

The pre-X-Plane LQR baseline, X-Plane identification campaign, frozen LQR and
DeePC runtimes, guarded integration evidence, direct demonstrations, and
prospective power audits are complete for the declared R3 scope. In X-Plane,
the roll LQR executed safely but achieved about 11.1 percent improvement in the
frozen matched-pair integral metric, below the predeclared 30 percent gate.
Both direct LQR and DeePC demonstrations subsequently passed their functionality
and safety gates, but their separate reloads do not establish superiority.
Stage 5 remains open and the manuscript reports that boundary explicitly.

Paper-facing generated outputs are reproduced with:

```bash
cd /home/ubuntu/GHYN/Xplane_controllers/EHEKATL_BWB_XP12
backstepping/ehekatl_xplane12_backstepping_bridge/.venv/bin/python -B \
  paper/generate_paper_results.py
```

The current full draft is `MANUSCRIPT_DRAFT.md`; generated tables and figures
are under `generated/`.
