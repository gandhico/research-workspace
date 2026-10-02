# APEX-v2 PyTorch-Parity Layer

Created: 2026-07-19

This folder is a new validation layer, separate from the older APEX-as-designed engine audit.

Purpose:

- follow the successful PyTorch architecture harness as closely as practical in Julia/CUDA;
- keep APEX-as-designed results intact and traceable;
- build a parity ladder before paper-grade APEX-v2 claims.

Current status:

- `APEXV2Parity.jl` implements forward-pass dense, recurrent/RSNN, and learnable-delay architecture families.
- `apex_v2_forward_smoke.jl` runs the first validation gate on the SHD-wide HDF5 cache.
- The first gate checks finite logits, PyTorch-style readout feature dimensions, events/sample, gate mean, voltage mean, and conductance mean.
- `apex_v2_readout_train_smoke.jl` freezes the forward features and verifies a finite, decreasing one-batch readout-head update.

Not done yet:

- gradient/training parity;
- ALIF/PLIF native Julia parity;
- paper-grade multi-seed runs;
- trace-level comparison against exported PyTorch intermediate states.

Recommended validation ladder:

1. G1/G2: shape/import/forward trace smoke.
2. G3: one-batch gradient sanity.
3. G4: one-seed training smoke.
4. G5: three-seed preflight.
5. G6: five-seed paper-grade run with paired tests.
