#!/usr/bin/env python3
"""Training-only R3 pitch candidate selection; never opens validation logs."""
from __future__ import annotations
import csv,json
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[1];TRAIN=ROOT/'logs/rich_R3_pitch_training_01_revised_20260712_181333.csv';FIT=(10.,50.)
CANDIDATES={
 'local':('pitch_deg','q_deg_s','total_pitch_ratio'),
 'aerodynamic':('pitch_deg','q_deg_s','alpha_deg','tas_m_s','total_pitch_ratio'),
 'coupled':('pitch_deg','q_deg_s','alpha_deg','tas_m_s','p_deg_s','r_deg_s','beta_deg','total_pitch_ratio'),
 'surface_aerodynamic':('pitch_deg','q_deg_s','alpha_deg','tas_m_s','distributed_elv1_wing2l_deg'),
 'surface_coupled':('pitch_deg','q_deg_s','alpha_deg','tas_m_s','p_deg_s','r_deg_s','beta_deg','distributed_elv1_wing2l_deg'),
}
def load():
 with TRAIN.open(newline='') as f:r=list(csv.DictReader(f))
 data={k:np.array([float(x[k]) for x in r]) for k in r[0] if k not in ('test_id','aircraft_config','payload','fuel','weather','failures','routing','start_block_reason','recovery_abort_reason','identification_abort_reason','rate_units_declared','recovery_axis','identification_axis','identification_frequencies_hz','identification_phases_rad') and r[0][k] not in ('True','False','')}
 t=data['t_s'];pre=t<10
 for k in CANDIDATES['surface_coupled']+('total_pitch_ratio',):data[k]=data[k]-data[k][pre].mean()
 return data
def matrix(data,fields,delay,lo,hi):
 t=data['t_s'];idx=np.flatnonzero((t>=lo)&(t<=hi));idx=idx[(idx>=delay)&(idx<len(t)-1)];x=[]
 for field in fields:
  use=idx-delay if field in ('total_pitch_ratio','distributed_elv1_wing2l_deg') else idx;x.append(data[field][use])
 X=np.column_stack(x);y=(data['q_deg_s'][idx+1]-data['q_deg_s'][idx])/(t[idx+1]-t[idx]);return X,y,idx
def fit_predict(X,y,Xv):
 scale=X.std(axis=0);scale[scale<1e-12]=1;Xs=X/scale;beta_s=np.linalg.lstsq(Xs,y,rcond=None)[0];return beta_s/scale,Xv@(beta_s/scale),float(np.linalg.cond(Xs))
def lagcorr(x):
 z=x-x.mean();d=z@z;return float(z[:-1]@z[1:]/d) if d else 0.
def multistep(data,fields,delay,beta,lo,hi):
 t=data['t_s'];valid=np.flatnonzero((t>=lo)&(t<=hi));first,last=int(valid[0]),int(valid[-1]);report={}
 for horizon in (1,5,10,20):
  errors=[]
  for start in range(max(first,delay),last-horizon):
   theta=float(data['pitch_deg'][start]);q=float(data['q_deg_s'][start])
   for step in range(horizon):
    k=start+step;values=[]
    for field in fields:
     if field=='pitch_deg':values.append(theta)
     elif field=='q_deg_s':values.append(q)
     elif field in ('total_pitch_ratio','distributed_elv1_wing2l_deg'):values.append(data[field][k-delay])
     else:values.append(data[field][k])
    dt=t[k+1]-t[k];qdot=beta@np.array(values);theta+=dt*q;q+=dt*qdot
   errors.append(q-data['q_deg_s'][start+horizon])
  rmse=float(np.sqrt(np.mean(np.square(errors))));report[str(horizon)]={'rate_rmse_deg_s':rmse,'rate_nrmse':rmse/float(np.std(data['q_deg_s'][valid]))}
 return report
def main():
 data=load();reports=[]
 for name,fields in CANDIDATES.items():
  for delay in range(5):
   folds=[]
   for train_window,test_window in (((10.,30.),(30.,50.)),((30.,50.),(10.,30.))):
    X,y,_=matrix(data,fields,delay,*train_window);Xv,yv,_=matrix(data,fields,delay,*test_window);beta,pred,cond=fit_predict(X,y,Xv);err=yv-pred;prediction=multistep(data,fields,delay,beta,*test_window);folds.append({'rmse':float(np.sqrt(np.mean(err**2))),'nrmse':float(np.sqrt(np.mean(err**2))/np.std(yv)),'condition_scaled':cond,'multistep':prediction,'multistep_mean_nrmse':float(np.mean([x['rate_nrmse'] for x in prediction.values()]))})
   X,y,_=matrix(data,fields,delay,*FIT);beta,pred,cond=fit_predict(X,y,X);res=y-pred
   reports.append({'name':name,'fields':fields,'delay_samples':delay,'temporal_folds':folds,'temporal_mean_nrmse':float(np.mean([f['nrmse'] for f in folds])),'temporal_multistep_mean_nrmse':float(np.mean([f['multistep_mean_nrmse'] for f in folds])),'beta':beta.tolist(),'training_rmse':float(np.sqrt(np.mean(res**2))),'training_nrmse':float(np.sqrt(np.mean(res**2))/np.std(y)),'condition_scaled':cond,'residual_lag1':lagcorr(res),'sample_count':len(y)})
 eligible=[x for x in reports if x['condition_scaled']<1e4 and all(np.isfinite(x['beta']))]
 selected=min(eligible,key=lambda x:x['temporal_multistep_mean_nrmse']);result={'status':'frozen_training_only_predictor','training_file':TRAIN.name,'validation_files_opened':[],'fit_window_s':FIT,'candidate_count':len(reports),'selection_rule':'minimum bidirectional mean recursive 0.1/0.5/1.0/2.0-s rate NRMSE with scaled condition < 1e4','claim_boundary':'qdot/short-horizon predictor; full expanded state dynamics still required before LQR synthesis','selected':selected,'candidates':reports}
 out=ROOT/'configs/rich_R3_pitch_model.json';out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'selected':selected,'candidate_count':len(reports)},indent=2))
if __name__=='__main__':main()
