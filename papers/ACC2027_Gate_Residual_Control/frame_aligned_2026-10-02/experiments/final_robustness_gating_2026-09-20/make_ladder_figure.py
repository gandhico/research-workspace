"""Ladder version of the old "attitude_detail" figure (outputs / Euler angles / quaternions / inputs).

Rows 1-4 (attitude error, roll, pitch, yaw): the three PD versions of the paper's baseline ladder in a blue gradient (light -> dark = weak -> strong
baseline: original fixed PD, PD + rate feedforward at rho = 1, PD + rate feedforward at rho = 3) and the CMG-PES run on each in a red gradient.
The controller signals are semi-transparent and the reference is a solid-black dashed line drawn on top of them, so it can always be told apart.
Rows 5-6 (quaternion, rotor forces): the best CMG run of the mission (lowest 45-s mean error among the CMG versions drawn).

Nothing is re-simulated: every trace is one of the runs behind Table II, and every mean shown is checked against the tables the paper is built from
(experiments/baseline_restatement_2026-09-16/master_table.csv, results/final_nominal.csv).

Variants
  A  log error axis (the ladder spans two decades: 30 deg for the fixed PD, 0.5 deg for the tuned baseline)
  B  linear error axis (the original look; the tuned baselines are squeezed against zero)
  C  as A plus a zoom column (one 8-s window) next to the full run, for every row
CF2's PD+ff rho = 3 + CMG-PES run uses the adopted beta = 0.2 (gated); --cf2-beta 0.5 draws the noise-free beta = 0.5 run instead (lower error on
Hard45, but beta = 0.5 diverges on CF2 Hardstep under noise, so it is not the adopted setting).
Outputs: figures_out/ladder/<platform>_<mission>_ladder_<A|B|C>[_beta05].{png,pdf,json}   (title-free; --titles adds the old bold section titles)
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D

import figlib as F
from figlib_multi import _qmul, _ref_quat

HERE = Path(__file__).resolve().parent
ACC = HERE.parents[1]
ARCH = ACC / "experiments" / "nengo_nef_replication_2026-08-29" / "results"
MASTER = ACC / "experiments" / "baseline_restatement_2026-09-16" / "master_table.csv"
R = HERE / "results"
OUT = HERE / "figures_out" / "ladder"

BLUES = ["#3D8FD1", "#1560B0", "#08306B"]      # fixed PD, PD+ff rho=1, PD+ff rho=3   (light -> dark = weak -> strong baseline)
REDS = ["#F0552F", "#C0141B", "#67000D"]       # CMG-PES on each
LW = [1.5, 1.25, 1.05]                         # weak baselines are drawn wider (and first), strong ones thinner and on top
ALPHA_EULER = 0.55                             # controller signals in rows 2-4: transparent, so the reference stays identifiable
ALPHA_ERR = 0.8                                # error row (no reference there): light transparency shows where curves overlap
COMP = {"w": "#222222", "x": "#E69F00", "y": "#009E73", "z": "#7B3294"}           # quaternion components (no red/blue: those are the families)
MOTOR = ["#E69F00", "#009E73", "#7B3294", "#666666"]
NAMES = ["PD", r"PD+ff $\rho{=}1$", r"PD+ff $\rho{=}3$"]
ZOOM = {"hard45": (14.0, 22.0), "full3": (14.0, 22.0), "roll": (10.0, 20.0), "yaw360": (5.0, 45.0), "hardstep": (9.0, 15.0)}


# --------------------------------------------------------------------------------------------------------------------- data
def _load_archived(d: Path) -> dict:
    """Archived-runner trace (error quaternion + reference Euler angles logged; measured quaternion recovered as conj(q_e) (x) q_ref)."""
    tr = pd.read_csv(d / "trace.csv")
    s = json.loads((d / "summary.json").read_text(encoding="utf-8"))
    step = max(1, int(round(0.005 / float(tr.t.iloc[1] - tr.t.iloc[0]))))
    tr = tr.iloc[::step].reset_index(drop=True)
    qref = _ref_quat(tr.ref_roll.to_numpy(), tr.ref_pitch.to_numpy(), tr.ref_yaw.to_numpy())
    q = _qmul(tr[["qe_w", "qe_x", "qe_y", "qe_z"]].to_numpy() * np.array((1.0, -1.0, -1.0, -1.0)), qref)
    return dict(t=tr.t.to_numpy(), err=tr.qerr.to_numpy(), ref=np.degrees(tr[["ref_roll", "ref_pitch", "ref_yaw"]].to_numpy()), q=q,
                act=tr[[f"actuator_{i}" for i in range(4)]].to_numpy(), mean=float(s["qerr_mean_rad"]), src=str(d))


def _load_sealed(d: Path) -> dict:
    tr = pd.read_csv(d / "trace.csv")
    s = json.loads((d / "summary.json").read_text(encoding="utf-8"))
    return dict(t=tr.t.to_numpy(), err=tr.qerr_true_rad.to_numpy(), ref=np.degrees(tr[["ref_roll", "ref_pitch", "ref_yaw"]].to_numpy()),
                q=tr[[f"qtrue_{c}" for c in "wxyz"]].to_numpy(), act=tr[[f"actuator_command_{i}" for i in range(4)]].to_numpy(),
                mean=float(s["metrics"]["qerr_true_mean_rad"]), src=str(d))


def run_specs(platform: str, mission: str, cf2_beta: float) -> list[dict]:
    """The six runs of the ladder: (family, level, loader, path, beta of the CMG residual)."""
    a = "x2" if platform == "x2" else "cf2_rotor"
    m45 = ARCH / "matched_45s"
    ff = ARCH / "pid_baseline_2026-09-10"
    nom = R / "confirmatory" / "nominal" / platform / mission
    pd1 = (ff / "rate_ff_select" / "left-neg" / f"x2_{mission}") if platform == "x2" and mission != "hardstep" else (ff / "rate_ff_left_neg" / f"{a}_{mission}_classical")
    if platform == "x2" or cf2_beta == 0.5:        # sealed campaign, gated arm at beta 0.5
        cmg2, beta2 = nom / "cmg_pes_gated" / "load_1" / "seed_001", 0.5
    else:                                           # amendment A2: CF2 adopted beta 0.2, gated
        cmg2, beta2 = R / "confirmatory_a2" / "a2_nominal" / platform / mission / "cmg_pes_gated_b02" / "load_1" / "seed_001", 0.2
    return [
        dict(fam="pd", lvl=0, load=_load_archived, path=m45 / f"{a}_{mission}_classical", beta=None),
        dict(fam="pd", lvl=1, load=_load_archived, path=pd1, beta=None),
        dict(fam="pd", lvl=2, load=_load_sealed, path=nom / "pdff_rho3" / "nominal" / "seed_001", beta=None),
        dict(fam="cmg", lvl=0, load=_load_archived, path=m45 / f"{a}_{mission}_nengo_nef_pes", beta=0.5),
        dict(fam="cmg", lvl=1, load=_load_archived, path=ff / "rate_ff_left_neg" / f"{a}_{mission}_nengo_nef_pes", beta=0.5),
        dict(fam="cmg", lvl=2, load=_load_sealed, path=cmg2, beta=beta2),
    ]


def load_runs(platform: str, mission: str, cf2_beta: float) -> list[dict]:
    runs = []
    for sp in run_specs(platform, mission, cf2_beta):
        r = sp["load"](sp["path"])
        r.update(fam=sp["fam"], lvl=sp["lvl"], beta=sp["beta"], platform=platform)
        runs.append(r)
    check_means(platform, mission, runs)
    return runs


def check_means(platform: str, mission: str, runs: list[dict]) -> None:
    """The means drawn must be the ones in the paper's tables (relative tolerance 1e-4; the two executions of the CMG-on-PD configuration differ by 3e-8 (X2) and 2e-6 (CF2))."""
    mt = next(r for r in csv.DictReader(MASTER.open(encoding="utf-8")) if r["platform"] == platform and r["mission"] == mission)
    fn = {(r["platform"], r["mission"], r["label"]): float(r["qerr_true_mean_rad"]) for r in csv.DictReader((R / "final_nominal.csv").open(encoding="utf-8"))}
    cmg2_label = "cmg_pes_gated" if (platform == "x2" or runs[5]["beta"] == 0.2) else "cmg_pes_gated_b05"
    want = {("pd", 0): float(mt["PD"]), ("cmg", 0): float(mt["CMG_on_PD"]), ("pd", 1): float(mt["PDff_1x"]), ("cmg", 1): float(mt["CMG_on_PDff_1x"]),
            ("pd", 2): fn[(platform, mission, "pdff_rho3")], ("cmg", 2): fn[(platform, mission, cmg2_label)]}
    for r in runs:
        w = want[(r["fam"], r["lvl"])]
        r["table_rel_dev"] = abs(r["mean"] - w) / w
        assert r["table_rel_dev"] <= 1e-4, (platform, mission, r["fam"], r["lvl"], r["mean"], w)


def euler_deg(q: np.ndarray, ref_deg: np.ndarray) -> np.ndarray:
    e = F._unwrap(F.euler_zyx(q))
    return e + np.round((ref_deg[0] - e[0]) / 360.0) * 360.0


# ------------------------------------------------------------------------------------------------------------------- figure
def label(r: dict, base: float | None) -> str:
    deg = np.degrees(r["mean"])
    if r["fam"] == "pd":
        return f"{NAMES[r['lvl']]}   {deg:.2f}°"
    core = {0: "PD", 1: r"PD+ff $\rho{=}1$", 2: r"PD+ff $\rho{=}3$"}[r["lvl"]]
    gate = ", gated" if r["lvl"] == 2 else ""
    beta = rf", $\beta$={r['beta']:.1f}" if (r["lvl"] == 2 and r["platform"] != "x2") else ""      # CF2's beta differs between variants: say it
    change = f"{100 * (r['mean'] - base) / base:+.1f}%".replace("-", "−")
    return f"{core} + CMG-PES{gate}{beta}   {deg:.2f}°  ({change})"


def ladder_figure(platform: str, mission: str, variant: str, *, titles: bool = False, cf2_beta: float = 0.2) -> Path:
    runs = load_runs(platform, mission, cf2_beta)
    pdr = {r["lvl"]: r for r in runs if r["fam"] == "pd"}
    cmr = [r for r in runs if r["fam"] == "cmg"]
    best = min(cmr, key=lambda r: r["mean"])
    z0, z1 = ZOOM[mission]
    ncol = 2 if variant == "C" else 1
    F.style(7.0)
    fig_h = 9.6
    fig, axs = plt.subplots(6, ncol, figsize=(7.2, fig_h), sharex="col", squeeze=False,
                            gridspec_kw={"height_ratios": [1.35, 1, 1, 1, 0.85, 0.95], "hspace": 0.16, "wspace": 0.2,
                                         **({"width_ratios": [1.6, 1.0]} if ncol == 2 else {})})
    scale_act, act_unit = (1.0, "Rotor force (N)") if platform == "x2" else (1e3, "Rotor force (mN)")
    order = sorted(runs, key=lambda r: (r["lvl"], r["fam"] == "cmg"))             # weak first, strong on top; CMG above its PD
    ref = runs[0]["ref"]
    t = runs[0]["t"]
    for c in range(ncol):
        zoom = c == 1
        m = (t >= z0) & (t <= z1) if zoom else np.ones_like(t, dtype=bool)
        # rows 1-4: transparent controller signals ...
        for r in order:
            col = (BLUES if r["fam"] == "pd" else REDS)[r["lvl"]]
            kw = dict(color=col, lw=LW[r["lvl"]] * (1.0 if not zoom else 1.1), zorder=2 + 2 * r["lvl"] + (r["fam"] == "cmg"), solid_capstyle="round")
            err = np.degrees(r["err"])
            axs[0, c].plot(r["t"][m], (np.clip(err, 0.01, None) if variant != "B" else err)[m], alpha=ALPHA_ERR, **kw)
            e = euler_deg(r["q"], r["ref"])
            for i in range(3):
                axs[1 + i, c].plot(r["t"][m], e[m, i], alpha=ALPHA_EULER, **kw)
        # ... and the reference on top of them, opaque
        for i in range(3):
            axs[1 + i, c].plot(t[m], ref[m, i], color="k", ls=(0, (4, 2.2)), lw=1.0, zorder=30)
        # rows 5-6: the best CMG run
        q = best["q"] * np.where(best["q"][:, :1] < 0, -1.0, 1.0)
        for k, comp in enumerate("wxyz"):
            axs[4, c].plot(best["t"][m], q[m, k], color=COMP[comp], lw=0.8, label=rf"$q_{comp}$")
        for k in range(4):
            axs[5, c].plot(best["t"][m], best["act"][m, k] * scale_act, color=MOTOR[k], lw=0.7, label=f"rotor {k}")
        # cosmetics
        if variant == "B":
            axs[0, c].set_ylim(0, None)
        else:
            axs[0, c].set_yscale("log")
            axs[0, c].set_ylim(0.03, 60)
            axs[0, c].set_yticks([0.1, 1, 10])
            axs[0, c].set_yticklabels(["0.1", "1", "10"])
        axs[4, c].set_ylim(-1.05, 1.05)
        if zoom:
            axs[0, c].set_xlim(z0, z1)
            for row in range(1, 6):                                               # y range from the data inside the window
                lo, hi = np.inf, -np.inf
                for ln in axs[row, c].get_lines():
                    x, y = ln.get_data()
                    sel = (x >= z0) & (x <= z1)
                    if sel.any():
                        lo, hi = min(lo, float(np.min(y[sel]))), max(hi, float(np.max(y[sel])))
                pad = 0.06 * (hi - lo + 1e-12)
                axs[row, c].set_ylim(lo - pad, hi + pad)
        else:
            axs[5, c].set_xlim(0, 45)
            if ncol == 2:
                for row in range(6):
                    axs[row, c].axvspan(z0, z1, color="#EDEDED", lw=0, zorder=0)
        axs[5, c].set_xlabel("Time (s)")
        for row in range(5):
            axs[row, c].tick_params(labelbottom=False)
        if c == 0:
            for row, lab in enumerate(["Attitude error (deg)", "Roll (deg)", "Pitch (deg)", "Yaw (deg)", "Quaternion", act_unit]):
                axs[row, c].set_ylabel(lab)
    # rows 5-6 belong to one run: say which, in its own colour, above the quaternion panel (no curve is covered)
    tag = f"rows below: best CMG run (lowest mean error) = {label(best, pdr[best['lvl']]['mean']).split('   ')[0]}"
    axs[4, 0].set_title(tag, fontsize=6.2, loc="left", color=REDS[2], pad=2.5)
    if platform != "x2":                       # CF2 forces sit close to the bottom of their range: leave room for the legend
        lo, hi = axs[5, 0].get_ylim()
        axs[5, 0].set_ylim(lo - 0.30 * (hi - lo), hi + 0.03 * (hi - lo))
    axs[4, 0].legend(loc="lower right", ncol=4, frameon=False, handlelength=1.1, columnspacing=0.8, fontsize=6.0)        # full-run column only: the
    axs[5, 0].legend(loc="lower right", ncol=4, frameon=False, handlelength=1.1, columnspacing=0.8, fontsize=6.0)        # bottom of these panels is empty
    if titles:
        for row, txt in ((0, "OUTPUTS"), (1, "EULER ANGLES")):
            axs[row, 0].set_title(txt, fontsize=7.0, loc="left", fontweight="bold")
    # one legend: PD versions | CMG versions | reference
    pds = sorted([r for r in runs if r["fam"] == "pd"], key=lambda r: r["lvl"])
    handles = [Line2D([], [], color=BLUES[r["lvl"]], lw=2.0, alpha=0.75) for r in pds]
    labels = [label(r, None) for r in pds]
    handles.append(Line2D([], [], color="k", ls=(0, (4, 2.2)), lw=1.0))
    labels.append("Reference")
    for r in sorted(cmr, key=lambda r: r["lvl"]):
        handles.append(Line2D([], [], color=REDS[r["lvl"]], lw=2.0, alpha=0.75))
        labels.append(label(r, pdr[r["lvl"]]["mean"]))
    handles.append(Line2D([], [], color="none"))
    labels.append("")
    fig.legend(handles, labels, loc="upper center", ncol=2, frameon=False, fontsize=6.6, handlelength=2.2, columnspacing=1.4, labelspacing=0.35,
               bbox_to_anchor=(0.5, 0.999), title="mean error, and change from the PD version it sits on", title_fontsize=6.2)
    fig.subplots_adjust(left=0.105, right=0.985, top=1 - 0.86 / fig_h, bottom=0.42 / fig_h)
    OUT.mkdir(parents=True, exist_ok=True)
    suffix = "_beta05" if (platform != "x2" and cf2_beta == 0.5) else ""
    stem = OUT / f"{platform.replace('-rotor', '')}_{mission}_ladder_{variant}{suffix}"
    fig.savefig(stem.with_suffix(".png"), dpi=300)
    fig.savefig(stem.with_suffix(".pdf"))
    plt.close(fig)
    nums = {"platform": platform, "mission": mission, "variant": variant, "best_cmg": {"lvl": best["lvl"], "beta": best["beta"], "mean_mrad": best["mean"] * 1e3},
            "runs": [{"family": r["fam"], "level": r["lvl"], "beta": r["beta"], "mean_mrad": r["mean"] * 1e3, "mean_deg": float(np.degrees(r["mean"])),
                      "rel_dev_from_paper_table": r["table_rel_dev"], "source": r["src"]} for r in runs]}
    (stem.with_suffix(".json")).write_text(json.dumps(nums, indent=2), encoding="utf-8")
    return stem


# ------------------------------------------------------------------------------------------------------------- compact (paper-column) figure
def compact_ladder_figure(platform: str, mission: str, *, cf2_beta: float = 0.2, size=(3.45, 3.05)) -> Path:
    """Two rows only (error, roll), sized for one real IEEE column (3.45 in) at the paper's normal ~7pt figure font.

    Same data, colors and transparency rule as the full ladder; no zoom column, no pitch/yaw/quaternion/actuator rows.
    This is what Fig. 4 should actually be: the 6-row/12-panel version does not fit a single column at a readable size
    (measured in the compiled PDF: axis text down to ~3.1pt against ~10pt body text).
    """
    runs = load_runs(platform, mission, cf2_beta)
    pdr = {r["lvl"]: r for r in runs if r["fam"] == "pd"}
    cmr = [r for r in runs if r["fam"] == "cmg"]
    best = min(cmr, key=lambda r: r["mean"])
    F.style(7.0)
    fig, axs = plt.subplots(2, 1, figsize=size, sharex=True, gridspec_kw={"height_ratios": [1.3, 1], "hspace": 0.14})
    order = sorted(runs, key=lambda r: (r["lvl"], r["fam"] == "cmg"))
    ref = runs[0]["ref"]
    t = runs[0]["t"]
    for r in order:
        col = (BLUES if r["fam"] == "pd" else REDS)[r["lvl"]]
        kw = dict(color=col, lw=LW[r["lvl"]], zorder=2 + 2 * r["lvl"] + (r["fam"] == "cmg"), solid_capstyle="round")
        axs[0].plot(r["t"], np.clip(np.degrees(r["err"]), 0.01, None), alpha=ALPHA_ERR, **kw)
        e = euler_deg(r["q"], r["ref"])
        axs[1].plot(r["t"], e[:, 0], alpha=ALPHA_EULER, **kw)
    axs[1].plot(t, ref[:, 0], color="k", ls=(0, (4, 2.2)), lw=1.0, zorder=30)
    axs[0].set_yscale("log")
    axs[0].set_ylim(0.03, 60)
    axs[0].set_yticks([0.1, 1, 10])
    axs[0].set_yticklabels(["0.1", "1", "10"])
    axs[0].set_ylabel("Attitude error (deg)")
    axs[1].set_ylabel("Roll (deg)")
    axs[1].set_xlabel("Time (s)")
    axs[1].set_xlim(0, 45)
    axs[0].tick_params(labelbottom=False)
    pds = sorted([r for r in runs if r["fam"] == "pd"], key=lambda r: r["lvl"])
    handles = [Line2D([], [], color=BLUES[r["lvl"]], lw=1.8, alpha=0.75) for r in pds]
    labels = [label(r, None) for r in pds]
    handles.append(Line2D([], [], color="k", ls=(0, (4, 2.2)), lw=0.9))
    labels.append("Reference")
    for r in sorted(cmr, key=lambda r: r["lvl"]):
        handles.append(Line2D([], [], color=REDS[r["lvl"]], lw=1.8, alpha=0.75))
        labels.append(label(r, pdr[r["lvl"]]["mean"]))
    fig.legend(handles, labels, loc="upper center", ncol=2, frameon=False, fontsize=5.8, handlelength=1.7, columnspacing=1.0,
               labelspacing=0.32, bbox_to_anchor=(0.5, 1.0))
    fig.subplots_adjust(left=0.185, right=0.985, top=1 - 0.86 / size[1], bottom=0.36 / size[1])
    OUT.mkdir(parents=True, exist_ok=True)
    suffix = "_beta05" if (platform != "x2" and cf2_beta == 0.5) else ""
    stem = OUT / f"{platform.replace('-rotor', '')}_{mission}_ladder_compact{suffix}"
    fig.savefig(stem.with_suffix(".png"), dpi=300)
    fig.savefig(stem.with_suffix(".pdf"))
    plt.close(fig)
    nums = {"platform": platform, "mission": mission, "variant": "compact", "best_cmg": {"lvl": best["lvl"], "beta": best["beta"], "mean_mrad": best["mean"] * 1e3},
            "runs": [{"family": r["fam"], "level": r["lvl"], "beta": r["beta"], "mean_mrad": r["mean"] * 1e3, "mean_deg": float(np.degrees(r["mean"])),
                      "rel_dev_from_paper_table": r["table_rel_dev"], "source": r["src"]} for r in runs]}
    (stem.with_suffix(".json")).write_text(json.dumps(nums, indent=2), encoding="utf-8")
    return stem


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--platforms", nargs="+", default=["x2", "cf2-rotor"])
    ap.add_argument("--missions", nargs="+", default=["hard45"])
    ap.add_argument("--variants", nargs="+", default=["A", "B", "C"])
    ap.add_argument("--compact", action="store_true", help="build the 2-row, single-column-legible figure instead (the recommended Fig. 4)")
    ap.add_argument("--cf2-beta", type=float, default=0.2, choices=(0.2, 0.5), help="beta of CF2's PD+ff rho=3 + CMG-PES run (adopted: 0.2)")
    ap.add_argument("--titles", action="store_true", help="add the old bold section titles (OUTPUTS / EULER ANGLES)")
    a = ap.parse_args()
    for p in a.platforms:
        for m in a.missions:
            if a.compact:
                print("wrote", compact_ladder_figure(p, m, cf2_beta=a.cf2_beta))
                continue
            for v in a.variants:
                print("wrote", ladder_figure(p, m, v, titles=a.titles, cf2_beta=a.cf2_beta))
