# High-Definition Haptic Device — Runners & Launchers Index

**No runners exist yet.** This platform currently has only the theoretical
foundations paper — no offline/twin/hardware code has been started.

Pulled forward from
`D:\NMSU_backups\Backup\00_Research_\Neuromorphic_Embodied_AI\13_High_Definition_Haptic_Device\`
on 2026-08-21. Sole content: `paper_math\haptic_hd_models_control_ieee.tex`
(+ compiled `.pdf`) — "High-Definition Haptic Device: Hardware Physics,
Identification, Modelling, and the Complete Controller Suite" (Gandhi
Contreras). Covers the physics/identification/modelling derivation and a
full controller suite (PID/LQR/LQG/backstepping/SMC/NMPC) **on paper only**.

Per `julia_bridge\README.md`, this device is `daq_mediated` in the Julia
bridge's board registry (QUARC-era: opens via a Q8-class DAQ card type, no
product-specific card) — relevant once code exists.

## Next step, when ready to build

Follow the same shape as `pendulum\` or `qdrone\`: `runners\run_offline_benchmark.py`
using the shared `_shared\quanser_residual_campaign` module (see
`qdrone\RUNNERS.md` §3 for how that dependency resolves), then a digital-twin
runner, then a hardware runner behind explicit arming.
