# Standard-library, constant-memory comparison of PES and normalized PES.
# The two-state control removes CMG conductance but retains v/r and readout.
using Printf
using LinearAlgebra

const H = 0.0005
const TV = 0.05
const TR = 0.005
const A = 50.0
const IB = 0.75
const IG = 1.25
const AG = 1e5
const BASE_ETA = 8e-4
const DELTA = 0.05
const SCALES = (0.1, 1.0, 10.0)

mutable struct Unit
    v::Float64
    r::Float64
end
Unit() = Unit(0.,0.)
sig(x) = x >= 0 ? inv(1+exp(-x)) : exp(x)/(1+exp(x))

function advance!(u::Unit, current::Float64, kind::Symbol)
    gamma = kind == :full ? 2.0 : 0.0
    oldv = u.v
    target = sig(clamp(A*(u.v-1+gamma*u.r),-60.,60.))
    u.r = clamp(u.r + H/TR*(target-u.r),0.,1.)
    c = kind == :leaky ? 0.0 : (120+30*abs(current))*u.r^2
    rate = 1/TV+c
    steady = current/(TV*rate)
    u.v = steady+exp(-H*rate)*(u.v-steady)
    return clamp(AG*u.r,0.,1.), oldv<1 && u.v>=1, u.v>=1
end

signal(t,amp,phase) = amp*(0.8*sin(2pi*1.3*t+phase)+
                           0.2*sin(2pi*3.7*t-0.4*phase))

mutable struct Stats
    n::Int
    g11::Float64
    g12::Float64
    g22::Float64
    b1::Float64
    b2::Float64
    yy::Float64
    norm2::Float64
    sat1::Int
    sat2::Int
    events::Int
    occupancy::Int
end
Stats() = Stats(0,0.,0.,0.,0.,0.,0.,0.,0,0,0,0)
function record!(s::Stats,a1,a2,y,z1,z2,o1,o2)
    s.n+=1
    s.g11+=a1*a1; s.g12+=a1*a2; s.g22+=a2*a2
    s.b1+=a1*y; s.b2+=a2*y; s.yy+=y*y
    s.norm2+=a1*a1+a2*a2
    s.sat1+=a1>=1-1e-12; s.sat2+=a2>=1-1e-12
    s.events+=Int(z1)+Int(z2)
    s.occupancy+=Int(o1)+Int(o2)
end

function features!(units,kind,amp,k,phase)
    y=signal((k-1)*H,amp,phase)
    a1,z1,o1=advance!(units[1],IB+IG*max(y,0.),kind)
    a2,z2,o2=advance!(units[2],IB+IG*max(-y,0.),kind)
    return y,a1,a2,z1,z2,o1,o2
end

function gram_min(s::Stats)
    a,b,d=s.g11/s.n,s.g12/s.n,s.g22/s.n
    return max(0.,(a+d)/2-sqrt(((a-d)/2)^2+b*b))
end

function fitted_weights(s::Stats)
    g=[s.g11 s.g12;s.g12 s.g22]
    return pinv(g)*[s.b1,s.b2]
end

function optimal_rmse(s::Stats)
    w=fitted_weights(s)
    return sqrt(max(0.,(s.yy-2*dot(w,[s.b1,s.b2])+dot(w,[s.g11*w[1]+s.g12*w[2],s.g12*w[1]+s.g22*w[2]]))/s.n))
end

function run_case(kind,amp)
    # Unsupervised prepass only matches mean effective step across methods.
    units=(Unit(),Unit())
    pre=Stats()
    for k in 1:24000
        y,a1,a2,z1,z2,o1,o2=features!(units,kind,amp,k,0.)
        record!(pre,a1,a2,y,z1,z2,o1,o2)
    end
    mean_norm2=pre.norm2/pre.n
    # 1:3 ordinary PES, 4:6 normalized PES. Same initial weights and samples.
    w=zeros(2,6)
    late2=zeros(6)
    units=(Unit(),Unit())
    train=Stats()
    late=Stats()
    for k in 1:24000
        y,a1,a2,z1,z2,o1,o2=features!(units,kind,amp,k,0.)
        record!(train,a1,a2,y,z1,z2,o1,o2)
        if k>16000
            record!(late,a1,a2,y,z1,z2,o1,o2)
        end
        norm2=a1*a1+a2*a2
        for j in 1:6
            pred=clamp(w[1,j]*a1+w[2,j]*a2,-1.,1.)
            err=y-pred
            if k>16000
                late2[j]+=err*err
            end
            step=BASE_ETA*SCALES[mod1(j,3)]
            if j>3
                step*=(DELTA+mean_norm2)/(DELTA+norm2)
            end
            w[1,j]=clamp(w[1,j]+step*err*a1,-6.,6.)
            w[2,j]=clamp(w[2,j]+step*err*a2,-6.,6.)
        end
    end
    fitted=fitted_weights(train)
    test=Stats()
    loss2=zeros(6)
    fit2=0.
    for phase in (0.77,1.91)
        units=(Unit(),Unit())
        for k in 1:8000
            y,a1,a2,z1,z2,o1,o2=features!(units,kind,amp,k,phase)
            record!(test,a1,a2,y,z1,z2,o1,o2)
            fit2+=(y-fitted[1]*a1-fitted[2]*a2)^2
            for j in 1:6
                pred=clamp(w[1,j]*a1+w[2,j]*a2,-1.,1.)
                loss2[j]+=(y-pred)^2
            end
        end
    end
    for j in 1:6
        rule=j<=3 ? "PES" : "normalized_PES"
        @printf("%s,%.3f,%s,%.1f,%.7g,%.7g,%.7g,%.7g,%.7g,%.7g,%.7g,%.7g,%.5f,%.5f,%d,%d,%.5f,%.5f\n",
                String(kind),amp,rule,SCALES[mod1(j,3)],mean_norm2,
                gram_min(late),sqrt(late2[j]/8000),sqrt(loss2[j]/test.n),
                sqrt(fit2/test.n),optimal_rmse(test),sqrt(test.yy/test.n),
                sqrt(train.yy/train.n),test.sat1/test.n,test.sat2/test.n,
                test.events,test.occupancy,w[1,j],w[2,j])
    end
end

println("cell,amplitude,rule,rate_scale,train_mean_feature_norm2,late_gram_min,late_train_rmse,test_rmse,train_fit_test_rmse,test_optimal_linear_rmse,test_target_rms,train_target_rms,test_sat_plus,test_sat_minus,test_upcrossings,test_occupancies,w_plus,w_minus")
for kind in (:full,:reduced,:leaky), amp in (0.08,0.35)
    run_case(kind,amp)
end
