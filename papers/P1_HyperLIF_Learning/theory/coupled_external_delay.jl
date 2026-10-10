# External 20 ms delay target with jointly refitted linear readout and
# one recurrent connection. HyperLIF and two-state adaptive leaky control.
include("hyper_coupled_regime_learning.jl")
const EX_N=8000               # four seconds, 0.5 ms observation step
const EX_DELAY=0.02
const EX_RIDGE=1e-6
const EX_GAINS=(0.25,0.5,1.0)
const EX_EPOCHS=8

function ex_leaky_cell(s,e,current,ecurrent)
    v,a=s; ev,ea=e
    dv=(-65-v+2current-a)/0.05
    da=(0.25*(v+65)-a)/0.025
    dev=(-ev+2ecurrent-ea)/0.05
    dea=(0.25ev-ea)/0.025
    vp=v+OBS_DT*dv; ap=a+OBS_DT*da
    evp=ev+OBS_DT*dev; eap=ea+OBS_DT*dea
    dvp=(-65-vp+2current-ap)/0.05
    dap=(0.25*(vp+65)-ap)/0.025
    devp=(-evp+2ecurrent-eap)/0.05
    deap=(0.25evp-eap)/0.025
    return (v+OBS_DT*(dv+dvp)/2,a+OBS_DT*(da+dap)/2),
           (ev+OBS_DT*(dev+devp)/2,ea+OBS_DT*(dea+deap)/2)
end
function ex_step(model,s1,s2,e1,e2,theta,u,method)
    if model==:leaky
        q2=(s2[1]+65)/20; q1=(s1[1]+65)/20
        i1=7+4max(u,0.0)+theta*q2
        i2=7+4max(-u,0.0)+0.5q1
        di1=q2+(method==:exact ? theta*e2[1]/20 : 0.0)
        di2=method==:exact ? 0.5*e1[1]/20 : 0.0
        new1,de1=ex_leaky_cell(s1,e1,i1,di1)
        new2,de2=ex_leaky_cell(s2,e2,i2,di2)
        return new1,new2,de1,de2
    else
        gamma=model==:hyper_g0 ? 0.0 : 2.0
        return hc_step(s1,s2,e1,e2,theta,u,gamma,method)
    end
end
function ex_features(model,theta,phase;method=:exact)
    if model==:leaky
        s1=(-65.0,0.0); s2=s1
    else
        s1=(0.0,0.0); s2=s1
    end
    e1=(0.0,0.0); e2=e1
    x=Matrix{Float64}(undef,EX_N,4)
    dx=Matrix{Float64}(undef,EX_N,4)
    events=0; occupancy=0
    threshold=model==:leaky ? -50.0 : 1.0
    for k in 1:EX_N
        old1=s1[1]; old2=s2[1]
        u=drive((k-1)*OBS_DT,phase)
        s1,s2,e1,e2=ex_step(model,s1,s2,e1,e2,theta,u,method)
        x[k,1]=s1[1]; x[k,2]=s2[1]
        x[k,3]=s1[2]; x[k,4]=s2[2]
        dx[k,1]=e1[1]; dx[k,2]=e2[1]
        dx[k,3]=e1[2]; dx[k,4]=e2[2]
        events+=(old1<threshold && s1[1]>=threshold)+
                (old2<threshold && s2[1]>=threshold)
        occupancy+=(s1[1]>=threshold)+(s2[1]>=threshold)
    end
    return x,dx,events,occupancy
end
function ex_target(phase)
    y=Vector{Float64}(undef,EX_N)
    for k in 1:EX_N
        t=(k-1)*OBS_DT
        y[k]=t<EX_DELAY ? 0.0 : drive(t-EX_DELAY,phase)
    end
    return y
end
function ex_fit(x,dx,y,cols)
    xx=x[:,cols]; dd=dx[:,cols]
    mx=vec(mean(xx,dims=1)); my=mean(y)
    xc=xx.-mx'; yc=y.-my
    p=length(cols)
    gram=xc'xc/EX_N+EX_RIDGE*Matrix{Float64}(I,p,p)
    cross=xc'yc/EX_N
    w=gram\cross
    bias=my-dot(mx,w)
    pred=bias.+xx*w
    err=pred.-y
    jac=dd*w
    mse=mean(abs2,err)
    objective=mse/2+EX_RIDGE*sum(abs2,w)/2
    grad=mean(err.*jac)
    jac2=mean(abs2,jac)
    return w,bias,sqrt(mse),objective,grad,jac2
end
function ex_eval(model,theta,phase,w,bias,cols)
    x,_,events,occupancy=ex_features(model,theta,phase)
    y=ex_target(phase)
    pred=bias.+x[:,cols]*w
    return sqrt(mean(abs2,pred.-y)),events,occupancy
end
function ex_train(model,readout,method,gain)
    cols=readout==:voltage ? [1,2] : [1,2,3,4]
    y=ex_target(0.0)
    theta=0.0
    for _ in 1:EX_EPOCHS
        x,dx,_,_=ex_features(model,theta,0.0;method=method)
        _,_,_,_,grad,j2=ex_fit(x,dx,y,cols)
        theta=clamp(theta-gain*grad/(j2+1e-4),-1.0,1.5)
    end
    x,dx,_,_=ex_features(model,theta,0.0)
    w,bias,trainrmse,objective,_,_=ex_fit(x,dx,y,cols)
    valrmse,_,_=ex_eval(model,theta,0.77,w,bias,cols)
    return theta,w,bias,trainrmse,valrmse
end
function main_external()
    println("row,model,readout,method,gain,theta,train_rmse,val_rmse,test_rmse,initial_exact_gradient,initial_local_gradient,initial_fd_gradient,baseline_val_rmse,baseline_test_rmse,test_events,test_occupancy")
    for model in (:hyper_g0,:hyper_g2,:leaky), readout in (:voltage,:voltage_gate)
        cols=readout==:voltage ? [1,2] : [1,2,3,4]
        y=ex_target(0.0)
        x,dx,_,_=ex_features(model,0.0,0.0)
        w,bias,trainrmse,obj,grad,j2=ex_fit(x,dx,y,cols)
        _,dd,_,_=ex_features(model,0.0,0.0;method=:local)
        localgrad=ex_fit(x,dd,y,cols)[5]
        step=1e-6
        xp,dp,_,_=ex_features(model,step,0.0)
        xm,dm,_,_=ex_features(model,-step,0.0)
        fd=(ex_fit(xp,dp,y,cols)[4]-ex_fit(xm,dm,y,cols)[4])/(2step)
        abs(grad-fd)<2e-3*max(1e-6,abs(fd)) || error("external gradient check failed $model $readout $grad $fd")
        baseval,_,_=ex_eval(model,0.0,0.77,w,bias,cols)
        basetest,_,_=ex_eval(model,0.0,1.91,w,bias,cols)
        @printf("baseline,%s,%s,none,NaN,0,%.9g,%.9g,%.9g,%.9g,%.9g,%.9g,%.9g,%.9g,NaN,NaN\n",
                String(model),String(readout),trainrmse,baseval,basetest,
                grad,localgrad,fd,baseval,basetest)
        for method in (:exact,:local)
            candidates=[]
            for gain in EX_GAINS
                theta,wt,b,trainr,valr=ex_train(model,readout,method,gain)
                push!(candidates,(gain,theta,wt,b,trainr,valr))
                @printf("candidate,%s,%s,%s,%.3f,%.9g,%.9g,%.9g,NaN,NaN,NaN,NaN,%.9g,%.9g,NaN,NaN\n",
                        String(model),String(readout),String(method),gain,theta,
                        trainr,valr,baseval,basetest)
            end
            gain,theta,wt,b,trainr,valr=candidates[argmin([c[6] for c in candidates])]
            testr,events,occupancy=ex_eval(model,theta,1.91,wt,b,cols)
            @printf("selected,%s,%s,%s,%.3f,%.9g,%.9g,%.9g,%.9g,NaN,NaN,NaN,%.9g,%.9g,%d,%d\n",
                    String(model),String(readout),String(method),gain,theta,
                    trainr,valr,testr,baseval,basetest,events,occupancy)
        end
    end
end
if abspath(PROGRAM_FILE)==@__FILE__
    main_external()
end
