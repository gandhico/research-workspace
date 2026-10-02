"""Backstepping-style facade for the frozen R3 discrete roll-rate LQR."""
from lqr.discrete_cascade_roll_lqr import DiscreteCascadeRollLQR

class LQRController:
    """Expose ``SetPoint``, ``output``, ``clear`` and ``update`` like Backstepping."""
    def __init__(self):
        self._runtime = DiscreteCascadeRollLQR()
        self.clear()

    def clear(self):
        self.SetPoint = 0.0
        self.output = 0.0
        self.raw_output = 0.0
        self.last_result = {}
        self._runtime.reset()

    def update(self, feedback_value, total_roll_perturbation, ctrl_value):
        error = float(feedback_value) - float(self.SetPoint)
        self.last_result = self._runtime.update(error, total_roll_perturbation, ctrl_value)
        self.output = self.last_result["command"]
        self.raw_output = self.last_result["raw_command"]
        return self.output
