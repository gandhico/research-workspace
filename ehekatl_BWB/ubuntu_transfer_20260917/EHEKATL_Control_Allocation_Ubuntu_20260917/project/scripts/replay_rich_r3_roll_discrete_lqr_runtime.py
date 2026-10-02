#!/usr/bin/env python3
"""Replay the exact runtime roll LQR over saved high-rate logs."""
import csv,json,sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'lqr'));from discrete_cascade_roll_lqr import DiscreteCascadeRollLQR
LOGS=(ROOT/'logs/rich_R3_roll_dualrate_pilot_20260712_193416.csv',ROOT/'logs/rich_R3_roll_dualrate_confirmation_20260712_194543.csv')
def replay(path):
 with path.open(newline='') as f:r=list(csv.DictReader(f))
 t=np.array([float(x['t_s']) for x in r]);pre=t<5;p=np.array([float(x['p_deg_s']) for x in r]);total=np.array([float(x['total_roll_ratio']) for x in r]);yoke=np.array([float(x['yoke_roll_ratio']) for x in r]);p-=p[pre].mean();total-=total[pre].mean();yoke-=yoke[pre].mean();c=DiscreteCascadeRollLQR();out=[c.update(*x) for x in zip(p,total,yoke)];commands=np.array([x['command'] for x in out]);return {'file':path.name,'rows':len(r),'peak_abs_command':float(np.max(np.abs(commands))),'maximum_slew':float(np.max(np.abs(np.diff(commands)))),'magnitude_limited_samples':sum(x['magnitude_limited'] for x in out),'slew_limited_samples':sum(x['slew_limited'] for x in out)}
def main():
 result={'runtime':'lqr/discrete_cascade_roll_lqr.py','replays':[replay(p) for p in LOGS]};out=ROOT/'configs/rich_R3_roll_discrete_lqr_runtime_replay.json';out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
