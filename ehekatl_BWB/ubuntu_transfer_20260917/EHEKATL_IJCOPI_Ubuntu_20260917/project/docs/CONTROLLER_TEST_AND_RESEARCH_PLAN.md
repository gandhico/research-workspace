# Controller test and research plan

## Common direct-test structure

```text
                         R3 start gate
                              |
                    live / trim / ownership
                              |
          +-------------------+-------------------+
          |                   |                   |
   Backstepping 10 Hz      LQR 35 Hz          DeePC 35 Hz
   recovery reference    measured cascade      P-only frozen
          |                   |                   |
          +---------- rich state/control CSV ----+
                              |
                  automatic frozen analyzer
                              |
               PASS evidence or visible FAIL
```

LQR and DeePC direct runners both use captured trim, explicit roll/pitch axis
ownership, the original Backstepping pitch stabilizer, bounded roll commands,
latched Backstepping fallback, and guaranteed restoration. They do not emulate
the unsafe “leave the last command active” behavior of the historical runner.

## Real advances and gates

```text
[DONE] Backstepping repeatable R3 baseline and small-pulse recovery
   |
[DONE] Roll/pitch stabilized identification and held-out datasets
   |
[DONE] Local delay-aware models and offline LQR robustness
   |
[DONE] Safe R3 roll-LQR integration
   +--> [FAIL] required 30% matched improvement (observed ~11.1%)
   |
[DONE] P-only DeePC reconstruction, optimization, runtime, 243-case replay
   |
[DONE] 35-Hz observe integration and guarded design pilot
   +--> [BLOCKED] powered superiority benchmark is impractical
   |
[CURRENT] Stage 5 body-rate validation / experiment redesign
   |
[BLOCKED] Stage 6 attitude loop
   |
[BLOCKED] Stage 7 combined recovery comparison
```

## Direct R3 test procedure

1. Load the exact clean R3 situation: about 1700 m, 39 kt, 240 Pa, pitch 1.3°,
   low body rates, artificial stability on, automation off, live and not replay.
2. Run one controller only after a fresh reload.
3. Use the canonical one-command launchers:

```bash
cd /home/ubuntu/GHYN/Xplane_controllers/EHEKATL_BWB_XP12
bash lqr/run_lqr_direct.sh
```

or:

```bash
cd /home/ubuntu/GHYN/Xplane_controllers/EHEKATL_BWB_XP12
bash deepc/run_deepc_direct.sh
```

4. Each launcher creates `logs/direct_lqr_<timestamp>.csv` or
   `logs/direct_deepc_<timestamp>.csv`, then prints the frozen analyzer result.
5. A start-gate block, latch, missed timing gate, or analyzer failure is failed
   evidence. Reload before another controller; do not widen limits.

## Proposed continuation

### Track A — reproducible controller demonstration

- Collect only user-requested direct demonstrations, each from a fresh R3 reload.
- Register hashes and classify each log as demonstration, not confirmation.
- Generate one common plotting/scoring report for Backstepping, LQR, and DeePC.
- Do not infer superiority from unmatched direct runs.

### Track B — improve the research contribution offline

- Diagnose why the measured DeePC design-pilot advantage is not statistically
  identifiable under fresh-reload variation.
- Explore controller/experiment changes only on design/model evidence while
  keeping command, slew, safety, and held-out isolation unchanged.
- Require a materially larger robust effect and prospective power ≥0.80 at a
  practical duration before opening another confirmation campaign.

### Track C — paper synthesis now

- Report successful engineering results: control-path diagnosis, delay-aware
  identification, exact runtime integration, constraints, fallback, and failed
  performance/power gates.
- Present LQR and DeePC claims at their actual boundaries.
- Build figures/tables only from registered immutable logs and scripts.

## Next decision gate

Direct controller demonstrations are available now. Research advancement beyond
Stage 5 requires either:

- a practical, powered offline experiment redesign, or
- a controller redesign with a materially larger robust modeled effect.

Until then, Stage 6 attitude feedback and combined-controller claims remain blocked.
