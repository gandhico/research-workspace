"""Ceiling-effect analysis for EE 475/551 laboratory scores (IEEE ToE paper, Fig. 10).

Implements the methodology in `proposal_ceiling_effect_stats.md`:
  - bounded description (mean/median/SD/IQR/skew + % at ceiling), no unbounded Gaussian
  - paired Wilcoxon signed-rank on aligned theory->DT module pairs + effect size
  - cohort-wide delta = s_theory - s_DT distribution (median/IQR/range)
  - robust dispersion test (Brown-Forsythe / Levene) with bootstrap IQR-ratio CI
  - replacement two-panel Fig. 10 (violin+box; delta distribution)

INPUT: a de-identified long-format CSV with columns:
    student_id, module, category, score        # category in {theoretical, digital_twin}
Aligned module pairs default to (4,5), (6,7), (10,11) per Table II.

USAGE: python ceiling_effect_analysis.py scores.csv
Requires: numpy, pandas, scipy, matplotlib.
"""
from __future__ import annotations
import sys
import numpy as np
import pandas as pd
from scipy import stats
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ALIGNED_PAIRS = [(4, 5), (6, 7), (10, 11)]   # (theoretical module, digital-twin module)
CEIL_HI, CEIL_MAX = 95.0, 100.0


def ceiling_stats(x):
    x = np.asarray(x, float)
    return dict(n=len(x), mean=x.mean(), median=np.median(x), sd=x.std(ddof=1),
                iqr=np.subtract(*np.percentile(x, [75, 25])), skew=stats.skew(x),
                pct_ge95=100*np.mean(x >= CEIL_HI), pct_max=100*np.mean(x >= CEIL_MAX))


def rank_biserial_signed(d):
    """Matched-pairs rank-biserial effect size from paired differences d."""
    d = d[d != 0]
    if len(d) == 0:
        return 0.0
    r = stats.rankdata(np.abs(d))
    rp, rn = r[d > 0].sum(), r[d < 0].sum()
    return (rp - rn) / (rp + rn)


def bootstrap_iqr_ratio(a, b, n=10000, seed=0):
    rng = np.random.default_rng(seed)
    def iqr(v): return np.subtract(*np.percentile(v, [75, 25]))
    ratios = []
    for _ in range(n):
        ra = rng.choice(a, len(a), replace=True)
        rb = rng.choice(b, len(b), replace=True)
        rb_iqr = iqr(rb)
        ratios.append(iqr(ra) / rb_iqr if rb_iqr > 0 else np.nan)
    ratios = np.array(ratios)[~np.isnan(np.array([iqr(a)]))] if iqr(b) else np.array(ratios)
    lo, hi = np.nanpercentile(ratios, [2.5, 97.5])
    return iqr(a)/iqr(b) if iqr(b) else np.nan, lo, hi


def main(path):
    df = pd.read_csv(path)
    df["category"] = df["category"].str.lower().str.strip()
    theo = df[df.category == "theoretical"].score.values
    dt = df[df.category == "digital_twin"].score.values

    print("=" * 64)
    print("DESCRIPTIVE (bounded; report these instead of Gaussian mu/sigma)")
    for name, x in [("Theoretical", theo), ("Digital-Twin", dt)]:
        s = ceiling_stats(x)
        print(f"  {name:12s} n={s['n']:3d}  mean={s['mean']:5.1f} median={s['median']:5.1f} "
              f"SD={s['sd']:4.1f} IQR={s['iqr']:4.1f} skew={s['skew']:+.2f} "
              f">=95%={s['pct_ge95']:4.0f} =100%={s['pct_max']:4.0f}")
    print("  (rule of thumb: >15% at the maximum => ceiling effect)")

    # paired Wilcoxon on aligned within-student pairs
    print("=" * 64)
    print("PAIRED theory->DT (Wilcoxon signed-rank on aligned module pairs)")
    deltas = []
    for mt, md in ALIGNED_PAIRS:
        m = df.pivot_table(index="student_id", columns="module", values="score")
        if mt in m and md in m:
            pair = m[[mt, md]].dropna()
            d = (pair[mt] - pair[md]).values
            deltas.append(d)
            if len(d) >= 3 and np.any(d != 0):
                w, p = stats.wilcoxon(pair[mt].values, pair[md].values)
                print(f"  modules {mt}->{md}: n={len(d)} median_delta={np.median(d):+.1f} "
                      f"W={w:.0f} p={p:.4f} rank-biserial={rank_biserial_signed(d):+.2f}")
    alld = np.concatenate(deltas) if deltas else np.array([])
    if len(alld):
        print(f"  COHORT delta = s_theory - s_DT : median={np.median(alld):+.1f} "
              f"IQR={np.subtract(*np.percentile(alld,[75,25])):.1f} "
              f"range=[{alld.min():+.0f},{alld.max():+.0f}]  (n={len(alld)})")

    # dispersion test (ceiling compresses variance)
    print("=" * 64)
    print("DISPERSION (does DT disperse more than theory?)")
    bf = stats.levene(theo, dt, center="median")   # Brown-Forsythe
    r, lo, hi = bootstrap_iqr_ratio(dt, theo)
    print(f"  Brown-Forsythe: W={bf.statistic:.2f} p={bf.pvalue:.4f}")
    print(f"  IQR ratio DT/theory = {r:.2f}  (95% bootstrap CI {lo:.2f}-{hi:.2f})")

    # replacement Fig. 10
    fig, ax = plt.subplots(1, 2, figsize=(10, 4.2))
    parts = ax[0].violinplot([theo, dt], showmedians=True)
    for i, x in enumerate([theo, dt], 1):
        ax[0].scatter(np.full_like(x, i) + np.random.uniform(-.06, .06, len(x)), x, s=12, alpha=.5, zorder=3)
    ax[0].set_xticks([1, 2]); ax[0].set_xticklabels(["Theoretical", "Digital-Twin"])
    ax[0].set_ylabel("Laboratory score (%)"); ax[0].set_ylim(0, 105); ax[0].axhline(100, ls=":", c="gray")
    ax[0].set_title("(a) Score distributions by modality")
    if len(alld):
        ax[1].boxplot(alld, vert=True, widths=.5)
        ax[1].scatter(np.ones_like(alld) + np.random.uniform(-.06, .06, len(alld)), alld, s=14, alpha=.6, zorder=3)
        ax[1].axhline(0, ls="--", c="k", lw=1)
        ax[1].set_xticks([1]); ax[1].set_xticklabels([r"$\delta = s_{theory}-s_{DT}$"])
        ax[1].set_ylabel("performance index  $\\delta$ (points)")
        ax[1].set_title("(b) Theory-to-practice gap across cohort")
    fig.tight_layout()
    out = path.rsplit(".", 1)[0] + "_fig10_corrected.png"
    fig.savefig(out, dpi=220)
    print("=" * 64); print("SAVED", out)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "scores.csv")
