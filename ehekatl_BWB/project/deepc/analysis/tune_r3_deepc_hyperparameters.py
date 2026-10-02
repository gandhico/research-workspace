#!/usr/bin/env python3
"""Training/model-only robust DeePC penalty scan; held-out logs remain closed."""

from __future__ import annotations

import itertools,json,sys
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
import deepc.analysis.replay_r3_deepc_uncertainty_vectorized as replay
from synthesize_rich_r3_roll_discrete_lqr import matrices

OUT=ROOT/'configs/rich_R3_deepc_hyperparameter_scan.json'
RU_VALUES=(.001,.003,.01)
RDU_VALUES=(.005,.01,.02,.05)

def main():
 ctrl,center,scale=replay.build();model=json.loads((ROOT/'configs/rich_R3_roll_discrete_cascade.json').read_text());yt=model['yoke_to_total']['selected']['beta'];sp=model['surface_to_p']['selected']['beta'];g=model['total_to_surface']['static_gain'];scales=list(itertools.product((.75,1.,1.25),repeat=5));ab=[matrices(yt[0]*s[0],yt[1]*s[1],yt[2]*s[2],g,sp[0]*s[3],sp[1]*s[4]) for s in scales];a=np.stack([x[0] for x in ab]);b=np.stack([x[1] for x in ab]);lqr=replay.simulate(a,b,'lqr',ctrl,center,scale);results=[]
 for ru,rdu in itertools.product(RU_VALUES,RDU_VALUES):
  replay.RU=ru;replay.RDU=rdu;candidate=replay.simulate(a,b,'deepc',ctrl,center,scale);ir=candidate['integral']/lqr['integral'];pr=candidate['peak']/lqr['peak'];record={'r_u':ru,'r_du':rdu,'worst_integral_ratio':float(ir.max()),'median_integral_ratio':float(np.median(ir)),'worst_peak_ratio':float(pr.max()),'maximum_sent_command':float(candidate['maxcmd'].max()),'maximum_base_slew':float(candidate['maxslew'].max()),'optimizer_nonconverged_updates':int(candidate['nonconv'].sum()),'passes_fixed_gates':bool(ir.max()<=.90 and pr.max()<=1.10 and candidate['maxcmd'].max()<=replay.COMMAND_LIMIT+1e-15 and candidate['maxslew'].max()<=replay.SLEW_LIMIT+1e-15 and candidate['nonconv'].sum()==0)};results.append(record);print(json.dumps(record))
 passing=[x for x in results if x['passes_fixed_gates']];best=min(passing,key=lambda x:x['worst_integral_ratio']) if passing else None
 eligible=[x for x in passing if x['worst_integral_ratio']<=best['worst_integral_ratio']*1.02] if best else []
 # Larger penalties are less aggressive; maximize their normalized sum among
 # candidates within two percent of the strongest robust result.
 selected=max(eligible,key=lambda x:(x['r_u']/max(RU_VALUES)+x['r_du']/max(RDU_VALUES),x['r_du'],x['r_u'])) if eligible else None
 artifact={'status':'pass' if selected else 'fail','training_model_only':True,'held_out_response_files_opened':[],'fixed':{'t_ini':5,'horizon':5,'lambda_g':10.,'q_y':1.,'disturbance_amplitude':replay.AMP,'command_limit':replay.COMMAND_LIMIT,'slew_limit':replay.SLEW_LIMIT,'uncertainty_cases':243,'worst_integral_ratio_gate':.90,'worst_peak_ratio_gate':1.10},'grid':{'r_u':RU_VALUES,'r_du':RDU_VALUES},'selection_rule':'Among fixed-gate passes, choose the least aggressive penalty pair within 2 percent of the minimum worst-case integral ratio.','results':results,'best_effect_candidate':best,'selected_candidate':selected,'pass':bool(selected),'claim_boundary':'Training/model hyperparameter design only; no held-out or X-Plane claim.'};OUT.write_text(json.dumps(artifact,indent=2)+'\n');print(json.dumps({'status':artifact['status'],'best':best,'selected':selected},indent=2));raise SystemExit(0 if selected else 1)

if __name__=='__main__':main()
