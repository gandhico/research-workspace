#!/usr/bin/env python3
"""Verify packaged runtime identity against the design optimizer."""
import csv,json,sys,time
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
from deepc.src.regularized_deepc import RegularizedDeePC
from deepc.src.r3_roll_runtime import R3RollDeePCRuntime
from synthesize_rich_r3_roll_discrete_lqr import matrices

def main():
 config=json.loads((ROOT/'deepc/configs/rich_R3_deepc_runtime.json').read_text());model=json.loads((ROOT/'configs/rich_R3_roll_discrete_cascade.json').read_text());yt=model['yoke_to_total']['selected']['beta'];sp=model['surface_to_p']['selected']['beta'];a,b=matrices(yt[0],yt[1],yt[2],model['total_to_surface']['static_gain'],sp[0],sp[1]);design=RegularizedDeePC(np.zeros(20),np.zeros(20),5,5,10.);design._past_map=np.array(config['past_map']);design._future_input_map=np.array(config['future_input_map']);runtime=R3RollDeePCRuntime();x=np.zeros(3);uh=np.zeros(5);ph=np.zeros(5);commands=[];errors=[];runtimes=[]
 for n in range(1050):
  current_p=float(x[0]);ph=np.r_[ph[1:],current_p];uini=uh/config['input_scale'];pini=ph/config['output_scale'];began=time.perf_counter();reference=np.zeros(5);expected=design.optimize(uini,pini,reference,config['input_limit']/config['input_scale'],config['slew_limit']/config['input_scale'],q_y=config['q_y'],r_u=config['r_u'],r_du=config['r_du'],tolerance=config['solver_tolerance'],max_iterations=config['solver_max_iterations']);actual=runtime.update(current_p);runtimes.append((time.perf_counter()-began)*1000);command=expected.future_u[0]*config['input_scale'];errors.append(abs(command-actual['command']));commands.append(command);uh=np.r_[uh[1:],command];t=n/35;d=0.
  for i,start in enumerate((10.,12.)):
   if start<=t<=start+.2:d=(1 if i%2==0 else -1)*.00005*np.sin(np.pi*(t-start)/.2)
  x=a@x+b[:,0]*(command+d)
 artifact={'samples':1050,'maximum_command_identity_error':float(max(errors)),'peak_command':float(max(abs(np.array(commands)))),'runtime_combined_design_and_packaged_ms_median':float(np.median(runtimes)),'runtime_combined_design_and_packaged_ms_max':float(max(runtimes)),'fallback_latched':runtime.latched,'pass':bool(max(errors)<=1e-15 and not runtime.latched),'claim_boundary':'Offline exact-runtime identity only.'};(ROOT/'configs/rich_R3_deepc_runtime_identity.json').write_text(json.dumps(artifact,indent=2)+'\n');print(json.dumps(artifact,indent=2));raise SystemExit(0 if artifact['pass'] else 1)
if __name__=='__main__':main()
