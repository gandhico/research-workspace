# Two recurrent CMG cells; one internal weight learned from forward sensitivity.
# Standard-library-only, constant-memory experiment with a realizable teacher.
using Printf
using LinearAlgebra

const H=0.0005
const TV=0.05
const TR=0.005
const ALPHA=50.0
const KAPPA=0.9           # fixed reciprocal connection, cell 1 -> cell 2
const TEACHER_THETA=0.7   # learned connection, cell 2 -> cell 1
const NTRAIN=4000
const NTEST=8000

sig(x)=x>=0 ? inv(1+exp(-x)) : exp(x)/(1+exp(x))
signal(t,phase)=0.08*(0.8*sin(2pi*1.3*t+phase)+
                       0.2*sin(2pi*3.7*t-0.4*phase))

mutable struct Pair
    v1::Float64; r1::Float64; v2::Float64; r2::Float64
    ev1::Float64; er1::Float64; ev2::Float64; er2::Float64
end
Pair()=Pair(0.,0.,0.,0.,0.,0.,0.,0.)

function cell_step(v,r,ev,er,current,ecurrent)
    arg=clamp(ALPHA*(v-1),-60.,60.)
    target=sig(arg)
    dtarget=abs(ALPHA*(v-1))<60 ? target*(1-target)*ALPHA*ev : 0.
    rp=clamp(r+H/TR*(target-r),0.,1.)
    erp=(1-H/TR)*er+H/TR*dtarget
    cscale=120+30*abs(current)
    dcscale=30*sign(current)*ecurrent
    c=cscale*rp^2
    dc=dcscale*rp^2+2*cscale*rp*erp
    rate=1/TV+c
    drate=dc
    steady=current/(TV*rate)
    esteady=ecurrent/(TV*rate)-current*drate/(TV*rate^2)
    decay=exp(-H*rate)
    edecay=-H*decay*drate
    vp=steady+decay*(v-steady)
    evp=esteady+edecay*(v-steady)+decay*(ev-esteady)
    return vp,rp,evp,erp
end

function advance!(s::Pair, drive, theta; sensitivity=:exact)
    # Both currents use the previous states: simultaneous recurrent update.
    i1=0.75+1.25*drive+theta*(s.v2-0.75)
    i2=0.75-1.25*drive+KAPPA*(s.v1-0.75)
    ei1=(s.v2-0.75)+(sensitivity==:exact ? theta*s.ev2 : 0.)
    ei2=sensitivity==:exact ? KAPPA*s.ev1 : 0.
    v1,r1,ev1,er1=cell_step(s.v1,s.r1,s.ev1,s.er1,i1,ei1)
    v2,r2,ev2,er2=cell_step(s.v2,s.r2,s.ev2,s.er2,i2,ei2)
    s.v1,s.r1,s.v2,s.r2=v1,r1,v2,r2
    s.ev1,s.er1,s.ev2,s.er2=ev1,er1,ev2,er2
    return 10*(v1-v2),10*(ev1-ev2)
end

function rollout(theta,phase,nsteps;sensitivity=:exact)
    teacher=Pair(); student=Pair()
    sum_e2=0.; sum_grad=0.; sum_j2=0.
    for k in 1:nsteps
        drive=signal((k-1)*H,phase)
        target,_=advance!(teacher,drive,TEACHER_THETA)
        pred,jac=advance!(student,drive,theta;sensitivity=sensitivity)
        err=pred-target
        sum_e2+=err*err
        sum_grad+=err*jac
        sum_j2+=jac*jac
    end
    return sqrt(sum_e2/nsteps),sum_e2/(2*nsteps),sum_grad/nsteps,sum_j2/nsteps
end

function fit_internal(sensitivity)
    theta=0.
    first_grad=NaN
    for epoch in 1:12
        rmse,loss,grad,j2=rollout(theta,0.,NTRAIN;sensitivity=sensitivity)
        epoch==1 && (first_grad=grad)
        # One-parameter damped Gauss-Newton step using a streaming Jacobian.
        theta=clamp(theta-0.5*grad/(j2+1e-6),-1.5,1.5)
        if epoch in (1,2,4,8,12)
            @printf("internal_epoch,%s,%d,%.9g,%.9g,%.9g,%.9g\n",
                    String(sensitivity),epoch,theta,rmse,grad,j2)
        end
    end
    test_rmse=rollout(theta,0.77,NTEST)[1]
    @printf("internal_summary,%s,%.9g,%.9g,%.9g\n",
            String(sensitivity),theta,test_rmse,first_grad)
    return theta
end

function fit_decoder_pes()
    w1,w2=1.,-1.   # output is 10*(v1-v2) initially
    for epoch in 1:40
        teacher=Pair(); student=Pair(); err2=0.
        for k in 1:NTRAIN
            drive=signal((k-1)*H,0.)
            target,_=advance!(teacher,drive,TEACHER_THETA)
            advance!(student,drive,0.)
            a1,a2=10*student.v1,10*student.v2
            error=target-(w1*a1+w2*a2)
            err2+=error^2
            w1=clamp(w1+8e-4*error*a1,-6.,6.)
            w2=clamp(w2+8e-4*error*a2,-6.,6.)
        end
        if epoch in (1,2,4,8,12,20,40)
            @printf("decoder_epoch,PES,%d,%.9g,%.9g,%.9g\n",epoch,w1,w2,sqrt(err2/NTRAIN))
        end
    end
    teacher=Pair(); student=Pair(); err2=0.
    for k in 1:NTEST
        drive=signal((k-1)*H,0.77)
        target,_=advance!(teacher,drive,TEACHER_THETA)
        advance!(student,drive,0.)
        err2+=(target-10*(w1*student.v1+w2*student.v2))^2
    end
    @printf("decoder_summary,PES,%.9g,%.9g,%.9g\n",w1,w2,sqrt(err2/NTEST))
end

function fit_decoder_least_squares()
    teacher=Pair(); student=Pair()
    gram=zeros(2,2); cross=zeros(2)
    for k in 1:NTRAIN
        drive=signal((k-1)*H,0.)
        target,_=advance!(teacher,drive,TEACHER_THETA)
        advance!(student,drive,0.)
        a1,a2=10*student.v1,10*student.v2
        gram[1,1]+=a1*a1; gram[1,2]+=a1*a2
        gram[2,1]+=a2*a1; gram[2,2]+=a2*a2
        cross[1]+=a1*target; cross[2]+=a2*target
    end
    weights=pinv(gram)*cross
    teacher=Pair(); student=Pair(); err2=0.
    for k in 1:NTEST
        drive=signal((k-1)*H,0.77)
        target,_=advance!(teacher,drive,TEACHER_THETA)
        advance!(student,drive,0.)
        err2+=(target-10*(weights[1]*student.v1+weights[2]*student.v2))^2
    end
    @printf("decoder_summary,least_squares_diagnostic,%.9g,%.9g,%.9g\n",
            weights[1],weights[2],sqrt(err2/NTEST))
end

function event_audit(theta,phase,nsteps)
    state=Pair(); events=0; occupancy=0
    for k in 1:nsteps
        old1,old2=state.v1,state.v2
        advance!(state,signal((k-1)*H,phase),theta)
        events+=Int(old1<1 && state.v1>=1)+Int(old2<1 && state.v2>=1)
        occupancy+=Int(state.v1>=1)+Int(state.v2>=1)
    end
    @printf("event_audit,theta=%.6f,%d,%d,%d\n",theta,nsteps,events,occupancy)
end

println("row_type,method,epoch_or_theta,parameter_or_rmse,gradient_or_weight,jacobian_norm_or_rmse")
for theta in (0.,0.35)
    _,loss,grad,_=rollout(theta,0.,NTRAIN)
    _,_,local_grad,_=rollout(theta,0.,NTRAIN;sensitivity=:local)
    dh=1e-5
    fd=(rollout(theta+dh,0.,NTRAIN)[2]-rollout(theta-dh,0.,NTRAIN)[2])/(2dh)
    @printf("gradient_audit,theta=%.2f,%.9g,%.9g,%.9g,%.9g\n",
            theta,loss,grad,local_grad,fd)
    abs(grad-fd)<=1e-5*max(1e-3,abs(fd)) || error("exact eligibility gradient failed finite difference")
end
theta_exact=fit_internal(:exact)
theta_local=fit_internal(:local)
fit_decoder_pes()
fit_decoder_least_squares()
event_audit(0.,0.77,NTEST)
event_audit(theta_exact,0.77,NTEST)
event_audit(theta_local,0.77,NTEST)
event_audit(TEACHER_THETA,0.77,NTEST)
