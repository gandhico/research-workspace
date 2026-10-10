# Standard-library trajectory audit around canonical linear stability changes.
# Uses the frozen-target exact gate and frozen-conductance exact voltage steps.
using Printf
const H=1e-4
const TV=0.02
const TR=0.002
sig(x)=x>=0 ? inv(1+exp(-x)) : exp(x)/(1+exp(x))

function run(family,current,h=H)
    v=0.;r=0.;lastv=0.
    count=0;occupied=0;sumv=0.;sumv2=0.;sumr=0.;sumr2=0.
    nsteps=round(Int,3/h)
    transient=round(Int,2/h)
    for k in 1:nsteps
        lastv=v
        target=sig(clamp(100*(v-1+0.2*r),-80.,80.))
        r=target+(r-target)*exp(-h/TR)
        cscale=family==:fixed ? 100.0 : 20.0+80.0*abs(current)
        rate=1/TV+cscale*r^2
        steady=(current/TV)/rate
        v=steady+exp(-rate*h)*(v-steady)
        if k>transient
            count+=Int(lastv<1 && v>=1)
            occupied+=Int(v>=1)
            sumv+=v;sumv2+=v*v;sumr+=r;sumr2+=r*r
        end
    end
    sampled=nsteps-transient
    meanv=sumv/sampled;meanr=sumr/sampled
    sdv=sqrt(max(0.,sumv2/sampled-meanv^2))
    sdr=sqrt(max(0.,sumr2/sampled-meanr^2))
    @printf("%s,%.2f,%.7g,%d,%d,%.9g,%.9g,%.9g,%.9g\n",
            String(family),current,h,count,occupied,meanv,sdv,meanr,sdr)
end

println("family,current,dt,last_second_upcrossings,last_second_occupancies,mean_v,sd_v,mean_r,sd_r")
for family in (:fixed,:adaptive), current in (0.9,1.0,2.2,2.4,6.0,10.0,15.0,16.0,20.0,30.0)
    run(family,current)
end
run(:fixed,2.4,5e-5)
run(:adaptive,6.0,5e-5)
run(:adaptive,16.0,5e-5)
