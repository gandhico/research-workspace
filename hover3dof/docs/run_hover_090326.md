# Hover 3-DOF

Environment
cd C:\Research\hover3dof\nengo_gui_hil_2026-08-29
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

# PD baseline, roll mission, real hardware
```
.\launch_hover_experiment.ps1 -Mission roll -Controller pd -Mode hardware -ConfirmHardwareReview
```

# CMG-PES (neuromorphic residual), roll mission, real hardware — your best validated result
````
.\launch_hover_experiment.ps1 -Mission roll -Controller nengo-pes -Mode hardware -ConfirmHardwareReview
````

# Baselines GUI Missions
```
.\launch_hover_experiment.ps1 -Mission hover    -Controller pd -Mode hardware -ConfirmHardwareReview   # 5s
.\launch_hover_experiment.ps1 -Mission roll     -Controller pd -Mode hardware -ConfirmHardwareReview   # 8s — already confirmed working
.\launch_hover_experiment.ps1 -Mission full3    -Controller pd -Mode hardware -ConfirmHardwareReview   # 12s
.\launch_hover_experiment.ps1 -Mission hard45   -Controller pd -Mode hardware -ConfirmHardwareReview   # 12s
.\launch_hover_experiment.ps1 -Mission hardstep -Controller pd -Mode hardware -ConfirmHardwareReview   # 12s
.\launch_hover_experiment.ps1 -Mission yaw360   -Controller pd -Mode hardware -ConfirmHardwareReview   # 45s — longest, riskiest, save for last
```

Time Adaptive
```
.\launch_hover_experiment.ps1 -Mission roll -Controller pd -Mode hardware -ConfirmHardwareReview -DurationOverride 20

.\launch_hover_experiment.ps1 -Mission hover    -Controller pd -Mode hardware -ConfirmHardwareReview -DurationOverride 10
.\launch_hover_experiment.ps1 -Mission roll     -Controller pd -Mode hardware -ConfirmHardwareReview -DurationOverride 15
.\launch_hover_experiment.ps1 -Mission full3    -Controller pd -Mode hardware -ConfirmHardwareReview -DurationOverride 20
.\launch_hover_experiment.ps1 -Mission hard45   -Controller pd -Mode hardware -ConfirmHardwareReview -DurationOverride 20
.\launch_hover_experiment.ps1 -Mission hardstep -Controller pd -Mode hardware -ConfirmHardwareReview -DurationOverride 20
.\launch_hover_experiment.ps1 -Mission yaw360   -Controller pd -Mode hardware -ConfirmHardwareReview -DurationOverride 45

```

