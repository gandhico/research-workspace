# Pure ODE replication of the quaternion attitude-control paper.
#
# Run from the project root:
#
#   julia experiments/quaternion_quad/paper_ode_replication.jl --solver rk4
#
# This writes:
#
#   results/logs/paper_ode_julia_summary.csv
#   results/figures/quaternion_quad/paper_ode_replication_julia/
#
# The CSV is compatible with the Python script:
#
#   python experiments/quaternion_quad/paper_ode_replication.py --solver rk4 --julia-csv results/logs/paper_ode_julia_summary.csv

using LinearAlgebra
using Printf
using Statistics

const PLOTS_LOAD_ERROR = Ref{Any}(nothing)
const HAS_PLOTS = try
    @eval import Plots
    true
catch err
    PLOTS_LOAD_ERROR[] = err
    false
end

const PAPER_I = Diagonal([6.5e-4, 6.5e-4, 1.2e-3])
const PAPER_PQ = 20.0
const PAPER_PW = 4.0
const PAPER_TAU_LIMIT = 4.0

function q_normalize(q)
    n = norm(q)
    if n < 1e-12
        return [1.0, 0.0, 0.0, 0.0]
    end
    return q ./ n
end

q_conj(q) = [q[1], -q[2], -q[3], -q[4]]

function q_mul(p, q)
    p0, p1, p2, p3 = p
    q0, q1, q2, q3 = q
    return [
        p0*q0 - p1*q1 - p2*q2 - p3*q3,
        p0*q1 + p1*q0 + p2*q3 - p3*q2,
        p0*q2 - p1*q3 + p2*q0 + p3*q1,
        p0*q3 + p1*q2 - p2*q1 + p3*q0,
    ]
end

function euler_to_quat(phi, theta, psi)
    cphi, sphi = cos(phi / 2.0), sin(phi / 2.0)
    cth, sth = cos(theta / 2.0), sin(theta / 2.0)
    cpsi, spsi = cos(psi / 2.0), sin(psi / 2.0)
    return q_normalize([
        cphi*cth*cpsi + sphi*sth*spsi,
        sphi*cth*cpsi - cphi*sth*spsi,
        cphi*sth*cpsi + sphi*cth*spsi,
        cphi*cth*spsi - sphi*sth*cpsi,
    ])
end

function quat_to_euler(q)
    q = q_normalize(q)
    q0, q1, q2, q3 = q
    phi = atan(2.0 * (q0*q1 + q2*q3), q0*q0 - q1*q1 - q2*q2 + q3*q3)
    theta = asin(clamp(2.0 * (q0*q2 - q3*q1), -1.0, 1.0))
    psi = atan(2.0 * (q0*q3 + q1*q2), q0*q0 + q1*q1 - q2*q2 - q3*q3)
    return [phi, theta, psi]
end

wrap_to_pi(x) = mod.(x .+ pi, 2.0*pi) .- pi

function q_angle_error(qerr)
    qerr = q_normalize(qerr)
    return 2.0 * atan(norm(qerr[2:4]), max(1e-12, abs(qerr[1])))
end

function reference_euler(t, scenario)
    if scenario == "step"
        return [t >= 1.0 ? 1.0 : 0.0, t >= 5.0 ? 1.0 : 0.0, t >= 9.0 ? 1.0 : 0.0]
    elseif scenario == "sine"
        return 0.5 .* sin.(t .+ [0.0, pi/2.0, pi])
    elseif scenario == "flip"
        phi = clamp((2.0*pi/5.0) * t, 0.0, 2.0*pi)
        return [phi, 0.0, 0.0]
    else
        error("Unknown scenario: $scenario")
    end
end

function reference_quat(t, scenario)
    phi, theta, psi = reference_euler(t, scenario)
    return euler_to_quat(phi, theta, psi)
end

scenario_time(scenario) = scenario == "flip" ? 5.0 : 15.0

function control_law(t, x, scenario, pq, pw, tau_limit, shortest_path)
    q = q_normalize(x[1:4])
    omega = x[5:7]
    qref = reference_quat(t, scenario)
    qerr = q_mul(qref, q_conj(q))
    if shortest_path && qerr[1] < 0.0
        qerr = -qerr
    end
    tau = -pq .* qerr[2:4] .- pw .* omega
    tau = clamp.(tau, -tau_limit, tau_limit)
    return tau, qref, q_normalize(qerr)
end

function rhs(t, x, scenario, pq, pw, tau_limit, shortest_path)
    q = q_normalize(x[1:4])
    omega = x[5:7]
    tau, _, _ = control_law(t, x, scenario, pq, pw, tau_limit, shortest_path)
    omega_quat = [0.0, omega[1], omega[2], omega[3]]
    qdot = -0.5 .* q_mul(omega_quat, q)
    wdot = PAPER_I \ (tau .- cross(omega, PAPER_I * omega))
    return [qdot; wdot]
end

function step_fixed(t, x, dt, scenario, solver, pq, pw, tau_limit, shortest_path)
    if solver == "euler"
        xnext = x .+ dt .* rhs(t, x, scenario, pq, pw, tau_limit, shortest_path)
    elseif solver == "midpoint"
        k1 = rhs(t, x, scenario, pq, pw, tau_limit, shortest_path)
        xnext = x .+ dt .* rhs(t + 0.5*dt, x .+ 0.5*dt .* k1, scenario, pq, pw, tau_limit, shortest_path)
    elseif solver == "rk4"
        k1 = rhs(t, x, scenario, pq, pw, tau_limit, shortest_path)
        k2 = rhs(t + 0.5*dt, x .+ 0.5*dt .* k1, scenario, pq, pw, tau_limit, shortest_path)
        k3 = rhs(t + 0.5*dt, x .+ 0.5*dt .* k2, scenario, pq, pw, tau_limit, shortest_path)
        k4 = rhs(t + dt, x .+ dt .* k3, scenario, pq, pw, tau_limit, shortest_path)
        xnext = x .+ (dt / 6.0) .* (k1 .+ 2.0 .* k2 .+ 2.0 .* k3 .+ k4)
    else
        error("Unsupported solver: $solver")
    end
    xnext[1:4] = q_normalize(xnext[1:4])
    return xnext
end

function simulate(scenario, solver, dt, pq, pw, tau_limit, shortest_path)
    tf = scenario_time(scenario)
    t = collect(0.0:dt:tf)
    if t[end] < tf
        push!(t, tf)
    end
    x = [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    states = zeros(length(t), 7)
    states[1, :] .= x
    tic = time()
    for k in 2:length(t)
        x = step_fixed(t[k-1], x, t[k] - t[k-1], scenario, solver, pq, pw, tau_limit, shortest_path)
        states[k, :] .= x
    end
    runtime = time() - tic

    q_hist = zeros(length(t), 4)
    q_ref_hist = zeros(length(t), 4)
    eul_ref_hist = zeros(length(t), 3)
    eul_meas_hist = zeros(length(t), 3)
    eul_err = zeros(length(t), 3)
    tau_hist = zeros(length(t), 3)
    qerr_angle = zeros(length(t))
    tau_norm = zeros(length(t))
    sat = falses(length(t))
    qnorm_err = zeros(length(t))

    for k in eachindex(t)
        xk = vec(states[k, :])
        q = q_normalize(xk[1:4])
        eul_ref = reference_euler(t[k], scenario)
        eul_meas = quat_to_euler(q)
        tau, qref, qerr = control_law(t[k], xk, scenario, pq, pw, tau_limit, shortest_path)
        q_hist[k, :] .= q
        q_ref_hist[k, :] .= qref
        eul_ref_hist[k, :] .= eul_ref
        eul_meas_hist[k, :] .= eul_meas
        tau_hist[k, :] .= tau
        eul_err[k, :] .= wrap_to_pi(eul_meas .- eul_ref)
        qerr_angle[k] = q_angle_error(qerr)
        tau_norm[k] = norm(tau)
        sat[k] = any(abs.(tau) .>= tau_limit - 1e-9)
        qnorm_err[k] = abs(norm(q) - 1.0)
    end

    return Dict(
        "source" => "julia",
        "scenario" => scenario,
        "solver" => solver,
        "dt" => dt,
        "runtime" => runtime,
        "t" => t,
        "state" => states,
        "q" => q_hist,
        "q_ref" => q_ref_hist,
        "eul_ref" => eul_ref_hist,
        "eul_meas" => eul_meas_hist,
        "eul_err" => eul_err,
        "tau" => tau_hist,
        "qerr_angle" => qerr_angle,
        "rmse_phi" => sqrt(mean(eul_err[:, 1] .^ 2)),
        "rmse_theta" => sqrt(mean(eul_err[:, 2] .^ 2)),
        "rmse_psi" => sqrt(mean(eul_err[:, 3] .^ 2)),
        "qerr_mean" => mean(qerr_angle),
        "qerr_max" => maximum(qerr_angle),
        "tau_mean" => mean(tau_norm),
        "tau_max" => maximum(tau_norm),
        "sat_fraction" => mean(sat),
        "qnorm_max_error" => maximum(qnorm_err),
    )
end

function arg_value(args, key, default)
    idx = findfirst(==(key), args)
    if idx === nothing || idx == length(args)
        return default
    end
    return args[idx + 1]
end

function ensure_plots()
    if !HAS_PLOTS
        println("Plots.jl is required for Julia figures.")
        println("Install once with:")
        println("  julia experiments/quaternion_quad/install_julia_plots.jl")
        println("The metrics CSV was still saved. Plotting error was: $(PLOTS_LOAD_ERROR[])")
        return false
    end
    return true
end

function savefig_safe(plot_obj, path)
    mkpath(dirname(path))
    Plots.savefig(plot_obj, path)
    println("Saved Julia figure: $path")
end

function plot_response(row, figures_dir)
    scenario = row["scenario"]
    solver = row["solver"]
    t = row["t"]
    eul_ref = row["eul_ref"]
    eul_meas = row["eul_meas"]
    tau = row["tau"]
    q = row["q"]
    q_ref = row["q_ref"]
    qerr_angle = row["qerr_angle"]
    label = "$(scenario)_$(solver)"

    if scenario == "step" || scenario == "sine"
        p1 = Plots.plot(t, eul_ref[:, 1], linestyle=:dash, label="reference", ylabel="Phi [rad]", grid=true)
        Plots.plot!(p1, t, eul_meas[:, 1], label="response")
        p2 = Plots.plot(t, eul_ref[:, 2], linestyle=:dash, label="reference", ylabel="Theta [rad]", grid=true)
        Plots.plot!(p2, t, eul_meas[:, 2], label="response")
        p3 = Plots.plot(t, eul_ref[:, 3], linestyle=:dash, label="reference", ylabel="Psi [rad]", grid=true)
        Plots.plot!(p3, t, eul_meas[:, 3], label="response")
        p4 = Plots.plot(t, qerr_angle, label="q error", ylabel="q error [rad]", xlabel="Time [s]", grid=true)
        fig = Plots.plot(
            p1, p2, p3, p4,
            layout=(4, 1),
            size=(900, 800),
            plot_title="Julia pure ODE attitude response: $(scenario), $(solver)",
        )
        savefig_safe(fig, joinpath(figures_dir, "$(label)_attitude_response.png"))

        c1 = Plots.plot(t, tau[:, 1], label="", ylabel="Mx [Nm]", grid=true)
        Plots.hline!(c1, [PAPER_TAU_LIMIT, -PAPER_TAU_LIMIT], linestyle=:dash, color=:black, label="")
        c2 = Plots.plot(t, tau[:, 2], label="", ylabel="My [Nm]", grid=true)
        Plots.hline!(c2, [PAPER_TAU_LIMIT, -PAPER_TAU_LIMIT], linestyle=:dash, color=:black, label="")
        c3 = Plots.plot(t, tau[:, 3], label="", ylabel="Mz [Nm]", xlabel="Time [s]", grid=true)
        Plots.hline!(c3, [PAPER_TAU_LIMIT, -PAPER_TAU_LIMIT], linestyle=:dash, color=:black, label="")
        fig = Plots.plot(
            c1, c2, c3,
            layout=(3, 1),
            size=(900, 650),
            plot_title="Julia pure ODE control effort: $(scenario), $(solver)",
        )
        savefig_safe(fig, joinpath(figures_dir, "$(label)_control_effort.png"))
    end

    if scenario == "flip"
        p1 = Plots.plot(t, eul_ref[:, 1], linestyle=:dash, label="reference", ylabel="Phi [rad]", grid=true)
        Plots.plot!(p1, t, eul_meas[:, 1], label="response")
        p2 = Plots.plot(t, tau[:, 1], label="", ylabel="Mx [Nm]", grid=true)
        Plots.hline!(p2, [PAPER_TAU_LIMIT, -PAPER_TAU_LIMIT], linestyle=:dash, color=:black, label="")
        p3 = Plots.plot(t, qerr_angle, label="q error", ylabel="q error [rad]", xlabel="Time [s]", grid=true)
        fig = Plots.plot(
            p1, p2, p3,
            layout=(3, 1),
            size=(900, 700),
            plot_title="Julia pure ODE flip response: $(solver)",
        )
        savefig_safe(fig, joinpath(figures_dir, "$(label)_phi_mx_error.png"))

        q0p = Plots.plot(t, q_ref[:, 1], linestyle=:dash, label="q0 reference", ylabel="q0", grid=true)
        Plots.plot!(q0p, t, q[:, 1], label="q0 response")
        q1p = Plots.plot(t, q_ref[:, 2], linestyle=:dash, label="q1 reference", ylabel="q1", xlabel="Time [s]", grid=true)
        Plots.plot!(q1p, t, q[:, 2], label="q1 response")
        fig = Plots.plot(
            q0p, q1p,
            layout=(2, 1),
            size=(900, 550),
            plot_title="Julia pure ODE flip quaternion components: $(solver)",
        )
        savefig_safe(fig, joinpath(figures_dir, "$(label)_q0_q1.png"))
    end
end

function plot_solver_comparison(rows, figures_dir)
    scenarios = sort(unique([row["scenario"] for row in rows]))
    solvers = sort(unique([row["solver"] for row in rows]))
    metrics = ["qerr_mean", "tau_mean", "sat_fraction", "runtime"]
    for scenario in scenarios
        subset = [row for row in rows if row["scenario"] == scenario]
        panels = []
        for metric in metrics
            values = [only([row[metric] for row in subset if row["solver"] == solver]) for solver in solvers]
            push!(panels, Plots.bar(solvers, values, label="", title=metric, grid=true, xrotation=25))
        end
        fig = Plots.plot(
            panels...,
            layout=(2, 2),
            size=(1000, 700),
            plot_title="Julia pure ODE solver comparison: $(scenario)",
        )
        savefig_safe(fig, joinpath(figures_dir, "$(scenario)_solver_comparison.png"))
    end
end

function main()
    args = ARGS
    scenario_arg = arg_value(args, "--scenario", "all")
    solver_arg = arg_value(args, "--solver", "rk4")
    dt = parse(Float64, arg_value(args, "--dt", "0.002"))
    pq = parse(Float64, arg_value(args, "--pq", string(PAPER_PQ)))
    pw = parse(Float64, arg_value(args, "--pw", string(PAPER_PW)))
    tau_limit = parse(Float64, arg_value(args, "--tau-limit", string(PAPER_TAU_LIMIT)))
    shortest_path = !("--long-flip" in args)
    plots_enabled = !("--no-plots" in args)

    scenarios = scenario_arg == "all" ? ["step", "sine", "flip"] : [scenario_arg]
    solvers = solver_arg == "all-fixed" ? ["euler", "midpoint", "rk4"] : [solver_arg]
    rows = Dict[]
    for scenario in scenarios
        for solver in solvers
            println("Running Julia pure ODE scenario=$scenario solver=$solver dt=$dt")
            push!(rows, simulate(scenario, solver, dt, pq, pw, tau_limit, shortest_path))
        end
    end

    root = normpath(joinpath(@__DIR__, "..", ".."))
    logs_dir = joinpath(root, "results", "logs")
    figures_dir = joinpath(root, "results", "figures", "quaternion_quad", "paper_ode_replication_julia")
    mkpath(logs_dir)
    path = joinpath(logs_dir, "paper_ode_julia_summary.csv")
    fields = [
        "source", "scenario", "solver", "dt", "runtime",
        "rmse_phi", "rmse_theta", "rmse_psi",
        "qerr_mean", "qerr_max", "tau_mean", "tau_max",
        "sat_fraction", "qnorm_max_error",
    ]
    open(path, "w") do io
        println(io, join(fields, ","))
        for row in rows
            println(io, join([string(row[field]) for field in fields], ","))
        end
    end
    println("Saved Julia summary: $path")

    if plots_enabled && ensure_plots()
        for row in rows
            plot_response(row, figures_dir)
        end
        if length(solvers) > 1
            plot_solver_comparison(rows, figures_dir)
        end
    end
end

main()
