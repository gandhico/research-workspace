# Follow-up on validation-selected gamma=2 local external-task weights.
include("coupled_external_delay.jl")
println("theta,phase,late_v1_mean,late_v2_mean,late_r1_mean,late_r2_mean,final_r1,final_r2,events,occupancy")
for theta in (0.0,0.30715511,0.565657444), phase in (0.0,0.77,1.91)
    x,_,events,occupancy=ex_features(:hyper_g2,theta,phase)
    late=vec(mean(x[6001:end,:],dims=1))
    @printf("%.9g,%.3f,%.9g,%.9g,%.9g,%.9g,%.9g,%.9g,%d,%d\n",
            theta,phase,late[1],late[2],late[3],late[4],
            x[end,3],x[end,4],events,occupancy)
end
