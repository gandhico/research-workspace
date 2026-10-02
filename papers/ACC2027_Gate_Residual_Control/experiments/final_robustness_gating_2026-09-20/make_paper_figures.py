"""Build the title-free paper figures from the campaign runs (no simulation is rerun).

Outputs go to figures_out/.  Each run is read from results/ by (campaign, platform, mission, arm, tag).
"""
from __future__ import annotations

import sys
from pathlib import Path

import figlib as F

HERE = Path(__file__).resolve().parent
RES = HERE / "results" / "confirmatory"
OUT = HERE / "figures_out"


def run_dir(campaign, platform, mission, arm, tag="nominal", seed=1):
    d = RES / campaign / platform / mission / arm / tag / f"seed_{seed:03d}"
    if not (d / "trace.csv").exists():
        raise FileNotFoundError(d)
    return d


def nominal(platform, mission, arm):
    tag = "load_1" if arm == "cmg_pes_gated" else "nominal"
    return run_dir("nominal", platform, mission, arm, tag)


def hardstep_gate(plat: str = "x2", window=(10.7, 13.1), axis="z", out_name=None, size=(3.45, 2.4),
                  tq_scale=1.0, tq_unit="N$\\cdot$m"):
    """Zoom on one Hardstep step: log error, and the binding-axis torque with the gate's blocked intervals."""
    import matplotlib.pyplot as plt
    import numpy as np
    F.style()
    arms = ("pdff_rho3", "cmg_pes_table", "cmg_pes_gated")
    d = {a: F.load(nominal(plat, "hardstep", a)) for a in arms}
    lim = float(d["pdff_rho3"][1]["actuation"]["torque_limits_Nm"]["xyz".index(axis)])
    t0, t1 = window
    fig, axs = plt.subplots(2, 1, figsize=size, sharex=True, gridspec_kw={"height_ratios": [1.15, 1], "hspace": 0.14})
    for a in arms:
        df = d[a][0]
        m = ((df.t >= t0) & (df.t <= t1)).to_numpy()
        axs[0].semilogy(df.t[m], np.degrees(df.qerr_true_rad[m]).clip(lower=1e-2), color=F.COLORS[a], lw=0.95,
                        label=F.NAMES[a], zorder=3 if a == "cmg_pes_gated" else 2)
    axs[0].set_ylim(0.05, 200)
    axs[0].set_ylabel("Error (deg)")
    axs[0].axhline(5.0, color="#999999", lw=0.5, ls=":")
    for a, ls, lw in (("pdff_rho3", "-", 1.0), ("cmg_pes_table", "-", 0.8), ("cmg_pes_gated", "-", 0.95)):
        df = d[a][0]
        m = ((df.t >= t0) & (df.t <= t1)).to_numpy()
        axs[1].plot(df.t[m], df[f"tau_command_{axis}"][m] * tq_scale, color=F.COLORS[a], lw=lw, ls=ls)
    for s in (+1, -1):
        axs[1].axhline(s * lim * tq_scale, color="#666666", lw=0.6, ls="--")
    dfg = d["cmg_pes_gated"][0]
    m = ((dfg.t >= t0) & (dfg.t <= t1)).to_numpy()
    blocked = (dfg[f"output_gate_mask_{axis}"].to_numpy() == 0.0) & m
    tt = dfg.t.to_numpy()
    edges = np.flatnonzero(np.diff(np.r_[0, blocked.astype(int), 0]))
    for s, e in zip(edges[::2], edges[1::2]):
        for ax in axs:
            ax.axvspan(tt[s], tt[min(e, len(tt) - 1)], color="#cfe8dc", alpha=0.8, lw=0, zorder=0)
    axs[1].set_ylabel(f"{'Roll Pitch Yaw'.split()['xyz'.index(axis)]} torque\n({tq_unit})")
    axs[1].set_xlabel("Time (s)")
    axs[1].set_xlim(t0, t1)
    axs[0].tick_params(labelbottom=False)
    handles = [plt.Line2D([], [], color=F.COLORS[a], lw=1.0, label=F.NAMES[a]) for a in arms]
    handles.append(plt.Rectangle((0, 0), 1, 1, fc="#cfe8dc", ec="none", label="residual blocked"))
    fig.legend(handles=handles, loc="upper center", ncol=4, frameon=False, bbox_to_anchor=(0.5, 1.0),
               handlelength=1.4, columnspacing=0.9, fontsize=6.0)
    # margins in inches (0.228 in above, 0.325 in below): identical to the former 0.905 / 0.135 at 2.4 in height, and they
    # keep the axis label when the figure is made shorter (v14)
    fig.subplots_adjust(left=0.20, right=0.985, top=1 - 0.228 / size[1], bottom=0.325 / size[1])
    out = OUT / (out_name or f"{plat}_hardstep_gate_zoom")
    fig.savefig(out.with_suffix(".png"), dpi=300)
    fig.savefig(out.with_suffix(".pdf"))
    plt.close(fig)


A2 = HERE / "results" / "confirmatory_a2"


def _a2_dir(campaign, platform, mission, tag, seed):
    """CF2's selected primary arm (gated, beta = 0.2) lives under confirmatory_a2 (amendment A2)."""
    d = A2 / campaign / platform / mission / "cmg_pes_gated_b02" / tag / f"seed_{seed:03d}"
    if not (d / "trace.csv").exists():
        raise FileNotFoundError(d)
    return d


def dist_dir(plat, arm, level="x1", seed=1):
    tag = f"dist_{level}" + ("__load_1" if arm == "cmg_pes_gated" else "")
    if plat == "cf2-rotor" and arm == "cmg_pes_gated":
        return _a2_dir("a2_dist", plat, "hover", tag, seed)
    return run_dir("disturbance", plat, "hover", arm, tag, seed)


def noise_dir(plat, mission, arm, level="realistic", seed=1):
    tag = f"noise_{level}" + ("__load_1" if arm == "cmg_pes_gated" else "")
    if plat == "cf2-rotor" and arm == "cmg_pes_gated":
        return _a2_dir("a2_noise", plat, mission, tag, seed)
    return run_dir("noise", plat, mission, arm, tag, seed)


def disturbance_figures():
    import numpy as np
    for plat in ("x2", "cf2-rotor"):
        runs = {a: F.load(dist_dir(plat, a))[0] for a in ("pdff_rho3", "cmg_pes_gated")}
        gain = runs["pdff_rho3"]["disturbance_gain"].to_numpy()
        t = runs["pdff_rho3"]["t"].to_numpy()
        on = gain >= 0.5
        edges = np.flatnonzero(np.diff(np.r_[0, on.astype(int), 0]))
        shade = [(t[s], t[min(e, len(t) - 1)]) for s, e in zip(edges[::2], edges[1::2])]
        F.attitude_figure(runs, OUT / f"{plat}_hover_disturbance_attitude_rho3", size=(3.45, 3.55),
                          err_unit="deg", legend_cols=3, shade=shade)
        F.neuron_figure(runs["cmg_pes_gated"], OUT / f"{plat}_hover_disturbance_neurons_rho3", size=(3.45, 3.2))


def noise_figures():
    for plat in ("x2", "cf2-rotor"):
        runs = {a: F.load(noise_dir(plat, "hard45", a))[0] for a in ("pdff_rho3", "cmg_pes_gated")}
        F.attitude_figure(runs, OUT / f"{plat}_hard45_noise_attitude_rho3", size=(3.45, 3.55), err_ylim=(0, 60),
                          legend_cols=3)
        F.neuron_figure(runs["cmg_pes_gated"], OUT / f"{plat}_hard45_noise_neurons_rho3", size=(3.45, 3.2),
                        residual_ylim=(-0.12, 0.12) if plat == "x2" else None)


def main(which: list[str]) -> None:
    OUT.mkdir(exist_ok=True)
    if "hard45" in which:
        runs = {a: F.load(nominal("x2", "hard45", a))[0] for a in ("pdff_rho3", "cmg_pes_table")}
        for df in runs.values():
            assert F.check_euler_convention(df) < 1e-6
        F.attitude_figure(runs, OUT / "x2_hard45_attitude_rho3", size=(3.45, 3.15), err_ylim=(0, 25),
                          legend_cols=3)
        # compact version used in the paper: the three Euler panels are indistinguishable from the reference,
        # so only the error and the roll panel are kept (the full four-panel figure above is in the package)
        F.attitude_figure(runs, OUT / "x2_hard45_attitude_rho3_compact", size=(3.45, 2.1), err_ylim=(0, 25),
                          legend_cols=3, euler_axes=(0,))
        F.neuron_figure(runs["cmg_pes_table"], OUT / "x2_hard45_neurons_rho3", size=(3.45, 3.2), residual_ylim=(-0.06, 0.06))
    if "hardstep" in which:
        for plat in ("x2", "cf2-rotor"):
            runs = {a: F.load(nominal(plat, "hardstep", a))[0]
                    for a in ("pdff_rho3", "cmg_pes_table", "cmg_pes_gated")}
            F.attitude_figure(runs, OUT / f"{plat}_hardstep_attitude_rho3", size=(3.45, 3.55),
                              t_window=(0, 45), err_unit="deg", legend_cols=4)
    if "disturbance" in which:
        disturbance_figures()
    if "noise" in which:
        noise_figures()
    if "hardstep_zoom" in which:
        hardstep_gate("x2", axis="z")
        hardstep_gate("cf2-rotor", axis="x", out_name="cf2-rotor_hardstep_gate_zoom", tq_scale=1e3,
                      tq_unit="mN$\\cdot$m")
    print("done ->", OUT)


if __name__ == "__main__":
    main(sys.argv[1:] or ["hard45", "hardstep"])
