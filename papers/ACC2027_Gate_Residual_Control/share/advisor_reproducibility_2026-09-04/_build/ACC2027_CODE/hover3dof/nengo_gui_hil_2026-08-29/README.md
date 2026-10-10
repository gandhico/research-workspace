# Nengo GUI/HIL for the Quanser 3DOF Hover

This isolated package implements the MuJoCo-matched quaternion-PD baseline and
the six-unit coupled membrane--gate (CMG) residual with Nengo built-in PES.
The hardware/control worker runs at 200 Hz, the inner neural controller runs ten
steps at 0.5 ms (2 kHz), and the dashboard samples immutable state at 50 Hz.

## Frozen neuron-family benchmark (2026-09-01)

The Hover testbench now supports an **emulation-only** matched comparison of
CMG, LIF, ALIF, Izhikevich, and LIFRate neurons in fixed and online-PES modes.
The full nominal/hard-pulse matrix contains 110 cells and 100 lossless 2-kHz
neural archives. The connected Q8 family check is hard-coded unarmed and was
audited to have exactly zero output on every DAC channel. Only `pd` and the
previously qualified `nengo-pes` controller may be armed.

Read the frozen equations, results, limitations, paths, and commands in
`docs\NENGO_NEURON_FAMILY_CAMPAIGN_2026-09-01.md`.

Use `docs\COMMAND_CATALOG_2026-09-01.md` and
`launch_hover_experiment.ps1` to reproduce any mission in live GUI, accelerated
headless, zero-output Q8 shadow, or qualified physical-hardware mode.

```powershell
$py = 'C:\Research\hover3dof\.venv\Scripts\python.exe'
$root = 'C:\Research\hover3dof\nengo_gui_hil_2026-08-29'
& $py "$root\launch_hover_nengo_gui.py" `
  --io emulated --controller nengo-pes --mission hard45 --duration 25
```

Every PD run saves a complete 200 Hz `trace.csv`. Every Nengo-PES run also
saves a lossless `neural_trace_2khz.npz` plus JSON schema, including the six
currents, `v`, `r`, activity, state-equation terms, raw/clipped decoder, target,
PES error, all 18 weights and updates, and residual torque.

Read `LAB_RUNBOOK.md` and
`C:\Research\papers\ACC2027_Gate_Residual_Control\docs\NENGO_FULL_TELEMETRY_2026-08-31.md`.
The offline direct/Nengo audit passed with maximum residual difference
`1.687e-8`. The Q8 zero-output qualification, five-mission connected shadow
campaign, armed PD hover qualification, and first matched armed Roll validation
are complete. The preliminary `n=1` Roll result improved mean attitude error by
1.394% at beta=0.10/cap=0.10 V and 2.162% at beta=0.20/cap=0.20 V. See
`C:\Research\hover3dof\docs\NENGO_ARMED_HARDWARE_VALIDATION_2026-08-31.md`.

For local browser automation or environments where Nengo's one-time token is
not visible, the launcher accepts `--gui-password <local-password>`. This only
changes GUI authentication; it does not change the controller or hardware I/O.
