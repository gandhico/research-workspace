"""Shared Quanser HyperLIF residual validation utilities."""

from .platforms import PLATFORM_CONFIGS, get_platform_config
from .runner import run_benchmark

__all__ = ["PLATFORM_CONFIGS", "get_platform_config", "run_benchmark"]

