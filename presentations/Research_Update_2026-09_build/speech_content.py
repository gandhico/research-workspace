"""Speech, Q&A and cheat-sheet content for Research_Update_Slides_2026-09.

Single source for (a) the speaker notes written into the .pptx and (b) the printable
study guide. Superscripts are written as ^{...} and converted per output.
Every number here is copied from the same sources as the slides (see slide 12 notes).
"""

TOTAL_MINUTES = 16

SLIDES = [
    # ------------------------------------------------------------------ 1
    dict(
        n=1, title="ACC 2027 | Neuromorphic Residual Attitude Control", time="1:30",
        purpose="Explain the idea of the ACC paper in one breath: keep the classical controller, add a bounded, learned correction.",
        before="(After your “Papers” slide) We have three papers. Let me start with the most important one, the ACC paper.",
        speech=[
            "This is our ACC 2027 paper with Dr. Sandoval and Dr. García Carrillo: “Online PES Decoder Learning in Neuromorphic Residual UAV Attitude Control.”",
            "The problem is attitude tracking for quadrotors. The controller must follow fast references while the rotors have force limits, the sensors are noisy, and there are disturbances.",
            "Our idea is simple: we keep the classical controller, and we add a small learned correction on top. In the figure, the gray path at the top is the baseline: a quaternion PD, then the rotor allocation, then the MuJoCo plant. The blue box at the bottom is the neuromorphic residual.",
            "It has three parts. First, six coupled membrane–gate units, CMG units: one positive and one negative for each torque axis. They give us temporal features. Second, a decoder with eighteen weights that learns online with PES, the prescribed error sensitivity rule. Third, a bound: the correction can never be larger than beta times the torque limit, and it enters before the same allocator. So if beta is zero, we get the PD back exactly.",
            "On the right: we prove bounded states and weights and a conditional local stability result, and we test two airframes in MuJoCo, the Skydio X2 and the Crazyflie 2, with five missions, noise, disturbances and five neuron families.",
        ],
        short="We keep the quaternion PD and add a bounded CMG–PES correction before the rotor allocator; β = 0 gives the PD back.",
        numbers=[("CMG units / decoder weights", "6 / 18"), ("Residual bound", "|δ| ≤ β·ℓ, β = 0.5 in tests"),
                 ("Simulation", "MuJoCo X2 + CF2, 5 missions × 45 s, 2 kHz"),
                 ("Direct vs Nengo", "2.0×10^{-6} relative mean difference")],
        qa=[
            ("What is PES?", "Prescribed Error Sensitivity: a local, error-driven rule for the decoder weights, ΔW = η·ε·aᵀ, with a small leak and a projection that keeps the weights bounded. The error ε is a PD-like teaching target minus the residual output."),
            ("What is a CMG unit? Is it a control-moment gyroscope?", "No. CMG here means coupled membrane–gate: a continuous neuron with a leaky membrane and a gate that changes its conductance. No spikes and no reset; we read the gate-derived activity as a temporal feature."),
            ("Your theorem certifies a tiny β, but you use 0.5. Isn’t that a problem?", "The theorem is conservative: it gives local input-to-state stability for small β and shows how the bound scales with β·ℓ. At β = 0.5, stability is observed in every run, not certified, and we write that explicitly in the paper."),
            ("Why add a residual instead of replacing the controller?", "Safety and interpretability. The classical loop stays the stabilizing backbone, the correction is bounded, and setting β = 0 recovers the baseline exactly."),
        ],
        avoid=["“Guaranteed stable” (it is certified only for small β).", "“Energy-efficient” (not measured).", "“Well-tuned PD” for the fixed baseline."],
    ),
    # ------------------------------------------------------------------ 2
    dict(
        n=2, title="ACC 2027 | Results — Where the Residual Helps", time="2:00",
        purpose="Show the three-rung baseline ladder and say clearly where the residual helps and where it does not.",
        before="",
        speech=[
            "Here are the results. The chart shows how much the residual reduces the attitude error, as a geometric mean over the five missions.",
            "We test it on three baselines, from weak to strong. Against the fixed PD, the error goes down about 44 percent on both vehicles. With rate feedforward, about 58 percent. With a bandwidth-tuned PD plus feedforward, it is still 36 percent on the X2, but only 6.5 percent on the Crazyflie. The table below gives the absolute numbers.",
            "On the right there are three messages. First, robustness: with realistic sensor noise, every reduction stays positive, and under repeated torque bursts the X2 error drops from 11.5 to 6.65 degrees.",
            "Second, the mechanism: the gain comes from decoder learning. If we freeze the decoder, we keep at most one fifth of the improvement. LIF, ALIF and LIFRate neurons are almost silent with this input, so PES has nothing to learn from.",
            "Third, the limits, which we state in the paper. The gain gets smaller as the baseline gets stronger. On Hardstep, with the tuned baseline, the error gets worse; that mission has 63 to 111 degree steps, so it is dominated by slewing. And this is simulation only: at beta 0.5, stability is observed, not certified.",
            "So the take-away: the residual is a bounded, recoverable complement to good model-free control, not a replacement for tuning.",
        ],
        short="CMG–PES reduces the error on every baseline (44% → 58% → 6–36%), is robust to noise and bursts, and PES learning is the lever; Hardstep at ρ = 3 is the exception.",
        numbers=[("Fixed PD (X2 / CF2)", "−44.5% / −44.2%"), ("PD + rate ff, ρ = 1", "−57.8% / −57.6%"),
                 ("Tuned PD + ff, ρ = 3", "−35.6% / −6.5%"), ("Per case vs fixed PD", "17.3–60.6%"),
                 ("Realistic noise", "all positive, 18.1–55.8%"), ("X2 torque bursts", "11.50° → 6.65° (−42.2%)"),
                 ("CF2 burst rerun", "−50.2%"), ("Hardstep at ρ = 3", "error +17.0% (X2), +1.3% (CF2)")],
        qa=[
            ("A tuned PD with feedforward alone beats CMG on the fixed PD. So why not just tune the PD?", "Yes, it does, and that is exactly why we show the whole ladder. The claim is that the residual improves each baseline: 36% on the tuned X2, 6.5% on the tuned CF2. It complements tuning; it does not replace it."),
            ("Isn’t this just extra proportional gain?", "In the tested regime the gates latch open, and PES behaves like a lagged proportional correction with a corner near 9.6 rad/s. We say that in the paper. What the architecture adds is that the correction is learned online, bounded, and removable."),
            ("Why does Hardstep get worse?", "Hardstep commands 63–111° steps every 2 s; 97–99% of its mean error is unavoidable slew. At ρ = 3 the loop passes the PES corner, so the lagged residual comes out of phase. Scored by settling time to a 5° band, the residual helps at the canonical bandwidth (X2 −31%, CF2 −42%); that is internal analysis, not in the 8-page paper."),
            ("Why the geometric mean?", "The arithmetic mean is dominated by Hardstep, whose errors are much larger. The geometric mean weights each mission equally."),
            ("Does it help model-based controllers like LQR, backstepping or MPC?", "We checked outside the paper. With accurate or moderately wrong models (inertia 0.6× to 1.6×), it does not help LQR, backstepping, MPC or NMPC. It gives +5–8% on backstepping under an unmodeled disturbance. It helps model-free baselines most, which fits its PD-like teaching signal."),
            ("Is the noise model calibrated?", "No. Two synthetic levels (0.010 and 0.020 rad, plus rate noise), two seeds each, and the error is computed from the noisy quaternion, so it includes the noise floor. We say so in the paper."),
            ("Any hardware?", "Not in this paper; it is MuJoCo only. Separately, the Nengo CMG–PES ran on the 3-DOF Hover: Roll +2.7 ± 1.1% over three pairs, other missions mixed. Hardware validation is future work for this paper."),
        ],
        avoid=["“Beats model-based controllers.”", "Quoting the 17–60% range without saying it is against the fixed PD.", "Hiding the Hardstep regression."],
    ),
    # ------------------------------------------------------------------ 3
    dict(
        n=3, title="ComRob 2026 | Neuromorphic Hexarotor Control", time="1:00",
        purpose="Report the accepted paper and its honest result: the SNN closely reproduces the classical loop, with higher error.",
        before="",
        speech=[
            "The second paper was accepted, with minor revisions, at ComRob 2026 in Mexico. It is a collaboration with Anel Olivares, Víctor Silva, Eduardo Espinoza, Juan Bustamante and Patricio Ordaz. [Optional: add one sentence on your part.]",
            "The idea is a fully neuromorphic closed loop for a coaxial hexarotor. Both the vehicle dynamics and the cascade controller run as recurrent spiking networks in Nengo, with the Neural Engineering Framework. One neural template covers all six subsystems: PID in the position loops and PD in the attitude loops.",
            "The table compares the spiking controller with the same controller in MATLAB/Simulink. The signals match very closely, with correlation above 0.999, and the RMS position error is below 5 centimeters. To be honest, the SNN has higher RMSE and ISE than the classical loop, because of finite ensembles and neuron saturation. The next steps are the full nonlinear model, disturbances, and neuromorphic hardware.",
        ],
        short="Accepted: plant and cascade controller both run as SNNs in Nengo; correlation > 0.999 with Simulink, RMS position error < 5 cm, higher RMSE than classical.",
        numbers=[("Correlation x / y / −z", "0.9993 / 0.9998 / 0.9992"), ("RMSE SNN x / y / z", "0.032 / 0.033 / 0.048 m"),
                 ("RMSE classical x / y / z", "0.008 / 0.013 / 0.019 m"), ("Network", "200 neurons per ensemble, τ = 0.1 s"),
                 ("Mission", "60 s: climb 3 m, +1 m in x, 1.5 m lateral step at 15 s")],
        qa=[
            ("Why is the SNN worse than the classical controller?", "Finite ensembles (200 neurons) add decoding error, LIF rates saturate for large inputs, and the 0.1 s synaptic filter adds lag. The goal was a faithful neuromorphic realization, not better performance."),
            ("Why simulate the plant with neurons too?", "To have a fully neuromorphic closed loop, where state evolution and control are computed in the same framework. It is a step toward running everything on neuromorphic hardware."),
            ("What did the minor revision ask for?", "More implementation detail for Simulink and Nengo, the derivative approximation, the RMSE/ISE and correlation metrics, a discussion of the NEF limits, and public code."),
            ("Does it run in real time on hardware?", "Not yet. It runs in Nengo on a CPU; deployment on neuromorphic hardware is future work."),
            ("How were the SNN gains chosen?", "Heuristically, by observing closed-loop performance (Table I). They differ from the classical gains because of the neural representation."),
        ],
        avoid=["“The SNN outperforms the classical controller.”", "“Runs on neuromorphic hardware.”"],
    ),
    # ------------------------------------------------------------------ 4
    dict(
        n=4, title="IEEE ToE | Experiential Learning & Digital Twins", time="1:30",
        purpose="Present the course paper: a clear, paired theory-to-twin gap and a model → twin → hardware student project.",
        before="",
        speech=[
            "The third paper is for IEEE Transactions on Education, with Hilda Contreras Aguirre, Hengameh Mirhajianmoghadam, Omar García Alcántara and Dr. García Carrillo. It is about our course EE 475/551, Control Systems Synthesis, in Spring 2026: 21 students, fully asynchronous.",
            "Students learn system identification, robust, optimal and nonlinear control, and they practice on QLabs digital twins that match the real Quanser hardware, here the Qube-Servo 3 and the Aero 2.",
            "The chart shows the main result. For the same students, we compare a theory lab with the digital-twin lab on the same topic. Theory scores are near 99 percent; digital-twin scores are around 81 percent. That is a gap of 17.4 points, every one of the 21 students shows it, and p is below 0.001. We read it as a theory-to-practice gap: implementation adds real demands. It does not mean the twins reduce learning.",
            "On the right is a student project on the Aero 2: the same PD and backstepping controllers go from the model, to the twin, to the hardware. Pitch transfers well; yaw gets harder at each step, and the twin already shows that difficulty. The MATLAB and Python versions agree within 0.65 degrees.",
        ],
        short="Same students: theory 98.8% vs digital-twin 81.4% (−17.4 pp, p < 0.001); Aero 2 controllers transfer model → twin → hardware.",
        numbers=[("Theory → twin (overall)", "98.81% → 81.37%, −17.44 pp"), ("95% bootstrap CI", "[11.6, 23.8] pp"),
                 ("Students lower", "21 / 21; Wilcoxon + Holm p < 0.001"),
                 ("Module pairs", "04–05: 17.90 · 06–07: 19.05 · 10–11: 15.38 pp"),
                 ("Survey", "13 of 21 responded (62%)"),
                 ("Aero 2 PD pitch / yaw RMSE", "8.97 → 8.68 → 8.03° / 19.09 → 24.47 → 26.07°"),
                 ("MATLAB vs Python", "≤ 0.65° (QLabs), ≤ 0.19° (hardware)")],
        qa=[
            ("Does the lower twin score mean digital twins are worse for learning?", "No. It is a paired, descriptive comparison of two different activities. The twin lab adds implementation demands: timing, noise, data and engineering decisions. The paper says clearly that it is not a causal claim."),
            ("Isn’t there a ceiling effect?", "Yes. Theory scores are close to 99%, so there is little room above. That is why we use paired non-parametric tests, medians and bootstrap confidence intervals."),
            ("Why Wilcoxon and Holm?", "The scores are paired, bounded and not normal, so Wilcoxon signed-rank fits. We have three comparisons, so Holm controls the family-wise error."),
            ("What about ethics and student data?", "All records and survey answers were de-identified, and quotations are anonymous. [Confirm the exact IRB wording with Hilda before submission.]"),
            ("Does this generalize?", "It is one course, one semester, n = 21, and no control group; we say so. Next come more offerings and institutions, a common assessment, and open-source twins."),
            ("Why does yaw degrade on hardware?", "Actuator authority, stiction, model mismatch, propeller asymmetry, sampling and filtering. The twin already shows a larger yaw error, which is the point: the twin is a useful intermediate step."),
        ],
        avoid=["“Digital twins reduce learning” or “digital twins cause better learning” (no causal claim).", "Generalizing beyond one course."],
    ),
    # ------------------------------------------------------------------ 5
    dict(
        n=5, title="Research Lines | What Is Verified vs. Planned", time="0:45",
        purpose="Give the map of the six lines and set the rule: evidence levels are never merged.",
        before="(After your “Research” slide) Now the research lines. First, one slide as a map.",
        speech=[
            "This is the map of the six lines. For each one I show what is verified today, the strongest evidence we have, and the next milestone.",
            "The labels matter. Gray-blue means verified software, sand means digital twin, crimson means a logged hardware run, and dashed means proposed. I keep them separate on every slide, so a simulation result is never presented as a hardware result.",
            "In short: HyperLIF and DILISIC are verified in software; the Quanser platforms and the QCar already have hardware runs; the omnicopter and the satellite are digital twins; and the QCar fusion and the gyroscope are still plans.",
        ],
        short="Six lines; each labeled software, twin, hardware or proposed.",
        numbers=[("Legend", "software · twin · hardware · proposed"), ("Verified means", "saved result or passing tests")],
        qa=[
            ("Six lines is a lot. What is your priority?", "This semester: first the ACC submission, second the HyperLIF Julia runs on the HPC, third the QCar baseline with Grafton, fourth the omnicopter identification with Diego and Fabian. DILISIC/QArm and the gyroscope are gated behind identification and shadow-mode steps. All lines share one controller contract and one residual architecture, so the work transfers."),
            ("What exactly does “verified” mean?", "A reproducible saved result or a passing test suite. “Hardware” means a logged physical run."),
        ],
        avoid=["Mixing the labels, e.g., calling a twin result a hardware result."],
    ),
    # ------------------------------------------------------------------ 6
    dict(
        n=6, title="HyperLIF | Python Results Reproduced in Julia", time="1:30",
        purpose="Show the Python results and exactly which of them are reproduced in Julia; set up the HPC next step.",
        before="",
        speech=[
            "Line one is HyperLIF, our neuron. HyperLIF replaces the hard reset of the LIF neuron with a continuous reset controlled by a fast gate. That gate becomes a state we can read.",
            "The chart shows the Python results in PyTorch, with five seeds. HyperLIF improves most on temporal data. For example, SHD goes from 48 to 64 percent, and the gain almost disappears on N-MNIST, which is nearly static. To be fair, ALIF is a strong competitor on SHD, so we present HyperLIF as a different mechanism, not a universal winner.",
            "On the right is the Julia replication, in four steps. One: the neuron in PyTorch matches our validated NumPy and Nengo reference to below ten to the minus nine. Two: with the same weights, Julia reproduces the PyTorch forward pass for dense, recurrent and delay networks. Three: native Julia training on the same SHD data reproduces the direction of the result, HyperLIF above LIF, with a different pipeline and within the seed spread. Four: a new Julia learning package with three learning modes and one hundred tests, ready for the HPC.",
            "The next step is to run it on the NMSU cluster, first a screening run and then the five-seed runs.",
        ],
        short="PyTorch: HyperLIF gains most on temporal data; Julia reproduces the neuron, the forward pass, and the direction of the SHD result; HPC runs next.",
        numbers=[("SHD (LIF / HyperLIF / Adaptive)", "48.4 / 63.7 / 58.1%"), ("DVS-32", "69.8 / 81.8 / 79.0%"),
                 ("N-MNIST", "89.5 / 90.8 / 90.4%"), ("ALIF vs HyperLIF (SHD FF shortlist)", "55.7% vs 54.8%"),
                 ("Neuron parity", "< 10^{-9}"), ("Forward parity (shared weights)", "≤ 1.05×10^{-5} (HyperLIF)"),
                 ("Native Julia SHD, 5 seeds", "LIF 24.1 ± 7.8% vs HyperLIF 24.9 ± 6.7%"),
                 ("Julia tests", "100 (learning); portable 16/16 re-run this week")],
        qa=[
            ("What is HyperLIF exactly?", "A LIF neuron whose reset is continuous: a fast gate r opens near threshold and increases a reset conductance G = g·r², which pulls the voltage down smoothly. The gate is a readable state; LIF has no equivalent."),
            ("Why is the Julia accuracy 25% when PyTorch reaches 64%?", "It is a different pipeline: a native dense Julia/APEX model, 10 epochs, with the gate feedback calibrated. It is not the same architecture. The claim is parity of the model (forward pass) and of the direction of the learning result. Accuracy parity comes from the new package on the HPC."),
            ("Why Julia at all?", "One language for neuron, learning and control. It is fast on CPU and GPU, calls the Quanser HIL library directly, and runs well on HPC. It is also an independent re-implementation, which catches errors."),
            ("Does HyperLIF save energy?", "We do not claim that. Older “spike counts” were threshold occupancy, not events; we now log true upward crossings separately. Energy needs measured hardware power."),
            ("Is HyperLIF better than ALIF?", "Not universally. ALIF slightly leads the feed-forward and delay SHD shortlists; HyperLIF leads the recurrent one. Its unique value is the decodable gate state."),
            ("When will the HPC runs be done?", "The package and SLURM scripts are ready. Next is submitting the screening profile (27 runs per dataset), then the 5-seed, 40-epoch profile. I don’t want to promise a date before the first jobs run."),
        ],
        avoid=["“Julia reproduces the PyTorch accuracy.”", "“HyperLIF beats ALIF.”", "Energy claims."],
    ),
    # ------------------------------------------------------------------ 7
    dict(
        n=7, title="Quanser Platforms | Julia in the Loop on Digital Twins", time="1:30",
        purpose="Show the common pipeline, the Julia results on the twins, and the hardware results from the Python stack.",
        before="",
        speech=[
            "Line two is the Quanser platforms. Every robot follows the same pipeline: system identification, then model-based controllers, then a model-free or neuromorphic residual. And every controller runs offline, on the QLabs twin, and on hardware, with the same code contract.",
            "The new part is Julia. Julia talks directly to the Quanser HIL library, with no Python in the loop. The plot is a real run on the Qube-Servo 3 twin: energy swing-up, then the LQR catches the pendulum at 4 seconds and holds it, with the loop at 500 hertz. We also closed a PD loop on the Aero 2 twin at 200 hertz, and the 3-DOF Hover bridge passes all 103 checks without opening the device.",
            "The bottom table is hardware, with the Python stack. On the Qube, the gate residual is about as accurate as an always-on residual, but it is active only 4.4 percent of the time. On the Aero 2, PD tracks pitch better on hardware than on the twin. On the Hover, CMG–PES beats PD on the roll mission by 2.7 percent over three pairs; the other missions are mixed. Julia on hardware is the next step.",
        ],
        short="Same pipeline on every robot; Julia now closes loops on the Qube (500 Hz) and Aero 2 (200 Hz) twins; hardware results so far come from Python.",
        numbers=[("Qube twin (Julia)", "499.98 Hz, catch 4.03 s, hold 15.97 s, α RMS 1.24° (final 2 s)"),
                 ("Aero 2 twin (Julia)", "199.8 Hz, pitch RMS 0.048 rad"), ("Hover bridge / registry", "103/103 tests · 15 boards"),
                 ("Qube hardware gate ±0.20 V", "0.775 ± 0.161°, 4.4% active (always-on 70.4%)"),
                 ("Aero 2 hardware PD", "pitch RMS 0.084 rad (twin 0.150)"),
                 ("Hover Roll, 3 pairs", "+2.65 ± 1.08%; Full3 −3.21% (1 pair)")],
        qa=[
            ("Did Julia match Python on the same task?", "Not as a matched experiment yet. Both run at their target rates on the twins. The next step is a matched Python-vs-Julia run with the same gains, scene and metrics."),
            ("Why not run Julia on the hardware already?", "We follow the same safety ladder as with Python: sensor-only, then shadow, then low authority. Technically it is only a change of card identifier."),
            ("Is the Qube hardware residual the same as the ACC one?", "No. The June hardware block used an earlier gate blend. The canonical ACC gate has only run on the Qube twin. I keep them separate."),
            ("The Hover gain is small. Is it meaningful?", "Roll is repeatable over three pairs (+2.65 ± 1.08%), but it is small and depends on the mission; the other missions are single pairs and mixed. I present it as preliminary hardware evidence."),
            ("Why do the twin and the hardware differ on the Aero 2?", "Yaw authority depends on the operating point (stiction; props must be at hover), and the twin configuration must match the model (half-rotor vs 2-DOF helicopter). The twin is slightly conservative in pitch."),
            ("Where is system identification in Julia?", "Identification runs today in Python and MATLAB, and it is also in the course. Julia identification is on this semester’s list."),
        ],
        avoid=["“Julia runs on the hardware.”", "“The Qube hardware used the ACC gate.”", "“The Hover improves on all missions.”"],
    ),
    # ------------------------------------------------------------------ 8
    dict(
        n=8, title="Omnicopter | MuJoCo Twin & Neuromorphic Control", time="1:30",
        purpose="Present the twin methodology, the frozen result (PD nominal vs CMG–PES under disturbance/mismatch), and the collaboration.",
        before="",
        speech=[
            "Line three is the omnicopter, in collaboration with Diego and Fabian. It is a fully actuated vehicle: eight reversible rotors on the diagonals of a cube, so it can control force and torque independently.",
            "On the left is the twin methodology. We start from the CAD file, fix the eight rotor frames from the real vehicle, build the six-by-eight wrench map, which has full rank, and allocate with bounds. The baseline is a geometric PD with feedforward, and on top we add the same CMG–PES residual from the ACC paper, now with twelve units and six channels. The Nengo version matches the direct version to ten to the minus seven newtons.",
            "The table on the right shows the results. With the exact model, PD is better at nominal tracking. After an impulse, CMG–PES reduces the position error by 42 to 48 percent. And with model mismatch in mass, inertia, motors and external force, it reduces the position error by 55 percent and the attitude error by 27 percent, in all nine paired runs.",
            "So the frozen conclusion is: PD for nominal tracking, CMG–PES for disturbances and uncertainty. Next, with Diego and Fabian, we measure the real parameters and start the hardware test card.",
        ],
        short="Twin built from CAD with verified rotor frames; PD wins nominal, CMG–PES wins after impulses (−42 to −48%) and under mismatch (−55% position, 9/9).",
        numbers=[("Nominal (25 missions) PD vs CMG", "1.03 mm, 0.026° vs 11.6 mm, 0.063°"),
                 ("After impulse (position / attitude)", "−41.7% / −33.6% and −47.8% / −33.1%"),
                 ("Held-out mismatch", "0.218 → 0.098 m (−55.0%), 4.67 → 3.43° (−26.6%), 9/9"),
                 ("Direct vs Nengo", "≤ 1.1×10^{-7} N"), ("Architecture", "8 rotors, ±10 N, 12 CMG units, 6 channels, 500 Hz")],
        qa=[
            ("Why is PD better in the nominal case?", "The plant is the exact model, so PD with feedforward is nearly perfect. The canonical CMG units also start with a transient, because they are driven by the gravity-compensating wrench. The revised version centers the inputs at equilibrium, so the residual is exactly zero when the error is zero."),
            ("Is this a real digital twin?", "Not a predictive one yet. Geometry and rotor frames are confirmed, but mass, inertia, thrust maps and aerodynamics are not identified, and they stay empty until we measure them. It is a controller-development twin."),
            ("It needs negative thrust. Is that realistic?", "The design needs reversible propulsion. We still have to measure the bidirectional thrust maps, the deadband and the ±10 N bounds on the bench."),
            ("Did more neurons help?", "No. 12, 48 and 192 units gave almost the same results. Saturation and missing motor states matter more."),
            ("Is 9 out of 9 significant?", "It is three held-out seeds times three missions: a consistent trend, not a statistical claim. The plan is 30 development and 30 held-out seeds."),
            ("What does each collaborator do?", "[Fill in: Diego …; Fabian … — Fabian authored the omnicopter mechatronic-design paper.]"),
        ],
        avoid=["“Predictive twin” or “flight-ready.”", "“CMG–PES is better in all cases” (PD wins nominal)."],
    ),
    # ------------------------------------------------------------------ 9
    dict(
        n=9, title="DILISIC | Replicated; Next: QArm, QArm Mini & Haptic", time="1:15",
        purpose="Show the verified replication, raise the math points politely, and explain what must change before the arms move.",
        before="",
        speech=[
            "Line four is DILISIC, the double-integrator limbic-system-inspired controller by Rubio Scola, Dr. García Carrillo and Hespanha. Each agent gets a learning layer that makes it behave like a double integrator, so standard consensus control can be used with uncertain, high-order agents.",
            "We replicated the paper’s seven-agent flexible-arm experiment in Python. The plot shows the seven arms, the center of mass following the reference, and the disturbance at 70 seconds. All eleven summary metrics reproduce to ten to the minus six; I re-ran it this week. The part that is not exact yet is the obstacle and flocking law in the Appendix. During the replication we also noted four points that I would like to confirm with the authors: the sign convention of the error, one term in the Lyapunov derivative, the positivity of the inverse-gain estimate, and the norm in one projection.",
            "On the right is what we must adapt before the arms move. The paper assumes the input enters the highest derivative, but the QArm exposes position servos. So first we identify the servo loop and use DILISIC as an outer loop. We also need a derivative observer, joint- or task-space agents, and the haptic device as the human leader. Everything starts in shadow mode.",
        ],
        short="DILISIC replicated (11/11 metrics at 10^{-6}); on the arms it becomes an outer loop around identified position servos, starting in shadow mode.",
        numbers=[("Replication", "7 agents, 80 s, 11/11 metrics at 10^{-6}"), ("Final CoM error", "9.5×10^{-5} rad"),
                 ("Tests", "11/11 pass (re-run this week)"), ("Plant / basis", "4th-order flexible arm; p = 45 RBF"),
                 ("Disturbance", "70–75 s")],
        qa=[
            ("What does “limbic-inspired” mean here?", "The learning estimator imitates the amygdala / orbitofrontal emotional-learning loop: RBF networks estimate the unknown dynamics f and the inverse gain h, with projection-bounded updates and a robust Riccati term."),
            ("Why replicate before going to hardware?", "To have a reference implementation we trust. Then any difference on hardware comes from the plant, not from the code."),
            ("What are the four points exactly?", "(1) Section III uses e = x − x_d while Eq. (30) prints x_d − x; we used Section III. (2) Eq. (21) treats 1/ĥ* as constant although it depends on the state; that is fine if its derivative is bounded, and we would like to confirm. (3) ĥ* > 0 needs a lower bound; we use a positive floor. (4) The projection in Eq. (25) probably needs ‖W_f‖ in the denominator."),
            ("Why not apply it directly to the QArm?", "The QArm smart servos take position commands, not a torque at the highest derivative, so a direct application breaks the paper’s assumptions. We identify the servo loop and use DILISIC as an outer loop, first in shadow mode."),
            ("What is the role of the haptic device?", "The human operator becomes the leader of the multi-arm team; stability then needs passivity or virtual coupling in the loop."),
        ],
        avoid=["“The paper is wrong” — say “points to confirm with the authors.”", "“It works on the QArm” (not actuated yet)."],
    ),
    # ------------------------------------------------------------------ 10
    dict(
        n=10, title="QCar | Neuromorphic Sensor Fusion & Control", time="1:30",
        purpose="Present what exists, the three-phase plan with Grafton, and the one research question the benchmark answers.",
        before="",
        speech=[
            "Line five is the QCar, where I will work with Grafton on neuromorphic sensor fusion and control.",
            "What we have today, on the left: a runner on the car’s own Jetson with seven controllers (PID, SMC, an image-based NMPC, a HyperLIF gate, and three gated residual versions), tested at low speed. We also have a ROS 2 EKF that fuses wheel speed, IMU and LiDAR odometry.",
            "The plan has three phases. Phase A uses everything Quanser gives us (cameras, LiDAR, IMU, encoders) with a synchronized EKF and a kinematic-bicycle MPC with hard constraints and a safety filter. This is our strong baseline. Phase B adds the neuromorphic layer: the CMG–PES residual on the MPC command, as in the ACC paper, and HyperLIF or CMG populations that encode the sensor streams and the EKF innovations. The command is always projected into a safe set. Phase C is the benchmark: no residual, ANN, SNN and RL, with the same inputs and bounds, in nominal and degraded conditions, measuring safety, tracking, latency and real energy.",
            "On the right is Grafton’s first month. And the question we want to answer is at the bottom: do the temporal states of the neurons really help, compared with a memoryless network?",
        ],
        short="Hardware lane following exists; plan: Quanser-native MPC baseline → HyperLIF/CMG fusion + residual → matched ANN/SNN/RL benchmark with Grafton.",
        numbers=[("Controllers on the car", "7 (low-speed tests)"), ("Earlier benchmark (legacy code)", "lane-error RMS 0.126 → 0.112, 5.9% steering saturation"),
                 ("Benchmark design", "≥ 5 trials per cell; safety, tracking, latency, J/route"),
                 ("Grafton plan", "W1 logging · W2 offline baselines · W3 fusion evaluator · W4 low-speed runs")],
        qa=[
            ("Why MPC first, and not the SNN directly?", "A fair test needs a strong, constraint-aware baseline that uses Quanser’s full stack. Then any gain from the SNN is real, not the result of a weak baseline."),
            ("HyperLIF or CMG, which one?", "Both, with the same inputs and bounds. CMG–PES is proven as a residual (ACC, omnicopter); HyperLIF gives decodable gate states for fusion. The benchmark decides."),
            ("How would temporal features help fusion?", "They keep a short memory of the sensor streams and innovations, for example to detect drift, dropout or wheel slip, which a memoryless ANN does not have. The ANN residual with the same inputs is our control for that hypothesis."),
            ("How will you measure energy?", "From the Jetson power rails or an external meter, as joules per route. We will not use spike counts or FLOPs as energy."),
            ("What is wrong with the current EKF?", "LiDAR odometry is labeled as GPS, the same heading is fused twice, there is no time alignment, and the process noise is fixed. We fix those before calling it validated fusion."),
            ("What is Grafton’s role?", "Reproducibility: signal dictionary, logging, offline tests, the fusion evaluator and result cards, through small reviewed pull requests. Safety sign-off stays with the senior team."),
        ],
        avoid=["“Neuromorphic fusion works” (it is a plan).", "Calling the image-state NMPC a full vehicle NMPC."],
    ),
    # ------------------------------------------------------------------ 11
    dict(
        n=11, title="Space Systems | Basilisk Twin & 3-DOF Gyroscope", time="1:15",
        purpose="Show the working satellite twin and the method that links Basilisk, a gimbal twin, and the physical gyroscope.",
        before="",
        speech=[
            "Line six is neuromorphic perception and control for space systems.",
            "On the left is what runs today: Basilisk, the spacecraft simulation framework, now with native MuJoCo dynamics. One satellite with three reaction wheels converges from an attitude error of 0.374 to about six times ten to the minus four in 600 seconds, and the wheel torque stays within its 0.2 newton-meter limit.",
            "On the right is the 3-DOF gyroscope. It is a spinning rotor inside two gimbals: when you apply torque to one gimbal, the other one moves through gyroscopic coupling. That is the control-moment-gyroscope principle that real spacecraft use. We have the model and the controller suite derived, but no hardware run yet.",
            "The method connects three pieces: the Basilisk mission, a MuJoCo twin of the gimbals, and the real gyroscope through QUARC or our Julia bridge. Perception uses encoders, IMU and camera with an event-driven spiking estimator; control uses a classical baseline plus the same bounded residual. The ladder: identify the gyroscope, validate its twin, then hardware-in-the-loop with Basilisk mission profiles, then compare ANN and SNN estimators, and later multiple spacecraft.",
        ],
        short="Basilisk–MuJoCo satellite converges in 600 s; plan: identify the gyroscope, validate a gimbal twin, then hardware-in-the-loop with Basilisk.",
        numbers=[("Satellite (600 s)", "MRP error 0.374 → 6.4×10^{-4}"), ("Rate error", "5.5×10^{-5} rad/s"),
                 ("Wheels", "|torque| ≤ 0.2 N·m, ≤ 2,945 rpm"), ("Tooling", "Basilisk 2.11.1 MJScene; Q8 channel map ready")],
        qa=[
            ("Why Basilisk?", "It is a standard astrodynamics framework with flight-software modules (navigation, guidance, MRP feedback, wheel allocation), and the version we use, 2.11.1, has native MuJoCo dynamics for wheels, gimbals and appendages."),
            ("What are MRPs?", "Modified Rodrigues Parameters: a three-parameter attitude representation used in Basilisk. With shadow-set switching it avoids singularities."),
            ("How does a lab gyroscope relate to a satellite?", "It is the lab version of a control-moment gyroscope, a real spacecraft actuator based on momentum exchange through gimbals. We can test perception and control on real momentum-exchange physics."),
            ("What is the neuromorphic part here?", "An event-driven SNN estimator for perception, compared with an ANN on the same data, and the same bounded residual on the classical controller."),
            ("When will the gyroscope run?", "Identification and the gimbal twin this semester; hardware-in-the-loop after that."),
        ],
        avoid=["“We control the gyroscope” (no hardware run yet).", "Mixing CMG (neuron) with control-moment gyroscope."],
    ),
    # ------------------------------------------------------------------ 12
    dict(
        n=12, title="Summary | Next Steps", time="0:45",
        purpose="Close with the one idea, the evidence level, and the priorities.",
        before="",
        speech=[
            "To close: one idea connects everything. We keep the classical controller as the anchor, add a small, bounded neuromorphic correction, and move it from simulation, to digital twins, to hardware.",
            "We have one paper accepted and two near submission. In simulation, CMG–PES helps under disturbances and model mismatch; on hardware we have first positive but modest results. Julia now reproduces our Python results and drives the Quanser twins.",
            "The table shows the next steps for each line. The immediate priorities are the ACC submission, the Julia runs on the HPC, and starting the QCar work with Grafton. Thank you. I am happy to take questions.",
        ],
        short="Baseline + bounded neuromorphic residual, moved from simulation to twins to hardware; priorities: ACC, Julia/HPC, QCar.",
        numbers=[("Papers", "1 accepted, 2 near submission"), ("Hardware evidence", "Qube 4.4% active residual; Hover Roll +2.7%")],
        qa=[
            ("What is your main contribution?", "A neuromorphic residual architecture: keep the classical controller, add a bounded, online-learned neuron-based correction, and validate it along a ladder from simulation to twins to hardware, with explicit evidence labels."),
            ("Where is the neuromorphic advantage, if tuned classical control is as good?", "The advantage we see is adaptation to what the baseline does not model (disturbances and mismatch), with a bounded, removable correction. Energy advantages would need neuromorphic hardware and measured power; we do not claim them yet."),
        ],
        avoid=["“Neuromorphic beats classical.”"],
    ),
]

# ---------------------------------------------------------------- run of show
RUN_OF_SHOW = [
    ("Your title slide", "0:20", "Good evening. I’ll summarize our papers and the six research lines, and where each one stands."),
    ("Your “Papers” slide", "0:20", "We have three papers this semester. I’ll start with the most important one, the ACC paper."),
    ("New slides 1–4", "6:00", "ACC (2 slides), ComRob, ToE."),
    ("Your “Research” slide", "0:20", "Now the research lines. First, one slide as a map."),
    ("New slides 5–11", "9:15", "Map, then lines 1–6."),
    ("New slide 12", "0:45", "Summary and next steps."),
    ("Your “Platforms” / “Methodology” slides (optional)", "0:45", "Use only if time allows; they show the platform family behind the lines."),
    ("Your “My Passion” slide", "0:30", "Long term, all of this points to heterogeneous multi-agent systems: homes, agriculture, infrastructure and space."),
    ("Your “Thank you” slide", "—", "Thank you. I’m happy to take questions."),
]

# ---------------------------------------------------------------- cross-cutting Q&A
CROSS_QA = [
    ("Big picture", "What is the common thread across all these projects?",
     "One architecture and one method. The architecture: keep a classical controller as the anchor and add a bounded, online-learned neuromorphic correction. The method: move it from simulation to digital twins to hardware, with the same code contract and explicit evidence labels."),
    ("Big picture", "You have many platforms. Aren’t you spread too thin?",
     "The platforms share one controller contract, so the work transfers. I prioritize: ACC submission, then the Julia/HPC runs, then the QCar baseline with Grafton, then the omnicopter identification. DILISIC/QArm and the gyroscope wait behind their identification and shadow-mode gates."),
    ("Big picture", "What is novel compared with residual RL or adaptive control?",
     "The residual uses continuous neuron dynamics as a temporal basis and a local PES rule instead of backpropagation or a reward. It is bounded, so the baseline is recovered exactly at β = 0. We have not yet benchmarked it against L1 or MRAC; that is a fair next comparison."),
    ("Claims", "Where is the energy advantage of neuromorphic computing?",
     "We don’t claim one yet. Energy needs neuromorphic hardware and measured power. Our current claim is about adaptation and robustness, under stated conditions."),
    ("Claims", "Can you guarantee stability?",
     "Locally and conditionally: bounded states and weights, exact baseline recovery at β = 0, and local ISS for small β. At the β we use, stability is observed, not certified. We say that explicitly."),
    ("Claims", "How do you avoid overclaiming?",
     "Evidence labels on every slide, frozen results with checksums, selection rules declared before results, and re-running the checks: this week the Julia tests, the Hover bridge and the DILISIC replication all passed again."),
    ("Hardware", "How do you keep hardware experiments safe?",
     "A staged ladder: sensor-only, then shadow mode, then low authority with hard limits, watchdog and abort, with a person at the E-stop. The residual is bounded and can be switched off without touching the baseline."),
    ("Hardware", "Why is so much of this still in simulation?",
     "Simulation and twins let us debug and falsify ideas cheaply. The hardware we already have (Qube, Aero 2, Hover, QCar) follows the same code path, and each line has a concrete hardware gate as its next milestone."),
    ("Julia", "Why move to Julia if Python already works?",
     "Speed on CPU and GPU, direct calls to the Quanser HIL library without Python in the loop, HPC-friendly, and an independent re-implementation that catches errors. Python remains the reference where results were first produced."),
    ("Future", "What would convince you that the neuromorphic part is really necessary?",
     "The matched QCar benchmark: the same inputs and bounds for ANN, SNN and RL residuals. If the temporal states do not beat a memoryless residual, that is an important negative result, and we will report it."),
    ("Future", "How does this become a dissertation?",
     "One way to frame it: neuron (HyperLIF), then learning (PES and the Julia learning package), then control (the bounded residual), then platforms (UAVs, ground vehicles, space). The ACC paper is the control core."),
]

RECOVERY = [
    ("You don’t know the answer", "“That’s a good question. I don’t want to guess the number; I’ll check the source file and send it to you after the meeting.”"),
    ("They push on a weak result", "“You’re right, that result is modest. What I can claim is ___ under ___ conditions, and the next test that would settle it is ___.”"),
    ("They propose a new experiment", "“That’s a useful test. I’ll add it to the next steps; it fits in the ___ line.”"),
    ("You run out of time", "Skip to slide 12 and say: “The table shows the next step for each line; I’m happy to go back to any of them in the questions.”"),
    ("Someone mixes up CMG", "“Just to be clear: in our neuron, CMG means coupled membrane–gate, not control-moment gyroscope.”"),
]

GLOSSARY = [
    ("PES", "Prescribed Error Sensitivity: local, error-driven learning rule for decoder weights (Nengo/NEF)."),
    ("CMG (neuron)", "Coupled membrane–gate unit: continuous membrane + gate; not a control-moment gyroscope."),
    ("HyperLIF", "LIF neuron with a continuous, gate-controlled reset; the gate is a readable state."),
    ("LIF / ALIF", "Leaky integrate-and-fire / adaptive-threshold LIF (a strong baseline)."),
    ("NEF / Nengo", "Neural Engineering Framework / the Python simulator that implements it."),
    ("Residual (β, ℓ)", "Correction added to the baseline; bounded by β·ℓ; β = 0 recovers the baseline."),
    ("ρ (ACC)", "Bandwidth scale of the PD baseline (ρ = 3 is the tuned rung). In ComRob, ρ is a correlation."),
    ("ISS", "Input-to-state stability: bounded disturbance gives bounded error."),
    ("Geometric mean", "Mean of logs across missions; stops one large mission (Hardstep) from dominating."),
    ("QLabs / QUARC / HIL", "Quanser digital twins / real-time control software / hardware-in-the-loop library."),
    ("EKF / NIS", "Extended Kalman filter / normalized innovation squared (a filter-consistency test)."),
    ("MPC / NMPC", "(Nonlinear) model predictive control."),
    ("MRP", "Modified Rodrigues Parameters, the attitude coordinates used in Basilisk."),
    ("Basilisk / MJScene", "Spacecraft simulation framework / its native MuJoCo dynamics object."),
    ("DILISIC / LISIC", "Double-integrator limbic-system-inspired control (Rubio Scola, García Carrillo, Hespanha)."),
    ("SHD / SSC / DVS / N-MNIST", "Spiking audio (Heidelberg digits, speech commands), event-camera gestures, and neuromorphic MNIST datasets."),
]

# --------------------------------------------------------------- helpers
_SUP = str.maketrans("0123456789-+", "⁰¹²³⁴⁵⁶⁷⁸⁹⁻⁺")


def to_unicode(s):
    """Convert 10^{-6} markers into Unicode superscripts (for pptx notes)."""
    out, i = [], 0
    while i < len(s):
        j = s.find("^{", i)
        if j < 0:
            out.append(s[i:])
            break
        k = s.find("}", j)
        out.append(s[i:j])
        out.append(s[j + 2:k].translate(_SUP))
        i = k + 1
    return "".join(out)


def notes_text(sl):
    """Speaker-notes version: script + short Q&A + numbers, plain text."""
    lines = [f"SAY (about {sl['time']} min)"]
    if sl.get("before"):
        lines.append("Lead-in: " + sl["before"])
    lines += [""] + [to_unicode(p) for p in sl["speech"]]
    lines += ["", "IF THEY ASK"]
    for q, a in sl["qa"][:4]:
        lines.append(f"• {to_unicode(q)} → {to_unicode(a)}")
    lines += ["", "KEY NUMBERS: " + "; ".join(f"{k}: {to_unicode(v)}" for k, v in sl["numbers"])]
    lines += ["DON'T SAY: " + " ".join(to_unicode(x) for x in sl["avoid"])]
    return "\n".join(lines)
