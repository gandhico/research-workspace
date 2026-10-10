# Tomorrow morning execution checklist

## 1. Verify the environment (5 minutes)

```powershell
cd C:\Research\papers\ACC2027_Gate_Residual_Control
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\scripts\smoke_all.ps1
```

Expected: all tests pass and six MuJoCo backends finish.

The pendulum QLabs closure matrix is already complete. Do not rerun it tomorrow
unless checking reproducibility; its canonical report is
`results\reports\pendulum_qlabs_matched20.md`.

## 2. Freeze the scientific language (10 minutes)

Use the title **Online PES-Adapted Neuromorphic Membrane–Gate Residual Control
for Actuator-Constrained UAV Quaternion Attitude Tracking**.
Call the enhanced Crazyflie result **CF2 four-rotor
authority design study**. Never call it stock CF2 hardware.

## 3. Launch the priority experiments

Run the robustness matrix first because the headline nominal results already
exist:

```powershell
.\scripts\run_robustness_matrix.ps1
```

Then launch the mission matrices:

```powershell
.\scripts\run_x2_paper_matrix.ps1
.\scripts\run_cf2_paper_matrix.ps1
```

If time is limited, prioritize X2 Hard45/full3/hardstep and CF2 Hard45.

## 4. Aggregate new runs

Each script prints its result directory. Aggregate it with:

```powershell
.\.venv\Scripts\python.exe .\scripts\summarize_run_tree.py <result-directory>
```

Rebuild the current validated figures with:

```powershell
.\.venv\Scripts\python.exe .\scripts\build_validation_report.py
```

## 5. Paper work

- Start from `paper\WORKING_DRAFT.md`.
- Use `paper\tables\hard45_results.tex`.
- Use figures from `results\reports`.
- Put stock CF2 saturation and the CF2 authority sweep together; this turns a
  weakness into an actuator-feasibility result.
- State that online PES adapts during the mission. Add frozen-weight hold-out
  experiments before making a generalization claim.

## 6. Decision gates

- If robustness improvement remains above 30%, keep the 50% nominal result in
  the abstract and robustness in the main table.
- If fixed/adaptive conductance remain identical, present it as a negative
  ablation and reduce the gate gain in a follow-up sensitivity run.
- If CF2-design needs more than 1.5× thrust in longer missions, report the exact
  threshold; do not silently increase it.
- Do not spend the morning on QCar hardware until the paper matrices are running.
- For QCar, keep the existing lane-following controller as the baseline. First
  run CMG/SNN perception and steering in shadow mode for lane keeping; log its error
  beside the current vision estimate before allowing it to affect steering.
