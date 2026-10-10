# Gamma=2 coupled ACC HyperLIF: finite-time gate basins over connection
# weight and input phase. Stream one row per run; no task labels used.
include("coupled_external_delay.jl")
println("theta,phase,late_r1_mean,late_r2_mean,late_v1_mean,late_v2_mean,basin,events,occupancy")
for theta in 0.0:0.05:0.8, phase in 0.0:(2pi/32):2pi
    x,_,events,occupancy=ex_features(:hyper_g2,theta,phase)
    late=vec(mean(x[6001:end,:],dims=1))
    high1=late[3]>0.99; high2=late[4]>0.99
    low1=late[3]<0.01; low2=late[4]<0.01
    basin=high1 && low2 ? "high_low" :
          high1 && high2 ? "high_high" :
          low1 && high2 ? "low_high" :
          low1 && low2 ? "low_low" : "intermediate"
    @printf("%.3f,%.9g,%.9g,%.9g,%.9g,%.9g,%s,%d,%d\n",
            theta,phase,late[3],late[4],late[1],late[2],basin,
            events,occupancy)
end
