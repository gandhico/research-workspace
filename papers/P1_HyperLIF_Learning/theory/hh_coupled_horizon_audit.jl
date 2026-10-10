# How training horizon changes local gradient and one-weight learning.
include("hh_coupled_weight_learning.jl")

function horizon_audit()
    println("row,model,method,gain,horizon_ms,theta,train_window_rmse,train_full_rmse,val_full_rmse,test_full_rmse,exact_gradient_at_zero,local_gradient_at_zero")
    for model in (:hh_quiet,:hh_tonic,:hh_eq8)
        train=teacher_targets(model,0.0)[1]
        val=teacher_targets(model,0.77)[1]
        test=teacher_targets(model,1.91)[1]
        for nsteps in (40,100,200,500,1000,2000)
            y=@view train[1:nsteps]
            exact=rollout(model,0.0,y,0.0)[3]
            localgrad=rollout(model,0.0,y,0.0;method=:local)[3]
            @printf("gradient,%s,none,NaN,%.1f,0,NaN,NaN,NaN,NaN,%.9g,%.9g\n",
                    String(model),nsteps*OBS_DT*1000,exact,localgrad)
        end
        for method in (:exact,:local)
            candidates=[]
            for gain in (0.25,0.5,1.0)
                theta=0.0
                lastval=Inf
                for nsteps in (40,100,200,500,1000,2000)
                    y=@view train[1:nsteps]
                    for _ in 1:3
                        _,_,grad,j2,_,_=rollout(model,0.0,y,theta;method=method)
                        theta=clamp(theta-gain*grad/(j2+1e-6),-1.5,1.5)
                    end
                    wr=rollout(model,0.0,y,theta)[1]
                    fr=rollout(model,0.0,train,theta)[1]
                    lastval=rollout(model,0.77,val,theta)[1]
                    @printf("curriculum,%s,%s,%.3f,%.1f,%.9g,%.9g,%.9g,%.9g,NaN,NaN,NaN\n",
                            String(model),String(method),gain,nsteps*OBS_DT*1000,
                            theta,wr,fr,lastval)
                end
                push!(candidates,(gain,theta,lastval))
            end
            gain,theta,valrmse=candidates[argmin([c[3] for c in candidates])]
            tr=rollout(model,1.91,test,theta)[1]
            @printf("selected_test,%s,%s,%.3f,1000.0,%.9g,NaN,NaN,%.9g,%.9g,NaN,NaN\n",
                    String(model),String(method),gain,theta,valrmse,tr)
        end
    end
end
if abspath(PROGRAM_FILE)==@__FILE__
    horizon_audit()
end
