"""Frozen guarded runtime for the R3 P-only DeePC candidate."""

from __future__ import annotations
import json
from pathlib import Path
import numpy as np

from deepc.src.regularized_deepc import RegularizedDeePC

DEFAULT_CONFIG=Path(__file__).resolve().parents[1]/'configs/rich_R3_deepc_runtime.json'

class R3RollDeePCRuntime:
 def __init__(self,config_path=DEFAULT_CONFIG):
  self.config=json.loads(Path(config_path).read_text());self.past_map=np.asarray(self.config['past_map'],float);self.future_map=np.asarray(self.config['future_input_map'],float);self._prepare_optimizer();self.reset()
 def _prepare_optimizer(self):
  c=self.config;n=c['horizon'];m=self.future_map;self._reference=np.zeros(n);self._difference=np.eye(n);self._difference[1:,:-1]-=np.eye(n-1);self._previous_vector=np.zeros(n);self._hessian=c['q_y']*(m.T@m)+c['r_u']*np.eye(n)+c['r_du']*(self._difference.T@self._difference);self._step=.95/max(np.linalg.eigvalsh(self._hessian)[-1],1e-12);self._limit=c['input_limit']/c['input_scale'];self._slew=c['slew_limit']/c['input_scale']
 def reset(self):self.u_history=np.zeros(self.config['t_ini']);self.p_history=np.zeros(self.config['t_ini']);self.previous_command=0.;self.latched=False;self.latch_reason=''
 def latch(self,reason):self.latched=True;self.latch_reason=str(reason);return {'command':0.,'fallback_required':True,'reason':self.latch_reason,'converged':False,'iterations':0}
 def update(self,p_error_deg_s):
  if self.latched:return {'command':0.,'fallback_required':True,'reason':self.latch_reason,'converged':False,'iterations':0}
  if not np.isfinite(p_error_deg_s):return self.latch('non-finite P input')
  c=self.config;current_p_history=np.r_[self.p_history[1:],float(p_error_deg_s)];u_ini=self.u_history/c['input_scale'];p_ini=current_p_history/c['output_scale'];past=np.r_[u_ini,p_ini];constant=self.past_map@past;m=self.future_map;prev=self.previous_command/c['input_scale'];self._previous_vector.fill(0.);self._previous_vector[0]=prev;linear=c['q_y']*m.T@(constant-self._reference)-c['r_du']*self._difference.T@self._previous_vector;u=np.full(c['horizon'],prev);converged=False
  for iteration in range(1,c['solver_max_iterations']+1):
   candidate=RegularizedDeePC._project_input(u-self._step*(self._hessian@u+linear),prev,self._limit,self._slew)
   if np.max(np.abs(candidate-u))<=c['solver_tolerance']:u=candidate;converged=True;break
   u=candidate
  if not converged:return self.latch('optimizer did not converge')
  command=float(u[0]*c['input_scale'])
  if not np.isfinite(command):return self.latch('non-finite optimizer command')
  if abs(command)>c['input_limit']+1e-15 or abs(command-self.previous_command)>c['slew_limit']+1e-15:return self.latch('optimizer bound inconsistency')
  self.previous_command=command;self.u_history=np.r_[self.u_history[1:],command];self.p_history=current_p_history
  return {'command':command,'fallback_required':False,'reason':'','converged':True,'iterations':iteration}
