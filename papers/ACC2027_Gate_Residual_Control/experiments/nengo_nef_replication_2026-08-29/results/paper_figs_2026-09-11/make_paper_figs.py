"""Paper-format figures for the best fair result: CMG-PES on tuned PD + ff.

Uses the paper's own plotting code, unmodified on disk:
  plot_attitude_detail.py  -> {platform}_{mission}_attitude.png  (Figs. 4, 6 format)
  compile_and_plot.py      -> {platform}_{mission}_neurons.png   (Figs. 5, 7 format)

Both hard-code the baseline's name ("Quaternion PD"). The source text is
loaded, only the label strings are replaced, and the result is executed in a
private namespace, so the layout, panels, colours and dpi are exactly those of
the published figures while the legend names the baseline actually plotted.

Runs (staged in ./runs/, copied from results/baselines_2026-09-10/):
  classical      PD + reference-rate feedforward at 3x bandwidth (tuned)
  nengo_nef_pes  CMG-PES on that baseline, beta 0.5 (the pre-declared rule's
                 choice for X2)

Run:  python make_paper_figs.py
"""
from __future__ import annotations

from pathlib import Path

HERE = Path(__file__).resolve().parent
EXP = HERE.parents[1]                 # experiments/nengo_nef_replication_2026-08-29
RUNS = HERE / "runs"
MISSIONS = ("full3", "roll")
BASELINE = "Tuned PD + ff"
CMG = "CMG-PES on tuned PD + ff"


def load_variant(script: str, replacements: list[tuple[str, str]]) -> dict:
    src = (EXP / script).read_text(encoding="utf-8")
    for old, new in replacements:
        if old not in src:
            raise SystemExit(f"{script}: expected text not found: {old!r}")
        src = src.replace(old, new)
    ns = {"__name__": f"variant_of_{script}", "__file__": str(EXP / script)}
    exec(compile(src, str(EXP / script), "exec"), ns)
    return ns


attitude = load_variant("plot_attitude_detail.py", [
    ("Quaternion PD", BASELINE),
    ("Nengo CMG+PES", CMG),
    # .2f prints Roll's CMG mean (0.0042 deg) as "0.00"; 3 significant figures
    ("_mean:.2f} deg)", "_mean:.3g} deg)"),
])
neurons = load_variant("compile_and_plot.py", [
    (': Nengo CMG states and online PES decoder"',
     ': Nengo CMG states and online PES decoder (on tuned PD + ff, beta 0.5)"'),
])
neurons["PLOTS"] = HERE

for m in MISSIONS:
    cdir = RUNS / f"x2_{m}_classical"
    ndir = RUNS / f"x2_{m}_nengo_nef_pes"
    attitude["plot_attitude"]("x2", m, cdir, ndir, HERE / f"x2_{m}_attitude.png")
    neurons["_neuron_plot"]("x2", m, ndir)
    print(f"wrote {HERE / f'x2_{m}_neurons.png'}")
