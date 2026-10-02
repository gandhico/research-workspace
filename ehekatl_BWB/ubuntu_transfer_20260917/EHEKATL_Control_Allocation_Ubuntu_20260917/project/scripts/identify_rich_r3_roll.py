#!/usr/bin/env python3
"""Training-only R3 roll candidate selection; never opens validation logs."""
import csv,json
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[1];TRAIN=ROOT/'logs/rich_R3_roll_training_01_20260712_184050.csv';FIT=(10.,50.)
CANDIDATES={'local':('roll_deg','p_deg_s','total_roll_ratio'),'aerodynamic':('roll_deg','p_deg_s','beta_deg','tas_m_s','total_roll_ratio'),'coupled':('roll_deg','p_deg_s','beta_deg','tas_m_s','q_deg_s','r_deg_s','alpha_deg','total_roll_ratio'),'surface_aerodynamic':('roll_deg','p_deg_s','beta_deg','tas_m_s','distributed_ail1_wing2l_deg'),'surface_coupled':('roll_deg','p_deg_s','beta_deg','tas_m_s','q_deg_s','r_deg_s','alpha_deg','distributed_ail1_wing2l_deg')}
INPUTS=('total_roll_ratio','distributed_ail1_wing2l_deg')
def load():
 with TRAIN.open(newline='') as f:r=list(csv.DictReader(f))
 names=set().union(*CANDIDATES.values())|{'t_s'};data={k:np.array([float(x[k]) for x in r]) for k in names};pre=data['t_s']<10
 for k in set().union(*CANDIDATES.values()):data[k]-=data[k][pre].mean()
 return data
def matrix(data,fields,delay,lo,hi):
 t=data['t_s'];idx=np.flatnonzero((t>=lo)&(t<=hi));idx=idx[(idx>=delay)&(idx<len(t)-1)];X=np.column_stack([data[f][idx-delay] if f in INPUTS else data[f][idx] for f in fields]);y=(data['p_deg_s'][idx+1]-data['p_deg_s'][idx])/(t[idx+1]-t[idx]);return X,y
def fit(X,y,Xv):
 scale=X.std(0);scale[scale<1e-12]=1;Xs=X/scale;b=np.linalg.lstsq(Xs,y,rcond=None)[0]/scale;return b,Xv@b,float(np.linalg.cond(Xs))
def lag1(x):
 z=x-x.mean();d=z@z;return float(z[:-1]@z[1:]/d) if d else 0.
def multistep(data,fields,delay,beta,lo,hi):
 t=data['t_s'];valid=np.flatnonzero((t>=lo)&(t<=hi));first,last=int(valid[0]),int(valid[-1]);out={}
 for horizon in (1,5,10,20):
  errors=[]
  for start in range(max(first,delay),last-horizon):
   angle=float(data['roll_deg'][start]);rate=float(data['p_deg_s'][start])
   for step in range(horizon):
    k=start+step;values=[]
    for field in fields:
     if field=='roll_deg':values.append(angle)
     elif field=='p_deg_s':values.append(rate)
     elif field in INPUTS:values.append(data[field][k-delay])
     else:values.append(data[field][k])
    dt=t[k+1]-t[k];accel=beta@np.array(values);angle+=dt*rate;rate+=dt*accel
   errors.append(rate-data['p_deg_s'][start+horizon])
  rmse=float(np.sqrt(np.mean(np.square(errors))));out[str(horizon)]={'rate_rmse_deg_s':rmse,'rate_nrmse':rmse/float(np.std(data['p_deg_s'][valid]))}
 return out
def main():
 data=load();reports=[]
 for name,fields in CANDIDATES.items():
  for delay in range(5):
   folds=[]
   for train,test in (((10.,30.),(30.,50.)),((30.,50.),(10.,30.))):
    X,y=matrix(data,fields,delay,*train);Xv,yv=matrix(data,fields,delay,*test);b,pred,cond=fit(X,y,Xv);err=yv-pred;multi=multistep(data,fields,delay,b,*test);folds.append({'qdot_label':'pdot','rmse':float(np.sqrt(np.mean(err**2))),'nrmse':float(np.sqrt(np.mean(err**2))/np.std(yv)),'condition_scaled':cond,'multistep':multi,'multistep_mean_nrmse':float(np.mean([x['rate_nrmse'] for x in multi.values()]))})
   X,y=matrix(data,fields,delay,*FIT);b,pred,cond=fit(X,y,X);res=y-pred;reports.append({'name':name,'fields':fields,'delay_samples':delay,'temporal_folds':folds,'temporal_mean_nrmse':float(np.mean([f['nrmse'] for f in folds])),'temporal_multistep_mean_nrmse':float(np.mean([f['multistep_mean_nrmse'] for f in folds])),'beta':b.tolist(),'training_pdot_rmse':float(np.sqrt(np.mean(res**2))),'training_pdot_nrmse':float(np.sqrt(np.mean(res**2))/np.std(y)),'condition_scaled':cond,'residual_lag1':lag1(res),'sample_count':len(y)})
 eligible=[x for x in reports if x['condition_scaled']<1e4 and np.all(np.isfinite(x['beta']))];selected=min(eligible,key=lambda x:x['temporal_multistep_mean_nrmse']);result={'status':'frozen_training_only_predictor','training_file':TRAIN.name,'validation_files_opened':[],'fit_window_s':FIT,'candidate_count':len(reports),'selection_rule':'minimum bidirectional mean recursive 0.1/0.5/1.0/2.0-s rate NRMSE with scaled condition < 1e4','claim_boundary':'pdot/short-horizon predictor; full expanded state dynamics still required before LQR synthesis','selected':selected,'candidates':reports};out=ROOT/'configs/rich_R3_roll_model.json';out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'selected':selected,'candidate_count':len(reports)},indent=2))
if __name__=='__main__':main()
