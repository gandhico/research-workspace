"""Build analysis/report/index.html from the report CSVs and figures (numbers are never hand-typed)."""
from __future__ import annotations

import csv
import html
from pathlib import Path

HERE = Path(__file__).resolve().parent
REP = HERE / "analysis" / "report"
PLATFORMS = (("x2", "X2"), ("cf2-rotor", "CF2-rotor"))
MISSIONS = ("roll", "full3", "hard45", "hardstep", "yaw360")
DEFS = {
    "CMG (paper, G=1e5, chi=1)": "Canonical coupled membrane–gate unit, Table I parameters. Reference.",
    "LPF + static logistic": "a = clip(G·σ(α(LPF<sub>τ</sub>(I) − v<sub>th</sub>)), 0, 1). Same τ, α, v<sub>th</sub>, G as CMG; no gate state, no γr threshold feedback, no conductance.",
    "CMG chi=0": "Canonical CMG with input-dependent conductance switched off (χ = 0).",
    "Latch replay": "a<sub>j</sub> = 0.3728 until unit j's recorded CMG latch time (first r &gt; 0.5), then 1. Open-loop two-level schedule.",
    "CMG G=1e3": "Canonical CMG with readout gain G = 10³ (preregistered development rule).",
    "CMG G=1": "Canonical CMG with readout gain G = 1, so a = r.",
    "Constant-rest (a=0.3728)": "a ≡ 0.3728 on all six units, CMG's resting readout.",
    "Constant-one (archived)": "a ≡ 1 on all six units; archived NumPy adapter (same-step PES).",
    "Constant-one (Nengo PES order)": "a ≡ 1 with the Nengo one-step PES ordering; checks the ordering effect.",
    "Static paired (archived)": "a = clip(I / (I<sub>b</sub> + I<sub>g</sub>), 0, 1); no temporal state.",
}
VERDICT_CLASS = {"reference": "ref", "reproduces CMG": "good", "fails": "bad", "partial": "mid"}


def rows():
    with (REP / "summary_table.csv").open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def num(v: str) -> str:
    x = float(v)
    return f"{x:+.1f}"


def cell(v: str, ref: str | None) -> str:
    x = float(v)
    cls = "pos" if x > 0.05 else "neg" if x < -0.05 else "zero"
    better = ref is not None and x > float(ref) + 3.0
    return f'<td class="n {cls}{" up" if better else ""}">{x:+.1f}</td>'


def main() -> None:
    R = rows()
    cmg = R[0]
    agg = []
    for r in R:
        v = r["verdict"]
        agg.append(
            f'<tr><th scope="row">{html.escape(r["arm"])}</th>'
            f'<td class="n strong">{float(r["x2:geomean"]):.2f}%</td>'
            f'<td class="n strong">{float(r["cf2-rotor:geomean"]):.2f}%</td>'
            f'<td><span class="pill {VERDICT_CLASS[v]}">{html.escape(v)}</span></td>'
            f'<td class="def">{DEFS[r["arm"]]}</td></tr>'
        )
    per = []
    for r in R:
        cells = []
        for p, _ in PLATFORMS:
            for m in MISSIONS:
                cells.append(cell(r[f"{p}:{m}"], None if r is cmg else cmg[f"{p}:{m}"]))
        per.append(f'<tr><th scope="row">{html.escape(r["arm"])}</th>{"".join(cells)}</tr>')
    sat = []
    for r in R:
        cells = []
        for p, _ in PLATFORMS:
            for m in MISSIONS:
                cells.append(f'<td class="n">{float(r[f"{p}:{m}:frac_a_eq_1"]):.2f}</td>')
        sat.append(f'<tr><th scope="row">{html.escape(r["arm"])}</th>{"".join(cells)}</tr>')
    head_missions = "".join(f"<th>{m}</th>" for _ in PLATFORMS for m in MISSIONS)
    head_plat = "".join(f'<th colspan="5">{lab}</th>' for _, lab in PLATFORMS)
    lpf = R[1]
    activity = []
    for m in MISSIONS:
        figs = "".join(
            f'<figure class="plate"><img src="activity_{p}_{m}.png" alt="Per-unit activity of all ten bases, {lab} {m}" loading="lazy">'
            f"<figcaption>{lab} · {m} · CMG {float(cmg[f'{p}:{m}']):+.1f}% · LPF + logistic {float(lpf[f'{p}:{m}']):+.1f}%</figcaption></figure>"
            for p, lab in PLATFORMS
        )
        activity.append(f'<section class="mission" id="act-{m}"><h3>{m}</h3>{figs}</section>')
    nav = " ".join(f'<a href="#act-{m}">{m}</a>' for m in MISSIONS)

    page = TEMPLATE.format(
        x2_cmg=f'{float(cmg["x2:geomean"]):.2f}', cf2_cmg=f'{float(cmg["cf2-rotor:geomean"]):.2f}',
        x2_lpf=f'{float(lpf["x2:geomean"]):.2f}', cf2_lpf=f'{float(lpf["cf2-rotor:geomean"]):.2f}',
        agg="".join(agg), per="".join(per), sat="".join(sat), head_missions=head_missions,
        head_plat=head_plat, activity="".join(activity), nav=nav,
    )
    (REP / "index.html").write_text(page, encoding="utf-8")
    print("wrote", REP / "index.html")


TEMPLATE = """<title>CMG Mechanism Controls</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Literata:opsz,wght@7..72,500;7..72,650&family=Public+Sans:wght@400;600&family=JetBrains+Mono:wght@400;600&display=swap">
<style>
/* Layout: single reading column (findings, tables) that widens to full width for figure plates. */
:root {{
  --bg: #f6f7f8; --surface: #ffffff; --ink: #1b2430; --muted: #5a6675; --rule: #d9dee4;
  --accent: #0f6e78; --good: #1d7a46; --good-bg: #e3f3e9; --bad: #a3372b; --bad-bg: #f8e6e3;
  --mid: #8a6a12; --mid-bg: #f7efd8; --ref: #3b4a5c; --ref-bg: #e7ebf0; --up: #e6f4f5;
  --display: "Literata", Georgia, serif; --body: "Public Sans", "Segoe UI", system-ui, sans-serif;
  --mono: "JetBrains Mono", Consolas, monospace;
}}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{
  --bg: #12171d; --surface: #1a2129; --ink: #e4e9ee; --muted: #9aa6b4; --rule: #2e3742;
  --accent: #5fc3cc; --good: #7fd6a0; --good-bg: #183324; --bad: #f09a8e; --bad-bg: #3a1f1b;
  --mid: #e5c56b; --mid-bg: #352c14; --ref: #b8c4d2; --ref-bg: #26303b; --up: #173238; color-scheme: dark; }} }}
:root[data-theme="dark"] {{
  --bg: #12171d; --surface: #1a2129; --ink: #e4e9ee; --muted: #9aa6b4; --rule: #2e3742;
  --accent: #5fc3cc; --good: #7fd6a0; --good-bg: #183324; --bad: #f09a8e; --bad-bg: #3a1f1b;
  --mid: #e5c56b; --mid-bg: #352c14; --ref: #b8c4d2; --ref-bg: #26303b; --up: #173238; color-scheme: dark; }}
body {{ background: var(--bg); color: var(--ink); font: 15px/1.6 var(--body); }}
.wrap {{ max-width: 1240px; margin: 0 auto; padding-inline: 20px; padding-block: 28px 64px; display: grid; gap: 40px; }}
.col {{ max-width: 760px; }}
h1, h2, h3 {{ font-family: var(--display); font-weight: 650; text-wrap: balance; margin: 0; line-height: 1.2; }}
h1 {{ font-size: 2.1rem; }} h2 {{ font-size: 1.45rem; margin-bottom: 10px; }} h3 {{ font-size: 1.1rem; text-transform: capitalize; }}
p {{ margin: 0 0 10px; }} .lede {{ color: var(--muted); font-size: 1.02rem; }}
.eyebrow {{ font: 600 .72rem/1 var(--mono); letter-spacing: .08em; text-transform: uppercase; color: var(--accent); margin-bottom: 10px; }}
.kpis {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 12px; margin-top: 18px; }}
.kpi {{ background: var(--surface); border: 1px solid var(--rule); border-radius: 6px; padding: 14px 16px; }}
.kpi b {{ display: block; font: 600 1.55rem/1.1 var(--mono); font-variant-numeric: tabular-nums; }}
.kpi span {{ color: var(--muted); font-size: .85rem; }}
ol.findings {{ margin: 0; padding-left: 1.3em; display: grid; gap: 8px; }}
.tablebox {{ overflow-x: auto; background: var(--surface); border: 1px solid var(--rule); border-radius: 6px; }}
table {{ border-collapse: collapse; width: 100%; font-size: .86rem; }}
th, td {{ padding: 7px 10px; border-bottom: 1px solid var(--rule); text-align: left; vertical-align: top; }}
thead th {{ font: 600 .74rem/1.3 var(--mono); letter-spacing: .04em; color: var(--muted); background: var(--bg); white-space: nowrap; }}
tbody th {{ font-weight: 600; white-space: nowrap; }}
td.n {{ font-family: var(--mono); font-variant-numeric: tabular-nums; text-align: right; white-space: nowrap; }}
td.strong {{ font-weight: 600; }} td.def {{ color: var(--muted); min-width: 280px; }}
td.pos {{ color: var(--good); }} td.neg {{ color: var(--bad); }} td.zero {{ color: var(--muted); }}
td.up {{ background: var(--up); font-weight: 600; }}
.pill {{ display: inline-block; padding: 2px 9px; border-radius: 99px; font: 600 .74rem/1.5 var(--body); white-space: nowrap; }}
.pill.good {{ color: var(--good); background: var(--good-bg); }} .pill.bad {{ color: var(--bad); background: var(--bad-bg); }}
.pill.mid {{ color: var(--mid); background: var(--mid-bg); }} .pill.ref {{ color: var(--ref); background: var(--ref-bg); }}
.note {{ color: var(--muted); font-size: .84rem; margin-top: 8px; }}
.plate {{ margin: 0; background: #ffffff; border: 1px solid var(--rule); border-radius: 6px; padding: 8px; }}
.plate img {{ display: block; width: 100%; height: auto; }}
figcaption {{ font: .78rem/1.4 var(--mono); color: #3b4552; padding: 6px 4px 0; }}
.grid2 {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 520px), 1fr)); gap: 16px; }}
.mission {{ display: grid; gap: 12px; padding-top: 6px; }}
.jump {{ display: flex; flex-wrap: wrap; gap: 8px; margin: 6px 0 4px; }}
.jump a {{ font: 600 .8rem/1 var(--mono); color: var(--accent); text-decoration: none; border: 1px solid var(--rule); padding: 6px 10px; border-radius: 99px; background: var(--surface); }}
.jump a:focus-visible, .jump a:hover {{ outline: 2px solid var(--accent); outline-offset: 1px; }}
code {{ font: .86em var(--mono); }}
.eq {{ font-family: var(--mono); background: var(--surface); border: 1px solid var(--rule); border-radius: 6px; padding: 12px 14px; overflow-x: auto; white-space: pre; font-size: .84rem; line-height: 1.7; }}
</style>

<div class="wrap">
<header class="col">
  <div class="eyebrow">ACC 2027 · CMG–PES residual · experiment 2026-10-01</div>
  <h1>CMG Mechanism Controls</h1>
  <p class="lede">What does the coupled membrane–gate neuron contribute to the PES residual? Ten residual bases on the frozen ρ = 3 PD + desired-rate feedforward runner, two MuJoCo platforms, five 45 s missions, noise-free, seed 1. Only the paired-current → activity map changes between arms.</p>
  <div class="kpis">
    <div class="kpi"><b>{x2_cmg}% / {cf2_cmg}%</b><span>CMG (paper), X2 / CF2 geometric-mean error reduction</span></div>
    <div class="kpi"><b>{x2_lpf}% / {cf2_lpf}%</b><span>LPF + static logistic, same readout without gate dynamics</span></div>
    <div class="kpi"><b>0 of 10 runs</b><span>CMG gates that ever release after latching</span></div>
  </div>
</header>

<section class="col">
  <h2>Findings</h2>
  <ol class="findings">
    <li><b>Removing the gate dynamics improves the result.</b> LPF + static logistic equals CMG where CMG never latches (Roll, Yaw360) or latches at once (Hardstep), and beats it on Full3 and Hard45 on both platforms.</li>
    <li><b>Latching discards the useful signal.</b> With αγ = 100 the release fold sits near v ≈ −0.89, below v<sub>reset</sub> = 0, so a latched unit stays at a = 1 for the rest of the mission. On latched missions CMG performs about like constant-one.</li>
    <li><b>The useful feature is the small graded part above rest.</b> Constant-rest has the same ‖a‖² as CMG on Roll (0.83 vs 0.85) but gives +10% instead of +78%. Latch replay, which keeps only the two levels, fails on both platforms.</li>
    <li><b>Readout gain matters; conductance does not.</b> χ = 0 is identical to χ = 1 to two decimals. Lowering G to 10³ or 1 removes the graded tail and the gain with it.</li>
    <li><b>PES ordering is not a confound.</b> Constant-one gives 10.34% / 4.29% with either update ordering.</li>
  </ol>
</section>

<section>
  <h2>Summary by arm</h2>
  <div class="tablebox"><table>
    <thead><tr><th>Basis</th><th>X2</th><th>CF2</th><th>Preregistered verdict</th><th>Definition</th></tr></thead>
    <tbody>{agg}</tbody>
  </table></div>
  <p class="note">Geometric mean over five missions of mean true quaternion-angle error ratio to classical; improvement = 100·(1 − ratio). Verdicts from <code>PREREGISTRATION.md</code>: reproduces CMG ≥ 90% of CMG's improvement on both platforms; fails ≤ 50% on both. The CMG row reproduces the published Sec. VI-D numbers (asserted in <code>analyze.py</code>).</p>
</section>

<section>
  <h2>Every mission</h2>
  <figure class="plate"><img src="improvement_heatmap.png" alt="Heatmap of error reduction for every basis, mission and platform"></figure>
  <div class="tablebox" style="margin-top:16px"><table>
    <thead><tr><th rowspan="2">Basis</th>{head_plat}</tr><tr>{head_missions}</tr></thead>
    <tbody>{per}</tbody>
  </table></div>
  <p class="note">Error reduction vs classical, %. Shaded cells beat CMG on that mission by more than 3 points.</p>
</section>

<section>
  <h2>How often the readout sits at a = 1</h2>
  <div class="tablebox"><table>
    <thead><tr><th rowspan="2">Basis</th>{head_plat}</tr><tr>{head_missions}</tr></thead>
    <tbody>{sat}</tbody>
  </table></div>
  <p class="note">Fraction of unit-samples with a = 1. CMG on Hard45/Hardstep sits near 1 because latched units never release; LPF + logistic returns to rest whenever the command falls.</p>
</section>

<section class="col">
  <h2>What the LPF + logistic arm computes</h2>
  <div class="eq">I± = 0.75 + 1.25·max(±u₀/ℓ, 0)                  same paired current as CMG
r_k = σ(α(v_(k−1) − v_th)),  α = 50, v_th = 1     instantaneous gate, no γr feedback
v_k = v_(k−1)·e^(−dt/τ) + I_k·(1 − e^(−dt/τ))     τ = 0.05 s, no conductance discharge
a_k = clip(G·r_k, 0, 1),  G = 10⁵                 same readout as CMG</div>
  <p class="note">Decoder [I, −I], PES with Nengo's one-step ordering, η = 8·10⁻⁴, leak, ±6 projection, β (X2 0.5, CF2 0.2) and the output gate are identical in every arm. A NumPy restatement of CMG with the same ordering reproduces the archived Nengo run to 3·10⁻¹³ over 90,000 closed-loop steps.</p>
</section>

<section>
  <h2>Tracking error over time</h2>
  <p class="note">True quaternion error, log scale. On Roll and Yaw360 the CMG trace lies under the LPF + logistic trace.</p>
  <div class="grid2">
    <figure class="plate"><img src="error_x2.png" alt="X2 quaternion error versus time, five missions"><figcaption>X2</figcaption></figure>
    <figure class="plate"><img src="error_cf2-rotor.png" alt="CF2-rotor quaternion error versus time, five missions"><figcaption>CF2-rotor</figcaption></figure>
  </div>
</section>

<section>
  <h2>Per-unit activity, all ten bases</h2>
  <p class="note">Units ordered +x, +y, +z, −x, −y, −z. Each panel title gives that arm's error reduction on the mission.</p>
  <nav class="jump" aria-label="Jump to mission">{nav}</nav>
  {activity}
</section>

<section class="col">
  <h2>Scope and open questions</h2>
  <ol class="findings">
    <li>Single deterministic seed, noise-free MuJoCo rigid-body plants; same scope as Sec. VI-D.</li>
    <li>LPF + logistic uses 1.6–2× CMG's residual on Full3/Hard45 (≤ 4.4% of the torque limit RMS); the output gate never blocks.</li>
    <li>The initial decoder [I, −I] and the learned change each exceed the total output and largely cancel. An η = 0 frozen-decoder control would separate fixed feedforward from learning; it has not been run.</li>
  </ol>
  <p class="note">Source: <code>experiments/cmg_mechanism_controls_2026-10-01</code> — <code>PREREGISTRATION.md</code>, <code>analysis/RESULTS.md</code>, <code>analysis/report/summary_table.csv</code>.</p>
</section>
</div>
"""

if __name__ == "__main__":
    main()
