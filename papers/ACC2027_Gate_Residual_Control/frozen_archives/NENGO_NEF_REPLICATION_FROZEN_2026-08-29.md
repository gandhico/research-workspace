# Frozen Nengo/NEF replication

- Canonical archive: `C:\Research\papers\ACC2027_Gate_Residual_Control\frozen_archives\nengo_nef_replication_CANONICAL_FROZEN_2026-08-29.zip`
- Size: 140,333,100 bytes
- SHA-256: `AE7744C7E5BF31B62AB95F72A31F5338A9C1102DE1D71F2DDF2C0D056F973E9E`
- Captured source: `C:\Research\papers\ACC2027_Gate_Residual_Control\experiments\nengo_nef_replication_2026-08-29`

The earlier archives without `CANONICAL` are retained as pre-final checkpoints.
The canonical archive includes the corrected direct-reference PES-error logging
semantics and final reproduction commands; neither change affects any of the 24
baseline/Nengo campaign results.

The archive contains the Nengo CMG neuron, built-in-PES decoder, matched MuJoCo
runner, resumable campaign runner, compiler/plotter, equivalence audit, tests,
24 completed 45-second matched runs, all logged neural/controller signals,
compiled tables, 25 plots, and the full progress/equations document.

## Code SHA-256

- `nengo_cmg.py`: `4A82CB87139C174899E057ADE887E24D57B4982576263D0C2149F3F8FCA13F4D`
- `run_mujoco_nef.py`: `CA4069FFF33B4D70997DC35B3A5290D7298DCB2A2EC8FF37AC408D2700AABD4F`
- `run_campaign.py`: `F069D02036DDE09718FCE43EF8AD6A93467FF61F107FDDFD5AE6DAD6CFCE6FEA`
- `compile_and_plot.py`: `66682B0A4F708A50F140DFF28C2742DC53FE9D5B161101DC0E331DC4AC1D2499`
- `verify_archived_equivalence.py`: `69AF1748A3F4BE2930D110634A9821AF48AA66DDD94D3C687899618F4BC05CC9`
- `test_nengo_cmg.py`: `E1F577A27FB13B7DC16110F3042997F08EE40271615F39DC73BDB0E142A03595`

## Verification

- Two numerical conformance tests pass.
- The worst difference from the archived direct-CMG/PES mean-error result is
  2.012921 parts per million.
- No hardware interface is imported or accessed by this experiment.
