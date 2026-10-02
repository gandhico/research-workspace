# Prespecified gain/readout sensitivity study

Created before inspecting any new sweep output. Frozen paper results and controllers are not edited.

Primary question: how do readout gain G and intrinsic conductance modulation chi affect closed-loop tracking and the measured neural states?

## Fixed protocol

- MuJoCo X2 and CF2-rotor (CF2 actuator scale 1.5; X2 scale 1).
- roll, full3, hard45, hardstep, yaw360; 45 s; 0.0005 s integration/control interval.
- Identical canonical quaternion PD, allocation, references, initial conditions and torque policy=model.
- beta=0.5, per-step PES eta=0.0008, decoder leak=0.000001, target=clip(-8 e_q), weight bound=6; seed=1, no noise/disturbance.
- Direct CMG: G in {1,100,1000,10000,100000,1000000}, chi in {0,1}: 120 runs, plus 10 fresh PD anchors.
- Ten exploratory memoryless paired-linear/PES comparators: a=[max(u0/ell,0),max(-u0/ell,0)], identical six features, W0, teacher, update, leak, clipping and authority. Not an optimally tuned classical adaptive controller.
- Eight Nengo cross-checks: X2/full3 and CF2/hardstep at G={1,1000,100000,1000000}, chi=1. This checks selected gains only; the main factorial sweep uses the direct reference implementation.

## Data and interpretation

Every case saves canonical trace.csv (5 ms), full-rate scalar tracking metrics, manifests, and compressed full-rate neural arrays (0.5 ms). Direct archives include exact pre-update decoder and decoder increment. Nengo archives use the canonical built-in probes and their documented timing.

Report every completed case, failures, error reduction relative to the matched fresh PD, activity saturation, raw-gate/conductance statistics, activity Gram spectrum, and decoder drift. One deterministic realization per cell; no confidence intervals or seed-based significance claims.

G is not in the intrinsic state equations. Changing G changes feature amplitude, clipping, effective PES excitation and, through feedback, the input trajectory. Keeping eta fixed is operational sensitivity, not an isolated representation comparison or an equalized-learning-rate benchmark. Do not replace the frozen G=100000 paper matrix with post-selected winners.

The paired-linear comparator removes membrane/gate memory and changes the feature map. It can refute claims that CMG is necessary for improvement, but cannot establish a universal ordering of tuned controllers.

No hardware access. No frozen source modifications. Each run records source hashes and the wrapper overrides.
