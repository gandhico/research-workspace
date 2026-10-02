"""Exploratory, post-v5 (not a declared version): does forcing strong S engagement on a NON-saturating
mission (Hard45) actually help, once e_ref is no longer the bottleneck? Isolates the calibration question
(fixed by rescaling e_ref) from the saturation question (Hardstep: more engagement made things worse).
e_ref=0.005 (20x smaller) makes |eq|/e_ref on Hard45 reach magnitudes comparable to what Hardstep sees
against the original e_ref=0.1.
"""
from pathlib import Path
from run_dual_v5 import run
from dual_controller import TunerConfig

OUT = Path(r"C:\Research\papers\P5_DualSelfTuning_Residual_CMG\results\v5_2026-09-25_probe_eref")
tcfg = TunerConfig(v2_gating=True, e_ref=0.005)

for fam in ("lqr", "backstepping"):
    b = run("x2", "hard45", fam, "base", OUT / fam / "base", duration=45.0)
    s = run("x2", "hard45", fam, "st", OUT / fam / "st", duration=45.0, tuner=tcfg)
    r = run("x2", "hard45", fam, "res", OUT / fam / "res", duration=45.0)
    d = run("x2", "hard45", fam, "dual", OUT / fam / "dual", duration=45.0, tuner=tcfg)
    st_gain = 100 * (1 - s["qerr_mean_rad"] / b["qerr_mean_rad"])
    dual_gain = 100 * (1 - d["qerr_mean_rad"] / r["qerr_mean_rad"])
    print(f"{fam:14s} base={b['qerr_mean_rad']*1e3:8.3f}mrad  st_mult_mean={['%.3f' % v for v in s['multiplier_mean']]}"
          f"  max={['%.3f' % v for v in s['multiplier_max']]}  WS_fro={s['WS_final_fro']:.4f}"
          f"  st_vs_base={st_gain:+6.2f}%  dual_vs_res={dual_gain:+6.2f}%")
