"""Create an integrity manifest for a result tree without duplicating raw data."""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    parser.add_argument("--label", required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    output = (args.output or root / "FROZEN_SHA256_MANIFEST.json").resolve()
    files = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.resolve() == output:
            continue
        files.append({
            "path": path.relative_to(root).as_posix(),
            "bytes": path.stat().st_size,
            "sha256": sha256(path),
        })
    payload = {
        "schema": 1,
        "label": args.label,
        "frozen_utc": datetime.now(timezone.utc).isoformat(),
        "root": str(root),
        "files": len(files),
        "total_bytes": sum(item["bytes"] for item in files),
        "counts": {
            "summaries": sum(item["path"].endswith("summary.json") for item in files),
            "neural_npz": sum("neural_trace" in item["path"] and item["path"].endswith(".npz") for item in files),
            "schemas": sum(item["path"].endswith("neural_trace_schema.json") for item in files),
            "png": sum(item["path"].endswith(".png") for item in files),
            "pdf": sum(item["path"].endswith(".pdf") for item in files),
        },
        "entries": files,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: payload[key] for key in ("label", "root", "files", "total_bytes", "counts")}, indent=2))
    print(output)


if __name__ == "__main__":
    main()
