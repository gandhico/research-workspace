# ACC 2027 QUBE pendulum closure record

**Date:** 2026-08-27  
**Platform:** Quanser QUBE Servo 3 pendulum in QLabs  
**Connection:** PAL virtual card, `hardware=0`, `tcpip://localhost:18923`  
**Controller source:** `C:\Research\papers\ACC2027_Gate_Residual_Control\src\gra_control\gate.py`  
**Canonical dataset:** `results\acc2027_twin\*closure_matched20*`  
**Canonical report:** `analysis\acc2027_twin_closure_matched20\aggregate.md`

This file is the continuation entry point for a future session. It distinguishes
what was measured from what is only proposed.

## 1. Bottom line

The canonical ACC gate-state controller was connected to the real QLabs/PAL
virtual-twin interface and exercised at 500 Hz. Three matched trials were run for
each of five controllers. Every trial accumulated exactly 20 s of upright balance,
remained balanced for its final 5 s, and reported zero amplifier faults and zero
stalls.

The matched nominal experiment does **not** demonstrate an accuracy improvement.
Classical LQR and the fixed/online residual variants converge to essentially the
same encoder-quantized limit cycle. This is a useful safety and transfer result,
not a performance result. Do not use the earlier apparent 14% improvement in a
paper claim; it disappeared when balance exposure was matched.

| Controller | n | final-5-s alpha RMS (deg) | vs classical | residual RMS (V) |
|---|---:|---:|---:|---:|
| classical | 3 | 1.0581 +/- 0.0012 | reference | 0.0000 |
| fixed residual | 3 | 1.0590 +/- 0.0020 | -0.08% | 0.0798 |
| adaptive-conductance residual | 3 | 1.1170 +/- 0.1003 | -5.57% | 0.0748 |
| online-PES fixed conductance | 3 | 1.0566 +/- 0.0011 | +0.15% | 0.0482 |
| online-PES adaptive conductance | 3 | 1.0570 +/- 0.0015 | +0.10% | 0.0415 |

The adaptive-conductance mean is degraded by one run that selected the alternate
approximately 1.23-degree QLabs limit cycle. The same alternate branch appeared
under classical and other controllers in the earlier fixed-wall-time dataset, so
it cannot presently be attributed to adaptive conductance.

## 2. Exact architecture

The balance state is

\[
x=[\theta,\alpha,\dot\theta,\dot\alpha]^\top,
\]

where `theta` is the rotary-arm angle and `alpha=0` is upright. Because PAL zeros
the encoders at construction, the runner first measures the hanging reference
`alpha_h` and applies

\[
\alpha=\operatorname{wrap}_{[-\pi,\pi)}
(\alpha_{raw}-\alpha_h-\pi).
\]

The validated QLabs LQR voltage is

\[
v_0=\operatorname{sat}_{5\,V}(Kx),\qquad
K=[-1.000,\ 26.72,\ -0.8269,\ 2.214].
\]

The normalized baseline demand is pair encoded:

\[
z=v_0/5,\quad I^+=I_b+I_g\max(z,0),\quad
I^-=I_b+I_g\max(-z,0),
\]

with `I_b=0.75` and `I_g=1.25`. Each HyperLIF unit evolves as

\[
\dot r=\frac{\sigma(\alpha_n[v-(v_{th}-\gamma r)])-r}{\tau_r},
\]

\[
\dot v=-\frac{v-v_{rest}}{\tau}+\frac{I}{\tau}
-g(I)r^2(v-v_{reset}),
\]

where fixed conductance uses `g(I)=g0` and adaptive conductance uses
`g(I)=g0+g1|I|`. Activity is the continuous gate state, not a spike count:

\[
a=\operatorname{clip}(10^5r,0,1).
\]

The fixed decoder is `W=[1,-1]`. Online PES uses

\[
s_k=\operatorname{clip}(W_ka_k,-1,1),
\]

\[
y_k^*=\operatorname{clip}
\left(k_e\frac{\alpha_k}{20^\circ}
+k_d\frac{\dot\alpha_k}{6\,rad/s},-1,1\right),
\]

\[
W_{k+1}=\Pi_{[-6,6]}
\left(W_k+\eta(y_k^*-s_k)a_k^\top-\lambda W_k\right).
\]

All canonical conditions except the separately available legacy-blend ablation
preserve the classical backbone:

\[
v=\operatorname{sat}_{5\,V}(v_0+\beta\,5s),
\qquad \beta=0.35/5=0.07.
\]

Thus the requested neural contribution is bounded to 0.35 V before final command
saturation. The residual is disabled during energy swing-up; it operates only in
upright balance.

## 3. QLabs connection and safety path

The Python runner constructs:

```python
QubeServo3(id=0, hardware=0, frequency=500, pendulum=1, readMode=1)
```

PAL maps this to the QLabs QUBE 3 pendulum virtual card on port 18923. The loop:

1. reads `motorPosition`, `pendulumPosition`, `motorSpeed`, `pendulumSpeed`,
   `motorCurrent`, `amplifierFault`, and `motorStallDetected`;
2. computes classical swing-up or LQR plus the bounded residual;
3. sends one scalar with `write_voltage(v)`;
4. uses the RGB LED as a phase/error indicator; and
5. always sends 0 V, sets the LED red, terminates the virtual amplifier, and
   closes the card in a `finally` block.

This runner cannot select physical hardware: `hardware=0` is hard-coded. It is
therefore a virtual-twin runner, not a hardware runner.

The working machine paths on 2026-08-27 were:

```text
Python: C:\Users\gandhico\AppData\Local\miniconda3\envs\hyperlif\python.exe
PAL:    C:\Users\gandhico\Documents\Quanser_Academic_Resources_tmp\0_libraries\python
ACC:    C:\Research\papers\ACC2027_Gate_Residual_Control
```

The runner auto-discovers these paths and also accepts `--pal-path` and
`--acc-root`. Every summary records the Python executable and SHA-256 hashes of
both the runner and canonical controller source.

## 4. Fair matched protocol

1. Command 0 V until raw pendulum position spans less than 0.5 degrees over a
   1.5 s window. Do not use the tachometer for rest detection; QLabs has a
   persistent approximately 0.061 rad/s bias at rest.
2. Record the hanging raw angle after settling.
3. Use the unchanged classical energy swing-up controller.
4. Capture balance only when `|alpha| <= 20 deg`, `|alpha_dot| <= 6 rad/s`, and
   `|theta| <= 110 deg`; retain balance while `|alpha| <= 35 deg`.
5. Accumulate exactly 20.0 s of actual balance samples for every controller.
6. Abort at 90 s wall time if 20 s of balance cannot be accumulated.
7. Compare the final 5 s and repeat each controller three times.

Capture time is logged but is **not** a matched performance metric because the
QLabs arm state is not reset between separate PAL processes.

## 5. What was invalidated

The archived fixed-30-s-wall-time dataset is under
`analysis\acc2027_twin_closure_n3`. It appeared to show approximately 14%
improvement for most residual controllers. That comparison was confounded because
swing-up consumed a different fraction of each run; one online learner received
14.8 s of balance data while another received approximately 29 s. A subsequent
matched classical run also selected the lower 1.06-degree limit cycle. The
apparent improvement must therefore not be cited.

QLabs encoder resolution is `2*pi/2048`, or about 0.176 degrees/count. The twin
exhibits repeatable limit-cycle branches near 1.06 degrees and 1.23 degrees RMS.
Nominal RMS differences of this size require reset-controlled repetitions and
cannot safely be assigned to the residual controller.

## 6. Reproduction commands

Open QLabs with the QUBE Servo 3 pendulum scene, then run:

```powershell
cd C:\Research\pendulum

# Safe 0-V connectivity and convention check
$env:PYTHONPATH = 'C:\Users\gandhico\Documents\Quanser_Academic_Resources_tmp\0_libraries\python'
& C:\Users\gandhico\AppData\Local\miniconda3\envs\hyperlif\python.exe `
  .\runners\twin_diagnostic.py 3

# Canonical matched matrix, hardware=0 only
.\scripts\run_acc2027_twin_matrix.ps1 `
  -BalanceDuration 20 -MaxDuration 90 -Trials 3 `
  -ResidualCapV 0.35 -Label paper_matched20

# Aggregate and plot
& C:\Research\papers\ACC2027_Gate_Residual_Control\.venv\Scripts\python.exe `
  .\tools\summarize_acc2027_twin.py `
  --label paper_matched20 `
  --output .\analysis\paper_matched20
```

## 7. Permitted and prohibited claims

Permitted:

- The same canonical gate-state implementation used by the MuJoCo drones ran
  through the QLabs/PAL QUBE interface at 500 Hz.
- A 0.35 V bounded additive residual preserved upright balance in all 12 neural
  trials, with zero reported faults or stalls.
- Online PES updated the decoder during operation.
- Under the matched nominal protocol, online-PES and fixed residual accuracy was
  practically equivalent to LQR.

Not permitted:

- The pendulum nominal experiment improved accuracy by 14%.
- Adaptive conductance improved pendulum performance.
- QLabs results are physical-hardware results.
- The current experiment establishes disturbance rejection or generalization.

## 8. If pendulum work is reopened

The next useful experiment is not another nominal hold. Implement a matched
disturbance benchmark with: classical swing-up; a slow arm-reference recentering
phase; an explicit `|theta| <= 25 deg` pass gate; identical voltage impulses;
fixed pre-perturb balance exposure; and at least three trials. Abort rather than
perturb from the arm hard stop. The July `twin_perturbation_benchmark.py` data are
unmatched and remain hypothesis-generating only.

For ACC 2027, the pendulum can currently support a cross-platform feasibility and
safety statement. The >50% performance evidence remains the X2 and explicit CF2
rotor-authority design experiments.
