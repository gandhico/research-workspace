# Section II revision and Figure 1 audit - 2026-09-05

Scope: manuscript Section II only. No controller, model, experiment result, or original manuscript was modified. The manuscript inside the user's latest downloaded ZIP is preserved byte-for-byte under source/. This is a proposed replacement section, not a rewritten complete paper.

## What to use

- `section_II_revised.tex`: replacement Section II, retaining existing equation/section labels.
- `figure1_interface.tex`: editable TikZ replacement for Figure 1 (`fig:scale`).
- `model_references.bib`: eight primary-source bibliography entries covering MuJoCo, model provenance, and manufacturer comparisons.
- `section_II_review.tex`: standalone two-column review wrapper, not official ACC submission formatting.
- `compiled_model_characteristics.json`: diagnostic values from actual local compiled models.
- `inspect_models.py`: read-only model inspection; no dynamics or hardware is run. The output names `*_used` encode the intended main-comparison scales (CF2 1.5, X2 1), not a claim to have verified every historical run manifest.

## Recommended integration

1. Remove the old `fig:scale` figure environment from the introduction; otherwise its label is duplicated.
2. Replace only the existing Section II up to, but not including, Section III with `section_II_revised.tex` (or input that file).
3. Place `figure1_interface.tex` next to the root TeX file and add `\usepackage{tikz}` to its preamble.
4. Merge the new bibliography entries into the manuscript bibliography or append `model_references` to the existing `\bibliography{...}`.
5. Keep the existing Figure 2 photos/geometries for visual identification if space permits; Figure 1 now serves a different purpose: actuator signs, allocation, and feedback. Do not imply that photographs are hardware experiments on CF2/X2.
6. Compile twice after bibliography processing and check the full-paper float layout. The standalone review is intentionally more descriptive than a final page-limited ACC section. Retain the short characteristics table; the full X2 tensor and detailed physics limitations can move into reproducibility material if needed, but retain the tuning-vector distinction in the paper.

## Claim boundary: CF2 contribution

Updated after manufacturer comparison: "We extend the Menagerie CF2 model with an explicit four-rotor thrust-allocation interface and evaluate increased actuator authority at 1.5 times the upstream simulation thrust limit." The upstream README calls the limits arbitrary and in need of tuning. Therefore neither "nominal" nor "1.5x" denotes a calibrated stock-hardware thrust rating.

Do not call it a completed or hardware-validated CF2 model. The site geometry (92 mm diagonal) and reaction coefficient (0.005 m) are design assumptions. The modification preserves mass/inertia; it does not identify a stronger motor, increased mass, RPM, motor time constant, battery, power, or thermal behavior. A 1.5x force bound does not mean 1.5x rotor speed, power, torque in every feasible allocation, or tracking performance.

At 45 degrees of single-axis tilt, ideal constant-height collective demand is sqrt(2) Mg. The unscaled model's maximum collective is 1.321 Mg; the increased-authority model permits 1.982 Mg. This explains an imposed model headroom limitation, not a demonstrated stock-hardware limitation, closed-loop guarantee, or full description of the Hard45 reference.

## Manufacturer comparison incorporated in Section II

The revised chapter now includes a second, explicitly manufacturer-referenced table; the model table and Figure 1 caption distinguish simulation authority from hardware ratings. Bitcraze's historical power-supply test reports 57.9 gram-force at 93.75% PWM (approximately 0.567805 N). Our 0.525 N bound is about 7.54% below this measured point, not evidence of 50% stronger-than-stock propulsion. This is not a guaranteed continuous battery-powered thrust rating. The 2015 motor response (~180 ms from zero to 25,000 RPM) is a measured transient, not a first-order time constant; our models omit it. Product-specification masses match, while X2 thrust/inertia/reaction coefficients are not established by the reviewed manufacturer specifications. Rotor-center spacing is not the overall aircraft envelope. The original complete manuscript source remains untouched; its other chapters may still use "enhanced-propulsion" language and will need a separate consistency pass when integrating this Section II. Existing result filenames and labels were not renamed or altered.

An early 5 s Hard45 classical-controller authority sweep provides exploratory evidence: `results/validation/cf2_authority_sweep_5s/scale_1/classical/summary.json` reports mean quaternion error 1.630437 rad, versus 0.292720 rad at `scale_1.5/classical/summary.json`. Both use dt=0.0005 and the same reported torque limits. These are historical summaries, not newly reproduced runs or a full-mission statistical validation of a hardware upgrade. The large authority benefit is present without CMG and must not be counted as a neural benefit. A contemporary rerun with frozen identical gains, initialization, horizon, and disturbances is needed for a definitive 1x-versus-1.5x design comparison.

## New and consequential inertia finding

`run_mujoco_nef.py` reads `model.body_inertia[body_id]` and uses that vector directly in gain and torque-bound formulas. MuJoCo stores principal moments in the inertial frame, whose orientation relative to the body is `body_iquat`. CF2 has aligned frames; X2 does not. In particular, the physical X2 tensor has xz coupling -0.0021 kg m^2, and its body-axis diagonal is approximately (0.0366517, 0.0254117, 0.0605280), not the returned vector (0.0607113, 0.0364684, 0.0254117).

The revision therefore names the implemented array `j_tune` and reconstructs the physical tensor as R_BI diag(j_p) R_BI^T. No gain has been changed. This preserves the results' actual controller definition. The comparison remains against that fixed baseline, not an optimized PD controller. A future body-frame-inertia-based retuning is a distinct baseline experiment and must be reported as such, with both PD and CMG rerun. Existing improvements alone do not establish superiority over every properly retuned classical baseline.

The ideal energy identity remains restricted to scalar proportional gain, fixed reference, an unsaturated ideal plant, and a smooth sign branch. Adding passive/disturbance torque to the plant equation requires setting those terms to zero explicitly in that identity's assumptions.

## Figure 1 corrections

The source figure has body axes, force arrows, and Omega labels, rather than just unannotated geometries. It is not enough to use its caption as an actuator specification. Its pictorial numbering has not been validated against the source site's order. The replacement top-down diagram uses the actual order: 1=(-x,-y), 2=(-x,+y), 3=(+x,+y), 4=(+x,-y), with kappa signs (-,+,-,+). It deliberately avoids rotation-speed arrows because these actuators do not simulate motor RPM states. The two drawings are independently scaled and explicitly not a size comparison.

The bottom interface is a high-level schematic; the detailed CMG state and learning internals remain in Section III. Signal flow is reference/state -> PD (optionally CMG) -> requested torque; independent height loop -> T; inverse mixer -> nonnegative force clipping -> MuJoCo site wrenches -> simulator-state feedback. Requested torque, clipped motor force, and realized torque are three distinct signals. No arrow represents a hardware sensor or physical drone connection.

## Evidence map (paths relative to C:/Research/papers/ACC2027_Gate_Residual_Control)

| Description | Source | Relevant implementation |
|---|---|---|
| Latest paper basis | `paper/study/section_II_2026-09-05/source/ACC2027.tex` | Section II and old `fig:scale` |
| Model selection and interfaces | `src/gra_control/platforms/drone.py` | `SPECS`, `_free_joint` |
| Rotor ordering, arms, reaction signs | `src/gra_control/platforms/drone.py` | `_mixer`: [1; p_y; -p_x; gear_z] |
| Controller torque bounds | same | `torque_limits` |
| CF2 design assumptions | `models/cf2_rotor_design/README.md` | Preserved parameters and assumed rotor design |
| CF2 rotor dynamics/assets | `models/cf2_rotor_design/scene.xml` and its included XML | Rotor site force interface |
| Upstream CF2 | `third_party/mujoco_menagerie/bitcraze_crazyflie_2/scene.xml` and included XML | Collective plus abstract body moments |
| X2 model | `third_party/mujoco_menagerie/skydio_x2/scene.xml` and included XML | Four force actuators, inferred inertia |
| Nengo-runner gain mapping | `experiments/nengo_nef_replication_2026-08-29/run_mujoco_nef.py:159` | Principal moments read directly; gain construction at 164-165 |
| Force authority scaling | same, lines 183-188 | Upper ctrlrange scaled both locally and in model |
| Attitude and rate feedback | same, lines 218-219 | Conjugated qpos quaternion and rotational qvel |
| Collective, allocation, applied controls | same, lines 290-332 | Height loop, clipping, data.ctrl; optional disturbance xfrc |
| Plant advancement | same, line 426 | mj_step after control calculation and per-step logging |
| Direct implementation | `src/gra_control/platforms/drone.py` | Same principal-inertia gain convention in run_drone |
| Quaternion algebra | `src/gra_control/math3d.py` | quat_error, quat_angle, quaternion conventions |

## Physics boundaries to keep visible

- Six mechanical DOFs, not four independent mechanical rotor-speed DOFs.
- Both XML models enable air density/viscosity and default inertia-based fluid forces. Do not describe MuJoCo as supplying detailed propeller flow or CFD.
- CF2 uses RK4; X2 uses Euler. The runner sets h=0.0005 s, not a common integrator. These are rigid-body integration settings; do not conflate them with CMG's internal state-update rule or Nengo's own signal updates.
- Three virtual sensor definitions exist, but the tested controller reads simulator state. Optional runner noise does not equal a validated estimator/sensor stack.
- Four nonnegative algebraic site-force inputs are in newtons. Reaction coefficient units are meters. There is no actuator activation dynamics or motor-speed state in these compiled models.
- X2 mass/inertia are model values inferred from its geoms, not claimed manufacturer-identified parameters.

Primary references: https://github.com/google-deepmind/mujoco_menagerie ; https://mujoco.readthedocs.io/en/stable/XMLreference.html#body-inertial ; https://mujoco.readthedocs.io/en/3.1.1/computation/fluid.html .
