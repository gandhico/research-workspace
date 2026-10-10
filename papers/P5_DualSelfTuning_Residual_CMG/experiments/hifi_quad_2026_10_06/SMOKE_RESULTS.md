# First opt-in L1 rotor-response smoke — 2026-10-06

Command (using the established ACC MuJoCo 3.12.0 environment):

`C:\Research\papers\ACC2027_Gate_Residual_Control\.venv\Scripts\python.exe experiments\hifi_quad_2026_10_06\smoke_rotor_response.py`

Result at `dt=0.0005 s`:

| Scene | Zero-lag L0 parity | Synthetic 30 ms motor-speed lag, 100 ms hover altitude difference |
|---|---|---:|
| X2 | `ctrl`, `qpos`, `qvel` bit-exact for 200 MuJoCo steps | 0.029245 m |
| CF2 stock design | `ctrl`, `qpos`, `qvel` bit-exact for 200 MuJoCo steps | 0.029127 m |

The analytic half-speed check also passed: after `tau*ln(2)` from rest under a full-force command, quadratic thrust is one quarter of maximum.

These results verify code path and model sensitivity only. **30 ms is synthetic**, not an identified X2 or CF2 motor time constant. No motor/battery parameters have been fitted, and no controller campaign or hardware validation is reported by this smoke.
