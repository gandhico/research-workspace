# Frozen 3DOF Hover PD--CMG campaign

Frozen on 2026-08-29 before starting the Nengo/NEF replication work.

## Immutable archive

- Archive: `C:\Research\hover3dof\frozen_archives\pd_cmg_focused_final_round_FROZEN_2026-08-29.zip`
- Archive size: 51,869,410 bytes
- SHA-256: `D2C6E78211F60E669DA1C86D285656337B5E03A2E676C029D9AE2343CA0AB4A1`
- Source captured: `C:\Research\hover3dof\pd_cmg_focused_final_round_2026-08-28`

The archive contains the runner, source, tests, documentation, all raw hardware
traces and summaries, the compiled campaign tables, and the available final
plots. It was created only after re-running the campaign compiler.

## Frozen inventory

- Recorded hardware-run directories: 50
- `trace.csv` files: 50
- `summary.json` files: 50
- Compiler-valid runs: 26
- Candidate PD/PD-CMG pairs: 16
- Compiler-valid matched pairs: 14
- Safety-aborted runs retained: 6
- PD-CMG traces with the complete neuron schema: 18

Compiled tables are in the archived copy of:

- `results\compiled\campaign_runs.csv`
- `results\compiled\campaign_pairs.csv`
- `results\compiled\campaign.json`

## Frozen code identities

- PD/CMG hardware runner SHA-256:
  `679180F559D449DBB671A4F9E0B725EB0EDF23CE1F91E64288EDCE2095059359`
- Quaternion-PD and allocator source SHA-256:
  `B4AA3F0F597DB8D7B65FB027306E7AE78871BCDA493E80CD14052020D84C96D3`
- Campaign compiler SHA-256:
  `C237BD3C91AFD923582B8D5CE2B38054482492A209D4DA2B21CEEA62C486C29A`
- Original LQR hardware runner remained untouched; SHA-256:
  `A20DBB24A6DA87AE3A4332CDE5E8C9B5E2CB4ADA022C0A3F1875F55DE93A6446`

## Results frozen for reporting

The strongest repeatable PD-CMG hardware result is the Roll mission. Two
independent authority ladders produced mean-error improvements of 9.11%,
12.15%, 21.67% and 7.50%, 10.07%, 19.57% at 0.3, 0.6, and 1.2 V residual
caps, respectively. The two 1.2 V trials average approximately 20.62%.

The matched fixed-bias Hard45 ladder completed normally. Its 1.2 V result
improved mean error by 1.56% and maximum error by 1.75%. The matched Full3
ladder also completed; its 1.2 V result improved mean error by 1.57% while
worsening maximum error by 2.30%, which must be reported as a tradeoff.

The two stability-priority Yaw360 runs were only 10 s qualification segments,
not complete missions and not final matched comparisons. They achieved mean
errors of 3.040 and 3.079 degrees with pitch/roll allocator scale equal to 1,
but the raw-yaw home mismatch prevented the complete mission.

The final shaped Hardstep PD run
`pd_armed_20260828_141406` completed the full 25 s / 5,000 samples with no
safety abort. It used `reference_scale=0.7`, a 0.5 s cubic transition,
stability-priority allocation, and a 2 V motor floor. Its mean quaternion-angle
error was 24.187 degrees and its maximum was 67.669 degrees. This is explicitly
the `Hardstep-0.7-shaped` mission, not the canonical discontinuous Hardstep.
No matched CMG run exists for this shaped mission.

## Frozen plots

The archive contains the four matched plots available at freeze time:

- `results\plots\final_matched\hard45_pd_vs_pd_cmg.png`
- `results\plots\final_matched\hard45_pd_cmg_neurons.png`
- `results\plots\final_matched\full3_pd_vs_pd_cmg.png`
- `results\plots\final_matched\full3_pd_cmg_neurons.png`

## Scientific boundaries

- Do not pair runs across the fixed-bias and stability-priority allocator generations.
- Do not report partial Yaw360 qualifications as completed missions.
- Do not call `Hardstep-0.7-shaped` the canonical Hardstep mission.
- Retain all aborted and dry-run records; they document safety and protocol development.
- Any future uniform paper table should rerun both PD and PD-CMG under the same allocator,
  mission definition, duration, authority cap, and reset/home procedure.
