using Test
using LinearAlgebra
using Random
using Zygote
using HyperLIFLearning

@testset "learning-mode primitives" begin
    previous = fill(0.95f0, 2, 2)
    next = fill(0.99f0, 2, 2)
    @test all(iszero, surrogate_upcrossing(previous, next, 1f0, 10f0))
    gradient_next = Zygote.gradient(
        value -> sum(surrogate_upcrossing(previous, value, 1f0, 10f0)), next)[1]
    @test all(isfinite, gradient_next)
    @test all(>(0f0), gradient_next)

    crossing = fill(1.05f0, 2, 2)
    @test all(==(1f0), hard_upcrossing(previous, crossing, 1f0))

    f(value) = first(interpolated_event_time(
        fill(0.8f0, 1, 1), fill(value, 1, 1), 1f0, 0f0, 1f-3))[1]
    value = 1.2f0
    automatic = Zygote.gradient(f, value)[1]
    epsilon = 1f-4
    finite_difference = (f(value + epsilon) - f(value - epsilon)) / (2f0 * epsilon)
    @test isapprox(automatic, finite_difference; rtol=2f-3, atol=2f-5)

    trace = Float32[0.9, 1.1, 1.2, 0.8, 1.05]
    crossings = sum(hard_upcrossing(trace[1:end-1], trace[2:end], 1f0))
    occupancy = sum(Float32.(trace[2:end] .>= 1f0))
    @test crossings == 2f0
    @test occupancy == 3f0
end

@testset "three cells x three learning modes" begin
    rng = MersenneTwister(11)
    input = randn(rng, Float32, 3, 4, 12)
    labels = [1, 2, 1, 2]
    targets = zeros(Float32, 2, 4)
    for b in eachindex(labels)
        targets[labels[b], b] = 1f0
    end

    for cell in (:hyperlif, :adaptive, :next)
        for mode in (:continuous, :surrogate, :event_time)
            config = HyperConfig(cell=cell, learning_mode=mode,
                                 architecture=:dense, alpha=30f0,
                                 input_scale=4f0)
            parameters = init_parameters(rng, 3, 5, 2, config)
            logits, aux = forward(parameters, input, config)
            @test size(logits) == (2, 4)
            @test all(isfinite, logits)
            @test 0f0 <= aux.no_event_fraction <= 1f0
            @test aux.occupancy_per_sample >= 0f0
            @test aux.crossings_per_sample >= 0f0
            loss = classification_loss(parameters, input, targets, config)
            @test isfinite(loss)
            gradients = Zygote.gradient(
                p -> classification_loss(p, input, targets, config), parameters)[1]
            @test gradients.W_head !== nothing
            @test all(isfinite, gradients.W_head)
            @test gradients.W_in === nothing || all(isfinite, gradients.W_in)
        end
    end
end

@testset "architecture contracts" begin
    rng = MersenneTwister(4)
    input = randn(rng, Float32, 2, 3, 9)
    for architecture in (:dense, :recurrent, :delay)
        config = HyperConfig(cell=:next, learning_mode=:continuous,
                             architecture=architecture, delay_mode=:causal,
                             alpha=25f0, input_scale=3f0)
        parameters = init_parameters(rng, 2, 4, 3, config)
        logits, _ = forward(parameters, input, config)
        @test size(logits) == (3, 3)
        @test parameter_count(parameters) > 0
    end

    @test_throws ErrorException validate_config(HyperConfig(delay_kernel_size=4))
    @test feature_dimension(HyperConfig(cell=:next, learning_mode=:continuous), 7) == 35
    @test feature_dimension(HyperConfig(learning_mode=:surrogate), 7) == 7
    @test feature_dimension(HyperConfig(learning_mode=:event_time), 7) == 7

    bounded_config = HyperConfig(recurrent_gain=0.3f0)
    raw_recurrence = 10f0 .* randn(rng, Float32, 12, 12)
    effective_recurrence = HyperLIFLearning._bounded_recurrent_matrix(
        raw_recurrence, bounded_config)
    @test opnorm(effective_recurrence) <= bounded_config.recurrent_gain + 5f-6

    # Per-sample normalization must not make a prediction depend on unrelated
    # examples sharing its minibatch.
    batch_config = HyperConfig(cell=:hyperlif, learning_mode=:continuous,
                               architecture=:dense, readout=:hybrid_vr,
                               input_scale=3f0)
    batch_parameters = init_parameters(rng, 2, 4, 3, batch_config)
    sample_a = randn(rng, Float32, 2, 1, 9)
    sample_b = randn(rng, Float32, 2, 1, 9)
    logits_alone, _ = forward(batch_parameters, sample_a, batch_config)
    logits_together, _ = forward(batch_parameters, cat(sample_a, sample_b; dims=2),
                                 batch_config)
    @test isapprox(logits_alone[:, 1], logits_together[:, 1]; rtol=2f-5, atol=2f-5)
end
