# Two-unit, standard-library-only PES audit of the ACC CMG discretization.
# Run: julia --startup-file=no theory/tiny_pes_cmg.jl
# No AD, packages, datasets, checkpoints, or stored trajectories are required.
using Printf
using LinearAlgebra

const DT = 0.0005
const TAU_V = 0.05
const TAU_R = 0.005
const ALPHA = 50.0
const G0 = 120.0
const G1 = 30.0
const IBIAS = 0.75
const IGAIN = 1.25
const ACTIVITY_GAIN = 1.0e5
const ETA = 8.0e-4
const WMAX = 6.0

mutable struct Cell
    v::Float64
    r::Float64
    previous_v::Float64
end

Cell() = Cell(0.0, 0.0, 0.0)

@inline sigmoid(x) = x >= 0 ? 1 / (1 + exp(-x)) : exp(x) / (1 + exp(x))

function step!(c::Cell, current::Float64, gamma::Float64)
    c.previous_v = c.v
    target = sigmoid(clamp(ALPHA * (c.v - 1.0 + gamma * c.r), -60.0, 60.0))
    c.r = clamp(c.r + (DT / TAU_R) * (target - c.r), 0.0, 1.0)
    conductance = (G0 + G1 * abs(current)) * c.r^2
    rate = 1 / TAU_V + conductance
    steady_v = ((current / TAU_V) + 0.0 * conductance) / rate
    c.v = steady_v + exp(-rate * DT) * (c.v - steady_v)
    activity = clamp(ACTIVITY_GAIN * c.r, 0.0, 1.0)
    upcrossing = c.previous_v < 1.0 && c.v >= 1.0
    occupancy = c.v >= 1.0
    return activity, upcrossing, occupancy
end

@inline function signal(t::Float64, amplitude::Float64, phase::Float64)
    return amplitude * (0.8 * sin(2pi * 1.3 * t + phase) +
                        0.2 * sin(2pi * 3.7 * t - 0.4 * phase))
end

mutable struct Moments
    n::Int
    g11::Float64
    g12::Float64
    g22::Float64
    b1::Float64
    b2::Float64
    target2::Float64
    pes2::Float64
    saturated1::Int
    saturated2::Int
    events::Int
    occupancies::Int
end
Moments() = Moments(0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)

function record!(m::Moments, a1, a2, y, prediction, z1, z2, o1, o2)
    m.n += 1
    m.g11 += a1^2
    m.g12 += a1 * a2
    m.g22 += a2^2
    m.b1 += a1 * y
    m.b2 += a2 * y
    m.target2 += y^2
    m.pes2 += (y - prediction)^2
    m.saturated1 += a1 >= 1.0 - 1e-12
    m.saturated2 += a2 >= 1.0 - 1e-12
    m.events += Int(z1) + Int(z2)
    m.occupancies += Int(o1) + Int(o2)
end

function eigenvalues(m::Moments)
    a, b, d = m.g11 / m.n, m.g12 / m.n, m.g22 / m.n
    center = (a + d) / 2
    radius = sqrt(((a - d) / 2)^2 + b^2)
    return max(0.0, center - radius), center + radius
end

function oracle(m::Moments)
    # Tiny ridge is for a defined minimum-norm-like solution in rank loss.
    a, b, d = m.g11 + 1e-10, m.g12, m.g22 + 1e-10
    det = a * d - b^2
    return (d * m.b1 - b * m.b2) / det,
           (a * m.b2 - b * m.b1) / det
end

function run_case(label, gamma, amplitude)
    cells = (Cell(), Cell())
    weights = [0.0, 0.0]
    late = Moments()
    training = Moments()
    for k in 1:24000
        t = (k - 1) * DT
        y = signal(t, amplitude, 0.0)
        a1, z1, o1 = step!(cells[1], IBIAS + IGAIN * max(y, 0.0), gamma)
        a2, z2, o2 = step!(cells[2], IBIAS + IGAIN * max(-y, 0.0), gamma)
        prediction = clamp(weights[1] * a1 + weights[2] * a2, -1.0, 1.0)
        record!(training, a1, a2, y, prediction, z1, z2, o1, o2)
        if k > 16000
            record!(late, a1, a2, y, prediction, z1, z2, o1, o2)
        end
        error = y - prediction
        weights[1] = clamp(weights[1] + ETA * error * a1, -WMAX, WMAX)
        weights[2] = clamp(weights[2] + ETA * error * a2, -WMAX, WMAX)
    end
    oracle_weights = oracle(training)
    evaluation = Moments()
    oracle2 = 0.0
    tail_pes2 = 0.0
    tail_oracle2 = 0.0
    # Fresh cells and phase-shifted waveform test the mapping, not state carryover.
    cells = (Cell(), Cell())
    for k in 1:8000
        y = signal((k - 1) * DT, amplitude, 0.77)
        a1, z1, o1 = step!(cells[1], IBIAS + IGAIN * max(y, 0.0), gamma)
        a2, z2, o2 = step!(cells[2], IBIAS + IGAIN * max(-y, 0.0), gamma)
        prediction = clamp(weights[1] * a1 + weights[2] * a2, -1.0, 1.0)
        record!(evaluation, a1, a2, y, prediction, z1, z2, o1, o2)
        oracle_prediction = oracle_weights[1] * a1 + oracle_weights[2] * a2
        oracle2 += (y - oracle_prediction)^2
        if k > 2000
            tail_pes2 += (y - prediction)^2
            tail_oracle2 += (y - oracle_prediction)^2
        end
    end
    low, high = eigenvalues(late)
    @printf("%s,%.3f,%.3f,%.7g,%.7g,%.7g,%.7g,%.7g,%.7g,%.7g,%.4f,%.4f,%d,%d,%.5f,%.5f\n",
            label, gamma, amplitude, low, high,
            sqrt(late.pes2 / late.n), sqrt(evaluation.pes2 / evaluation.n),
            sqrt(oracle2 / evaluation.n), sqrt(tail_pes2 / 6000),
            sqrt(tail_oracle2 / 6000),
            evaluation.saturated1 / evaluation.n,
            evaluation.saturated2 / evaluation.n,
            evaluation.events, evaluation.occupancies,
            weights[1], weights[2])
end

println("case,gamma,amplitude,late_gram_min,late_gram_max,late_pes_rmse,test_pes_rmse,test_oracle_rmse,tail_pes_rmse,tail_oracle_rmse,sat_plus,sat_minus,test_upcrossings,test_occupancies,w_plus,w_minus")
run_case("ACC_full_low", 2.0, 0.08)
run_case("ACC_reduced_low", 0.0, 0.08)
run_case("ACC_full_high", 2.0, 0.35)
run_case("ACC_reduced_high", 0.0, 0.35)

# A three-feature decoder adds one analog voltage contrast to the two ACC
# activities. This keeps the network at two neurons and three decoder weights.
function run_hybrid(label, gamma, amplitude)
    cells = (Cell(), Cell())
    weights = zeros(3)
    gram = zeros(3, 3)
    cross = zeros(3)
    for k in 1:24000
        y = signal((k - 1) * DT, amplitude, 0.0)
        a1, _, _ = step!(cells[1], IBIAS + IGAIN * max(y, 0.0), gamma)
        a2, _, _ = step!(cells[2], IBIAS + IGAIN * max(-y, 0.0), gamma)
        features = [a1, a2, 10.0 * (cells[1].v - cells[2].v)]
        prediction = clamp(dot(weights, features), -1.0, 1.0)
        error = y - prediction
        for j in 1:3
            cross[j] += features[j] * y
            for i in 1:3
                gram[i, j] += features[i] * features[j]
            end
            weights[j] = clamp(weights[j] + ETA * error * features[j], -WMAX, WMAX)
        end
    end
    oracle_weights = (gram + 1e-8 * I) \ cross
    cells = (Cell(), Cell())
    pes2 = 0.0
    oracle2 = 0.0
    tail_pes2 = 0.0
    tail_oracle2 = 0.0
    for k in 1:8000
        y = signal((k - 1) * DT, amplitude, 0.77)
        a1, _, _ = step!(cells[1], IBIAS + IGAIN * max(y, 0.0), gamma)
        a2, _, _ = step!(cells[2], IBIAS + IGAIN * max(-y, 0.0), gamma)
        features = [a1, a2, 10.0 * (cells[1].v - cells[2].v)]
        pes2 += (y - clamp(dot(weights, features), -1.0, 1.0))^2
        oracle2 += (y - dot(oracle_weights, features))^2
        if k > 2000
            tail_pes2 += (y - clamp(dot(weights, features), -1.0, 1.0))^2
            tail_oracle2 += (y - dot(oracle_weights, features))^2
        end
    end
    @printf("%s,%.3f,%.3f,%.7g,%.7g,%.7g,%.7g,%.5f,%.5f,%.5f,%.5f\n", label, gamma,
            amplitude, sqrt(pes2 / 8000), sqrt(oracle2 / 8000),
            sqrt(tail_pes2 / 6000), sqrt(tail_oracle2 / 6000),
            weights[1], weights[2], weights[3], oracle_weights[3])
end

println("hybrid_case,gamma,amplitude,test_pes_rmse,test_oracle_rmse,tail_pes_rmse,tail_oracle_rmse,w_plus,w_minus,w_voltage_contrast,oracle_voltage_contrast")
run_hybrid("ACC_full_high_hybrid", 2.0, 0.35)
run_hybrid("ACC_reduced_high_hybrid", 0.0, 0.35)

# Fixed-current, single-neuron equilibrium scan. The scan brackets sign changes;
# it is a numerical audit, not a certified enumeration of tangent roots.
@inline function equilibrium_voltage(r, current)
    conductance = (G0 + G1 * abs(current)) * r^2
    return current / (1 + TAU_V * conductance)
end

@inline function gate_balance(r, current, gamma)
    v = equilibrium_voltage(r, current)
    return sigmoid(ALPHA * (v - 1 + gamma * r)) - r
end

function roots(current, gamma)
    found = Float64[]
    ngrid = 10000
    left = 0.0
    fleft = gate_balance(left, current, gamma)
    for k in 1:ngrid
        right = k / ngrid
        fright = gate_balance(right, current, gamma)
        if fleft * fright < 0 || fright == 0.0
            lo, hi = left, right
            flo = fleft
            for _ in 1:55
                mid = (lo + hi) / 2
                fmid = gate_balance(mid, current, gamma)
                if flo * fmid <= 0
                    hi = mid
                else
                    lo, flo = mid, fmid
                end
            end
            root = (lo + hi) / 2
            if isempty(found) || abs(root - found[end]) > 1e-7
                push!(found, root)
            end
        end
        left, fleft = right, fright
    end
    return found
end

println("equilibrium_case,current,gamma,r,v,trace,determinant,locally_stable")
for (label, gamma) in (("ACC_full", 2.0), ("ACC_reduced", 0.0))
    for current in (0.75, 0.85, 1.10)
        for r in roots(current, gamma)
            v = equilibrium_voltage(r, current)
            cscale = G0 + G1 * abs(current)
            lambda = 1 / TAU_V + cscale * r^2
            sigprime = r * (1 - r)
            j11 = -lambda
            j12 = -2 * cscale * r * v
            j21 = ALPHA * sigprime / TAU_R
            j22 = (ALPHA * gamma * sigprime - 1) / TAU_R
            trace = j11 + j22
            determinant = j11 * j22 - j12 * j21
            @printf("%s,%.2f,%.1f,%.9g,%.9g,%.6g,%.6g,%s\n",
                    label, current, gamma, r, v, trace, determinant,
                    trace < 0 && determinant > 0 ? "true" : "false")
        end
    end
end
