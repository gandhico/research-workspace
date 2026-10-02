"""Validate the archived-trace adapter before any Izhikevich figure is trusted.

The archived CMG rho = 3 run (baselines_2026-09-10/stretch/pdff/bw3/x2_hard45_nengo_nef_pes) and this campaign's
`cmg_pes_table` run are bit-identical simulations, stored in two different trace schemas.  The adapter must therefore
reproduce, from the archived schema, the Euler angles, error and residual that the new schema stores directly.
"""
import sys
from pathlib import Path

import numpy as np

import figlib as F
import figlib_multi as FM

HERE = Path(__file__).resolve().parent
arch = HERE.parent / "nengo_nef_replication_2026-08-29" / "results" / "baselines_2026-09-10" / "stretch" / "pdff" / "bw3"
ok = True
for mission in ("hard45", "hardstep", "roll"):
    a, _ = FM.load_archived(arch / f"x2_{mission}_nengo_nef_pes")
    n, _ = F.load(HERE / "results" / "confirmatory" / "nominal" / "x2" / mission / "cmg_pes_table" / "nominal" / "seed_001")
    assert len(a) == len(n) and np.allclose(a.t, n.t)
    e_a, e_n = F.euler_zyx(F.qcols(a, "qtrue")), F.euler_zyx(F.qcols(n, "qtrue"))
    d_euler = np.max(np.abs((e_a - e_n + 180) % 360 - 180))
    d_err = np.max(np.abs(a.qerr_true_rad - n.qerr_true_rad))
    d_res = max(np.max(np.abs(a[f"realized_residual_{c}"] - n[f"realized_residual_{c}"])) for c in "xyz")
    d_v = np.max(np.abs(a.voltage_0 - n.voltage_0))
    good = d_euler < 1e-6 and d_err < 1e-12 and d_res < 1e-12 and d_v < 1e-12
    ok &= good
    print(f"{mission:9s} max |Euler diff| {d_euler:.2e} deg   |error diff| {d_err:.2e}   |residual diff| {d_res:.2e}   |v diff| {d_v:.2e}   {'OK' if good else 'FAIL'}")
print("\nADAPTER VALIDATED" if ok else "\nADAPTER FAILED")
sys.exit(0 if ok else 1)
