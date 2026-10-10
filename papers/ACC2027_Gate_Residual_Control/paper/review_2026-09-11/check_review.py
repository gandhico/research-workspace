"""Read-only numerical audit of manuscript evidence and proposed local theorem.

Does not modify experimental code, traces, or frozen summaries.
"""
import json, csv, itertools
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[1]
TABLES = HERE / 'evidence/data/data/tables'
EXP = PROJECT / 'experiments/nengo_nef_replication_2026-08-29'
report = {}
rows = list(csv.DictReader((TABLES/'noise_sensitivity.csv').open()))
report['noise'] = {
    'moderate_sd_range_percentage_points': [min(float(r['n1_moderate_red_sd']) for r in rows),max(float(r['n1_moderate_red_sd']) for r in rows)],
    'higher_sd_range_percentage_points': [min(float(r['n2_realistic_red_sd']) for r in rows),max(float(r['n2_realistic_red_sd']) for r in rows)],
    'higher_reduction_range_percent': [min(float(r['n2_realistic_red']) for r in rows),max(float(r['n2_realistic_red']) for r in rows)],
    'metric': 'runner computes qerr from noise-corrupted q_meas, not independent ground truth',
}
families = list(csv.DictReader((TABLES/'nengo_neuron_family_benchmark.csv').open()))
report['family']={f:{'mean_requested_residual_utilization_rms':float(np.mean([float(r['residual_utilization_rms']) for r in families if r['family_mode']==f])), 'mean_reduction':float(np.mean([float(r['improvement_pct']) for r in families if r['family_mode']==f]))} for f in sorted(set(r['family_mode'] for r in families))}
report['local_theory']={}
models = {
 'CF2': (np.diag([2.3951e-5,2.3951e-5,3.2347e-5]),np.array([2.3951e-5,2.3951e-5,3.2347e-5]),.0325,.0325,.005),
 'X2': (np.array([[.03665169811320774,0,-.0021],[0,.025411698113207686,0],[-.0021,0,.060528000000000325]]),np.array([.060711294842784244,.0364684032704233,.025411698113207547]),.14,.18,.0201),
}
rng = np.random.default_rng(123)
for name,(J,j,px,py,k) in models.items():
    Kq=np.diag(2*j*np.array([4,4,3.5])**2)
    Kw=np.diag(2*.95*j*np.array([4,4,3.5]))
    A=np.block([[np.zeros((3,3)),.5*np.eye(3)],[-np.linalg.solve(J,Kq),-np.linalg.solve(J,Kw)]])
    E=np.vstack([np.zeros((1,3)),np.eye(3)])
    H=E.T
    B=np.array([[1,1,1,1],[-py,py,py,-py],[px,px,-px,-px],[-k,k,-k,k]])
    Binv=np.linalg.inv(B)
    LA=max(np.linalg.norm(H@B@np.diag(d)@Binv@E,2) for d in itertools.product([0,1],repeat=4))
    # Q_L=I; all state components are expressed in fixed SI numerical units.
    P=np.linalg.solve(np.kron(np.eye(6),A.T)+np.kron(A.T,np.eye(6)),-np.eye(6).reshape(-1,order='F')).reshape((6,6),order='F')
    G=np.vstack([np.zeros((3,3)),np.linalg.inv(J)])
    pmin,pmax=np.linalg.eigvalsh(P)[[0,-1]]
    L=np.sqrt((.25*(1+.25/(1+np.sqrt(1-.25**2))))**2+np.linalg.cond(J)**2)
    r=min(.25,1/(4*np.linalg.norm(P,2)*L))
    c=1-2*np.linalg.norm(P,2)*L*r
    b=np.linalg.norm(P@G,2)
    dmax=c*r*np.sqrt(pmin/pmax)/(2*b)
    ell=np.maximum(j*np.array([12,12,10]),1e-6)
    max_violation=0.
    for _ in range(1000):
        t=rng.uniform(0,4)
        u0=rng.uniform(-1,1,3)*ell
        delta=rng.uniform(-.5,.5,3)*ell
        u=np.clip(u0+delta,-ell,ell)
        fmax=np.ones(4)*(13 if name=='X2' else .13125)
        out=lambda x:H@B@np.clip(Binv@np.r_[t,x],0,fmax)
        max_violation=max(max_violation,np.linalg.norm(out(u)-out(u0))-LA*np.linalg.norm(u-u0))
    report['local_theory'][name]={
       'J_body':J.tolist(),'j_tune':j.tolist(),'A':A.tolist(),'P':P.tolist(),
       'eigenvalues_A':[[float(z.real),float(z.imag)] for z in np.linalg.eigvals(A)],
       'P_eigenvalue_range':[float(pmin),float(pmax)],
       'lyapunov_residual_norm':float(np.linalg.norm(A.T@P+P@A+np.eye(6))),
       'allocator_L2_gain':float(LA),'random_allocator_bound_max_violation':float(max_violation),
       'conservative_example_r':float(r),'sufficient_dbar_Nm_strictly_below':float(dmax),
       'beta_0_5_allocator_bound_Nm':float(.5*LA*np.linalg.norm(ell)),
       'scope':'Local nominal continuous-time attitude result. Bounds do NOT certify beta=0.5 experiments or sampled-data implementation.'}

report['disturbance']={}
for tag,sub,pdname,cmgname in [
 ('X2_45','hover_intermittent_2026-09-05','pd_disturbed','cmg_disturbed'),
 ('X2_180','final_sweep_2026-09-05/B_long_hover','classical','nengo-nef-pes'),
 ('CF2_45','final_sweep_2026-09-05/C_cf2_hover','classical','nengo-nef-pes')]:
    base=EXP/'results'/sub
    summ=[json.loads((base/n/'summary.json').read_text()) for n in [pdname,cmgname]]
    names=['t','qerr']+[f'decoder_w_{i}' for i in range(18)]
    trace=[]
    for n in [pdname,cmgname]:
        with (base/n/'trace.csv').open() as f:
            reader=csv.DictReader(f)
            trace.append(np.array([[float(row.get(k,0)) for k in names] for row in reader]))
    a,b=trace
    assert np.allclose(a[:,0],b[:,0])
    t=a[:,0]; burst=(t>=5)&(((t-5)%10)<5); quiet=(t>=5)&~burst
    intervals=[]
    for lo in range(5,int(t[-1])+1,5):
        m=(t>=lo)&(t<lo+5)
        intervals.append({'start_s':lo,'phase':'burst' if (lo-5)%10==0 else 'quiet','reduction_pct':float(100*(1-b[m,1].mean()/a[m,1].mean()))})
    W0=np.c_[np.eye(3),-np.eye(3)].reshape(18)
    report['disturbance'][tag]={
      'source':str(base),'torque_Nm':summ[0]['disturbance_torque_Nm'],
      'full_rate_mean_rad':[s['qerr_mean_rad'] for s in summ],
      'mean_reduction_pct':100*(1-summ[1]['qerr_mean_rad']/summ[0]['qerr_mean_rad']),
      'burst_means_deg':[float(np.rad2deg(x[burst,1].mean())) for x in trace],
      'quiet_means_deg':[float(np.rad2deg(x[quiet,1].mean())) for x in trace],
      'intervals':intervals,'burst_count':sum(x['phase']=='burst' for x in intervals),
      'last_decoder_displacement':float(np.linalg.norm(b[-1,2:]-W0)),
      'maximum_absolute_decoder_entry':float(np.abs(b[:,2:]).max()),
    }
(HERE/'review_checks.json').write_text(json.dumps(report,indent=2))
print(json.dumps({k:v for k,v in report.items() if k!='disturbance'},indent=2))
print(json.dumps(report['disturbance'],indent=2))
