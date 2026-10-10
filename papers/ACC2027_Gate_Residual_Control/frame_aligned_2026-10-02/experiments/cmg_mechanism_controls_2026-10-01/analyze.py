"""Analyze the CMG mechanism controls against the archived strict_exact references.

Outputs in analysis/:
  confirm_all_runs.csv, confirm_aggregate.csv, development.csv, RESULTS.md,
  improvement_by_mission.png, activity_new_arms.png
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
EXP = HERE.parents[0]
STRICT = EXP / "neuron_basis_decisive_2026-09-24" / "results" / "strict_exact"
DEV_BASE = EXP / "neuron_basis_decisive_2026-09-24" / "results" / "development_baseline"
CONFIRM = HERE / "results" / "confirm"
DEV = HERE / "results" / "development"
OUT = HERE / "analysis"
PLATFORMS = ("x2", "cf2-rotor")
MISSIONS = ("roll", "full3", "hard45", "hardstep", "yaw360")
ARCHIVED = ("cmg", "constant-one", "paired-current")
NEW = ("lpf-logistic", "constant-rest", "latch-replay", "cmg_chi0", "constant-one-nengo-order", "cmg_G1e3", "cmg_G1")
LABEL = {
    "cmg": "CMG (archived, chi=1)", "constant-one": "constant-one (archived, same-step PES)",
    "paired-current": "static paired (archived)", "lpf-logistic": "LPF + static logistic",
    "constant-rest": "constant-rest (a=0.3728)", "latch-replay": "latch replay",
    "cmg_chi0": "CMG chi=0", "constant-one-nengo-order": "constant-one (Nengo PES order)",
    "cmg_G1e3": "CMG G=1e3", "cmg_G1": "CMG G=1",
}
PUBLISHED = {"x2": 37.30, "cf2-rotor": 22.42}


def run_dir(platform: str, mission: str, arm: str) -> Path:
    return (STRICT if arm in ARCHIVED + ("classical",) else CONFIRM) / platform / mission / arm


def run_stats(path: Path) -> dict:
    s = json.loads((path / "summary.json").read_text(encoding="utf-8"))
    row = {"qerr_mean_rad": s["metrics"]["qerr_true_mean_rad"],
           "residual_nrms": s["metrics"].get("realized_residual_normalized_rms", 0.0)}
    npz = path / "neural_trace_full_rate.npz"
    if npz.exists():
        z = np.load(npz)
        a, r, g = z["activity"], z["gate"], z["output_gate_mask"]
        row.update({
            "a_norm2_mean": float(np.mean(np.sum(a ** 2, axis=1))),
            "frac_a_saturated": float(np.mean(a >= 1 - 1e-9)),
            "units_latched": int(np.sum(np.any(r > 0.5, axis=0))),
            "gate_blocked_fraction": float(np.mean(g < 0.5)),
        })
    return row


def geomean_improvement(ratios: list[float]) -> float:
    return 100.0 * (1.0 - float(np.exp(np.mean(np.log(ratios)))))


def verdict(arm_imp: dict, cmg_imp: dict) -> str:
    frac = [arm_imp[p] / cmg_imp[p] for p in PLATFORMS]
    if all(f >= 0.9 for f in frac):
        return "reproduces CMG"
    if all(f <= 0.5 for f in frac):
        return "fails"
    return "partial"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    rows, missing = [], []
    for platform in PLATFORMS:
        for mission in MISSIONS:
            base = run_stats(run_dir(platform, mission, "classical"))["qerr_mean_rad"]
            for arm in ARCHIVED + NEW:
                path = run_dir(platform, mission, arm)
                if not (path / "summary.json").exists():
                    missing.append(f"{platform}/{mission}/{arm}")
                    continue
                st = run_stats(path)
                ratio = st["qerr_mean_rad"] / base
                rows.append({"platform": platform, "mission": mission, "arm": arm,
                             "error_ratio": ratio, "improvement_percent": 100 * (1 - ratio), **st})
    fields = sorted({k for r in rows for k in r}, key=lambda k: (k not in ("platform", "mission", "arm"), k))
    with (OUT / "confirm_all_runs.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

    agg = {}
    for arm in ARCHIVED + NEW:
        agg[arm] = {}
        for platform in PLATFORMS:
            rr = [r for r in rows if r["arm"] == arm and r["platform"] == platform]
            if len(rr) == len(MISSIONS):
                agg[arm][platform] = geomean_improvement([r["error_ratio"] for r in rr])
    for p in PLATFORMS:  # self-check against the published Sec. VI-D numbers
        assert abs(agg["cmg"][p] - PUBLISHED[p]) < 0.01, (p, agg["cmg"][p])
    with (OUT / "confirm_aggregate.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["arm", "x2_geomean_improvement_percent", "cf2_geomean_improvement_percent", "verdict"])
        for arm in ARCHIVED + NEW:
            if len(agg[arm]) == 2:
                w.writerow([arm, f"{agg[arm]['x2']:.2f}", f"{agg[arm]['cf2-rotor']:.2f}",
                            "" if arm in ARCHIVED else verdict(agg[arm], agg["cmg"])])

    # Development check (15 s, X2)
    dev_rows = []
    for tag_dir in sorted(DEV.glob("G*_chi*")):
        for mission in ("roll", "hard45"):
            p = tag_dir / mission
            if not (p / "summary.json").exists():
                continue
            base = json.loads((DEV_BASE / mission / "classical" / "summary.json").read_text())["metrics"]["qerr_true_mean_rad"]
            st = run_stats(p)
            dev_rows.append({"setting": tag_dir.name, "mission": mission,
                             "improvement_percent": 100 * (1 - st["qerr_mean_rad"] / base), **st})
    if dev_rows:
        with (OUT / "development.csv").open("w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=list(dev_rows[0]))
            w.writeheader()
            w.writerows(dev_rows)

    write_report(rows, agg, dev_rows, missing)
    make_figures(rows)
    print((OUT / "RESULTS.md").read_text(encoding="utf-8"))


def write_report(rows, agg, dev_rows, missing) -> None:
    L = ["# CMG mechanism controls — results", "",
         "Generated by `analyze.py`. Metric: geometric mean over five missions of the mean true",
         "quaternion-angle error ratio to the classical rho=3 PD+ff baseline (Sec. VI-D). The CMG row",
         "reproduces the published 37.30% / 22.42% (asserted).", ""]
    if missing:
        L += [f"**Missing runs ({len(missing)}):** " + ", ".join(missing), ""]
    L += ["## Aggregate", "", "| Arm | X2 | CF2 | Verdict (preregistered) |", "|---|---|---|---|"]
    for arm in ARCHIVED + NEW:
        if len(agg[arm]) == 2:
            v = "reference" if arm in ARCHIVED else verdict(agg[arm], agg["cmg"])
            L.append(f"| {LABEL[arm]} | {agg[arm]['x2']:.2f}% | {agg[arm]['cf2-rotor']:.2f}% | {v} |")
    L += ["", "## Per mission (improvement %, units latched, mean ||a||^2)", ""]
    arms = [a for a in ARCHIVED + NEW if len(agg[a]) == 2]
    L.append("| Platform | Mission | " + " | ".join(LABEL[a] for a in arms) + " |")
    L.append("|---|---|" + "---|" * len(arms))
    for p in PLATFORMS:
        for m in MISSIONS:
            cells = []
            for a in arms:
                r = next(x for x in rows if x["platform"] == p and x["mission"] == m and x["arm"] == a)
                extra = f" ({r['units_latched']}L, {r['a_norm2_mean']:.2f})" if "units_latched" in r else ""
                cells.append(f"{r['improvement_percent']:+.1f}{extra}")
            L.append(f"| {p} | {m} | " + " | ".join(cells) + " |")
    if dev_rows:
        L += ["", "## Development check (X2, 15 s, CMG readout gain G and chi)", "",
              "| Setting | Mission | Improvement | units latched | frac a saturated | mean ||a||^2 |", "|---|---|---|---|---|---|"]
        for r in dev_rows:
            L.append(f"| {r['setting']} | {r['mission']} | {r['improvement_percent']:+.2f}% | {r.get('units_latched')} | "
                     f"{r.get('frac_a_saturated', 0):.3f} | {r.get('a_norm2_mean', 0):.3f} |")
    (OUT / "RESULTS.md").write_text("\n".join(L) + "\n", encoding="utf-8")


def make_figures(rows) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    arms = [a for a in ARCHIVED + NEW if sum(r["arm"] == a for r in rows) == 10]
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.2), sharey=True)
    width = 0.8 / len(arms)
    for ax, p in zip(axes, PLATFORMS):
        for i, a in enumerate(arms):
            vals = [next(r for r in rows if r["platform"] == p and r["mission"] == m and r["arm"] == a)["improvement_percent"] for m in MISSIONS]
            ax.bar(np.arange(len(MISSIONS)) + (i - len(arms) / 2 + 0.5) * width, vals, width, label=LABEL[a])
        ax.axhline(0, color="k", lw=0.8)
        ax.set_xticks(range(len(MISSIONS)), MISSIONS)
        ax.set_title(p)
        ax.grid(axis="y", alpha=0.3)
    axes[0].set_ylabel("error reduction vs classical [%]")
    axes[1].legend(fontsize=7, loc="upper right")
    fig.tight_layout()
    fig.savefig(OUT / "improvement_by_mission.png", dpi=140)
    plt.close(fig)

    new_neural = [a for a in ("lpf-logistic", "latch-replay", "cmg_chi0") if a in arms]
    if new_neural:
        fig, axes = plt.subplots(len(MISSIONS), len(new_neural) + 1, figsize=(4 * (len(new_neural) + 1), 10), sharex=True, sharey=True)
        for c, a in enumerate(("cmg", *new_neural)):
            for m_i, m in enumerate(MISSIONS):
                z = np.load(run_dir("x2", m, a) / "neural_trace_full_rate.npz")
                ax = axes[m_i, c]
                ax.plot(z["t"][::20], z["activity"][::20], lw=0.8)
                ax.set_title(f"x2/{m} — {LABEL[a]}", fontsize=8)
                ax.set_ylim(-0.05, 1.05)
        fig.tight_layout()
        fig.savefig(OUT / "activity_new_arms.png", dpi=120)
        plt.close(fig)


if __name__ == "__main__":
    main()
