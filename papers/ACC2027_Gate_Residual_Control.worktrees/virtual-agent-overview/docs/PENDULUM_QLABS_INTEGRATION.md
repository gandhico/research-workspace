# Pendulum QLabs integration and closure

The authoritative detailed record is
`C:\Research\pendulum\docs\ACC2027_PENDULUM_CLOSURE_2026-08-27.md`.
This file records the ACC-repository boundary.

## Backend boundary

- `models\pendulum_surrogate.xml` is a deliberately low-fidelity MuJoCo
  integration surrogate. It tests the common API and logging only.
- `C:\Research\pendulum\runners\twin_acc2027_gate_residual.py` is the QLabs
  virtual-twin runner. It connects through Quanser PAL using
  `QubeServo3(..., hardware=0, pendulum=1)` on port 18923.
- Both paths import the canonical CMG controller implementation from
  `src\gra_control\gate.py`; the QLabs summary records its SHA-256.
- Neither path is physical QUBE hardware. The QLabs runner cannot select
  `hardware=1`.

## Canonical QLabs result, 2026-08-27

Five controllers were tested in three trials each at 500 Hz. Each trial used the
same 5 V LQR, a maximum 0.35 V additive residual, and exactly 20 s of accumulated
upright balance. Every condition remained balanced in the final 5 s with no
amplifier faults or stalls.

| Controller | final-5-s alpha RMS, mean +/- std (deg) | vs LQR |
|---|---:|---:|
| LQR | 1.0581 +/- 0.0012 | reference |
| fixed residual | 1.0590 +/- 0.0020 | -0.08% |
| adaptive-conductance residual | 1.1170 +/- 0.1003 | -5.57% |
| online-PES fixed conductance | 1.0566 +/- 0.0011 | +0.15% |
| online-PES adaptive conductance | 1.0570 +/- 0.0015 | +0.10% |

Interpretation: nominal equilibrium accuracy is practically equivalent to LQR.
The architecture transfers safely and online weights update, but the QLabs
nominal hold does not support a performance-improvement claim. An earlier
fixed-wall-time dataset appeared to show approximately 14% improvement; matching
actual balance exposure revealed it as a QLabs limit-cycle/protocol confound.

Artifacts are copied to:

- `results\reports\pendulum_qlabs_matched20.md`
- `results\reports\pendulum_qlabs_matched20.csv`
- `results\reports\pendulum_qlabs_matched20.png`
- `results\reports\pendulum_qlabs_matched20.pdf`

## Reproduce

```powershell
cd C:\Research\pendulum
.\scripts\run_acc2027_twin_matrix.ps1 `
  -BalanceDuration 20 -MaxDuration 90 -Trials 3 `
  -ResidualCapV 0.35 -Label paper_matched20
```

Do not spend additional ACC time tuning nominal pendulum RMS. If reopened, the
next scientifically discriminating experiment is a reset-controlled,
arm-recentered, repeated disturbance benchmark.
