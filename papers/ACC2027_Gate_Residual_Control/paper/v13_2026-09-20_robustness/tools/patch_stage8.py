"""Stage 8 (space + one accuracy fix): tighter noise paragraph, ablation/neuron-family/Nengo paragraphs, abstract, Table II note.

The ablation paragraph claimed to ablate the readout gain G; no G sweep is in this paper (it is listed as future work), so the claim is removed.
"""
import csv
import math
import statistics as st
from pathlib import Path

EXP = Path(r"C:\Research\papers\ACC2027_Gate_Residual_Control\experiments\final_robustness_gating_2026-09-20")
D = Path(r"C:\Research\papers\ACC2027_Gate_Residual_Control\paper\v13_2026-09-20_robustness")
P, TP = D / "ACC2027.tex", D / "tables" / "table_all_restructured.tex"
s, tab = P.read_text(encoding="utf-8"), TP.read_text(encoding="utf-8")

rd = lambda n: list(csv.DictReader((EXP / "results" / n).open()))
noiser, nomr = rd("final_noise.csv"), rd("final_nominal.csv")
noise = {(r["noise_level"], r["platform"], r["mission"], int(r["seed"]), r["label"]): float(r["qerr_true_mean_rad"]) for r in noiser}
noise_rows = {(r["noise_level"], r["platform"], r["mission"], int(r["seed"]), r["label"]): r for r in noiser}
nom = {(r["platform"], r["mission"], r["label"]): float(r["qerr_true_mean_rad"]) for r in nomr}
M = ("roll", "full3", "hard45", "hardstep", "yaw360")
X, C = "x2", "cf2-rotor"
seeds = {lv: sorted({int(r["seed"]) for r in noiser if r["noise_level"] == lv}) for lv in ("moderate", "realistic")}
gm = lambda xs: math.exp(sum(math.log(x) for x in xs) / len(xs))
red = lambda b, c: 100 * (1 - c / b)
mred = lambda lv, p, m, arm="cmg_pes_gated": st.mean(red(noise[(lv, p, m, sd, "pdff_rho3")], noise[(lv, p, m, sd, arm)]) for sd in seeds[lv])
sdev = lambda lv, p, m: st.stdev([red(noise[(lv, p, m, sd, "pdff_rho3")], noise[(lv, p, m, sd, "cmg_pes_gated")]) for sd in seeds[lv]])
floor = lambda lv, p, m: st.mean(noise[(lv, p, m, sd, "pdff_rho3")] for sd in seeds[lv]) * 1e3


def geo_noise(lv, p):
    b = gm([st.mean(noise[(lv, p, m, sd, "pdff_rho3")] for sd in seeds[lv]) for m in M])
    c = gm([st.mean(noise[(lv, p, m, sd, "cmg_pes_gated")] for sd in seeds[lv]) for m in M])
    return red(b, c)


def geo_nom(p):
    return red(gm([nom[(p, m, "pdff_rho3")] for m in M]), gm([nom[(p, m, "cmg_pes_gated")] for m in M]))


def sg(x, nd=1):
    return ("$-$" if x < 0 else "$+$") + f"{abs(x):.{nd}f}"


b5_div = sum(1 for lv in seeds for sd in seeds[lv] if noise[(lv, C, "hardstep", sd, "cmg_pes_gated_b05")] > 2 * noise[(lv, C, "hardstep", sd, "pdff_rho3")])
b5_n = sum(len(seeds[lv]) for lv in seeds)
b5_err = [math.degrees(noise[(lv, C, "hardstep", sd, "cmg_pes_gated_b05")]) for lv in seeds for sd in seeds[lv]]
b5_sat = [float(noise_rows[(lv, C, "hardstep", sd, "cmg_pes_gated_b05")]["rotor_sat_fraction"]) * 100 for lv in seeds for sd in seeds[lv]]
sd_f3h45 = max(sdev(lv, p, m) for lv in seeds for p in (X, C) for m in ("full3", "hard45"))


def sub(tag, old, new, text="s"):
    global s, tab
    body = s if text == "s" else tab
    assert body.count(old) == 1, f"{tag}: expected exactly 1 match, found {body.count(old)}"
    body = body.replace(old, new)
    if text == "s":
        s = body
    else:
        tab = body
    print("ok  ", tag)


# ----------------------------------------------------------------------------------- noise paragraph (tighter)
a = s.index(r"Noise sets a floor under the true error of an already accurate loop.")
b = s.index(r"\label{sec:disturbance}")
new_noise = (
    r"Noise sets a floor under the true error of an accurate loop. On Roll and Yaw360 the PD+ff error rises from $0.34$ and $0.20$ mrad (X2) to "
    + f"${floor('moderate', X, 'roll'):.2f}$ and ${floor('moderate', X, 'yaw360'):.2f}$" + r" mrad at the moderate level, so the residual has nothing left to remove and changes it by "
    + f"{sg(mred('moderate', X, 'roll'))}/{sg(mred('moderate', X, 'yaw360'))}" + r"\% (X2) and " + f"{sg(mred('moderate', C, 'roll'))}/{sg(mred('moderate', C, 'yaw360'))}" + r"\% (CF2); at the realistic level, "
    + f"{sg(mred('realistic', X, 'roll'))}/{sg(mred('realistic', X, 'yaw360'))}" + r"\% and " + f"{sg(mred('realistic', C, 'roll'))}/{sg(mred('realistic', C, 'yaw360'))}" + r"\%. "
    r"Where the baseline error exceeds the floor the benefit survives in every seed (standard deviations below "
    + f"${math.ceil(sd_f3h45 * 10) / 10:.1f}$" + r" pp): at the realistic level Full3 and Hard45 keep "
    + f"${mred('realistic', X, 'full3'):.1f}$ and ${mred('realistic', X, 'hard45'):.1f}\\%$ on X2 and ${mred('realistic', C, 'full3'):.1f}$ and ${mred('realistic', C, 'hard45'):.1f}\\%$ on CF2, "
    + f"so the five-mission geometric mean falls from ${geo_nom(X):.1f}$ and ${geo_nom(C):.1f}\\%$ to ${geo_noise('realistic', X):.1f}$ and ${geo_noise('realistic', C):.1f}\\%$. "
    r"The smaller CF2 share is an authority limit: at $\beta=.5$ CF2 keeps " + f"${mred('realistic', C, 'full3', 'cmg_pes_gated_b05'):.1f}$ and ${mred('realistic', C, 'hard45', 'cmg_pes_gated_b05'):.1f}\\%$"
    + r", but Hardstep diverges in " + f"{b5_div}/{b5_n}" + r" seeds (mean error $" + f"{min(b5_err):.0f}^\\circ$--${max(b5_err):.0f}^\\circ$" + r", rotors at a bound in $" + f"{min(b5_sat):.0f}$--${max(b5_sat):.0f}"
    + r"\%$ of samples), because the requested collective thrust exceeds what the rotors deliver, allocation rather than the torque box binds, and \eqref{eq:gate} does not act. "
    r"Two variants that also block on allocator saturation still diverged on the development seeds, so $\beta=.2$ is used." "\n\n"
)
s = s[:a] + new_noise + s[b:]
print("ok   noise paragraph")

# ----------------------------------------------------------------------------------- ablation
sub("ablation_intro",
    r"We ablate decoder adaptation (PES), conductance modulation ($\chi$), and readout gain ($G$). With decoder mode held fixed,",
    r"We ablate decoder adaptation (PES) and conductance modulation ($\chi$). With decoder mode held fixed,")
sub("ablation_fixed",
    r"""\emph{Fixed versus adaptive decoder.} Holding $W_k=W_0$ keeps CMG dynamics but limits the readout to the paired difference $\bm a^+-\bm a^-$. It yields only modest reductions (Table~\ref{tab:all}) compared to PES.

""",
    r"""\emph{Fixed versus adaptive decoder.} Holding $W_k=W_0$ keeps CMG dynamics but limits the readout to the paired difference $\bm a^+-\bm a^-$, and yields only modest reductions (Table~\ref{tab:all}).

""")
j = s.index("highest instantaneous frequency is $2.1$ rad/s")
assert s[j - 9: j - 3] == "Hard45" and s[j - 2: j] == "s ", repr(s[j - 9: j])      # "Hard45<apostrophe>s "
s = s[: j - 9] + "Hard45's " + s[j:]                                                # plain ASCII apostrophe
print("ok   apostrophe")

# ----------------------------------------------------------------------------------- neuron family
a = s.index(r"The Nengo benchmark spans two models, five missions, and eleven controllers")
b = s.index(r"\subsection{Measurement Noise and Repeated Disturbances}")
new_family = (
    r"The Nengo benchmark spans two models, five missions, and eleven controllers (PD plus fixed/PES variants of CMG, LIF, ALIF, Izhikevich \cite{izhikevich2003}, and LIFRate) that share the same bounded residual and actuator interface; only the neuron dynamics and native-state-to-activity map differ. "
    r"Across the full matrix (figure omitted) two patterns hold. First, PES is the dominant lever in every family: fixed decoders rarely match their PES counterparts, extending Sec.~\ref{sec:ablation} to every basis. "
    r"Second, lower error is not free: some Izhikevich--PES cells reach the smallest error, but at a normalized residual RMS near $0.37$ against $0.12$ for CMG--PES (Table~\ref{tab:all}) and with larger decoder movement. "
    r"Proposition~\ref{prop:pes} explains the flat rows: a silent basis stalls the update. LIF, ALIF and LIFRate units are active in $0.1\%$ of unit-samples on Full3 and Hard45 and under $0.05\%$ on Roll and Yaw360, whereas CMG (resting at $a_j\approx0.37$) and Izhikevich are active in ${\ge}99.9\%$. "
    r"Persistent activity is therefore necessary for effective PES adaptation but does not by itself set effort, since Izhikevich shares it and spends three times the authority: CMG--PES attains comparable tracking at markedly lower realized effort." "\n\n"
)
s = s[:a] + new_family + s[b:]
print("ok   neuron family")

# ----------------------------------------------------------------------------------- Nengo paragraph
a = s.index(r"\paragraph{Nengo realization}")
b = s.index(r"%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%" "\n" r"\section{Proofs}")
new_nengo = (
    r"\paragraph{Nengo realization}" "\n"
    r"In Nengo~4.1.0 a custom \texttt{NeuronType} exposes membrane and gate states and injects current directly, bypassing NEF gain/intercept fitting. The teaching graph adds a one-step latency, so the weight sequences differ; over ten direct/Nengo cases the maximum relative mean-error difference is $2.013\times10^{-6}$: tested numerical agreement, not formal equivalence." "\n\n"
)
s = s[:a] + new_nengo + s[b:]
print("ok   Nengo paragraph")

# ----------------------------------------------------------------------------------- Table II note
sub("table_note2",
    r"$\rho=3$ rows use the saturation-aware gate \eqref{eq:gate} with $\beta=.5$ (X2) and $.2$ (CF2); $^\ddagger$ungated, $\beta=.5$ on X2 and $.05$ on CF2 "
    r"(the $\rho=1$ and fixed-PD rows are ungated). Noise rows: error of the true attitude, seed means, identical noise stream for both arms "
    r"(realistic $0.020$\,rad, $0.050$\,rad\,s$^{-1}$, $10$ seeds; moderate $0.010$, $0.025$, $5$ seeds). ",
    r"$\rho=3$ rows are gated \eqref{eq:gate} with $\beta=.5$ (X2), $.2$ (CF2); $^\ddagger$ungated, $\beta=.5$, $.05$ (the $\rho=1$ and fixed-PD rows are ungated). "
    r"Noise rows: true-attitude error, seed means, same noise stream for both arms (realistic $0.020$\,rad, $0.050$\,rad\,s$^{-1}$, $10$ seeds; moderate $0.010$, $0.025$, $5$). ", text="t")

# ----------------------------------------------------------------------------------- abstract (tighter)
abs_new = (
    "Quadrotor attitude controllers must track time-varying references within coupled rotor-force limits despite modeling uncertainty, measurement noise, and disturbances. "
    "We present an online neuromorphic residual: six continuous membrane-gate (CMG) units generate temporal features and eighteen decoder weights adapt online through prescribed error sensitivity (PES). "
    "The bounded correction augments a saturated quaternion PD controller before rotor-force allocation, with explicit authority bounds, exact recovery of the baseline when disabled, and a saturation-aware gate that stops it from opposing an axis already at its torque limit. "
    f"Against a bandwidth-tuned PD with desired-rate feedforward, the gated residual lowers geometric-mean attitude error by ${geo_nom(X):.1f}\\%$ on X2 and ${geo_nom(C):.1f}\\%$ on CF2 noise-free, and burst-phase error under repeated torque disturbances by $14\\%$ and $6\\%$. "
    f"Under sensor noise it keeps ${min(mred('realistic', p, m) for p in (X, C) for m in ('full3', 'hard45')):.0f}$--${max(mred('realistic', p, m) for p in (X, C) for m in ('full3', 'hard45')):.0f}\\%$ on the multi-axis missions and is neutral or slightly negative where the baseline is already at the noise floor. "
    "The gate cuts the X2 loss on abrupt Hardstep commands from $17\\%$ to $2\\%$ but cannot make it a gain; on CF2, rotor-level saturation under noise limits the usable authority. "
    "An Izhikevich basis lowers fixed-PD error a few points more than CMG at three times the realized effort ($0.37$ versus $0.12$ of the axis bound); ablations point to persistent activity with online decoder adaptation, not conductance modulation, as the principal mechanism."
)
a = s.index(r"\begin{abstract}") + len(r"\begin{abstract}") + 1
b = s.index(r"\end{abstract}")
s = s[:a] + abs_new + "\n" + s[b:]
print("ok   abstract")

P.write_text(s, encoding="utf-8")
TP.write_text(tab, encoding="utf-8")
print("written")
