"""Generate a broad, staged tuning matrix for HyperLIF Nengo experiments.

This is a setup artifact, not a benchmark. It writes a deliberately ambitious
candidate matrix that combines the practical readout threshold theta_event=0.95
with origin, origin-aware calibration, adaptive reset gain, gate-shape changes,
decoder/state ablations, and a few out-of-the-box ideas worth testing.

The matrix is meant to be consumed in stages. Nothing here changes the validated
core neuron claims; rows marked ``local_subclass`` or ``new_decoder`` require a
separate exploratory implementation before they can be treated as evidence.
"""

from __future__ import annotations

from dataclasses import dataclass, fields

from _common import CSV_DIR, ensure_results, write_log
from simulation.metrics import write_rows


@dataclass(frozen=True)
class Candidate:
    candidate_id: str
    stage: str
    priority: int
    candidate: str
    family: str
    theta_event: str
    origin_policy: str
    v_reset: str = ""
    min_voltage: str = ""
    delta_reset: str = ""
    rate_to_current: str = ""
    reset_gain: str = ""
    base_gain: str = ""
    gain_scaling: str = ""
    alpha: str = ""
    tau_r: str = ""
    gamma: str = ""
    ensemble_max_rates: str = ""
    ensemble_intercepts: str = ""
    synapse: str = ""
    decoder_features: str = ""
    apps_first: str = ""
    implementation: str = "core_params"
    hypothesis: str = ""
    risk: str = ""
    decision_rule: str = ""


def row(**kwargs: object) -> Candidate:
    defaults = {
        "v_reset": "",
        "min_voltage": "",
        "delta_reset": "",
        "rate_to_current": "80",
        "reset_gain": "",
        "base_gain": "",
        "gain_scaling": "",
        "alpha": "100",
        "tau_r": "0.002",
        "gamma": "0.2",
        "ensemble_max_rates": "40..120",
        "ensemble_intercepts": "-0.5..0.5",
        "synapse": "0.02",
        "decoder_features": "decoded_output",
        "apps_first": "communication,function,transform,memory,oscillator,pes",
        "implementation": "core_params",
        "hypothesis": "",
        "risk": "",
        "decision_rule": "",
    }
    defaults.update(kwargs)
    return Candidate(**defaults)


def build_candidates() -> list[Candidate]:
    rows: list[Candidate] = []

    def add(**kwargs: object) -> None:
        rows.append(row(candidate_id=f"T{len(rows) + 1:03d}", **kwargs))

    # Stage 0: anchors and sanity checks. These define the comparison floor.
    add(
        stage="0_anchor",
        priority=1,
        candidate="LIF native reference",
        family="lif",
        theta_event="native",
        origin_policy="none",
        rate_to_current="native",
        alpha="",
        tau_r="",
        gamma="",
        hypothesis="Keep native LIF as the accuracy and recurrent-stability reference.",
        risk="None; this is the anchor.",
        decision_rule="Every tuning win must be compared against this row.",
    )
    for family in ("hyperlif", "adaptive"):
        for theta in ("1.00", "0.95"):
            add(
                stage="0_anchor",
                priority=1,
                candidate=f"{family} theta {theta}",
                family=family,
                theta_event=theta,
                origin_policy="none",
                base_gain="20" if family == "adaptive" else "",
                gain_scaling="80" if family == "adaptive" else "",
                reset_gain="100" if family == "hyperlif" else "",
                hypothesis="Separate pure theta_event effects from origin and calibration effects.",
                risk="Known: theta_event improves event availability but not uniformly RMSE.",
                decision_rule="Keep theta 0.95 as default only if it improves event availability without destabilizing recurrent apps.",
            )
    for family in ("hyperlif", "adaptive"):
        add(
            stage="0_anchor",
            priority=1,
            candidate=f"{family} theta 0.95 static origin current baseline",
            family=family,
            theta_event="0.95",
            origin_policy="static_v_reset",
            v_reset="-0.6",
            min_voltage="-2.0",
            base_gain="20" if family == "adaptive" else "",
            gain_scaling="80" if family == "adaptive" else "",
            reset_gain="100" if family == "hyperlif" else "",
            hypothesis="Reproduce the current origin finding before expanding the sweep.",
            risk="Mixed result: communication/PES can improve while memory/transform/oscillator worsen.",
            decision_rule="Use as the reference origin row; do not call origin a win unless new rows dominate it.",
        )

    # Stage 1: robust origin + theta_event combinations.
    for family in ("hyperlif", "adaptive"):
        for v_reset, label in (("-0.3", "mild"), ("-0.6", "medium"), ("-0.9", "deep")):
            add(
                stage="1_origin_threshold",
                priority=1,
                candidate=f"{family} theta 0.95 {label} static origin",
                family=family,
                theta_event="0.95",
                origin_policy="static_v_reset",
                v_reset=v_reset,
                min_voltage="-2.0",
                base_gain="20" if family == "adaptive" else "",
                gain_scaling="80" if family == "adaptive" else "",
                reset_gain="100" if family == "hyperlif" else "",
                hypothesis="Find the origin depth that increases useful events without damaging recurrent state.",
                risk="Too-deep origin can amplify calibration mismatch or push decoded dynamics away from target.",
                decision_rule="Prefer rows that improve communication/PES while keeping transform and memory within 15% of theta 0.95.",
            )
        for theta in ("0.98", "0.92", "0.90"):
            add(
                stage="1_origin_threshold",
                priority=2,
                candidate=f"{family} theta {theta} with medium origin",
                family=family,
                theta_event=theta,
                origin_policy="static_v_reset",
                v_reset="-0.6",
                min_voltage="-2.0",
                base_gain="20" if family == "adaptive" else "",
                gain_scaling="80" if family == "adaptive" else "",
                reset_gain="100" if family == "hyperlif" else "",
                hypothesis="Test whether theta 0.95 is special or just one point on a dense/sparse trade curve.",
                risk="Lower theta can create extra events that do not carry useful decoded information.",
                decision_rule="Keep only theta values that improve event decoder or app RMSE, not raw event count alone.",
            )

    # Stage 2: origin-aware calibration. This directly attacks the current Nengo issue.
    for family in ("hyperlif", "adaptive"):
        for rate_to_current in ("40", "60", "100", "140"):
            add(
                stage="2_origin_aware_calibration",
                priority=1,
                candidate=f"{family} theta 0.95 origin rate_to_current {rate_to_current}",
                family=family,
                theta_event="0.95",
                origin_policy="static_v_reset",
                v_reset="-0.6",
                min_voltage="-2.0",
                rate_to_current=rate_to_current,
                base_gain="20" if family == "adaptive" else "",
                gain_scaling="80" if family == "adaptive" else "",
                reset_gain="100" if family == "hyperlif" else "",
                hypothesis="The origin problem may be a gain/rate fit problem, not a neuron-dynamics problem.",
                risk="Fast-readout proxy can overfit one app and break another.",
                decision_rule="Select by multi-app score: decoded RMSE average plus penalties for memory error and runaway oscillator amplitude.",
            )
        for max_rates, intercepts, label in (
            ("20..80", "-0.8..0.2", "low-rate negative-intercept"),
            ("40..160", "-0.7..0.3", "wide-rate negative-intercept"),
            ("80..200", "-0.3..0.7", "high-rate positive-intercept"),
        ):
            add(
                stage="2_origin_aware_calibration",
                priority=2,
                candidate=f"{family} theta 0.95 origin {label} ensemble",
                family=family,
                theta_event="0.95",
                origin_policy="static_v_reset",
                v_reset="-0.6",
                min_voltage="-2.0",
                ensemble_max_rates=max_rates,
                ensemble_intercepts=intercepts,
                base_gain="20" if family == "adaptive" else "",
                gain_scaling="80" if family == "adaptive" else "",
                reset_gain="100" if family == "hyperlif" else "",
                hypothesis="Origin shifts tuning curves, so ensemble intercept/max-rate bands should move with it.",
                risk="Requires extending the app sweep to expose ensemble settings.",
                decision_rule="Keep if it improves transform and memory without losing the communication/PES origin gain.",
            )
        for synapse in ("0.01", "0.05", "0.10"):
            add(
                stage="2_origin_aware_calibration",
                priority=3,
                candidate=f"{family} theta 0.95 origin synapse {synapse}",
                family=family,
                theta_event="0.95",
                origin_policy="static_v_reset",
                v_reset="-0.6",
                min_voltage="-2.0",
                synapse=synapse,
                base_gain="20" if family == "adaptive" else "",
                gain_scaling="80" if family == "adaptive" else "",
                reset_gain="100" if family == "hyperlif" else "",
                hypothesis="Some origin failures may be decoder-filter mismatch rather than intrinsic instability.",
                risk="Long synapses can hide timing failures; short synapses can make sparse readout noisy.",
                decision_rule="Use only if app performance improves and event timing remains interpretable.",
            )

    # Stage 3: adaptive reset-gain placement.
    for base_gain, gain_scaling, label in (
        ("10", "40", "soft adaptive"),
        ("20", "40", "low beta"),
        ("20", "120", "high beta"),
        ("40", "80", "high base"),
        ("40", "120", "high base high beta"),
    ):
        for origin_policy, v_reset, min_voltage in (
            ("none", "", ""),
            ("static_v_reset", "-0.6", "-2.0"),
        ):
            add(
                stage="3_adaptive_gain",
                priority=2,
                candidate=f"adaptive theta 0.95 {label} {origin_policy}",
                family="adaptive",
                theta_event="0.95",
                origin_policy=origin_policy,
                v_reset=v_reset,
                min_voltage=min_voltage,
                base_gain=base_gain,
                gain_scaling=gain_scaling,
                hypothesis="Adaptive gain should be placed for recurrent app stability, not only DB avoidance.",
                risk="High beta can self-silence or distort memory; low beta can reintroduce high-drive latch risk.",
                decision_rule="Prefer rows that reduce oscillator blow-up and memory error without killing PES learning.",
            )

    # Stage 4: gate-shape variants. These are still core parameters, but claims
    # should remain parameter-family claims until seed/app sweeps support them.
    for family in ("hyperlif", "adaptive"):
        for alpha, tau_r, gamma, label in (
            ("60", "0.003", "0.15", "soft slow gate"),
            ("80", "0.004", "0.25", "wide hysteresis slow gate"),
            ("150", "0.001", "0.20", "sharp fast gate"),
            ("100", "0.002", "0.30", "strong hysteresis"),
            ("100", "0.002", "0.10", "weak hysteresis"),
        ):
            add(
                stage="4_gate_shape",
                priority=3,
                candidate=f"{family} theta 0.95 origin {label}",
                family=family,
                theta_event="0.95",
                origin_policy="static_v_reset",
                v_reset="-0.6",
                min_voltage="-2.0",
                alpha=alpha,
                tau_r=tau_r,
                gamma=gamma,
                base_gain="20" if family == "adaptive" else "",
                gain_scaling="80" if family == "adaptive" else "",
                reset_gain="100" if family == "hyperlif" else "",
                hypothesis="If recurrent apps fail from gate timing, reshape the detector before discarding origin.",
                risk="Changes model operating regime; must not be merged into reference claims prematurely.",
                decision_rule="Promote only if single-neuron F-I and Nengo app metrics both improve.",
            )

    # Stage 5: out-of-the-box ideas. These require experiment-local subclasses,
    # new decoders, or mixed-population app builders.
    for family in ("hyperlif", "adaptive"):
        for delta_reset in ("0.15", "0.30", "0.60"):
            add(
                stage="5_out_of_box",
                priority=2,
                candidate=f"{family} theta 0.95 gate-coupled origin delta_reset {delta_reset}",
                family=family,
                theta_event="0.95",
                origin_policy="gate_coupled_delta_reset",
                v_reset="0.0",
                min_voltage="-2.0",
                delta_reset=delta_reset,
                implementation="local_subclass",
                base_gain="20" if family == "adaptive" else "",
                gain_scaling="80" if family == "adaptive" else "",
                reset_gain="100" if family == "hyperlif" else "",
                hypothesis="Move the origin only when the gate opens, preserving baseline encoding but adding after-hyperpolarization.",
                risk="Not in the validated P3 Nengo class; needs parity and single-neuron checks before app claims.",
                decision_rule="Promote only if it recovers origin sparsity without the static-origin memory/transform penalty.",
            )

    out_of_box = [
        (
            "mixed population dense+sparse",
            "mixed_population",
            "0.95",
            "static_v_reset",
            "-0.6",
            "-2.0",
            "app_builder",
            "Use half theta-only neurons for communication and half origin neurons for sparse state memory.",
            "More moving parts; decoder may exploit population imbalance.",
            "Keep if mixed population dominates both pure theta and pure origin on at least four apps.",
        ),
        (
            "dual decoder spikes+gate",
            "adaptive",
            "0.95",
            "static_v_reset",
            "-0.6",
            "-2.0",
            "new_decoder",
            "Let spikes carry events while gate carries readiness, especially for recurrent memory and PES.",
            "Needs app-specific decoder plumbing; not comparable to spike-only NEF out of the box.",
            "Keep if gate/state ablation explains a real app improvement, not just a regression fit.",
        ),
        (
            "homeostatic theta tuned candidate",
            "adaptive",
            "adaptive_0.99_target60",
            "none",
            "",
            "",
            "local_subclass",
            "Import the tuned theta rule from project 05 to make better-timed events rather than more events.",
            "Adds theta_event state; needs parity for voltage/gate plus theta state.",
            "Keep if event-only and combined decoder improve in multi-neuron channels.",
        ),
        (
            "origin annealing",
            "adaptive",
            "0.95",
            "annealed_static_v_reset",
            "0.0_to_-0.6",
            "-2.0",
            "local_subclass",
            "Start dense to bootstrap recurrent state, then anneal origin for sparse steady operation.",
            "Time-varying neuron parameter complicates claims and reproducibility.",
            "Keep only for control/learning apps where transient bootstrap is explicit.",
        ),
        (
            "PES gate eligibility",
            "adaptive",
            "0.95",
            "static_v_reset",
            "-0.6",
            "-2.0",
            "new_learning_rule",
            "Use reset_gate as an eligibility/readiness modulator for PES-like updates.",
            "Learning-rule change, not just neuron tuning; belongs in a separate result section.",
            "Keep if late error improves and ablation shows gate factor is responsible.",
        ),
        (
            "task-routed neuron family",
            "mixed",
            "0.95",
            "static_v_reset",
            "-0.6",
            "-2.0",
            "app_builder",
            "Use HyperLIF for communication/PES and Adaptive for high-drive recurrent control.",
            "May look like hand-picked app specialization unless pre-registered.",
            "Use only after single-family sweeps identify stable family-specific strengths.",
        ),
        (
            "readiness residual output",
            "adaptive",
            "0.95",
            "static_v_reset",
            "-0.6",
            "-2.0",
            "new_decoder",
            "Decode a residual from voltage+gate+dynamic_gain and add it to the standard NEF output.",
            "Can overfit small apps; must use held-out stimuli/seeds.",
            "Keep if residual improves transform/control with seed-matched validation.",
        ),
        (
            "event bandpass readout",
            "hyperlif",
            "0.95_plus_gate_slope",
            "static_v_reset",
            "-0.6",
            "-2.0",
            "local_subclass",
            "Emit useful events only near upward voltage crossings with active gate motion.",
            "New event rule; can no longer be described as readout threshold only.",
            "Keep as speculative only unless it improves event usefulness and preserves parity of continuous state.",
        ),
    ]
    for name, family, theta, origin, v_reset, min_voltage, implementation, hypothesis, risk, decision in out_of_box:
        add(
            stage="5_out_of_box",
            priority=3,
            candidate=name,
            family=family,
            theta_event=theta,
            origin_policy=origin,
            v_reset=v_reset,
            min_voltage=min_voltage,
            implementation=implementation,
            base_gain="20" if family in ("adaptive", "mixed") else "",
            gain_scaling="80" if family in ("adaptive", "mixed") else "",
            reset_gain="100" if family in ("hyperlif", "mixed") else "",
            decoder_features="spikes,voltage,gate,dynamic_gain",
            apps_first="communication,memory,pes,control",
            hypothesis=hypothesis,
            risk=risk,
            decision_rule=decision,
        )

    return rows


def main() -> None:
    ensure_results()
    candidates = build_candidates()
    field_names = [field.name for field in fields(Candidate)]
    rows = [{name: getattr(candidate, name) for name in field_names} for candidate in candidates]
    csv_path = CSV_DIR / "11_full_tuning_candidate_matrix.csv"
    write_rows(csv_path, rows)

    by_stage: dict[str, int] = {}
    by_impl: dict[str, int] = {}
    for candidate in candidates:
        by_stage[candidate.stage] = by_stage.get(candidate.stage, 0) + 1
        by_impl[candidate.implementation] = by_impl.get(candidate.implementation, 0) + 1

    lines = [
        "Full HyperLIF/Nengo tuning setup",
        f"Candidates: {len(candidates)}",
        f"CSV: {csv_path}",
        "",
        "Stages:",
        *[f"- {stage}: {count}" for stage, count in sorted(by_stage.items())],
        "",
        "Implementation classes:",
        *[f"- {impl}: {count}" for impl, count in sorted(by_impl.items())],
        "",
        "Recommended execution order:",
        "1. Run all priority-1 rows from stages 0-2 on the existing six-app sweep.",
        "2. Add stage-3 adaptive-gain rows if memory/oscillator remain poor.",
        "3. Add stage-4 gate-shape rows only after single-neuron F-I sanity checks.",
        "4. Prototype stage-5 rows in separate experiment-local subclasses/decoders.",
        "",
        "Claim rule: a row is interesting only if it improves decoded metrics without",
        "hiding instability behind higher event count or longer synaptic smoothing.",
    ]
    write_log("11_full_tuning_setup.txt", "\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
