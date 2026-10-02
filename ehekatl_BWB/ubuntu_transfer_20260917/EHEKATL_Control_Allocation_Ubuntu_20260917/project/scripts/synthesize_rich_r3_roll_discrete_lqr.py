#!/usr/bin/env python3
"""Synthesize and audit a 35 Hz rate-only LQR from the validated discrete cascade."""
import csv,itertools,json
from pathlib import Path
import numpy as np
from synthesize_stage4_lqr import solve_dare
ROOT=Path(__file__).resolve().parents[1];MODEL=ROOT/'configs/rich_R3_roll_discrete_cascade.json';LIMIT=.0002;SLEW=.00005;RATE_SCALE=.05
LOGS=(ROOT/'logs/rich_R3_roll_dualrate_pilot_20260712_193416.csv',ROOT/'logs/rich_R3_roll_dualrate_confirmation_20260712_194543.csv')
def matrices(at,b0,b1,g,ap,c):
 A=np.array([[ap,c*g*at,c*g*b1],[0,at,b1],[0,0,0]],float);B=np.array([[c*g*b0],[b0],[1.]],float);return A,B
def bounded(k,x,previous):
 raw=float(-k@x);value=max(-LIMIT,min(LIMIT,raw));value=max(previous-SLEW,min(previous+SLEW,value));return value,raw
def simulate(A,B,k,initial,steps=700):
 x=np.array(initial,float);u=0.;peak=0;sat=0;hist=[]
 for _ in range(steps):
  u,raw=bounded(k,x,u);sat+=abs(raw)>LIMIT or abs(u-(hist[-1][0] if hist else 0))>=SLEW-1e-15;x=A@x+B[:,0]*u;peak=max(peak,abs(u));hist.append((u,*x))
 a=np.array(hist);return {'peak_command':peak,'saturation_fraction':sat/steps,'final_5s_max_abs_p_deg_s':float(np.max(np.abs(a[-175:,1]))),'final_5s_max_abs_total_roll':float(np.max(np.abs(a[-175:,2]))),'history':a}
def replay(path,k):
 with path.open(newline='') as f:r=list(csv.DictReader(f))
 t=np.array([float(x['t_s']) for x in r]);pre=t<5;p=np.array([float(x['p_deg_s']) for x in r]);total=np.array([float(x['total_roll_ratio']) for x in r]);u_meas=np.array([float(x['yoke_roll_ratio']) for x in r]);p-=p[pre].mean();total-=total[pre].mean();u_meas-=u_meas[pre].mean();previous=0.;commands=[];raw=[]
 for i in range(len(r)):previous,z=bounded(k,np.array([p[i],total[i],u_meas[i]]),previous);commands.append(previous);raw.append(z)
 return {'file':path.name,'peak_abs_command':float(np.max(np.abs(commands))),'peak_abs_raw':float(np.max(np.abs(raw))),'saturation_samples':int(np.sum(np.abs(raw)>LIMIT)),'maximum_slew':float(np.max(np.abs(np.diff(commands))))}
def main():
 m=json.loads(MODEL.read_text());yt=m['yoke_to_total']['selected'];sp=m['surface_to_p']['selected'];at=yt['beta'][0];b0,b1=yt['beta'][1:];g=m['total_to_surface']['static_gain'];ap,c=sp['beta'];A,B=matrices(at,b0,b1,g,ap,c);Q=np.diag([1/RATE_SCALE**2,0,0]);R=np.array([[1/LIMIT**2]]);K=solve_dare(A,B,Q,R)[0].reshape(-1);closed=A-B@K.reshape(1,-1);nominal=np.linalg.eigvals(closed);cont=np.column_stack((B,A@B,A@A@B));cases=[]
 for scales in itertools.product((.75,1.,1.25),repeat=5):
  Av,Bv=matrices(at*scales[0],b0*scales[1],b1*scales[2],g,ap*scales[3],c*scales[4]);poles=np.linalg.eigvals(Av-Bv@K.reshape(1,-1));cases.append(float(np.max(np.abs(poles))))
 stresses=[simulate(A,B,K,[p,0,0]) for p in (.005,.01,-.005,-.01)];replays=[replay(p,K) for p in LOGS];result={'status':'offline_candidate','sample_rate_hz':35,'state':['p_error_deg_s','total_roll_perturbation','previous_yoke_perturbation'],'input':'next_yoke_perturbation','angle_feedback':0.0,'bryson_rate_scale_deg_s':RATE_SCALE,'rate_scale_selection':'smallest audited candidate among 0.01/0.02/0.03/0.05/0.10 with zero raw saved-log replay saturation','A_discrete':A.tolist(),'B_discrete':B.tolist(),'controllability_rank':int(np.linalg.matrix_rank(cont)),'Q':Q.tolist(),'R':R.tolist(),'gain_K':K.tolist(),'nominal_closed_loop_poles':[[float(x.real),float(x.imag)] for x in nominal],'nominal_spectral_radius':float(np.max(np.abs(nominal))),'limits':{'command_abs':LIMIT,'slew_per_35hz_sample':SLEW},'uncertainty':{'coefficient_scale_grid':[.75,1,1.25],'cases':len(cases),'worst_spectral_radius':max(cases),'unstable_cases':sum(x>=1 for x in cases)},'stress':[ {k:v for k,v in x.items() if k!='history'} for x in stresses],'saved_log_replay':replays,'claim_boundary':'offline rate-only candidate; no roll angle feedback and no flight validation'}
 out=ROOT/'configs/rich_R3_roll_discrete_lqr.json';out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
