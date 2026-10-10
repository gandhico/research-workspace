# Repeated normalized PES passes on the settled full-ACC fixture.
# Isolates learnability after the high gate has latched from cold-start shift.
include("acc_multisignal_readout.jl")
const RATES=(1e-4,4e-4,1.6e-3)
train,_,_=simulate(2.,0.)
val,_,_=simulate(2.,.77)
test,_,_=simulate(2.,1.91)
inds=16001:24000
println("readout,eta,epoch,active_features,online_train_rmse,frozen_train_rmse,validation_settled_rmse,test_settled_rmse,LS_settled_test_mean_rmse")
for readout in (:gate_raw,:conductance_gateonly,:conductance_full,:membrane,:v_plus_conductance)
    cols=COLS[readout]
    raw=train[inds,cols]
    mu=vec(mean(raw,dims=1));sd=vec(std(raw,dims=1,corrected=false))
    active=findall(sd .>1e-12)
    p=length(active)
    x=p==0 ? zeros(length(inds),0) : (raw[:,active].-mu[active]')./sd[active]'
    xv=p==0 ? zeros(length(inds),0) : (val[inds,cols[active]].-mu[active]')./sd[active]'
    xt=p==0 ? zeros(length(inds),0) : (test[inds,cols[active]].-mu[active]')./sd[active]'
    y=train[inds,1];yv=val[inds,1];yt=test[inds,1]
    _,_,_,_,floors=fit_eval(train,(val,test),cols,:settled)
    floor_mean=sqrt((floors[1]^2+floors[2]^2)/2)
    for eta in RATES
        w=zeros(p+1)
        for epoch in 1:10
            online2=0.
            for k in eachindex(y)
                pred=w[1]
                for i in 1:p
                    pred+=w[i+1]*x[k,i]
                end
                err=y[k]-pred
                online2+=err^2
                norm2=1.
                for i in 1:p
                    norm2+=x[k,i]^2
                end
                rate=eta/(1+norm2)
                w[1]+=rate*err
                for i in 1:p
                    w[i+1]+=rate*err*x[k,i]
                end
            end
            if epoch in (1,10)
                frozen=sqrt(mean(abs2,(w[1].+x*w[2:end]).-y))
                vr=sqrt(mean(abs2,(w[1].+xv*w[2:end]).-yv))
                tr=sqrt(mean(abs2,(w[1].+xt*w[2:end]).-yt))
                @printf("%s,%.7g,%d,%d,%.9g,%.9g,%.9g,%.9g,%.9g\n",
                        String(readout),eta,epoch,p,sqrt(online2/length(y)),frozen,vr,tr,floor_mean)
            end
        end
    end
end
