from __future__ import annotations

from dataclasses import dataclass
import numpy as np


@dataclass
class LaneEstimate:
    lane_error: float
    confidence: float
    event_fraction: float
    valid: bool


class TemporalContrastLaneSNN:
    """Dependency-free spiking shadow estimator for QCar camera frames.

    ON/OFF temporal-contrast events feed leaky column neurons; the active
    population centroid estimates lane position. This is a shadow-mode
    integration baseline, not a trained convolutional SNN.
    """

    def __init__(self, width: int, threshold: float = 0.08,
                 membrane_decay: float = 0.90, spike_threshold: float = 2.0,
                 min_event_fraction: float = 1e-3):
        self.width = int(width)
        self.threshold = float(threshold)
        self.decay = float(membrane_decay)
        self.spike_threshold = float(spike_threshold)
        self.min_event_fraction = float(min_event_fraction)
        self.previous: np.ndarray | None = None
        self.membrane = np.zeros(self.width, dtype=float)

    def reset(self) -> None:
        self.previous = None
        self.membrane.fill(0.0)

    def step(self, gray_roi: np.ndarray, desired_x_normalized: float = 0.5) -> LaneEstimate:
        frame = np.asarray(gray_roi, dtype=float)
        if frame.ndim != 2 or frame.shape[1] != self.width:
            raise ValueError(f"Expected grayscale ROI with width {self.width}; got {frame.shape}")
        if frame.max(initial=0.0) > 1.0:
            frame = frame/255.0
        if self.previous is None:
            self.previous = frame.copy()
            return LaneEstimate(0.0, 0.0, 0.0, False)

        delta = frame-self.previous
        self.previous[:] = frame
        events = (delta > self.threshold) | (delta < -self.threshold)
        column_current = np.sum(events, axis=0, dtype=float)
        self.membrane[:] = self.decay*self.membrane+column_current
        spikes = self.membrane >= self.spike_threshold
        self.membrane[spikes] = 0.0

        event_fraction = float(np.mean(events))
        weights = column_current+spikes.astype(float)
        total = float(np.sum(weights))
        valid = event_fraction >= self.min_event_fraction and total > 0.0
        if not valid:
            return LaneEstimate(0.0, 0.0, event_fraction, False)
        x = np.arange(self.width, dtype=float)
        lane_x = float(np.sum(x*weights)/total)/max(self.width-1, 1)
        error = lane_x-float(desired_x_normalized)
        confidence = float(np.clip(event_fraction/(10*self.min_event_fraction), 0.0, 1.0))
        return LaneEstimate(error, confidence, event_fraction, True)

