# SOTA Literature Review — CMG-PES / HyperLIF Residual Neuromorphic Control
### For manuscript context. Compiled from live web search 2026-09-01 — every citation below was returned by an actual search, none fabricated from memory. Verify exact page/volume numbers before final submission; not all sources returned full bibliographic detail.

---

## 1. What fields does this paper integrate?

The architecture (paired continuous membrane-gate neurons, PES-learned decoder, additive bounded residual on top of a classical baseline, validated in MuJoCo *and* on real hardware) sits at the intersection of five literatures that are not usually combined in one paper:

| Field | Why this paper touches it | Centrality |
|---|---|---|
| **Neural Engineering Framework / Nengo** | The CMG unit and its Nengo-native port (`nengo_cmg.py`) are built directly on NEF principles (representation via population coding, transformation via decoded weights); PES is Nengo's own learning rule | **Core** |
| **Residual learning for control** | The whole architecture is "classical baseline + learned bounded correction" — the control-theory analogue of residual/RL-augmented control | **Core** |
| **Spiking vs. non-spiking neuromorphic models** | CMG is explicitly *non-spiking* (continuous membrane/gate ODE); the paper directly ablates it against LIF/Adaptive-LIF/Izhikevich under identical control conditions | **Core** |
| **Quadrotor/UAV control theory** | Baseline is quaternion-PD (spacecraft/rigid-body attitude control lineage) plus a Mellinger-Kumar-style differential-flatness position→attitude cascade | **Supporting** |
| **Hardware-in-the-loop / real-time embedded control** | Final validation is on a genuine 200 Hz hard-real-time physical rig (Quanser 3DOF Hover), not simulation-only | **Supporting** |
| **Sim-to-real transfer** | The paper explicitly measures and reports the simulation→hardware performance gap for this specific architecture | **Supporting** |
| **Adaptive control theory (L1/MRAC)** | Not directly benchmarked against, but is the paper's natural non-neuromorphic competitor set — see Section 4, Gap 1 | **Adjacent, underused** |

---

## 2. Our contribution(s) — stated precisely

1. **A residual-augmentation architecture validated on *both* simulation and real hardware with the same neuron model, same learning rule, and traceable code path** (see the companion technical audit's Part 4). Most SNN/neuromorphic-control papers found in this search stop at simulation (Trajectory Control of Quadrotors via SNN, MDPI 2024) or single-axis hardware (blimp PID-mimicking SNN); genuine multi-DOF sim+hardware validation of an *online-learning* neuromorphic residual is comparatively rare in what this search surfaced.

2. **A direct, controlled ablation of continuous (non-spiking) vs. spiking neuron families under identical residual-learning conditions on a demanding, coupled 6-DOF control task**, showing spiking families (LIF/ALIF/Izhikevich) destabilize even at 1/50th the continuous model's residual authority, while a matched non-spiking rate model (LIFRate) stays stable — isolating spiking discretization noise, not "being non-CMG," as the mechanism. The literature search found spiking-vs-rate comparisons framed around *training* stability (FORCE-trained LIF vs rate networks) but not real-time *control-loop* stability under a hard deadline — this appears to be a genuinely underexplored angle.

3. **A Nengo/NEF-verified implementation matched to a hand-rolled NumPy reference to ~1e-7 relative error**, which is a concrete reproducibility/hardware-portability contribution (NEF/Nengo models are the standard on-ramp to neuromorphic silicon such as Loihi/SpiNNaker, per the surveyed hardware literature).

4. **An honestly reported, quantified sim-to-real performance gap** for this specific architecture (large benefit on a heavier simulated platform, muted-to-negative on a lighter one and on real hardware) — contributing a data point to the sim-to-real literature specifically for neuromorphic residual controllers, a combination not directly covered by the general RL sim-to-real surveys found.

5. **A concrete systems/implementation finding**: online neuromorphic learning (Nengo) sharing a process with a monitoring GUI can silently violate a hard real-time control deadline via GIL/thread contention, invisible to per-component benchmarking — found, root-caused, and fixed this session. The general HIL literature covers timing/deadline concerns abstractly; this is a specific, reproducible neuromorphic-control instance of it.

---

## 3. Bibliography — see `SOTA_LITERATURE_REVIEW_2026-09-01.bib` (companion file)

Organized by field; full entries with URLs in the .bib file.

**NEF / Nengo / PES**: Eliasmith & Anderson (NEF foundations); Eliasmith et al., "Nengo and the Neural Engineering Framework: From Spikes to Cognition"; Bekolay et al., "Nengo: a Python tool for building large-scale functional brain models" (Frontiers in Neuroinformatics, 2014); Voelker & Eliasmith, "A Solution to the Dynamics of the Prescribed Error Sensitivity Learning Rule"; DeWolf, Stewart, Slotine & Eliasmith, "A spiking neural model of adaptive arm control" (Proc. Royal Society B, 2016); Nengo/low-power AI hardware for embedded neurorobotics (Frontiers in Neurorobotics, 2020).

**Spiking neuron models**: Izhikevich, "Simple model of spiking neurons" (IEEE Trans. Neural Networks, 2003); spike-frequency-adaptation reviews (Communications Engineering, 2024); non-spiking dynamic-leak neuron model for recurrent-network stability (2021).

**Online SNN learning / e-prop**: Bellec et al., "A solution to the learning dilemma for recurrent networks of spiking neurons" (Nature Communications, 2020).

**Neuromorphic UAV/robot control**: "Trajectory Control of Quadrotors via Spiking Neural Networks" (Electronics/MDPI, 2024); "Towards neuromorphic control: A spiking neural network based PID controller for UAV" (Stagsted, Vitale et al.); "Evolving Spiking Neural Networks to Mimic PID Control for Autonomous Blimps" (2023); "Neuromorphic Digital-Twin-based Controller for Indoor Multi-UAV Systems" (2025); "Embodied Neuromorphic Artificial Intelligence for Robotics" (survey, 2024); adaptive-control-of-wheelchair-arm-on-Loihi (Frontiers in Neuroscience, 2022).

**Residual/corrective control learning**: "Residual Policy Learning in Robotics" and "Residual Reinforcement Learning" overviews; "Residual Policy Learning for Vehicle Control of Autonomous Racing Cars" (2023); "Residual Reinforcement Learning for Robot Control".

**Classical quadrotor control**: Lee, Leok & McClamroch, "Geometric Tracking Control of a Quadrotor UAV on SE(3)" (CDC 2010) and the 2013 Asian J. Control follow-up; Mellinger & Kumar, "Minimum snap trajectory generation and control for quadrotors" (ICRA 2011); "Position and attitude control of multi-rotor aerial vehicles: A survey" (2019); cascade/time-scale-separation control surveys.

**Quaternion attitude control**: quaternion-feedback PD regulator surveys and Lyapunov-based results (multiple, spacecraft-attitude lineage).

**Adaptive control (L1/MRAC)**: "Geometric L1 Adaptive Attitude Control for a Quadrotor UAV" (Kotaru & Edmonson, arXiv:1910.07730).

**Neuromorphic hardware / HIL**: Davies et al., "Advancing Neuromorphic Computing With Loihi: A Survey of Results and Outlook" (2021); "Neuromorphic computing hardware and neural architectures for robotics" (survey); general HIL-simulation references (MathWorks/NI/Wikipedia, non-academic but standard).

**Sim-to-real**: "Sim-to-Real Transfer in Deep Reinforcement Learning for Robotics: a Survey" (2020); "Sim-to-(Multi)-Real: Transfer of Low-Level Robust Control Policies to Multiple Quadrotors" (2019).

---

## 4. Honest scoring against the SOTA

This is a scholarly self-assessment, not a promotional one — weaknesses are stated as plainly as strengths, matching the standard this whole research session has held to.

| Axis | Score (1-5) | Reasoning |
|---|---|---|
| **Novelty of the core idea** | 4/5 | Non-spiking, PES-learned residual on classical control, validated identically in sim and hardware, is a real gap — most neuromorphic-control papers surveyed are either purely simulated or single-axis hardware. Not a 5 because "residual on top of a baseline" itself is well-established (residual RL); the novelty is specifically in the *neuron model choice* and the *dual validation*, not the augmentation paradigm itself. |
| **Rigor of validation** | 4/5 | Genuine strength: Nengo-equivalence verified to ~1e-7, honest negative results reported (CF2, hardstep, yaw360), root causes chased down empirically rather than asserted. Held back from 5 by modest hardware sample sizes (a few runs per mission, not large statistical campaigns) and the neuron-family ablation being hardware-emulated only, not hardware-armed. |
| **Positioning against SOTA control baselines** | 2/5 | **Gap.** The baseline compared against is quaternion-PD only. The literature's actual current SOTA for robust/adaptive quadrotor control includes L1 adaptive control and geometric SE(3) control — neither is benchmarked. A reviewer from the controls community will ask "how does this compare to L1-adaptive or an MRAC baseline, not just PD?" |
| **Positioning against SOTA neuromorphic-control work** | 3/5 | Reasonably positioned against SNN-quadrotor-control papers (PID-mimicking, NEF-based stabilization) found in this search, but the paper does not cite or differentiate against the closest analogue found — DeWolf et al.'s Nengo-based adaptive arm control, which is architecturally the nearest prior work (Nengo + PES + residual-style adaptive correction, just on a different plant). This should be added and explicitly differentiated. |
| **Energy/hardware-efficiency framing** | 1/5 | **Gap.** A large fraction of the neuromorphic-computing literature's motivation is energy efficiency on actual neuromorphic silicon (Loihi et al.). This work runs CMG-PES on conventional CPU throughout — no power/energy claim is made or measured. The Nengo-equivalence result is a *portability* argument, not a demonstrated efficiency one. Worth stating explicitly as future work rather than leaving it implicit. |
| **Reproducibility / traceability** | 5/5 | Genuine strength, unusual for this literature: every result traces to a specific file, config, and commit-equivalent hash (this session's own audit). Most surveyed papers do not offer this. |
| **Honesty of reported results** | 5/5 | Negative and mixed results (CF2, hardstep, yaw360, HyperLIF's own self-diagnosed spurious fixed-gate result) are reported alongside wins, not filtered out — stronger than most of the surveyed literature, which tends to report only favorable configurations. |

**Overall**: a methodologically strong, honestly reported piece of work whose principal weakness for publication is *comparative scope*, not *rigor* — it under-benchmarks against the classical-control SOTA (L1/geometric) that reviewers in the controls community will expect, and it doesn't engage with the one closest neuromorphic-control precedent (DeWolf et al.) that a neuromorphic-computing reviewer will expect to see cited and differentiated. Both are addressable without new experiments — they're framing/positioning fixes, not additional data-collection needs, given time constraints already discussed this session. The energy-efficiency gap is a legitimate future-work item, not something fixable before submission without new hardware.
