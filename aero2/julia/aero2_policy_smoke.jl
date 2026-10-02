module Aero2PolicySmoke

using Printf

const PD_KP_PITCH = 116.24203523333735
const PD_KD_PITCH = 99.698951398313469
const PD_KP_YAW = 35.8625570008741
const PD_KD_YAW = 38.028899215266975
const V_MAX = 24.0

function pd_policy(theta, theta_rate_f, psi, psi_rate_f, ref_theta, ref_psi, _dt=nothing)
    u_pitch = PD_KP_PITCH * (ref_theta - theta) - PD_KD_PITCH * theta_rate_f
    u_yaw = PD_KP_YAW * (ref_psi - psi) - PD_KD_YAW * psi_rate_f
    return (
        clamp(u_pitch, -V_MAX, V_MAX),
        clamp(u_yaw, -V_MAX, V_MAX),
    )
end

function main(args)
    if length(args) != 7
        error("usage: julia aero2_policy_smoke.jl theta theta_rate_f psi psi_rate_f ref_theta ref_psi dt")
    end
    theta, theta_rate_f, psi, psi_rate_f, ref_theta, ref_psi, _dt = parse.(Float64, args)
    u_pitch, u_yaw = pd_policy(theta, theta_rate_f, psi, psi_rate_f, ref_theta, ref_psi)
    @printf("%.17g,%.17g\n", u_pitch, u_yaw)
end

end

if abspath(PROGRAM_FILE) == @__FILE__
    Aero2PolicySmoke.main(ARGS)
end
