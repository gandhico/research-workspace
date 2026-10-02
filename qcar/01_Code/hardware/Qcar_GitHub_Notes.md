# QCar2 SNNs (Hardware) — GitHub Notes

**Date:** 2026-06-05

Reference for where the QCar code lives and what was shared.

---

## Where the code lives

| Location | Path / repo | Contents |
|----------|-------------|----------|
| Local master (source) | `C:\00_Research_\Neuromorphic_Embodied_AI\05_Qcar_SNNs\01_Code\hardware` | Full working set |
| Personal monorepo (private) | `Neuromorphic-Embodied-AI` → `Qcar2/` | Full QCar code (shared as-is, update later) |
| Collaboration (private) | `hmirh/SNN-Controller-for-Qcar2-with-SLAM` → `hardware/` | Two runners (on `qcar_control`) |

Unlike Coaxial, the full QCar code was OK to share — no curation needed.

---

## What was shared

Files committed to the collaboration repo's `hardware/` folder:

- `qcar2_unified_lane_control_base_v6.py` — V6 unified controller (PID / SMC /
  lightweight image NMPC / HyperLIF residual)
- `qcar2_unified_lane_control_hardware_v1.py` — hardware-safe runner;
  perception-only by default, **motion requires the `--armed` flag**

> Both also reside in the monorepo `Qcar2/` folder (plus their docs/CITATION).

---

## Important structural decision

The collaboration repo is a **ROS 2 Python package** (`qcar_estimator`), with
nodes registered in `setup.py` `entry_points`.

The QCar scripts were checked and found to be **standalone Quanser programs**
(`from pal.products.qcar import ...`, plain `def main()`, **no `rclpy`**). They
are run directly (e.g. `python qcar2_unified_lane_control_hardware_v1.py --armed`),
**not** ROS 2 nodes.

→ Therefore they were placed in a plain `hardware/` folder at the repo root, and
**nothing was added to `setup.py`**. (Promoting them to their own
`qcar_control` ROS 2 package later remains an option — raised as a question in the PR.)

---

## Collaboration contribution

- **Repo:** `hmirh/SNN-Controller-for-Qcar2-with-SLAM`
- **Branch:** `qcar_control` (already existed on the remote; was identical to
  default until this contribution)
- **Commit:** `feat: add standalone QCar2 hardware lane-control runners`
- **Pull request:** opened, base **`qcar_estimator`** (see open item below)

---

## Commands used (for reference)

```powershell
cd "C:\00_Research_\_github\SNN-Controller-for-Qcar2-with-SLAM"
git checkout qcar_control
git pull
mkdir hardware
Copy-Item "C:\00_Research_\Neuromorphic_Embodied_AI\05_Qcar_SNNs\01_Code\hardware\*.py" ".\hardware\"
git status
git add hardware
git commit -m "feat: add standalone QCar2 hardware lane-control runners"
git push
# then open PR on GitHub
```

---

## Open items / next steps

- **Confirm the PR base branch** with hmirh/brtgio: integration target is
  `qcar_estimator` (current default) or `master`? Adjust PR base if needed.
- Decide (with the team) whether control code stays in `hardware/` or becomes its
  own `qcar_control` ROS 2 package.
- Let reviewers merge (don't self-merge).
- Note: the QCar repo had earlier commits whose message was literally
  `git commit -m "feat: ..."` — going forward, the message is only the quoted text.
