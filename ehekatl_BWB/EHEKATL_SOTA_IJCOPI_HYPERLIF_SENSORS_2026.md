# EHEKATL BWB: state of the art, IJCOPI acceptance plan, HyperLIF/CMG benchmark, and physical sensor architecture

**Date:** 2026-09-17  
**Scope:** BWB control and optimisation; delay-aware LQR versus constrained DeePC; HyperLIF/CMG neuron benchmarking; sensor architecture for a physical EHEKATL logistics and defence-oriented research platform.

## 1. Executive verdict

The EHEKATL programme should be separated into three publishable contributions:

1. **IJCOPI paper:** delay-aware discrete LQR versus constrained regularised Data-Enabled Predictive Control (DeePC), using the same measured command path, 35 Hz deadline, limits, datasets, safety supervisor, and paired protocol.
2. **Aerospace control paper:** covariance-aware constrained allocation of independently commanded elevons and rudders below a formally specified backstepping virtual-control law.
3. **Neuromorphic paper:** bounded HyperLIF/CMG residual augmentation benchmarked fairly against recognised spiking neuron families and a matched non-spiking recurrent baseline.

Do not combine these three novelty claims in one manuscript. The IJCOPI submission becomes stronger when it answers one narrow question rigorously: **what survives when offline optimal control is transferred to the measured real-time BWB simulator interface?**

## 2. Where BWB control and optimisation are now

### 2.1 Established state of the art

| Research line | Demonstrated advance | Remaining limitation | Meaning for EHEKATL |
|---|---|---|---|
| X-48 flight research | NASA/Boeing X-48B flight tests demonstrated envelope expansion, system identification, stall recovery, and interaction of a highly redundant set of surfaces. The baseline system used nonlinear dynamic inversion and pseudo-daisy-chain allocation at 200 Hz. | Highly specialised vehicle and proprietary control architecture; difficult to reproduce; results do not answer whether modern direct data-driven predictive control transfers to another BWB. | Use X-48 as the flight-research benchmark for instrumentation, excitation, envelope gates, and control-authority reporting. |
| Linear optimal and robust control | LQR/LQG, structured robust control, mixed H2/H-infinity, and LPV control provide efficient synthesis and explicit robustness objectives. Integrated H-infinity work has jointly sized BWB surfaces, allocation, and flight-control gains. | Model dependence, local validity, weight selection, and weak native treatment of actuator constraints in LQR. | The delay-aware discrete LQR is the transparent model-based comparator; do not use the old continuous gain at 35 Hz. |
| Control allocation | Weighted pseudoinverse, direct allocation, redistributed pseudoinverse, QP, nonlinear allocation, and incremental allocation distribute redundant moment commands under limits. | Linear effectiveness assumptions fail at high angle of attack or large deflection. Wind-tunnel BWB results reported typical 10-30% moment loss and, for some algorithms, only about 50% of requested moment. | Make full control-effectiveness covariance and constrained allocation the core of the elevon paper. |
| Nonlinear and fault-tolerant flight control | Backstepping, sliding-mode variants, INDI, observers, adaptive fuzzy control, and RBF disturbance observers address nonlinearities, uncertain aerodynamics, CG movement, and actuator faults. | Much of the public BWB evidence remains simulation-only; results are hard to compare because plants, commands, constraints, and metrics differ. | Preserve backstepping as the safety architecture, but reconcile the CCE adaptive law with the current scalar Python implementation. |
| Data-driven predictive control | DeePC has experimental quadrotor results and growing robust, kernel, distributionally robust, closed-loop, segmented, and hybrid formulations. | Public aerial evidence is dominated by rotorcraft; noise, data conditioning, nonlinear envelope changes, and online optimisation remain central limitations. | A carefully bounded BWB/X-Plane transfer study is distinctive, but the novelty must be the experimental optimisation protocol and implementation-gap diagnosis. |
| Neuromorphic flight control | Recent work demonstrates SNN flight control, neuromorphic attitude estimation, and event-camera-to-control pipelines on small drones. | Direct flight-critical use remains sensitive to training distribution, timing, hardware mapping, and safety certification; most evidence is rotorcraft-based. | Use HyperLIF/CMG only as bounded residual authority with a classical fallback and report deadline/energy/sparsity metrics. |

### 2.2 Primary literature anchors

- NASA X-48B flight research and instrumentation objectives: [X-48B test progress](https://ntrs.nasa.gov/citations/20090020686), [flight-test overview](https://ntrs.nasa.gov/api/citations/20090005939/downloads/20090005939.pdf), and [in-flight stability analysis](https://ntrs.nasa.gov/citations/20080034515).
- X-48/HWB optimal allocation and yaw augmentation: [Engine Yaw Augmentation for Hybrid-Wing-Body Aircraft](https://ntrs.nasa.gov/api/citations/20110016018/downloads/20110016018.pdf).
- BWB allocation nonlinearities and wind-tunnel evidence: [Control allocation performance for BWB aircraft](https://doi.org/10.1016/j.ast.2013.01.004).
- Integrated BWB surface, control-law, and allocation design using structured H-infinity optimisation: [Integrated design of flight-control surfaces and laws](https://doi.org/10.1016/j.ifacol.2017.08.2085).
- Fault-tolerant BWB backstepping with RBF disturbance observation: [Observer-based incremental backstepping sliding-mode control](https://doi.org/10.1016/j.neucom.2021.08.069).
- Current configuration-level review: [BWB design, stability, and control optimisation review](https://doi.org/10.1016/j.treng.2025.100397).
- Current tailless-control review: [A Review of Control Methods for Tailless Aircraft](https://doi.org/10.1142/S2737480724300026).
- DeePC foundations and flight evidence: [original DeePC](https://arxiv.org/abs/1811.05890), [regularised/distributionally robust DeePC](https://arxiv.org/abs/1903.06804), [quadrotor DeePC](https://doi.org/10.1002/rnc.5686), and [Hybrid DeePC](https://doi.org/10.1109/OJCSYS.2025.3625364).

### 2.3 The defensible research gap

Do not claim that DeePC has never been used in aircraft without a formal systematic search. The defensible statement is:

> Published DeePC flight-control evidence is concentrated in multirotor platforms, while the open BWB literature is dominated by model-based robust/nonlinear control and optimisation-based control allocation. A reproducible comparison of delay-aware discrete LQR and constrained DeePC through a measured BWB simulator command-to-realised-actuator path is therefore underrepresented.

The EHEKATL paper can fill four connected gaps:

1. transfer from continuous offline design to a sampled, delayed realised control path;
2. common-interface comparison of model-based and behavioural data-driven optimisation;
3. safety-supervised real-time implementation with explicit actuator ownership and restoration;
4. publication of negative gates, timing distributions, code, configurations, and held-out datasets.

## 3. Strong IJCOPI paper plan

### 3.1 Final title

**From Offline Optimality to Real-Time Simulation Flight: Delay-Aware LQR and Constrained DeePC for an EHEKATL Blended-Wing-Body Aircraft**

### 3.2 Central question

Under identical measured input/output definitions, delays, command and slew limits, update rate, trim condition, safety supervisor, and held-out trials, how do delay-aware discrete LQR and constrained regularised DeePC differ in safety, tracking, constraint use, robustness, and real-time computational behaviour?

### 3.3 Controller scope

- **Controller 1:** discrete LQR/DARE designed on the identified command-to-realised roll cascade at 35 Hz, including the measured delay.
- **Controller 2:** constrained regularised DeePC using the same control input and measured output, with a frozen Hankel dataset and predeclared hyperparameters.
- **Safety controller:** the existing recovery controller remains outside the performance comparison and acts only as the permanent fallback.

The current DeePC implementation is P-only roll-rate regulation near R3. Either keep the title and claims explicitly local, or pass a new preregistered reconstruction gate before adding roll angle or another output. Do not quietly promote a failed multi-output model into the paper.

### 3.4 What makes the contribution strong enough

The manuscript must be an optimisation/informatics paper, not a generic aerospace simulation report. Its five contributions should be stated explicitly:

1. **Implementation-gap diagnosis:** exact sampled analysis explains why the published continuous LQR gains are not implementation-ready at 35 Hz.
2. **Measured-path redesign:** discrete LQR is synthesised on the identified command-to-realised path rather than the nominal aerodynamic plant alone.
3. **Constraint-aware behavioural optimisation:** DeePC includes command and slew constraints, regularisation, frozen data, and online deadline monitoring.
4. **Matched real-time protocol:** both controllers use the same interface, limits, initial-state gates, safety monitor, log schema, and restoration test.
5. **Reproducibility and claim discipline:** all data, code, thresholds, negative gates, and computational timing are archived; failed superiority or reconstruction gates remain visible.

IJCOPI has relevant precedent in [robust discrete hexacopter control](https://ijcopi.org/ojs/article/view/423), [SNN implementation of LQR](https://ijcopi.org/ojs/article/view/320), [tail-sitter identification and adaptive control](https://ijcopi.org/ojs/article/view/1230), and a 2026 [PSO quadrotor study using five flight scenarios](https://ijcopi.org/ojs/article/view/1347). The paper must nevertheless foreground computational optimisation to satisfy the [journal scope](https://ijcopi.org/ojs/about).

### 3.5 Minimum evidence gates before submission

| Gate | Minimum pass condition |
|---|---|
| Interface parity | Identical input/output definition, routing, scaling, saturation, slew, and logging for both controllers. |
| Safety | Zero uncommanded ownership events; every abort restores the original actuator state; all nonfinite/deadline paths tested. |
| Paired experiment | Use the planned within-session switching protocol. The current power analysis indicates approximately 24 matched pulse pairs rather than separate reload comparisons. |
| Primary outcome | Freeze one primary metric before confirmation runs, such as normalised roll-rate IAE over a fixed window. |
| Secondary outcomes | RMSE, peak, settling time, control energy, total variation, command/slew utilisation, fallback count, restoration error. |
| Timing | Report median, 95th percentile, 99th percentile, maximum solve time, and deadline misses for both controllers. |
| Robustness | Matched held-out disturbances, sensor-noise injection, delay perturbation, gain/effectiveness perturbation, and at least low/nominal/high dynamic-pressure stress conditions. |
| DeePC ablation | Dataset length, Tini, horizon, regularisation, constraints on/off, and noise level; do not tune on the confirmation set. |
| LQR ablation | Bryson-normalised weights, delay/no-delay model, saturation-aware simulation, and sensitivity to identified-model covariance. |
| Statistics | Paired effect estimate with 95% interval, exact sample count, seed policy, exclusions, and multiplicity control for secondary outcomes. |
| Reproducibility | Environment lock file, controller configuration hashes, raw logs, processing scripts, figure scripts, and machine-readable claim matrix. |

If superiority remains unconfirmed, use an implementation-feasibility/non-inferiority conclusion rather than forcing a win. A credible negative result with a mechanistic explanation is stronger than a fragile positive claim.

### 3.6 Proposed experimental matrix

Use a two-stage design:

**Stage A - frozen local comparison**

- operating point: R3;
- task: P-only roll-rate regulation;
- 24 matched LQR/DeePC pulse pairs using within-session switching;
- identical initial-state and safety gates;
- confirmation dataset opened only after all code and thresholds are frozen.

**Stage B - generalisation stress test**

- dynamic pressure: low, nominal, high;
- disturbances: deterministic gust trace and stochastic noise with shared seeds;
- delay: nominal plus bounded injected delay;
- effectiveness: nominal plus bounded multiplicative loss;
- constraints: nominal and deliberately active command/slew cases.

Stage B may be reported as stress evidence rather than formal flight-envelope validation if it lacks adequate repeats.

### 3.7 Required figures and tables

1. EHEKATL control-path and safety architecture.
2. Failure of the old continuous LQR after exact 35 Hz sampling.
3. Identified delay-aware plant and residual diagnostics.
4. DeePC Hankel/prediction/optimisation schematic.
5. Matched time histories with command and slew constraints visible.
6. Paired primary-outcome estimation plot, not only bar charts.
7. Solver-time empirical distributions and deadline line.
8. Robustness heat map across delay/noise/effectiveness conditions.
9. Claim-and-evidence table showing pass, limited, failed, and planned claims.

### 3.8 Twenty-page manuscript allocation

| Section | Target pages |
|---|---:|
| Title, bilingual metadata, abstract, keywords | 1 |
| Introduction and tightly scoped SOTA | 2 |
| EHEKATL realised control path and implementation failure | 2.5 |
| Delay-aware LQR and constrained DeePC formulations | 4 |
| Frozen protocol, safety, and statistics | 2.5 |
| Results and timing | 4.5 |
| Discussion, limitations, and applicability | 1.5 |
| Conclusion | 0.5 |
| References | 1.5 |

Follow the current [IJCOPI submission requirements](https://www.ijcopi.org/ojs/about/submissions): British English, Word/OpenOffice/RTF delivery, 70-150-word abstract, 4-6 keywords, APA 7, double-blind version, AI-use disclosure, and no more than 20 pages.

## 4. HyperLIF/CMG neuron research line

### 4.1 Correct architectural description

The local CMG-PES implementation is a **Coupled Membrane-Gate continuous unit** with a sigmoid gate, continuous activity, paired positive/negative channels, and an online PES decoder. In its current canonical form it is non-spiking. It must not be called an SNN neuron merely because it evolved from the HyperLIF programme.

The local evidence is useful but mixed:

- fixed-gate HyperLIF produced a spurious apparent gain caused by baseline detuning and was correctly rejected;
- learned HyperLIF/CMG-PES produced strong simulation results in some quadrotor conditions;
- the same architecture showed platform-dependent negative results on the CF2 rotor model;
- real Quanser Hover results were small or mixed outside a near-zero hover baseline;
- LIF, AdaptiveLIF, Izhikevich, and LIFRate comparisons exist in emulation, but those neuron families were not safety-qualified on the physical rig;
- conventional spiking families destabilised one 6-DOF simulation even at low residual authority, which makes authority matching and safety gating mandatory.

This history should be treated as a strength: the EHEKATL study can be designed to prevent the exact confounds already found in the earlier programme.

### 4.2 Benchmark roster

Use one common recurrent/residual network shell and change only the neuron model:

1. CMG with fixed decoder.
2. CMG-PES with online learned decoder.
3. HyperLIF and Adaptive HyperLIF.
4. Standard LIF.
5. Adaptive LIF / ALIF or LSNN cell.
6. Parametric LIF (PLIF; learnable membrane time constant).
7. Izhikevich.
8. LIFRate as a continuous rate-coded control.
9. Matched GRU or simple recurrent ANN as a non-spiking temporal baseline.
10. Zero-residual and residual-authority-matched classical controls.

PLIF provides a recognised learnable-time-constant comparator ([ICCV 2021 paper](https://openaccess.thecvf.com/content/ICCV2021/html/Fang_Incorporating_Learnable_Membrane_Time_Constant_To_Enhance_Learning_of_Spiking_ICCV_2021_paper.html)); ALIF/LSNN tests slow adaptive state ([LSNN foundation](https://proceedings.neurips.cc/paper_files/paper/2018/hash/c203d8a151612acf12457e4d67635a95-Abstract.html)); Izhikevich tests richer spiking/bursting dynamics at moderate cost ([original model](https://doi.org/10.1109/TNN.2003.820440)); and e-prop provides a recognised online eligibility-trace learning baseline ([Nature Communications 2020](https://doi.org/10.1038/s41467-020-17236-y)).

### 4.3 Fair-comparison rules

Freeze all of the following across neuron families:

- identical sensor features, normalisation, encoder, decoder dimension, and control target;
- matched neuron count and a second comparison matched by parameter or operation budget;
- identical residual-authority bound and actuator QP;
- identical training data, train/validation/test split, seeds, and stopping rule;
- separate comparisons for offline BPTT/surrogate training and online PES/e-prop learning;
- identical quantisation and timestep where a neuromorphic deployment is claimed;
- one classical controller with residual authority set exactly to zero;
- one baseline-gain control to prove that an apparent benefit is not simple detuning.

Report both control and computational metrics:

```text
tracking: IAE, RMSE, peak, settling, allocation residual
safety: envelope exceedance, saturation time, fallback events
robustness: gust/noise/fault/delay performance and OOD rejection
neural: spike rate, sparsity, membrane/gate saturation, residual duty cycle
compute: median/p95/max latency, jitter, memory, SynOps/MACs, deadline misses
energy: measured board power where available; otherwise label an energy proxy explicitly
```

### 4.4 Initial EHEKATL placement

Do not let the neuron directly command elevons. Use:

```text
backstepping virtual moment
  + bounded CMG/HyperLIF residual moment or effectiveness correction
  -> covariance-aware constrained allocator
  -> independent surfaces
```

The allocator and envelope monitor remain authoritative. Residual authority should begin at 2-5% of the available moment, then increase only after offline, software-in-the-loop, and hardware-in-the-loop gates. This follows the safer residual architecture while preserving a meaningful neuromorphic research question.

Recent flight evidence makes an event-camera extension scientifically attractive: neuromorphic vision-to-control has been flown on small drones ([Science Robotics 2024](https://doi.org/10.1126/scirobotics.adi0591)), and SNN attitude estimation/control has been deployed on a Crazyflie-class vehicle ([IEEE RA-L research record](https://research.tudelft.nl/en/publications/neuromorphic-attitude-estimation-and-control/)). EHEKATL should first use event vision for state/residual estimation, landing, or optical-flow experiments, not as the only stabilising sensor.

## 5. Physical EHEKATL sensor architecture

### 5.1 Platform assumptions from the thesis

The current design record describes approximately:

- 2.4 m span and 1.4 m2 reference area;
- 1.65 m centre-body/root-chord length;
- approximately 6.4-7 kg nominal simulated mass and 10 kg maximum configured mass;
- 19-35 m/s design speed range;
- eight trailing-edge surfaces/elevons and two rudders.

These values must be reweighed and surveyed on the physical airframe before procurement. Sensor placement and wiring must be included in the CG/inertia update.

### 5.2 Priority 0: flight safety and scientific truth set

| Sensor subsystem | Recommended capability | Research purpose |
|---|---|---|
| Primary autopilot IMUs | Three isolated/redundant accelerometer-gyro paths plus dual barometers | Flight-control state estimate and sensor-fault voting. Current Cube-class hardware exposes triple IMU and dual barometer architectures. |
| Independent reference INS | Separate calibrated IMU or dual-GNSS/INS, 200-400 Hz output | Truth/reference channel independent of the controller estimator; essential for evaluating covariance and estimator bias. |
| Dual-antenna multi-band RTK GNSS | 10-20 Hz RTK/PVT, carrier-phase raw data, PPS | Position, velocity, nonmagnetic heading, centimetre-class relative trajectories when corrections and geometry permit, and system-wide time base. |
| Five-hole air-data probe | Dynamic/static pressure, angle of attack, sideslip; calibrated over 19-35 m/s | Identifies the BWB aerodynamic state and control-effectiveness map; much more valuable than pitot airspeed alone. |
| Independent static pressure and temperature | Shielded static source, barometric altitude, outside-air temperature | Air-density correction and independent check of the multi-hole probe. |
| Surface-position sensing | Absolute encoder on every independently commanded elevon/rudder, at least 100-200 Hz | Requested-versus-realised deflection, backlash, rate limits, jams, and allocator validation. |
| Actuator health | Servo current, bus voltage, winding/case temperature where available | Detects saturation, binding, thermal limits, and impending failure. |
| Propulsion telemetry | Motor RPM, ESC current/voltage/temperature, commanded duty/throttle | Thrust identification, asymmetric-thrust studies, power/energy optimisation, and fault labelling. |
| Structural instrumentation | Wing-root strain, selected elevon hinge/servo load, and high-rate vibration accelerometers | Loads, aeroelastic coupling, flutter warning research, and wind-tunnel/flight correlation. |
| Time-synchronised recorder | Hardware PPS/time trigger, lossless binary logging, independent power and storage | Aligns IMU, air data, surfaces, power, neural activity, and external ground truth. |

PX4 documents fusion of IMU, GNSS, and other position sources in EKF2 and supports independent external INS sources ([PX4 INS guidance](https://docs.px4.io/main/en/sensor/inertial_navigation_systems)). CubePilot documents triple IMUs and dual barometers in current Cube modules ([Cube module overview](https://docs.cubepilot.org/user-guides/autopilot/the-cube-module-overview)). These are architectural examples, not a procurement decision.

For the research truth channel, a dual-GNSS/INS such as the VN-300 class offers high-rate attitude/position output and GNSS-compass heading ([official product brief](https://www.vectornav.com/docs/default-source/product-brief/vn-300-product-brief.pdf)). A lower-cost RTK path can use a ZED-F9P-class receiver with raw carrier observations and PPS ([official data sheet](https://content.u-blox.com/sites/default/files/documents/ZED-F9P-01B_DataSheet_UBX-17051259.pdf)). A UAV multi-function probe should measure airspeed, altitude, angle of attack, and sideslip ([Aeroprobe overview](https://www.aeroprobe.com/)). Final hardware must be selected only after mass, range, environmental, interface, and budget requirements are frozen.

### 5.3 Priority 1: landing, logistics, and payload research

| Sensor | Logistics experiment enabled |
|---|---|
| Downward range sensor (lidar or radar altimeter) | Repeatable flare/landing height and terrain clearance; radar is preferable where dust, fog, or vegetation affects lidar. |
| Downward global-shutter RGB camera | Visual landing markers, optical flow, package-drop-zone documentation, and photogrammetry. |
| Cargo-bay load cells | Payload mass, load shift, in-flight CG estimation, and release verification. |
| Cargo temperature/humidity | Cold-chain and sensitive-material logistics research. |
| Cargo shock/vibration logger | Quantifies handling quality and payload survivability. |
| Door/latch position and current sensing | Confirms cargo-bay state and detects mechanical binding. |
| UWB ranging/tag receiver | Precision relative positioning at warehouses, landing zones, or GNSS-constrained test sites. |
| RFID/barcode interface | Chain-of-custody and autonomous cargo identification. |

The principal logistics research question should be **control and energy performance under uncertain payload mass and CG**, not simply carrying a box. Load cells, RTK/INS, air data, surface encoders, and power telemetry make that question publishable.

### 5.4 Priority 2: defence-oriented, non-weapon research sensing

Focus the platform on sensing, resilience, navigation, and communications research:

| Sensor | Defensible research use |
|---|---|
| Synchronized RGB plus long-wave infrared camera | Search and rescue, inspection, night operations, multispectral fusion, and perception under poor illumination. |
| Event camera | Low-latency optical flow, landing, high-dynamic-range motion sensing, and direct HyperLIF/SNN benchmarking. A current EVK4-class unit provides 1280x720 event resolution, synchronization, and a roughly 40 g form factor ([official documentation](https://docs.prophesee.ai/stable/hw/evk/evk4.html)). |
| Passive RF spectrum monitor | Research on C2/GNSS interference detection and link-quality awareness; use only within applicable radio and privacy law. |
| Dual independent navigation chains | Detects GNSS/INS disagreement and enables bounded dead-reckoning tests without claiming certified anti-jam performance. |
| ADS-B In / cooperative traffic receiver | Situational awareness during authorised research operations; do not add ADS-B Out without regulatory and integration review. |
| Magnetometer array or remote compass | Studies motor/current magnetic interference and estimator consistency. |
| Multiband communications telemetry | Measures link latency, packet loss, RSSI, handover, and redundancy for the later two-aircraft programme. |

Thermal and RF equipment may have export, frequency, privacy, or end-use restrictions. Those checks belong in the procurement gate. Low radar observability is not a sensor-suite claim and requires a separate electromagnetic/RCS programme.

### 5.5 Neuromorphic sensor package

For HyperLIF/CMG research, synchronise the following on one time base:

```text
event camera events
global-shutter RGB frames
IMU/INS raw increments
air-data alpha, beta, qbar
requested and realised surface positions
CMG/HyperLIF membrane, gate, spike, decoder, and residual traces
classical command, allocator solution, constraints, and fallback state
```

The event camera is a research payload, not a replacement for the IMU/air-data safety chain. Hardware timestamps or PPS-triggered timestamp discipline are mandatory; software receipt time is inadequate for latency claims.

### 5.6 Integration architecture

```text
Safety flight controller
  - redundant IMUs/barometers
  - GNSS, airspeed, basic actuator outputs
  - envelope monitor and recovery controller

Research computer
  - DeePC / allocation / CMG-HyperLIF experiments
  - event/RGB/thermal perception
  - cannot bypass surface and envelope bounds

Independent recorder / truth chain
  - reference INS/RTK
  - air data, surface encoders, loads, power
  - PPS-disciplined timestamps

Ground station
  - health telemetry, experiment arming, abort
  - no dependence on the research computer for safe recovery
```

Keep experimental research computation partitioned from the safety controller. Every experimental command must pass through the same bound, rate, allocation, and abort layer.

### 5.7 Procurement order

1. Surface encoders and logging before new control laws.
2. Five-hole air-data system before covariance-aware allocation.
3. Independent INS/dual RTK and PPS distribution before claims about estimator covariance or manoeuvre accuracy.
4. Power, RPM, temperature, and load sensing before logistics optimisation.
5. Event/RGB package before HyperLIF perception experiments.
6. Thermal, UWB, passive RF, and redundant communications after the basic flight-research platform is qualified.

FAA Remote ID and operating rules must be checked for each physical campaign. The FAA describes Remote ID as broadcasting aircraft identification and location and provides a research letter-of-authorisation path in some cases ([FAA Remote ID](https://www.faa.gov/uas/getting_started/remote_id)).

## 6. Publication sequence

| Paper | Primary contribution | Evidence threshold |
|---|---|---|
| IJCOPI | Reproducible delay-aware LQR versus constrained DeePC implementation study | Matched paired campaign, runtime statistics, stress tests, frozen claims |
| BWB allocation | Covariance-aware constrained allocation for eight elevons/two rudders below backstepping | Independent surface actuation, full effectiveness covariance, five manoeuvres, fault case |
| HyperLIF/CMG | Fair neuron-family residual-control benchmark | Identical shell/authority/training, classical controls, compute/energy metrics, held-out OOD cases |
| Sensor/logistics | Payload/CG-aware flight-control and energy optimisation | Physical load sensing, repeatable payload cases, RTK/air-data truth, energy accounting |
| Wind tunnel | Nonlinear surface effectiveness and uncertainty map | Calibrated force/moment balance and surface-state measurement |
| Two-aircraft system | Safe cooperative flight with communication constraints | Two independently qualified aircraft, link-loss fallback, relative navigation truth |

## 7. Claim boundaries

- X-Plane results are controller-in-the-loop simulation evidence, not physical flight evidence.
- Wind-tunnel results validate aerodynamic/control effectiveness, not free-flight handling qualities.
- CMG is currently a continuous coupled membrane-gate unit; the SNN claim belongs to explicitly spiking HyperLIF/LIF/ALIF/PLIF/Izhikevich variants.
- A BWB configuration can offer aerodynamic, volume, and payload advantages, but logistics value must be measured through payload fraction, range/endurance, energy, handling, and turnaround metrics.
- Defence relevance can be stated in terms of sensing, resilience, autonomy, cooperative control, and communications. Low observability and combat capability require separate evidence and should not be asserted in these control papers.
- No publication venue can be guaranteed to accept the work. The strategy above maximises defensibility, fit, and reproducibility while preserving negative results.
