# Constant-memory ACC single-neuron basin and slow-sweep audit.
# Equilibrium roots are bracketed numerically; trajectory classes are empirical.
using Printf

const TV=0.05
const TR=0.005
const ALPHA=50.0
const GAMMA=2.0
const G0=120.0
const G1=30.0
const DT=0.0001

sig(x)=x>=0 ? inv(1+exp(-x)) : exp(x)/(1+exp(x))
function equilibrium(current,r)
    c=G0+G1*current
    v=current/(1+TV*c*r*r)
    s=sig(ALPHA*(v-1+GAMMA*r))
    return v,s-r
end
function roots(current;nscan=20000)
    found=Float64[]
    left=0.0; fleft=equilibrium(current,left)[2]
    for j in 1:nscan
        right=j/nscan; fright=equilibrium(current,right)[2]
        if fleft*fright<0
            lo,hi=left,right
            for _ in 1:65
                mid=(lo+hi)/2
                if equilibrium(current,mid)[2]*equilibrium(current,lo)[2]<=0
                    hi=mid
                else
                    lo=mid
                end
            end
            push!(found,(lo+hi)/2)
        end
        left,fleft=right,fright
    end
    return found
end
function eq_stats(current,r)
    v,_=equilibrium(current,r)
    c=G0+G1*current
    lambda=1/TV+c*r*r
    fvr=-2*c*r*v
    frv=ALPHA*r*(1-r)/TR
    frr=(ALPHA*GAMMA*r*(1-r)-1)/TR
    trace=-lambda+frr
    determinant=-lambda*frr-fvr*frv
    return v,trace,determinant
end
function step(v,r,current)
    target=sig(clamp(ALPHA*(v-1+GAMMA*r),-80.,80.))
    rp=target+(r-target)*exp(-DT/TR)
    rate=1/TV+(G0+G1*current)*rp*rp
    steady=(current/TV)/rate
    vp=steady+exp(-DT*rate)*(v-steady)
    return vp,rp
end
function run(current,v0,r0;duration=4.0,window=1.0)
    v,r=v0,r0
    n=round(Int,duration/DT); beginwin=n-round(Int,window/DT)
    sv=0.;sv2=0.;sr=0.;sr2=0.;minv=Inf;maxv=-Inf
    crosses=0;occupied=0
    for k in 1:n
        prev=v
        v,r=step(v,r,current)
        if k>beginwin
            sv+=v;sv2+=v*v;sr+=r;sr2+=r*r
            minv=min(minv,v);maxv=max(maxv,v)
            crosses+=Int(prev<1 && v>=1)
            occupied+=Int(v>=1)
        end
    end
    m=n-beginwin
    return (v=v,r=r,meanv=sv/m,sdv=sqrt(max(0.,sv2/m-(sv/m)^2)),
            meanr=sr/m,sdr=sqrt(max(0.,sr2/m-(sr/m)^2)),
            minv=minv,maxv=maxv,crosses=crosses,occupied=occupied)
end
function logit_roots(current)
    ib=parse(BigFloat,string(current))
    f(q)=begin
        r=sig(q)
        v=ib/(1+BigFloat("0.05")*(120+30*ib)*r*r)
        q-50*(v-1+2*r)
    end
    found=BigFloat[]
    left=BigFloat(-40); fleft=f(left)
    for j in 1:240
        right=BigFloat(-40)+BigFloat(j)/2; fright=f(right)
        if fleft*fright<0
            lo,hi=left,right
            for _ in 1:220
                mid=(lo+hi)/2
                if f(lo)*f(mid)<=0
                    hi=mid
                else
                    lo=mid
                end
            end
            push!(found,(lo+hi)/2)
        end
        left,fleft=right,fright
    end
    return found
end
setprecision(BigFloat,256)
println("equilibrium,current,root_index,q,r,v,one_minus_r,dr_dI,dv_dI,trace,determinant,linear_class")
for current in (0.84,0.87,0.88,0.888,0.889,0.90,0.94,1.00)
    for (j,q) in enumerate(logit_roots(current))
        rb=sig(q)
        ib=parse(BigFloat,string(current))
        den=1+BigFloat("0.05")*(120+30*ib)*rb*rb
        vi=(1+BigFloat("0.05")*120*rb*rb)/den^2
        vr=-2*BigFloat("0.05")*(120+30*ib)*ib*rb/den^2
        hr=50*rb*(1-rb)*(vr+2)-1
        ri=-50*rb*(1-rb)*vi/hr
        vtotal=vi+vr*ri
        v,tr,det=eq_stats(current,Float64(rb))
        cls=det<0 ? "saddle" : tr<0 ? "stable" : "unstable"
        @printf("equilibrium,%.6f,%d,%.12g,%s,%.9g,%s,%s,%s,%.9g,%.9g,%s\n",
                current,j,Float64(q),string(rb),v,string(1-rb),string(ri),string(vtotal),tr,det,cls)
    end
end
println("trajectory,current,v0,r0,mean_v,sd_v,mean_r,sd_r,min_v,max_v,upcrossings,occupancies,final_v,final_r")
for current in (0.87,0.888,0.889,0.90,0.94,1.00)
    for (v0,r0) in ((0.,0.),(.8,0.),(.8,.05),(.8,.5),(.8,1.),(1.2,0.),(1.2,.5),(1.2,1.))
        z=run(current,v0,r0)
        @printf("trajectory,%.6f,%.3f,%.3f,%.9g,%.9g,%.9g,%.9g,%.9g,%.9g,%d,%d,%.9g,%.9g\n",
                current,v0,r0,z.meanv,z.sdv,z.meanr,z.sdr,z.minv,z.maxv,z.crosses,z.occupied,z.v,z.r)
    end
end
println("sweep,direction,current,mean_v,sd_v,upcrossings,occupancies,final_v,final_r")
for (direction,currents) in (("up",collect(.82:.01:1.02)),("down",collect(1.02:-.01:.82)))
    v,r=0.,0.
    for current in currents
        z=run(current,v,r;duration=1.0,window=.5)
        v,r=z.v,z.r
        @printf("sweep,%s,%.6f,%.9g,%.9g,%d,%d,%.9g,%.9g\n",
                direction,current,z.meanv,z.sdv,z.crosses,z.occupied,v,r)
    end
end
println("basin,current,v0,r0,final_v,final_r,class")
for v0 in 0.:.12:1.2, r0 in 0.:.1:1.
    z=run(.87,v0,r0;duration=2.0,window=.5)
    cls=z.r<.1 ? "low" : z.r>.9 ? "high" : "unsettled"
    @printf("basin,0.870000,%.6f,%.6f,%.9g,%.9g,%s\n",v0,r0,z.v,z.r,cls)
end
