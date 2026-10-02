# P1 APEX-v2 PyTorch Trace-Comparison Gate

Date: 2026-07-19

Purpose: compare the new APEX-v2 forward-parity scaffold against the successful PyTorch architecture logic on the same first SHD-wide HDF5 batch.

## Scripts

PyTorch exporter:

`C:\00_Research_\Neural_Networks_and_Learning\08_HyperLIF_Architectures\scripts\export_pytorch_first_batch_trace.py`

Comparison:

`C:\00_Research_\Neural_Networks_and_Learning\08_HyperLIF_Architectures\scripts\compare_pytorch_apex_v2_traces.py`

## Commands

```powershell
cd C:\00_Research_\Neural_Networks_and_Learning\08_HyperLIF_Architectures
C:\00_Research_\Neural_Networks_and_Learning\07_AdHyperLIF_Triage\.venv\Scripts\python.exe scripts\export_pytorch_first_batch_trace.py --device cpu --batch-size 32 --hidden-dim 64 --seed 1
C:\00_Research_\Neural_Networks_and_Learning\07_AdHyperLIF_Triage\.venv\Scripts\python.exe scripts\compare_pytorch_apex_v2_traces.py --apex-v2 results\apex_v2\apex_v2_forward_smoke_20260719_174512.csv
```

## Outputs

PyTorch trace CSV:

`C:\00_Research_\Neural_Networks_and_Learning\08_HyperLIF_Architectures\results\apex_v2\pytorch_first_batch_trace.csv`

Comparison CSV:

`C:\00_Research_\Neural_Networks_and_Learning\08_HyperLIF_Architectures\results\apex_v2\pytorch_vs_apex_v2_trace_compare.csv`

## Result

The structural comparison passed:

`PYTORCH_APEX_V2_TRACE_COMPARE_OK`

Summary:

- matched rows: `54`
- missing PyTorch rows: `0`
- missing APEX-v2 rows: `0`
- structural failures: `0`

Structural checks:

- architecture/neuron/readout row coverage
- feature dimensions
- logit shape
- finite feature/logit values

## State-Summary Comparison

This is not weight-identical trace parity yet. PyTorch and APEX-v2 initialize weights independently, so exact event/voltage/gate equality is not expected. The purpose of this gate is structural parity and qualitative state-behavior agreement.

Mean deltas across all 54 rows:

| Quantity | Mean absolute delta | Max absolute delta |
|---|---:|---:|
| events/sample | `39.767361` | `65.000000` |
| gate mean | `0.015508` | `0.028237` |

Mean state summaries by neuron:

| Neuron | PyTorch events/sample | APEX-v2 events/sample | PyTorch gate mean | APEX-v2 gate mean |
|---|---:|---:|---:|---:|
| LIF | `656.083` | `720.948` | `0.00000` | `0.00000` |
| HyperLIF | `550.875` | `584.312` | `0.38763` | `0.41581` |
| Adaptive HyperLIF | `241.688` | `262.688` | `0.24361` | `0.26196` |

The qualitative hierarchy matches the PyTorch story:

`LIF events > HyperLIF events > Adaptive HyperLIF events`

## Claim Discipline

Safe claim:

APEX-v2 now structurally reproduces the PyTorch architecture/readout surface on the same SHD-wide first batch: 54/54 rows match in feature dimensions, logit shapes, and finite outputs. Its state summaries preserve the expected event-efficiency ordering.

Unsafe claim:

Do not claim weight-identical trace parity or training parity yet. The next parity step is a shared-weight or exported-weight gate.

## Next Gate

- Export PyTorch weights for the same first-batch trace configuration, or initialize APEX-v2 from a serialized weight packet.
- Run value-level trace comparison for one architecture first: recurrent HyperLIF `hybrid_vr`.
- Then run one-seed frozen-trunk readout training smoke on PyTorch and APEX-v2 using the same features.

## Readiness Effect

At the time of this structural-trace note, P1 remained 94%. This was superseded later on 2026-07-19 by `P1_APEX_V2_SHARED_WEIGHT_PARITY_2026_07_19.md`, which completed the value-level shared-weight parity gate and moved P1 to 95%.
