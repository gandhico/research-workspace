# QDrone/QDrone2 Results

Expected output layout:

```text
results/
  offline/
    qdrone_<timestamp>/
      csv/
        qdrone_baseline.csv
        qdrone_hyperlif_residual.csv
      figures/
        qdrone_baseline_vs_hyperlif_residual.png
      summary.json
```

Hardware logs should include telemetry time, pose/attitude estimates, rates,
baseline commands, residual commands, final motor/attitude commands, gate values,
arm state, battery state, and failsafe state.

