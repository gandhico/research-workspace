#!/usr/bin/env python3
"""Exact bounded 35 Hz rate-only LQR for the validated R3 discrete roll cascade."""
import numpy as np
K=np.array([0.0002943998507329812,0.0027424434530730407,0.02925278612522486])
COMMAND_LIMIT=.0002;SLEW_LIMIT=.00005
class DiscreteCascadeRollLQR:
 def __init__(self):self.reset()
 def reset(self):self.previous_command=0.
 def update(self,p_error_deg_s,total_roll_perturbation,previous_yoke_perturbation):
  state=np.array([p_error_deg_s,total_roll_perturbation,previous_yoke_perturbation],float);raw=float(-K@state);bounded=max(-COMMAND_LIMIT,min(COMMAND_LIMIT,raw));command=max(self.previous_command-SLEW_LIMIT,min(self.previous_command+SLEW_LIMIT,bounded));self.previous_command=command;return {'command':command,'raw_command':raw,'magnitude_limited':abs(raw)>COMMAND_LIMIT,'slew_limited':abs(command-bounded)>1e-15}
