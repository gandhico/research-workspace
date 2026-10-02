# Calibration: learn the twin's sign conventions + arm range. Gentle, safe.
#  phase 1: 0 V settle  -> hanging alpha, arm rest
#  phase 2: +1.5 V step -> which way does +V move the arm? any limit?
#  phase 3: -1.5 V step -> the other way
include(joinpath(@__DIR__, "QuanserHIL.jl"))
using .QuanserHIL
const CPR=2048.0
ang(c)=2pi*Float64(c)/CPR
wrap(x)=mod(x+pi,2pi)-pi

function phase(card, volts, dur, hz)
    dt=1/hz; n=round(Int,dur*hz)
    th0=NaN; thmin=Inf; thmax=-Inf; al=0.0; ald=0.0; thd=0.0
    nextt=time()+dt
    for k in 1:n
        s=QuanserHIL.read_immediate(card; encoders=UInt32[0,1], other=UInt32[14000,14001])
        theta=ang(s.encoders[1]); alpha=wrap(ang(s.encoders[2])-pi)
        isnan(th0) && (th0=theta)
        thmin=min(thmin,theta); thmax=max(thmax,theta)
        al=alpha; ald=ang(s.other[2]); thd=ang(s.other[1])
        QuanserHIL.write_analog(card,UInt32[0],[volts])
        rem=nextt-time(); rem>0.002 && sleep(rem-0.002); while time()<nextt; end; nextt+=dt
    end
    (th0=th0, thmin=thmin, thmax=thmax, al=al, ald=ald, thd=thd)
end

function main()
    card=QuanserHIL.open_board(:qube3; target=:virtual)
    QuanserHIL.write_digital(card,UInt32[0],Int8[1])
    try
        p1=phase(card,0.0,1.5,200)
        println("0V settle : theta=", round(rad2deg(p1.th0),digits=1), "->", round(rad2deg(p1.thmax),digits=1),
                "  hanging alpha=", round(rad2deg(p1.al),digits=1), " deg (|.|=", round(rad2deg(abs(p1.al)),digits=1), ")")
        p2=phase(card,1.5,1.0,200)
        println("+1.5V     : theta range [", round(rad2deg(p2.thmin),digits=1), ",", round(rad2deg(p2.thmax),digits=1),
                "] end=", round(rad2deg(p2.th0),digits=1), "  arm speed(ch14000)=", round(p2.thd,digits=1), " rad/s")
        phase(card,0.0,1.0,200)            # let it settle back
        p3=phase(card,-1.5,1.0,200)
        println("-1.5V     : theta range [", round(rad2deg(p3.thmin),digits=1), ",", round(rad2deg(p3.thmax),digits=1),
                "] end=", round(rad2deg(p3.th0),digits=1), "  arm speed(ch14000)=", round(p3.thd,digits=1), " rad/s")
    finally
        QuanserHIL.write_analog(card,UInt32[0],[0.0])
        QuanserHIL.write_digital(card,UInt32[0],Int8[0])
        QuanserHIL.close(card)
    end
    println("calibration done")
end
main()
