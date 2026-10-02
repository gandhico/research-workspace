# References

## Project papers (NMSU — Contreras, Guerra, Garcia)
- **[Ref 1]** *Sample-data real-time hardware tests on the Quanser Aero2 platform
  for digital control* (Module 1 / HM04, EE-475/EE-551). Sampling, IMU bias/noise,
  ZOH, excitation, bias-corrected pitch state. LaTeX/PDF: place in `papers/`.
- **[Ref 2]** *Hardware-Oriented Modelling, Identification and Control of the
  Quanser AERO 2-DOF Platform* (mid-project). Trim search, pitch doublet, yaw
  chirp, coupled ARX, one-step vs free-run validation (Table I).
  Source: `aero2_paper_results/source_draft/conference_101719_updated.tex`.
- **[Ref 3]** *Modelling, Identification, and Control of the Quanser Aero2 System*
  (final / full technical report). Full nonlinear & linear models, ARX/DARX
  (Table II), validation/uncertainty, PD/LQR/LQG/MPC/backstepping/SMC/NMPC,
  hardware benchmark (Table IV). Source:
  `aero2_paper_results/14_latex_sections/full_integrated_paper_draft.tex`.

> The three PDFs were staged ephemerally and removed; the LaTeX sources above are
> the authoritative recoverable copies. Place rebuilt PDFs in `docs/papers/`.

## Classic control references (cited in Ref 1)
- K. J. Åström, B. Wittenmark, *Computer-Controlled Systems: Theory and Design*, Prentice Hall, 3rd ed., 1997.
- G. F. Franklin, J. D. Powell, M. L. Workman, *Digital Control of Dynamic Systems*, Pearson, 3rd ed., 2015.

## Cross-repo — Adaptive HyperLIF (surveyed in `10_neuromorphic_hyperlif.md`)
- Paper: *Robust Biophysical Spiking Neural Networks: The Adaptive HyperLIF Model*, TNNLS submission, Apr 2026.
- `…\Neural_Networks_and_Learning\01_Adaptive_HyperLIF` — **learning/identification** (Julia): paper impl, gate-eligibility e-prop, Hebbian, APEX V11 CUDA engine.
- `…\Neural_Networks_and_Learning\04_Adaptive_HyperLIF_Nengo` — **modelling** (Python/Nengo): clean neuron core + Nengo ports.
- `…\Neuromorphic_Embodied_AI\01_HyperLIF_Gate_Residual` — **control** (Python): PD + gate-state residual, +7.35% vs classical PD (quadrotor). Pure-numpy neuron in `v2_clean/.../neuron_dynamics.py`.

## SOTA references in this repo (`00_SOTA/`)
**Reviewed — canonical 2-DOF model validated** (see `02_modelling.md` → "Model
fidelity vs. SOTA"). All three below give the same canonical Quanser model:
- S.-K. Kim, C. K. Ahn, "Performance-Boosting Attitude Control for 2-DOF Helicopter
  Applications via Surface Stabilization," *IEEE TIE* 69(7), 2022 — `boosting attitude control 2DoF.pdf`.
- S.-K. Kim, K. S. Kim, C. K. Ahn, "Order Reduction Approach to Velocity Sensorless…
  PD-Type Attitude Stabilizer for 2-DOF Helicopter," *IEEE TII* 18(10), 2022 — `Order_Reduction_Areo2.pdf`.
- Z. Zhao, J. Zhang, Z. Liu, C. Mu, K.-S. Hong, "Adaptive NN Control of an Uncertain
  2-DOF Helicopter with Unknown Backlash-Like Hysteresis and Output Constraints,"
  *IEEE TNNLS*, 2022 — `Adaptive NN Control Aero2.pdf`. Table I gives Quanser params:
  J_p=0.0215, J_y=0.0237 kg·m²; M=1.075 kg; D_p=0.0071, D_y=0.0220 N/V; l=0.0071 m;
  K_pp=0.0011, K_py=0.0021, K_yp=−0.0027, K_yy=0.0022 N·m/V. (RBF-NN + BLF — also
  relevant to the neuromorphic phase.)

**Not yet deep-read** (catalogued; review for Phase 10 / control comparison):
`RL_Aero2.pdf`; `Book_NN_Control_Robot.pdf` (108 MB, general NN-control background);
journal PDFs `eng7040170`, `ajss v11i1 300`, `aei-2025-0003`.

## Original implementation
`C:\02_Research\01_Robotics_Quanser\01_Aero2` — canonical: `aero2_clean/` (M1–M8),
`aero2_minimal_control/` (control + Table IV), `aero2_paper_results/` (docs).
