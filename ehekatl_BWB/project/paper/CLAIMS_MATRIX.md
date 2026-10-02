# Claims and evidence matrix

Status values are `SUPPORTED`, `LIMITED`, `FAILED`, and `PLANNED`.

| ID | Candidate paper claim | Status | Primary evidence | Claim boundary |
|---|---|---|---|---|
| C01 | Thesis-model LQR is stable in the offline continuous-time LTI simulations. | SUPPORTED | `research_handoff_lqr_deepc/.../data/lti/` and summaries | Pre-X-Plane only. |
| C02 | Increasing longitudinal input penalty to R=1 reduces the small-case elevator demand to 9.45 deg without saturation. | SUPPORTED | `summary_Rlon_1p0_Rlat_1p0.txt` | Supplied LTI model and declared initial condition only. |
| C03 | Direct transfer of nominal LQR conclusions to X-Plane is invalid. | SUPPORTED | Stage 2--5 control-path, delay, augmentation, model, and operating-point evidence in the development record | Demonstrates implementation gap, not universal LQR inadequacy. |
| C04 | The R3 35-Hz measured roll cascade is repeatable on held-out data. | LIMITED | Discrete-cascade training and confirmation artifacts | R3, local perturbations, measured cascade, declared bounds only. |
| C05 | The R3 roll LQR executes safely with exact runtime behavior and fallback availability. | SUPPORTED | `rich_R3_roll_lqr_pilot_20260712_200705.csv` and analyzer | Integration/safety only; no disturbance-performance claim. |
| C06 | The frozen R3 roll LQR provides at least 30 percent integral disturbance improvement over backstepping. | FAILED | Matched baseline/LQR pair and frozen scorer | Observed improvement about 11.1 percent; do not weaken the gate. |
| C07 | The observed 9--11 percent effect is identifiable with longer separate-run pulse tests. | FAILED | Statistical power and pulse-count audits | Up to 48 pulses/controller remained underpowered. |
| C08 | Regularized constrained DeePC improves held-out X-Plane performance over frozen LQR. | PLANNED | Future frozen DeePC protocol and held-out evidence | No claim until offline and online gates pass. |
| C09 | The first provisional P-only DeePC passes the predeclared 243-case robust offline improvement gate. | FAILED | `configs/rich_R3_deepc_hyperparameter_scan.json` entry Ru=0.01/Rdu=0.05 | Median ratio 0.8068, but worst ratio 0.9065 exceeded the unchanged 0.90 gate. |
| C10 | The redesigned P-only DeePC passes the unchanged 243-case frozen-model gate against LQR. | LIMITED | `configs/rich_R3_deepc_hyperparameter_scan.json` and `configs/rich_R3_deepc_uncertainty_replay.json` | Offline validated cascade only; worst/median integral ratios 0.8953/0.7881. No X-Plane claim. |
| C11 | The frozen P-only DeePC runtime meets the R3 35-Hz observe-only integration gate. | LIMITED | `logs/rich_R3_roll_deepc_observe_20260810_122949.csv` and `scripts/analyze_rich_r3_roll_deepc_observe.py` | Timing, integration, exact-history, constraints, and fallback readiness only; no DeePC control was sent. |
| C12 | The guarded frozen P-only DeePC executes safely and produces a measurable, recovered response in one R3 design pilot. | LIMITED | `logs/rich_R3_roll_deepc_pilot_20260810_144136.csv` and frozen pilot analyzer | One design pilot only; excluded from confirmation and not evidence of superiority over LQR. |
| C13 | A statistically powered DeePC-versus-LQR confirmation is practical under the available R3 pulse protocols. | FAILED | `configs/rich_R3_deepc_separate_power.json`, `configs/rich_R3_deepc_paired_power.json`, and `configs/rich_R3_deepc_paired_iae_power.json` | Separate reloads require 48 pulses/controller; paired IAE requires 24/controller and unvalidated mode switching. No benchmark flight authorized. |
| C14 | The frozen P-only DeePC executes directly at 35 Hz in X-Plane with bounded commands, exact runtime/history behavior, no safety event, and verified restoration. | LIMITED | `logs/direct_deepc_20260810_150657.csv` and frozen pilot analyzer | One user-requested direct demonstration at R3; not independent confirmation or superiority evidence. |
| C15 | The measured-cascade roll LQR executes directly at 35 Hz in X-Plane with bounded commands, exact runtime replay, no safety event, and verified restoration. | LIMITED | `logs/direct_lqr_20260810_151244.csv` and frozen matched-run analyzer | One user-requested direct demonstration at R3; unmatched to the DeePC run. |
| C16 | The direct DeePC demonstration outperforms the direct LQR demonstration in X-Plane. | LIMITED | `paper/generated/direct_demonstration_metrics.json` | Descriptive values favor DeePC slightly, but separate reloads preclude causal or statistical superiority claims. |

This matrix must be updated when a material analysis changes a claim's status
or boundary.
