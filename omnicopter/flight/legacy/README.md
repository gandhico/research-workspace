# Legacy scripts (kept for reference, not used any more)

The first link and motor scripts, moved here on 2026-11-05 from the lab PC folder
`Desktop\Omnidrone` so that the whole project lives in one place. They still run, but the
tools in `flight/` replace them.

| Folder | Date | What it did | Replaced by |
|---|---|---|---|
| `xbee_serial/` | 2026-09-11 | Serial tests on COM5 at 57600 baud over an XBee radio: open the port (`serialcomm.py`), send text (`TXD_test.py`), listen for bytes (`bytesplease.py`), wait for a MAVLink heartbeat (`MAVLinkConnectionTest.py`). This link was abandoned (the original folder was called `Communication_Failed`). | The Pico W Wi-Fi bridge |
| `pico_link/` | 2026-09-15 | First tests of the Pico W Wi-Fi ↔ Cube UART bridge on UDP 14550: UART loopback (`pico_loopback_test.py`), heartbeat (`communication_test_1.py`), full diagnostic (`communication_test_2.py`). | `flight/ap_link.py` (used by every tool) |
| `motor_tests/` | 2026-11-04/05 | Motor tests with `MAV_CMD_DO_MOTOR_TEST`: all 8 motors in percent mode (`motor_test_1.py`, guarded: refuses on the reversible 6DoF set-up), the DShot-3D variant (`motor_test_1_DSHOT.py`) and an interactive version with emergency stop (`motor_test_2.py`). | `flight/motor_test_6dof.py` |

`motor_test_1.zip` (an identical copy of `motor_test_1.py`) was not kept. The Motive rigid-body
file `Aries_Omnidrone.motive` moved to `flight/mocap/`.
