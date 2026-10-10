# Exploratory constant-I=8 HH basin probe. A finite trajectory is not a
# proof of a periodic attractor or a complete basin boundary.
include("hh_hyperlif_tiny_pes.jl")

function run_const(s0; current=8.0, seconds=4.0, dt_ms=0.025)
    s=s0; events=0; late=0; last_spike=NaN; sum_isi=0.0; n_isi=0
    nsteps=Int(round(seconds*1000/dt_ms))
    for k in 1:nsteps
        oldv=s[1]
        s=hh_step(s,current,dt_ms)
        if oldv<0 && s[1]>=0
            t=k*dt_ms/1000
            events+=1
            if t>seconds/2
                late+=1
                if !isnan(last_spike)
                    sum_isi+=t-last_spike; n_isi+=1
                end
                last_spike=t
            end
        end
    end
    return events,late,n_isi==0 ? NaN : sum_isi/n_isi,s[1]
end

equil=hh_equilibrium(8.0)
println("initialization,delta_v_mV,total_crossings,late_crossings,late_mean_isi_s,end_voltage_mV")
for (label,s) in (("rest_state",hh_init()),
                  ("exact_equilibrium",equil))
    e,l,isi,v=run_const(s)
    @printf("%s,%.3f,%d,%d,%.9g,%.9g\n",label,s[1]-equil[1],e,l,isi,v)
end
for delta in (-10.0,-5.0,-2.0,-1.0,-0.5,0.5,1.0,2.0,5.0,10.0)
    s=(equil[1]+delta,equil[2],equil[3],equil[4])
    e,l,isi,v=run_const(s)
    @printf("voltage_only,%.3f,%d,%d,%.9g,%.9g\n",delta,e,l,isi,v)
end
