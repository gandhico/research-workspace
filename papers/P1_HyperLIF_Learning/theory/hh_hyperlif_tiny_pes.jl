# Two independent driven cells per model; delayed-signal decoder learning.
# Standard-library Julia only. The applied current is NOT a decoder feature.
using LinearAlgebra, Statistics, Printf

const OBS_DT = 0.0005                 # seconds; 0.5 ms observation interval
const NS = 24000                     # 12 seconds, 3 phases
const PHASES = (0.0, 0.77, 1.91)    # train, validation, final test
const ETAS = (1e-4, 4e-4, 1.6e-3, 6.4e-3)
const READOUTS = (:voltage, :gate, :voltage_gate, :conductance,
                  :voltage_conductance, :full_conductance,
                  :voltage_lp20, :gate_lp20, :voltage_gate_lp20,
                  :voltage_lp50, :gate_lp50, :voltage_gate_lp50,
                  :m_gate, :h_gate, :n_gate,
                  :m_gate_lp20, :h_gate_lp20, :n_gate_lp20)
const NFEATURES = 14

drive(t, phase) = 0.35*(0.8*sin(2pi*1.3*t+phase) +
                        0.2*sin(2pi*3.7*t-0.4*phase))
sig(x) = x >= 0 ? inv(1+exp(-x)) : exp(x)/(1+exp(x))

# Stable HH alpha rates, ms^-1, voltage in mV. Classic 1952 parameterization.
vtrap(x, y) = abs(x/y) < 1e-6 ? y*(1+x/(2y)+x*x/(12y*y)) : x/(-expm1(-x/y))
function hh_rates(v)
    am = 0.1*vtrap(v+40, 10); bm = 4*exp(-(v+65)/18)
    ah = 0.07*exp(-(v+65)/20); bh = inv(1+exp(-(v+35)/10))
    an = 0.01*vtrap(v+55, 10); bn = 0.125*exp(-(v+65)/80)
    return am,bm,ah,bh,an,bn
end
function hh_rhs(s::NTuple{4,Float64}, current)
    v,m,h,n=s
    am,bm,ah,bh,an,bn=hh_rates(v)
    ina=120*m^3*h*(v-50)
    ik=36*n^4*(v+77)
    il=0.3*(v+54.387)
    return (current-ina-ik-il,
            am*(1-m)-bm*m, ah*(1-h)-bh*h, an*(1-n)-bn*n)
end
add4(a,b,c) = ntuple(i->a[i]+c*b[i],4)
function hh_step(s,current,dt_ms)
    k1=hh_rhs(s,current)
    k2=hh_rhs(add4(s,k1,dt_ms/2),current)
    k3=hh_rhs(add4(s,k2,dt_ms/2),current)
    k4=hh_rhs(add4(s,k3,dt_ms),current)
    return ntuple(i->s[i]+dt_ms*(k1[i]+2k2[i]+2k3[i]+k4[i])/6,4)
end
function hh_init()
    am,bm,ah,bh,an,bn=hh_rates(-65.0)
    return (-65.0,am/(am+bm),ah/(ah+bh),an/(an+bn))
end
function hh_stationary(v)
    am,bm,ah,bh,an,bn=hh_rates(v)
    return (v,am/(am+bm),ah/(ah+bh),an/(an+bn))
end
function hh_equilibrium(current)
    lo=-80.0; hi=-40.0
    flo=hh_rhs(hh_stationary(lo),current)[1]
    fhi=hh_rhs(hh_stationary(hi),current)[1]
    flo*fhi<0 || error("HH equilibrium not bracketed")
    for _ in 1:100
        mid=(lo+hi)/2
        fm=hh_rhs(hh_stationary(mid),current)[1]
        if fm*flo<=0
            hi=mid; fhi=fm
        else
            lo=mid; flo=fm
        end
    end
    return hh_stationary((lo+hi)/2)
end
ishh(model)=model in (:hh_rest,:hh_tonic,:hh_eq8)

# ACC two-state cell with current-dependent reset conductance. Same fixed
# update as acc_multisignal_readout.jl; gamma=0 is reduced feedback and
# gamma=2 is the studied high-readiness latch regime.
function hyper_step(s::NTuple{2,Float64},current,gamma)
    v,r=s
    target=sig(clamp(50*(v-1+gamma*r),-60.0,60.0))
    newr=r+0.1*(target-r)
    c=(120+30*abs(current))*newr^2
    rate=20+c
    steady=20*current/rate
    newv=steady+exp(-OBS_DT*rate)*(v-steady)
    return (newv,newr)
end

# Continuous adaptive leaky control: two states, no reset. This is a
# stateful linear control, not a spike-reset ALIF cell.
# tau_v=50 ms, tau_a=25 ms, E_L=-65 mV, R=2 mV/current,
# adaptation equilibrium a=0.25*(v-E_L).
function leaky_step(s::NTuple{2,Float64},current)
    v,a=s
    dv=(-65-v+2current-a)/0.05
    da=(0.25*(v+65)-a)/0.025
    # Heun is more than sufficient at 0.5 ms for this linear system.
    vp=v+OBS_DT*dv; ap=a+OBS_DT*da
    dvp=(-65-vp+2current-ap)/0.05
    dap=(0.25*(vp+65)-ap)/0.025
    return (v+OBS_DT*(dv+dvp)/2,a+OBS_DT*(da+dap)/2)
end

function currents(model,u)
    pos=max(u,0.0); neg=max(-u,0.0)
    if model==:hh_rest
        return (0.0+8pos,0.0+8neg)
    elseif model==:hh_tonic || model==:hh_eq8
        return (8.0+8pos,8.0+8neg)
    elseif model==:hyper_g0 || model==:hyper_g2
        return (0.75+1.25pos,0.75+1.25neg)
    else
        return (7.0+4pos,7.0+4neg)
    end
end

function simulate(model,phase; hh_substeps=20)
    x=zeros(NS,NFEATURES)
    vprev=zeros(2)
    events=0; occupancy=0
    first_event=NaN
    if ishh(model)
        init=model==:hh_eq8 ? hh_equilibrium(8.0) : hh_init()
        states=[init,init]
        threshold=0.0
    elseif model==:hyper_g0 || model==:hyper_g2
        states=[(0.0,0.0),(0.0,0.0)]
        threshold=1.0
    else
        states=[(-65.0,0.0),(-65.0,0.0)]
        threshold=-50.0
    end
    for k in 1:NS
        t=(k-1)*OBS_DT
        u=drive(t,phase)
        input=currents(model,u)
        for j in 1:2
            current=input[j]
            if ishh(model)
                s=states[j]
                for substep in 1:hh_substeps
                    oldv=s[1]
                    s=hh_step(s,current,OBS_DT*1000/hh_substeps)
                    cross=oldv<threshold && s[1]>=threshold
                    if cross && isnan(first_event)
                        first_event=t+substep*OBS_DT/hh_substeps
                    end
                    events+=cross
                end
                states[j]=s
                v,m,h,n=s
                x[k,j]=v; x[k,2+j]=m; x[k,4+j]=h; x[k,6+j]=n
                x[k,8+j]=120*m^3*h
                x[k,10+j]=36*n^4
                x[k,12+j]=120*m^3*h*(v-50)+36*n^4*(v+77)+0.3*(v+54.387)
            elseif model==:hyper_g0 || model==:hyper_g2
                oldv=states[j][1]
                gamma=model==:hyper_g0 ? 0.0 : 2.0
                s=hyper_step(states[j],current,gamma)
                states[j]=s
                v,r=s
                cross=oldv<threshold && v>=threshold
                if cross && isnan(first_event)
                    first_event=t+OBS_DT
                end
                events+=cross
                x[k,j]=v; x[k,2+j]=r
                x[k,8+j]=120*r^2              # state-only conductance
                x[k,10+j]=(120+30*abs(current))*r^2 # direct current factor
                x[k,12+j]=x[k,10+j]*v
            else
                oldv=states[j][1]
                s=leaky_step(states[j],current)
                states[j]=s
                cross=oldv<threshold && s[1]>=threshold
                if cross && isnan(first_event)
                    first_event=t+OBS_DT
                end
                events+=cross
                x[k,j]=s[1]; x[k,2+j]=s[2]
            end
            occupancy+=states[j][1]>=threshold
        end
    end
    return x,events,occupancy,first_event
end

function columns(model,readout)
    hh=ishh(model)
    gate=hh ? collect(3:8) : [3,4]
    if readout==:voltage
        return [1,2]
    elseif readout==:gate
        return gate
    elseif readout==:voltage_gate
        return vcat([1,2],gate)
    elseif readout==:conductance
        return hh ? [9,10,11,12] : [9,10]
    elseif readout==:voltage_conductance
        return hh ? [1,2,9,10,11,12] : [1,2,9,10]
    elseif readout==:full_conductance
        return hh ? [9,10,11,12] : [11,12]
    elseif readout==:m_gate
        return [3,4]
    elseif readout==:h_gate
        return [5,6]
    elseif readout==:n_gate
        return [7,8]
    end
end

function target(phase,delay)
    y=Vector{Float64}(undef,NS)
    for k in 1:NS
        t=(k-1)*OBS_DT
        y[k]=t>=delay ? drive(t-delay,phase) : 0.0
    end
    return y
end
function feature_map(data,cols,tau)
    raw=data[:,cols]
    tau==0.0 && return raw
    out=similar(raw)
    out[1,:]=raw[1,:]
    alpha=1-exp(-OBS_DT/tau)
    for k in 2:NS, j in 1:length(cols)
        out[k,j]=out[k-1,j]+alpha*(raw[k,j]-out[k-1,j])
    end
    return out
end
rmse(pred,y,inds)=sqrt(mean(abs2,@view(pred[inds]).-y[inds]))
const COLD=1:8000; const SETTLED=16001:24000
function fit_case(model,readout,delay,data,ys)
    name=String(readout)
    parts=split(name,"_lp")
    base=Symbol(parts[1])
    tau=length(parts)==1 ? 0.0 : parse(Float64,parts[2])/1000
    cols=columns(model,base)
    raw=feature_map(data[1],cols,tau)
    mu=vec(mean(raw,dims=1)); sd=vec(std(raw,dims=1,corrected=false))
    active=findall(sd .> 1e-12)
    xx=[isempty(active) ? zeros(NS,0) :
        (feature_map(d,cols[active],tau).-mu[active]')./sd[active]' for d in data]
    p=length(active)
    y=ys[1]
    # Least squares is a diagnostic representation limit, not online PES.
    trainmean=mean(y)
    if p==0
        lsval=sqrt(mean(abs2,ys[2].-trainmean))
        lstest=sqrt(mean(abs2,ys[3].-trainmean))
        rank=0
    else
        f=svd(xx[1];full=false)
        rank=count(s->s>maximum(f.S)*1e-8,f.S)
        b=rank==0 ? zeros(p) :
            f.V[:,1:rank]*((f.U[:,1:rank]'*(y.-trainmean))./f.S[1:rank])
        lsval=sqrt(mean(abs2,ys[2].-(trainmean.+xx[2]*b)))
        lstest=sqrt(mean(abs2,ys[3].-(trainmean.+xx[3]*b)))
    end
    besteta=0.0; bestval=Inf; besttest=NaN
    bestcold=NaN; bestsettled=NaN
    for eta in ETAS
        w=zeros(p+1)
        for k in 1:NS
            norm2=1.0
            pred=w[1]
            for j in 1:p
                f=xx[1][k,j]
                norm2+=f*f; pred+=w[j+1]*f
            end
            e=y[k]-pred
            rate=eta/norm2
            w[1]+=rate*e
            for j in 1:p
                w[j+1]+=rate*e*xx[1][k,j]
            end
        end
        vp=w[1].+xx[2]*w[2:end]
        vc=rmse(vp,ys[2],COLD); vs=rmse(vp,ys[2],SETTLED)
        score=sqrt((vc^2+vs^2)/2)
        if score<bestval
            tp=w[1].+xx[3]*w[2:end]
            besteta=eta; bestval=score
            besttest=sqrt((rmse(tp,ys[3],COLD)^2+
                           rmse(tp,ys[3],SETTLED)^2)/2)
            bestcold=rmse(tp,ys[3],COLD)
            bestsettled=rmse(tp,ys[3],SETTLED)
        end
    end
    return p,rank,lsval,lstest,besteta,bestval,besttest,bestcold,bestsettled
end

function main()
    println("model,delay_s,readout,active_features,rank,ls_val_rmse,ls_test_rmse,pes_eta,pes_val_rmse,pes_test_rmse,pes_test_cold_rmse,pes_test_settled_rmse,train_events,val_events,test_events,train_occupancy,val_occupancy,test_occupancy,train_first_event_s,val_first_event_s,test_first_event_s")
    for model in (:hh_rest,:hh_tonic,:hh_eq8,:hyper_g0,:hyper_g2,:leaky_adaptive)
        sims=[simulate(model,p) for p in PHASES]
        data=[s[1] for s in sims]
        for delay in (0.0,0.02)
            ys=[target(p,delay) for p in PHASES]
            for readout in READOUTS
                if model==:leaky_adaptive &&
                   readout in (:conductance,:voltage_conductance,:full_conductance)
                    continue
                end
                if !ishh(model) &&
                   readout in (:m_gate,:h_gate,:n_gate,
                               :m_gate_lp20,:h_gate_lp20,:n_gate_lp20)
                    continue
                end
                vals=fit_case(model,readout,delay,data,ys)
                @printf("%s,%.3f,%s,%d,%d,%.9g,%.9g,%.7g,%.9g,%.9g,%.9g,%.9g,%d,%d,%d,%d,%d,%d,%.9g,%.9g,%.9g\n",
                        String(model),delay,String(readout),vals...,
                        sims[1][2],sims[2][2],sims[3][2],
                        sims[1][3],sims[2][3],sims[3][3],
                        sims[1][4],sims[2][4],sims[3][4])
            end
        end
    end
end
if abspath(PROGRAM_FILE)==@__FILE__
    main()
end
