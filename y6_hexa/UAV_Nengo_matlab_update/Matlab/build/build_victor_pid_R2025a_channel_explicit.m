function build_victor_pid_R2025a_channel_explicit()
%BUILD_VICTOR_PID_R2025A_CHANNEL_EXPLICIT Channel-explicit twins of the PID models.
%
% Parallel, non-destructive version of build_victor_pid_R2025a. The original
% monolithic builder and its models are left untouched; this builder writes four
% models with a "_CE" suffix:
%
%   Modelo_1gdl_PID_R2025a_CE
%   Quadri_Sub_Por_Partes_PID_R2025a_CE
%   Quadri_Victor_combination_PID_R2025a_CE
%   Quadrotor_model_2020_PID_R2025a_CE
%
% In these twins every control channel (x, y, z, psi, theta, phi and the 1-DOF z)
% is its OWN labelled subsystem with an explicit error junction, P/I/D gains,
% integral memory (Unit Delay) and saturation. All bus vectors are split with
% Demux into individually NAMED signals (x_ref, ex, Ix, theta_d, tau_phi, ...) so
% each channel is trackable on the wires instead of disappearing into one
% monolithic MATLAB Function block. This matches the schematic in
% diagrams/Quadri_Victor_combination_PID_R2025a_CE.drawio.
%
% The per-channel control math is copied verbatim from the validated monolithic
% controllers (build/matlab_function_code/pid_*_controller.m), so the twins are
% numerically identical to the originals. Verify with run/compare_CE_vs_monolithic.
%
% The reference generators and RK4 plants are reused unchanged. The four logged
% signals (pid_reference, pid_state, pid_command, pid_error) keep the exact legacy
% vector order.

rootDir = fileparts(fileparts(mfilename('fullpath')));   % .../Matlab
modelDir = fullfile(rootDir, "models");
codeDir  = fullfile(rootDir, "build", "matlab_function_code");
paramFile = fullfile(rootDir, "params", "victor_pid_params.m");
if ~exist(modelDir, 'dir'), mkdir(modelDir); end
evalin('base', "run('" + strrep(paramFile,"'","''") + "')");
bdclose('all');

qIdx = quad_index_map();
q20Idx = q2020_index_map();

build_1gdl_channel_model("Modelo_1gdl_PID_R2025a_CE", modelDir, codeDir, paramFile, ...
    "ref_1gdl_pid.m", "plant_1gdl_rk4.m", "pid1_x0", "pid1_t_stop", "pid1_param_vec", 14);

build_quad_channel_model("Quadri_Sub_Por_Partes_PID_R2025a_CE", modelDir, codeDir, paramFile, ...
    "ref_quad_local_pid.m", "plant_quad_victor_rk4.m", "quad_x0", "quad_t_stop", "quad_param_vec", 36, qIdx);

build_quad_channel_model("Quadri_Victor_combination_PID_R2025a_CE", modelDir, codeDir, paramFile, ...
    "ref_quad_local_pid.m", "plant_quad_victor_rk4.m", "quad_x0", "quad_t_stop", "quad_param_vec", 36, qIdx);

build_quad_channel_model("Quadrotor_model_2020_PID_R2025a_CE", modelDir, codeDir, paramFile, ...
    "ref_quadrotor_2020_pid.m", "plant_quadrotor_2020_rk4.m", "q2020_x0", "q2020_t_stop", "q2020_param_vec", 32, q20Idx);

disp("Channel-explicit PID R2025a twins written to:");
disp(modelDir);
end

% =====================================================================
%  Quadrotor cascaded model (x,y,z position -> transformation ->
%  psi,theta,phi attitude -> thrust/mixer -> RK4 plant), channel explicit.
% =====================================================================
function build_quad_channel_model(model, modelDir, codeDir, paramFile, refScript, plantScript, x0Var, stopVar, paramVar, psize, ix)
new_model(model, paramFile, stopVar);

% --- Sources -------------------------------------------------------
add_block('simulink/Sources/Clock', model + "/Clock", 'Position', [40 30 70 60]);
add_block('simulink/Sources/Constant', model + "/Parameter Vector", 'Position', [40 120 150 170]);
set_param(model + "/Parameter Vector", 'Value', char(paramVar));

% --- Reference generator + split into named reference channels -----
add_mfunction_file(model + "/Reference Generator", fullfile(codeDir, refScript), [190 20 330 110]);
set_mf_size(model + "/Reference Generator", "t", "[1 1]");
set_mf_size(model + "/Reference Generator", "p", psz(psize));
set_mf_size(model + "/Reference Generator", "ref", "[7 1]");
add_block('simulink/Signal Routing/Demux', model + "/Demux Reference", 'Outputs', '7', 'Position', [380 20 390 200]);

% --- State memory (Unit Delay) + split into named state channels ---
add_block('simulink/Discrete/Unit Delay', model + "/State Memory", 'Position', [380 320 450 380]);
set_param(model + "/State Memory", 'InitialCondition', char(x0Var), 'SampleTime', 'pid_dt');
add_block('simulink/Signal Routing/Demux', model + "/Demux State", 'Outputs', '12', 'Position', [490 300 500 540]);

% --- RK4 plant -----------------------------------------------------
add_mfunction_file(model + "/Quadrotor Plant", fullfile(codeDir, plantScript), [1180 320 1340 400]);
set_mf_size(model + "/Quadrotor Plant", "state", "[12 1]");
set_mf_size(model + "/Quadrotor Plant", "cmd", "[4 1]");
set_mf_size(model + "/Quadrotor Plant", "p", psz(psize));
set_mf_size(model + "/Quadrotor Plant", "state_next", "[12 1]");

% --- Per-channel PID subsystems ------------------------------------
% Position loops -> acceleration / thrust commands
add_pid_channel(model, "PID X", [560 40], code_pos_channel(ix.x, ix.int_xy), ...
    ["ref" "dref" "x" "dx" "p"], ["acmd" "e" "I"], psize);
add_pid_channel(model, "PID Y", [560 180], code_pos_channel(ix.y, ix.int_xy), ...
    ["ref" "dref" "y" "dy" "p"], ["acmd" "e" "I"], psize);
add_pid_channel(model, "PID Z", [560 320], code_z_channel(ix.z, ix.int_z), ...
    ["ref" "z" "dz" "p"], ["uz" "e" "I"], psize);

% Position errors -> desired attitude (atan2 transformation)
add_fcn_block(model, "Transformation", [760 60], code_transformation(ix.tilt), ...
    ["ax" "ay" "theta" "p"], ["theta_d" "phi_d"], psize);

% Attitude loops -> torques
add_pid_channel(model, "PID Psi", [960 320], code_att_channel(ix.psi, ix.int_att, ix.tau_psi, true), ...
    ["ref" "ang" "dang" "p"], ["tau" "e" "I"], psize);
add_pid_channel(model, "PID Theta", [960 40], code_att_channel(ix.theta, ix.int_att, ix.tau_theta, false), ...
    ["ref" "ang" "dang" "p"], ["tau" "e" "I"], psize);
add_pid_channel(model, "PID Phi", [960 180], code_att_channel(ix.phi, ix.int_att, ix.tau_phi, false), ...
    ["ref" "ang" "dang" "p"], ["tau" "e" "I"], psize);

% Altitude command + attitude -> total thrust (mixer numerator)
add_fcn_block(model, "Thrust", [960 460], code_thrust(ix.den_min, ix.u_min, ix.u_max), ...
    ["uz" "theta" "phi" "p"], ["u"], psize);

% --- Mux of the 4 actuator commands routed to the plant ------------
add_block('simulink/Signal Routing/Mux', model + "/Mux Plant Command", 'Inputs', '4', 'Position', [1120 330 1130 410]);

% --- Logging muxes (preserve legacy vector order) ------------------
add_block('simulink/Signal Routing/Mux', model + "/Mux Command Log", 'Inputs', '9', 'Position', [1120 60 1130 240]);
add_block('simulink/Signal Routing/Mux', model + "/Mux Error Log", 'Inputs', '12', 'Position', [1120 560 1130 800]);

add_toworkspace(model + "/log_reference", "pid_reference", [430 20 550 50]);
add_toworkspace(model + "/log_state", "pid_state", [560 620 680 650]);
add_toworkspace(model + "/log_command", "pid_command", [1200 60 1320 90]);
add_toworkspace(model + "/log_error", "pid_error", [1200 560 1320 590]);
add_block('simulink/Sinks/Scope', model + "/State Scope", 'Position', [620 700 670 740]);
add_block('simulink/Sinks/Scope', model + "/Command Scope", 'Position', [1260 130 1310 170]);
add_block('simulink/Sinks/Terminator', model + "/Term dz_ref", 'Position', [560 540 580 560]);

% --- Wiring --------------------------------------------------------
wire(model, "Clock/1", "Reference Generator/1");
wire(model, "Parameter Vector/1", "Reference Generator/2");
wire(model, "Reference Generator/1", "Demux Reference/1", "ref_vec");
wire(model, "Reference Generator/1", "log_reference/1");

% Reference demux: 1 x_ref, 2 dx_ref, 3 y_ref, 4 dy_ref, 5 z_ref, 6 dz_ref, 7 psi_ref
wire(model, "Demux Reference/1", "PID X/1", "x_ref");
wire(model, "Demux Reference/2", "PID X/2", "dx_ref");
wire(model, "Demux Reference/3", "PID Y/1", "y_ref");
wire(model, "Demux Reference/4", "PID Y/2", "dy_ref");
wire(model, "Demux Reference/5", "PID Z/1", "z_ref");
wire(model, "Demux Reference/6", "Term dz_ref/1", "dz_ref");   % z loop damps measured dz only
wire(model, "Demux Reference/7", "PID Psi/1", "psi_ref");

% State feedback
wire(model, "Quadrotor Plant/1", "State Memory/1", "state_next");
wire(model, "State Memory/1", "Demux State/1", "state_vec");
wire(model, "State Memory/1", "Quadrotor Plant/1");
wire(model, "State Memory/1", "log_state/1");
wire(model, "State Memory/1", "State Scope/1");

% State demux: 1 x,2 dx,3 y,4 dy,5 z,6 dz,7 psi,8 dpsi,9 theta,10 dtheta,11 phi,12 dphi
wire(model, "Demux State/1", "PID X/3", "x");
wire(model, "Demux State/2", "PID X/4", "dx");
wire(model, "Demux State/3", "PID Y/3", "y");
wire(model, "Demux State/4", "PID Y/4", "dy");
wire(model, "Demux State/5", "PID Z/2", "z");
wire(model, "Demux State/6", "PID Z/3", "dz");
wire(model, "Demux State/7", "PID Psi/2", "psi");
wire(model, "Demux State/8", "PID Psi/3", "dpsi");
wire(model, "Demux State/9", "PID Theta/2", "theta");
wire(model, "Demux State/9", "Transformation/3");
wire(model, "Demux State/9", "Thrust/2");
wire(model, "Demux State/10", "PID Theta/3", "dtheta");
wire(model, "Demux State/11", "PID Phi/2", "phi");
wire(model, "Demux State/11", "Thrust/3");
wire(model, "Demux State/12", "PID Phi/3", "dphi");

% Parameter vector fan-out
wire(model, "Parameter Vector/1", "PID X/5");
wire(model, "Parameter Vector/1", "PID Y/5");
wire(model, "Parameter Vector/1", "PID Z/4");
wire(model, "Parameter Vector/1", "PID Psi/4");
wire(model, "Parameter Vector/1", "PID Theta/4");
wire(model, "Parameter Vector/1", "PID Phi/4");
wire(model, "Parameter Vector/1", "Transformation/4");
wire(model, "Parameter Vector/1", "Thrust/4");
wire(model, "Parameter Vector/1", "Quadrotor Plant/3");

% Cascade: position commands -> transformation / thrust
wire(model, "PID X/1", "Transformation/1", "ax_cmd");
wire(model, "PID Y/1", "Transformation/2", "ay_cmd");
wire(model, "PID Z/1", "Thrust/1", "uz_cmd");
wire(model, "Transformation/1", "PID Theta/1", "theta_d");
wire(model, "Transformation/2", "PID Phi/1", "phi_d");

% Actuator command mux to plant: [u; tau_psi; tau_theta; tau_phi]
wire(model, "Thrust/1", "Mux Plant Command/1", "u");
wire(model, "PID Psi/1", "Mux Plant Command/2", "tau_psi");
wire(model, "PID Theta/1", "Mux Plant Command/3", "tau_theta");
wire(model, "PID Phi/1", "Mux Plant Command/4", "tau_phi");
wire(model, "Mux Plant Command/1", "Quadrotor Plant/2", "cmd_vec");

% Command log mux: [u, tau_psi, tau_theta, tau_phi, theta_d, phi_d, ax_cmd, ay_cmd, uz_cmd]
wire(model, "Thrust/1", "Mux Command Log/1");
wire(model, "PID Psi/1", "Mux Command Log/2");
wire(model, "PID Theta/1", "Mux Command Log/3");
wire(model, "PID Phi/1", "Mux Command Log/4");
wire(model, "Transformation/1", "Mux Command Log/5");
wire(model, "Transformation/2", "Mux Command Log/6");
wire(model, "PID X/1", "Mux Command Log/7");
wire(model, "PID Y/1", "Mux Command Log/8");
wire(model, "PID Z/1", "Mux Command Log/9");
wire(model, "Mux Command Log/1", "log_command/1");
wire(model, "Mux Command Log/1", "Command Scope/1");

% Error log mux: [ex,ey,ez,epsi,etheta,ephi,Ix,Iy,Iz,Ipsi,Itheta,Iphi]
wire(model, "PID X/2", "Mux Error Log/1");
wire(model, "PID Y/2", "Mux Error Log/2");
wire(model, "PID Z/2", "Mux Error Log/3");
wire(model, "PID Psi/2", "Mux Error Log/4");
wire(model, "PID Theta/2", "Mux Error Log/5");
wire(model, "PID Phi/2", "Mux Error Log/6");
wire(model, "PID X/3", "Mux Error Log/7");
wire(model, "PID Y/3", "Mux Error Log/8");
wire(model, "PID Z/3", "Mux Error Log/9");
wire(model, "PID Psi/3", "Mux Error Log/10");
wire(model, "PID Theta/3", "Mux Error Log/11");
wire(model, "PID Phi/3", "Mux Error Log/12");
wire(model, "Mux Error Log/1", "log_error/1");

finish_model(model, modelDir);
end

% =====================================================================
%  1-DOF vertical hover model (single explicit altitude PID channel).
% =====================================================================
function build_1gdl_channel_model(model, modelDir, codeDir, paramFile, refScript, plantScript, x0Var, stopVar, paramVar, psize)
new_model(model, paramFile, stopVar);

add_block('simulink/Sources/Clock', model + "/Clock", 'Position', [40 30 70 60]);
add_block('simulink/Sources/Constant', model + "/Parameter Vector", 'Position', [40 120 150 170]);
set_param(model + "/Parameter Vector", 'Value', char(paramVar));

add_mfunction_file(model + "/Reference Generator", fullfile(codeDir, refScript), [190 20 330 110]);
set_mf_size(model + "/Reference Generator", "t", "[1 1]");
set_mf_size(model + "/Reference Generator", "p", psz(psize));
set_mf_size(model + "/Reference Generator", "ref", "[2 1]");
add_block('simulink/Signal Routing/Demux', model + "/Demux Reference", 'Outputs', '2', 'Position', [380 20 390 90]);

add_block('simulink/Discrete/Unit Delay', model + "/State Memory", 'Position', [380 320 450 380]);
set_param(model + "/State Memory", 'InitialCondition', char(x0Var), 'SampleTime', 'pid_dt');
add_block('simulink/Signal Routing/Demux', model + "/Demux State", 'Outputs', '2', 'Position', [490 320 500 400]);

add_mfunction_file(model + "/Hover Plant", fullfile(codeDir, plantScript), [900 320 1060 400]);
set_mf_size(model + "/Hover Plant", "state", "[2 1]");
set_mf_size(model + "/Hover Plant", "ctrl", "[1 1]");
set_mf_size(model + "/Hover Plant", "p", psz(psize));
set_mf_size(model + "/Hover Plant", "state_next", "[2 1]");

% Single altitude PID channel (with mg feed-forward), command order matches legacy.
add_pid_channel(model, "PID Z", [600 120], code_1gdl_channel(), ...
    ["z_ref" "dz_ref" "z" "dz" "p"], ["T" "T_unsat" "ff" "e" "I" "edot"], psize);

add_block('simulink/Signal Routing/Mux', model + "/Mux Command Log", 'Inputs', '6', 'Position', [840 60 850 240]);
add_block('simulink/Signal Routing/Mux', model + "/Mux Error Log", 'Inputs', '3', 'Position', [840 520 850 640]);

add_toworkspace(model + "/log_reference", "pid_reference", [430 20 550 50]);
add_toworkspace(model + "/log_state", "pid_state", [560 620 680 650]);
add_toworkspace(model + "/log_command", "pid_command", [920 60 1040 90]);
add_toworkspace(model + "/log_error", "pid_error", [920 520 1040 550]);
add_block('simulink/Sinks/Scope', model + "/Altitude Scope", 'Position', [620 700 670 740]);
add_block('simulink/Sinks/Scope', model + "/Thrust Scope", 'Position', [960 130 1010 170]);

wire(model, "Clock/1", "Reference Generator/1");
wire(model, "Parameter Vector/1", "Reference Generator/2");
wire(model, "Reference Generator/1", "Demux Reference/1", "ref_vec");
wire(model, "Reference Generator/1", "log_reference/1");
wire(model, "Demux Reference/1", "PID Z/1", "z_ref");
wire(model, "Demux Reference/2", "PID Z/2", "dz_ref");

wire(model, "Hover Plant/1", "State Memory/1", "state_next");
wire(model, "State Memory/1", "Demux State/1", "state_vec");
wire(model, "State Memory/1", "Hover Plant/1");
wire(model, "State Memory/1", "log_state/1");
wire(model, "State Memory/1", "Altitude Scope/1");
wire(model, "Demux State/1", "PID Z/3", "z");
wire(model, "Demux State/2", "PID Z/4", "dz");

wire(model, "Parameter Vector/1", "PID Z/5");
wire(model, "Parameter Vector/1", "Hover Plant/3");

wire(model, "PID Z/1", "Hover Plant/2", "T");

% Command log: [T, T_unsat, ff, e, I, edot]   (PID Z outports 1..6 in this order)
wire(model, "PID Z/1", "Mux Command Log/1");
wire(model, "PID Z/2", "Mux Command Log/2");
wire(model, "PID Z/3", "Mux Command Log/3");
wire(model, "PID Z/4", "Mux Command Log/4");
wire(model, "PID Z/5", "Mux Command Log/5");
wire(model, "PID Z/6", "Mux Command Log/6");
wire(model, "Mux Command Log/1", "log_command/1");
wire(model, "Mux Command Log/1", "Thrust Scope/1");

% Error log: [e, I, edot]
wire(model, "PID Z/4", "Mux Error Log/1");
wire(model, "PID Z/5", "Mux Error Log/2");
wire(model, "PID Z/6", "Mux Error Log/3");
wire(model, "Mux Error Log/1", "log_error/1");

finish_model(model, modelDir);
end

% =====================================================================
%  Per-channel control code generators (indices baked per model).
%  Math copied verbatim from the validated monolithic controllers.
% =====================================================================
function s = code_pos_channel(g, intidx)
% Position loop: acceleration command, derivative on (ref - state) rate.
s = sprintf([ ...
'function [acmd, e, I] = fcn(ref, dref, pos, dpos, p, I_prev)\n' ...
'%%#codegen\n' ...
'dt = p(1);\n' ...
'kp = p(%d); ki = p(%d); kd = p(%d); ilim = p(%d);\n' ...
'e = ref - pos;\n' ...
'de = dref - dpos;\n' ...
'I = min(max(I_prev + dt*e, -ilim), ilim);\n' ...
'acmd = kp*e + ki*I + kd*de;\n' ...
'end\n'], g(1), g(2), g(3), intidx);
end

function s = code_z_channel(g, intidx)
% Altitude loop: derivative damps measured dz only (no dz_ref term).
s = sprintf([ ...
'function [uz, e, I] = fcn(ref, z, dz, p, I_prev)\n' ...
'%%#codegen\n' ...
'dt = p(1);\n' ...
'kp = p(%d); ki = p(%d); kd = p(%d); ilim = p(%d);\n' ...
'e = ref - z;\n' ...
'de = -dz;\n' ...
'I = min(max(I_prev + dt*e, -ilim), ilim);\n' ...
'uz = kp*e + ki*I + kd*de;\n' ...
'end\n'], g(1), g(2), g(3), intidx);
end

function s = code_att_channel(g, intidx, taulimidx, wrapPsi)
% Attitude loop: derivative damps measured rate only, torque saturated.
if wrapPsi
    errLine = 'e = mod((ref - ang) + pi, 2*pi) - pi;\n';
else
    errLine = 'e = ref - ang;\n';
end
s = sprintf([ ...
'function [tau, e, I] = fcn(ref, ang, dang, p, I_prev)\n' ...
'%%#codegen\n' ...
'dt = p(1);\n' ...
'kp = p(%d); ki = p(%d); kd = p(%d); ilim = p(%d); taulim = p(%d);\n' ...
errLine ...
'de = -dang;\n' ...
'I = min(max(I_prev + dt*e, -ilim), ilim);\n' ...
'tau = min(max(kp*e + ki*I + kd*de, -taulim), taulim);\n' ...
'end\n'], g(1), g(2), g(3), intidx, taulimidx);
end

function s = code_transformation(tiltidx)
% Desired tilt from position acceleration commands (small-angle inversion).
s = sprintf([ ...
'function [theta_d, phi_d] = fcn(ax, ay, theta, p)\n' ...
'%%#codegen\n' ...
'g = p(3); tilt = p(%d);\n' ...
'theta_d = min(max(atan2(ax, g), -tilt), tilt);\n' ...
'phi_d = min(max(atan2(-ay*cos(theta), g), -tilt), tilt);\n' ...
'end\n'], tiltidx);
end

function s = code_thrust(denidx, uminidx, umaxidx)
% Total thrust = (mg + uz) / (cos theta cos phi), saturated.
s = sprintf([ ...
'function u = fcn(uz, theta, phi, p)\n' ...
'%%#codegen\n' ...
'm = p(2); g = p(3); den_min = p(%d); u_min = p(%d); u_max = p(%d);\n' ...
'u_unsat = (m*g + uz)/max(cos(theta)*cos(phi), den_min);\n' ...
'u = min(max(u_unsat, u_min), u_max);\n' ...
'end\n'], denidx, uminidx, umaxidx);
end

function s = code_1gdl_channel()
% 1-DOF altitude PID with mg feed-forward (param indices fixed for 1gdl vec).
s = [ ...
'function [T, T_unsat, ff, e, I, edot] = fcn(z_ref, dz_ref, z, dz, p, I_prev)' newline ...
'%#codegen' newline ...
'dt = p(1); m = p(2); g = p(3);' newline ...
'Kp = p(9); Ki = p(10); Kd = p(11); ilim = p(12); T_min = p(13); T_max = p(14);' newline ...
'e = z_ref - z;' newline ...
'edot = dz_ref - dz;' newline ...
'I = min(max(I_prev + dt*e, -ilim), ilim);' newline ...
'ff = m*g;' newline ...
'T_unsat = Kp*e + Ki*I + Kd*edot + ff;' newline ...
'T = min(max(T_unsat, T_min), T_max);' newline ...
'end' newline];
end

% =====================================================================
%  Parameter-vector index maps.
% =====================================================================
function ix = quad_index_map()
ix.x = [12 13 14]; ix.y = [15 16 17]; ix.z = [9 10 11];
ix.psi = [18 19 20]; ix.theta = [21 22 23]; ix.phi = [24 25 26];
ix.tilt = 27; ix.den_min = 28; ix.u_min = 29; ix.u_max = 30;
ix.tau_psi = 31; ix.tau_theta = 32; ix.tau_phi = 33;
ix.int_xy = 34; ix.int_z = 35; ix.int_att = 36;
end

function ix = q2020_index_map()
ix.z = [5 6 7]; ix.x = [8 9 10]; ix.y = [11 12 13];
ix.phi = [14 15 16]; ix.psi = [17 18 19]; ix.theta = [20 21 22];
ix.tilt = 23; ix.den_min = 24; ix.u_min = 25; ix.u_max = 26;
ix.tau_psi = 27; ix.tau_theta = 28; ix.tau_phi = 29;
ix.int_xy = 30; ix.int_z = 31; ix.int_att = 32;
end

% =====================================================================
%  Low-level builder helpers.
% =====================================================================
function new_model(model, paramFile, stopVar)
if bdIsLoaded(model), close_system(model, 0); end
new_system(model);
load_system(model);
% Portable callback: params/ is resolved relative to the saved model file (models/..)
set_param(model, 'InitFcn', "run(fullfile(fileparts(fileparts(get_param(bdroot,'FileName'))),'params','victor_pid_params.m'))");
set_param(model, 'SolverType', 'Fixed-step');
set_param(model, 'Solver', 'FixedStepDiscrete');
set_param(model, 'FixedStep', 'pid_dt');
set_param(model, 'StopTime', char(stopVar));
end

function finish_model(model, modelDir)
try
    Simulink.BlockDiagram.arrangeSystem(model);
catch
end
save_system(model, fullfile(modelDir, model + ".slx"), 'OverwriteIfChangedOnDisk', true);
close_system(model, 0);
end

function add_pid_channel(model, name, topLeft, codeStr, inNames, outNames, psize)
%ADD_PID_CHANNEL Subsystem = inports -> MATLAB Function (PID math) -> outports,
% with a self-contained integral memory (Unit Delay) fed back as the LAST
% function input. The integrator output is the channel output named "I".
ss = model + "/" + name;
add_block('built-in/Subsystem', ss, 'Position', [topLeft(1) topLeft(2) topLeft(1)+150 topLeft(2)+110]);
nin = numel(inNames);
for i = 1:nin
    add_block('built-in/Inport', ss + "/" + inNames(i), 'Position', [20 30+40*i 50 44+40*i]);
end
add_block('simulink/User-Defined Functions/MATLAB Function', ss + "/PID", 'Position', [180 40 320 200]);
set_chart_script(ss + "/PID", codeStr);
add_block('simulink/Discrete/Unit Delay', ss + "/Integral Memory", 'Position', [180 260 250 310]);
set_param(ss + "/Integral Memory", 'InitialCondition', '0', 'SampleTime', 'pid_dt');
nout = numel(outNames);
for j = 1:nout
    add_block('built-in/Outport', ss + "/" + outNames(j), 'Position', [400 30+40*j 430 44+40*j]);
end
% External inports -> first nin function inputs
for i = 1:nin
    add_line(ss, inNames(i) + "/1", "PID/" + string(i), 'autorouting', 'on');
end
% Integral memory -> last function input (I_prev)
add_line(ss, "Integral Memory/1", "PID/" + string(nin+1), 'autorouting', 'on');
% Function outputs -> outports
for j = 1:nout
    add_line(ss, "PID/" + string(j), outNames(j) + "/1", 'autorouting', 'on');
end
% Integral output feeds the memory
intIdx = find(outNames == "I", 1);
add_line(ss, "PID/" + string(intIdx), "Integral Memory/1", 'autorouting', 'on');
set_mf_size(ss + "/PID", "p", psz(psize));
try, Simulink.BlockDiagram.arrangeSystem(ss); catch, end
end

function add_fcn_block(model, name, topLeft, codeStr, inNames, outNames, psize)
%ADD_FCN_BLOCK Stateless subsystem: inports -> MATLAB Function -> outports.
ss = model + "/" + name;
add_block('built-in/Subsystem', ss, 'Position', [topLeft(1) topLeft(2) topLeft(1)+150 topLeft(2)+110]);
for i = 1:numel(inNames)
    add_block('built-in/Inport', ss + "/" + inNames(i), 'Position', [20 30+40*i 50 44+40*i]);
end
add_block('simulink/User-Defined Functions/MATLAB Function', ss + "/Fcn", 'Position', [180 40 320 200]);
set_chart_script(ss + "/Fcn", codeStr);
for j = 1:numel(outNames)
    add_block('built-in/Outport', ss + "/" + outNames(j), 'Position', [400 30+40*j 430 44+40*j]);
end
for i = 1:numel(inNames)
    add_line(ss, inNames(i) + "/1", "Fcn/" + string(i), 'autorouting', 'on');
end
for j = 1:numel(outNames)
    add_line(ss, "Fcn/" + string(j), outNames(j) + "/1", 'autorouting', 'on');
end
set_mf_size(ss + "/Fcn", "p", psz(psize));
try, Simulink.BlockDiagram.arrangeSystem(ss); catch, end
end

function h = wire(model, src, dst, name)
%WIRE add_line + optional signal name (named signals make channels trackable).
h = add_line(model, src, dst, 'autorouting', 'on');
if nargin >= 4 && strlength(string(name)) > 0
    try, set_param(h, 'Name', char(name)); catch, end
end
end

function add_mfunction_file(blockPath, scriptFile, pos)
add_block('simulink/User-Defined Functions/MATLAB Function', blockPath, 'Position', pos);
set_chart_script(blockPath, fileread(scriptFile));
end

function set_chart_script(blockPath, codeStr)
rt = sfroot;
chart = rt.find('-isa', 'Stateflow.EMChart', 'Path', char(blockPath));
if isempty(chart)
    error('Could not find MATLAB Function chart for %s', blockPath);
end
chart.Script = char(codeStr);
end

function set_mf_size(blockPath, dataName, dataSize)
rt = sfroot;
chart = rt.find('-isa', 'Stateflow.EMChart', 'Path', char(blockPath));
if isempty(chart)
    error('Could not find MATLAB Function chart for %s', blockPath);
end
data = chart.find('-isa', 'Stateflow.Data', 'Name', char(dataName));
if isempty(data)
    warning('Could not find data %s in %s', dataName, blockPath);
else
    data.Props.Array.Size = char(dataSize);
end
end

function add_toworkspace(blockPath, varName, pos)
add_block('simulink/Sinks/To Workspace', blockPath, 'Position', pos);
set_param(blockPath, 'VariableName', varName, 'SaveFormat', 'StructureWithTime');
end

function s = psz(n)
s = "[" + string(n) + " 1]";
end
