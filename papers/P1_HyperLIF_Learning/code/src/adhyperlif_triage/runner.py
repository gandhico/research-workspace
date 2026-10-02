"""Config-driven entry point for the triage benchmark.

One YAML config == one matrix slice. Today the ``parity`` mode is wired (the validation gate);
the dataset/training modes (``smoke``/``tiny``/``stress``) are explicit stubs that mark exactly
where Phase 1 (Tonic adapters + surrogate-gradient trainer) plugs in. This keeps the skeleton
honest: nothing claims to run until it actually does.

Usage:
    python -m adhyperlif_triage.runner --config configs/parity_smoke.yaml
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from .neurons import HyperLIFConfig


def load_config(path: str | Path) -> dict[str, Any]:
    import yaml

    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def build_neuron_config(spec: dict[str, Any]) -> HyperLIFConfig:
    """Map a config ``neuron`` block onto a :class:`HyperLIFConfig` (unknown keys ignored)."""
    valid = HyperLIFConfig().to_dict().keys()
    return HyperLIFConfig(**{k: v for k, v in (spec or {}).items() if k in valid})


def _run_parity() -> int:
    # Defer to the standalone parity script so there is a single source of truth.
    import runpy

    script = Path(__file__).resolve().parents[2] / "scripts" / "run_parity.py"
    runpy.run_path(str(script), run_name="__main__")
    return 0


def _run_benchmark(cfg: dict) -> int:
    from .train import run_smoke

    t = cfg.get("train", {}) or {}
    run_smoke(
        dataset=cfg.get("dataset", "synthetic"),
        mode=cfg.get("mode", "smoke"),
        seeds=tuple(t.get("seeds", [0, 1, 2])),
        epochs=int(t.get("epochs", 5)),
        hidden=int(t.get("hidden", 64)),
        lr=float(t.get("lr", 1e-3)),
        dt=float(t.get("dt", 1e-3)),
        T=int(t.get("T", 20)),
        input_scale=float(t.get("input_scale", 16.0)),
        batch_size=int(t.get("batch_size", 16)),
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Adaptive HyperLIF triage runner")
    ap.add_argument("--config", required=True, help="path to a YAML experiment config")
    args = ap.parse_args(argv)

    cfg = load_config(args.config)
    mode = cfg.get("mode", "parity")
    if mode == "parity":
        return _run_parity()
    if mode in {"smoke", "tiny"}:
        return _run_benchmark(cfg)
    if mode == "stress":
        raise NotImplementedError("stress mode (hard/noisy datasets) arrives with the Tonic adapter")
    raise ValueError(f"unknown mode: {mode!r}")


if __name__ == "__main__":
    raise SystemExit(main())
