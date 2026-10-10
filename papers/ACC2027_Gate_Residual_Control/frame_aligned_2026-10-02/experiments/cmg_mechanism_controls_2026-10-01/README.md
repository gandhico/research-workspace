# CMG mechanism controls (2026-10-01)

What does the coupled membrane–gate (CMG) neuron contribute to the CMG–PES residual? Preregistered controls on
the frozen ρ = 3 PD + desired-rate feedforward runner (X2 and CF2-rotor, five 45 s missions, seed 1, noise-free).
Only the paired-current → activity map changes between arms. Frozen experiment folders are not modified.

**Result:** LPF + static logistic (CMG without gate state, γ feedback or conductance) gives 46.34% / 28.61% vs
CMG's 37.30% / 22.42%. CMG gates latch irreversibly (release fold below v_reset), which collapses features to
a = 1; χ has no effect; lowering G removes the useful graded tail. Read `MECHANISM_AND_TRANSFER.md` first.

Report page (private): https://claude.ai/artifact/3ZzbKfmNLLjn7MQKA2dcgC

## Reproduce

```powershell
$py = 'C:\Research\papers\ACC2027_Gate_Residual_Control\.venv\Scripts\python.exe'
$x  = 'C:\Research\papers\ACC2027_Gate_Residual_Control\experiments\cmg_mechanism_controls_2026-10-01'
& $py "$x\phase0_latch_diagnostics.py"                  # archived-trace diagnostics + latch schedule
& $py "$x\check_gates.py"                               # needs results\gates (see below)
& $py "$x\run_campaign.py" --mode development --workers 4
& $py "$x\run_campaign.py" --mode confirm --workers 4    # 70 cases, cached by summary.json
& $py "$x\analyze.py"
& $py "$x\make_report_figures.py"; & $py "$x\make_report_html.py"
```

Gate runs (X2 Hard45, 45 s): `run_cmg_controls.py --controller cmg-numpy` → `results\gates\g1_cmg_numpy`,
`--controller cmg` → `g2_cmg_nengo_wrapper`, and `..\neuron_basis_decisive_2026-09-24\run_neuron_basis.py
--controller constant-one` → `g3_constant_one_rerun`, each with the strict platform arguments.

Raw run outputs (`results\`, ~5 GB of full-rate neural archives) are backed up on
`D:\NMSU_backups\laptop_2026-10-01\research_full\papers\ACC2027_Gate_Residual_Control\experiments\cmg_mechanism_controls_2026-10-01\`.
