# EHEKATL distributed elevon control allocation

This package is the reproducible numerical starting point for the proposed
backstepping plus control-allocation paper. It allocates commanded roll, pitch
and yaw angular acceleration to eight elevons and two rudders subject to
surface position, rate and detected-failure constraints.

## Current evidence

The numerical campaign used five manoeuvres, four actuator scenarios, three
allocation methods and 30 Monte Carlo draws per cell, for 1,800 closed-loop
runs at 35 Hz. The effectiveness matrix is an explicit research prior; it is
not yet an identified EHEKATL or wind-tunnel matrix.

The constrained QP was the best current method under the fault-informed model.
Compared with the fault-unaware fixed mixer, it reduced mean virtual-control
allocation RMSE by approximately 72% for a jammed left outer elevon, 66% for a
failed left rudder and 61% for a 45% loss in both outboard elevons. Mean
attitude RMSE decreased by about 5.3%, 4.5% and 4.2%, respectively. Under the
nominal model, the fixed mixer and constrained QP were effectively equivalent.

The covariance-aware penalty was implemented and stayed feasible, but the
current weight over-regularised the command distribution. It improved on the
fault-unaware mixer in the fault cases but did not outperform the nominal
constrained QP. This is a useful negative result: covariance weighting must be
identified and tuned from surface-effectiveness data, not chosen to force a
positive comparison.

## Reproduce the numerical campaign

```powershell
Set-Location 'C:\Research\ehekatl_BWB\project'
& 'C:\Research\ehekatl_BWB\.venv-control\Scripts\python.exe' -m unittest elevon_allocation.test_allocator -v
& 'C:\Research\ehekatl_BWB\.venv-control\Scripts\python.exe' -m elevon_allocation.simulate_maneuvers --trials 30 --output 'elevon_allocation\results'
```

Outputs are in `results/`: trial-level and summary CSV/JSON files plus PDF and
PNG figures.

## Thesis ACS versus distributed-elevon mission

`mission_comparison.py` applies the same 70-second climb, survey-turn,
reversal, descent and flare reference to two architectures. The baseline uses
the thesis convention: two inner elevon pairs are grouped as elevators, two
outer pairs are grouped as ailerons and the rudders share one directional
command. The extension independently allocates the same requested roll, pitch
and yaw acceleration across all eight elevons and both rudders. Both use the
same attitude controller, uncertain plant draw, gusts, limits and noise. A left
outer elevon is jammed at zero at 32 seconds; only the allocation extension is
given the detected failure and may redistribute demand.

```powershell
Set-Location 'C:\Research\ehekatl_BWB\project'
& 'C:\Research\ehekatl_BWB\.venv-control\Scripts\python.exe' -m elevon_allocation.mission_comparison
& 'C:\Research\ehekatl_BWB\.venv-control\Scripts\python.exe' -m elevon_allocation.mission_campaign --trials 20
```

The comparison is a numerical architecture study using the declared research-
prior effectiveness matrix. It must not be described as identified EHEKATL,
X-Plane, wind-tunnel or flight-test evidence.

The generated mission package includes attitude, allocation-demand and
per-surface redistribution figures in PNG/PDF, a representative metrics table,
raw time histories and the 20-pair Monte Carlo summary.

## Read-only X-Plane shadow test

The supplied project has no `.acf` file and no verified writable datarefs for
the eight individual elevons. Independent surface engagement is therefore
blocked. The shadow runner reads attitude and body rates, computes the virtual
command and proposed individual surface commands, and writes a CSV. Its source
contains no `sendCTRL` or `sendDREF` call.

With X-Plane 12 and XPlaneConnect running:

```powershell
Set-Location 'C:\Research\ehekatl_BWB\project'
& 'C:\Research\ehekatl_BWB\.venv-control\Scripts\python.exe' -m elevon_allocation.xplane_shadow_allocator --duration 20 --hz 20 --roll-setpoint 0 --pitch-setpoint 0
```

Do not add a surface-write path until the aircraft file, surface indices,
deflection signs, override ownership, restoration behaviour and command-to-
realised effectiveness have passed read-only and low-authority gates.

## Identification required before engagement

1. Obtain the exact EHEKATL `.acf` used in X-Plane 12 and archive its hash.
2. Map each elevon and rudder to its realised deflection array index.
3. Verify sign, zero, deflection limit, slew and cross-coupling one surface at a
   time in paused and live read-only diagnostics.
4. Collect stabilised small-amplitude multisine data at low, nominal and high
   dynamic pressure.
5. Estimate the full control-effectiveness matrix and covariance, including
   actuator dynamics and dependence on angle of attack.
6. Freeze the allocator and safety monitor before the first engaged design
   pilot. Preserve backstepping as permanent fallback.
