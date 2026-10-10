# Gradient/eligibility check at several internal weights and horizons.
include("hh_coupled_weight_learning.jl")
println("model,horizon_ms,theta,exact_gradient,local_gradient,finite_difference_gradient,local_relative_difference,exact_fd_relative_difference")
for model in (:hh_quiet,:hh_tonic,:hh_eq8)
    target=teacher_targets(model,0.0)[1]
    for nsteps in (40,2000), theta in (0.0,0.35,0.65)
        y=@view target[1:nsteps]
        exact=rollout(model,0.0,y,theta)[3]
        approx=rollout(model,0.0,y,theta;method=:local)[3]
        step=1e-5
        fd=(rollout(model,0.0,y,theta+step)[2]-
            rollout(model,0.0,y,theta-step)[2])/(2step)
        localrel=abs(approx-exact)/max(1e-10,abs(exact))
        fdrel=abs(fd-exact)/max(1e-10,abs(exact))
        @printf("%s,%.1f,%.3f,%.9g,%.9g,%.9g,%.9g,%.9g\n",
                String(model),nsteps*OBS_DT*1000,theta,
                exact,approx,fd,localrel,fdrel)
    end
end
