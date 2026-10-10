"""Prepare the frame-aligned sandbox for the paper inputs that reproduce_all.ps1 does not regenerate.

1. Copies (never links) the published runs that do NOT contain omega_d anywhere in their control law, so they are
   bit-for-bit what the frame-aligned code would produce:
     fixed PD and CMG on fixed PD   (run_mujoco_nef.py, tau0 = -kq eq - kw omega)            matched_45s, regress
     PID 0.05 without feedforward   (run_mujoco_nef_pid.py, --rate-ff none -> omega_d = 0)   tune/ki0.05
     Izhikevich on fixed PD         (run_fixed_pd_izh_corrected.py, fixed PD)                izh_fixed_pd_corrected_2026-09-24
     Nengo vs NumPy equivalence     (implementation identity check, archived fixed-PD cases) compiled
     reduced CMG on fixed PD        (cmg_mechanism_controls results/ladder/pd)
2. Copies the cmg_mechanism_controls_2026-10-01 CODE (its rho = 3 confirm/development arms are re-run).
Writes COPIED_UNAFFECTED.md in the sandbox. Run once:
    .venv/Scripts/python.exe tools/frame_aligned/stage_extras.py
"""
import re
import shutil
from pathlib import Path

from build_sandbox import CODE_EXT, REPO, SB, SKIP_DIR_PREFIX

NN = Path("experiments") / "nengo_nef_replication_2026-08-29" / "results"
MC = Path("experiments") / "cmg_mechanism_controls_2026-10-01"
UNAFFECTED = [NN / "matched_45s", NN / "pid_baseline_2026-09-10" / "regress", NN / "pid_baseline_2026-09-10" / "tune" / "ki0.05",
              NN / "izh_fixed_pd_corrected_2026-09-24", NN / "compiled", MC / "results" / "ladder" / "pd"]
# the fixed-PD runners must not contain the rate reference at all
NO_OMEGA_D = [Path("experiments") / "nengo_nef_replication_2026-08-29" / f for f in ("run_mujoco_nef.py", "run_fixed_pd_izh_corrected.py")]


def main():
    for f in NO_OMEGA_D:
        s = (REPO / f).read_text(encoding="utf-8")
        assert not re.search(r"omega_d|reference_rate|rate_ff", s), f"{f} uses the rate reference; it is not unaffected"
    lines = ["# Runs copied unchanged from the published tree", "",
             "Their control law has no desired-rate term (fixed PD, or PID with --rate-ff none so omega_d = 0), so the",
             "frame-aligned rate error cannot change them. Everything else in this sandbox was re-run with the patch.", ""]
    for rel in UNAFFECTED:
        src, dst = REPO / rel, SB / rel
        assert src.is_dir(), src
        if dst.exists():
            print("exists, kept:", dst); continue
        shutil.copytree(src, dst)
        n = sum(1 for p in dst.rglob("*") if p.is_file())
        lines.append(f"- `{rel.as_posix()}` ({n} files)")
        print("copied", rel, n)
    base = REPO / MC
    for p in base.rglob("*"):
        rel = p.relative_to(base)
        if not p.is_file() or any(part.startswith(SKIP_DIR_PREFIX) for part in rel.parts[:-1]):
            continue
        if p.suffix not in CODE_EXT or p.suffix in {".png", ".csv"} or p.stat().st_size > 5_000_000:
            continue
        q = SB / MC / rel
        q.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, q)
    lines += ["", f"Code of `{MC.as_posix()}` copied; its confirm/development arms are re-run in the sandbox.", ""]
    (SB / "COPIED_UNAFFECTED.md").write_text("\n".join(lines), encoding="utf-8")
    print("wrote", SB / "COPIED_UNAFFECTED.md")


if __name__ == "__main__":
    main()
