#!/usr/bin/env python3
"""Score frozen R3 roll predictor on held-out data without refitting."""
import argparse,csv,json
from pathlib import Path
import numpy as np
from identify_rich_r3_roll import multistep,lag1,INPUTS
ROOT=Path(__file__).resolve().parents[1]
def main():
 p=argparse.ArgumentParser();p.add_argument('csv',type=Path);p.add_argument('--out',type=Path,required=True);a=p.parse_args();artifact=json.loads((ROOT/'configs/rich_R3_roll_model.json').read_text());model=artifact['selected'];fields=model['fields'];delay=model['delay_samples'];beta=np.array(model['beta'])
 with a.csv.open(newline='') as f:rows=list(csv.DictReader(f))
 data={k:np.array([float(r[k]) for r in rows]) for k in set(fields)|{'t_s'}};t=data['t_s'];pre=t<10
 for k in fields:data[k]-=data[k][pre].mean()
 idx=np.flatnonzero((t>=10)&(t<=50));idx=idx[(idx>=delay)&(idx<len(t)-1)];X=np.column_stack([data[f][idx-delay] if f in INPUTS else data[f][idx] for f in fields]);y=(data['p_deg_s'][idx+1]-data['p_deg_s'][idx])/(t[idx+1]-t[idx]);res=y-X@beta;rmse=float(np.sqrt(np.mean(res**2)));nrmse=rmse/float(np.std(y));prediction=multistep(data,fields,delay,beta,10,50);multi=float(np.mean([x['rate_nrmse'] for x in prediction.values()]));gate=json.loads((ROOT/'configs/rich_R3_roll_validation_gate.json').read_text());checks={'pdot_ratio':nrmse/model['training_pdot_nrmse']<=gate['maximum_validation_to_training_pdot_nrmse_ratio'],'recursive_ratio':multi/model['temporal_multistep_mean_nrmse']<=gate['maximum_validation_to_training_recursive_mean_nrmse_ratio'],'residual_lag1':abs(lag1(res))<=gate['maximum_absolute_residual_lag1']}
 result={'status':'independent_score_no_refit','validation_file':a.csv.name,'frozen_training_file':artifact['training_file'],'model_name':model['name'],'fields':fields,'delay_samples':delay,'beta':model['beta'],'pdot_rmse':rmse,'pdot_nrmse':nrmse,'training_pdot_nrmse':model['training_pdot_nrmse'],'validation_to_training_pdot_nrmse_ratio':nrmse/model['training_pdot_nrmse'],'recursive_prediction':prediction,'recursive_mean_nrmse':multi,'training_temporal_recursive_mean_nrmse':model['temporal_multistep_mean_nrmse'],'validation_to_training_recursive_ratio':multi/model['temporal_multistep_mean_nrmse'],'residual_lag1':lag1(res),'frozen_gate_checks':checks,'frozen_gate_pass':all(checks.values()),'no_refit_or_reselection':True};a.out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2));raise SystemExit(0 if result['frozen_gate_pass'] else 1)
if __name__=='__main__':main()
