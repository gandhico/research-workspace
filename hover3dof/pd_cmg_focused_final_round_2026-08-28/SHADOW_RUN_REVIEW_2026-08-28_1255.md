# Review of the 12:55 Q8 shadow runs

Review date: 2026-08-28. These runs were executed by the user before the final
MuJoCo-conformance revision of the isolated runner.

## Runs reviewed

| Run | Controller | Samples | Abort | Deadline misses | Saturation |
|---|---|---:|---|---:|---:|
| `pd_dryrun_20260828_125528` | PD | 1000 | none | 0 | 0 |
| `pd-cmg_dryrun_20260828_125534` | PD-CMG | 1000 | none | 0 | 0 |

Both used `armed=false`. The Q8 encoders were read, the control calculation was
executed, and the trace was saved, but every physical analog output was forced
to zero. The final zero-output cleanup and card close both completed.

The zero tracking error, zero gate drive, and constant computed `[2,2,2,2] V`
are expected because the controller tared a stationary rig and the `hover`
reference is identically zero. This confirms the zero-reference signal path; it
does not validate closed-loop tracking or nonzero CMG/PES behavior.

## Provenance boundary

The manifests record runner SHA-256
`c27b0324669fb60a564745f18ffc37d0c14f25b4be84a7a6bc745e47b55064be`.
That build predates the final MuJoCo-conformance correction. In particular it
used:

- the LQR-equivalent Euler-PD bridge;
- one neural/PES step per 5 ms hardware interval;
- the earlier `actual cap = beta * max-residual-volts` convention;
- `beta=0.1`, `max-residual-volts=1`, hence an actual 0.1 V cap;
- `learning-rate=0.0002`, `k-error=2`;
- membrane, gate, and decoder-weight logging, but not the subsequently added
  quaternion, body-rate, activity, current, and PES-target channels.

The frozen MuJoCo-matched runner SHA-256 is
`4D4D442CD302F660DE05C0E958EC3398F7218B358B0158DE75080EADE1F2B597`.
It uses quaternion PD, body angular velocity, six torque-space CMG units, ten
0.5 ms neural substeps, and a motor cap independent of beta.

Therefore these two traces are retained as successful pre-conformance Q8 shadow
checks, but they are excluded from the final PD-versus-PD-CMG result set.

## Correct next shadow check

Use a nonzero reference while still disarmed to exercise quaternion PD, CMG,
PES, allocation, saturation flags, and every neuron/decoder channel:

```powershell
$py = 'C:\Research\hover3dof\.venv\Scripts\python.exe'
$root = 'C:\Research\hover3dof\pd_cmg_focused_final_round_2026-08-28'
$runner = "$root\runners\hover3dof_hil_pd_cmg_control.py"

& $py $runner --controller pd --pd-profile mujoco --mission hard45 --duration 5
& $py $runner --controller pd-cmg --pd-profile mujoco --mission hard45 --duration 5 `
  --beta 0.5 --motor-residual-cap-volts 0.3 --learning-rate 0.0008 `
  --k-error 8 --k-rate 0 --neural-substeps 10
```

Because these commands omit `--armed`, the physical outputs remain zero. The
second command's 0.3 V cap is the first staged hardware authority, but in this
shadow run it affects only computed/logged commands.
