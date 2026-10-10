# ACC single-cell local saddle-node certificate with 256-bit directed intervals.
# Standard libraries only. Certificates establish local folds in stated boxes;
# they do not enumerate all equilibria or certify a global bifurcation diagram.
using Printf
setprecision(BigFloat, 256)

const TV = big"0.05"
const TR = big"0.005"
const A = big"50"
const GAMMA = big"2"
const G0 = big"120"
const G1 = big"30"

sig(x) = inv(1 + exp(-x))
function branch(q)
    r = sig(q)
    req = 1 - GAMMA*r + q/A
    c0 = 1 + TV*G0*r^2
    den = 1 - TV*G1*r^2*req
    current = req*c0/den
    rp = -GAMMA + inv(A*r*(1-r))
    c0p = 2*TV*G0*r
    denp = -TV*G1*(2*r*req + r^2*rp)
    didr = ((rp*c0 + req*c0p)*den - req*c0*denp)/den^2
    return current, r, req, den, didr*r*(1-r)
end

# Canonical fixed/adaptive families: enclose local linear-stability changes
# along their exact constant-positive-current equilibrium parameterizations.
struct Family
    name::String
    tv::BigFloat
    tr::BigFloat
    alpha::BigFloat
    gamma::BigFloat
    g0::BigFloat
    g1::BigFloat
end

function generic_branch(q, p::Family)
    r=sig(q)
    req=1-p.gamma*r+q/p.alpha
    c0=1+p.tv*p.g0*r^2
    den=1-p.tv*p.g1*r^2*req
    current=req*c0/den
    rp=-p.gamma+inv(p.alpha*r*(1-r))
    c0p=2*p.tv*p.g0*r
    denp=-p.tv*p.g1*(2*r*req+r^2*rp)
    didr=((rp*c0+req*c0p)*den-req*c0*denp)/den^2
    didq=didr*r*(1-r)
    c=p.g0+p.g1*current
    lambda=inv(p.tv)+c*r^2
    vp=-2*p.tv*c*r*current/(1+p.tv*c*r^2)^2
    hr=p.alpha*r*(1-r)*(vp+p.gamma)-1
    determinant=-lambda*hr/p.tr
    trace=-lambda+(p.alpha*p.gamma*r*(1-r)-1)/p.tr
    traceprime=-(p.g1*didq*r^2+2*c*r^2*(1-r))+
        p.alpha*p.gamma/p.tr*(1-2*r)*r*(1-r)
    return current,r,den,trace,determinant,didq,traceprime
end

function generic_interval(q,p::Family)
    one=Iv(1)
    # Use enclosing decimal inputs, not stringified point BigFloats, so the
    # certificate covers the paper's stated decimal parameters exactly.
    tv=Iv("0.02"); tr=Iv("0.002"); al=Iv(100); gamma=Iv("0.2")
    g0=p.name=="canonical_fixed" ? Iv(100) : Iv(20)
    g1=p.name=="canonical_fixed" ? Iv(0) : Iv(80)
    r=inv(one+exp(-q))
    req=one-gamma*r+q/al
    c0=one+tv*g0*sq(r)
    den=one-tv*g1*sq(r)*req
    current=req*c0/den
    rp=-gamma+inv(al*r*(one-r))
    c0p=Iv(2)*tv*g0*r
    denp=-(tv*g1*(Iv(2)*r*req+sq(r)*rp))
    didr=((rp*c0+req*c0p)*den-req*c0*denp)/sq(den)
    didq=didr*r*(one-r)
    c=g0+g1*current
    lambda=inv(tv)+c*sq(r)
    vp=-(Iv(2)*tv*c*r*current)/sq(one+tv*c*sq(r))
    hr=al*r*(one-r)*(vp+gamma)-one
    determinant=-(lambda*hr)/tr
    trace=-lambda+(al*gamma*r*(one-r)-one)/tr
    traceprime=-(g1*didq*sq(r)+Iv(2)*c*sq(r)*(one-r))+
        al*gamma/tr*(one-Iv(2)*r)*r*(one-r)
    return current,r,den,trace,determinant,didq,traceprime
end

function audit_canonical()
families=(Family("canonical_fixed",big"0.02",big"0.002",big"100",big"0.2",big"100",big"0"),
          Family("canonical_adaptive",big"0.02",big"0.002",big"100",big"0.2",big"20",big"80"))
println("stability_kind,family,q_lower,q_upper,I_interval,r_interval,trace_left,trace_right,det_interval,dI_dq_interval,dtrace_dq_interval")
for p in families
    qprev=big"-30"
    prev=generic_branch(qprev,p)
    for k in 1:1400
        q=big"-30"+BigFloat(k)/20
        curr=generic_branch(q,p)
        if prev[1]>0 && curr[1]>0 && prev[3]>0 && curr[3]>0 &&
           prev[5]>0 && curr[5]>0 && prev[4]*curr[4]<0
            lo,hi=qprev,q
            flo=prev[4]
            for _ in 1:250
                mid=(lo+hi)/2
                fm=generic_branch(mid,p)[4]
                if flo*fm<=0
                    hi=mid
                else
                    lo,flo=mid,fm
                end
            end
            center=(lo+hi)/2
            lower_text=string(round(center-big"1e-16",RoundDown;digits=16,base=10))
            upper_text=string(round(center+big"1e-16",RoundUp;digits=16,base=10))
            qbox=Iv(Iv(lower_text).l,Iv(upper_text).u)
            left=generic_interval(Iv(lower_text),p)[4]
            right=generic_interval(Iv(upper_text),p)[4]
            i,r,den,trace,det,di,dt=generic_interval(qbox,p)
            (left.u<0 && right.l>0 || left.l>0 && right.u<0) || error("trace root not bracketed")
            den.l>0 && i.l>0 && det.l>0 || error("invalid positive-current stable-eigen pair")
            (di.l>0 || di.u<0) && (dt.l>0 || dt.u<0) ||
                error("nontransverse linear stability crossing")
            @printf("linear_boundary,%s,%s,%s,[%s;%s],[%s;%s],[%s;%s],[%s;%s],[%s;%s],[%s;%s],[%s;%s]\n",
                    p.name,lower_text,upper_text,string(i.l),string(i.u),
                    string(r.l),string(r.u),string(left.l),string(left.u),
                    string(right.l),string(right.u),string(det.l),string(det.u),
                    string(di.l),string(di.u),string(dt.l),string(dt.u))
        end
        qprev,prev=q,curr
    end
end
end

function find_fold_bracket()
    candidates = Tuple{BigFloat,BigFloat}[]
    qprev = big"-30"
    iprev, _, _, dprev, fprev = branch(qprev)
    for k in 1:1000
        q = big"-30" + BigFloat(k)/10
        i, _, _, den, f = branch(q)
        if i > 0 && iprev > 0 && den > 0 && dprev > 0 && f*fprev < 0
            push!(candidates, (qprev, q))
        end
        qprev, iprev, dprev, fprev = q, i, den, f
    end
    return candidates
end

function bisect_fold(lo, hi)
    flo = branch(lo)[5]
    for _ in 1:250
        mid = (lo + hi)/2
        fmid = branch(mid)[5]
        if flo*fmid <= 0
            hi = mid
        else
            lo, flo = mid, fmid
        end
    end
    return lo, hi
end

# Every interval operation rounds toward the exterior. Decimal constants are
# enclosed by parsing separately under downward and upward MPFR rounding.
struct Iv
    l::BigFloat
    u::BigFloat
end
rd(f::Function) = setrounding(f, BigFloat, RoundDown)
ru(f::Function) = setrounding(f, BigFloat, RoundUp)
Iv(s::String) = Iv(rd(() -> parse(BigFloat,s)), ru(() -> parse(BigFloat,s)))
Iv(x::Integer) = Iv(BigFloat(x), BigFloat(x))
Base.:+(x::Iv,y::Iv) = Iv(rd(() -> x.l+y.l),ru(() -> x.u+y.u))
Base.:-(x::Iv) = Iv(-x.u,-x.l)
Base.:-(x::Iv,y::Iv) = x + (-y)
function Base.:*(x::Iv,y::Iv)
    lo = rd(() -> minimum((x.l*y.l,x.l*y.u,x.u*y.l,x.u*y.u)))
    hi = ru(() -> maximum((x.l*y.l,x.l*y.u,x.u*y.l,x.u*y.u)))
    return Iv(lo,hi)
end
function Base.inv(x::Iv)
    x.l <= 0 <= x.u && error("interval denominator contains zero")
    return Iv(rd(() -> inv(x.u)),ru(() -> inv(x.l)))
end
Base.:/(x::Iv,y::Iv) = x*inv(y)
Base.exp(x::Iv) = Iv(rd(() -> exp(x.l)),ru(() -> exp(x.u)))
sq(x::Iv) = x.l >= 0 ? Iv(rd(() -> x.l*x.l),ru(() -> x.u*x.u)) : x*x

function interval_branch(q::Iv)
    one, tv, al, gamma, g0, g1 = Iv(1), Iv("0.05"), Iv(50), Iv(2), Iv(120), Iv(30)
    r = inv(one+exp(-q))
    req = one-gamma*r+q/al
    c0 = one+tv*g0*sq(r)
    den = one-tv*g1*sq(r)*req
    current = req*c0/den
    rp = -gamma+inv(al*r*(one-r))
    c0p = Iv(2)*tv*g0*r
    denp = -(tv*g1*(Iv(2)*r*req+sq(r)*rp))
    didr = ((rp*c0+req*c0p)*den-req*c0*denp)/sq(den)
    return current,r,den,didr*r*(one-r)
end

function interval_nondegeneracy(q::Iv)
    one,tv,tr,al,gamma,g0,g1 = Iv(1),Iv("0.05"),Iv("0.005"),Iv(50),Iv(2),Iv(120),Iv(30)
    current,r,den,_ = interval_branch(q)
    c = g0+g1*current
    a = tv*c
    v = current/(one+a*sq(r))
    vp = -(Iv(2)*a*current*r)/sq(one+a*sq(r))
    vpp = -(Iv(2)*a*current*(one-Iv(3)*a*sq(r)))/((one+a*sq(r))*sq(one+a*sq(r)))
    hrr = al*r*(one-r)*(vpp+al*(one-Iv(2)*r)*sq(vp+gamma))
    vi = (one+tv*g0*sq(r))/sq(one+tv*c*sq(r))
    hi = al*r*(one-r)*vi
    trace = -(inv(tv)+c*sq(r))+(al*gamma*r*(one-r)-one)/tr
    return current,r,den,hrr,hi,trace
end

println("certificate_kind,q_lower,q_upper,I_lower,I_upper,r_lower,r_upper,left_derivative_interval,right_derivative_interval,Hrr_interval,HI_interval,trace_interval")
candidates = find_fold_bracket()
isempty(candidates) && error("no positive-current derivative sign-change bracket")
for (qlo0,qhi0) in candidates
    qlo,qhi = bisect_fold(qlo0,qhi0)
    # Print a slightly widened rational-decimal box around the BigFloat root.
    center = (qlo+qhi)/2
    radius = big"1e-16"
    lower_text = string(round(center-radius,RoundDown;digits=16,base=10))
    upper_text = string(round(center+radius,RoundUp;digits=16,base=10))
    qbox = Iv(lower_text).l <= Iv(upper_text).u ? Iv(Iv(lower_text).l,Iv(upper_text).u) : error("bad box")
    _,_,_,left_d = interval_branch(Iv(lower_text))
    _,_,_,right_d = interval_branch(Iv(upper_text))
    current,r,den,hrr,hi,trace = interval_nondegeneracy(qbox)
    (left_d.u < 0 && right_d.l > 0 || left_d.l > 0 && right_d.u < 0) ||
        error("derivative signs do not bracket a fold")
    den.l > 0 || error("parameterization denominator not positive")
    (hrr.l > 0 || hrr.u < 0) || error("Hrr interval includes zero")
    hi.l > 0 || error("HI interval not positive")
    trace.u < 0 || error("nonzero eigenvalue at fold not stable")
    @printf("local_fold,%s,%s,%s,%s,%s,%s,[%s;%s],[%s;%s],[%s;%s],[%s;%s],[%s;%s]\n",
            lower_text,upper_text,string(current.l),string(current.u),
            string(r.l),string(r.u),string(left_d.l),string(left_d.u),
            string(right_d.l),string(right_d.u),string(hrr.l),string(hrr.u),
            string(hi.l),string(hi.u),string(trace.l),string(trace.u))
end

audit_canonical()
