include("hh_hyperlif_tiny_pes.jl")
println("model,phase,events_dt025ms,events_dt0125ms,occupancy_dt025ms,occupancy_dt0125ms,rms_voltage_difference_mV")
for model in (:hh_rest,:hh_tonic,:hh_eq8), phase in PHASES
    a,e,o,_=simulate(model,phase;hh_substeps=20)
    b,e2,o2,_=simulate(model,phase;hh_substeps=40)
    d=sqrt(mean(abs2,a[:,1:2].-b[:,1:2]))
    @printf("%s,%.3f,%d,%d,%d,%d,%.9g\n",String(model),phase,e,e2,o,o2,d)
end
