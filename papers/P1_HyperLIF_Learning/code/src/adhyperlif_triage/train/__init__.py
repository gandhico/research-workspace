"""Training: supervised surrogate-BPTT trainer, the roster, and benchmark orchestration."""

from .benchmark import run_smoke
from .roster import origin_roster, phase1_roster, phase1b_roster
from .trainer import train_and_eval

__all__ = ["run_smoke", "phase1_roster", "phase1b_roster", "origin_roster", "train_and_eval"]
