"""Scientific audit/figures; run with the bundled analysis Python, not hardware."""
from pathlib import Path
import json
import hashlib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE=Path(__file__).resolve().parent
OUT=HERE/'analysis';OUT.mkdir(exist_ok=True)
plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,
                     'pdf.fonttype':42,'ps.fonttype':42,'savefig.dpi':180})

def load_results():
    rows=[]
    for path in sorted((HERE/'results').glob('*/summary.json')):
        s=json.loads(path.read_text())
        if not s.get('complete') or not path.with_name('sweep_manifest.json').exists(): continue
        s['case_id']=path.parent.name
        s['gamma']=s.get('gamma',2.0)
        s['summary_path']=str(path)
        s['controller_backend']={'pd':'none','direct':'canonical-numpy-reference',
                                  'linear':'paired-linear-numpy-reference','constant':'constant-basis-numpy-reference','nengo':'nengo-4.1.0-built-in-PES'}[s['backend']]
        s['nengo_pes_learning_rate']=9.6 if s['backend']=='nengo' else None
        rows.append(s)
    df=pd.DataFrame(rows)
    df['bias']=df['bias'].fillna(.75) if 'bias' in df else .75
    base={(r.platform,r.mission):r.qerr_mean_rad for r in df[df.backend=='pd'].itertuples()}
    df['baseline_mean_rad']=[base.get((r.platform,r.mission),np.nan) for r in df.itertuples()]
    df['improvement_pct']=100*(1-df.qerr_mean_rad/df.baseline_mean_rad)
    scalar=df.drop(columns=[k for k in df if df[k].map(lambda x:isinstance(x,(dict,list))).any()])
    scalar.to_csv(OUT/'all_completed_cases.csv',index=False,float_format='%.12g')
    return df

def verify_direct(s):
    d=np.load(s.neural_trace_full_rate)
    a=d['activity'];w=d['weights_pre'];dw=d['weight_delta'];y=d['target'];z=d['decoded_clipped_pre']
    expected=np.clip(w+.0008*(y-z)[:,:,None]*a[:,None,:]-1e-6*w,-6,6)-w
    check={'case_id':s.case_id,'samples':len(a),'archive_finite':all(np.isfinite(d[k]).all() for k in d.files),
           'pes_increment_max_abs_mismatch':float(np.max(abs(dw-expected))),
           'activity_min':float(a.min()),'activity_max':float(a.max()),
           'weight_max':float(abs(w).max())}
    saturated=np.all(a==1,axis=1)
    bad=np.flatnonzero(~saturated)
    start=0 if len(bad)==0 else int(bad[-1]+1)
    check['all_six_saturated_persistent_start_s']=start*.0005 if start<len(a) else None
    if start < len(a)-1:
        zz=w.sum(axis=2)
        pred=(1-1e-6)*zz[:-1]+6*.0008*(y[:-1]-np.clip(zz[:-1],-1,1))
        check['saturated_filter_recursion_max_abs_mismatch']=float(np.max(abs(zz[1:]-pred)[start:]))
    else: check['saturated_filter_recursion_max_abs_mismatch']=None
    if s.backend=='direct':
        r=d['gate'];v=d['voltage'];current=d['current']
        old_r=np.vstack([np.zeros(6),r[:-1]]);old_v=np.vstack([np.zeros(6),v[:-1]])
        b=1/(1+np.exp(-np.clip(50*(old_v-1+s.gamma*old_r),-60,60)))
        check['gate_step_max_abs_mismatch']=float(np.max(abs(r-(old_r+.1*(b-old_r)))))
        c=(120+30*s.chi*np.abs(current))*r*r
        lam=20+c;decay=np.exp(-lam*.0005)
        expected_v=old_v*decay+(20*current/lam)*(1-decay)
        check['membrane_step_max_abs_mismatch']=float(np.max(abs(v-expected_v)))
    return check

def figures(df):
    labels=[('x2','roll','X2 / Roll'),('x2','full3','X2 / Full3'),('cf2-rotor','hardstep','CF2 1.5x / Hardstep')]
    fig,axs=plt.subplots(3,3,figsize=(12,9),layout='constrained')
    for row,(p,m,title) in enumerate(labels):
        sub=df[(df.platform==p)&(df.mission==m)&(df.backend=='direct')&(df.gamma==2)]
        for chi,style,color in [(0,'--','#7a5195'),(1,'-','#007c91')]:
            d=sub[sub.chi==chi].sort_values('gain')
            for ax,col,scale in zip(axs[row],['improvement_pct','activity_saturated_fraction','conductance_over_leak_mean'],[1,100,1]):
                ax.semilogx(d.gain,d[col]*scale,marker='o',ls=style,color=color,label=fr'$\chi={chi}$')
                ax.grid(alpha=.2);ax.set_xlabel('Readout gain G')
        axs[row,0].set_title(title);axs[row,0].axhline(0,color='gray',lw=.8)
        axs[row,0].set_ylabel('Mean error reduction vs PD (%)')
        axs[row,1].set_ylabel('Activity at ceiling (%)')
        axs[row,2].set_ylabel('Mean conductance / leak')
        axs[row,0].legend()
    fig.suptitle('Gain sensitivity: fixed PES rate and authority; one deterministic run per cell')
    fig.savefig(OUT/'gain_sweep.png');fig.savefig(OUT/'gain_sweep.pdf');plt.close(fig)
    d=np.load(HERE/'open_loop/ramp_states.npz');I=d['current'];t=d['t_s']
    fig,axs=plt.subplots(2,2,figsize=(9,6),layout='constrained')
    for col,gamma in enumerate([2,.5]):
        for chi,style,color in [(0,'--','#7a5195'),(1,'-','#007c91')]:
            arr=d[f'gamma{gamma}_chi{chi}']
            axs[0,col].plot(t,arr[:,0],ls=style,color=color,label=fr'$\chi={chi}$')
            axs[1,col].plot(t,arr[:,1],ls=style,color=color)
        axs[0,col].set_title(fr'Threshold feedback $\gamma={gamma}$')
        axs[0,col].set_ylabel('Membrane v');axs[0,col].legend()
        axs[1,col].set_ylabel('Raw gate r');axs[1,col].set_xlabel('Time (s)')
        for ax in axs[:,col]:ax.grid(alpha=.2)
    fig.suptitle('Matched input: triangular current 0.75 to 2 to 0.75 (peak at 8 s)')
    fig.savefig(OUT/'conductance_regimes.png');fig.savefig(OUT/'conductance_regimes.pdf');plt.close(fig)
    sub=df[(df.backend=='direct')&(df.gamma!=2)&(df.bias==.75)].copy()
    if len(sub):
        fig,axs=plt.subplots(1,2,figsize=(10,4),layout='constrained',sharey=True)
        for ax,m in zip(axs,['full3','hardstep']):
            for gamma,color in [(0,'#c05827'),(.5,'#007c91')]:
                for chi,ls in [(0,'--'),(1,'-')]:
                    x=sub[(sub.mission==m)&(sub.gamma==gamma)&(sub.chi==chi)].sort_values('gain')
                    ax.plot(x.gain,x.improvement_pct,ls=ls,marker='o',color=color,label=fr'$\gamma={gamma},\chi={chi}$')
            ax.set_title('X2 / '+m);ax.set_xlabel('Readout gain G');ax.set_xticks([1,3]);ax.grid(alpha=.2)
        axs[0].set_ylabel('Mean error reduction vs PD (%)');axs[1].legend(fontsize=8)
        fig.suptitle('New intrinsic regimes: development tests, not frozen-paper results')
        fig.savefig(OUT/'regime_tracking.png');fig.savefig(OUT/'regime_tracking.pdf');plt.close(fig)
    sub=df[(df.backend=='direct')&(df.gamma==.5)&(df.bias==1)].copy()
    if len(sub):
        fig,axs=plt.subplots(1,2,figsize=(9,4),layout='constrained')
        for ax,m in zip(axs,['full3','hardstep']):
            for chi,ls,color in [(0,'--','#7a5195'),(1,'-','#007c91')]:
                x=sub[(sub.mission==m)&(sub.chi==chi)].sort_values('gain')
                ax.plot(x.gain,x.improvement_pct,ls=ls,marker='o',color=color,label=fr'$\chi={chi}$')
            ax.set_title('X2 / '+m);ax.set_xlabel('Readout gain G');ax.set_xticks([1,3]);ax.grid(alpha=.2)
            ax.axhline(0,color='gray',lw=.8);ax.legend()
        axs[0].set_ylabel('Mean error reduction vs PD (%)')
        fig.suptitle(r'New operating point: $\gamma=0.5$, $I_b=1.0$ (all outcomes shown)')
        fig.savefig(OUT/'bias_tracking.png');fig.savefig(OUT/'bias_tracking.pdf');plt.close(fig)
    fig,ax=plt.subplots(figsize=(9,4),layout='constrained')
    x=np.arange(3);width=.23
    for j,(backend,label,color) in enumerate([('direct','CMG, G=100000','#007c91'),('linear','Paired-linear + PES','#c05827'),('constant','Constant basis + PES','#7a5195')]):
        vals=[]
        for p,m,_ in labels:
            d=df[(df.platform==p)&(df.mission==m)&(df.backend==backend)]
            if backend=='direct':d=d[(d.gain==100000)&(d.chi==1)&(d.gamma==2)]
            vals.append(float(d.iloc[0].improvement_pct) if len(d) else np.nan)
        bars=ax.bar(x+(j-1)*width,vals,width,label=label,color=color)
        ax.bar_label(bars,fmt='%.2f',padding=3,fontsize=9)
    ax.set_xticks(x,[v[2] for v in labels]);ax.set_ylim(0,70)
    ax.set_ylabel('Mean error reduction vs matched PD (%)');ax.grid(axis='y',alpha=.2)
    ax.legend(loc='upper center',ncols=3,fontsize=9)
    ax.set_title('Same PES teacher, update, authority and plant; different activity bases')
    fig.savefig(OUT/'simple_basis_comparison.png');fig.savefig(OUT/'simple_basis_comparison.pdf');plt.close(fig)

def main():
    df=load_results()
    checks=[]
    for s in df[df.backend.isin(['direct','linear','constant'])].itertuples():
        checks.append(verify_direct(s))
    (OUT/'archive_checks.json').write_text(json.dumps(checks,indent=2,allow_nan=False))
    pairs=[]
    for (p,m,g,gamma,bias),part in df[df.backend=='direct'].groupby(['platform','mission','gain','gamma','bias']):
        if set(part.chi)=={0,1}:
            a=part[part.chi==0].iloc[0];b=part[part.chi==1].iloc[0]
            pairs.append(dict(platform=p,mission=m,gain=g,gamma=gamma,bias=bias,
                error_chi0_rad=a.qerr_mean_rad,error_chi1_rad=b.qerr_mean_rad,
                chi1_reduction_vs_chi0_pct=100*(1-b.qerr_mean_rad/a.qerr_mean_rad),
                pd_reduction_chi0_pct=a.improvement_pct,pd_reduction_chi1_pct=b.improvement_pct))
    pd.DataFrame(pairs).to_csv(OUT/'conductance_pairs.csv',index=False,float_format='%.12g')
    backends=[]
    for s in df[df.backend=='nengo'].itertuples():
        same=df[(df.backend=='direct')&(df.gamma==2)&(df.platform==s.platform)&(df.mission==s.mission)&(df.gain==s.gain)&(df.chi==1)]
        if len(same):
            ref=same.iloc[0]
            backends.append(dict(platform=s.platform,mission=s.mission,gain=s.gain,
                direct_mean_rad=ref.qerr_mean_rad,nengo_mean_rad=s.qerr_mean_rad,
                relative_mean_difference=abs(s.qerr_mean_rad-ref.qerr_mean_rad)/ref.qerr_mean_rad))
    pd.DataFrame(backends).to_csv(OUT/'backend_checks.csv',index=False,float_format='%.12g')
    figures(df)
    (OUT/'status.json').write_text(json.dumps(dict(completed_runs=len(df),
        direct_archive_checks=len(checks),nengo_checks=len(backends),
        expected_focused_runs=28,expected_regime_runs=16,
        max_pes_check=max((c['pes_increment_max_abs_mismatch'] for c in checks),default=0)),indent=2))
    print(df[['case_id','qerr_mean_rad','improvement_pct']].to_string(index=False))

if __name__=='__main__':main()
