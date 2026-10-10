# Local constant-current equilibrium and Jacobian of canonical HH equations.
include("hh_hyperlif_tiny_pes.jl")

function hh_jacobian(s,current)
    J=zeros(4,4)
    for j in 1:4
        epsj=1e-5*max(abs(s[j]),1.0)
        sp=ntuple(i->i==j ? s[i]+epsj : s[i],4)
        sm=ntuple(i->i==j ? s[i]-epsj : s[i],4)
        fp=hh_rhs(sp,current); fm=hh_rhs(sm,current)
        for i in 1:4
            J[i,j]=(fp[i]-fm[i])/(2epsj)
        end
    end
    return J
end
println("current_uA_per_cm2,voltage_mV,m,h,n,eigenvalues_per_ms")
for current in (0.0,8.0)
    s=hh_equilibrium(current)
    e=eigvals(hh_jacobian(s,current))
    @printf("%.1f,%.9f,%.9f,%.9f,%.9f,%s\n",current,s...,join(string.(e),";"))
end
