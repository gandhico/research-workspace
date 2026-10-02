# Omnicopter mission runners

## Recommended launchers when PowerShell scripts are disabled

Every named mission below also has a `.cmd` launcher. These launch Python directly and do not change PowerShell execution policy. Use a plain underscore in filenames: `quaternion_sign.cmd`.

```powershell
Set-Location 'C:\Research\omnicopter\mujoco\control\runners'
.\quaternion_sign.cmd

# Any named mission: replace .ps1 with .cmd in the stage lists below
.\circle_yaw_360.cmd
.\circle_yaw_360.cmd -Headless

# Headless campaigns, stopping at the first nonpass
.\campaign_baseline.cmd
.\campaign_all.cmd
.\campaign_pes.cmd

# List missions or run a smaller campaign using the Python CLI options
.\run.cmd --list
.\run.cmd --max-stage 3
```

Named `.cmd` mission launchers accept either `-Headless` or `-DryRun`; campaign launchers accept `-DryRun`. For custom output paths, use `.\run.cmd --mission hover --output 'C:\path\to\new_folder'` and add `--view` if desired. The PowerShell-only options described later apply to `.ps1` files.

## PowerShell script alternative

Each named PowerShell runner opens one live MuJoCo mission and saves its measurements. These scripts use the existing MuJoCo Python environment and locate missions.py relative to themselves; no previously defined shell variables are needed.

Open PowerShell, then run:

```powershell
Set-Location 'C:\Research\omnicopter\mujoco\control\runners'
```

Choose one command at a time from the stages below. Each mission starts with a hold and ends with a settling hold; the window closes at the end. Space pauses/resumes. Closing the window early aborts the run. Rotations use fixed world axes relative to the model's initial attitude.

## Stage 0: Hover and quaternions

```powershell
.\hover.ps1
.\quaternion_sign.ps1
```

## Stage 1: Translation

```powershell
.\translate_x.ps1
.\translate_y.ps1
.\translate_z.ps1
```

## Stage 2: Small attitude changes

```powershell
.\attitude_x_15.ps1
.\attitude_y_15.ps1
.\attitude_z_15.ps1
```

## Stage 3: Large attitude changes

```powershell
.\attitude_x_45.ps1
.\attitude_y_45.ps1
.\attitude_y_90.ps1
.\attitude_x_180.ps1
```

## Stage 4: Complete rotations

```powershell
.\yaw_360.ps1
.\yaw_minus_360.ps1
.\spin_x_360.ps1
.\spin_y_360.ps1
```

## Stage 5: Spatial trajectories

```powershell
.\circle.ps1
.\figure_eight.ps1
.\helix.ps1
.\circle_yaw_360.ps1
```

## Stage 6: Disturbance recovery

```powershell
.\hover_push.ps1
.\circle_yaw_push.ps1
```

## Stage 7: Speed exploration

```powershell
.\yaw_360_24s.ps1
.\yaw_360_12s.ps1
.\yaw_360_6s.ps1
```

The historical pose-only baseline passed stages 0-6 and yaw_360_24s, then failed the 12-second tracking gates. After analytic velocity/acceleration feedforward was added, the final PD campaign passed all 25 missions, including yaw_360_6s. Running an individual mission bypasses earlier-stage prerequisites. These results apply to simulation, not hardware qualification.

## Campaign runners

Campaigns run headlessly, in order, stopping at the first failed or aborted mission:

```powershell
# Baseline: stages 0 through 6 (22 missions)
.\campaign_baseline.ps1

# Full campaign: stages 0 through 7 (25 defined missions)
.\campaign_all.ps1

# Matched full campaign with the canonical online-PES residual
.\campaign_pes.ps1

# A smaller campaign: stages 0 through 3
.\run.ps1 -Campaign -MaxStage 3
```

Both modes use the same mission gates and bounded eight-rotor allocator. A failed gate returns a nonzero exit code.

## Options

The generic PowerShell runner accepts `-Controller pd` (default) or `-Controller cmg-pes`. PES settings are `-Beta`, `-LearningRate`, and `-Leak`; selected values are recorded in the artifacts.

```powershell
.\run.ps1 -Campaign -MaxStage 7 -Controller cmg-pes -Beta 0.05 -LearningRate 0.0008
```

```powershell
# Any named mission can run without a viewer
.\circle_yaw_360.ps1 -Headless

# List every mission and its total simulation duration
.\run.ps1 -List

# Generic runner accepts any mission name
.\run.ps1 -Mission spin_x_360

# Preview the exact Python command without starting simulation
.\yaw_360.ps1 -DryRun
.\campaign_all.ps1 -DryRun

# Optional output directory: it must not already exist
.\hover.ps1 -Headless -Output 'C:\Research\omnicopter\mujoco\control\output\my_hover_trial'
```

All runners accept -Python 'C:\path\to\python.exe' if the environment moves. It must contain MuJoCo and NumPy. The default interpreter is C:\Research\papers\ACC2027_Gate_Residual_Control\.venv\Scripts\python.exe.

Results default to a new timestamped folder under [control/output](../output): campaign.json, manifest.json, and each mission's trace.csv and summary.json. Headless and viewer modes both record results. To generate a report after a run, use the printed results path:

```powershell
& 'C:\Research\papers\ACC2027_Gate_Residual_Control\.venv\Scripts\python.exe' 'C:\Research\omnicopter\mujoco\control\campaign_report.py' 'C:\path\printed\after\RESULTS'
```

For the campaign design and gates, see [MISSION_CAMPAIGN.md](../MISSION_CAMPAIGN.md). For previous measurements, see [the baseline report](../output/campaign_initial_20260904/REPORT.md).
