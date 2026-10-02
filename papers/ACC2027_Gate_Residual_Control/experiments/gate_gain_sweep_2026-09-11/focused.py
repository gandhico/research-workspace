"""Resource-bounded subset; wait for existing own workers before starting."""
import concurrent.futures
import json
from pathlib import Path
import argparse
import sweep

def cases():
    return [c for c in sweep.cases() if (c['platform'],c['mission']) in [('x2','full3'),('cf2-rotor','hardstep')]
            and (c['backend'] in ['pd','linear'] or c['gain'] in [1,1000,100000,1000000])]

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--jobs',type=int,default=2);a=p.parse_args()
    todo=cases();sweep.write_json(Path(__file__).with_name('focused_cases.json'),todo)
    with concurrent.futures.ThreadPoolExecutor(max_workers=a.jobs) as pool:
        for n,f in enumerate(concurrent.futures.as_completed([pool.submit(sweep.launch,c) for c in todo]),1):
            print(n,len(todo),f.result(),flush=True)
