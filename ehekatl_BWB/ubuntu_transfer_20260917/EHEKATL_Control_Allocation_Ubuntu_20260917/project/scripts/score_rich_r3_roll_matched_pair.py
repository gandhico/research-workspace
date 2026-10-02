#!/usr/bin/env python3
"""Apply the frozen matched roll LQR-versus-baseline performance gates."""
import argparse,csv,json
from pathlib import Path
import numpy as np
def metrics(path):
 r=list(csv.DictReader(path.open(newline='')));t=np.array([float(x['t_s']) for x in r]);p=np.array([float(x['p_deg_s']) for x in r]);p-=p[(t>=5)&(t<9)].mean();active=(t>=10)&(t<18);final=t>=25;return {'peak_abs_p_deg_s':float(np.max(np.abs(p[active]))),'integral_abs_p_deg':float(np.trapezoid(np.abs(p[active]),t[active])),'final_5s_max_abs_p_deg_s':float(np.max(np.abs(p[final])))}
def main():
 p=argparse.ArgumentParser();p.add_argument('baseline',type=Path);p.add_argument('lqr',type=Path);a=p.parse_args();b=metrics(a.baseline);l=metrics(a.lqr);peak=l['peak_abs_p_deg_s']/b['peak_abs_p_deg_s'];integral=l['integral_abs_p_deg']/b['integral_abs_p_deg'];checks={'baseline_measurable':b['peak_abs_p_deg_s']>=.0015,'peak_non_degradation':peak<=1.10,'integral_improvement':integral<=.70,'baseline_settled':b['final_5s_max_abs_p_deg_s']<=.002,'lqr_settled':l['final_5s_max_abs_p_deg_s']<=.002};out={'baseline':str(a.baseline),'lqr':str(a.lqr),'baseline_metrics':b,'lqr_metrics':l,'peak_ratio':peak,'integral_ratio':integral,'checks':checks,'pass':all(checks.values()),'claim_boundary':'matched R3 roll-rate disturbance performance only'};print(json.dumps(out,indent=2));raise SystemExit(0 if out['pass'] else 1)
if __name__=='__main__':main()
