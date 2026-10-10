"""Emit the two new LaTeX tables for paper v10: the baseline ladder and the compact neuron-family summary."""
from __future__ import annotations

import collections
import csv
import statistics as st
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
NF = Path(r"C:\Research\papers\ACC2027_Gate_Residual_Control\experiments\nengo_nef_replication_2026-08-29"
          r"\results\neuron_family_compiled\neuron_family_results.csv")
MISSIONS = ("roll", "full3", "hard45", "hardstep", "yaw360")
ML = {"roll": "Roll", "full3": "Full3", "hard45": "Hard45", "hardstep": "Hardstep", "yaw360": "Yaw360"}

rows = {(r["platform"], r["mission"]): r for r in csv.DictReader((HERE / "master_table.csv").open(encoding="utf-8"))}


def geo(v):
    return float(np.exp(np.mean([np.log(x) for x in v])))


def mr(x):                       # rad -> mrad, table formatting
    v = 1e3 * x
    return f"{v:.2f}" if v >= 0.1 else f"{v:.3f}"


L = [r"\begin{table}[t]", r"\caption{Baseline ladder on the same ten cells: reference-rate feedforward"
     r" \eqref{eq:pdff} at the Table~\ref{tab:mujoco} bandwidth and at the swept optimum $\rho=3$, each without"
     r" and with the CMG--PES residual. Errors in $10^{-3}$\,rad; $\Delta$ is the residual's reduction over the"
     r" baseline in the same block; geo is the geometric mean over the five missions.}",
     r"\label{tab:ladder}\centering\scriptsize", r"\setlength{\tabcolsep}{2.6pt}",
     r"\begin{tabular}{@{}llrrrrrr@{}}", r"\toprule",
     r"&&\multicolumn{3}{c}{PD+ff, $\rho=1$}&\multicolumn{3}{c}{PD+ff, $\rho=3$ (tuned)}\\",
     r"\cmidrule(lr){3-5}\cmidrule(l){6-8}",
     r"Model&Mission&base&+CMG&$\Delta$[\%]&base&+CMG&$\Delta$[\%]\\\midrule"]
for p, tag in (("x2", "X2"), ("cf2-rotor", "CF2")):
    for i, m in enumerate(MISSIONS):
        r = rows[(p, m)]
        lead = tag if i == 0 else ""
        L.append(f"{lead}&{ML[m]}&{mr(float(r['PDff_1x']))}&{mr(float(r['CMG_on_PDff_1x']))}&"
                 f"{float(r['CMGonff1x_vs_ff1x_pct']):.1f}&{mr(float(r['PDff_3x']))}&"
                 f"{mr(float(r['CMG_on_PDff_3x']))}&{float(r['CMGonff3x_vs_ff3x_pct']):.1f}\\\\")
    g = {k: geo([float(rows[(p, m)][k]) for m in MISSIONS])
         for k in ("PDff_1x", "CMG_on_PDff_1x", "PDff_3x", "CMG_on_PDff_3x")}
    rule = r"\midrule" if p == "x2" else r"\bottomrule"
    L.append(f"&\\emph{{geo}}&{mr(g['PDff_1x'])}&{mr(g['CMG_on_PDff_1x'])}&"
             f"{100 * (1 - g['CMG_on_PDff_1x'] / g['PDff_1x']):.1f}&{mr(g['PDff_3x'])}&{mr(g['CMG_on_PDff_3x'])}&"
             f"{100 * (1 - g['CMG_on_PDff_3x'] / g['PDff_3x']):.1f}\\\\{rule}")
L += [r"\end{tabular}", r"\end{table}"]
(HERE / "tex_table_ladder.tex").write_text("\n".join(L) + "\n", encoding="utf-8")

nf = collections.defaultdict(list)
for r in csv.DictReader(NF.open(encoding="utf-8")):
    nf[r["family_mode"]].append(r)
N = [r"\begin{table}[t]", r"\caption{Nengo neuron-family benchmark, mean over ten cells (two models, five"
     r" missions): error reduction over the shared PD baseline for a fixed and a PES decoder, PES residual"
     r" effort as RMS fraction of the per-axis limit, and the fraction of unit-samples with $|a_j|>10^{-9}$.}",
     r"\label{tab:family}\centering\footnotesize", r"\setlength{\tabcolsep}{4pt}",
     r"\begin{tabular}{@{}lrrrr@{}}", r"\toprule",
     r"Family&fixed [\%]&PES [\%]&PES effort&active\\\midrule"]
for fam, tag in (("cmg", "CMG"), ("izhikevich", "Izhikevich"), ("lif", "LIF"), ("alif", "ALIF"),
                 ("lifrate", "LIFRate")):
    f, p_ = nf[f"{fam}-fixed"], nf[f"{fam}-pes"]
    N.append(f"{tag}&{st.mean(float(r['improvement_pct']) for r in f):.1f}&"
             f"{st.mean(float(r['improvement_pct']) for r in p_):.1f}&"
             f"{st.mean(float(r['residual_utilization_rms']) for r in p_):.3f}&"
             f"{st.mean(float(r['activity_occupancy_fraction']) for r in p_):.3f}\\\\")
N += [r"\bottomrule", r"\end{tabular}", r"\end{table}"]
(HERE / "tex_table_family.tex").write_text("\n".join(N) + "\n", encoding="utf-8")
print("\n".join(L))
print()
print("\n".join(N))
