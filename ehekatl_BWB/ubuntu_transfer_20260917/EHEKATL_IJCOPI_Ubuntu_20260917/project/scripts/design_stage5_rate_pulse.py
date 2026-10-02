#!/usr/bin/env python3
"""Audit the frozen Stage-5 pitch disturbance pulse over model uncertainty."""

import itertools, json
from pathlib import Path
import numpy as np
from synthesize_stage4_lqr import c2d_rk4, DT, COMMAND_LIMIT, SLEW_PER_SAMPLE

ROOT=Path(__file__).resolve().parents[1]
PULSE_START=10.0; PULSE_DURATION=0.5; PULSE_AMPLITUDE=0.0002; TOTAL_SECONDS=30.0

def pulse(t):
    if t<PULSE_START or t>PULSE_START+PULSE_DURATION:return 0.0
    return PULSE_AMPLITUDE*np.sin(np.pi*(t-PULSE_START)/PULSE_DURATION)

def simulate(beta,delay,gain):
    ac=np.array([[0.,1.],[beta[0],beta[1]]]);bc=np.array([[0.],[beta[2]]]);ad,bd=c2d_rk4(ac,bc)
    x=np.zeros(2);history=[0.,0.,0.,0.];previous=0.;angles=[];rates=[];commands=[]
    for n in range(round(TOTAL_SECONDS/DT)):
        t=n*DT;disturbance=pulse(t);state=np.array([x[1],*history[:3]])
        requested=float((-gain@state).item())+disturbance
        command=float(np.clip(requested,previous-SLEW_PER_SAMPLE,previous+SLEW_PER_SAMPLE));command=float(np.clip(command,-COMMAND_LIMIT,COMMAND_LIMIT))
        delayed=history[delay-1];x=ad@x+bd[:,0]*delayed;history=[command,*history[:-1]];previous=command
        angles.append(x[0]);rates.append(x[1]);commands.append(command)
    t=np.arange(len(rates))*DT;post=(t>=PULSE_START)&(t<20);final=t>=25
    return {"peak_abs_pitch_deg":float(max(abs(np.array(angles)))),"peak_abs_q_deg_s":float(max(abs(np.array(rates)[post]))),
            "final_5s_max_abs_q_deg_s":float(max(abs(np.array(rates)[final]))),"final_5s_max_abs_pitch_deg":float(max(abs(np.array(angles)[final]))),
            "peak_command":float(max(abs(np.array(commands)))),"max_slew":float(max(abs(np.diff([0.]+commands)))),
            "saturation_fraction":float(np.mean(abs(np.array(commands))>=COMMAND_LIMIT-1e-12))}

def main():
    stage3=json.loads((ROOT/'configs/stage3_models.json').read_text());stage4=json.loads((ROOT/'configs/stage4_lqr_design.json').read_text())
    model=stage3['models']['pitch'];gain=np.array(stage4['controllers']['pitch']['inner_rate_controller']['K_rate_history'])
    beta=np.array(model['beta']);stderr=np.array(model['stderr']);cases=[]
    for signs in itertools.product((-2.,0.,2.),repeat=3):
        varied=beta+np.array(signs)*stderr
        for delay in (2,3,4):cases.append({"sigma_offsets":signs,"delay_samples":delay,**simulate(varied,delay,gain)})
    summary={"pulse":{"start_s":PULSE_START,"duration_s":PULSE_DURATION,"amplitude":PULSE_AMPLITUDE},"cases":len(cases),
             "min_peak_abs_q_deg_s":min(x['peak_abs_q_deg_s'] for x in cases),"max_peak_abs_q_deg_s":max(x['peak_abs_q_deg_s'] for x in cases),
             "max_final_5s_abs_q_deg_s":max(x['final_5s_max_abs_q_deg_s'] for x in cases),"max_final_5s_abs_pitch_deg":max(x['final_5s_max_abs_pitch_deg'] for x in cases),
             "max_peak_command":max(x['peak_command'] for x in cases),"max_slew":max(x['max_slew'] for x in cases),
             "max_saturation_fraction":max(x['saturation_fraction'] for x in cases)}
    out=ROOT/'configs/stage5_pitch_rate_pulse_design.json';out.write_text(json.dumps({"summary":summary,"cases":cases},indent=2)+'\n');print(json.dumps(summary,indent=2))

if __name__=='__main__':main()
