# Runner Commands — Quick Reference

All commands are run from the `v2_clean/` directory.

---

## 1. Classical Baseline — Rotor-Level (Skydio X2)

```powershell
python runners\run_rotor_level.py `
  --quad skydio_x2 `
  --controller classical `
  --mission hover `
  --sim-time 20 `
  --viewer --dashboard --save-csv --save-figures
```

Hard45 tracking test:
```powershell
python runners\run_rotor_level.py `
  --quad skydio_x2 `
  --controller classical `
  --mission hard45 `
  --sim-time 45 `
  --viewer --dashboard --save-csv --save-figures
```

---

## 2. Classical Baseline — CF2 Body-Torque (Legacy Path)

```powershell
python runners\run_rotor_level.py `
  --quad bitcraze_crazyflie_2 `
  --controller classical `
  --mission hard45 `
  --sim-time 45 `
  --viewer --dashboard --save-csv
```

---

## 3. Direct LIF Residual

```powershell
python runners\run_rotor_level.py `
  --quad skydio_x2 `
  --controller direct_lif `
  --mission hard45 `
  --sim-time 45 `
  --blend 0.20 `
  --direct-scale control `
  --activity-mode voltage `
  --viewer --dashboard --save-csv
```

---

## 4. Direct HyperLIF Gate-State Residual (Best Result)

```powershell
python runners\run_rotor_level.py `
  --quad bitcraze_crazyflie_2 `
  --controller direct_hyperlif `
  --mission hard45 `
  --sim-time 45 `
  --blend 0.50 `
  --direct-scale control `
  --activity-mode gate `
  --gate-gain 100000 `
  --viewer --dashboard --save-csv --save-figures
```

---

## 5. Adaptive HyperLIF Gate-State Residual

```powershell
python runners\run_rotor_level.py `
  --quad bitcraze_crazyflie_2 `
  --controller direct_adaptive_hyperlif `
  --mission hard45 `
  --sim-time 45 `
  --blend 0.50 `
  --direct-scale control `
  --activity-mode gate `
  --gate-gain 100000 `
  --viewer --dashboard --save-csv --save-figures
```

---

## 6. Rotor-Level HyperLIF Residual (Skydio X2 Only)

```powershell
python runners\run_rotor_level.py `
  --quad skydio_x2 `
  --controller rotor_residual_hyperlif `
  --mission hard45 `
  --sim-time 45 `
  --residual-blend 0.10 `
  --gate-gain 50000 `
  --viewer --dashboard --save-csv --save-figures
```

---

## 7. Rotor-Level Adaptive HyperLIF Residual

```powershell
python runners\run_rotor_level.py `
  --quad skydio_x2 `
  --controller rotor_residual_adaptive_hyperlif `
  --mission hard45 `
  --sim-time 45 `
  --residual-blend 0.10 `
  --gate-gain 100000 `
  --viewer --dashboard --save-csv --save-figures
```

---

## 8. Nengo LIFRate Baseline

```powershell
python runners\run_rotor_level.py `
  --quad skydio_x2 `
  --controller nengo_lifrate `
  --mission hard45 `
  --sim-time 20 `
  --n-neurons 400 `
  --viewer --dashboard --save-csv
```

---

## 9. Benchmark Sweep (Multiple Controllers)

Smoke test (fast):
```powershell
python runners\run_benchmark_sweep.py `
  --preset smoke `
  --quad skydio_x2 `
  --missions roll,hard45 `
  --sim-time 20
```

Full gate-mode sweep:
```powershell
python runners\run_benchmark_sweep.py `
  --preset full `
  --quad bitcraze_crazyflie_2 `
  --missions hard45 `
  --sim-time 45 `
  --activity-mode gate `
  --direct-scale control `
  --gate-gain 100000 `
  --blend 0.50
```

Rotor-level comparison:
```powershell
python runners\run_benchmark_sweep.py `
  --preset rotor `
  --quad skydio_x2 `
  --missions hover,roll,hard45 `
  --sim-time 30
```

Cross-quad comparison (run twice with different --quad):
```powershell
python runners\run_benchmark_sweep.py --preset quick --quad skydio_x2 --missions hard45 --sim-time 45
python runners\run_benchmark_sweep.py --preset quick --quad bitcraze_crazyflie_2 --missions hard45 --sim-time 45
```

---

## Important CLI Flags

| Flag                    | Default   | Description                                   |
|-------------------------|-----------|-----------------------------------------------|
| --viewer                | off       | Open MuJoCo 3D viewer window                  |
| --dashboard             | off       | Open live matplotlib dashboard                |
| --realtime              | off       | Slow sim to real-time during viewer            |
| --save-csv              | off       | Save CSV + JSON summary + config               |
| --save-figures          | off       | Save PNG plots                                 |
| --save-npz              | off       | Save NumPy .npz array file                     |
| --no-save               | off       | Suppress all file output                       |
| --blend                 | 0.20      | Body-torque neural blend (direct_ controllers) |
| --activity-mode         | voltage   | voltage / gate / events                        |
| --direct-scale          | paper     | paper / control (time-constant rescaling)      |
| --gate-gain             | 1.0       | Gate activity multiplier                       |
| --residual-blend        | 0.10      | Rotor-residual blend                           |
| --z-ref                 | 1.0       | Altitude reference [m]                         |
| --sim-time              | 20.0      | Simulation duration [s]                        |
| --dt                    | 0.0005    | Simulation timestep [s]                        |
