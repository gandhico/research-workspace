"""Backstepping-style facade for the frozen R3 P-only DeePC controller."""
from deepc.src.r3_roll_runtime import R3RollDeePCRuntime

class DeePC:
    """Expose ``SetPoint``, ``output``, ``clear`` and ``update`` like Backstepping."""
    def __init__(self, config_path=None):
        self._runtime = R3RollDeePCRuntime() if config_path is None else R3RollDeePCRuntime(config_path)
        self.clear()

    def clear(self):
        self.SetPoint = 0.0
        self.output = 0.0
        self.last_result = {}
        self._runtime.reset()

    def update(self, feedback_value, ctrl_value=None):
        error = float(feedback_value) - float(self.SetPoint)
        self.last_result = self._runtime.update(error)
        self.output = self.last_result["command"]
        return self.output

    @property
    def fallback_required(self):
        return bool(self.last_result.get("fallback_required", False))
