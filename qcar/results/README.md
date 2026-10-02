# QCar/QCar2 Results

Expected output layout:

```text
results/
  offline/
    qcar_<timestamp>/
      csv/
        qcar_baseline.csv
        qcar_hyperlif_residual.csv
      figures/
        qcar_baseline_vs_hyperlif_residual.png
      summary.json
```

Hardware logs from `01_Code/hardware/qcar2_unified_lane_control_hardware_v1.py`
are currently stored in `01_Code/hardware/logs/`. For paper figures, copy only
selected final logs or summary tables into a curated results subfolder with a
short manifest.

