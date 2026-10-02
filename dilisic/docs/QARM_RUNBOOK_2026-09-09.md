# QArm DILISIC readiness runbook — 2026-09-09

## Decision

Do not connect the present DILISIC output directly to either arm tomorrow.
The replication is verified against its software contract, but the QArm and
QArm Mini have no repository hardware runner, no identified command-to-joint
model, and no measured derivative/noise contract. The full QArm's available
workflow is position-servo based; PWM must only be considered on hardware/API
that explicitly exposes and documents it.

The safe deliverable for tomorrow is a **shadow replication**: acquire a
bounded joint log, identify the closed position-servo channel, replay DILISIC
without actuation, and compare its requested correction with measured limits.

## Mathematical interface that must be closed

The paper controller assumes a scalar affine plant

\[
q^{(4)}=f(x)+g(x)u+d,\qquad x=[q,\dot q,\ddot q,q^{(3)}]^T,
\]

with known input-gain sign and \(g(x)>0\). A vendor position command is instead
an input to an undocumented inner servo. Its observable closed-loop contract is
first screened as

\[
q_{k+1}=a_1q_k+a_2q_{k-1}+b u_{k-d}+c+\epsilon_k.
\]

Passing this screen does not turn the position command into the paper's
highest-derivative input. It only supports an outer-loop or shadow-mode study.

## Bench sequence

1. Mechanically support the arm; clear its workspace; keep a physical E-stop
   operator present. Confirm joint and command units from the exact installed
   PAL version.
2. Log one joint at a time with `time_s,command,position`. Use small,
   rate-limited, zero-mean multilevel steps about a safe pose. Never excite near
   a joint limit. Start with actuation disabled and confirm logging/timestamps.
3. Identify using the project environment:

   ```powershell
   cd C:\Research\dilisic
   .\.venv\Scripts\python.exe .\tools\qarm_identify_position_servo.py JOINT_LOG.csv --output JOINT_CONTRACT.json
   ```

4. Stop if any `checks` field is false. A true `shadow_ready` only authorizes
   offline replay/shadow comparison; the report intentionally keeps
   `direct_dilisic_actuation_ready=false`.
5. In shadow mode, log baseline command, raw DILISIC correction, bounded
   correction, tracking state, estimator state, loop time, saturation flags,
   E-stop/fault state, and timestamps. Send zero/baseline commands to hardware.
6. Only after an independent review should a bounded outer-loop correction be
   considered. Begin with one joint, low authority, hard position/rate/command
   limits, watchdog, stale-data rejection, baseline fallback, and an observer
   whose noise/bandwidth tradeoff is documented.

## No-go conditions

- wrong or changing input-gain sign; insufficient excitation; unstable fitted
  poles; sample jitter above 5%; poor chronological validation;
- unverified units, encoder zero, joint limits, command rate, or E-stop;
- derivative estimates dominated by noise; loop overruns or stale telemetry;
- any claim that the software-only DILISIC match proves QArm stability.

## Evidence already available

The corrected seven-agent simulation passes all 11 reference metrics at
`1e-6` relative tolerance. Eleven controller, experiment, and identification
tests pass, including a synthetic known-system delay/gain recovery test.
Hardware readiness remains a separate evidence gate by design.
