# Startup trace: watch theta/alpha/alpha_dot and the control terms from rest,
# to see why the arm runs to a limit. Prints a downsampled trace. Safe: caps at 4 V.
include(joinpath(@__DIR__, "QuanserHIL.jl"))
using .QuanserHIL

const Rm=7.5; const kt=0.0422; const mr=0.095; const r=0.085
const mp=0.024; const Lp=0.129; const l=Lp/2; const g=9.81
const Jp_cm=mp*Lp^2/12
const Er=2*mp*g*l
const a_max=(kt*10/Rm)/(mr*r)
const ACC2V=mr*r*Rm/kt
const CPR=2048.0
ang(c)=2pi*Float64(c)/CPR
wrap(x)=mod(x+pi,2pi)-pi

function main(args)
    mu = length(args)>=1 ? parse(Float64,args[1]) : 45.0
    kc = length(args)>=2 ? parse(Float64,args[2]) : 2.5
    hz=200.0; dt=1/hz; dur=3.0; n=round(Int,dur*hz)
    card=QuanserHIL.open_board(:qube3; target=:virtual)
    QuanserHIL.write_digital(card,UInt32[0],Int8[1])
    println("t     theta°   alpha°   adot     upump   ucent    v")
    t0=time(); nextt=t0+dt
    try
        for k in 1:n
            s=QuanserHIL.read_immediate(card; encoders=UInt32[0,1], other=UInt32[14000,14001])
            theta=ang(s.encoders[1]); alpha=wrap(ang(s.encoders[2])-pi)
            theta_dot=ang(s.other[1]); alpha_dot=ang(s.other[2])
            E=0.5*Jp_cm*alpha_dot^2 + mp*g*l*(1+cos(alpha))
            upump=mu*(E-Er)*sign(alpha_dot*cos(alpha))
            ucent=-(kc*theta + 0.15*kc*theta_dot)
            u=clamp(upump+ucent,-a_max,a_max)
            v=clamp(ACC2V*u,-4.0,4.0)   # capped for safe diagnostic
            QuanserHIL.write_analog(card,UInt32[0],[v])
            if k % 15 == 0
                println(rpad(round(k/hz,digits=2),6),
                    rpad(round(rad2deg(theta),digits=1),9), rpad(round(rad2deg(alpha),digits=1),9),
                    rpad(round(alpha_dot,digits=2),9), rpad(round(upump,digits=2),8),
                    rpad(round(ucent,digits=2),9), round(v,digits=2))
            end
            rem=nextt-time(); rem>0.002 && sleep(rem-0.002); while time()<nextt; end; nextt+=dt
        end
    finally
        QuanserHIL.write_analog(card,UInt32[0],[0.0])
        QuanserHIL.write_digital(card,UInt32[0],Int8[0])
        QuanserHIL.close(card)
    end
    println("done")
end
main(ARGS)
