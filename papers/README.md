# HyperLIF Paper Portfolio

Organized 2026-08-18 from `D:\NMSU_backups\Backup\00_Research_\{Neural_Networks_and_Learning, Neuromorphic_Embodied_AI}`.
Source folders are untouched on the backup drive — everything here is a copy (raw per-timestep
CSV logs and `.venv` excluded; only `_summary.json`/`_config.json` + figures kept from P3's logs).

| Folder | Paper | Readiness (updated 2026-08-19) | Draft |
|---|---|---:|---|
| `P1_HyperLIF_Learning\` | HyperLIF Learning (temporal SNN architecture) | Ready for advisor review — all tables verified against raw data, Julia/APEX code included | `main.tex` |
| `P2_HyperLIF_Nengo\` | Nengo/NEF Reference Implementation | 91% per its own claim-by-claim audit; remaining gap is submission mechanics | `paper\main.tex` |
| `P3_Gate_Residual\fixed_adaptive\` | Gate-state residual control — fixed decode + adaptive-boundary result | Ready — internal contradiction fixed, PDF rebuilds clean, code independently reproducible | `paper\main2.tex` |
| `P3_Gate_Residual\learned\` | Gate-state residual control — online-learned decode (**+86.7% CF2 / ~57% X2** error reduction) | Ready — generating code recovered and included; not yet fused with `fixed_adaptive` (needs advisor input, see fusion plan) | `paper\main.tex` |
| `_planning\` | Portfolio decision, P3 fusion plan, progress register, claim audits, peer-review audit, advisor meeting guide | — | see `PAPER_PORTFOLIO_DECISION.md`, `P3_FUSION_PLAN_2026_07_20.md`, `PEER_REVIEW_AUDIT_2026-08-19.md` |
| `_share_2026-08-18\` | Advisor package — 4 PDFs, 4 code zips, cover note, reproducibility table | — | ready to send |

## Active work (updated 2026-09-16)

| Folder | Paper | Status |
|---|---|---|
| `ACC2027_Gate_Residual_Control\` | CMG–PES bounded residual on quaternion PD (ACC 2027 target) | **v14 (2026-09-21), 7 pages**, `paper\v14_2026-09-21_izhikevich\` (+ `ACC2027_v14_overleaf.zip`, `AUDIT_v14_2026-09-21.md`; v13 = `paper\v13_2026-09-20_robustness\`). v14 adds the Izhikevich rival basis under the CMG protocol (amendment A3, 33 runs, reduced grid): on the tuned baseline it is level with or below CMG on Full3/Hard45 and far worse on Roll/Yaw360 (geo-mean error x2.6 X2 / x1.8 CF2 the baseline's) at ~10x CMG's effort; the gate is not CMG-specific; report `experiments\final_robustness_gating_2026-09-20\REPORT_IZHIKEVICH_A3.md`. Since v13: saturation-aware output gate; noise and disturbance re-run on the tuned PD+ff (true-attitude error, paired seeds); **CF2's rho=3 row had been run at beta=0.05, not the stated 0.5** — with the gate CF2 reaches 36.5% noise-free at beta=0.5 but diverges on Hardstep under noise, so beta=0.2 (22.4%) is used; noise erases the benefit on Roll/Yaw360 (only Full3/Hard45 keep 11%/4%); Hardstep ceiling is parity (12 gate configurations, −2.1…+0.3%). Two figures (vehicle photos, CMG-unit topology) moved to `\iffalse` for space. Experiments, pre-registration and figures: `experiments\final_robustness_gating_2026-09-20\README.md`. |
| `P5_DualSelfTuning_Residual_CMG\` | Dual CMG self-tuning PID + CMG–PES residual (journal/2028 track) | v0–v4 and a 6-DOF pilot **frozen** 2026-09-12 (P5-QUAT-6DOF-2026-09-12-R1). Gated dual v2 beats the residual by 2–4%; the published STN-PID-PES law does not transfer (closed-loop sign bias). High-fidelity MuJoCo twin track not started. |

## P3 status — not yet one paper

`fixed_adaptive\` and `learned\` are **two separate `.tex` sources that your own
2026-07-20 plan (`_planning\P3_FUSION_PLAN_2026_07_20.md`) decided to merge** into one
fused manuscript (fixed = safety, adaptive = boundary, learned = performance headline).
That merge hasn't happened yet — Phase 0 in the fusion plan. Two more things before P3 is
submittable:

1. `fixed_adaptive\paper\main2.tex` still contains the disproven "Adaptive HyperLIF
   outperforms fixed HyperLIF" claim (Contribution 3). The fix is already written —
   `fixed_adaptive\paper\sec_mujoco_gate_mechanism.tex` — it just needs `\input`ing after
   `\section{Results}`. See `fixed_adaptive\docs\2026_07_05_results_params_runners.md` for
   the full correction writeup.
2. Four scope decisions are still open (venue, hardware-as-pillar, cross-substrate depth,
   learned-gate-as-main-result) — see `_planning\P3_FUSION_PLAN_2026_07_20.md` §7.

## Pre-existing (untouched)

`conferences\`, `journals\ToE_DigitalTwin\` (the Quanser workstation IEEE ToE paper), and
`reviews\Deep_MPC_Collision_Avoidance_UAV_Swarm\` were already here before this reorg —
unrelated to the HyperLIF portfolio, left as-is.
