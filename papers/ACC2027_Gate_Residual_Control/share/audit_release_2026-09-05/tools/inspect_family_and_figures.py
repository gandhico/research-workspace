from pathlib import Path
import sys,json,zipfile,re,hashlib,subprocess
import numpy as np
from nengo.builder.learning_rules import SimPES
from nengo.builder.signal import Signal
ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parents[1]
NEF=ROOT/'experiments/nengo_nef_replication_2026-08-29'
sys.path.insert(0,str(NEF))
from nengo_neuron_family import NengoNeuronFamilyAugmentor
cal=json.loads((NEF/'feature_calibration.json').read_text())['families']
findings=[]
for family,c in cal.items():
    S=c['feature_scale'];dt=.0005;eta=.0008
    a=np.linspace(.1,.6,6);error=np.array([.2,-.1,.3])
    sig_a=Signal(S*a);sig_e=Signal(error);sig_d=Signal(np.zeros((3,6)))
    signals={sig_a:S*a,sig_e:error,sig_d:np.zeros((3,6))}
    op=SimPES(sig_a,sig_e,sig_d,eta*6/(dt*S))
    op.make_step(signals,dt,None)()
    normalized_delta=S*signals[sig_d]
    equal_normalized_delta=-eta*np.outer(error,a)
    ratio=float(np.linalg.norm(normalized_delta)/np.linalg.norm(equal_normalized_delta))
    assert abs(ratio-S)<1e-10
    model=NengoNeuronFamilyAugmentor(family,np.ones(3),dt,feature_scale=S,native_current_scale=c.get('native_current_scale',1))
    peak=0.
    for _ in range(600):
        model.step(np.ones(3),np.zeros(3));peak=max(peak,float(model.activity.max()))
    model.close()
    findings.append({'family':family,'S':S,'normalized_PES_increment_factor_vs_eta':ratio,'short_test_activity_peak':peak,'equal_normalized_eta_requires_eta_N':'eta*n/(h*S^2); proposed correction NOT implemented','scope':'Isolated actual Nengo SimPES operator test plus 0.3-s live family activity check; no closed-loop ranking retest.'})
(OUT/'family_scaling_check.json').write_text(json.dumps(findings,indent=2))
zpath=Path(r'C:/Users/gandhico/Downloads/Online_PES_Adaptive_HyperLIF_Residual_Control___Quaternions_Tracking (1).zip')
dest=OUT/'source_figures';dest.mkdir(exist_ok=True)
tex=(ROOT/'paper/study/section_II_2026-09-05/source/ACC2027.tex').read_text()
figure_records=[]
with zipfile.ZipFile(zpath) as z:
    for i,f in enumerate(re.findall(r'\\begin\{figure\*?\}.*?\\end\{figure\*?\}',tex,re.S),1):
        label=re.search(r'\\label\{([^}]+)\}',f).group(1)
        paths=[]
        for line in f.splitlines():
            if '\\includegraphics' not in line:continue
            path=line.split(']{',1)[1].rstrip('}')
            path=path.replace('\\detokenize{','')
            match=[n for n in z.namelist() if any(n.endswith(path+ext) for ext in ['.pdf','.png','.jpg']) and not n.startswith('backup/')]
            if len(match)!=1:
                paths.append({'requested':path,'matches':match});continue
            p=dest/f'{i}_{Path(match[0]).name}'
            p.write_bytes(z.read(match[0]))
            text=subprocess.check_output(['pdftotext',str(p),'-'],text=True,encoding='utf-8') if p.suffix=='.pdf' else 'Raster figure: inspected visually.'
            paths.append({'zip_path':match[0],'extracted':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'text':text})
        figure_records.append({'number':i,'label':label,'files':paths})
(OUT/'figure_inventory.json').write_text(json.dumps(figure_records,indent=2))
print(json.dumps({'family':findings,'figures':figure_records},indent=2))
