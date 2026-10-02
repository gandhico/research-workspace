#!/usr/bin/env python3
"""Freeze the selected R3 DeePC predictor into a runtime-only JSON artifact."""

from __future__ import annotations
import csv,hashlib,json,sys
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from deepc.src.regularized_deepc import RegularizedDeePC

SOURCE=ROOT/'logs/rich_R3_roll_dualrate_pilot_20260712_193416.csv'
OUT=ROOT/'deepc/configs/rich_R3_deepc_runtime.json'

def main():
 with SOURCE.open(newline='') as f:r=np.array([[float(x[k]) for k in ('t_s','yoke_roll_ratio','p_deg_s')] for x in csv.DictReader(f)])
 z=r[(r[:,0]>=5)&(r[:,0]<15),1:];center=z.mean(0);scale=z.std(0,ddof=1);zn=(z-center)/scale;controller=RegularizedDeePC(zn[:,0],zn[:,1],5,5,10.)
 artifact={'schema_version':1,'status':'frozen_offline_runtime_candidate','source_file':str(SOURCE.relative_to(ROOT)),'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'source_window_s':[5.,15.],'sample_rate_hz':35.,'t_ini':5,'horizon':5,'lambda_g':10.,'q_y':1.,'r_u':.01,'r_du':.02,'input_limit':.0002,'slew_limit':.00005,'solver_tolerance':1e-7,'solver_max_iterations':300,'input_center':float(center[0]),'input_scale':float(scale[0]),'output_center':float(center[1]),'output_scale':float(scale[1]),'past_map':controller._past_map.tolist(),'future_input_map':controller._future_input_map.tolist(),'held_out_response_files_opened':[],'claim_boundary':'Frozen offline runtime parameters; no X-Plane authorization.'};OUT.write_text(json.dumps(artifact,indent=2)+'\n');print(json.dumps({k:v for k,v in artifact.items() if k not in ('past_map','future_input_map')},indent=2))

if __name__=='__main__':main()
