# Omnicopter physical--virtual test card

## Stop conditions before arming

- [ ] Hardware revision and parameter-set ID recorded.
- [ ] Propellers, reversible ESC mode and positive direction inspected.
- [ ] Rotor numbers 1--8 mapped one at a time at minimum safe command.
- [ ] Each physical positive thrust axis matches the corresponding MuJoCo site +Z.
- [ ] Command-to-newton calibration and bounds loaded per motor.
- [ ] IMU-to-body and motion-capture-to-MuJoCo transforms frozen.
- [ ] Acquisition timestamps, clock offset, packet loss and transport delay logged.
- [ ] Independent E-stop, attitude/rate/position/voltage limits exercised.
- [ ] PD-only tethered check completed before any residual authority.

Any unchecked item stops the armed test.

## Run order

| Run | Mode | Controller with authority | CMG setting | Objective |
|---:|---|---|---|---|
| 1 | Desarmed | None | Off | Validate logs, clocks and transforms. |
| 2 | Bench | Individual motor | Off | Validate numbering, signs, curves and delays. |
| 3 | Restrained | PD | Off | Validate allocator and body-wrench directions. |
| 4 | Shadow | PD | All four compute only | Direct/Nengo command equivalence on real state. |
| 5 | Tethered hover | PD | CMG frozen, zero authority | Establish physical baseline and noise floor. |
| 6 | Tethered hover | PD + frozen residual | Low predeclared authority | Check residual sign and saturation interaction. |
| 7 | Tethered hover | PD + online PES | Low authority and independent abort | First adaptive feasibility test. |
| 8+ | Confirmatory blocks | Randomized PD/CMG variants | Pre-registered | Paired performance comparison. |

## Minimum files per run

- immutable raw hardware log;
- common-frame converted log and transform manifest;
- shadow MuJoCo log;
- controller/parameter/model hashes;
- battery state, environment and hardware revision;
- operator, date, run order and deviations;
- paired validation report.

Do not tune using confirmatory runs. If a change is required, close that batch,
record the change, and begin a new versioned batch with new retained trials.
