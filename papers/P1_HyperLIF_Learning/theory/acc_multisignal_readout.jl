# Causal two-cell ACC readout audit. External sinusoidal target; tiny arrays only.
# Compares cold-start and settled features, with train-only standardization.
using LinearAlgebra
using Printf
using Statistics
const DT=0.0005
const N=24000
const A=0.35
const COLS=Dict(
    :gate_raw=>[2,3], :gate_clipped=>[18,19],
    :membrane=>[4,5], :conductance_full=>[6,7],
    :conductance_gateonly=>[8,9], :reset_current=>[10,11],
    :gate_target=>[12,13], :gate_flux=>[14,15], :dvdt=>[16,17],
    :v_plus_gate=>[4,5,2,3],
    :v_plus_conductance=>[4,5,6,7],
    :gate_plus_conductance=>[2,3,6,7],
    :v_gate_conductance=>[4,5,2,3,6,7])
const ORDER=(:gate_raw,:gate_clipped,:membrane,:conductance_full,
             :conductance_gateonly,:reset_current,:gate_target,:gate_flux,
             :dvdt,:v_plus_gate,:v_plus_conductance,
             :gate_plus_conductance,:v_gate_conductance)
sig(x)=x>=0 ? inv(1+exp(-x)) : exp(x)/(1+exp(x))
signal(t,phase)=A*(0.8*sin(2pi*1.3*t+phase)+
                   0.2*sin(2pi*3.7*t-0.4*phase))
mutable struct Cell
    v::Float64
    r::Float64
end
Cell()=Cell(0.,0.)
function step!(z::Cell,current,gamma)
    oldv,oldr=z.v,z.r
    target=sig(clamp(50*(oldv-1+gamma*oldr),-60.,60.))
    z.r=oldr+.1*(target-oldr)
    cfull=(120+30*abs(current))*z.r^2
    cgate=120*z.r^2
    rate=20+cfull
    steady=20*current/rate
    z.v=steady+exp(-DT*rate)*(oldv-steady)
    return cfull,cgate,cfull*z.v,target,(z.r-oldr)/DT,(z.v-oldv)/DT,
           clamp(1e5*z.r,0.,1.),Int(oldv<1 && z.v>=1),Int(z.v>=1)
end
function simulate(gamma,phase;delay=0.)
    a,b=Cell(),Cell()
    data=Matrix{Float64}(undef,N,19)
    events=occupied=0
    for k in 1:N
        t=(k-1)*DT
        drive=signal(t,phase)
        y=t>=delay ? signal(t-delay,phase) : 0.
        i1=.75+1.25*max(drive,0.)
        i2=.75+1.25*max(-drive,0.)
        c1,cg1,s1,t1,f1,dv1,clip1,z1,o1=step!(a,i1,gamma)
        c2,cg2,s2,t2,f2,dv2,clip2,z2,o2=step!(b,i2,gamma)
        data[k,:]=[y,a.r,b.r,a.v,b.v,c1,c2,cg1,cg2,s1,s2,
                   t1,t2,f1,f2,dv1,dv2,clip1,clip2]
        events+=z1+z2;occupied+=o1+o2
    end
    return data,events,occupied
end
function fit_eval(train,tests,cols,window)
    inds=window==:cold ? (1:8000) : (16001:24000)
    y=train[inds,1]
    raw=train[inds,cols]
    means=vec(mean(raw,dims=1))
    stds=vec(std(raw,dims=1,corrected=false))
    active=findall(stds .>1e-12)
    mu=mean(y)
    if isempty(active)
        preds=[fill(mu,length(inds)) for _ in tests]
        return 0,0,0.,sqrt(mean(abs2,y.-mu)),
               [sqrt(mean(abs2,tests[j][inds,1].-preds[j])) for j in eachindex(tests)]
    end
    mu_x=means[active];sigma_x=stds[active]
    x=(raw[:,active].-mu_x')./sigma_x'
    decomp=svd(x;full=false)
    rank_eff=count(s->s>maximum(decomp.S)*1e-8,decomp.S)
    coeff=rank_eff==0 ? zeros(length(active)) :
       decomp.V[:,1:rank_eff]*((decomp.U[:,1:rank_eff]'*(y.-mu))./decomp.S[1:rank_eff])
    ratio=rank_eff==length(active) ? minimum(decomp.S)^2/maximum(decomp.S)^2 : 0.
    trainpred=mu.+x*coeff
    testerrs=Float64[]
    for data in tests
        xt=(data[inds,cols[active]].-mu_x')./sigma_x'
        push!(testerrs,sqrt(mean(abs2,data[inds,1].-(mu.+xt*coeff))))
    end
    return length(active),rank_eff,ratio,sqrt(mean(abs2,y.-trainpred)),testerrs
end
function main()
    println("gamma,window,readout,active_features,effective_rank,centered_gram_ratio,train_rmse,test_phase077_rmse,test_phase191_rmse,test_mean_rmse,total_test_upcrossings,total_test_occupancies")
    for gamma in (0.,.5,2.)
        train,_,_=simulate(gamma,0.)
        test1,z1,o1=simulate(gamma,.77)
        test2,z2,o2=simulate(gamma,1.91)
        for window in (:cold,:settled), readout in ORDER
            na,nr,ratio,tr,errs=fit_eval(train,(test1,test2),COLS[readout],window)
            @printf("%.3f,%s,%s,%d,%d,%.9g,%.9g,%.9g,%.9g,%.9g,%d,%d\n",
                    gamma,String(window),String(readout),na,nr,ratio,tr,
                    errs[1],errs[2],sqrt((errs[1]^2+errs[2]^2)/2),z1+z2,o1+o2)
        end
    end
end
if abspath(PROGRAM_FILE)==@__FILE__
    main()
end
