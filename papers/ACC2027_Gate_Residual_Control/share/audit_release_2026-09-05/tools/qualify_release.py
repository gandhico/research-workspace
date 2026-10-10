"""Simulation-only qualification of the unchanged relocatable package."""
from pathlib import Path
import subprocess,time,json
REPO=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parents[1]
STAGE=REPO/'share/advisor_reproducibility_2026-09-04/_build/ACC2027_CODE'
PY=STAGE/'.venv/Scripts/python.exe'
tests=[]
def run(label,args):
    start=time.perf_counter()
    with (OUT/'qualification.log').open('a') as log:
        log.write('\n'+label+'\n');log.flush()
        p=subprocess.run([str(PY),str(STAGE/'reproduce.py'),*map(str,args)],cwd=STAGE,stdout=log,stderr=subprocess.STDOUT)
    tests.append({'test':label,'exit_code':p.returncode,'seconds':time.perf_counter()-start})
    (OUT/'qualification.json').write_text(json.dumps({'tests':tests,'scope':'Existing previously clean-installed portable environment. Simulation only; no physical or interactive GUI actuation.'},indent=2))
    print(label,p.returncode,flush=True)
    if p.returncode:raise SystemExit(p.returncode)
run('Core, family, GUI-model and two-platform smoke',['smoke','--output',OUT/'retested'])
run('Hover emulated I/O only',['hover-emulated','--mission','roll','--duration','.1','--output',OUT/'retested'])
run('Three legacy summary routes, smoke',['legacy','--duration','.1','--output',OUT/'retested'])
for platform in ['x2','cf2-rotor']:
    run(platform+' full 45-s Nengo Hard45',['single','--platform',platform,'--mission','hard45','--duration','45','--output',OUT/'retested'])
print('Qualification finished',flush=True)
