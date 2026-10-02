# HyperLIF D: to C: research audit

Date: 2026-08-21  
Scope: the three D: research roots supplied for HyperLIF learning, Nengo parity, and gate-residual flight control.

## Outcome

The C: paper workspace now contains the principal reproducible code and evidence needed for the HyperLIF papers and the 2026-08-22 laboratory presentation. Existing C: manuscripts and rebuilt PDFs were preserved when they were newer or intentionally different; no existing file was overwritten.

## Resolved source roots

- `D:\NMSU_backups\Backup\00_Research_\Neural_Networks_and_Learning`
- `D:\NMSU_backups\Backup\00_Research_\Neuromorphic_Embodied_AI\01_HyperLIF_Gate_Residual`
- `D:\NMSU_backups\Backup\02_Research\00_Code_Ecosystem\neuromorphic-robotics-control`

## Audit matrix

| Paper area | D: authoritative area | C: destination | Final status |
|---|---|---|---|
| P1 learning baseline | `07_AdHyperLIF_Triage` | `P1_HyperLIF_Learning\code` | 940/940 audited files matched exactly before supplementation. |
| P1 architecture/APEX extensions | `08_HyperLIF_Architectures` | `P1_HyperLIF_Learning\code` | Missing results, scripts, architecture sources, Julia checks, documentation, and six APEX-v2 HDF5 fixtures copied. Source `__pycache__` bytecode was deliberately excluded. |
| P2 Nengo paper | `04_Adaptive_HyperLIF_Nengo\05_Adaptive_HyperLIF_Nengo_Paper` | `P2_HyperLIF_Nengo` | 140/141 files exact; only `paper\main.pdf` differs because C: contains a rebuilt PDF. Source and evidence are complete. |
| P3 fixed/adaptive controller | `v2_clean` | `P3_Gate_Residual\fixed_adaptive` | 151 result/evidence files now match exactly. C: `paper\main2.tex` was retained because it is newer/corrected. |
| P3 learned gate controller | neuromorphic-robotics-control authoritative dependency chain | `P3_Gate_Residual\learned` | All nine canonical controller/model/result dependencies checked were exact. Extra D: scripts were exploratory or older and are not required by the C: runners. |

## Files promoted to C:

### P1 HyperLIF learning

- 98 result files total now mirrored from the architecture extension tree, including six APEX-v2 HDF5 validation fixtures.
- 13 experiment/analysis scripts.
- 7 Python architecture source files; 7 compiled `__pycache__` files intentionally omitted.
- 11 Julia validation files.
- 2 architecture documentation files.
- 3 top-level research reports: advisor briefing, dense-roster insights, and Paper 2 report.

### P3 gate residual

- 44 previously missing fixed/adaptive evidence files copied into `fixed_adaptive\results`.
- Copied payload: 1,518,389,408 bytes (about 1.414 GiB).
- Final fixed/adaptive results comparison: 151/151 files exact by SHA-256/size check.

## Intentional divergences preserved

- P1 C: manuscript/IEEE paper material is newer than the D: copy; it was not replaced.
- P2 `paper\main.pdf` is a rebuilt artifact and does not byte-match D:, while the underlying source/evidence does.
- P3 `fixed_adaptive\paper\main2.tex` on C: contains newer corrections and was not replaced.
- Generated Python bytecode caches and unrelated exploratory/legacy scripts were not copied.

## Verified headline evidence used in the presentation

- Learning: SHD 0.484 to 0.637; DVS-Gesture-32 0.698 to 0.818; gate-only DVS-32 LIF 0.131 versus HyperLIF 0.776.
- Fixed gate: Crazyflie score 0.287391 to 0.266117 (7.4% lower); Skydio X2 0.299286 to 0.282060 (5.8% lower). The residual is near-silent, so the honest interpretation is mostly selective half-PD detuning.
- Learned gate, Crazyflie Hard45: classical 0.287391; fixed 0.266117; STN-PID-PES 0.047864; online PES 0.038258; e-prop 0.038215.
- Learned gate, Skydio X2: classical 0.299286; fixed 0.282060; online PES 0.129264. STN-PID-PES remains approximately classical on X2.
- Robustness: the aggressive target wins smooth tracking but diverges on Crazyflie hard steps; balanced and strong-damping targets trade peak performance for command robustness.

## Open experimental item

Hardware validation on a physical Aero2/static quad remains pending. The current portability evidence is exact Python/Nengo parity on NengoCore; OpenCL, Loihi, and NengoDL require custom-neuron/backend engineering before claiming deployment portability.

## Presentation handoff

The meeting deck is `HyperLIF_Neuromorphic_Flight_Control.pptx` in this folder. It contains 12 slides with source notes, local MuJoCo airframe renders, minimal text, and the verified comparisons above. The final overflow test passed and all slides were visually inspected.
