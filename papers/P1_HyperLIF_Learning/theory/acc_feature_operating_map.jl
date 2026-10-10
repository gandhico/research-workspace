# Tiny independent-target feature audit: two ACC cells, no trained hidden state.
# Quantifies where a fixed linear decoder could represent the input waveform.
using Printf
using LinearAlgebra
const DT=.0005
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
function dataset(gamma,amp,phase)
    a,b=Cell(),Cell()
    data=Matrix{Float64}(undef,8000,5) # target,r1,r2,v1,v2
    events=0;occupied=0
    for k in 1:8000
        y=signal((k-1)*DT,amp,phase)
        z1,o1=step!(a,.75+1.25*max(y,0.),gamma)
        z2,o2=step!(b,.75+1.25*max(-y,0.),gamma)
        data[k,1]=y;data[k,2]=a.r;data[k,3]=b.r
        data[k,4]=a.v;data[k,5]=b.v
        events+=z1+z2;occupied+=o1+o2
    end
    return data,events,occupied
end
function features(data,readout,gain)
    if readout==:readiness
        return clamp.(gain.*data[:,2:3],0.,1.)
    end
    return data[:,4:5]
end
function audit(train,test,readout,gain)
    x=features(train,readout,gain); xt=features(test,readout,gain)
    y=train[:,1]; yt=test[:,1]
    g=x'*x/size(x,1)
    eig=eigvals(Symmetric(g))
    ratio=max(0.,eig[1])/max(eps(),eig[2])
    w=pinv(g)*(x'*y/size(x,1))
    trainrmse=norm(x*w-y)/sqrt(length(y))
    testrmse=norm(xt*w-yt)/sqrt(length(yt))
    sat=sum(xt.>=1-1e-12)/(2*size(xt,1))
    return ratio,max(0.,eig[2]),trainrmse,testrmse,sat,w
end
println("gamma,amplitude,readout,gain,train_gram_ratio,train_gram_max,train_fit_rmse,test_rmse,test_saturation_fraction,test_upcrossings,test_occupancies,w1,w2")
for gamma in (0.,.25,.5,1.,2.), amp in (.08,.35)
    train,_,_=dataset(gamma,amp,0.)
    test,events,occupied=dataset(gamma,amp,.77)
    for readout in (:readiness,:voltage)
        gains=readout==:readiness ? (1.,100.,1e5) : (1.,)
        for gain in gains
            ratio,lmax,tr,te,sat,w=audit(train,test,readout,gain)
            @printf("%.3f,%.3f,%s,%.0f,%.9g,%.9g,%.9g,%.9g,%.6f,%d,%d,%.9g,%.9g\n",
                    gamma,amp,String(readout),gain,ratio,lmax,tr,te,sat,events,occupied,w[1],w[2])
        end
    end
end
