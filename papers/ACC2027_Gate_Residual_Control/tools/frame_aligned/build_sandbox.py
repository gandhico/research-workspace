"""Frame-aligned re-run sandbox (Dr. Sandoval's review of Eq. 15, 2026-10-02).

Copies the repository CODE (no results) to frame_aligned_2026-10-02/ with the same relative tree, then applies the
only change: every rate-tracking error omega - omega_d becomes the frame-aligned omega_e = omega - R(q_e)^T omega_d of
P-(8). Four sites, each patched with an exact-match assertion:
  1. AdvancedBaseline.torque (every family; primary, robustness, A5, Izhikevich, neuron-basis runners)
  2. NMPC closed-loop rollout: the nominal law's rate error at each predicted step
  3. NMPC cost: predicted rate error
  4. inline PD/PID+ff laws: run_mujoco_nef_baselines.py (rho = 1 ladder) and run_controllers_gated.py (PID+ff)
The published results and sealed files are never touched; campaigns run inside the sandbox and write there.
    .venv\\Scripts\\python.exe tools\\frame_aligned\\build_sandbox.py
"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SB = REPO / "frame_aligned_2026-10-02"
STUDIES = ["nengo_nef_replication_2026-08-29", "theory_certificate_2026-09-12", "baseline_restatement_2026-09-16",
           "final_robustness_gating_2026-09-20", "neuron_basis_decisive_2026-09-24"]
TOP = ["src", "reproduce", "models", "third_party", "pyproject.toml"]
SKIP_DIR_PREFIX = ("results", "figures_out", "viewer_runs", "recordings", "_smoke", "__pycache__", "_root_smoke", "analysis")
CODE_EXT = {".py", ".ps1", ".json", ".md", ".tex", ".xml", ".obj", ".stl", ".png", ".toml", ".yaml", ".yml", ".txt", ".csv"}

ROT = '''

def _rotT(q):
    """R(q)^T for R(q) v = vec(q (x) [0, v] (x) q*): carries the desired-frame rate into the body frame (P-(8))."""
    w, x, y, z = np.asarray(q, dtype=float) / np.linalg.norm(q)
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - w * z), 2 * (x * z + w * y)],
                     [2 * (x * y + w * z), 1 - 2 * (x * x + z * z), 2 * (y * z - w * x)],
                     [2 * (x * z - w * y), 2 * (y * z + w * x), 1 - 2 * (x * x + y * y)]]).T
'''


def copy_code():
    if SB.exists():
        raise SystemExit(f"{SB} exists; remove it first if you really want to rebuild")
    for item in TOP:
        src = REPO / item
        if src.is_file():
            SB.mkdir(parents=True, exist_ok=True); shutil.copy2(src, SB / item); continue
        for p in src.rglob("*"):
            if p.is_file() and "__pycache__" not in p.parts:
                q = SB / p.relative_to(REPO); q.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(p, q)
    for s in STUDIES:
        base = REPO / "experiments" / s
        for p in base.rglob("*"):
            rel = p.relative_to(base)
            if not p.is_file() or any(part.startswith(SKIP_DIR_PREFIX) for part in rel.parts[:-1]):
                continue
            if p.suffix not in CODE_EXT or p.stat().st_size > 5_000_000:
                continue
            q = SB / "experiments" / s / rel; q.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(p, q)


def patch(path: Path, edits):
    s = path.read_text(encoding="utf-8")
    for old, new in edits:
        assert s.count(old) == 1, f"{path.name}: expected one match of {old!r}"
        s = s.replace(old, new)
    path.write_text(s, encoding="utf-8")


def main():
    copy_code()
    bl = SB / "experiments" / "nengo_nef_replication_2026-08-29" / "run_mujoco_nef_baselines.py"
    patch(bl, [
        ("\n\nclass AdvancedBaseline:", ROT + "\n\nclass AdvancedBaseline:"),
        ("        e, we = 2.0 * eq, omega - wd\n",
         "        qe_fa, _ = quat_error(reference_quat(t, self.a.mission, self.a.duration), q_meas)   # FRAME-ALIGNED\n"
         "        e, we = 2.0 * eq, omega - _rotT(qe_fa) @ wd\n"),
        ("                    _, ekp = quat_error(qrs[k], quat_conj(q))\n"
         "                    acc = wds[k] - self.k1 * 2.0 * ekp - self.k2 * (w - wrs[k])\n",
         "                    qep, ekp = quat_error(qrs[k], quat_conj(q))\n"
         "                    acc = wds[k] - self.k1 * 2.0 * ekp - self.k2 * (w - _rotT(qep) @ wrs[k])   # FRAME-ALIGNED\n"),
        ("                _, ek = quat_error(qrs[k + 1], quat_conj(q))\n                wek = w - wrs[k + 1]\n",
         "                qek, ek = quat_error(qrs[k + 1], quat_conj(q))\n"
         "                wek = w - _rotT(qek) @ wrs[k + 1]   # FRAME-ALIGNED\n"),
        ("                tau0_unsat = -kq * eq - kw * (omega - omega_d) - ki * eq_integral\n",
         "                tau0_unsat = -kq * eq - kw * (omega - _rotT(qe) @ omega_d) - ki * eq_integral   # FRAME-ALIGNED\n"),
    ])
    cg = SB / "experiments" / "final_robustness_gating_2026-09-20" / "run_controllers_gated.py"
    patch(cg, [
        ("from run_mujoco_nef_baselines import AdvancedBaseline, reference_rate  # noqa: E402",
         "from run_mujoco_nef_baselines import AdvancedBaseline, reference_rate, _rotT  # noqa: E402"),
        ("tau0_unsat = -kq_pd * eq_feedback - kw_pd * (omega_feedback - omega_d) - ki_pd * eq_integral",
         "tau0_unsat = -kq_pd * eq_feedback - kw_pd * (omega_feedback - _rotT(qe_feedback) @ omega_d) - ki_pd * eq_integral"
         "  # FRAME-ALIGNED"),
    ])
    # same Python environment as the paper (junction, no copy)
    subprocess.run(["cmd", "/c", "mklink", "/J", str(SB / ".venv"), str(REPO / ".venv")], check=True, capture_output=True)
    (SB / "FRAME_ALIGNED_README.md").write_text(
        "# Frame-aligned re-run (2026-10-02)\n\nCode copy of the paper repository with omega - omega_d replaced by "
        "omega_e = omega - R(q_e)^T omega_d at the four sites listed in tools/frame_aligned/build_sandbox.py "
        "(search FRAME-ALIGNED). Results written here are NOT the published results.\n", encoding="utf-8")
    print("sandbox ready:", SB)


if __name__ == "__main__":
    main()
