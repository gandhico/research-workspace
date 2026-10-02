# Block Diagrams & Interactive GUI — Phase 2 (1-DOF altitude)

Companion artifacts to the `exp01` benchmark: a runnable **Nengo GUI** model and two
**block diagrams** (a Simulink-style classical loop and the NEF/neural loop), ready for the
paper.

---

## 1. Block diagrams (TikZ → PDF, paper-grade)

Source + compiled output in [`paper/diagrams/`](../paper/diagrams):

| File | What it shows |
|---|---|
| `blockdiagram_classical_altitude.{tex,pdf}` | **Simulink-style** classical loop: `Step → Σ → Kp → Σ(+mg) → Sat[0,u_max] → 1/m → Σ(−g) → 1/s → 1/s → z`, with altitude feedback (`−z`) and rate feedback (`Kd·ż`). |
| `blockdiagram_nef_altitude.{tex,pdf}` | **NEF/Nengo** loop, identical topology, but the PD law is computed by spiking ensembles `e_z`, `de_z`, `u_fb` (LIF); gravity `mg` is a feed-forward node; plant is a Nengo `Node`. |

Compile (MiKTeX, verified working here):
```bash
cd paper/diagrams
pdflatex -interaction=nonstopmode blockdiagram_classical_altitude.tex
pdflatex -interaction=nonstopmode blockdiagram_nef_altitude.tex
```
The `.tex` files are `standalone`, so the paper can `\input{}` them or `\includegraphics`
the PDFs.

### On "Simulink" specifically (honest status)
- **MATLAB/Simulink is not available in this environment** (verified in Phase 0). I therefore
  produced the classical loop as a **Simulink-style block diagram** rather than an actual
  `.slx`. The diagram is faithful to how the model would be wired in Simulink (Sum / Gain /
  Saturation / Integrator `1/s` blocks).
- The **role** Simulink plays in Victor's benchmark (the "conventional" reference) is filled
  here by the **classical Python controller** (`src/controllers_classical/altitude_pd.py`),
  which drives the *same* plant as the NEF controller and is validated against 2nd-order
  theory in `exp01`. That is the apples-to-apples comparison the paper needs.
- If you want a real `.slx`, I can write a MATLAB builder script (`new_system`/`add_block`/
  `add_line`) for you to run in your MATLAB 2025b — but I **cannot execute or verify it here**,
  so it would ship marked UNVERIFIED. Say the word and I'll add it.

---

## 2. Interactive Nengo GUI

Files in [`src/gui/`](../src/gui):
`gui_exp01_altitude_nef.py` (self-contained model) + `gui_exp01_altitude_nef.py.cfg`
(pre-arranged layout & live plots, in the native `nengo_gui 0.6.0` format — validated to load).

**Launch:**
```bash
cd src/gui
../../../.venv/Scripts/nengo.exe gui_exp01_altitude_nef.py
# or:  ../../../.venv/Scripts/python.exe -m nengo_gui gui_exp01_altitude_nef.py
```
Then press the play ▶ button. The `.cfg` opens the GUI straight onto the benchmark scenario
(a 1 m altitude step at t = 1 s) with four live displays:

| Plot | Signal |
|---|---|
| `z vs z_ref` | altitude tracking the reference (the headline result) |
| `u [N]` | thrust command (hover ≈ 8.83 N, transient peak ≈ 17 N) |
| `e_z` | decoded altitude error |
| `u_fb` | decoded PD feedback (thrust beyond hover) |

The network graph shows the live neuron populations and connections — i.e. the neuromorphic
"block diagram" animated. This is the same controller as `experiments/exp01`, so the GUI is a
visual companion to the quantitative benchmark (the offline runner remains the source of truth
for the metrics, since it also runs the classical and rate-mode controllers for comparison).

---

## 3. How this feeds the paper

- **Fig. (controller):** the two block diagrams side-by-side (classical vs NEF) for §IV.
- **Fig. (results):** `results/plots/exp01_altitude.png` + the metrics table.
- The GUI is for demos / advisor walkthroughs and for sanity-checking the neural dynamics; it
  is not itself a paper figure.
