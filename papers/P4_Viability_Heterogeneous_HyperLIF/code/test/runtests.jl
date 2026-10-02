using HyperLIFLearning
using LinearAlgebra
using Random
using Test
using ViabilityHyperLIF
using Zygote

@testset "viability geometry" begin
    box = ViabilityBox([-2, 0], [2, 10]; names=[:position, :battery])
    @test viability_health([0, 5], box) == 1f0
    @test viability_health([2, 5], box) == 0f0
    @test viability_health([2.2, 5], box) < 0f0
    @test viability_region(0.8) == :nominal
    @test viability_region(0.4) == :adaptive
    @test viability_region(0.1) == :protective
    @test viability_region(-0.1) == :emergency
end

@testset "regime construction and arbitration" begin
    regimes = default_regimes()
    base = HyperConfig(cell=:hyperlif, architecture=:dense,
                       learning_mode=:continuous, readout=:hybrid_vr)
    configs = build_population_configs(base, regimes)
    @test length(configs) == 4
    @test configs[1].v_threshold > configs[end].v_threshold
    @test configs[1].event_threshold == configs[1].v_threshold
    safe_weights = regime_weights(0.95, regimes)
    critical_weights = regime_weights(0.05, regimes)
    @test isapprox(sum(safe_weights), 1f0; atol=1f-6)
    @test argmax(safe_weights) == 1
    @test argmax(critical_weights) == 4
    @test collect(getproperty.(shd_calibrated_regimes(), :input_scale)) ==
          Float32[2, 4, 32, 32]
end

@testset "heterogeneous forward and gradient" begin
    rng = MersenneTwister(19)
    base = HyperConfig(cell=:hyperlif, architecture=:dense,
                       learning_mode=:continuous, readout=:hybrid_vr,
                       alpha=30f0)
    configs = build_population_configs(base)
    parameters = init_heterogeneous_parameters(rng, 3, 3, 2, configs)
    input = randn(rng, Float32, 3, 4, 10)
    targets = Float32[1 0 1 0; 0 1 0 1]
    logits, aux = heterogeneous_forward(parameters, input, configs)
    @test size(logits) == (2, 4)
    @test all(isfinite, logits)
    @test isapprox(sum(aux.weights), 1f0; atol=1f-6)
    loss = heterogeneous_classification_loss(parameters, input, targets, configs)
    @test isfinite(loss)
    gradient = Zygote.gradient(
        p -> heterogeneous_classification_loss(p, input, targets, configs), parameters)[1]
    @test all(isfinite, gradient.mix_logits)
    @test all(isfinite, gradient.populations[1].W_head)
end

@testset "coupled homeostasis" begin
    regimes = default_regimes()
    state = HomeostaticState(length(regimes))
    observed = Float32[0.10, 0.10, 0.10, 0.40]
    updated = update_homeostasis(state, observed, regimes;
                                 ema_fraction=1f0, learning_rate=0.2f0)
    @test all(updated.threshold_offsets .> 0f0)
    frozen = update_homeostasis(state, observed, regimes;
                                ema_fraction=1f0, learning_rate=0.2f0, gate=0f0)
    @test all(iszero, frozen.threshold_offsets)
    @test plasticity_gate(0.8) > 0.99f0
    @test plasticity_gate(0.0) < 0.01f0
    @test rate_band_penalty(observed, regimes) > 0f0
end

@testset "reference CBF shield" begin
    box = ViabilityBox([-1, -1], [1, 1])
    x = Float32[0.95, 0.0]
    drift = zeros(Float32, 2)
    control = Matrix{Float32}(I, 2, 2)
    result = shield_action(Float32[1, 0], x, drift, control, box;
                           kappa=2f0,
                           action_lower=Float32[-2, -2],
                           action_upper=Float32[2, 2])
    @test result.certified
    @test result.action[1] <= 0.10002f0
    @test result.max_violation <= 1f-5

    infeasible = CBFConstraints(Float32[1; -1;;], Float32[-1, -1])
    failed = project_halfspaces(Float32[0], infeasible; max_sweeps=5)
    @test !failed.certified
end

@testset "shared-gain profile and matched controls" begin
    bank = shd_shared_gain_regimes()
    @test length(bank) == 4
    # One shared gain: the regime must come from the intrinsic parameters, not
    # from a per-population input signal-to-noise advantage.
    @test length(unique(getproperty.(bank, :input_scale))) == 1
    @test all(regime -> regime.input_scale == 1.4f0, bank)
    # Bands must be ordered and non-overlapping, and must lie inside the rates
    # actually reachable on the SHD cache (results/shared_gain_sweep.csv).
    for index in 1:3
        @test bank[index].target_rate_max <= bank[index + 1].target_rate_min
    end
    @test bank[1].target_rate_min == 0f0
    @test bank[end].target_rate_max <= 0.05f0
    @test shd_shared_gain_regimes(2f0)[1].input_scale == 2f0

    averaged = mean_regime(bank)
    @test averaged.name == :homogeneous_mean
    @test averaged.input_scale == 1.4f0
    @test isapprox(averaged.tau_v, sum(getproperty.(bank, :tau_v)) / 4; atol=1f-7)
    @test isapprox(averaged.v_threshold,
                   sum(getproperty.(bank, :v_threshold)) / 4; atol=1f-6)
    @test length(matched_homogeneous_regime(bank)) == 1

    # Budget matching: four narrow populations against one wide one.
    rng = MersenneTwister(31)
    base = HyperConfig(cell=:hyperlif, architecture=:dense,
                       learning_mode=:continuous, readout=:hybrid_vr)
    used(parameters, configs) = sum(
        length(population.W_in) + length(population.b_in) +
        length(population.W_head) + length(population.b_head)
        for (population, config) in zip(parameters.populations, configs)) +
        length(parameters.mix_logits)
    hidden, n_input, n_classes = 6, 40, 20
    het_configs = build_population_configs(base, bank)
    het = init_heterogeneous_parameters(rng, n_input, hidden, n_classes, het_configs)
    hom_configs = build_population_configs(base, matched_homogeneous_regime(bank))
    hom = init_heterogeneous_parameters(rng, n_input, hidden * 4, n_classes, hom_configs)
    @test used(het, het_configs) - used(hom, hom_configs) == 3 * n_classes + 3
end
