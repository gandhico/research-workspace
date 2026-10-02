# EHEKATL mission comparison: thesis grouped ACS versus distributed elevons

## Question

Does independent allocation across the eight trailing-edge elevons improve a
representative EHEKATL mission relative to the primary-control abstraction used
in the thesis?

## Compared architectures

The **thesis grouped ACS** retains three logical commands. Two inner elevon
pairs move together as elevators, two outer pairs move antisymmetrically as
ailerons, and both rudders share one directional command. This matches the
thesis controller abstraction even though the physical model contains eight
trailing-edge surfaces.

The **distributed-elevon extension** uses the identical attitude controller and
virtual roll, pitch and yaw acceleration request, but solves a constrained QP
at 35 Hz for ten independent commands: eight elevons and two rudders. Surface
position, slew and a detected actuator jam are enforced inside the allocation.

## Mission and common conditions

Both architectures fly the same 70-second attitude programme: trim, climb,
right survey turn, level survey leg, reversing turn, descent and flare. Both
receive the same sampled effectiveness matrix, sensor/process noise, angular
damping, gust moments at 23 s and 46 s, command limits and rate limits. The left
outer elevon is jammed at zero at 32 s. The grouped ACS remains fault-unaware;
the extension receives the detected failure and redistributes the virtual
command among the remaining surfaces.

![Mission attitude comparison](results/mission_comparison/mission_attitude_comparison.png)

![Allocation comparison](results/mission_comparison/mission_allocation_comparison.png)

![Surface redistribution](results/mission_comparison/mission_surface_redistribution.png)

The heat map makes the architectural distinction explicit. The grouped ACS
continues to issue the common aileron command to the failed left-outboard
surface because it has no failure model. The distributed QP pins that surface
to zero and redistributes the virtual-control request among the remaining
elevons and rudders subject to their rate and position constraints.

## Paired uncertainty campaign

Twenty paired trials used identical uncertainty and noise seeds within each
architecture pair. Positive values below favour independent allocation.

| Metric | Mean reduction | Approximate 95% interval |
|---|---:|---:|
| Overall attitude RMSE | 2.32% | 2.18% to 2.46% |
| Peak attitude error | 1.01% | 0.94% to 1.08% |
| Post-fault attitude RMSE | 3.40% | 3.22% to 3.58% |
| Virtual-control allocation RMSE | 70.74% | 66.59% to 74.89% |
| Surface RMS command | 9.07% | 8.51% to 9.62% |
| Command total variation | 11.65% | 11.32% to 11.98% |

![Paired mission improvements](results/mission_comparison/mission_monte_carlo_improvement.png)

The important result is not a large nominal tracking gain. With all actuators
healthy, both architectures have enough authority and should track similarly.
The extension materially reduces the mismatch between requested and realised
moments after the jam while using slightly less command magnitude and motion.
The closed-loop attitude improvement is modest because the outer-loop
controller is deliberately conservative and the failure removes only one of
ten effectors.

## Evidence boundary

This is a reproducible numerical architecture comparison, not an identified
EHEKATL result. The effectiveness matrix is a documented research prior. The
study does not yet include hinge moments, servo dynamics, nonlinear aerodynamic
tables, structural flexibility, airspeed dependence, ground effect or verified
X-Plane per-surface actuation. It demonstrates why the extension is worth
identifying and testing; it does not predict the physical aircraft's numerical
performance.

The next validation step is to identify the ten-column effectiveness matrix and
its covariance from the exact X-Plane `.acf`, followed by read-only surface
index/sign checks, low-authority one-surface tests and repeated mission pairs.

## Reproduction

```powershell
Set-Location 'C:\Research\ehekatl_BWB\project'
& 'C:\Research\ehekatl_BWB\.venv-control\Scripts\python.exe' -m unittest elevon_allocation.test_allocator elevon_allocation.test_mission_comparison -v
& 'C:\Research\ehekatl_BWB\.venv-control\Scripts\python.exe' -m elevon_allocation.mission_comparison
& 'C:\Research\ehekatl_BWB\.venv-control\Scripts\python.exe' -m elevon_allocation.mission_campaign --trials 20
```

Raw time histories and paired trial results are in
`results/mission_comparison/mission_timeseries.csv` and
`results/mission_comparison/mission_monte_carlo.csv`.
The representative-run values are also exported as the ready-to-quote Markdown
table `results/mission_comparison/mission_metrics_table.md`.
