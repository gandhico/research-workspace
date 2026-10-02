"""Complete the Roll gain range after observing its strong gain sensitivity."""
from concurrent.futures import ThreadPoolExecutor
import sweep

if __name__=='__main__':
    cases=[dict(platform='x2',mission='roll',backend='direct',gain=1000000,chi=chi) for chi in [0,1]]
    with ThreadPoolExecutor(max_workers=2) as pool:
        for result in pool.map(sweep.launch,cases): print(result,flush=True)
