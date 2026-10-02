# Frozen Nengo/NEF interactive GUI

- Canonical GUI-inclusive archive: `C:\Research\papers\ACC2027_Gate_Residual_Control\frozen_archives\nengo_nef_gui_CANONICAL_FROZEN_2026-08-29.zip`
- Size: 140,362,528 bytes
- SHA-256: `5E039E226FA104DD72A33F943DD12EB61FEE211537811A129B55B35EA1A9E6B8`
- Captured source: `C:\Research\papers\ACC2027_Gate_Residual_Control\experiments\nengo_nef_replication_2026-08-29`

This snapshot extends, but does not overwrite, the earlier frozen canonical
batch replication. It contains all 24 completed matched 45 s runs, compiled
tables and plots, plus the interactive Nengo GUI, layout, custom 0.5 ms backend,
portable launcher, operator guide and repeatable headless GUI smoke test.

## GUI code SHA-256

- `gui_cmg_pes_mujoco.py`: `C2BC93C4F255BFAF9863E2788FB63D89F9FF9ACCD3AE3290471075C6F0660576`
- `gui_cmg_pes_mujoco.py.cfg`: `CA7ECF6619171CDD2E5185B7490C87D9ADC319E1ADB5BF846670BB6EC45D5F75`
- `launch_gui.py`: `E35E28E684FB53B451295B1529C4764939BEC27938061B98CB4788FEDC7EC164`
- `nengo_dt0005_backend.py`: `EC84BA22D766E463723EAE01E588702DCF806DA4596EBEEB2C584787B06149ED`
- `smoke_test_gui.py`: `16C7DBABA9F474CD2872B3912498CF5B3615DAE1C54469C8D54A5D1572F1959D`
- `GUI_GUIDE_2026-08-29.md`: `638E8D34A0251447088A70C13FC62EEE1D4189B7F2533B6CEDC7BD904DDD9D7F`
- `results/gui_smoke_test.json`: `6A91D03C91D5D88EDE80B9CBF94781546E95BCC212AF9DBABE4AE26A6C24F01C`

## Verification

- Python compilation passed for all four GUI/runtime files.
- The headless GUI check passed for X2/hard45 and CF2/yaw360 at `dt=0.0005 s`.
- Each case ran 400 steps, all inspected signals were finite, and the expected
  two-error, six-neuron, and 3-by-6 decoder schemas were present.
- The local GUI server was reachable during validation.
- No physical hardware interface was imported or accessed.

The GUI is an exploratory/diagnostic representation. The original matched
batch runner and frozen 45 s campaign remain the source for paper metrics.
