# One internal connection in coupled ACC HyperLIF, gamma=0 versus gamma=2.
# Teacher-generated target; exact and detached local eligibility.
include("hh_hyperlif_tiny_pes.jl")

const HC_N=2000
const HC_THETA_STAR=0.7
const HC_KAPPA=0.9
const HC_GAINS=(0.25,0.5,1.0)
const HC_HORIZONS=(40,100,200,500,1000,2000)

function hc_cell(s::NTuple{2,Float64},e::NTuple{2,Float64},current,ecurrent,gamma)
    v,r=s; ev,er=e
    rawarg=50*(v-1+gamma*r)
    arg=clamp(rawarg,-60.0,60.0)
    target=sig(arg)
    dtarget=abs(rawarg)<60 ? 50target*(1-target)*(ev+gamma*er) : 0.0
    rp=r+0.1*(target-r)
    erp=er+0.1*(dtarget-er)
    cscale=120+30*abs(current)
    dcscale=30*sign(current)*ecurrent
    c=cscale*rp^2
    dc=dcscale*rp^2+2cscale*rp*erp
    rate=20+c
    steady=20current/rate
    esteady=20ecurrent/rate-20current*dc/rate^2
    decay=exp(-OBS_DT*rate)
    edecay=-OBS_DT*decay*dc
    vp=steady+decay*(v-steady)
    evp=esteady+edecay*(v-steady)+decay*(ev-esteady)
    return (vp,rp),(evp,erp)
end
function hc_signal(t,phase)
    return drive(t,phase)
end
function hc_step(s1,s2,e1,e2,theta,u,gamma,method)
    i1=.75+1.25*max(u,0.0)+theta*(s2[1]-.75)
    i2=.75+1.25*max(-u,0.0)+HC_KAPPA*(s1[1]-.75)
    di1=(s2[1]-.75)+(method==:exact ? theta*e2[1] : 0.0)
    di2=method==:exact ? HC_KAPPA*e1[1] : 0.0
    new1,de1=hc_cell(s1,e1,i1,di1,gamma)
    new2,de2=hc_cell(s2,e2,i2,di2,gamma)
    return new1,new2,de1,de2
end
function hc_output(s1,s2,e1,e2,readout)
    if readout==:voltage
        return 10*(s1[1]-s2[1]),10*(e1[1]-e2[1])
    elseif readout==:gate
        return s1[2]-s2[2],e1[2]-e2[2]
    else
        return 10*(s1[1]-s2[1])+(s1[2]-s2[2]),
               10*(e1[1]-e2[1])+(e1[2]-e2[2])
    end
end
function hc_teacher(gamma,phase,readout)
    s1=(0.0,0.0); s2=s1; e1=s1; e2=s1
    y=Vector{Float64}(undef,HC_N)
    events=0; occupancy=0
    for k in 1:HC_N
        old1=s1[1]; old2=s2[1]
        u=hc_signal((k-1)*OBS_DT,phase)
        s1,s2,e1,e2=hc_step(s1,s2,e1,e2,HC_THETA_STAR,u,gamma,:exact)
        y[k]=hc_output(s1,s2,e1,e2,readout)[1]
        events+=(old1<1 && s1[1]>=1)+(old2<1 && s2[1]>=1)
        occupancy+=(s1[1]>=1)+(s2[1]>=1)
    end
    return y,events,occupancy
end
function hc_rollout(gamma,phase,readout,target,theta;method=:exact)
    s1=(0.0,0.0); s2=s1; e1=s1; e2=s1
    n=length(target)
    err2=0.0; grad=0.0; jac2=0.0
    coldjac=0.0; latejac=0.0
    cold_err2=0.0; late_err2=0.0
    events=0; occupancy=0
    for k in 1:n
        old1=s1[1]; old2=s2[1]
        u=hc_signal((k-1)*OBS_DT,phase)
        s1,s2,e1,e2=hc_step(s1,s2,e1,e2,theta,u,gamma,method)
        pred,jac=hc_output(s1,s2,e1,e2,readout)
        err=pred-target[k]
        err2+=err^2; grad+=err*jac; jac2+=jac^2
        if k<=min(n,400)
            coldjac+=jac^2; cold_err2+=err^2
        end
        if k>max(0,n-400)
            latejac+=jac^2; late_err2+=err^2
        end
        events+=(old1<1 && s1[1]>=1)+(old2<1 && s2[1]>=1)
        occupancy+=(s1[1]>=1)+(s2[1]>=1)
    end
    return sqrt(err2/n),grad/n,jac2/n,coldjac/min(n,400),
           latejac/min(n,400),sqrt(cold_err2/min(n,400)),
           sqrt(late_err2/min(n,400)),events,occupancy
end
function hc_fit(gamma,readout,train,method,gain,schedule)
    theta=0.0
    for horizon in (schedule==:full ? (HC_N,) : HC_HORIZONS)
        episodes=schedule==:full ? 18 : 3
        y=@view train[1:horizon]
        for _ in 1:episodes
            _,grad,j2,_,_,_,_,_,_=
                hc_rollout(gamma,0.0,readout,y,theta;method=method)
            theta=clamp(theta-gain*grad/(j2+1e-6),-1.5,1.5)
        end
    end
    return theta
end
function main_hyper_coupled()
    println("row,gamma,readout,schedule,method,gain,theta,train_rmse,val_rmse,test_rmse,test_cold_rmse,test_late_rmse,teacher_test_rms,teacher_train_events,teacher_val_events,teacher_test_events,student_test_events,teacher_train_occupancy,teacher_val_occupancy,teacher_test_occupancy,student_test_occupancy,initial_exact_gradient,initial_local_gradient,initial_fd_gradient,initial_jac2_cold,initial_jac2_late")
    for gamma in (0.0,2.0), readout in (:voltage,:gate,:voltage_gate)
        train,te,too=hc_teacher(gamma,0.0,readout)
        val,ve,vo=hc_teacher(gamma,0.77,readout)
        test,xe,xo=hc_teacher(gamma,1.91,readout)
        z=hc_rollout(gamma,0.0,readout,train,0.0)
        loc=hc_rollout(gamma,0.0,readout,train,0.0;method=:local)
        step=1e-5
        lplus=hc_rollout(gamma,0.0,readout,train,step)[1]^2/2
        lminus=hc_rollout(gamma,0.0,readout,train,-step)[1]^2/2
        fd=(lplus-lminus)/(2step)
        abs(z[2]-fd)<1e-5*max(1e-6,abs(fd)) || error("gradient check failed")
        @printf("gradient,%.1f,%s,none,none,NaN,0,%.9g,NaN,NaN,NaN,NaN,%.9g,%d,%d,%d,NaN,%d,%d,%d,NaN,%.9g,%.9g,%.9g,%.9g,%.9g\n",
                gamma,String(readout),z[1],sqrt(mean(abs2,test)),
                te,ve,xe,too,vo,xo,z[2],loc[2],fd,z[4],z[5])
        for schedule in (:full,:curriculum), method in (:exact,:local)
            candidates=[]
            for gain in HC_GAINS
                theta=hc_fit(gamma,readout,train,method,gain,schedule)
                trainrmse=hc_rollout(gamma,0.0,readout,train,theta)[1]
                valrmse=hc_rollout(gamma,0.77,readout,val,theta)[1]
                push!(candidates,(gain,theta,trainrmse,valrmse))
                @printf("candidate,%.1f,%s,%s,%s,%.3f,%.9g,%.9g,%.9g,NaN,NaN,NaN,%.9g,%d,%d,%d,NaN,%d,%d,%d,NaN,NaN,NaN,NaN,NaN,NaN\n",
                        gamma,String(readout),String(schedule),String(method),
                        gain,theta,trainrmse,valrmse,sqrt(mean(abs2,test)),
                        te,ve,xe,too,vo,xo)
            end
            gain,theta,trainrmse,valrmse=candidates[argmin([c[4] for c in candidates])]
            out=hc_rollout(gamma,1.91,readout,test,theta)
            @printf("selected,%.1f,%s,%s,%s,%.3f,%.9g,%.9g,%.9g,%.9g,%.9g,%.9g,%.9g,%d,%d,%d,%d,%d,%d,%d,%d,NaN,NaN,NaN,NaN,NaN\n",
                    gamma,String(readout),String(schedule),String(method),
                    gain,theta,trainrmse,valrmse,out[1],out[6],out[7],
                    sqrt(mean(abs2,test)),te,ve,xe,out[8],too,vo,xo,out[9])
        end
    end
end
if abspath(PROGRAM_FILE)==@__FILE__
    main_hyper_coupled()
end
