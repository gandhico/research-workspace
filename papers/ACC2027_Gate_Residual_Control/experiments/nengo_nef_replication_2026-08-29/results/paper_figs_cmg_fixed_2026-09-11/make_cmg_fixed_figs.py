"""Paper-format figures for CMG with a fixed decoder (no PES), both platforms,
five missions.

Uses the paper's own plotting code, unmodified on disk:
  plot_attitude_detail.py  -> {platform}_{mission}_attitude.png  (Figs. 4, 6 format)
  compile_and_plot.py      -> {platform}_{mission}_neurons.png   (Figs. 5, 7 format)

The source text is loaded, only label strings are replaced, and the result is
executed in a private namespace, so layout, panels, colours and dpi are those
of the published figures.

Runs are read in place from results/neuron_family_matched_45s/ (the matched
neuron-family campaign behind the paper's fixed-vs-PES tables):
  classical        the paper's quaternion PD
  nengo-cmg-fixed  CMG residual, beta 0.5, decoder held at its initial value

Run:  python make_cmg_fixed_figs.py
"""
from __future__ import annotations

from pathlib import Path

HERE = Path(__file__).resolve().parent
EXP = HERE.parents[1]                 # experiments/nengo_nef_replication_2026-08-29
RUNS = EXP / "results" / "neuron_family_matched_45s"
PLATFORMS = ("x2", "cf2-rotor")
MISSIONS = ("roll", "full3", "hard45", "hardstep", "yaw360")
CMG = "Nengo CMG, fixed decoder"


def load_variant(script: str, replacements: list[tuple[str, str]], extra: dict | None = None) -> dict:
    src = (EXP / script).read_text(encoding="utf-8")
    for old, new in replacements:
        if old not in src:
            raise SystemExit(f"{script}: expected text not found: {old!r}")
        src = src.replace(old, new)
    ns = {"__name__": f"variant_of_{script}", "__file__": str(EXP / script), **(extra or {})}
    exec(compile(src, str(EXP / script), "exec"), ns)
    return ns


def _is_number(text: str) -> bool:
    try:
        float(text)
    except ValueError:
        return False
    return True


attitude = load_variant("plot_attitude_detail.py", [
    ("Nengo CMG+PES", CMG),
    # .2f prints small means (e.g. 0.0042 deg) as "0.00"; 3 significant figures
    ("_mean:.2f} deg)", "_mean:.3g} deg)"),
    # the neuron-family traces carry a text column (family name, "cmg");
    # the published loader casts every column to float
    ("for r in rows]) for k in rows[0]}",
     "for r in rows]) for k in rows[0] if _is_number(rows[0][k])}"),
], extra={"_is_number": _is_number})
def _with_archive_gate(d, ndir):
    """The fixed-decoder runs log gate_i = 0.0 at every sample in trace.csv;
    the full-rate archive holds the true r. Take r from the archive at the
    trace's sample times, after checking the alignment on the activity."""
    import numpy as np
    z = np.load(ndir / "neural_trace_full_rate.npz")
    t_arc = z["t"]
    t_tr = d["t"].to_numpy()
    base = np.searchsorted(t_arc, t_tr - 1e-9)
    act = d[[f"activity_{i}" for i in range(6)]].to_numpy()
    inside = t_tr >= t_arc[0] - 1e-12          # rows logged before the archive starts
    best = None
    for off in (0, -1, 1, -2, 2):              # archive stamps t+dt; find the matching sample
        cand = np.clip(base + off, 0, len(t_arc) - 1)
        err = np.max(np.abs(z["activity"][cand][inside] - act[inside]))
        if best is None or err < best[0]:
            best = (err, cand, off)
    mismatch, idx, off = best
    if mismatch > 1e-9:
        raise SystemExit(f"{ndir}: archive/trace misaligned (activity differs by {mismatch:.3g})")
    print(f"  {ndir.parent.parent.name}/{ndir.parent.name}: archive offset {off:+d} sample, "
          f"activity match {mismatch:.1e}, {np.sum(~inside)} pre-archive row(s)")
    for i in range(6):
        d[f"gate_{i}"] = z["gate"][idx, i]
    return d


neurons = load_variant("compile_and_plot.py", [
    (': Nengo CMG states and online PES decoder"',
     ': Nengo CMG states, fixed decoder (no PES), beta 0.5"'),
    ('d = pd.read_csv(ndir / "trace.csv", usecols=columns)',
     'd = _with_archive_gate(pd.read_csv(ndir / "trace.csv", usecols=columns), ndir)'),
], extra={"_with_archive_gate": _with_archive_gate})
neurons["PLOTS"] = HERE

for p in PLATFORMS:
    for m in MISSIONS:
        cdir = RUNS / p / m / "classical"
        ndir = RUNS / p / m / "nengo-cmg-fixed"
        attitude["plot_attitude"](p, m, cdir, ndir, HERE / f"{p}_{m}_attitude.png")
        neurons["_neuron_plot"](p, m, ndir)
        print(f"wrote {HERE / f'{p}_{m}_neurons.png'}")
