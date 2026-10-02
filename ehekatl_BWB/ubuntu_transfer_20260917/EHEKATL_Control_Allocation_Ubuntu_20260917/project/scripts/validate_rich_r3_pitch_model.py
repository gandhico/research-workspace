#!/usr/bin/env python3
"""Score the frozen R3 pitch predictor on one held-out log without refitting."""
import argparse,csv,json
from pathlib import Path
import numpy as np
from identify_rich_r3_pitch import multistep,lagcorr

ROOT=Path(__file__).resolve().parents[1]
def main():
 p=argparse.ArgumentParser();p.add_argument('csv',type=Path);p.add_argument('--out',type=Path,required=True);p.add_argument('--apply-frozen-gate',action='store_true');a=p.parse_args();artifact=json.loads((ROOT/'configs/rich_R3_pitch_model.json').read_text());model=artifact['selected'];fields=model['fields'];delay=model['delay_samples'];beta=np.array(model['beta'])
 with a.csv.open(newline='') as f:rows=list(csv.DictReader(f))
 keys=set(fields)|{'t_s'};data={k:np.array([float(r[k]) for r in rows]) for k in keys};t=data['t_s'];pre=t<10
 for k in fields:data[k]=data[k]-data[k][pre].mean()
 idx=np.flatnonzero((t>=10)&(t<=50));idx=idx[(idx>=delay)&(idx<len(t)-1)];X=[]
 for field in fields:X.append(data[field][idx-delay] if field=='total_pitch_ratio' else data[field][idx])
 X=np.column_stack(X);y=(data['q_deg_s'][idx+1]-data['q_deg_s'][idx])/(t[idx+1]-t[idx]);res=y-X@beta;rmse=float(np.sqrt(np.mean(res**2)));nrmse=rmse/float(np.std(y));prediction=multistep(data,fields,delay,beta,10,50);multi=float(np.mean([x['rate_nrmse'] for x in prediction.values()]))
 result={'status':'independent_score_no_refit','validation_file':a.csv.name,'frozen_training_file':artifact['training_file'],'model_name':model['name'],'fields':fields,'delay_samples':delay,'beta':model['beta'],'qdot_rmse':rmse,'qdot_nrmse':nrmse,'training_qdot_nrmse':model['training_nrmse'],'validation_to_training_qdot_nrmse_ratio':nrmse/model['training_nrmse'],'recursive_prediction':prediction,'recursive_mean_nrmse':multi,'training_temporal_recursive_mean_nrmse':model['temporal_multistep_mean_nrmse'],'validation_to_training_recursive_ratio':multi/model['temporal_multistep_mean_nrmse'],'residual_lag1':lagcorr(res),'acceptance_note':'No new numeric ratio threshold was frozen before collection; report ratios without retroactive pass/fail.'}
 if a.apply_frozen_gate:
  gate=json.loads((ROOT/'configs/rich_R3_pitch_validation_gate.json').read_text());checks={'qdot_ratio':result['validation_to_training_qdot_nrmse_ratio']<=gate['maximum_validation_to_training_qdot_nrmse_ratio'],'recursive_ratio':result['validation_to_training_recursive_ratio']<=gate['maximum_validation_to_training_recursive_mean_nrmse_ratio'],'residual_lag1':abs(result['residual_lag1'])<=gate['maximum_absolute_residual_lag1']};result['frozen_gate_checks']=checks;result['frozen_gate_pass']=all(checks.values());result['acceptance_note']='Frozen post-design gate applied without refit or reselection.'
 a.out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
