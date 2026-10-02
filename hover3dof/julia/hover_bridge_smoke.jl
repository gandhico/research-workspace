using Test

include(joinpath(@__DIR__, "Hover3DOFHIL.jl"))
using .Hover3DOFHIL

@testset "3-DOF Hover Julia bridge (no hardware open)" begin
    p = probe()
    @test p.card_type == "q8_usb"
    @test p.hil_found
    @test motor_to_dac([-2.0, 6.0, 24.0, 60.0]) == [0.0, 2.0, 8.0, 8.0]
    f = RateFilter()
    for _ in 1:100
        rates = step!(f, [0.1, -0.2, 0.3], 1/200)
        @test all(isfinite, rates)
    end
end

println("HOVER_JULIA_V1_PASS: library/channel/units/filter tests; no device opened")
