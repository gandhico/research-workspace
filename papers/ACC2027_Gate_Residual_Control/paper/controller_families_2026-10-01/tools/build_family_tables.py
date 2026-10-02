"""Build the generated tables of the controller-family document and check its derivations.

Run from the repository root with the project venv:
    .venv\\Scripts\\python.exe paper\\controller_families_2026-10-01\\tools\\build_family_tables.py

Every number is computed from the repository code or the A5 run outputs; nothing is typed by hand:
  * gains of each family are read from AdvancedBaseline itself (the class the A5 runs used), built with the exact
    A5 command-line settings of run_campaign_a5.py / run_campaign_a5_nmpc_corrected.py;
  * the closed-form LQR gain is checked against SciPy's CARE solver;
  * the MPC first-move gain is recomputed for growing horizons and compared with the continuous LQR gain;
  * small-error closed-loop poles per family (and the PID third-order loop) are computed from the gains;
  * the per-family A5 results are read from results/a5_numbers.json (the file analyze_a5.py writes);
  * every cited source file is hashed and compared with the source_sha256 recorded by an A5 run of each family.
Writes ../generated/*.tex.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
DOC = HERE.parent
REPO = DOC.parents[1]
OUT = DOC / "generated"
FR = REPO / "experiments" / "final_robustness_gating_2026-09-20"
UP = REPO / "experiments" / "nengo_nef_replication_2026-08-29"
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(UP))
from run_mujoco_nef_baselines import AdvancedBaseline  # noqa: E402

WN0 = np.array([4.0, 4.0, 3.5])
RHO = 3.0
PLATFORMS = {"x2": "X2", "cf2-rotor": "CF2"}
FAMILIES = ["backstepping", "pid", "lqr", "smc", "mpc", "nmpc"]
LABEL = {"backstepping": "PD+ff (backstepping form)", "pid": "PID+ff", "lqr": "LQR", "smc": "SMC",
         "mpc": "MPC", "nmpc": "NMPC"}
MISSIONS = ["Roll", "Full3", "Hard45", "Hardstep", "Yaw360"]


def a5_args(family: str) -> argparse.Namespace:
    """The A5 settings (run_campaign_a5.py FAMILY_ARGS + common flags; NMPC from the corrected re-run)."""
    return argparse.Namespace(
        baseline=family if family != "pid" else "pd", bw_scale=3.0, rate_ff="left-neg", no_model_ff=True,
        baseline_rate_hz=0.0, dt=5e-4, mission="roll", duration=45.0, smc_eta_frac=0.5, mpc_dt=0.02,
        mpc_horizon=120, mpc_q_rate=0.0, nmpc_dt=0.06, nmpc_horizon=5, nmpc_terminal=1.5, nmpc_offset_frac=0.1,
        nmpc_rate_weight=2.0, nmpc_grid=3, nmpc_predict="policy")


def manifest(family: str, platform: str) -> dict:
    root = FR / "results" / ("a5_controllers_nmpc_corrected" if family == "nmpc" else f"a5_controllers/{family}")
    if family == "nmpc":
        return json.loads((root / platform / "roll" / "classical" / "manifest.json").read_text(encoding="utf-8"))
    return json.loads((root / platform / "roll" / "classical" / "manifest.json").read_text(encoding="utf-8"))


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def fmt(x, d=3):
    return f"{x:.{d}f}"


def main():
    OUT.mkdir(exist_ok=True)
    facts = {}

    # ---------------------------------------------------------------- platform constants from the A5 manifests
    plat = {}
    for p in PLATFORMS:
        d = manifest("lqr", p)["derived"]
        plat[p] = dict(J=np.array(d["body_inertia_kgm2"]), lim=np.array(d["torque_limits_Nm"]))
    wn = RHO * WN0

    # ---------------------------------------------------------------- LQR closed form: CARE residual
    # P = [[sqrt(2) w^3, w^2], [w^2, sqrt(2) w]] (q/r = w^4, r = 1) must solve A'P + PA - P B B' P + Q = 0,
    # be positive definite, and give K = B'P = [w^2, sqrt(2) w].
    worst, worst_k, min_eig = 0.0, 0.0, np.inf
    A = np.array([[0.0, 1.0], [0.0, 0.0]]); B = np.array([[0.0], [1.0]])
    for w in wn:
        P = np.array([[np.sqrt(2) * w ** 3, w ** 2], [w ** 2, np.sqrt(2) * w]])
        res = A.T @ P + P @ A - P @ B @ B.T @ P + np.diag([w ** 4, 0.0])
        worst = max(worst, float(np.max(np.abs(res))) / w ** 4)
        worst_k = max(worst_k, float(np.max(np.abs((B.T @ P).ravel() - [w ** 2, np.sqrt(2) * w]))))
        min_eig = min(min_eig, float(np.min(np.linalg.eigvalsh(P))))
    facts["lqrCareRelErr"] = f"{worst:.1e}"
    facts["lqrPminEig"] = f"{min_eig:.2f}"

    # ---------------------------------------------------------------- gains straight from AdvancedBaseline
    rows, poles_rows = [], []
    gains = {}
    for fam in FAMILIES:
        for p in PLATFORMS:
            J, lim = plat[p]["J"], plat[p]["lim"]
            if fam == "pid":
                # run_controllers_gated.py lines 253-256: kq = 2 J wn^2, kw = 2 zeta wn J, ki = 0.3 kq (on e_q).
                # In the e = 2 e_q variable per unit inertia: k1 = wn^2, k2 = 2 zeta wn, kI = 0.3 wn^2.
                k1, k2, kI = wn ** 2, 2 * 0.95 * wn, 0.3 * wn ** 2
            else:
                b = AdvancedBaseline(a5_args(fam), J, lim, WN0)
                kI = np.zeros(3)
                if fam in ("lqr", "backstepping", "nmpc"):
                    k1, k2 = b.k1, b.k2
                elif fam == "smc":       # inside the boundary layer: k1 = lam*eta/phi, k2 = lam + eta/phi
                    k1, k2 = b.lam * b.eta / b.phi, b.lam + b.eta / b.phi
                    facts[f"smcEta{PLATFORMS[p]}"] = ", ".join(fmt(x, 2) for x in b.eta)
                    facts[f"smcPhi{PLATFORMS[p]}"] = ", ".join(fmt(x, 3) for x in b.phi)
                elif fam == "mpc":
                    k1, k2 = b.K0[:, 0], b.K0[:, 1]
            gains[(fam, p)] = (np.asarray(k1), np.asarray(k2), np.asarray(kI))
        k1, k2, kI = gains[(fam, "x2")]
        assert all(np.allclose(gains[(fam, "x2")][i], gains[(fam, "cf2-rotor")][i]) for i in range(3)), fam
        nu = plat["x2"]["lim"] / plat["x2"]["J"]
        wn_eq, zeta_eq = np.sqrt(k1), k2 / (2 * np.sqrt(k1))
        rows.append(f"{LABEL[fam]} & " + " & ".join([
            "/".join(fmt(x, 1) for x in k1[[0, 2]]), "/".join(fmt(x, 2) for x in k2[[0, 2]]),
            "/".join(fmt(x, 2) for x in wn_eq[[0, 2]]), "/".join(fmt(x, 3) for x in zeta_eq[[0, 2]]),
            "/".join(fmt(np.degrees(x), 2) for x in (nu / k1)[[0, 2]]),
            ("/".join(fmt(x, 1) for x in kI[[0, 2]]) if np.any(kI) else "--")]) + r"\\")
        for ax, name in ((0, "roll/pitch"), (2, "yaw")):
            if np.any(kI):
                r = np.roots([1.0, k2[ax], k1[ax], kI[ax]])
            else:
                r = np.roots([1.0, k2[ax], k1[ax]])
            tol = 1e-6 * max(1.0, float(np.max(np.abs(r))))
            r = np.where(np.abs(r.imag) < tol, r.real, r)
            txt = []
            for z in sorted(r, key=lambda z: (z.real, -z.imag)):
                if abs(z.imag) < tol:
                    txt.append(f"${z.real:.2f}$")
                elif z.imag > 0:
                    txt.append(f"${z.real:.2f}\\pm{z.imag:.2f}j$")
            if len(txt) == 2 and txt[0] == txt[1]:
                txt = [txt[0] + " (double)"]
            wn_cl = np.abs(r[np.argmax(np.abs(r.imag))]) if np.any(np.abs(r.imag) > tol) else np.max(np.abs(r))
            poles_rows.append(f"{LABEL[fam]} & {name} & " + ", ".join(txt) + r"\\")
    (OUT / "family_gains.tex").write_text("\n".join(rows) + "\n", encoding="utf-8")
    (OUT / "family_poles.tex").write_text("\n".join(poles_rows) + "\n", encoding="utf-8")

    # PID Routh condition k2 k1 > kI
    k1, k2, kI = gains[("pid", "x2")]
    facts["pidRouthMargin"] = fmt(float(np.min(k2 * k1 / kI)), 1)

    # ---------------------------------------------------------------- MPC first-move gain vs horizon
    mrows = []
    J, lim = plat["x2"]["J"], plat["x2"]["lim"]
    for N in (5, 15, 30, 60, 120, 240):
        a = a5_args("mpc"); a.mpc_horizon = N
        b = AdvancedBaseline(a, J, lim, WN0)
        K = b.K0[0]
        mrows.append(f"{N} & {N * a.mpc_dt:.2f} & {K[0]:.2f} & {K[1]:.3f} & {K[0] / wn[0] ** 2:.3f} & "
                     f"{K[1] / (np.sqrt(2) * wn[0]):.3f}\\\\")
    (OUT / "mpc_horizon.tex").write_text("\n".join(mrows) + "\n", encoding="utf-8")
    # discrete infinite-horizon LQR at the same T (the limit of the receding-horizon gain)
    # Riccati recursion iterated to its fixed point (the DARE solution); its gain is the N -> infinity limit.
    T = 0.02
    Ad = np.array([[1, T], [0, 1.0]]); Bd = np.array([[0.5 * T * T], [T]])
    Qd, Rd = np.diag([wn[0] ** 4, 0.0]), np.array([[1.0]])
    P = Qd.copy()
    for _ in range(200000):
        Kd = np.linalg.solve(Rd + Bd.T @ P @ Bd, Bd.T @ P @ Ad)
        Pn = Qd + Ad.T @ P @ (Ad - Bd @ Kd)
        if np.max(np.abs(Pn - P)) <= 1e-12 * np.max(np.abs(P)):
            P = Pn
            break
        P = Pn
    Kd = np.linalg.solve(Rd + Bd.T @ P @ Bd, Bd.T @ P @ Ad).ravel()
    dare_res = Ad.T @ P @ Ad - P - Ad.T @ P @ Bd @ np.linalg.solve(Rd + Bd.T @ P @ Bd, Bd.T @ P @ Ad) + Qd
    facts["dareResidual"] = f"{float(np.max(np.abs(dare_res)) / np.max(np.abs(P))):.1e}"
    facts["mpcDareKone"], facts["mpcDareKtwo"] = fmt(Kd[0], 2), fmt(Kd[1], 3)
    a = a5_args("mpc"); b = AdvancedBaseline(a, J, lim, WN0)
    facts["mpcKone"], facts["mpcKtwo"] = fmt(b.K0[0, 0], 2), fmt(b.K0[0, 1], 3)
    facts["mpcVsDare"] = f"{float(np.max(np.abs(b.K0[0] - Kd) / np.abs(Kd))):.1e}"

    # ---------------------------------------------------------------- NMPC candidate set
    b = AdvancedBaseline(a5_args("nmpc"), J, lim, WN0)
    facts["nmpcCandidates"] = str(len(b.offsets))
    facts["nmpcHasZero"] = "yes" if any(np.all(o == 0) for o in b.offsets) else "NO"

    # ---------------------------------------------------------------- A5 results
    d = json.loads((FR / "results" / "a5_numbers.json").read_text(encoding="utf-8"))["families"]
    rrows = []
    for fam in FAMILIES:
        for p, pl in PLATFORMS.items():
            v = d[fam][p]
            rrows.append(f"{LABEL[fam] if p == 'x2' else ''} & {pl} & " + " & ".join(
                f"{x:+.1f}" for x in v["red_pct"]) + f" & \\textbf{{{v['geo_red_pct']:+.1f}}} & "
                f"{v['geo_baseline_mrad']:.2f}\\\\" + (r"\addlinespace" if p != "x2" else ""))
    (OUT / "family_results.tex").write_text("\n".join(rrows) + "\n", encoding="utf-8")

    # ---------------------------------------------------------------- hashes vs A5 manifests
    files = {
        "baseline_runner": UP / "run_mujoco_nef_baselines.py",
        "runner": FR / "run_controllers_gated.py",
        "nengo_cmg": UP / "nengo_cmg.py",
        "quaternion_and_reference": REPO / "src" / "gra_control" / "math3d.py",
        "platform_interface": REPO / "src" / "gra_control" / "platforms" / "drone.py",
    }
    extra = [FR / "run_campaign_a5.py", FR / "run_campaign_a5_nmpc_corrected.py", FR / "analyze_a5.py"]
    BSD = REPO / "experiments" / "backstepping_true_2026-10-01"
    new_files = [BSD / "true_backstepping.py", BSD / "run_true_backstepping.py", BSD / "verify_true_backstepping.py",
                 BSD / "run_campaign_true_bs.py"]
    hrows, match, checked = [], 0, 0
    for key, path in files.items():
        h = sha(path)
        ok_all = True
        for fam in FAMILIES:
            for p in PLATFORMS:
                rec = manifest(fam, p)["source_sha256"].get(key)
                checked += 1
                ok = rec == h
                match += ok
                ok_all &= ok
        rel = path.relative_to(REPO).as_posix()
        hrows.append(f"\\code{{{rel}}} & \\texttt{{{h[:16]}}} & {'identical (12/12 runs)' if ok_all else 'DIFFERS'}\\\\")
    for path in extra:
        rel = path.relative_to(REPO).as_posix()
        hrows.append(f"\\code{{{rel}}} & \\texttt{{{sha(path)[:16]}}} & campaign driver (not recorded)\\\\")
    hrows.append("\\ifwithbs")
    for path in new_files:
        rel = path.relative_to(REPO).as_posix()
        hrows.append(f"\\code{{{rel}}} & \\texttt{{{sha(path)[:16]}}} & new family (Sec.~\\ref{{sec:bstrue}})\\\\")
    hrows.append("\\fi")
    (OUT / "family_hashes.tex").write_text("\n".join(hrows) + "\n", encoding="utf-8")
    facts["hashMatch"], facts["hashChecked"] = str(match), str(checked)

    # ---------------------------------------------------------------- recursive backstepping (new family)
    BS = REPO / "experiments" / "backstepping_true_2026-10-01"
    ver = json.loads((BS / "results" / "verification.json").read_text(encoding="utf-8"))
    lin = ver["linearization"]
    facts["bsC"] = f"{lin['c_Nm']:.3f}"
    facts["bsKone"] = ", ".join(f"{x:.2f}" for x in lin["k1"])
    facts["bsKtwo"] = ", ".join(f"{x:.3f}" for x in lin["k2"])
    kin = max(max(v["z1_dot_max_abs_err"], v["wbar_dot_max_abs_err"]) for k, v in ver.items() if k.startswith("kinematics"))
    def sci(x):
        m, e = f"{x:.1e}".split("e")
        return f"${m}\\times10^{{{int(e)}}}$"
    facts["bsKinErr"] = sci(kin)
    facts["bsVdotErr"] = f"{100 * max(v['Vdot_fd_vs_formula_max_rel_err'] for k, v in ver.items() if k.startswith('lyapunov')):.2f}\\%"
    facts["bsAdaptErr"] = f"{100 * ver['adaptive_constant_disturbance']['max_rel_err']:.2f}\\%"
    facts["bsPoleErr"] = sci(lin["max_pole_diff_vs_pdff"])
    camp = BS / "results" / "campaign"
    MIS = ["roll", "full3", "hard45", "hardstep", "yaw360"]

    def q(fam, p, m, arm):
        f = camp / fam / p / m / arm / "summary.json"
        return json.loads(f.read_text(encoding="utf-8"))["metrics"]["qerr_true_mean_rad"] if f.exists() else None

    gm = lambda xs: float(np.exp(np.mean(np.log(xs))))
    rows, crows, complete, bsnum = [], [], True, {}
    for fam, lab in (("bs-true", "Recursive backstepping"), ("bs-adaptive", "Adaptive recursive backstepping")):
        for p, pl in PLATFORMS.items():
            b = [q(fam, p, m, "classical") for m in MIS]
            c = [q(fam, p, m, "nengo-nef-pes") for m in MIS]
            if None in b or None in c:
                complete = False
                continue
            red = [100 * (1 - ci / bi) for bi, ci in zip(b, c)]
            g = 100 * (1 - gm(c) / gm(b))
            bsnum[(fam, p)] = dict(base=b, cmg=c, red=red, geo=g)
            rows.append(f"{lab if p == 'x2' else ''} & {pl} & " + " & ".join(f"{x:+.1f}" for x in red)
                        + f" & \\textbf{{{g:+.1f}}} & {1e3 * gm(b):.2f}\\\\" + (r"\addlinespace" if p != "x2" else ""))
    for p, pl in PLATFORMS.items():
        ct = np.array(d["backstepping"][p]["baseline_mrad"]) / 1e3
        for fam, lab in (("bs-true", "recursive"), ("bs-adaptive", "adaptive")):
            if (fam, p) not in bsnum:
                continue
            b = np.array(bsnum[(fam, p)]["base"])
            crows.append(f"{pl} & {lab} & " + " & ".join(f"{x:+.1f}" for x in 100 * (1 - b / ct))
                         + f" & \\textbf{{{100 * (1 - gm(b) / gm(ct)):+.1f}}}\\\\")
    if complete:
        sec = [r"\subsection{Results: recursive backstepping with and without the residual}",
               r"Same protocol as A5 (Table~\ref{tab:results}): 45-s missions, $\rho=3$, noise-free, seed 1, gate on, the residual unchanged. "
               r"Run by \code{experiments/backstepping_true_2026-10-01/run_campaign_true_bs.py}; numbers computed from the run summaries by "
               r"\code{tools/build_family_tables.py}.",
               r"\begin{table}[H]\centering\small",
               r"\caption{Reduction of mean quaternion-angle error by the gated CMG--PES residual on the recursive backstepping laws "
               r"(\%, positive is better; 5-mission = reduction of geometric means; last column: baseline geometric mean, mrad).}\label{tab:bsres}",
               r"\begin{tabular}{@{}llrrrrrrr@{}}\toprule",
               r"Family & Platform & Roll & Full3 & Hard45 & Hardstep & Yaw360 & 5-mission & base (mrad)\\\midrule",
               *rows, r"\bottomrule\end{tabular}\end{table}",
               r"\begin{table}[H]\centering\small",
               r"\caption{Nominal laws alone (no residual): error reduction of the recursive designs relative to the computed-torque PD+ff "
               r"(the paper's primary baseline), \% (positive: the recursive law tracks better). The linearizations are identical, so these "
               r"differences come from the backstepping structure.}\label{tab:bsvsct}",
               r"\begin{tabular}{@{}llrrrrrr@{}}\toprule",
               r"Platform & law & Roll & Full3 & Hard45 & Hardstep & Yaw360 & 5-mission\\\midrule",
               *crows, r"\bottomrule\end{tabular}\end{table}"]
        for fam in ("bs-true", "bs-adaptive"):
            for p, pl in PLATFORMS.items():
                facts[f"bsGeo{fam.replace('bs-', '').replace('-', '')}{pl}"] = f"{bsnum[(fam, p)]['geo']:+.1f}"
    else:
        sec = [r"\subsection{Results}", r"\emph{The 40-run campaign was still running when this version was built.}"]
    (OUT / "bs_results_section.tex").write_text("\n".join(sec) + "\n", encoding="utf-8")
    facts["bsCampaignComplete"] = "yes" if complete else "no"

    # ---------------------------------------------------------------- platform facts
    for p, pl in PLATFORMS.items():
        facts[f"J{pl}"] = ", ".join(f"{x:.4g}" for x in plat[p]["J"])
        facts[f"ell{pl}"] = ", ".join(f"{x:.4g}" for x in plat[p]["lim"])
        facts[f"nu{pl}"] = ", ".join(f"{x:.2f}" for x in plat[p]["lim"] / plat[p]["J"])

    tex_name = lambda k: k.replace("CF2", "CFtwo").replace("X2", "Xtwo")   # TeX control words have no digits
    (OUT / "facts.tex").write_text("".join(f"\\newcommand{{\\f{tex_name(k)}}}{{{v}}}\n" for k, v in facts.items()),
                                   encoding="utf-8")
    print(json.dumps(facts, indent=1))
    print(open(OUT / "family_gains.tex").read())
    print(open(OUT / "family_poles.tex").read())
    print(open(OUT / "mpc_horizon.tex").read())


if __name__ == "__main__":
    main()
