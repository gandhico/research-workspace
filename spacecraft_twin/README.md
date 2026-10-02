# Basilisk - MuJoCo spacecraft digital twin

This project contains a functional single-satellite attitude-control example
using Basilisk 2.11.1's native MuJoCo dynamics. It is not a side-by-side
co-simulation: `MJScene` is the Basilisk dynamic object, and standard Basilisk
flight-software modules command three MuJoCo reaction-wheel actuators.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe .\single_satellite_mujoco.py
```

Each run writes `summary.json`, `trace.csv`, and
`attitude_convergence.png` under `results/`. The script fails if values are
non-finite or if the terminal attitude/rate convergence gate is not met.
The verified default horizon is 600 s. A 180 s run is stable, but does not yet
meet the deliberately strict terminal gate used by this example.

## Mathematical flow

Let `sigma_BR` be the modified Rodrigues parameters (MRPs) from reference frame
`R` to body `B`, and `omega_BR_B` the rate error. With integral action disabled
in this first baseline, Basilisk's feedback law is structurally

```text
L_r = -K sigma_BR - P omega_BR_B + feedforward/cross-coupling terms
```

The wheel allocation solves the body-torque relation

```text
L_r = -G_s u_s
```

for wheel torques `u_s`, with `G_s = I_3` here, and each wheel command is
clamped to `[-0.2, 0.2] N m` before it reaches the MuJoCo hinge actuator.
The combined bus-wheel angular momentum changes only through external torque;
internal wheel torque produces the equal-and-opposite bus reaction used for
attitude control.

## Multi-agent extension

Yes, multi-agent orbital systems are possible. Keep each satellite as its own
`MJScene` or as a disconnected free-body subtree in a shared scene, publish a
navigation message per agent, and run a local guidance/control stack per agent.
Add an explicit communication graph with sample time, delay, packet loss, and
neighbor selection. Start with Hill/Clohessy-Wiltshire relative dynamics for
formation-control design, then validate in Basilisk's nonlinear gravity model.
Avoid calling a multi-spacecraft simulation "multi-agent" unless the agents
have separate state, control, and communication contracts.
