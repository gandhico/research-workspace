"""Run/resume the exact 71 audited case definitions without broadening the sweep."""
import argparse
from concurrent.futures import ThreadPoolExecutor,as_completed
import json
from pathlib import Path
import sweep
import regime_probe
import sweep_extensions

def dispatch(c):
    if 'bias' in c or c['backend']=='constant':return sweep_extensions.launch(c)
    if 'gamma' in c:return regime_probe.launch(c)
    return sweep.launch(c)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--jobs',type=int,default=2);a=p.parse_args()
    cases=json.loads(Path(__file__).with_name('reproduction_cases.json').read_text())
    assert len(cases)==71
    failed=[]
    with ThreadPoolExecutor(max_workers=a.jobs) as pool:
        for n,f in enumerate(as_completed([pool.submit(dispatch,c) for c in cases]),1):
            result=f.result();print(n,len(cases),result,flush=True)
            if result[1] not in [0,'cached']:failed.append(result)
    if failed:raise SystemExit(f'Failed cases: {failed}')
