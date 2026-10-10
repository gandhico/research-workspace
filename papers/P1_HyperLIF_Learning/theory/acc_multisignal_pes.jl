# Frozen-transfer test for normalized online PES on multiple ACC readouts.
# Training-only feature standardization; validation and test phases are fresh.
include("acc_multisignal_readout.jl")
const ETAS=(1e-4,4e-4,1.6e-3,6.4e-3)
const TARGET_DELAY=isempty(ARGS) ? 0. : parse(Float64,ARGS[1])

function standardized(train,test1,test2,cols)
    raw=train[:,cols]
    mu=vec(mean(raw,dims=1))
    st=vec(std(raw,dims=1,corrected=false))
    active=findall(st .>1e-12)
    if isempty(active)
        return zeros(N,0),zeros(N,0),zeros(N,0)
    end
    m=mu[active];s=st[active]
    return (raw[:,active].-m')./s',
           (test1[:,cols[active]].-m')./s',
           (test2[:,cols[active]].-m')./s'
end
function rmse_windows(pred,y)
    return sqrt(mean(abs2,pred[1:8000].-y[1:8000])),
           sqrt(mean(abs2,pred[16001:24000].-y[16001:24000]))
end
function run_case(gamma,readout,train,val,test)
    x,xval,xtest=standardized(train,val,test,COLS[readout])
    p=size(x,2)
    weights=zeros(p+1,length(ETAS))
    late=zeros(length(ETAS))
    y=train[:,1]
    for k in 1:N
        norm2=1+sum(abs2,@view x[k,:])
        for j in eachindex(ETAS)
            pred=weights[1,j]
            for i in 1:p
                pred+=weights[i+1,j]*x[k,i]
            end
            e=y[k]-pred
            k>16000 && (late[j]+=e*e)
            rate=ETAS[j]/(1+norm2)
            weights[1,j]+=rate*e
            for i in 1:p
                weights[i+1,j]+=rate*e*x[k,i]
            end
        end
    end
    for j in eachindex(ETAS)
        valpred=weights[1,j].+xval*weights[2:end,j]
        testpred=weights[1,j].+xtest*weights[2:end,j]
        vc,vs=rmse_windows(valpred,val[:,1])
        tc,ts=rmse_windows(testpred,test[:,1])
        @printf("%.3f,%s,%.7g,%d,%.9g,%.9g,%.9g,%.9g,%.9g\n",
                gamma,String(readout),ETAS[j],p,sqrt(late[j]/8000),vc,vs,tc,ts)
    end
end
println("gamma,readout,eta,active_features,late_online_train_rmse,validation_cold_rmse,validation_settled_rmse,test_cold_rmse,test_settled_rmse")
for gamma in (0.,.5,2.)
    train,_,_=simulate(gamma,0.;delay=TARGET_DELAY)
    val,_,_=simulate(gamma,.77;delay=TARGET_DELAY)
    test,_,_=simulate(gamma,1.91;delay=TARGET_DELAY)
    for readout in ORDER
        run_case(gamma,readout,train,val,test)
    end
end
