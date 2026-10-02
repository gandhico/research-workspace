#!/usr/bin/env python3
"""Validate the frozen 35 Hz discrete roll cascade without refitting."""
import argparse,csv,json,sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'));from identify_rich_r3_roll_discrete_cascade import rolling
def main():
 p=argparse.ArgumentParser();p.add_argument('csv',type=Path);p.add_argument('--out',type=Path,required=True);a=p.parse_args();model=json.loads((ROOT/'configs/rich_R3_roll_discrete_cascade.json').read_text());gate=json.loads((ROOT/'configs/rich_R3_roll_discrete_cascade_gate.json').read_text())
 with a.csv.open(newline='') as f:r=list(csv.DictReader(f))
 t=np.array([float(x['t_s']) for x in r]);pre=t<5;data={'t':t,'yoke':np.array([float(x['yoke_roll_ratio']) for x in r]),'total':np.array([float(x['total_roll_ratio']) for x in r]),'surface':np.array([float(x['aileron_wing2l_deg']) for x in r]),'p':np.array([float(x['p_deg_s']) for x in r])}
 for k in ('yoke','total','surface','p'):data[k]-=data[k][pre].mean()
 def score(stage,u,y):
  s=stage['selected'];pred=rolling(data,u,y,np.array(s['beta']),s['na'],s['nb'],s['delay_samples'],5,25);mean=float(np.mean([v['nrmse'] for v in pred.values()]));return pred,mean,mean/s['temporal_recursive_mean_nrmse']
 yp,ym,yr=score(model['yoke_to_total'],'yoke','total');sp,sm,sr=score(model['surface_to_p'],'surface','p');gain=model['total_to_surface']['static_gain'];surface_rmse=float(np.sqrt(np.mean((data['surface']-gain*data['total'])**2))/np.std(data['surface']));sent=np.array([float(x['sent_roll_command']) for x in r[:-1]]);yoke=np.array([float(x['yoke_roll_ratio']) for x in r[1:]]);corr=float(np.corrcoef(sent,yoke)[0,1]);checks={'yoke_to_total_ratio':yr<=gate['maximum_yoke_to_total_recursive_nrmse_ratio'],'surface_to_p_ratio':sr<=gate['maximum_surface_to_p_recursive_nrmse_ratio'],'surface_static_map':surface_rmse<=gate['maximum_total_to_surface_relative_rmse'],'command_write':corr>=gate['minimum_sent_to_yoke_lag1_correlation']};result={'status':'independent_score_no_refit','file':a.csv.name,'yoke_to_total_recursive':yp,'yoke_to_total_mean_nrmse':ym,'yoke_to_total_training_nrmse':model['yoke_to_total']['selected']['temporal_recursive_mean_nrmse'],'yoke_to_total_ratio':yr,'surface_to_p_recursive':sp,'surface_to_p_mean_nrmse':sm,'surface_to_p_training_nrmse':model['surface_to_p']['selected']['temporal_recursive_mean_nrmse'],'surface_to_p_ratio':sr,'total_to_surface_relative_rmse':surface_rmse,'sent_to_yoke_lag1_correlation':corr,'checks':checks,'pass':all(checks.values()),'no_refit_or_reselection':True};a.out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2));raise SystemExit(0 if result['pass'] else 1)
if __name__=='__main__':main()
