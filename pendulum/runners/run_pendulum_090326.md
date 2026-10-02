# Cube-Servo 3 Pendulum runners

Environment Update
```
cd C:\Research\pendulum
$PY = "C:\Users\gandhico\AppData\Local\miniconda3\envs\hyperlif\python.exe"
```

Sensor check:
```
& $PY .\runners\run_online_qube.py --mode sensor_check --hardware 1 --duration 5
```

LED color test:
```
& $PY .\runners\run_online_qube.py --led-test --hardware 1
```

Equilibrium - Simulink baseline
```
& $PY .\runners\run_simulink_balance.py --hardware 1 --armed --duration 20 --voltage-limit 4.0 --require-manual-swing --manual-swing-release-deg 15 --alpha-upright-offset-deg 180 --capture-angle-deg 10 --capture-hysteresis-deg 2 --engage-confirm-samples 3 --max-engage-alpha-dot 3.0 --theta-ref-mode current_on_engage --soft-start-s 0.05
```

Equilibrium - HyperLIF residual balance
```
& $PY .\runners\run_simulink_balance.py --hardware 1 --armed --duration 60 --voltage-limit 4.0 --require-manual-swing --manual-swing-release-deg 15 --alpha-upright-offset-deg 180 --capture-angle-deg 10 --capture-hysteresis-deg 2 --engage-confirm-samples 3 --max-engage-alpha-dot 3.0 --theta-ref-mode current_on_engage --soft-start-s 0.05 --residual-mode gate --residual-scale 1.0 --residual-sign 1.0 --residual-neuron adaptive_hyperlif --residual-max-voltage 0.20 --residual-log-prefix qube3_gate_cap020_60s
```

Then immmediately plot the result you just got
```
& $PY .\tools\plot_qube_run.py (Get-ChildItem .\results\online\qube3_gate_cap020_60s_simulink_balance_*.csv | Sort-Object LastWriteTime | Select-Object -Last 1).FullName
```

## Residual Gate Implementation

Baseline
```
& $PY .\runners\run_simulink_balance.py --hardware 1 --armed --duration 60 --voltage-limit 4.0 --require-manual-swing --manual-swing-release-deg 15 --alpha-upright-offset-deg 180 --capture-angle-deg 10 --capture-hysteresis-deg 2 --engage-confirm-samples 3 --max-engage-alpha-dot 3.0 --theta-ref-mode current_on_engage --soft-start-s 0.05 --residual-mode none --log-prefix qube3_baseline_60s
```

Gate +- 0.10 V | run 4 times
```
& $PY .\runners\run_simulink_balance.py --hardware 1 --armed --duration 60 --voltage-limit 4.0 --require-manual-swing --manual-swing-release-deg 15 --alpha-upright-offset-deg 180 --capture-angle-deg 10 --capture-hysteresis-deg 2 --engage-confirm-samples 3 --max-engage-alpha-dot 3.0 --theta-ref-mode current_on_engage --soft-start-s 0.05 --residual-mode gate --residual-scale 1.0 --residual-sign 1.0 --residual-neuron adaptive_hyperlif --residual-max-voltage 0.10 --residual-log-prefix qube3_gate_cap010_60s
```

Gate +- 0.20 V | run 4 times
```
& $PY .\runners\run_simulink_balance.py --hardware 1 --armed --duration 60 --voltage-limit 4.0 --require-manual-swing --manual-swing-release-deg 15 --alpha-upright-offset-deg 180 --capture-angle-deg 10 --capture-hysteresis-deg 2 --engage-confirm-samples 3 --max-engage-alpha-dot 3.0 --theta-ref-mode current_on_engage --soft-start-s 0.05 --residual-mode gate --residual-scale 1.0 --residual-sign 1.0 --residual-neuron adaptive_hyperlif --residual-max-voltage 0.20 --residual-log-prefix qube3_gate_cap020_60s
```

Always on +- 0.10 V | run 4 times
```
& $PY .\runners\run_simulink_balance.py --hardware 1 --armed --duration 60 --voltage-limit 4.0 --require-manual-swing --manual-swing-release-deg 15 --alpha-upright-offset-deg 180 --capture-angle-deg 10 --capture-hysteresis-deg 2 --engage-confirm-samples 3 --max-engage-alpha-dot 3.0 --theta-ref-mode current_on_engage --soft-start-s 0.05 --residual-mode always_on --residual-scale 1.0 --residual-sign 1.0 --residual-neuron adaptive_hyperlif --residual-max-voltage 0.10 --residual-log-prefix qube3_always_on_cap010_60s
```

Always on +- 0.30 V | run 4 times
```
& $PY .\runners\run_simulink_balance.py --hardware 1 --armed --duration 60 --voltage-limit 4.0 --require-manual-swing --manual-swing-release-deg 15 --alpha-upright-offset-deg 180 --capture-angle-deg 10 --capture-hysteresis-deg 2 --engage-confirm-samples 3 --max-engage-alpha-dot 3.0 --theta-ref-mode current_on_engage --soft-start-s 0.05 --residual-mode always_on --residual-scale 1.0 --residual-sign 1.0 --residual-neuron adaptive_hyperlif --residual-max-voltage 0.30 --residual-log-prefix qube3_always_on_cap010_60s
```