# QBot — Runners & Launchers Index

**No runners exist yet.** This platform currently has only the theoretical
foundations paper — no offline/twin/hardware code has been started.

Pulled forward from
`D:\NMSU_backups\Backup\00_Research_\Neuromorphic_Embodied_AI\12_QBot\`
on 2026-08-21. Sole content: `paper_math\qbot_models_control_ieee.tex`
(+ compiled `.pdf`) — "Quanser QBot Differential-Drive Robot: Hardware
Physics, Identification, Modelling, and the Complete Controller Suite"
(Gandhi Contreras). Covers the physics/identification/modelling derivation
and a full controller suite (PID/LQR/LQG/backstepping/SMC/NMPC) **on paper
only**.

Note: the Julia bridge board registry (`julia_bridge\README.md`) distinguishes
`qbot2e` / `qbot3` (legacy, host-HIL) from `qbot_platform` (newer, streamed,
onboard HIL) — confirm which physical unit is in the lab before naming a
future code folder, the two have different transport paths.

## Next step, when ready to build

Follow the same shape as `pendulum\` or `qdrone\`: `runners\run_offline_benchmark.py`
using the shared `_shared\quanser_residual_campaign` module (see
`qdrone\RUNNERS.md` §3 for how that dependency resolves), then a digital-twin
runner, then a hardware runner behind explicit arming.
