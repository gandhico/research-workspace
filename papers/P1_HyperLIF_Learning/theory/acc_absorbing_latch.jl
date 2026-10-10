# Small numerical stress check of the analytic ACC high-gate invariant region.
using Printf
const DT=1e-4
const R0=0.999
const B=1/(0.05*30*R0^2)
sig(x)=x>=0 ? inv(1+exp(-x)) : exp(x)/(1+exp(x))
@assert B<1
@assert sig(50*(-B-1+2R0))>R0
@assert 0.05*(2+4/(3R0^3))<1
function main()
v,r=0.104756171,1.0
println("segment,current,min_v,min_r,last_v,last_r,threshold_upcrossings")
for (j,current) in enumerate((-1.,-10.,-1000.,0.,1000.,-1000.,0.))
    minv=Inf;minr=Inf;events=0
    for _ in 1:2000
        oldv=v
        target=sig(50*(v-1+2*r))
        r=target+(r-target)*exp(-DT/0.005)
        rate=1/0.05+(120+30*abs(current))*r^2
        steady=(current/0.05)/rate
        v=steady+exp(-rate*DT)*(v-steady)
        minv=min(minv,v);minr=min(minr,r)
        events+=Int(oldv<1 && v>=1)
        r>=R0 && v>=-B-1e-12 || error("escaped invariant rectangle")
    end
    @printf("%d,%.1f,%.9g,%.9g,%.9g,%.9g,%d\n",j,current,minv,minr,v,r,events)
end
@printf("invariant_check,r0=%.6f,B=%.9g,sigmoid_at_gate_corner=%.12g\n",
        R0,B,sig(50*(-B-1+2R0)))
end
main()
