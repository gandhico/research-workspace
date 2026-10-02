#!/usr/bin/env python3
"""Measure R3 roll spectral richness and distributed-aileron response."""
import argparse,csv,json
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
def read(path):
 with Path(path).open(newline='') as f:return list(csv.DictReader(f))
def spectrum(rows,field,freq,start,end):
 t=np.array([float(r['t_s']) for r in rows]);x=np.array([float(r[field]) for r in rows]);m=(t>=start)&(t<=end);t=t[m];x=x[m]-x[m].mean();out=[]
 for f in freq:
  d=np.column_stack((np.sin(2*np.pi*f*t),np.cos(2*np.pi*f*t)));out.append(float(np.linalg.norm(np.linalg.lstsq(d,x,rcond=None)[0])))
 return np.array(out)
def main():
 p=argparse.ArgumentParser();p.add_argument('csv',type=Path);p.add_argument('--out',type=Path);a=p.parse_args();design=json.loads((ROOT/'configs/rich_R3_excitation_design.json').read_text());freq=design['frequencies_hz'];rows=read(a.csv);base=[read(ROOT/'logs'/name) for name in design['baseline_logs']]
 input_noise=np.max([spectrum(r,'total_roll_ratio',freq,5,29.5) for r in base],axis=0);rate_noise=np.max([spectrum(r,'p_deg_s',freq,5,29.5) for r in base],axis=0);input_amp=spectrum(rows,'total_roll_ratio',freq,10,50);rate_amp=spectrum(rows,'p_deg_s',freq,10,50);input_snr=input_amp/input_noise;rate_snr=rate_amp/rate_noise
 t=np.array([float(r['t_s']) for r in rows]);m=(t>=10)&(t<=50);u=np.array([float(r['total_roll_ratio']) for r in rows])[m];surfaces={}
 for field in ('distributed_ail1_wing2l_deg','distributed_ail1_wing2r_deg','left_aileron_1_def_deg','right_aileron_1_def_deg'):
  x=np.array([float(r[field]) for r in rows])[m];surfaces[field]={'range_deg':[float(x.min()),float(x.max())],'peak_to_peak_deg':float(np.ptp(x)),'correlation_with_total_roll':float(np.corrcoef(u,x)[0,1])}
 checks={'minimum_input_spectral_snr':float(input_snr.min())>=2,'minimum_rate_spectral_snr':float(rate_snr.min())>=5,'surface_motion':all(x['peak_to_peak_deg']>=.001 for x in surfaces.values()),'surface_correlation':all(abs(x['correlation_with_total_roll'])>=.99 for x in surfaces.values())};result={'file':a.csv.name,'frequencies_hz':freq,'realized_input_amplitude':input_amp.tolist(),'realized_input_snr':input_snr.tolist(),'rate_response_amplitude_deg_s':rate_amp.tolist(),'rate_response_snr':rate_snr.tolist(),'surfaces':surfaces,'checks':checks,'pass':all(checks.values())};text=json.dumps(result,indent=2);print(text)
 if a.out:a.out.write_text(text+'\n')
 raise SystemExit(0 if result['pass'] else 1)
if __name__=='__main__':main()
