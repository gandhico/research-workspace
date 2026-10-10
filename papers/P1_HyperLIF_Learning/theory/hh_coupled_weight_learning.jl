# Coupled canonical HH pair: one internal connection learned by exact
# forward sensitivity or a detached local eligibility approximation.
# Fixed-theta episodes, scalar-state streaming, standard-library Julia.
include("hh_forward_sensitivity.jl")

const CW_NS=2000              # one second, 0.5 ms observations
const CW_SUBSTEPS=20          # 0.025 ms HH RK4
const CW_THETA_STAR=0.7
const CW_KAPPA=0.5
const CW_GAINS=(0.25,0.5,1.0)
const CW_EPOCHS=18       # same number of updates as six 3-update curriculum stages

q(v)=sig((v+60)/10)
dq(v)=q(v)*(1-q(v))/10

# The sensitivity forcing here is dI/dtheta, held over the observation
# interval. The derivative of the frozen-current recurrence is applied at
# the start of each interval, giving the tangent of the discretized model.
function hh_input_tangent_rhs(z,current,dcurrent)
    v,m,h,n,sv,sm,sh,sn=z
    f=hh_rhs((v,m,h,n),current)
    rates,drates=rate_values_derivatives(v)
    am,bm,ah,bh,an,bn=rates
    dam,dbm,dah,dbh,dan,dbn=drates
    jvv=-(120m^3*h+36n^4+0.3)
    jvm=-360m^2*h*(v-50)
    jvh=-120m^3*(v-50)
    jvn=-144n^3*(v+77)
    ds_v=jvv*sv+jvm*sm+jvh*sh+jvn*sn+dcurrent
    ds_m=(dam*(1-m)-dbm*m)*sv-(am+bm)*sm
    ds_h=(dah*(1-h)-dbh*h)*sv-(ah+bh)*sh
    ds_n=(dan*(1-n)-dbn*n)*sv-(an+bn)*sn
    return (f...,ds_v,ds_m,ds_h,ds_n)
end
function hh_tangent_interval(s,e,current,dcurrent)
    z=(s...,e...)
    events=0
    for _ in 1:CW_SUBSTEPS
        oldv=z[1]
        z=rk4_step(z,current,dcurrent,OBS_DT*1000/CW_SUBSTEPS,
                   hh_input_tangent_rhs)
        events+=oldv<0 && z[1]>=0
    end
    return ntuple(i->z[i],4),ntuple(i->z[4+i],4),events
end
function hh_state_interval(s,current)
    events=0
    for _ in 1:CW_SUBSTEPS
        oldv=s[1]
        s=hh_step(s,current,OBS_DT*1000/CW_SUBSTEPS)
        events+=oldv<0 && s[1]>=0
    end
    return s,events
end
function base_current(model)
    model==:hh_quiet && return 0.0
    return 8.0
end
function initial(model)
    model==:hh_eq8 ? hh_equilibrium(8.0) : hh_init()
end
function branch_currents(model,u,v1,v2,theta)
    base=base_current(model)
    return base+8max(u,0)+theta*q(v2),
           base+8max(-u,0)+CW_KAPPA*q(v1)
end
function teacher_targets(model,phase;theta_star=CW_THETA_STAR)
    s1=initial(model); s2=initial(model)
    y=Vector{Float64}(undef,CW_NS)
    events=0; occupied=0
    for k in 1:CW_NS
        u=drive((k-1)*OBS_DT,phase)
        i1,i2=branch_currents(model,u,s1[1],s2[1],theta_star)
        s1,e1=hh_state_interval(s1,i1)
        s2,e2=hh_state_interval(s2,i2)
        events+=e1+e2
        occupied+=(s1[1]>=0)+(s2[1]>=0)
        y[k]=(s1[1]-s2[1])/20
    end
    return y,events,occupied
end
function rollout(model,phase,target,theta;method=:exact)
    s1=initial(model); s2=initial(model)
    e1=(0.0,0.0,0.0,0.0); e2=e1
    sum_e2=0.0; sum_grad=0.0; sum_j2=0.0
    events=0; occupied=0
    nsteps=length(target)
    for k in 1:nsteps
        u=drive((k-1)*OBS_DT,phase)
        i1,i2=branch_currents(model,u,s1[1],s2[1],theta)
        if method==:exact
            di1=q(s2[1])+theta*dq(s2[1])*e2[1]
            di2=CW_KAPPA*dq(s1[1])*e1[1]
        elseif method==:local
            di1=q(s2[1]); di2=0.0
        else
            error("unknown method")
        end
        s1,e1,cross1=hh_tangent_interval(s1,e1,i1,di1)
        s2,e2,cross2=hh_tangent_interval(s2,e2,i2,di2)
        events+=cross1+cross2
        occupied+=(s1[1]>=0)+(s2[1]>=0)
        pred=(s1[1]-s2[1])/20
        jac=(e1[1]-e2[1])/20
        err=pred-target[k]
        sum_e2+=err*err
        sum_grad+=err*jac
        sum_j2+=jac*jac
    end
    return sqrt(sum_e2/nsteps),sum_e2/(2nsteps),
           sum_grad/nsteps,sum_j2/nsteps,events,occupied
end

function fit(model,method,gain,train_target)
    theta=0.0
    for _ in 1:CW_EPOCHS
        _,_,grad,j2,_,_=rollout(model,0.0,train_target,theta;method=method)
        theta=clamp(theta-gain*grad/(j2+1e-6),-1.5,1.5)
    end
    return theta
end
function main_coupled()
    println("row,model,method,gain,theta,train_rmse,val_rmse,test_rmse,teacher_train_events,teacher_val_events,teacher_test_events,student_test_events,teacher_train_occupancy,teacher_val_occupancy,teacher_test_occupancy,student_test_occupancy,exact_gradient,local_gradient,finite_difference_gradient")
    for model in (:hh_quiet,:hh_tonic,:hh_eq8)
        tr,te,too=teacher_targets(model,0.0)
        val,ve,vo=teacher_targets(model,0.77)
        test,xe,xo=teacher_targets(model,1.91)
        _,loss,grad,_,_,_=rollout(model,0.0,tr,0.0)
        localgrad=rollout(model,0.0,tr,0.0;method=:local)[3]
        step=1e-4
        fd=(rollout(model,0.0,tr,step)[2]-rollout(model,0.0,tr,-step)[2])/(2step)
        rel=abs(grad-fd)/max(1e-10,abs(grad))
        rel<5e-3 || error("HH coupled exact gradient failed: model=$model relative=$rel")
        @printf("gradient,%s,exact_vs_local,NaN,0,%.9g,NaN,NaN,%d,%d,%d,NaN,%d,%d,%d,NaN,%.9g,%.9g,%.9g\n",
                String(model),sqrt(2loss),te,ve,xe,too,vo,xo,grad,localgrad,fd)
        for method in (:exact,:local)
            candidates=[]
            for gain in CW_GAINS
                theta=fit(model,method,gain,tr)
                trainrmse=rollout(model,0.0,tr,theta)[1]
                valrmse=rollout(model,0.77,val,theta)[1]
                push!(candidates,(gain,theta,trainrmse,valrmse))
                @printf("candidate,%s,%s,%.3f,%.9g,%.9g,%.9g,NaN,%d,%d,%d,NaN,%d,%d,%d,NaN,NaN,NaN,NaN\n",
                        String(model),String(method),gain,theta,trainrmse,valrmse,
                        te,ve,xe,too,vo,xo)
            end
            chosen=candidates[argmin([c[4] for c in candidates])]
            gain,theta,trainrmse,valrmse=chosen
            testrmse,_,_,_,student_events,student_occupied=
                rollout(model,1.91,test,theta)
            @printf("selected,%s,%s,%.3f,%.9g,%.9g,%.9g,%.9g,%d,%d,%d,%d,%d,%d,%d,%d,NaN,NaN,NaN\n",
                    String(model),String(method),gain,theta,trainrmse,
                    valrmse,testrmse,te,ve,xe,student_events,
                    too,vo,xo,student_occupied)
        end
    end
end
if abspath(PROGRAM_FILE)==@__FILE__
    main_coupled()
end
