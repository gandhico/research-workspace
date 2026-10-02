#!/usr/bin/env python3
"""Offline design of a locally detrended, repeated-pulse R3 roll comparison."""
import csv,json
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];FILES={'baseline':ROOT/'logs/rich_R3_roll_matched_baseline_20260712_203402.csv','lqr':ROOT/'logs/rich_R3_roll_matched_lqr_20260712_203707.csv'};GRID=np.arange(0,1.0001,1/35)
def responses(path):
 r=list(csv.DictReader(path.open(newline='')));t=np.array([float(x['t_s']) for x in r]);p=np.array([float(x['p_deg_s']) for x in r]);out=[]
 for start,sign in ((10,1),(12,-1)):
  pre=(t>=start-.5)&(t<start);trend=np.polyfit(t[pre]-start,p[pre],1);out.append(sign*(np.interp(start+GRID,t,p)-np.polyval(trend,GRID)))
 return np.array(out)
def main():
 resp={k:responses(v) for k,v in FILES.items()};metrics={}
 for k,x in resp.items():
  mean=x.mean(axis=0);metrics[k]={'sign_aligned_peak_abs_p_deg_s':float(np.max(np.abs(mean))),'sign_aligned_integral_abs_p_deg':float(np.trapezoid(np.abs(mean),GRID)),'positive_negative_correlation':float(np.corrcoef(x[0],x[1])[0,1]),'replicate_nrmse':float(np.sqrt(np.mean((x[0]-x[1])**2))/np.ptp(mean)),'individual_integrals':np.trapezoid(np.abs(x),GRID,axis=1).tolist()}
 ratio=metrics['lqr']['sign_aligned_integral_abs_p_deg']/metrics['baseline']['sign_aligned_integral_abs_p_deg'];proposal={'pulse_starts_s':[7,10,13,16,19,22],'pulse_signs':[1,-1,1,-1,1,-1],'pulse_duration_s':.2,'pulse_amplitude':5e-5,'local_pretrend_window_s':.5,'response_window_s':1.,'sample_rate_hz':35,'primary_metric':'integral absolute sign-aligned mean P response','statistical_gate':'paired pulse bootstrap 95-percent upper confidence bound for LQR/baseline integral ratio <1.0','quality_gates':{'pulse_count_each_run':6,'median_opposite_sign_response_correlation_min':.75,'baseline_mean_peak_abs_p_deg_s_min':.0015,'response_snr_min':3.,'command_abs_max':.0002,'command_slew_max':5e-5,'final_5s_abs_p_deg_s_max':.002}}
 out={'status':'offline_metric_and_waveform_proposal_not_flight_authorized','source_use':'failed pair used as design evidence only; frozen failure retained','retrospective_design_metrics':metrics,'retrospective_integral_ratio':ratio,'interpretation':'about 9.1 percent locally detrended improvement; two pulses per run are insufficient to establish a confidence bound','proposed_experiment':proposal,'required_before_flight':['moving-block bootstrap power audit using immutable background residuals','243-case repeated-waveform command/safety audit','new default-observe wrapper and exact waveform analyzer','fresh observe-only X-Plane gate'],'claim_boundary':'offline statistical experiment redesign only'};path=ROOT/'configs/rich_R3_roll_statistical_comparison_design.json';path.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
if __name__=='__main__':main()
