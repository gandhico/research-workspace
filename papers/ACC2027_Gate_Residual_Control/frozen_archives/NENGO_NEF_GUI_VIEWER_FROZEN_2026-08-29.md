# Frozen Nengo/NEF GUI with live MuJoCo viewer

- Archive: `C:\Research\papers\ACC2027_Gate_Residual_Control\frozen_archives\nengo_nef_gui_viewer_CANONICAL_FROZEN_2026-08-29.zip`
- Size: 150,425,643 bytes
- SHA-256: `B77CCA35D3C0CB714742CFC20FEEF8A3FA2925CCE8D258471655FAE699D5F45B`
- Source: `C:\Research\papers\ACC2027_Gate_Residual_Control\experiments\nengo_nef_replication_2026-08-29`

This checkpoint preserves the user's current 8,742-byte preliminary dashboard
layout and adds an opt-in native MuJoCo viewer and wall-clock governor. It does
not overwrite the earlier batch-only or GUI-only canonical archives.

## Viewer behavior

- `--mujoco-viewer neural` visualizes the CMG--PES twin.
- `--mujoco-viewer baseline` visualizes the quaternion-PD twin.
- Both synchronized plants continue at the canonical `dt=0.0005 s`.
- `--realtime` paces Nengo simulation time to wall time.
- `--viewer-fps` independently limits rendering to 1--120 Hz (default 30).
- Headless, unpaced execution remains the default.

## SHA-256

- `gui_cmg_pes_mujoco.py`: `FD676B0D477B3958D44D61944A8ECBAF85E97AF28515D5F623D7A9E84B9F32C7`
- `gui_cmg_pes_mujoco.py.cfg`: `9AC463BCAFF53D8A24312670648FB9016ED1A12019438642E306BABC35FCA763`
- `launch_gui.py`: `CC25B575370AEE70504EE81552C7B1A64DAFCAE7B5943B9655187320866C6D29`
- `smoke_test_gui.py`: `04ACAC0161203A31D8B6AD2DD8092574980451A027479398EC0E781936202890`
- `GUI_GUIDE_2026-08-29.md`: `4D29482482BFB1A9B17845532D393234A170964C77CE0FF3E1A64DD62853DE02`

## Verification

- Python compilation passed.
- The unchanged headless regression passed for X2/hard45 and CF2/yaw360.
- The native Windows viewer opened, synchronized the X2/hover neural plant for
  400 steps, maintained approximately real-time pacing, and closed cleanly.
- The tested 0.2 s simulation interval required approximately 0.218 s wall time.
- No physical hardware interface was accessed.
