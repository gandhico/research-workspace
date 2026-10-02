# Qube-Servo 3 — Original Quanser Simulink Swing-Up Controller

Pulled forward 2026-09-03 from
`C:\Users\gandhico\Documents\Quanser\6_teaching\1_Controls\Qube_Servo_3\sp6_pendulum_control\2_swingup_control\`
(already-installed Quanser Academic Resources on this machine — not the backup
drive). This is Quanser's own validated energy-based swing-up model, the same
one `src\servo_pendulum_snn\simulink_balance_runner.py`'s `--auto-swing-up`
Python reimplementation is derived from (see that file's own comments for the
extracted formula/constants).

## Layout

```
matlab\
├── digital_twin\
│   ├── qs3_swingup.slx              <- COMPLETE model, run this first (no hardware risk)
│   ├── qs3_swingup_student.slx      <- fill-in-the-blank teaching version
│   ├── setup_swingup.m              <- computes Er, tau_max, a_max, K into the base workspace
│   ├── qube3_rotpen_param.m         <- QUBE-Servo 3 physical constants (mp, Lp, mr, r, Rm, kt, ...)
│   └── lab_procedure_swingup_ctrl.pdf  <- Quanser's own lab writeup for this model
└── hardware\
    └── qs3_swingup_student.slx      <- physical-hardware version — STUDENT ONLY, see caveat below
       (setup_swingup.m / qube3_rotpen_param.m duplicated here too, same content)
```

## How to run

1. Open MATLAB (R2025a, QUARC installed — confirmed on this machine per
   `C:\Research\SETUP.md`). No extra library files are needed: the model's
   "Rotary Pendulum Interface" hardware-I/O subsystem uses QUARC's own
   `HIL Initialize/Read/Write` blocks, which ship with the QUARC toolbox
   install itself (not a separate Quanser file to copy).
2. `cd` to `digital_twin\` (or `hardware\`) inside MATLAB, or add it to path.
3. Run the setup script first — the model reads workspace variables it does
   NOT define itself:
   ```matlab
   setup_swingup
   ```
   This runs `qube3_rotpen_param` internally and computes `Jp_cm`, `Er`,
   `tau_max`, `a_max`, and the balance gain `K = [-1.000 26.72 -0.8269 2.214]`
   into the base workspace.
4. Open the `.slx` file and press **Run** (or **Monitor & Tune** / external
   mode for the hardware version, via QUARC).
5. The model has a live **`ke (m/s/J)` slider** (default 50, range 0–100) you
   can drag while it's running to tune pump strength without stopping —
   `ke=50` is Quanser's own validated default, confirmed by extracting the
   `.slx` block diagram directly (it's a zip archive under the hood).
6. Built-in scopes: `Pendulum Energy (mJ)`, `Rotary Arm/Base (deg)`,
   `Inverted Pendulum (deg)`, `Vm (V)`.

## Recommended order for tomorrow

Start with **`digital_twin\qs3_swingup.slx`** (complete, QLabs twin, zero
hardware risk) to confirm the reference behavior and tune `ke` live if
needed. Only move to `hardware\qs3_swingup_student.slx` once that looks right.

## Caveat, checked 2026-09-03

`hardware\qs3_swingup_student.slx` is the only hardware-tier file Quanser
shipped in this module (no separate instructor version exists for hardware).
Checked its block structure directly (`.slx` is a zip archive — extracted and
diffed against the complete `digital_twin\qs3_swingup.slx`): **the swing-up
logic itself is present and structurally identical** — same subsystems
(`Swing-Up Control`, `Energy-Based Swing-Up Control`,
`(E-Er)*sign(a_dot*cos(a))`, `Pend Inertia`, `Pend Torque`, the `ke`/`Er`/
`u_max` ports), same 10 internal systems. It does not appear to be blanked
out as a fill-in exercise — should be runnable as-is. Still open it and read
through the diagram once in MATLAB before arming real hardware, same as any
new controller.
