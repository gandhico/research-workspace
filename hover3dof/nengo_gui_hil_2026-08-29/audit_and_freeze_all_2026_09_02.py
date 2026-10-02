"""Read-only experiment audit plus immutable index generation for the ACC 2027 project.

The script never opens Quanser hardware.  It validates the canonical physical
PD/CMG-PES pairs, indexes every saved Nengo/Hover summary, records the existing
MuJoCo and Q8-shadow integrity audits, and writes a SHA-256 freeze manifest.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
from collections import Counter
from pathlib import Path

import numpy as np


ROOT = Path(r"C:\Research\hover3dof\nengo_gui_hil_2026-08-29")
RESULTS = ROOT / "results"
DIRECT = RESULTS / "DIRECT_NENGO_FINAL_2026-09-01"
OUT = RESULTS / "FROZEN_AUDIT_2026-09-02"
MUJOCO = Path(
    r"C:\Research\papers\ACC2027_Gate_Residual_Control\experiments"
    r"\nengo_nef_replication_2026-08-29\results"
)

PAIRS = {
    "hover": (
        "pd_hover_none_armed_20260901_192613",
        "nengo-pes_hover_none_armed_20260901_192626",
    ),
    "roll": (
        "pd_roll_none_armed_20260901_192641",
        "nengo-pes_roll_none_armed_20260901_192654",
    ),
    "full3": (
        "pd_full3_none_armed_20260901_192715",
        "nengo-pes_full3_none_armed_20260901_192733",
    ),
    "hard45": (
        "pd_hard45_none_armed_20260901_192812",
        "nengo-pes_hard45_none_armed_20260901_192844",
    ),
    "hardstep": (
        "pd_hardstep_none_armed_20260901_192904",
        "nengo-pes_hardstep_none_armed_20260901_192922",
    ),
    "yaw360-reduced-range": (
        "pd_yaw360_none_armed_20260901_193849",
        "nengo-pes_yaw360_none_armed_20260901_193929",
    ),
}

FULL_SCALE_YAW_ABORTS = (
    "pd_yaw360_none_armed_20260901_193059",
    "pd_yaw360_none_armed_20260901_193741",
)

KNOWN_EXCLUSIONS = {
    str((RESULTS / "hardware" / "pd_hover_none_armed_20260901_182831").resolve()): (
        "exclude-invalid-instrumentation: impossible 1923.75-deg encoder step"
    ),
    str((RESULTS / "hardware" / "pd_hover_none_armed_20260901_182846").resolve()): (
        "exclude-unplanned-repeat: GUI restarted worker after nominal completion"
    ),
}

MATCH_FIELDS = (
    "mission",
    "duration",
    "reference_scale",
    "hardstep_transition_s",
    "allocation_policy",
    "motor_floor_volts",
    "max_abs_pitch_deg",
    "max_abs_roll_deg",
    "max_encoder_step_deg",
    "disturbance",
)


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def verify_existing_manifest(path: Path) -> dict:
    data = read_json(path)
    root = Path(data.get("root", path.parent))
    if isinstance(data.get("entries"), list):
        entries = data["entries"]
    elif isinstance(data.get("source_files"), list):
        entries = [*data["source_files"], *data.get("compiled_files", [])]
    elif isinstance(data.get("files"), list):
        entries = data["files"]
    else:
        return {"manifest": str(path), "status": "unsupported", "checked": 0, "failures": ["no entry list"]}
    failures = []
    checked_bytes = 0
    for entry in entries:
        item = Path(entry["path"])
        if not item.is_absolute():
            item = root / item
        if not item.exists():
            failures.append({"path": str(item), "reason": "missing"})
            continue
        expected_size = entry.get("size", entry.get("bytes"))
        actual_size = item.stat().st_size
        checked_bytes += actual_size
        if expected_size is not None and actual_size != int(expected_size):
            failures.append(
                {"path": str(item), "reason": "size", "expected": int(expected_size), "actual": actual_size}
            )
            continue
        actual_hash = sha256(item)
        if actual_hash.upper() != str(entry["sha256"]).upper():
            failures.append(
                {"path": str(item), "reason": "sha256", "expected": entry["sha256"], "actual": actual_hash}
            )
    return {
        "manifest": str(path),
        "status": "passed" if not failures else "failed",
        "checked": len(entries),
        "checked_bytes": checked_bytes,
        "failures": failures,
    }


def classify(summary_path: Path, summary: dict) -> str:
    cfg = summary.get("config", {})
    run_dir = str(summary_path.parent.resolve())
    if run_dir in KNOWN_EXCLUSIONS:
        return KNOWN_EXCLUSIONS[run_dir]
    if cfg.get("io_mode") == "q8" and not cfg.get("armed", False):
        return "q8-shadow-zero-output"
    if cfg.get("armed", False):
        if summary.get("run_completed", False):
            return "physical-completed"
        return "physical-safety-abort"
    if cfg.get("io_mode") == "emulated" or not summary.get("hardware", False):
        return "emulated"
    return "other"


def inventory_all_summaries() -> list[dict]:
    rows = []
    for path in sorted(RESULTS.rglob("summary.json")):
        try:
            summary = read_json(path)
        except Exception as exc:  # retained in audit rather than hidden
            rows.append({"summary_path": str(path), "classification": f"unreadable: {exc}"})
            continue
        cfg = summary.get("config", {})
        rows.append(
            {
                "summary_path": str(path),
                "run_directory": str(path.parent),
                "campaign": path.relative_to(RESULTS).parts[0],
                "controller": cfg.get("controller", ""),
                "mission": cfg.get("mission", ""),
                "io_mode": cfg.get("io_mode", ""),
                "armed": bool(cfg.get("armed", False)),
                "hardware": bool(summary.get("hardware", False)),
                "completed": bool(summary.get("run_completed", False)),
                "abort_reason": summary.get("abort_reason", ""),
                "duration_s": cfg.get("duration", ""),
                "reference_scale": cfg.get("reference_scale", ""),
                "samples": summary.get("n_steps_logged", ""),
                "mean_error_deg": summary.get("angle_err_mean_deg", ""),
                "max_error_deg": summary.get("angle_err_max_deg", ""),
                "classification": classify(path, summary),
            }
        )
    return rows


def load_trace(path: Path) -> tuple[list[dict], list[str]]:
    with path.open("r", newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        rows = list(reader)
        return rows, list(reader.fieldnames or [])


def farray(rows: list[dict], name: str) -> np.ndarray:
    return np.asarray([float(row[name]) for row in rows], dtype=float)


def audit_run(run_dir: Path, expect_neural: bool) -> dict:
    summary = read_json(run_dir / "summary.json")
    rows, columns = load_trace(run_dir / "trace.csv")
    cfg = summary["config"]
    expected_n = int(round(float(cfg["duration"]) * float(summary["hardware_rate_hz"])))
    numeric_finite = True
    for name in columns:
        try:
            values = farray(rows, name)
        except ValueError:
            continue
        if not np.all(np.isfinite(values)):
            numeric_finite = False
            break

    component_errors_deg = np.column_stack(
        [farray(rows, name) for name in ("yaw_error_wrapped_deg", "pitch_error_deg", "roll_error_deg")]
    )
    reported_angle_error_deg = np.linalg.norm(component_errors_deg, axis=1)
    written_cols = [f"{name}_written" for name in ("Vf", "Vb", "Vl", "Vr")]
    written = np.column_stack([farray(rows, name) for name in written_cols])
    angles = np.column_stack([farray(rows, name) for name in ("yaw_deg", "pitch_deg", "roll_deg")])
    max_step = np.max(np.abs(np.diff(angles, axis=0)), axis=0) if len(rows) > 1 else np.zeros(3)

    neural_path = run_dir / "neural_trace_2khz.npz"
    neural_ok = not expect_neural
    neural_samples = 0
    neural_arrays = 0
    if expect_neural and neural_path.exists():
        with np.load(neural_path) as archive:
            neural_arrays = len(archive.files)
            lengths = []
            neural_ok = True
            for name in archive.files:
                value = np.asarray(archive[name])
                if value.ndim > 0:
                    lengths.append(value.shape[0])
                if not np.all(np.isfinite(value)):
                    neural_ok = False
            neural_samples = max(lengths, default=0)
            neural_ok = neural_ok and neural_samples == len(rows) * 10

    checks = {
        "summary_completed": bool(summary["run_completed"]),
        "empty_abort_reason": summary.get("abort_reason", "") == "",
        "row_count_matches_summary": len(rows) == int(summary["n_steps_logged"]),
        "row_count_matches_duration": len(rows) == expected_n,
        "all_numeric_trace_values_finite": numeric_finite,
        "written_motor_voltages_nonnegative": float(np.min(written)) >= -1e-12,
        "written_motor_voltages_at_or_below_24V": float(np.max(written)) <= 24.0 + 1e-12,
        "summary_mean_reproduced": math.isclose(
            float(np.mean(reported_angle_error_deg)), float(summary["angle_err_mean_deg"]), rel_tol=0, abs_tol=1e-9
        ),
        "summary_max_reproduced": math.isclose(
            float(np.max(reported_angle_error_deg)), float(summary["angle_err_max_deg"]), rel_tol=0, abs_tol=1e-9
        ),
        "encoder_step_below_recorded_guard": float(np.max(max_step)) <= float(cfg["max_encoder_step_deg"]) + 1e-12,
        "neural_archive_expected_presence": neural_path.exists() == expect_neural,
        "neural_archive_finite_and_10x_rate": neural_ok,
    }
    return {
        "run_directory": str(run_dir),
        "controller": cfg["controller"],
        "mission": cfg["mission"],
        "duration_s": cfg["duration"],
        "reference_scale": cfg["reference_scale"],
        "angle_err_mean_deg": summary["angle_err_mean_deg"],
        "angle_err_max_deg": summary["angle_err_max_deg"],
        "deadline_miss_fraction": summary["deadline_miss_fraction"],
        "max_encoder_step_deg_ypr": max_step.tolist(),
        "motor_written_min_V": float(np.min(written)),
        "motor_written_max_V": float(np.max(written)),
        "hardware_samples": len(rows),
        "neural_samples": neural_samples,
        "neural_arrays": neural_arrays,
        "checks": checks,
        "passed": all(checks.values()),
    }


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    inventory = inventory_all_summaries()
    write_csv(OUT / "all_saved_run_inventory.csv", inventory)
    (OUT / "all_saved_run_inventory.json").write_text(
        json.dumps(inventory, indent=2) + "\n", encoding="utf-8"
    )

    physical_audits = []
    pair_rows = []
    pair_integrity = []
    for label, (pd_name, cmg_name) in PAIRS.items():
        pd_dir, cmg_dir = DIRECT / pd_name, DIRECT / cmg_name
        pd_audit = audit_run(pd_dir, expect_neural=False)
        cmg_audit = audit_run(cmg_dir, expect_neural=True)
        physical_audits.extend((pd_audit, cmg_audit))
        pd_s, cmg_s = read_json(pd_dir / "summary.json"), read_json(cmg_dir / "summary.json")
        matches = {field: pd_s["config"].get(field) == cmg_s["config"].get(field) for field in MATCH_FIELDS}
        pair_integrity.append({"mission_label": label, "fields": matches, "passed": all(matches.values())})
        pd_mean, cmg_mean = pd_s["angle_err_mean_deg"], cmg_s["angle_err_mean_deg"]
        pd_max, cmg_max = pd_s["angle_err_max_deg"], cmg_s["angle_err_max_deg"]
        pair_rows.append(
            {
                "mission": label,
                "reference_scale": pd_s["config"]["reference_scale"],
                "duration_s": pd_s["config"]["duration"],
                "pd_mean_deg": pd_mean,
                "cmg_mean_deg": cmg_mean,
                "mean_improvement_pct": 100.0 * (pd_mean - cmg_mean) / pd_mean,
                "pd_max_deg": pd_max,
                "cmg_max_deg": cmg_max,
                "max_improvement_pct": 100.0 * (pd_max - cmg_max) / pd_max,
                "matched_configuration": all(matches.values()),
                "pd_run": pd_name,
                "cmg_run": cmg_name,
            }
        )

    yaw_aborts = []
    for name in FULL_SCALE_YAW_ABORTS:
        summary = read_json(DIRECT / name / "summary.json")
        yaw_aborts.append(
            {
                "run": name,
                "duration_s": summary["config"]["duration"],
                "reference_scale": summary["config"]["reference_scale"],
                "samples_before_abort": summary["n_steps_logged"],
                "abort_reason": summary["abort_reason"],
                "mean_error_until_abort_deg": summary["angle_err_mean_deg"],
                "max_error_until_abort_deg": summary["angle_err_max_deg"],
            }
        )

    deep_audit = {
        "status": "passed" if all(x["passed"] for x in physical_audits) and all(x["passed"] for x in pair_integrity) else "failed",
        "scope": "canonical direct-Nengo physical matched pairs",
        "runs": physical_audits,
        "pair_configuration_integrity": pair_integrity,
        "full_scale_yaw360_safety_aborts": yaw_aborts,
    }
    (OUT / "canonical_physical_deep_audit.json").write_text(
        json.dumps(deep_audit, indent=2) + "\n", encoding="utf-8"
    )
    write_csv(OUT / "canonical_physical_matched_pairs.csv", pair_rows)
    (OUT / "canonical_physical_matched_pairs.json").write_text(
        json.dumps(pair_rows, indent=2) + "\n", encoding="utf-8"
    )

    registry_paths = {
        "mujoco_family_integrity": MUJOCO / "neuron_family_compiled" / "campaign_integrity_audit.json",
        "mujoco_family_raw_manifest": MUJOCO / "neuron_family_matched_45s" / "FROZEN_SHA256_MANIFEST.json",
        "hover_family_integrity": RESULTS / "hover_neuron_family_compiled_2026-09-01" / "campaign_integrity_audit.json",
        "hover_family_manifest": RESULTS / "hover_neuron_family_compiled_2026-09-01" / "FROZEN_SHA256_MANIFEST.json",
        "q8_family_shadow_audit": RESULTS / "q8_neuron_family_shadow_2026-09-01" / "SHADOW_AUDIT.json",
        "q8_family_shadow_manifest": RESULTS / "q8_neuron_family_shadow_2026-09-01" / "FROZEN_SHA256_MANIFEST.json",
        "physical_roll_n3": RESULTS / "hardware_armed_roll_n3_2026-09-01" / "armed_roll_n3_summary.json",
        "earlier_physical_campaign": RESULTS / "final_hardware_campaign_2026-09-01" / "campaign_results.json",
        "research_analysis": RESULTS / "FINAL_ANALYSIS_2026-09-01.md",
        "command_catalog": ROOT / "docs" / "COMMAND_CATALOG_2026-09-01.md",
        "audit_script": ROOT / "audit_and_freeze_all_2026_09_02.py",
        "direct_hardware_runner": ROOT / "run_hover_direct_nengo.py",
        "hover_nengo_engine": ROOT / "hover_nengo_hil_gui.py",
        "pd_baseline": Path(r"C:\Research\hover3dof\pd_cmg_focused_final_round_2026-08-28\src\pd_baseline.py"),
        "nengo_cmg": Path(
            r"C:\Research\papers\ACC2027_Gate_Residual_Control\experiments"
            r"\nengo_nef_replication_2026-08-29\nengo_cmg.py"
        ),
        "nengo_neuron_family": Path(
            r"C:\Research\papers\ACC2027_Gate_Residual_Control\experiments"
            r"\nengo_nef_replication_2026-08-29\nengo_neuron_family.py"
        ),
        "paper_draft": Path(
            r"C:\Research\papers\ACC2027_Gate_Residual_Control\paper"
            r"\acc2027_neuromorphic_gate_residual_draft.tex"
        ),
        "six_dof_progress": Path(
            r"C:\Research\papers\ACC2027_Gate_Residual_Control\experiments"
            r"\six_dof_expansion_2026-08-31\PROGRESS_2026-08-31.md"
        ),
    }
    registry = {}
    for key, path in registry_paths.items():
        registry[key] = {
            "path": str(path),
            "exists": path.exists(),
            "bytes": path.stat().st_size if path.exists() else None,
            "sha256": sha256(path) if path.exists() else None,
        }
    (OUT / "campaign_registry.json").write_text(json.dumps(registry, indent=2) + "\n", encoding="utf-8")

    upstream_verification = [
        verify_existing_manifest(registry_paths["mujoco_family_raw_manifest"]),
        verify_existing_manifest(registry_paths["hover_family_manifest"]),
        verify_existing_manifest(registry_paths["q8_family_shadow_manifest"]),
    ]
    (OUT / "UPSTREAM_MANIFEST_VERIFICATION.json").write_text(
        json.dumps(upstream_verification, indent=2) + "\n", encoding="utf-8"
    )

    counts = Counter(row["classification"] for row in inventory)
    audit_summary = {
        "status": deep_audit["status"],
        "saved_summary_count": len(inventory),
        "inventory_classification_counts": dict(sorted(counts.items())),
        "canonical_physical_pairs": len(pair_rows),
        "canonical_physical_completed_runs": len(physical_audits),
        "canonical_physical_deep_checks_passed": sum(
            sum(run["checks"].values()) for run in physical_audits
        ),
        "canonical_physical_deep_checks_total": sum(len(run["checks"]) for run in physical_audits),
        "full_scale_yaw360_aborts_preserved": len(yaw_aborts),
        "upstream_manifests": {
            "passed": sum(item["status"] == "passed" for item in upstream_verification),
            "total": len(upstream_verification),
            "files_checked": sum(item["checked"] for item in upstream_verification),
            "bytes_checked": sum(item["checked_bytes"] for item in upstream_verification),
            "failures": sum(len(item["failures"]) for item in upstream_verification),
        },
        "known_exclusions": KNOWN_EXCLUSIONS,
        "hardware_state_at_freeze": {
            "python_control_processes": 0,
            "last_controlled_shutdown_reported_all_four_outputs_zero": True,
            "final_q8_reopen_zero_check": "unavailable: HILError -108; cleanup call HILError -88",
        },
    }
    (OUT / "AUDIT_SUMMARY.json").write_text(json.dumps(audit_summary, indent=2) + "\n", encoding="utf-8")

    freeze_files = set()
    for path in DIRECT.rglob("*"):
        if path.is_file():
            freeze_files.add(path)
    for path in registry_paths.values():
        if path.exists():
            freeze_files.add(path)
    for path in OUT.iterdir():
        if path.is_file() and path.name != "FROZEN_SHA256_MANIFEST.json":
            freeze_files.add(path)
    freeze = {
        "schema": 1,
        "scope": "canonical direct-Nengo physical data plus campaign audit anchors",
        "files": [
            {"path": str(path), "bytes": path.stat().st_size, "sha256": sha256(path)}
            for path in sorted(freeze_files, key=lambda p: str(p).lower())
        ],
    }
    (OUT / "FROZEN_SHA256_MANIFEST.json").write_text(json.dumps(freeze, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(audit_summary, indent=2))
    print(f"freeze_manifest_sha256={sha256(OUT / 'FROZEN_SHA256_MANIFEST.json')}")
    print(f"output={OUT}")


if __name__ == "__main__":
    main()
