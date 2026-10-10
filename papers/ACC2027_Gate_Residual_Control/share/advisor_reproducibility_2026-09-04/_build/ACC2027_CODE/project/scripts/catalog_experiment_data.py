"""Build a machine-readable catalog of ACC and Hover run artifacts."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

import numpy as np


DEFAULT_ROOTS = (
    Path(r"C:\Research\papers\ACC2027_Gate_Residual_Control"),
    Path(r"C:\Research\hover3dof"),
)


def sha256(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def resolve_artifact(value, summary_path: Path):
    if not value:
        return None
    path = Path(value)
    if not path.is_absolute():
        path = summary_path.parent / path
    return path.resolve()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, default=Path(r"C:\Research\papers\ACC2027_Gate_Residual_Control\docs\data_catalog_2026-08-31"))
    parser.add_argument("--hash-large-files", action="store_true")
    parser.add_argument(
        "--deep-neural-stats",
        action="store_true",
        help="Catalog every NPZ signal with shape, dtype, finite check, and descriptive statistics.",
    )
    args = parser.parse_args()
    args.output_root.mkdir(parents=True, exist_ok=True)
    records = []
    for root in DEFAULT_ROOTS:
        for summary_path in root.rglob("summary.json"):
            try:
                summary = json.loads(summary_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError):
                continue
            config = summary.get("config", {})
            artifacts = {
                "trace": resolve_artifact(summary.get("trace"), summary_path),
                "neural_trace": resolve_artifact(
                    summary.get("neural_trace_full_rate") or summary.get("neural_trace_2khz"),
                    summary_path,
                ),
                "neural_schema": resolve_artifact(summary.get("neural_trace_schema"), summary_path),
                "manifest": (summary_path.parent / "manifest.json").resolve(),
            }
            record = {
                "repository_root": str(root),
                "summary": str(summary_path.resolve()),
                "experiment": summary.get("experiment", summary.get("platform", "unknown")),
                "platform": summary.get("platform", config.get("io_mode")),
                "controller": summary.get("controller", config.get("controller")),
                "mission": summary.get("mission", config.get("mission")),
                "duration_s": summary.get("duration", config.get("duration")),
                "run_completed": summary.get("run_completed", True),
                "abort_reason": summary.get("abort_reason", ""),
                "qerr_mean_rad": summary.get("qerr_mean_rad"),
                "qerr_max_rad": summary.get("qerr_max_rad"),
                "angle_err_mean_deg": summary.get("angle_err_mean_deg"),
                "angle_err_max_deg": summary.get("angle_err_max_deg"),
                "residual_mean_Nm": summary.get("residual_mean_Nm"),
                "saturation_fraction": summary.get("saturation_fraction"),
            }
            for name, path in artifacts.items():
                exists = bool(path and path.exists())
                record[name] = str(path) if path else None
                record[f"{name}_exists"] = exists
                record[f"{name}_bytes"] = path.stat().st_size if exists else None
                if exists and (args.hash_large_files or path.stat().st_size <= 10 * 1024 * 1024):
                    record[f"{name}_sha256"] = sha256(path)
                else:
                    record[f"{name}_sha256"] = None
            records.append(record)
    records.sort(key=lambda row: (str(row["platform"]), str(row["mission"]), str(row["controller"]), row["summary"]))
    fields = sorted({name for record in records for name in record})
    with (args.output_root / "experiment_data_catalog.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader(); writer.writerows(records)
    (args.output_root / "experiment_data_catalog.json").write_text(json.dumps(records, indent=2) + "\n", encoding="utf-8")
    plots = []
    for root in DEFAULT_ROOTS:
        for extension in ("*.png", "*.pdf", "*.pptx"):
            for path in root.rglob(extension):
                if "results" in {part.lower() for part in path.parts} or path.suffix.lower() == ".pptx":
                    plots.append({"path": str(path.resolve()), "bytes": path.stat().st_size, "kind": path.suffix.lower()})
    (args.output_root / "visual_artifact_catalog.json").write_text(json.dumps(plots, indent=2) + "\n", encoding="utf-8")

    neural_records = []
    if args.deep_neural_stats:
        seen = set()
        for record in records:
            value = record.get("neural_trace")
            if not value:
                continue
            archive_path = Path(value)
            key = str(archive_path.resolve()).lower()
            if key in seen or not archive_path.exists():
                continue
            seen.add(key)
            schema_path = archive_path.with_name("neural_trace_schema.json")
            schema = {}
            if schema_path.exists():
                try:
                    schema = json.loads(schema_path.read_text(encoding="utf-8"))
                except (json.JSONDecodeError, UnicodeDecodeError):
                    schema = {}
            try:
                with np.load(archive_path, allow_pickle=False) as archive:
                    for signal in archive.files:
                        values = np.asarray(archive[signal])
                        numeric = np.issubdtype(values.dtype, np.number)
                        finite = bool(np.all(np.isfinite(values))) if numeric else None
                        item = {
                            "archive": str(archive_path.resolve()),
                            "summary": record["summary"],
                            "platform": record["platform"],
                            "controller": record["controller"],
                            "mission": record["mission"],
                            "signal": signal,
                            "shape": "x".join(str(n) for n in values.shape),
                            "dtype": str(values.dtype),
                            "samples": int(values.shape[0]) if values.ndim else 1,
                            "elements": int(values.size),
                            "uncompressed_bytes": int(values.nbytes),
                            "all_finite": finite,
                            "sample_rate_hz": schema.get("sample_rate_hz"),
                        }
                        if numeric and values.size:
                            item.update({
                                "min": float(np.min(values)),
                                "max": float(np.max(values)),
                                "mean": float(np.mean(values)),
                                "std": float(np.std(values)),
                                "rms": float(np.sqrt(np.mean(np.asarray(values, dtype=float) ** 2))),
                                "nonzero_fraction": float(np.mean(values != 0)),
                            })
                        neural_records.append(item)
            except (OSError, ValueError) as exc:
                neural_records.append({
                    "archive": str(archive_path.resolve()),
                    "summary": record["summary"],
                    "platform": record["platform"],
                    "controller": record["controller"],
                    "mission": record["mission"],
                    "signal": "__ARCHIVE_ERROR__",
                    "error": str(exc),
                })
        if neural_records:
            neural_fields = sorted({name for item in neural_records for name in item})
            with (args.output_root / "neural_signal_catalog.csv").open("w", newline="", encoding="utf-8") as stream:
                writer = csv.DictWriter(stream, fieldnames=neural_fields)
                writer.writeheader(); writer.writerows(neural_records)
            (args.output_root / "neural_signal_catalog.json").write_text(
                json.dumps(neural_records, indent=2) + "\n", encoding="utf-8"
            )
    print(json.dumps({
        "runs": len(records),
        "visual_artifacts": len(plots),
        "neural_signals": len(neural_records),
        "output": str(args.output_root),
    }, indent=2))


if __name__ == "__main__":
    main()
