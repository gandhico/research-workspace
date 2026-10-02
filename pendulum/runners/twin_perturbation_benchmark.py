"""Qube3 pendulum twin — disturbance-rejection benchmark with LED error gauge.

Protocol (matches the spirit of the Jun-14 hardware trials, but automated):
  PHASE 1  SWINGUP  : energy swing-up from rest                      LED blue
  PHASE 2  CENTER   : hold equilibrium, wait until the ARM is centred LED cyan
                      (|theta| small) so there is symmetric room to move
  PHASE 3  PERTURB  : repeated identical voltage impulses; between
                      impulses the controller must recover            LED green->red gauge
  shutdown          : 0 V, amplifier off                              LED red

Every controller variant sees the SAME perturbation schedule (same times, same
amplitude, same width), so recovery is directly comparable.

Metrics per perturbation: peak |alpha| after onset, and recovery time back
under RECOVER_DEG. Plus the usual tail RMS over the whole perturbed phase.

Usage
-----
  python twin_perturbation_benchmark.py [method] [neuron] [v_pert] [blend]
    method : baseline | fixed_gate | online_pes | eprop_anneal
    neuron : lif | hyperlif | adaptive_hyperlif | izhikevich | none
"""
from __future__ import annotations
import sys, time, json, csv
from pathlib import Path

sys.path.insert(0, r"C:\Quanser\0_libraries\python")
sys.path.insert(0, r"C:\02_Research\00_Code_Ecosystem\neuromorphic-robotics-control\experiments\controller_benchmarks")
import numpy as np
from pal.products.qube import QubeServo3
from neuron_dynamics import make_direct_neuron

METHOD = sys.argv[1] if len(sys.argv) > 1 else "baseline"
NEURON = sys.argv[2] if len(sys.argv) > 2 else "hyperlif"
V_PERT = float(sys.argv[3]) if len(sys.argv) > 3 else 2.5
BLEND  = float(sys.argv[4]) if len(sys.argv) > 4 else 0.25
KC_SW  = float(sys.argv[5]) if len(sys.argv) > 5 else 3.0   # arm-centring gain during swing-up
K_TH_C = float(sys.argv[6]) if len(sys.argv) > 6 else 2.5   # extra theta pull while centring

HZ = 500.0; DT = 1.0/HZ
SETTLE_S   = 3.0            # balanced time required before centring check
CENTER_DEG = 25.0           # |theta| must be under this to start perturbing
CENTER_TIMEOUT_S = 8.0
N_PERT     = 6              # number of impulses
PERT_PERIOD = 4.0           # seconds between impulse onsets
PERT_WIDTH  = 0.12          # impulse duration (s)
RECOVER_DEG = 2.0           # |alpha| considered "recovered"
POST_S     = 3.0            # tail after the last impulse

MU=100.0; V_SW=10.0; KC=1.0
K = np.array([-1.000, 26.72, -0.8269, 2.214])
V_BAL=5.0; V_MAX=10.0
CAPTURE_RAD=np.radians(20.0); CAPTURE_RATE=6.0
CAPTURE_THETA=np.radians(110.0); HOLD_RAD=np.radians(45.0)
GATE_GAIN=1e5; CURRENT_BIAS=0.75; CURRENT_GAIN=1.25
K_ERR=8.0; LR=8e-4; K_RATE=0.3; LEAK=1e-3; W_CLIP=6.0
ALPHA_NORM=CAPTURE_RAD; RATE_NORM=6.0
Rm=7.5; kt=0.0422; mr=0.095; r=0.085; mp=0.024; Lp=0.129; l=Lp/2; g=9.81
Jp_cm=mp*Lp**2/12; Er=2*mp*g*l
a_max=(kt*10.0/Rm)/(mr*r); ACC2V=mr*r*Rm/kt

wrap=lambda x:(x+np.pi)%(2*np.pi)-np.pi
def f(x): return float(np.asarray(x,dtype=float).reshape(-1)[0])
LED_IDLE=np.array([1.,0.,0.]); LED_SWING=np.array([0.,0.,1.])
LED_CENTER=np.array([0.,1.,1.]); LED_SETTLE=np.array([1.,1.,0.])
def led_gauge(a):
    e=float(np.clip(abs(a)/CAPTURE_RAD,0,1)); return np.array([e,1.0-e,0.0])

use_res = METHOD!="baseline"
learn = METHOD in ("online_pes","eprop_anneal")
elig = anneal = (METHOD=="eprop_anneal")
neuron = make_direct_neuron(NEURON,n=6,activity_mode="gate",scale="control") if use_res else None
W=np.array([0.,0.,0.,0.,1.,-1.]); e_trace=np.zeros(6)

print("="*74)
print(f"QUBE3 TWIN — PERTURBATION BENCHMARK :: {METHOD} / {NEURON if use_res else '-'} "
      f"| V_pert={V_PERT} V x{N_PERT} every {PERT_PERIOD}s")
print("="*74)

q=QubeServo3(id=0,hardware=0,frequency=int(HZ),pendulum=1,readMode=1)
if not q.card.is_valid(): print("FAILED: card invalid"); sys.exit(1)

def settle_and_reference(qq, timeout=40.0, pos_tol=np.radians(0.5), hold=1.5):
    """Wait for the pendulum to hang at rest; return its raw angle.

    NOTE: the tachometer has a persistent offset (~0.061 rad/s) that never drops
    below a naive speed tolerance, so a speed-based rest detector can NEVER fire.
    Rest is therefore detected from POSITION stability over a sliding window.
    """
    t0 = time.perf_counter()
    win = []                       # (t, raw) samples over the last `hold` seconds
    while time.perf_counter() - t0 < timeout:
        qq.read_outputs(); qq.write_voltage(0.0)
        now = time.perf_counter(); raw = f(qq.pendulumPosition)
        win.append((now, raw))
        win = [(tw, rw) for (tw, rw) in win if now - tw <= hold]
        if len(win) > 50 and (now - win[0][0]) >= hold:
            vals = np.array([rw for (_, rw) in win])
            if (vals.max() - vals.min()) < pos_tol:
                return float(np.median(vals)), True
        time.sleep(DT)
    return f(qq.pendulumPosition), False

q.write_led(LED_SETTLE)
REST_RAW,ok=settle_and_reference(q)
print(f"settle: rest_raw={REST_RAW:+.4f} rad settled={ok}")

rows=[]; phase="SWINGUP"; bal_since=None; center_since=None
pert_times=[]; pert_idx=0; t_pert_start=None; end_time=None
mode_prev=-1
t0=time.perf_counter(); t_prev=t0; next_t=t0+DT
try:
    while True:
        q.read_outputs()
        t=time.perf_counter(); dt_m=t-t_prev; t_prev=t; tt=t-t0
        if end_time is not None and tt>end_time: break
        if tt>120.0: print("TIMEOUT"); break

        theta=f(q.motorPosition)
        alpha=wrap(f(q.pendulumPosition)-REST_RAW-np.pi)
        theta_dot=f(q.motorSpeed); alpha_dot=f(q.pendulumSpeed)

        latched=(mode_prev==1)
        capture=(abs(alpha)<=CAPTURE_RAD and abs(alpha_dot)<=CAPTURE_RATE and abs(theta)<=CAPTURE_THETA)
        balancing = capture or (latched and abs(alpha)<=HOLD_RAD)

        v_pert=0.0
        if balancing:
            mode=1
            # extra arm-centring authority while CENTERing, so the arm leaves the
            # +-135 deg limit and gains symmetric room before perturbations start
            k_theta = K[0]*(K_TH_C if phase=="CENTER" else 1.0)
            v_lqr=float(np.clip(k_theta*theta+K[1]*alpha+K[2]*theta_dot+K[3]*alpha_dot,-V_BAL,V_BAL))
            gate_mean=signed=np.nan
            if use_res:
                a_n=float(np.clip(alpha/ALPHA_NORM,-1,1)); ad_n=float(np.clip(alpha_dot/RATE_NORM,-1,1))
                v_n=float(np.clip(v_lqr/V_BAL,-1,1))
                cur=np.array([CURRENT_BIAS+CURRENT_GAIN*max(a_n,0.),CURRENT_BIAS+CURRENT_GAIN*max(-a_n,0.),
                              CURRENT_BIAS+CURRENT_GAIN*max(ad_n,0.),CURRENT_BIAS+CURRENT_GAIN*max(-ad_n,0.),
                              CURRENT_BIAS+CURRENT_GAIN*max(v_n,0.),CURRENT_BIAS+CURRENT_GAIN*max(-v_n,0.)])
                res=neuron.step(cur,DT)
                act=np.clip(np.asarray(res.activity,dtype=float)*GATE_GAIN,0.,1.)
                signed=float(np.clip(W@act,-1.,1.)); gate_mean=float(act.mean())
                v_ctrl=float(np.clip((1-BLEND)*v_lqr+BLEND*(signed*V_BAL),-V_BAL,V_BAL))
                if learn:
                    tgt=float(np.clip(-K_ERR*a_n-K_RATE*ad_n,-1,1)); e=tgt-signed
                    if elig:
                        fr=np.clip(tt/60.,0,1); d=0.98-0.48*fr
                        e_trace=d*e_trace+(1-d)*act; au=e_trace
                    else: au=act
                    lrn=LR*(1-0.8*np.clip(tt/60.,0,1)) if anneal else LR
                    W=np.clip(W+lrn*e*au-LEAK*W,-W_CLIP,W_CLIP)
            else:
                v_ctrl=v_lqr

            # ---- phase machine ----
            if phase=="SWINGUP":
                phase="CENTER"; bal_since=tt
            if phase=="CENTER":
                if abs(np.degrees(theta))<=CENTER_DEG and (tt-bal_since)>=SETTLE_S:
                    phase="PERTURB"
                    pert_times=[tt+0.5+i*PERT_PERIOD for i in range(N_PERT)]
                    end_time=pert_times[-1]+POST_S
                    print(f"  centred at t={tt:.2f}s (theta={np.degrees(theta):+.1f} deg) -> perturbing")
                elif (tt-bal_since)>CENTER_TIMEOUT_S+SETTLE_S:
                    phase="PERTURB"
                    pert_times=[tt+0.5+i*PERT_PERIOD for i in range(N_PERT)]
                    end_time=pert_times[-1]+POST_S
                    print(f"  centring timeout at t={tt:.2f}s (theta={np.degrees(theta):+.1f} deg) -> perturbing")
            if phase=="PERTURB" and pert_idx<len(pert_times):
                if tt>=pert_times[pert_idx]:
                    if t_pert_start is None: t_pert_start=tt
                    if tt-t_pert_start<PERT_WIDTH:
                        v_pert=V_PERT*(1 if pert_idx%2==0 else -1)
                    else:
                        t_pert_start=None; pert_idx+=1
            led = led_gauge(alpha) if phase!="CENTER" else LED_CENTER
        else:
            mode=0
            E=0.5*Jp_cm*alpha_dot**2+mp*g*l*(1+np.cos(alpha))
            u=float(np.clip(MU*(E-Er)*np.sign(alpha_dot*np.cos(alpha))-KC_SW*theta,-a_max,a_max))
            v_ctrl=float(np.clip(ACC2V*u,-V_SW,V_SW)); led=LED_SWING
            gate_mean=signed=np.nan

        v=float(np.clip(v_ctrl+v_pert,-V_MAX,V_MAX))
        q.write_voltage(v)
        if mode!=mode_prev or mode==1: q.write_led(led); mode_prev=mode
        rows.append(dict(t=tt,dt=dt_m,phase=phase,mode=mode,voltage=v,v_ctrl=v_ctrl,v_pert=v_pert,
                         theta=theta,alpha=alpha,alpha_deg=np.degrees(alpha),theta_deg=np.degrees(theta),
                         theta_dot=theta_dot,alpha_dot=alpha_dot,gate_mean=gate_mean,signed=signed,
                         amp_fault=f(q.amplifierFault)))
        rem=next_t-time.perf_counter()
        if rem>0: time.sleep(rem)
        next_t+=DT
finally:
    q.write_voltage(0.0); q.write_led(LED_IDLE); q.terminate()
    print("shutdown: 0 V, LED RED, amplifier off, closed.")

A=lambda k: np.array([r[k] for r in rows],dtype=float)
T=A("t"); AL=np.abs(A("alpha_deg")); PH=[r["phase"] for r in rows]
pert_mask=np.array([p=="PERTURB" for p in PH])
survived = bool(A("mode")[pert_mask].mean()>0.99) if pert_mask.any() else False
events=[]
for i,tp in enumerate(pert_times):
    w=(T>=tp)&(T<tp+PERT_PERIOD)
    if not w.any(): continue
    seg_t=T[w]; seg_a=AL[w]
    peak=float(seg_a.max()); pk_i=int(np.argmax(seg_a))
    rec=seg_t[pk_i:][seg_a[pk_i:]<=RECOVER_DEG]
    events.append(dict(idx=i,t=float(tp),peak_deg=peak,
                       recovery_s=(float(rec[0]-seg_t[pk_i]) if len(rec) else None)))
pk=[e["peak_deg"] for e in events]
rc=[e["recovery_s"] for e in events if e["recovery_s"] is not None]
rms_pert=float(np.sqrt((AL[pert_mask]**2).mean())) if pert_mask.any() else float("nan")
summary=dict(method=METHOD,neuron=(NEURON if use_res else None),blend=BLEND,v_pert=V_PERT,
             n_pert=len(events),survived_all=survived,
             peak_mean_deg=float(np.mean(pk)) if pk else None,
             peak_max_deg=float(np.max(pk)) if pk else None,
             recovery_mean_s=float(np.mean(rc)) if rc else None,
             recovered_count=len(rc),alpha_rms_perturb_deg=rms_pert,
             realized_hz=float(1.0/np.diff(T).mean()),events=events,
             W_final=(W.tolist() if use_res else None),
             amp_faults=int(A("amp_fault").sum()))
print(f"\nperturbations {len(events)} | survived_all={survived}")
if not events:
    print("NO PERTURBATIONS APPLIED — the run never reached the PERTURB phase "
          "(swing-up or centring failed). Check KC_SW / settling.")
else:
    print(f"peak |alpha| mean {summary['peak_mean_deg']:.2f} deg  max {summary['peak_max_deg']:.2f} deg")
if rc:
    print(f"recovery mean {summary['recovery_mean_s']:.3f} s "
          f"({len(rc)}/{len(events)} recovered <{RECOVER_DEG} deg)")
elif events:
    print("recovery: none reached threshold")
print(f"alpha RMS during perturbed phase {rms_pert:.3f} deg | rate {summary['realized_hz']:.1f} Hz")

out=Path(__file__).resolve().parent.parent/"results"/"twin_perturb"; out.mkdir(parents=True,exist_ok=True)
stamp=time.strftime("%Y%m%d_%H%M%S"); tag=f"{METHOD}_{NEURON if use_res else 'none'}_V{V_PERT}_{stamp}"
with open(out/f"{tag}.csv","w",newline="") as fh:
    w=csv.DictWriter(fh,fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
(out/f"{tag}.json").write_text(json.dumps(summary,indent=2))
print(f"saved: {out/(tag+'.csv')}")
