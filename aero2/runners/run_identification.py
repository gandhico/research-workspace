"""run_identification.py — fit ARX/DARX models and reproduce Ref 3 Table II.

Fits the four nominal models on the migrated M3 PRBS logs and reports the
one-step AND free-run fits separately (the project's central result: strong
local one-step prediction, weak free-run simulation). Exports DARX coefficients
to data/identified_models/.
"""
from __future__ import annotations

import json
import warnings
from pathlib import Path

import numpy as np

from aero2.identification import arx
from aero2.identification.arx import ArxModel
from aero2.io import find_log, load_log

REPO = Path(__file__).resolve().parents[1]
EXPORT = REPO / "data" / "identified_models"

# Table II nominal models (Ref 3): case, data, output, inputs, na, nb, nk, downsample, paper one-step fit
MODELS = [
    dict(case="Pitch SISO",       csv="M3_aero2_03_pitch_prbs.csv", output="theta",       inputs=["u_common"],           na=1, nb=3, nk=1, ds=1, paper=98.231),
    dict(case="Yaw-rate SISO",    csv="M3_aero2_04_yaw_prbs.csv",   output="gyro_z_corr",  inputs=["u_diff"],             na=2, nb=2, nk=2, ds=1, paper=91.431),
    dict(case="Coupled pitch",    csv="M3_aero2_05_coupled_prbs.csv", output="theta",      inputs=["u_common", "u_diff"], na=1, nb=1, nk=1, ds=2, paper=99.263),
    dict(case="Coupled yaw-rate", csv="M3_aero2_05_coupled_prbs.csv", output="gyro_z_corr", inputs=["u_common", "u_diff"], na=3, nb=4, nk=2, ds=1, paper=87.892),
]


def fit_one(cfg, val_frac: float = 0.30):
    log = load_log(find_log(cfg["csv"]))
    y, u, ts, ym, um = arx.prepare(
        log["t"], log[cfg["output"]], {k: log[k] for k in cfg["inputs"]},
        start_time=3.0, demean=True, downsample_factor=cfg["ds"],
    )
    Z, Y, start = arx.build_regressor(y, u, cfg["na"], cfg["nb"], cfg["nk"])
    ntr = int((1.0 - val_frac) * len(Y))
    theta, rank, cond = arx.estimate_ls(Z[:ntr], Y[:ntr])
    model = ArxModel(cfg["output"], cfg["inputs"], cfg["na"], cfg["nb"], cfg["nk"],
                     theta, ts, cfg["ds"], y_mean=ym, u_mean=um, rank=rank, cond=cond)

    onestep = arx.fit_metric(Y[ntr:], Z[ntr:] @ theta)            # validation one-step
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        ysim = arx.free_run_simulate(model, y, u)
    freerun = arx.fit_metric(y[start + ntr:], ysim[start + ntr:])
    return model, ts, onestep, freerun


def export(model: ArxModel, case: str) -> None:
    EXPORT.mkdir(parents=True, exist_ok=True)
    payload = {
        "case": case, "output": model.output, "inputs": model.inputs,
        "na": model.na, "nb": model.nb, "nk": model.nk,
        "sample_time_s": model.ts, "downsample": model.downsample,
        "constant_c": model.c,
        "denominator_z_minus_1": model.denominator_z_minus_1,
        "numerators_z_minus_1": {k: list(model.b(k)) for k in model.inputs},
        "cond_ztz": model.cond, "rank": model.rank,
    }
    (EXPORT / f"{case.lower().replace(' ', '_').replace('-', '_')}_darx.json").write_text(
        json.dumps(payload, indent=2))


def freerun_label(fr: float) -> str:
    if not np.isfinite(fr):
        return "very poor (diverged)"
    if fr < 0:
        return f"{fr:7.2f}% (very poor)"
    if fr < 50:
        return f"{fr:7.2f}% (poor)"
    return f"{fr:7.2f}%"


def main() -> None:
    print(f"{'Case':<18} {'Ts[s]':>9}  order            {'one-step':>9}  {'(Table II)':>11}  free-run")
    print("-" * 92)
    for cfg in MODELS:
        model, ts, onestep, freerun = fit_one(cfg)
        export(model, cfg["case"])
        order = f"na={cfg['na']},nb={cfg['nb']},nk={cfg['nk']}"
        print(f"{cfg['case']:<18} {ts:9.6f}  {order:<15}  {onestep:7.2f}%  {cfg['paper']:>10.2f}%  {freerun_label(freerun)}")
    print(f"\nExported DARX models -> {EXPORT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
