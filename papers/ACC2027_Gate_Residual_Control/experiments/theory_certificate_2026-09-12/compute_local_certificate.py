"""Numerical constants for the paper's local stability certificate (Sec. III-D).

Every quantity is computed from the same MuJoCo models, inertias, gains, torque
limits and allocation matrix that the experiments use, through the same code
paths (gra_control.platforms.drone). Nothing here is tuned.

Outputs
  certificate.json          all numbers, both platforms
  certificate_macros.tex    \newcommand values for the paper (copied into the
                            paper folder with --paper-dir)

Paper equations referenced (ACC2027 v9 numbering may shift; labels in brackets):
  gains            [eq:pd]            k_q = 2 j (.) wn^2, k_w = 2 zeta j (.) wn
  torque box       [sec:problem]      l = max(j (.) nu, 1e-6)
  allocation       [eq:allocationmatrix, eq:mixer]
  L_A              [eq:allocbound]    max_D ||H B D B^-1 E||_2 over 16 vertices
  linear model     [eq:localmodel]    A, F with the physical body tensor J
  remainder bound  [eq:localremainder] ||g(x)|| <= L_r ||x||^2
  certificate      [thm:local]        c, r*, dbar_max, beta_max
  latched PES      [eq:constantbasis] pole, time constant, stiffness ratio

Run:  python compute_local_certificate.py --paper-dir <paper folder>
"""
from __future__ import annotations

import argparse
import itertools
import json
import sys
from pathlib import Path

import mujoco
import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
from gra_control.platforms.drone import SPECS, _free_joint, _mixer, torque_limits  # noqa: E402

HERE = Path(__file__).resolve().parent
PLATFORMS = {"x2": 1.0, "cf2-rotor": 1.5}           # actuator_scale, as in the campaign
WN = np.array([4.0, 4.0, 3.5])
ZETA = 0.95
NU = np.array([12.0, 12.0, 10.0])
BETA, ETA, LAMBDA_W, K_E = 0.5, 8e-4, 1e-6, 8.0
H_STEP = 5e-4
G_READOUT, ALPHA_H, V_TH, I_B = 1e5, 50.0, 1.0, 0.75
MISSION_MAX_FREQ = {"roll": 0.7, "full3": 1.0, "hard45": 2.10}  # rad/s, largest component


def quat_to_rot(q):
    w, x, y, z = q
    return np.array([
        [1 - 2*(y*y + z*z), 2*(x*y - w*z), 2*(x*z + w*y)],
        [2*(x*y + w*z), 1 - 2*(x*x + z*z), 2*(y*z - w*x)],
        [2*(x*z - w*y), 2*(y*z + w*x), 1 - 2*(x*x + y*y)],
    ])


def lyap(A, Q):
    """Solve A^T P + P A = -Q by vectorization (6x6, exact to rounding)."""
    n = A.shape[0]
    I = np.eye(n)
    M = np.kron(I, A.T) + np.kron(A.T, I)
    P = np.linalg.solve(M, -Q.reshape(-1, order="F")).reshape(n, n, order="F")
    return 0.5 * (P + P.T)


def skew(v):
    return np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])


def remainder(x, J, Jinv):
    e, w = x[:3], x[3:]
    top = 0.5 * ((np.sqrt(max(1 - e @ e, 0.0)) - 1) * w + np.cross(e, w))
    return np.r_[top, -Jinv @ np.cross(w, J @ w)]


def certificate(A, F, Lr, Q):
    P = lyap(A, Q)
    ev = np.linalg.eigvalsh(P)
    p_min, p_max = ev[0], ev[-1]
    Pn = np.linalg.norm(P, 2)
    b = np.linalg.norm(P @ F, 2)
    lq = np.linalg.eigvalsh(Q)[0]
    r_star = min(lq / (4 * Pn * Lr), 1.0 - 1e-9)
    c = lq - 2 * Pn * Lr * r_star
    dbar = c * r_star / (2 * b) * np.sqrt(p_min / p_max)
    return dict(P=P, p_min=p_min, p_max=p_max, P_norm=Pn, b=b, lam_Q=lq,
                r_star=r_star, c=c, dbar_max=dbar, alpha=c / (2 * p_max))


def analyse(platform, scale, rng):
    spec = SPECS[platform]
    model = mujoco.MjModel.from_xml_path(str(spec.model))
    _, body, _, _ = _free_joint(model)
    j = model.body_inertia[body].copy()                       # j_tune (principal moments)
    J = quat_to_rot(model.body_iquat[body]) @ np.diag(j) @ quat_to_rot(model.body_iquat[body]).T
    mass = float(np.sum(model.body_mass))
    g = abs(float(model.opt.gravity[2]))
    ell = torque_limits(platform, j, model, "model")
    kq, kw = 2 * j * WN**2, 2 * ZETA * j * WN
    act, B, Binv, ctrl = _mixer(model)
    fmax = ctrl[:, 1] * scale

    Kq, Kw, Jinv = np.diag(kq), np.diag(kw), np.linalg.inv(J)
    A = np.block([[np.zeros((3, 3)), 0.5 * np.eye(3)], [-Jinv @ Kq, -Jinv @ Kw]])
    F = np.vstack([np.zeros((3, 3)), Jinv])
    eigA = np.linalg.eigvals(A)

    evJ = np.linalg.eigvalsh(J)
    kappa = evJ[-1] / evJ[0]
    Lr_steven = np.sqrt(2) / 4 + kappa                          # highlighted v7 bound
    Lr_tight = np.sqrt(2) / 4 + (kappa - 1) / 2                 # centred-inertia refinement

    # empirical sup of ||g||/||x||^2 on the unit ball (checks both bounds)
    worst = 0.0
    for _ in range(200_000):
        x = rng.normal(size=6)
        x *= rng.uniform(1e-3, 0.999) / np.linalg.norm(x)
        worst = max(worst, np.linalg.norm(remainder(x, J, Jinv)) / (x @ x))

    E = np.vstack([np.zeros((1, 3)), np.eye(3)])
    H = E.T
    LA = max(np.linalg.norm(H @ B @ np.diag(d) @ Binv @ E, 2)
             for d in itertools.product((0.0, 1.0), repeat=4))

    # rotor feasibility of the whole torque box at hover collective
    f_hover = [Binv @ np.r_[mass * g, np.array(s) * ell] for s in itertools.product((-1, 1), repeat=3)]
    f_hover = np.array(f_hover)
    box_feasible = bool(np.all(f_hover >= 0) and np.all(f_hover <= fmax))

    base = certificate(A, F, Lr_tight, np.eye(6))
    steven = certificate(A, F, Lr_steven, np.eye(6))
    # Q_L shape search (the margin is invariant to scaling Q_L)
    best = base | {"q_e": 1.0}
    for qe in np.logspace(-3, 3, 241):
        cand = certificate(A, F, Lr_tight, np.diag([qe] * 3 + [1.0] * 3))
        if cand["dbar_max"] > best["dbar_max"]:
            best = cand | {"q_e": float(qe)}

    # PD saturation inactive inside the certified ball?
    pd_gain_row = np.sqrt(kq**2 + kw**2)
    pd_unsat = bool(np.all(best["r_star"] * pd_gain_row <= ell))

    ell_norm = np.linalg.norm(ell)
    beta_max = best["dbar_max"] / (LA * ell_norm)
    beta_max_exact_alloc = best["dbar_max"] / ell_norm

    # latched-PES filter and graded-tail regime [eq:constantbasis]
    a_rest = min(1.0, G_READOUT / (1 + np.exp(-ALPHA_H * (I_B - V_TH))))
    regimes = {}
    for name, a2 in (("latched", 6.0), ("tail", 6 * a_rest**2)):
        pole = 1 - LAMBDA_W - ETA * a2
        tau_f = H_STEP / (1 - pole)
        regimes[name] = dict(a_norm2=a2, pole=pole, tau_s=tau_f, corner_rad_s=1 / tau_f,
                             dc_gain=ETA * a2 / (ETA * a2 + LAMBDA_W),
                             leak_mismatch=LAMBDA_W / (ETA * a2))
    lat = regimes["latched"]
    lag = {m: dict(gain=1 / np.sqrt(1 + (w * lat["tau_s"])**2),
                   phase_deg=float(np.degrees(np.arctan(w * lat["tau_s"]))))
           for m, w in MISSION_MAX_FREQ.items()}
    stiffness_ratio = BETA * K_E * ell / kq                     # = beta k_e nu / (2 wn^2)

    return dict(
        platform=platform, mass=mass, j_tune=j, J=J, kappa_J=kappa, ell=ell, ell_norm=ell_norm,
        kq=kq, kw=kw, B=B, f_max=fmax, eig_A_max_real=float(np.max(eigA.real)),
        Lr_steven=Lr_steven, Lr_tight=Lr_tight, Lr_empirical_sup=worst,
        L_A=LA, torque_box_rotor_feasible_at_hover=box_feasible,
        cert_Q_identity=base, cert_Q_identity_steven_Lr=steven, cert_best=best,
        pd_unsaturated_in_ball=pd_unsat, beta_max=beta_max,
        beta_max_if_no_rotor_clip=beta_max_exact_alloc,
        pes_regimes=regimes, latched_lag=lag, stiffness_ratio=stiffness_ratio,
    )


def to_jsonable(o):
    if isinstance(o, dict):
        return {k: to_jsonable(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [to_jsonable(v) for v in o]
    if isinstance(o, np.ndarray):
        return o.tolist()
    if isinstance(o, (np.floating, np.integer)):
        return o.item()
    return o


def sci(x, digits=2):
    m, e = f"{x:.{digits}e}".split("e")
    return f"{m}\\times10^{{{int(e)}}}"


def macros(res):
    out = ["% Generated by experiments/theory_certificate_2026-09-12/compute_local_certificate.py",
           "% Do not edit by hand; rerun the script."]
    for key, tag in (("x2", "X"), ("cf2-rotor", "C")):
        r = res[key]
        b = r["cert_best"]
        vals = {
            "kappaJ": f"{r['kappa_J']:.3f}",
            "LrSteven": f"{r['Lr_steven']:.3f}",
            "Lr": f"{r['Lr_tight']:.3f}",
            "LrEmp": f"{r['Lr_empirical_sup']:.3f}",
            "LA": f"{r['L_A']:.2f}",
            "rstar": sci(b["r_star"]),
            "dbarmax": sci(b["dbar_max"]),
            "betamax": sci(r["beta_max"]),
            "betamaxNoClip": sci(r["beta_max_if_no_rotor_clip"]),
            "qe": f"{b['q_e']:.3g}",
            "EigA": f"{r['eig_A_max_real']:.3f}",
        }
        for name, v in vals.items():
            out.append(f"\\newcommand{{\\cert{tag}{name}}}{{{v}}}")
    lat = res["x2"]["pes_regimes"]["latched"]
    tail = res["x2"]["pes_regimes"]["tail"]
    out += [
        f"\\newcommand{{\\pesPole}}{{{lat['pole']:.4f}}}",
        f"\\newcommand{{\\pesTau}}{{{lat['tau_s']:.3f}}}",
        f"\\newcommand{{\\pesCorner}}{{{lat['corner_rad_s']:.2f}}}",
        f"\\newcommand{{\\pesLeakLatched}}{{{sci(lat['leak_mismatch'], 1)}}}",
        f"\\newcommand{{\\pesLeakTail}}{{{sci(tail['leak_mismatch'], 1)}}}",
        f"\\newcommand{{\\pesTailPole}}{{{tail['pole']:.5f}}}",
        f"\\newcommand{{\\pesTailTau}}{{{tail['tau_s']:.2f}}}",
        f"\\newcommand{{\\lagHardGain}}{{{res['x2']['latched_lag']['hard45']['gain']:.3f}}}",
        f"\\newcommand{{\\lagHardPhase}}{{{res['x2']['latched_lag']['hard45']['phase_deg']:.1f}}}",
        f"\\newcommand{{\\stiffRatioRP}}{{{res['x2']['stiffness_ratio'][0]:.2f}}}",
        f"\\newcommand{{\\stiffRatioY}}{{{res['x2']['stiffness_ratio'][2]:.2f}}}",
    ]
    return "\n".join(out) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--paper-dir", type=Path, default=None)
    args = ap.parse_args()
    rng = np.random.default_rng(20260912)
    res = {p: analyse(p, s, rng) for p, s in PLATFORMS.items()}
    (HERE / "certificate.json").write_text(json.dumps(to_jsonable(res), indent=1), encoding="utf-8")
    tex = macros(res)
    (HERE / "certificate_macros.tex").write_text(tex, encoding="utf-8")
    if args.paper_dir:
        (args.paper_dir / "certificate_macros.tex").write_text(tex, encoding="utf-8")
    for p, r in res.items():
        b = r["cert_best"]
        print(f"\n== {p} ==")
        print(f"J =\n{np.array2string(r['J'], precision=6)}")
        print(f"j_tune={r['j_tune']}, ell={r['ell']}, kappa(J)={r['kappa_J']:.4f}, max Re eig(A)={r['eig_A_max_real']:.4f}")
        print(f"L_r steven={r['Lr_steven']:.4f} tight={r['Lr_tight']:.4f} empirical sup={r['Lr_empirical_sup']:.4f}")
        print(f"L_A={r['L_A']:.4f}; torque box rotor-feasible at hover: {r['torque_box_rotor_feasible_at_hover']}")
        for lab, cc in (("Q=I, tight L_r", r["cert_Q_identity"]), ("Q=I, v7 L_r", r["cert_Q_identity_steven_Lr"]), (f"best q_e={b['q_e']:.3g}", b)):
            print(f"  {lab:18s} r*={cc['r_star']:.4e} c={cc['c']:.4e} b={cc['b']:.4e} dbar_max={cc['dbar_max']:.4e} N m")
        print(f"PD unsaturated in certified ball: {r['pd_unsaturated_in_ball']}")
        print(f"beta_max={r['beta_max']:.4e} (with L_A), {r['beta_max_if_no_rotor_clip']:.4e} (no rotor clipping)")
        print(f"stiffness ratio beta k_e l/k_q = {r['stiffness_ratio']}")
    print("\nPES regimes:", json.dumps(to_jsonable(res["x2"]["pes_regimes"]), indent=1))
    print("latched lag at mission max frequency:", json.dumps(to_jsonable(res["x2"]["latched_lag"]), indent=1))


if __name__ == "__main__":
    main()
