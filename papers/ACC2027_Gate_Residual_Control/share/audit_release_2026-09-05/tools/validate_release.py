"""Read-only audit of research inputs; writes only into this release directory."""
from pathlib import Path
import csv, json, hashlib, importlib.util, sys, zipfile, re
import numpy as np
import pandas as pd

REPO=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parents[1]
NEF=REPO/'experiments/nengo_nef_replication_2026-08-29'
STAGE=REPO/'share/advisor_reproducibility_2026-09-04/_build/ACC2027_CODE'
PAPER=REPO/'paper/study/section_II_2026-09-05/source/ACC2027.tex'
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()
def module(name,path):
    s=importlib.util.spec_from_file_location(name,path); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
def rows(p):
    with Path(p).open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))
def main():
    OUT.mkdir(exist_ok=True)
    report={'manuscript':str(PAPER),'manuscript_sha256':sha(PAPER),'scope':'Saved-data reconciliation and code/algebra checks, not a stability proof or physical retest.'}
    m=module('previous_checks',REPO/'paper/tools/audit_v5_checks.py')
    report['algebra']=m.algebra_checks()
    primary=[]
    for row in rows(NEF/'results/compiled/matched_results.csv'):
        if row['mission']=='hover':continue
        cell={'platform':row['platform'],'mission':row['mission'],'runs':[]}
        configs=[]
        for kind,field in [('PD','baseline_run'),('CMG','nengo_run')]:
            p=Path(row[field]); s=json.loads((p/'summary.json').read_text())
            trace=pd.read_csv(p/'trace.csv')
            assert np.isfinite(trace.select_dtypes('number').to_numpy()).all(),p
            assert trace.t.iloc[0]==0 and trace.t.iloc[-1]>=44.99 and np.all(np.diff(trace.t)>0),p
            qe=trace[['qe_w','qe_x','qe_y','qe_z']].to_numpy()
            angle=2*np.arctan2(np.linalg.norm(qe[:,1:],axis=1),np.abs(qe[:,0]))
            assert np.max(np.abs(angle-trace.qerr))<1e-7,p
            if kind=='CMG':
                for j in range(6):
                    assert trace[f'gate_{j}'].between(0,1).all()
                    assert np.allclose(trace[f'activity_{j}'],np.clip(1e5*trace[f'gate_{j}'],0,1),atol=1e-9)
                for j in range(18):assert (abs(trace[f'decoder_w_{j}'])<=6+1e-12).all()
            fullrate=len(trace)==int(s['duration']/s['dt'])
            if fullrate:assert abs(trace.qerr.mean()-s['qerr_mean_rad'])<1e-12
            prefix='baseline' if kind=='PD' else 'nengo'
            assert abs(float(row[prefix+'_mean_rad'])-s['qerr_mean_rad'])<1e-12
            cell['runs'].append({'controller':kind,'directory':str(p),'trace_sha256':sha(p/'trace.csv'),'summary_sha256':sha(p/'summary.json'),'rows':len(trace),'last_t':float(trace.t.iloc[-1]),'mean_rad':s['qerr_mean_rad'],'trace_mean_rad':float(trace.qerr.mean()),'full_rate':fullrate,'bound_occupancy_fraction':s['saturation_fraction']})
            configs.append({k:s.get(k) for k in ['duration','dt','mission','platform','actuator_scale','torque_policy','torque_limits_Nm','initial_angle_deg','seed','disturbance_torque','attitude_noise_std','rate_noise_std']})
        assert configs[0]==configs[1],configs
        cell['matching_summary_configuration']=configs[0]
        cell['reduction_percent']=100*(cell['runs'][0]['mean_rad']-cell['runs'][1]['mean_rad'])/cell['runs'][0]['mean_rad']
        assert abs(cell['reduction_percent']-float(row['mean_improvement_percent']))<1e-9
        primary.append(cell)
        print('Validated primary',cell['platform'],cell['mission'],flush=True)
    report['primary']=primary
    family=rows(NEF/'results/neuron_family_compiled/neuron_family_results.csv')
    assert len(family)==100  # Compiled table excludes the ten PD baselines.
    family_all=list(family)
    for p in sorted((NEF/'results/neuron_family_matched_45s').glob('*/*/classical/summary.json')):
        s=json.loads(p.read_text());family_all.append({'trace':str(p.parent/'trace.csv'),'qerr_mean_rad':s['qerr_mean_rad']})
    assert len(family_all)==110
    checked=0
    for r in family_all:
        p=Path(r['trace']); s=json.loads((p.parent/'summary.json').read_text())
        assert abs(float(r['qerr_mean_rad'])-s['qerr_mean_rad'])<1e-12
        t=pd.read_csv(p,usecols=['t','qerr'])
        assert t.t.iloc[0]==0 and t.t.iloc[-1]>=44.99 and np.all(np.diff(t.t)>0)
        assert np.isfinite(t.to_numpy()).all()
        checked+=len(t)
    report['family']={'cells':len(family_all),'compiled_neural_rows':len(family),'trace_rows_checked':checked,'max_logged_activity':max(float(r['activity_max']) for r in family if r['activity_max']),'scope':'All summary means reconciled; all CSV time/error sequences checked. Full NPZ contents not re-audited in this release.'}
    hroot=Path('C:/Research/hover3dof/nengo_gui_hil_2026-08-29/results')
    hp=rows(hroot/'hardware_armed_roll_n3_2026-09-01/armed_roll_n3_paired_trials.csv')
    b=np.array([float(r['pd_mean_error_deg']) for r in hp]); n=np.array([float(r['cmg_mean_error_deg']) for r in hp]); imp=100*(b-n)/b
    assert np.allclose(imp,[float(r['paired_mean_improvement_percent']) for r in hp],atol=1e-10)
    report['hover_roll']={'n_pairs':len(hp),'pd_mean_deg':b.mean(),'pd_sd_deg':b.std(ddof=1),'cmg_mean_deg':n.mean(),'cmg_sd_deg':n.std(ddof=1),'reduction_mean_percent':imp.mean(),'reduction_sd_percent':imp.std(ddof=1),'metric':'wrapped Euler-error vector norm, not quaternion angle','scope':'paired table recomputation; raw hardware trace audit recorded separately'}
    provenance=[]
    for r in rows(STAGE/'SOURCE_MAP.csv'):
        original=Path(r['source'])
        provenance.append({'path':r['bundle_path'],'original_exists':original.is_file(),'source_unchanged':original.is_file() and sha(original)==r['source_sha256'],'package_matches_source':sha(STAGE/r['bundle_path'])==r['source_sha256'],'declared_change':r['change']})
    report['packaged_source_audit']=provenance
    report['source_change_count']=sum(not r['source_unchanged'] for r in provenance)
    report['changed_sources']=[r for r in provenance if not r['source_unchanged']]
    for r in provenance: assert r['package_matches_source'] or r['declared_change']!='none',r
    text=PAPER.read_text(encoding='utf-8')
    labels=re.findall(r'\\label\{([^}]+)\}',text)
    refs=re.findall(r'\\(?:eqref|ref)\{([^}]+)\}',text)
    report['paper_crossrefs']={'undefined':sorted(set(refs)-set(labels)),'duplicate_labels':sorted(k for k in set(labels) if labels.count(k)>1),'figures':[{'label':re.search(r'\\label\{([^}]+)\}',f).group(1),'graphics':re.findall(r'\\includegraphics[^\n]+',f)} for f in re.findall(r'\\begin\{figure\*?\}.*?\\end\{figure\*?\}',text,re.S)]}
    report['status']='Completed within stated scopes; substantive interpretation findings in AUDIT.md'
    (OUT/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Changed sources:',json.dumps(report['changed_sources'],indent=2),flush=True)
    print(json.dumps({'primary_pairs':len(primary),'family_cells':len(family),'source_change_count':report['source_change_count'],'output':str(OUT/'validation.json')},indent=2))
if __name__=='__main__':main()
