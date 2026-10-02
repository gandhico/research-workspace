#!/usr/bin/env python3
"""Training-only discrete ARX cascade identification at 35 Hz."""
import csv,json
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];LOG=ROOT/'logs/rich_R3_roll_dualrate_pilot_20260712_193416.csv';WINDOW=(5.,25.);FOLDS=(((5.,15.),(15.,25.)),((15.,25.),(5.,15.)))
def load():
 with LOG.open(newline='') as f:r=list(csv.DictReader(f))
 t=np.array([float(x['t_s']) for x in r]);pre=t<5;data={'t':t,'yoke':np.array([float(x['yoke_roll_ratio']) for x in r]),'total':np.array([float(x['total_roll_ratio']) for x in r]),'surface':np.array([float(x['aileron_wing2l_deg']) for x in r]),'p':np.array([float(x['p_deg_s']) for x in r])}
 for k in ('yoke','total','surface','p'):data[k]-=data[k][pre].mean()
 return data
def design(data,u_name,y_name,na,nb,delay,lo,hi):
 t,u,y=data['t'],data[u_name],data[y_name];start=max(na,delay+nb-1);idx=np.flatnonzero((t>=lo)&(t<=hi)&(np.arange(len(t))>=start));X=[]
 for k in idx:X.append([*(y[k-i] for i in range(1,na+1)),*(u[k-delay-j] for j in range(nb))])
 return np.array(X),y[idx],idx
def fit(X,y):
 scale=X.std(0);scale[scale<1e-14]=1;Xs=X/scale;b=np.linalg.lstsq(Xs,y,rcond=None)[0]/scale;return b,float(np.linalg.cond(Xs))
def poles(beta,na):return np.roots(np.r_[1.,-beta[:na]])
def rolling(data,u_name,y_name,beta,na,nb,delay,lo,hi):
 t,u,y=data['t'],data[u_name],data[y_name];valid=np.flatnonzero((t>=lo)&(t<=hi));first,last=int(valid[0]),int(valid[-1]);out={}
 for horizon in (1,5,10,20):
  errors=[]
  for start in range(max(first,na,delay+nb-1),last-horizon):
   history=list(y[start-na+1:start+1])
   for step in range(1,horizon+1):
    k=start+step;past=[history[-i] for i in range(1,na+1)];inputs=[u[k-delay-j] for j in range(nb)];history.append(float(beta@np.array(past+inputs)))
   errors.append(history[-1]-y[start+horizon])
  rmse=float(np.sqrt(np.mean(np.square(errors))));out[str(horizon)]={'rmse':rmse,'nrmse':rmse/float(np.std(y[valid]))}
 return out
def stage(data,u,y):
 reports=[]
 for na in range(1,4):
  for nb in range(1,4):
   for delay in range(4):
    folds=[]
    for train,test in FOLDS:
     X,z,_=design(data,u,y,na,nb,delay,*train);b,cond=fit(X,z);pred=rolling(data,u,y,b,na,nb,delay,*test);folds.append({'condition':cond,'poles':[[float(x.real),float(x.imag)] for x in poles(b,na)],'stable':bool(np.all(np.abs(poles(b,na))<1)),'recursive':pred,'recursive_mean_nrmse':float(np.mean([v['nrmse'] for v in pred.values()]))})
    X,z,_=design(data,u,y,na,nb,delay,*WINDOW);b,cond=fit(X,z);root=poles(b,na);reports.append({'na':na,'nb':nb,'delay_samples':delay,'beta':b.tolist(),'poles':[[float(x.real),float(x.imag)] for x in root],'stable':bool(np.all(np.abs(root)<1)),'condition':cond,'temporal_folds':folds,'temporal_recursive_mean_nrmse':float(np.mean([f['recursive_mean_nrmse'] for f in folds]))})
 eligible=[r for r in reports if r['stable'] and r['condition']<1e4 and all(f['stable'] and f['condition']<1e4 for f in r['temporal_folds'])];best=min(r['temporal_recursive_mean_nrmse'] for r in eligible);near=[r for r in eligible if r['temporal_recursive_mean_nrmse']<=1.025*best];selected=min(near,key=lambda r:(r['na']+r['nb'],r['delay_samples'],r['temporal_recursive_mean_nrmse']));return selected,reports
def main():
 data=load();yt,yr=stage(data,'yoke','total'),stage(data,'surface','p');surface_gain=float((data['total']@data['surface'])/(data['total']@data['total']));result={'status':'frozen_training_only_discrete_cascade','source_design_log':LOG.name,'validation_files_opened':[],'sample_rate_hz':35.,'fit_window_s':WINDOW,'candidate_count_per_dynamic_stage':36,'selection_rule':'lowest total ARX order among stable condition<1e4 candidates within 2.5 percent of best bidirectional recursive 1/5/10/20-sample mean NRMSE; then minimum delay/error','yoke_to_total':{'selected':yt[0],'candidates':yt[1]},'total_to_surface':{'static_gain':surface_gain,'relative_rmse':float(np.sqrt(np.mean((data['surface']-surface_gain*data['total'])**2))/np.std(data['surface']))},'surface_to_p':{'selected':yr[0],'candidates':yr[1]},'claim_boundary':'discrete measured cascade at 35 Hz; no continuous-time pole inference'}
 out=ROOT/'configs/rich_R3_roll_discrete_cascade.json';out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'yoke_to_total':yt[0],'total_to_surface':result['total_to_surface'],'surface_to_p':yr[0]},indent=2))
if __name__=='__main__':main()
