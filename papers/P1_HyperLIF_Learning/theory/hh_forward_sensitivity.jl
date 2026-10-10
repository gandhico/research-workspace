# Continuous forward sensitivity of classic HH to g_Na, integrated with RK4.
# Held initial state; compares with independently integrated finite differences.
include("hh_hyperlif_tiny_pes.jl")

function vtrap_prime(x,y)
    if abs(x/y)<1e-5
        return 0.5+x/(6y)-x^3/(180y^3)
    end
    q=exp(-x/y)
    den=-expm1(-x/y)
    return (den-x*q/y)/den^2
end
function rate_values_derivatives(v)
    am,bm,ah,bh,an,bn=hh_rates(v)
    dam=0.1*vtrap_prime(v+40,10)
    dbm=-bm/18
    dah=-ah/20
    dbh=bh*(1-bh)/10
    dan=0.01*vtrap_prime(v+55,10)
    dbn=-bn/80
    return (am,bm,ah,bh,an,bn),(dam,dbm,dah,dbh,dan,dbn)
end
function rhs_g(s,current,gna)
    v,m,h,n=s
    am,bm,ah,bh,an,bn=hh_rates(v)
    return (current-gna*m^3*h*(v-50)-36n^4*(v+77)-0.3*(v+54.387),
            am*(1-m)-bm*m,ah*(1-h)-bh*h,an*(1-n)-bn*n)
end
function aug_rhs(z,current,gna)
    v,m,h,n,sv,sm,sh,sn=z
    f=rhs_g((v,m,h,n),current,gna)
    rates,drates=rate_values_derivatives(v)
    am,bm,ah,bh,an,bn=rates
    dam,dbm,dah,dbh,dan,dbn=drates
    jvv=-(gna*m^3*h+36n^4+0.3)
    jvm=-3gna*m^2*h*(v-50)
    jvh=-gna*m^3*(v-50)
    jvn=-144n^3*(v+77)
    ds_v=jvv*sv+jvm*sm+jvh*sh+jvn*sn-m^3*h*(v-50)
    ds_m=(dam*(1-m)-dbm*m)*sv-(am+bm)*sm
    ds_h=(dah*(1-h)-dbh*h)*sv-(ah+bh)*sh
    ds_n=(dan*(1-n)-dbn*n)*sv-(an+bn)*sn
    return (f...,ds_v,ds_m,ds_h,ds_n)
end
addtuple(a,b,c)=ntuple(i->a[i]+c*b[i],length(a))
function rk4_step(z,current,gna,dt_ms,rhs)
    k1=rhs(z,current,gna)
    k2=rhs(addtuple(z,k1,dt_ms/2),current,gna)
    k3=rhs(addtuple(z,k2,dt_ms/2),current,gna)
    k4=rhs(addtuple(z,k3,dt_ms),current,gna)
    return ntuple(i->z[i]+dt_ms*(k1[i]+2k2[i]+2k3[i]+k4[i])/6,length(z))
end
function trajectory_at(initial,current,gna,seconds;dt_ms=0.025)
    s=initial
    for _ in 1:Int(round(seconds*1000/dt_ms))
        s=rk4_step(s,current,gna,dt_ms,rhs_g)
    end
    return s
end
function sensitivity_at(initial,current,gna,seconds;dt_ms=0.025)
    z=(initial...,0.0,0.0,0.0,0.0)
    for _ in 1:Int(round(seconds*1000/dt_ms))
        z=rk4_step(z,current,gna,dt_ms,aug_rhs)
    end
    return z
end

function main()
    println("current,initialization,time_s,voltage_mV,dV_dgNa_tangent,fd_step,dV_dgNa_fd,relative_error")
    for (current,label,initial) in ((0.0,"rest",hh_init()),
                                    (8.0,"rest",hh_init()),
                                    (8.0,"equilibrium",hh_equilibrium(8.0)))
        for seconds in (0.02,0.1,1.0,4.0,12.0)
            z=sensitivity_at(initial,current,120.0,seconds)
            for step in (0.01,0.001)
                vp=trajectory_at(initial,current,120.0+step,seconds)[1]
                vm=trajectory_at(initial,current,120.0-step,seconds)[1]
                fd=(vp-vm)/(2step)
                rel=abs(fd-z[5])/max(1e-10,abs(z[5]))
                @printf("%.1f,%s,%.3f,%.9g,%.9g,%.5g,%.9g,%.9g\n",
                        current,label,seconds,z[1],z[5],step,fd,rel)
            end
        end
    end
end
if abspath(PROGRAM_FILE)==@__FILE__
    main()
end
