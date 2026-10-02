using Test
using HyperLIFArchitectures

@testset "HyperLIF architecture invariants" begin
    p = HyperLIFParams{Float64}()
    s = HyperLIFState(3, 2, p)
    out = hyperlif_step(s, fill(0.75, 3, 2), p)
    @test all(0 .<= out.gate .<= 1)
    @test all(isfinite, out.voltage)

    x = reshape(Float64.(sin.(1:120)), 4, 3, 10)
    for kind in (:dense, :recurrent, :delay)
        model = init_architecture(4, 6, 2; kind=kind,
            readout=:hybrid_vr_conductance, params=p, seed=7)
        y = forward(model, x)
        @test size(y.features) == (18, 3)
        @test size(y.logits) == (2, 3)
        @test y.finite
    end
end

@testset "event semantics are explicit" begin
    occupancy = HyperLIFParams{Float64}(event_mode=:occupancy)
    crossing = HyperLIFParams{Float64}(event_mode=:upcrossing)
    so = HyperLIFState(1, 1, occupancy)
    sc = HyperLIFState(1, 1, crossing)
    so.v .= 1.2
    sc.v .= 1.2
    @test hyperlif_step(so, fill(4.0, 1, 1), occupancy).spikes[1] == 1.0
    @test hyperlif_step(sc, fill(4.0, 1, 1), crossing).spikes[1] == 0.0
    @test_throws ErrorException hyperlif_step(
        HyperLIFState(1, 1, HyperLIFParams{Float64}()), fill(0.0, 1, 1),
        HyperLIFParams{Float64}(event_mode=:invalid))
end

@testset "centered delay parity semantics and causal separation" begin
    p = HyperLIFParams{Float64}()
    dense = init_architecture(2, 3, 2; kind=:dense, params=p, seed=11)
    delay = init_architecture(2, 3, 2; kind=:delay, params=p, seed=99, kernel_size=7)
    delay.W_in .= dense.W_in
    delay.b_in .= dense.b_in
    delay.W_head .= dense.W_head
    delay.b_head .= dense.b_head
    x = randn(2, 4, 9)
    @test forward(dense, x).features ≈ forward(delay, x).features atol=1e-12

    # A noncentral future tap can affect centered offline delay but not causal delay.
    delay.delay_kernel .= 0
    delay.delay_kernel[:, end] .= 1
    delay.delay_mode = :centered
    centered = forward(delay, x).features
    delay.delay_mode = :causal
    causal = forward(delay, x).features
    @test !(centered ≈ causal)
end
