"""Resolve Dr. Sandoval's five highlighted (purple) edits in the v34 manuscript, using the frame-aligned re-run.

Reads  C:/Users/gandhico/Downloads/ACC2027_SPS (2).tex   (never modified)
Writes ACC2027_SPS.tex next to this script. Every edit is an exact, single-occurrence replacement (assert-checked).
Numbers come from frame_aligned_2026-10-02 (final_nominal.csv, a5_controllers) vs the published tree:
  primary geo reduction X2 37.297 -> 37.358, CF2 22.421 -> 22.495; largest per-mission change 0.56 pp (X2 Hard45);
  LQR/PID+ff/SMC/MPC geo changes -0.19/+0.07, +0.01/+0.08, +0.22/+0.20, -0.13/+0.07 pp (X2/CF2).
Freeze-PES screen: results_hardstep-development.csv, X2 Hardstep, noise-free, seed 1, beta .5, load 1: -2.1 % (gate: -2.0 %).
"""
from pathlib import Path

SRC = Path(r"C:\Users\gandhico\Downloads\ACC2027_SPS (2).tex")
OUT = Path(__file__).resolve().parent / "ACC2027_SPS.tex"

EDITS = [
    # 1. allocation matrix: thrust row verified against src/gra_control/platforms/drone.py::_mixer
    #    (B = [1; p_y; -p_x; kappa]); highlight removed, content unchanged.
    (r"\textcolor{purple}{1} & \textcolor{purple}{1} & \textcolor{purple}{1} & \textcolor{purple}{1} \\",
     r"1 & 1 & 1 & 1 \\"),
    # 2. Eq. (15): keep the frame-aligned law, disclose what the reported runs implement and the re-run effect.
    ("obtained by replacing $\\bm\\omega$ with the \\textcolor{purple}{frame-aligned} rate-tracking error\n"
     "\\textcolor{purple}{$\\bm\\omega_e$}\n"
     "\\begin{equation}\n"
     " \\bm u_0^{\\rm ff}=\\sat_{\\bm\\ell}\\bigl(-\\bm k_q\\odot\\bm e_q-\\bm k_\\omega\\odot\\textcolor{purple}{\\bm\\omega_e}\\bigr),\n"
     " \\label{eq:pdff}\n"
     "\\end{equation}\n",
     "obtained by replacing $\\bm\\omega$ with the frame-aligned rate-tracking error $\\bm\\omega_e$ of \\eqref{eq:errkin}\n"
     "\\begin{equation}\n"
     " \\bm u_0^{\\rm ff}=\\sat_{\\bm\\ell}\\bigl(-\\bm k_q\\odot\\bm e_q-\\bm k_\\omega\\odot\\bm\\omega_e\\bigr).\n"
     " \\label{eq:pdff}\n"
     "\\end{equation}\n"
     "The reported runs damp $\\bm\\omega-\\bm\\omega_d$, which differs from $\\bm\\omega_e$ by at most $\\theta_q\\|\\bm\\omega_d\\|$; "
     "with $\\bm\\omega_e$ the primary result of Sec.~\\ref{sec:baselines} becomes $37.4\\%/22.5\\%$ and the LQR, PID+ff, SMC, "
     "and MPC results change by at most $0.22$\\,pp.\n"),
    # 3. Eq. (24): omega_e is consistent with (15); k_omega^* = 0 in every reported run (Table I), so no result depends on it.
    ("weighting attitude and rate error, respectively\n\\begin{align}",
     "weighting attitude and rate error, respectively (all reported runs use $k_\\omega^*=0$, so $\\bm y_k^*$ depends on "
     "$\\bm e_{q,k}$ only)\n\\begin{align}"),
    (r"-k_\omega^*\textcolor{purple}{\bm\omega_{e,k}}),\\",
     r"-k_\omega^*\bm\omega_{e,k}),\\"),
    # 4. Anti-windup sentence: the gate is output-only (run_izh_robustness.py: "PES target/error/update are never
    #    masked"), so PES keeps adapting while blocked; the freeze-PES variant was screened and not adopted.
    (r"\textcolor{purple}{Because PES uses the ungated residual $\bm s_k$ rather than the physically applied $\tilde s_{k,i}$, "
     r"this provides an implicit anti-windup mechanism: the network satisfies its local learning objective and stops "
     r"updating even if the physical plant remains saturated.}",
     r"Because PES uses the ungated $\bm s_k$, the mask never enters $\bm\varepsilon_k$ and cannot by itself wind up the "
     r"decoder; PES still adapts on a blocked axis (Sec.~\ref{sec:failure}), and freezing those rows gave the same X2 "
     r"Hardstep result in development ($-2.1\%$ vs.\ $-2.0\%$)."),
    # 5. Contraction condition: uniqueness of the frozen-v gate equilibrium for every v_j holds iff alpha_h*gamma <= 4.
    (r"Since $\alpha_h\gamma=100>4$, the gate is bistable\textcolor{purple}{; a strictly graded, non-latching state "
     r"mathematically requires the contraction condition $\alpha_h\gamma<4$ (since $\max \sigma'(x)=1/4$). Thus,} for "
     r"frozen $v_j$ its equilibria fold at $v_j\approx0.888$ (onset) and $v_j\approx-0.888$ (release).",
     r"Since $\max\sigma'=1/4$, the frozen-$v_j$ gate equilibrium $r_j=\sigma(\alpha_h(v_j-v_{\rm th}+\gamma r_j))$ is "
     r"unique (graded, non-latching) for every $v_j$ iff $\alpha_h\gamma\le4$; here $\alpha_h\gamma=100$, so the gate is "
     r"bistable, with folds at $v_j\approx0.888$ (onset) and $-0.888$ (release)."),
]


def main():
    s = SRC.read_text(encoding="utf-8")
    for old, new in EDITS:
        n = s.count(old)
        assert n == 1, f"expected one match, found {n}: {old[:80]!r}"
        s = s.replace(old, new)
    assert "textcolor{purple}" not in s, "a purple highlight was left unresolved"
    OUT.write_text(s, encoding="utf-8", newline="")
    print("wrote", OUT)


if __name__ == "__main__":
    main()
