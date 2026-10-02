# Julia connection for the Quanser 3-DOF Hover

`Hover3DOFHIL.jl` adds the Hover to the direct Julia `ccall -> hil.dll`
transport already used for the Qube and Aero 2. It preserves the physically
verified channel order and the vendor nonnegative-voltage rule:

- AO0/1/2/3 = front/back/left/right;
- ENC0/1/2 = pitch/roll/yaw;
- motor voltage = DAC voltage times amplifier gain 3;
- every final motor command is clamped to `[0, 24] V` before conversion;
- `write_motor_voltages!(...; armed=false)` always writes zero.

Safe V0/V1 check (does not open a device):

```powershell
julia --startup-file=no .\julia\hover_bridge_smoke.jl
```

The module deliberately does not provide an automatically armed controller.
The first live step remains sensor-only, followed by shadow computation,
baseline-only control, and only then bounded residual control under the
existing `docs/SAFETY_CHECKLIST.md`.
