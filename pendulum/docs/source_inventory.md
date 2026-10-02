# Qube Servo/Pendulum Source Inventory

Useful Quanser sources reviewed and copied into this experiment tree:

- `vendor\quanser_examples\qube_servo_python\read_write_qube3.py`
- `vendor\quanser_examples\qube_servo_python\pd_control_qube_task.py`
- `vendor\quanser_examples\qube_servo_python\balance_control_qube.py`
- `vendor\quanser_examples\qube_servo3_quick_start_software`
- `vendor\quanser_examples\qube_servo3_balance_digital_twin_matlab`
- `vendor\quanser_examples\qube_servo3_lqr_digital_twin_matlab`
- `vendor\quanser_examples\qube_servo3_state_space_digital_twin_matlab`
- `vendor\quanser_reference\pal_products\qube.py`

The copied examples are for traceability and first-stack validation. The project
runner in `src\servo_pendulum_snn` reuses the same PAL API and Qube 3 balance
gain while adding command-line configuration, CSV logging, `--armed`, fault
zeroing, conservative voltage limits, and the HyperLIF gate-state residual.
