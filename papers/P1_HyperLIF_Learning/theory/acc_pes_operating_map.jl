# Online PES on a waveform target specified independently of any teacher cell.
# Three fixed small readout regimes; standard-library, constant-state training.
using Printf
const DT=.0005
const ETAS=(2e-4,8e-4,3.2e-3,1.28e-2,5.12e-2)
sig(x)=x>=0 ? inv(1+exp(-x)) : exp(x)/(1+exp(x))
signal(t,amp,phase)=amp*(.8*sin(2pi*1.3*t+phase)+.2*sin(2pi*3.7*t-.4*phase))
mutable struct Cell
    v::Float64
    r::Float64
end
Cell()=Cell(0.,0.)
function step!(c,current,gamma)
    old=c.v
    target=sig(clamp(50*(c.v-1+gamma*c.r),-60.,60.))
    c.r+=.1*(target-c.r)
    rate=20+(120+30*abs(current))*c.r^2
    steady=20*current/rate
    c.v=steady+exp(-DT*rate)*(c.v-steady)
    return Int(old<1 && c.v>=1),Int(c.v>=1)
end
function sample!(a,b,gamma,gain,readout,k,phase)
    y=signal((k-1)*DT,.35,phase)
    z1,o1=step!(a,.75+1.25*max(y,0.),gamma)
    z2,o2=step!(b,.75+1.25*max(-y,0.),gamma)
    x1=readout==:voltage ? a.v : clamp(gain*a.r,0.,1.)
    x2=readout==:voltage ? b.v : clamp(gain*b.r,0.,1.)
    return y,x1,x2,z1+z2,o1+o2
end
function run(label,gamma,gain,readout)
    weights=zeros(2,length(ETAS))
    late=zeros(length(ETAS))
    g11=g12=g22=0.
    a,b=Cell(),Cell()
    for k in 1:24000
        y,x1,x2,_,_=sample!(a,b,gamma,gain,readout,k,0.)
        if k>16000
            g11+=x1*x1;g12+=x1*x2;g22+=x2*x2
        end
        for j in eachindex(ETAS)
            err=y-(weights[1,j]*x1+weights[2,j]*x2)
            if k>16000
                late[j]+=err*err
            end
            weights[1,j]=clamp(weights[1,j]+ETAS[j]*err*x1,-6.,6.)
            weights[2,j]=clamp(weights[2,j]+ETAS[j]*err*x2,-6.,6.)
        end
    end
    gm=(g11+g22)/16000-sqrt(((g11-g22)/16000)^2+(g12/8000)^2)
    test=zeros(length(ETAS));events=0;occupied=0;sat=0
    a,b=Cell(),Cell()
    for k in 1:8000
        y,x1,x2,z,o=sample!(a,b,gamma,gain,readout,k,.77)
        events+=z;occupied+=o
        sat+=Int(x1>=1-1e-12)+Int(x2>=1-1e-12)
        for j in eachindex(ETAS)
            test[j]+=(y-(weights[1,j]*x1+weights[2,j]*x2))^2
        end
    end
    for j in eachindex(ETAS)
        @printf("%s,%.6g,%.9g,%.9g,%.9g,%.6f,%d,%d,%.9g,%.9g\n",
                label,ETAS[j],sqrt(late[j]/8000),sqrt(test[j]/8000),
                max(0.,gm),sat/16000,events,occupied,weights[1,j],weights[2,j])
    end
end
println("regime,eta,late_train_rmse,test_rmse,late_gram_min,test_sat_fraction,test_upcrossings,test_occupancies,w1,w2")
run("reduced_readiness_gain100",0.,100.,:readiness)
run("full_ACC_readiness_gain100000",2.,1e5,:readiness)
run("reduced_voltage",0.,1.,:voltage)
