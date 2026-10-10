# Fixed-gain curriculum sensitivity to the teacher's connection strength.
# Gain=1 came from the main theta*=0.7 validation run; this sweep is
# exploratory and does not reselect that gain using test data.
include("hh_coupled_weight_learning.jl")
println("model,teacher_theta,method,learned_theta,train_rmse,val_rmse,test_rmse,teacher_train_events,teacher_val_events,teacher_test_events")
for model in (:hh_quiet,:hh_tonic,:hh_eq8), teacher_theta in (0.3,0.5,0.7,0.9)
    train,te,_=teacher_targets(model,0.0;theta_star=teacher_theta)
    val,ve,_=teacher_targets(model,0.77;theta_star=teacher_theta)
    test,xe,_=teacher_targets(model,1.91;theta_star=teacher_theta)
    for method in (:exact,:local)
        theta=0.0
        for nsteps in (40,100,200,500,1000,2000)
            y=@view train[1:nsteps]
            for _ in 1:3
                _,_,grad,j2,_,_=rollout(model,0.0,y,theta;method=method)
                theta=clamp(theta-grad/(j2+1e-6),-1.5,1.5)
            end
        end
        tr=rollout(model,0.0,train,theta)[1]
        vr=rollout(model,0.77,val,theta)[1]
        xr=rollout(model,1.91,test,theta)[1]
        @printf("%s,%.3f,%s,%.9g,%.9g,%.9g,%.9g,%d,%d,%d\n",
                String(model),teacher_theta,String(method),theta,tr,vr,xr,te,ve,xe)
    end
end
