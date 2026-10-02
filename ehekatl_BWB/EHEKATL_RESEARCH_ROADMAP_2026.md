# EHEKATL BWB research and publication roadmap

**Prepared:** 2026-09-17  
**Project root:** `C:\Research\ehekatl_BWB`  
**Scope:** English dissertation/arXiv edition; LQR--DeePC optimal-control paper; adaptive-backstepping control allocation with elevons.

## 1. Executive decisions

1. Preserve the demonstrated simulator recovery controller as the baseline and permanent fallback. Until its scalar Python recurrence is reconciled with the adaptive vector law in the CCE paper, describe it as a **backstepping-inspired empirical baseline**, not as the implemented adaptive backstepping proof.
2. The optimal-control manuscript should compare the delay-aware LQR and constrained **Data-enabled Predictive Control (DeePC)** under one frozen interface and protocol. The project does not currently implement Differentiable Predictive Control, which is also abbreviated DPC.
3. Do not add a third main controller to the IJCOPI paper yet. Backstepping + LQR + DeePC already gives a clear baseline/model-based/data-driven structure. A gain-scheduled LPV/H-infinity controller is the best later robust-optimal comparator once multiple flight regimes have been identified.
4. Put the new optimal element for the elevon work in the **control allocator**: a bounded weighted least-squares or quadratic-program allocator below the backstepping virtual-control law.
5. Treat LIF/Adaptive HyperLIF as a later bounded residual estimator or residual allocator, not as the initial flight-critical controller. The classical stack must be frozen first.
6. Claims of instability, high maneuverability, low radar observability, or military capability require separate evidence. The existing thesis and CCE paper state that longitudinal static stability was obtained at a selected condition; a new relaxed-stability configuration must therefore be identified and documented before calling EHEKATL unstable.

## 2. Evidence already present in the archives

| Evidence | Current result | Publication implication |
|---|---|---|
| Dissertation backstepping | Repeatable R3 baseline and small-pulse recovery | Use as reference and fallback; do not claim global recovery |
| Historical fixed LQR | Large excursions and repeated safety disengagement | Useful implementation-gap evidence; not evidence that LQR is generally poor |
| Identified delay-aware LQR | Safe R3 integration; matched integral improvement about 11.1% | Failed the frozen 30% gate; report the failure honestly |
| P-only constrained DeePC | 243/243 offline uncertainty cases passed; 35 Hz integration and one guarded pilot passed | Real-time feasibility supported; superiority over LQR is not established |
| Direct LQR and DeePC demonstrations | Both safe, bounded, and restored actuator ownership | Separate reloads make the comparison descriptive, not causal |
| Interface and safety tests | 84 local unit/interface/routing tests pass on the audited source | The current bridge is a strong foundation for a common controller API |

The standalone `EHEKATL_BWB_LQR_IJCOPI.zip` manuscript is not submission-ready: it contains a hard-coded 2019 journal header, red author notes, an empty conclusion, incomplete X-Plane discussion, and only the pre-X-Plane LQR result. The complete project contains the stronger and more honest paper narrative.

Two technical audits must precede new claims:

- The published continuous-time gains are not suitable for direct 35 Hz use even on the stated paper model. An exact zero-order-hold audit gave sampled closed-loop spectral radii of about **1.521 longitudinally** and **31.008 laterally**. The very fast lateral pole (`-1503.55 s^-1`) implies an unrealistic sub-millisecond time scale. This confirms why the paper must use the separately identified, delay-aware **discrete** design rather than present the old gains as implementation-ready.
- `backstepping/Backstepping.py` is a scalar recurrence with fixed gains. It is not the adaptive vector/regressor law proved in the CCE paper. The simulator implementation can remain the successful empirical baseline, but it must not be labelled “adaptive backstepping” until equations, states, parameter updates, and the Lyapunov claim have been reconciled and implemented.

## 3. Workstream A — revised English dissertation for arXiv

### Proposed title

**Design and Control of the EHEKATL Blended-Wing-Body Aircraft**

### Editorial model

Prepare a **revised English edition**, not an undocumented literal replacement of the 2023 Spanish thesis. Keep a change log distinguishing:

- faithful translation;
- correction of typographical, equation, unit, and reference errors;
- updated time-sensitive statements and literature;
- new post-thesis notes or appendices.

The revised edition should cite the 2022 CCE paper and clearly label material that was previously published. Before upload, confirm the author's/university's right to distribute the translated derivative work. arXiv accepts translations, but the submitter must hold or obtain the needed rights.

### Source audit findings

- The active LaTeX source contains about **53,100 translatable words**, 89 figure environments, 33 tables, 242 displayed-equation environments, and roughly 1,248 inline mathematical expressions.
- The bundled `tesis.pdf` is an obsolete 2019 template containing placeholder authorship, a 2099 date, lorem ipsum, and a cart-pendulum example. It is **not** the translation or submission baseline.
- `Capitulo3/diseno_experimento.tex` is a 3,343-line monolith that contains the logical Chapters 3--6. The nominal Chapter 4 file is effectively empty. Split the logical chapters before translation so results are not silently misplaced.
- The archive contains 336 graphics in the main figure directory, but only 90 are referenced; 246 unused assets consume about 45 MB. Build a minimal public package and rename active assets to ASCII, space-free, case-stable paths.
- One equation label is duplicated, four bibliography records lack required fields, 25 contain explicitly empty fields, six DOI values are malformed as URL fields, and one bibliography record appears duplicated under an inconsistent key.
- Chapter 5 has only one citation command and Chapter 6 none. The control derivation and simulator validation need a targeted literature update rather than only linguistic translation.
- Only 13 of 89 figure environments contain citations. Audit authorship, licences, and attribution for historical aircraft, NASA/Airbus, map, and externally derived figures; embedded Spanish text in raster/vector artwork must be recreated or relabelled.
- A clean local PDFLaTeX test currently stops on missing `emptypage.sty`; the thesis class also declares the wrong internal class name. Produce a clean Spanish reference PDF before beginning English changes.

### Translation sequence

1. Freeze the Spanish source and generate a source manifest with hashes.
2. Remove stale outputs and unused assets, repair the class/build dependencies, split the logical chapters, and produce a clean Spanish reference build.
3. Build a terminology glossary: BWB, aerodynamic control surface, longitudinal/lateral-directional dynamics, angle of attack, sideslip, static margin, control effectiveness, backstepping, adaptive law, and X-Plane datarefs. Use US English for the arXiv thesis, but British English for the IJCOPI derivative manuscript as required by that journal.
4. Translate title, abstract, objectives, contributions, and conclusions first; use them to lock terminology and English voice.
5. Translate Chapters 1--3 section-by-section while preserving equations, labels, citations, and figure numbering.
6. Reconstruct Chapter 4. Its source file is essentially empty; results currently appear elsewhere and must be organized rather than silently invented.
7. Translate or redraw Spanish text embedded in figures. Preserve raw numerical data and do not relabel a plot unless its axes and units are verified.
8. Audit every bibliography entry, DOI, author name, year, URL, and citation-to-claim relationship.
9. Compile, render every page, and perform visual QA for equations, floats, tables, cross-references, bookmarks, and font embedding.
10. Produce a clean arXiv package containing only required `.tex`, `.bib`/`.bbl`, class/macro, and figure files. Remove backups, unused figures, generated PDFs, and private comments.

### arXiv package notes

- Suggested primary category: `eess.SY` (Systems and Control), with a possible aerospace cross-list only if accepted by the relevant category moderators.
- Identify it in the Comments field as an English revised edition/translation of the 2023 master's thesis.
- arXiv currently compiles TeX from the upload root, supports multi-file LaTeX projects, and requires authors to inspect the generated PDF.
- If an English-only version is submitted, do not append the Spanish source unless a bilingual edition is intentionally desired. For multilingual submissions, arXiv asks for the full English version first.

## 4. Workstream B — IJCOPI optimal-control paper

### Recommended manuscript

**From Offline Optimality to Real-Time Simulation Flight: Delay-Aware LQR and Constrained DeePC for an EHEKATL Blended-Wing-Body Aircraft**

### Central research question

When the same measured input path, delay, limits, safety supervisor, operating condition, and held-out protocol are used, what can nominal LQR and constrained regularized DeePC reliably claim for real-time roll-rate regulation of EHEKATL in X-Plane 12?

### Controller roles

| Controller | Role in the paper |
|---|---|
| Original backstepping | Validated recovery baseline and permanent fallback; not a new contribution |
| Delay-aware discrete LQR | Transparent model-based optimal baseline |
| Regularized constrained DeePC | Data-enabled predictive optimizer; current main candidate |

### Claims to make

- The thesis-model LQR is stable offline but does not transfer directly to the realized simulator control path.
- Measured routing, trim, artificial stability, delay, and operating point materially change the problem.
- Both frozen optimized controllers can execute at 35 Hz with limits, start/abort gates, fallback, and verified restoration.
- The LQR failed the preregistered 30% improvement gate; DeePC superiority remains unconfirmed because the powered benchmark is impractical under the current small-pulse protocol.
- Negative gates are reproducible engineering evidence, not failed research.

### Claims not to make

- DeePC is globally superior to LQR.
- Either controller stabilizes the full flight envelope.
- A single P-only local controller provides attitude control or large-disturbance recovery.
- X-Plane demonstrations are physical flight tests.

### IJCOPI compliance corrections

The current journal instructions require an English Word/OpenOffice/RTF manuscript, APA 7 references, British spelling, a 70--150 word abstract, 4--6 keywords, no more than 20 pages, double-blind review, bilingual English/Spanish metadata, and disclosure of AI-tool use. Replace the copied 2019 LaTeX masthead with the current journal template. Because IJCOPI is principally an optimisation/informatics journal, foreground the constrained optimisation formulation, dataset governance, reproducibility, and computation; a generic aircraft-control paper is a weaker scope match.

Before posting a paper preprint, ask the editor how the journal's prior-publication wording applies to arXiv. The English dissertation and the journal paper must also cite each other appropriately and avoid substantial uncited text reuse.

### Best additional optimal-control method

The best later high-level comparator is **LPV/H-infinity control**:

- it addresses the demonstrated operating-point and model-uncertainty problem;
- it is appropriate for a relaxed-stability BWB;
- it avoids a full online MPC implementation;
- it can be gain-scheduled over airspeed, dynamic pressure, angle of attack, and mass/CG.

Its limitation is that it needs a validated multi-regime model and careful uncertainty/weight definitions. Do not add it to the current paper until R3/R4 and additional regimes are identified independently.

LQG is useful as an estimator layer when sensor-noise/process covariance is introduced, but it is not a strong third controller contribution by itself. INDI is an excellent later flight-control benchmark for the elevon configuration, although it is not primarily an optimal-control method.

## 5. Workstream C — backstepping + constrained control allocation + elevons

### Proposed paper

**Covariance-Aware Optimal Control Allocation for an Adaptive-Backstepping EHEKATL Blended-Wing-Body Aircraft with Distributed Elevons**

### Required architecture

```text
reference / manoeuvre command
        -> state estimator and envelope monitor
        -> adaptive backstepping virtual moment command [L_c, M_c, N_c]
        -> constrained allocator using B_eff(x, delta)
        -> independent elevon/rudder commands
        -> X-Plane aircraft / later wind-tunnel model
        -> measured states, moments, and surface positions
```

The initial allocator should solve

```text
min_delta  ||Wm (B_eff delta - v_cmd)||^2
         + lambda_delta ||Wd (delta - delta_trim)||^2
         + lambda_rate  ||Wr (delta - delta_previous)||^2
         + lambda_drag  J_drag(delta)

subject to deflection limits, rate limits, failed/jammed surface constraints,
and optional hinge-moment/load limits.
```

Use bounded weighted least squares or an active-set QP first. Add a nonlinear/sequential allocator only after the measured effectiveness map shows that the linear local model is inadequate.

The publishable optimization contribution should be an **uncertainty-aware allocator**, not merely the application of a standard QP. Propagate the estimated control-effectiveness covariance through regularized Mahalanobis weighting, sampled/chance constraints, or a bounded worst-case robust QP. Treat the allocation residual as a bounded disturbance in an input-to-state-stability or uniform-ultimate-boundedness argument; do not promise asymptotic convergence in the presence of saturation, rate limits, identification error, or neural residuals.

### Interface requirement

The current `sendCTRL` bridge commands aggregate roll/pitch/yaw inputs and X-Plane performs the mixing. It reads distributed elevator/aileron deflections but does not independently command each surface. Therefore:

1. clone the `.acf` model for an elevon/control-allocation variant;
2. define an authoritative surface table containing surface ID, side, span station, function, sign convention, deflection/rate limits, command dataref, measurement dataref, and failure mask;
3. reconcile the CCE prose (two elevators, two ailerons, one rudder) with its figure showing eight named trailing-edge segments and apparent paired rudders;
4. define independently actuated symmetric elevon pairs in Plane Maker;
5. prove which surface datarefs are writable under the relevant override, or implement a small X-Plane SDK plugin exposing explicit surface commands;
6. add a `SurfaceCommand` API with units, sign, bounds, slew, ownership, and restoration semantics;
7. log requested and actual deflection for every surface;
8. retain the common controller facade (`SetPoint`, `output`, `clear`, `update`) above the new allocator adapter;
9. add interface-in-the-loop tests before any engaged run.

The supplied full-project ZIP does **not** contain the `.acf` aircraft file, so the surface configuration cannot yet be reproduced from this archive alone. Register the exact aircraft file/version and hash it before modifying the geometry.

### Control-effectiveness identification

Estimate the effectiveness matrix and its full coefficient covariance as a function of at least dynamic pressure, angle of attack, sideslip, airspeed, and deflection:

```text
B_eff = partial [L, M, N] / partial [delta_elevon_1, ..., delta_elevon_n, delta_r]
```

Use symmetric sweeps for pitch and differential sweeps for roll. Include rudder/elevon cross-coupling and interaction terms. Wind-tunnel measurements later become the strongest independent validation because BWB control effectiveness can be nonlinear in angle of attack and surface deflection.

### Five-manoeuvre validation matrix

1. Symmetric elevon pitch doublet / pull-up recovery.
2. Differential elevon roll doublet / bank reversal.
3. Rudder doublet and Dutch-roll damping to expose yaw--roll coupling.
4. Coordinated climbing/descending turn with simultaneous pitch, roll, and yaw demand.
5. Gust recovery with one elevon degraded, rate-limited, or jammed.

For each manoeuvre compare: fixed elevon mixing, weighted pseudoinverse, deterministic constrained QP, and covariance-aware robust QP. Add neural augmentation only after these four classical baselines are frozen.

### Covariance and statistics

Five manoeuvres are conditions, not enough samples for a covariance estimate. Run repeated paired trials per condition. Record the metric vector

```text
[IAE, RMSE, peak error, settling time, control energy,
 allocation residual, saturation fraction, maximum load, compute time].
```

Estimate:

- parameter covariance for each identified effectiveness matrix;
- state-estimator covariance if a Kalman/LQG layer is used;
- paired performance covariance across repeated trials;
- 95% bootstrap intervals and effect sizes;
- cross-manoeuvre covariance only after sufficient independent repeats.

Use held-out runs and freeze all thresholds before opening confirmation data.

## 6. HyperLIF/CMG and SNN-neuron benchmarking

The requested neural component is the existing **HyperLIF/CMG programme**, not an RBF network. The current canonical CMG-PES unit is a continuous, non-spiking coupled membrane-gate unit with paired channels and a learned decoder; explicitly spiking HyperLIF variants must therefore be distinguished from CMG in the paper. Continue the local neuron-family benchmark rather than presenting CMG alone.

Safe integration order:

1. classical backstepping + allocator is baseline and backup;
2. CMG-PES or HyperLIF predicts a virtual-moment residual, disturbance, or effectiveness correction;
3. a hard bound limits every neural residual to a documented fraction of available control authority;
4. allocator constraints and the safety supervisor remain authoritative;
5. compare fixed CMG, learned CMG-PES, HyperLIF/Adaptive HyperLIF, LIF, ALIF/LSNN, PLIF, Izhikevich, LIFRate, and a parameter-matched GRU/recurrent ANN;
6. use identical features, encoder/decoder, neuron or parameter budget, residual authority, training splits, seeds, and deadlines;
7. report tracking, safety, OOD robustness, spikes/sparsity, latency/jitter, memory, operations, and measured energy where available;
8. retain zero-residual and baseline-gain controls so a result cannot be explained by controller detuning;
9. only after held-out success consider an event-triggered two-aircraft communication/formation layer.

Do not put unvalidated HyperLIF results into the translated 2023 dissertation or the current LQR--DeePC paper. Add it as future work there and develop it as a separate contribution once the classical elevon stack is frozen.

## 7. Optimal-control history: advances and limits

| Period | Technique | Main advance | Main limitation | EHEKATL relevance |
|---|---|---|---|---|
| 1690s--1750s | Calculus of variations; Euler--Lagrange | Optimises an entire trajectory/function | Mostly open-loop; hard constraints and uncertainty are awkward | Mathematical foundation |
| 1830s | Hamilton--Jacobi theory | Value/action formulation and Hamiltonian structure | Nonlinear PDE is difficult in more than a few states | Foundation of HJB |
| 1950s | Bellman dynamic programming / HJB | Feedback optimality and sequential decisions | Curse of dimensionality | Foundation of MPC, RL, and approximate DP |
| 1950s--1960s | Pontryagin maximum principle | Necessary conditions for constrained nonlinear optimal trajectories | Two-point boundary problems; usually open-loop/local | Manoeuvre and trajectory optimisation |
| 1960s | LQR, Riccati theory, Kalman filtering, LQG | Efficient optimal feedback/estimation for linear-quadratic-Gaussian systems | Linear/quadratic assumptions; no native hard constraints; model dependence | Existing baseline; LQG estimator option |
| 1970s--1980s | Robust/minimax and H-infinity control | Optimises worst-case disturbance attenuation and model uncertainty | Can be conservative; weighting/uncertainty modelling is decisive | Strong future BWB comparator |
| 1970s--1990s | MPC | Receding-horizon optimisation with explicit constraints | Model and online-compute burden; certification and horizon tuning | Historical importance; intentionally not the present aircraft controller |
| 1980s--2000s | Direct collocation, pseudospectral methods, DDP/iLQR | Practical nonlinear trajectory optimisation | Local minima and computational burden; feedback still needs a tracking law | Offline aggressive manoeuvre design |
| 1990s--present | LPV/gain scheduling and integrated flight/control design | Covers changing operating regimes and co-designs effectors/laws | Scheduling validity and interpolation guarantees are difficult | High value after multi-regime identification |
| 1990s--present | Adaptive dynamic programming and reinforcement learning | Learns long-horizon policies and value functions | Data, safety, distribution shift, interpretability, certification | Later residual/formation work, not initial flight-critical control |
| 2010s--present | Optimisation-based control allocation | Handles redundant effectors, constraints, faults, drag/load objectives | Depends on accurate effectiveness maps and reliable real-time solvers | Core of the elevon paper |
| 2019--present | DeePC and related data-driven predictive control | Predicts and optimises directly from persistently exciting I/O trajectories | Noise, conditioning, data volume, local validity, and online optimisation | Already implemented; current paper focus |
| 2020s--present | Differentiable Predictive Control (DPC) | Trains fast explicit neural policies from differentiable closed-loop objectives | Approximate constraints/guarantees; needs a trustworthy differentiable model and OOD protection | Separate future study; not the current DeePC code |
| 2020s--present | Safe learning, barrier filters, differentiable optimisation layers | Combines learning with explicit safety constraints and runtime filters | Certificates inherit model/set assumptions; feasibility and timing matter | Possible HyperLIF residual safety layer |

## 8. Priority literature

### DeePC / data-driven predictive control

- Coulson, Lygeros, and Doerfler, [Data-Enabled Predictive Control: In the Shallows of the DeePC](https://arxiv.org/abs/1811.05890).
- Coulson, Lygeros, and Doerfler, [Regularized and Distributionally Robust DeePC](https://arxiv.org/abs/1903.06804).
- Huang, Zhen, Lygeros, and Doerfler, [Robust DeePC: tractable formulations and guarantees](https://arxiv.org/abs/2105.07199).
- Elokda et al., [Data-enabled predictive control for quadcopters](https://doi.org/10.1002/rnc.5686).
- Teutsch et al., [Handbook of linear data-driven predictive control](https://doi.org/10.1016/j.arcontrol.2023.100914).

### BWB / elevons / allocation

- Johansen and Fossen, [Control allocation--a survey](https://doi.org/10.1016/j.automatica.2013.01.035).
- Waters et al., [Control allocation performance for BWB aircraft and its impact on surface design](https://doi.org/10.1016/j.ast.2013.01.004).
- Choi, Kim, and Kim, [Robust control allocation with adaptive backstepping flight control](https://doi.org/10.1177/0954410013483687).
- [Integrated design of flight-control surfaces and laws for new aircraft configurations](https://doi.org/10.1016/j.ifacol.2017.08.2085).
- Chen et al., [Assessment of critical technologies for BWB conceptual design](https://doi.org/10.1016/j.cja.2019.06.006).
- [Direct Lift Control: principles, merits, and implementations](https://doi.org/10.1016/j.paerosci.2024.101073).

### DPC / learning-based control

- Drgona, Tuor, and Vrabie, [Learning constrained parametric differentiable predictive-control policies](https://doi.org/10.1109/TSMC.2024.3368026).
- Ames et al., [Control Barrier Function Based Quadratic Programs](https://doi.org/10.1109/TAC.2016.2638961).
- Fisac et al., [A general safety framework for learning-based control](https://doi.org/10.1109/TAC.2018.2876389).

## 9. Paper portfolio and venue order

| Output | Minimum defensible novelty | Best-fit venue direction |
|---|---|---|
| Revised English dissertation | Faithful/revised edition with corrections log and reproducible sources | arXiv `eess.SY` |
| LQR--DeePC paper | Common constrained protocol, implementation-gap diagnosis, frozen negative gates, real-time feasibility | IJCOPI if optimisation/informatics is foregrounded; otherwise Control Engineering Practice |
| Backstepping + elevon allocation | Independent surfaces, measured effectiveness, constrained/fault-tolerant allocator, five manoeuvres | AIAA Journal of Aircraft or Aerospace Science and Technology; Journal of Guidance, Control, and Dynamics if control theory dominates |
| Wind-tunnel effectiveness paper | Nonlinear effectiveness map versus angle of attack/deflection and allocator prediction error | Aerospace Science and Technology or AIAA Journal of Aircraft |
| HyperLIF residual allocation | Bounded residual, matched neural/continuous baselines, safety filter, repeated trials | IEEE TAES or a controls/neuromorphic venue after classical validation |
| Two-aircraft multi-agent system | Formation/coordination with communication constraints and event-triggered HyperLIF hypothesis | Later IEEE TAES/JGCD/robotics-control paper |

## 10. Immediate execution order

1. Unpack the four archives into version-controlled worktrees; retain the ZIPs as immutable inputs.
2. Begin the English dissertation with a glossary, translated abstract, and a corrections register.
3. Replace the obsolete IJCOPI draft with the full LQR--DeePC manuscript evidence and current Word template.
4. Freeze a controller-interface specification and dataset/claim registry before new tests.
5. Clone the aircraft into an elevon variant and prove independent surface-command authority in observe-only/interface tests.
6. Identify the multi-regime surface-effectiveness map, including uncertainty covariance.
7. Implement bounded QP allocation under the proven backstepping supervisor.
8. Run the five-manoeuvre simulator campaign with repeated paired trials.
9. Add wind-tunnel data when available; do not delay the simulator/interface paper plan waiting for it.
10. Start HyperLIF only as a bounded residual after the classical allocator passes all gates.

## 11. Claim boundaries to retain

- Relaxed static stability can improve responsiveness and reduce some trim penalties, but “more unstable means more manoeuvrable” is not a general law. Actuator authority/rate, bandwidth, delay, structural load, aeroelasticity, and envelope protection set the usable manoeuvrability.
- A BWB shape may be compatible with low-observable design, but low radar cross-section is not established by planform alone. It requires electromagnetic modelling/measurement plus treatment of edges, gaps, inlets, exhausts, materials, and aspect angle.
- High-fidelity X-Plane evidence remains simulation evidence.
- Wind-tunnel data validates aerodynamics/control effectiveness, not complete free-flight performance.
- The later two-aircraft goal should be built on two independently safe vehicles; formation control must never be the only stabilising loop.
