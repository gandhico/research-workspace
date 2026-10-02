"""Generate every LaTeX table from the canonical CSVs and parameter dataclasses.

Each table is written as a self-contained ``booktabs`` float (caption + label)
into ``paper/tables`` so the manuscript can ``\\input`` it directly. Numeric
tables are built from the experiment CSV files; the parameter table is built by
reflecting over the actual ``*Params`` dataclasses, so it cannot drift from the
implementation.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from neurons import AdaptiveHyperLIFParams, HyperLIFParams, LIFParams  # noqa: E402

CSV_DIR = PROJECT_ROOT / "results" / "csv"
OUT_DIR = PROJECT_ROOT / "paper" / "tables"


def load_rows(name: str) -> list[dict[str, str]]:
    with (CSV_DIR / name).open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def fnum(x: float, sig: int = 3) -> str:
    """Format a float for a table cell."""

    x = float(x)
    if x == 0.0:
        return "$0$"
    if abs(x) < 1e-3 or abs(x) >= 1e4:
        s = f"{x:.{sig}e}"
        mant, exp = s.split("e")
        return f"${mant}\\!\\times\\!10^{{{int(exp)}}}$"
    return f"{x:.{sig}g}"


def write(name: str, body: str) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / name).write_text(body, encoding="utf-8")
    print(f"wrote {name}")


# --------------------------------------------------------------------------- #
def tab_params() -> None:
    lif, h, a = LIFParams(), HyperLIFParams(), AdaptiveHyperLIFParams()
    dash = "--"

    def cell(val) -> str:
        if val is None:
            return dash
        if isinstance(val, float) and val.is_integer():
            return f"{val:g}"
        return f"{val:g}"

    rows = [
        ("Membrane time constant", r"$\tau$ (s)", lif.tau, h.tau, a.tau),
        ("Refractory period", r"$\tau_{\mathrm{ref}}$ (s)", lif.tau_ref, None, None),
        ("Resting potential", r"$v_{\mathrm{rest}}$", lif.v_rest, h.v_rest, a.v_rest),
        ("Reset potential", r"$v_{\mathrm{reset}}$", lif.v_reset, h.v_reset, a.v_reset),
        ("Threshold", r"$v_{\mathrm{thresh}}$", lif.v_thresh, h.v_thresh, a.v_thresh),
        ("Gate steepness", r"$\alpha$", None, h.alpha, a.alpha),
        ("Gate time constant", r"$\tau_r$ (s)", None, h.tau_r, a.tau_r),
        ("Hysteresis factor", r"$\gamma$", None, h.gamma, a.gamma),
        ("Fixed reset gain", r"$G_b$", None, h.reset_gain, None),
        ("Baseline reset gain", r"$G_{\mathrm{base}}$", None, None, a.base_gain),
        ("Adaptive scaling", r"$\beta$", None, None, a.gain_scaling),
        ("Spike amplitude", r"$A$", lif.amplitude, h.amplitude, a.amplitude),
        ("Min.\\ voltage clamp", r"$v_{\min}$", lif.min_voltage, h.min_voltage, a.min_voltage),
    ]
    lines = [
        r"\begin{table*}[t]",
        r"\centering",
        r"\caption{Default parameters of the reference implementation, reflected directly"
        r" from the \texttt{LIFParams}, \texttt{HyperLIFParams}, and"
        r" \texttt{AdaptiveHyperLIFParams} dataclasses. All voltages and gains are in the"
        r" normalized convention ($v_{\mathrm{rest}}=v_{\mathrm{reset}}=0$,"
        r" $v_{\mathrm{thresh}}=1$); $J$ and $G$ are dimensionless relative to the leak.}",
        r"\label{tab:params}",
        r"\begin{tabular}{llccc}",
        r"\toprule",
        r"Parameter & Symbol & LIF & HyperLIF & Adaptive HyperLIF \\",
        r"\midrule",
    ]
    for name, sym, vl, vh, va in rows:
        lines.append(f"{name} & {sym} & {cell(vl)} & {cell(vh)} & {cell(va)} \\\\")
    lines += [r"\bottomrule", r"\end{tabular}", r"\end{table*}", ""]
    write("tab_params.tex", "\n".join(lines))


def tab_model_compare() -> None:
    rows = [
        ("State variables", r"$\{v\}$", r"$\{v, r\}$", r"$\{v, r\}$"),
        ("Reset mechanism", "hard jump to $v_{\\mathrm{reset}}$",
         "gate conductance $G_b r^2$", "input-modulated $(G_{\\mathrm{base}}+\\beta|J|)r^2$"),
        ("Threshold event", "discontinuous", "smooth crossing", "smooth crossing"),
        ("Continuous \\& differentiable", "no (hybrid)", "yes", "yes"),
        ("Refractory handling", "explicit $\\tau_{\\mathrm{ref}}$",
         "gate hysteresis $\\gamma$", "gate hysteresis $\\gamma$"),
        ("High-drive behaviour", "unbounded firing", "depolarization-block latch",
         "bounded, graceful self-silencing"),
        ("Nengo \\texttt{NeuronType}", "(built-in)", r"\texttt{HyperLIFNengo}",
         r"\texttt{AdaptiveHyperLIFNengo}"),
    ]
    lines = [
        r"\begin{table*}[t]",
        r"\centering",
        r"\caption{Qualitative comparison of the three neuron models in the reference"
        r" implementation.}",
        r"\label{tab:modelcompare}",
        r"\small",
        r"\begin{tabular}{p{0.17\textwidth} p{0.23\textwidth} p{0.24\textwidth} p{0.25\textwidth}}",
        r"\toprule",
        r"Property & LIF & HyperLIF & Adaptive HyperLIF \\",
        r"\midrule",
    ]
    for name, vl, vh, va in rows:
        lines.append(f"{name} & {vl} & {vh} & {va} \\\\")
    lines += [r"\bottomrule", r"\end{tabular}", r"\end{table*}", ""]
    write("tab_model_compare.tex", "\n".join(lines))


def tab_sweep() -> None:
    rows = load_rows("03_current_sweep.csv")
    targets = [1.0, 1.5, 2.0, 2.4, 3.0, 4.0]

    def get(model: str, current: float, col: str) -> float:
        for r in rows:
            if r["model"] == model and abs(float(r["input_current"]) - current) < 1e-6:
                return float(r[col])
        return float("nan")

    lines = [
        r"\begin{table*}[t]",
        r"\centering",
        r"\caption{Steady-state response at representative constant currents (from"
        r" \texttt{03\_current\_sweep.csv}). The fixed-gain HyperLIF firing rate collapses"
        r" to zero and its mean voltage latches above threshold once $J$ exceeds the"
        r" analytical depolarization-block onset $J_{\mathrm{DB}}=2.4$, whereas Adaptive"
        r" HyperLIF sustains spiking with a bounded mean voltage.}",
        r"\label{tab:sweep}",
        r"\begin{tabular}{cccccc}",
        r"\toprule",
        r"& \multicolumn{3}{c}{Firing rate (Hz)} & \multicolumn{2}{c}{Mean voltage} \\",
        r"\cmidrule(lr){2-4}\cmidrule(lr){5-6}",
        r"$J$ & LIF & HyperLIF & Adaptive & HyperLIF & Adaptive \\",
        r"\midrule",
    ]
    for j in targets:
        lines.append(
            f"{j:g} & {get('LIF', j, 'event_rate_hz'):.1f} & "
            f"{get('HyperLIF', j, 'event_rate_hz'):.1f} & "
            f"{get('Adaptive HyperLIF', j, 'event_rate_hz'):.1f} & "
            f"{get('HyperLIF', j, 'voltage_mean'):.3f} & "
            f"{get('Adaptive HyperLIF', j, 'voltage_mean'):.3f} \\\\"
        )
    lines += [r"\bottomrule", r"\end{tabular}", r"\end{table*}", ""]
    write("tab_sweep.tex", "\n".join(lines))


def tab_parity() -> None:
    rows = load_rows("07_parity_metrics.csv")
    lines = [
        r"\begin{table}[t]",
        r"\centering",
        r"\caption{Standalone stable stepping vs.\ the Nengo \texttt{NeuronType} port"
        r" (from \texttt{07\_parity\_metrics.csv}). Agreement is exact to floating point:"
        r" zero RMSE, zero maximum voltage/gate difference, and zero event-timing"
        r" mismatches across both protocols and both models.}",
        r"\label{tab:parity}",
        r"\begin{tabular}{llcccc}",
        r"\toprule",
        r"Model & Protocol & $v$ RMSE & $\max|\Delta v|$ & $r$ RMSE & Event mism. \\",
        r"\midrule",
    ]
    for r in rows:
        model = r["model"].replace("Adaptive HyperLIF", "Adaptive")
        lines.append(
            f"{model} & {r['protocol']} & {fnum(r['voltage_rmse'])} & "
            f"{fnum(r['voltage_max_abs_diff'])} & {fnum(r['gate_rmse'])} & "
            f"{int(float(r['event_mismatch_count']))} \\\\"
        )
    lines += [r"\bottomrule", r"\end{tabular}", r"\end{table}", ""]
    write("tab_parity.tex", "\n".join(lines))


def tab_decoding() -> None:
    rows = load_rows("05_decoding_metrics.csv")
    label = {
        "voltage_to_current": r"Voltage $\rightarrow$ input current",
        "filtered_events_to_current": r"Filtered events $\rightarrow$ input current",
        "gate_to_readiness": r"Reset gate $\rightarrow$ readiness",
    }
    lines = [
        r"\begin{table}[t]",
        r"\centering",
        r"\caption{Scalar linear decoders fit by least squares with a 70/30 train/test"
        r" split (from \texttt{05\_decoding\_metrics.csv}).}",
        r"\label{tab:decoding}",
        r"\begin{tabular}{lcc}",
        r"\toprule",
        r"Decoder & Train RMSE & Test RMSE \\",
        r"\midrule",
    ]
    for r in rows:
        lines.append(
            f"{label.get(r['decoder'], r['decoder'])} & "
            f"{float(r['train_rmse']):.3f} & {float(r['test_rmse']):.3f} \\\\"
        )
    lines += [r"\bottomrule", r"\end{tabular}", r"\end{table}", ""]
    write("tab_decoding.tex", "\n".join(lines))


def tab_integration() -> None:
    rows = load_rows("06_integration_accuracy.csv")
    dts = sorted({float(r["dt"]) for r in rows}, reverse=True)

    def get(dt: float, method: str, col: str) -> float:
        for r in rows:
            if abs(float(r["dt"]) - dt) < 1e-12 and r["method"] == method:
                return float(r[col])
        return float("nan")

    lines = [
        r"\begin{table}[t]",
        r"\centering",
        r"\caption{Voltage error of the two stepping schemes against a fine RK4 reference"
        r" of the continuous ODE (from \texttt{06\_integration\_accuracy.csv}). Both"
        r" converge at first order; the gate update is shared and identical.}",
        r"\label{tab:integration}",
        r"\begin{tabular}{cccc}",
        r"\toprule",
        r"$\Delta t$ (s) & RMSE explicit & RMSE exponential & Gate RMSE \\",
        r"\midrule",
    ]
    for dt in dts:
        lines.append(
            f"{fnum(dt)} & {fnum(get(dt, 'julia', 'voltage_rmse'))} & "
            f"{fnum(get(dt, 'stable', 'voltage_rmse'))} & "
            f"{fnum(get(dt, 'julia', 'gate_rmse'))} \\\\"
        )
    lines += [r"\bottomrule", r"\end{tabular}", r"\end{table}", ""]
    write("tab_integration.tex", "\n".join(lines))


def tab_notation() -> None:
    rows = [
        (r"$v(t)$", "Membrane voltage (normalized)"),
        (r"$r(t)\in[0,1]$", "Continuous reset gate (fast activation-like proxy)"),
        (r"$J$ (= $I_{\mathrm{in}}$)", "Net input current / drive (normalized)"),
        (r"$\tau,\ \tau_r$", "Membrane and gate time constants ($\\tau_r\\ll\\tau$)"),
        (r"$v_{\mathrm{rest}},v_{\mathrm{reset}},v_{\mathrm{thresh}}$", "Rest, reset, threshold voltages"),
        (r"$\sigma(\cdot)$", "Logistic gate detector, steepness $\\alpha$"),
        (r"$\gamma,\ \theta_{\mathrm{eff}}$", "Hysteresis and effective threshold $\\theta_{\\mathrm{eff}}=v_{\\mathrm{thresh}}-\\gamma r$"),
        (r"$G_b$", "Fixed reset gain (baseline HyperLIF)"),
        (r"$G_{\mathrm{base}},\ \beta$", "Baseline gain and adaptive scaling (Adaptive HyperLIF)"),
        (r"$G(r,J)$", "Reset conductance scale; $G_b r^2$ or $(G_{\\mathrm{base}}+\\beta|J|)r^2$"),
        (r"$G_{\mathrm{dyn}}$", "Adaptive conductance scale $G_{\\mathrm{base}}+\\beta|J|$"),
        (r"$\lambda$", "Membrane relaxation rate $1/\\tau + G$"),
        (r"$J_{\mathrm{DB}}$", "Depolarization-block onset current"),
        (r"$\Delta t$", "Simulation time step"),
    ]
    lines = [
        r"\begin{table}[t]",
        r"\centering",
        r"\caption{Notation used throughout the paper.}",
        r"\label{tab:notation}",
        r"\begin{tabular}{l p{0.72\columnwidth}}",
        r"\toprule",
        r"Symbol & Meaning \\",
        r"\midrule",
    ]
    for sym, mean in rows:
        lines.append(f"{sym} & {mean} \\\\")
    lines += [r"\bottomrule", r"\end{tabular}", r"\end{table}", ""]
    write("tab_notation.tex", "\n".join(lines))


def main() -> None:
    tab_notation()
    tab_params()
    tab_model_compare()
    tab_sweep()
    tab_parity()
    tab_decoding()
    tab_integration()
    print(f"Tables written to {OUT_DIR}")


if __name__ == "__main__":
    main()
