%% victor_pid_params.m
% PID parameters for the R2025a PID conversions of the Victor baseline models.
% Run this script before simulating the generated PID models.

%% Shared discrete simulation settings
pid_dt = 0.001;

%% Modelo_1gdl_PID_R2025a parameters
m_1gdl = 1.0;
g_1gdl = 9.81;
theta_1gdl = 0.0;
phi_1gdl = 0.0;

pid1_z0 = 0.0;
pid1_dz0 = 0.0;
pid1_x0 = [pid1_z0; pid1_dz0];
pid1_int0 = 0.0;
pid1_t_stop = 20;
pid1_ref_k = 1.0;
pid1_z_ref_amplitude = 3.0;
pid1_z_ref_center = 4.0;

Kp_1gdl = 40.0;
Ki_1gdl = 2.0;
Kd_1gdl = 5.0;
pid1_int_limit = 5.0;
pid1_T_min = 0.0;
pid1_T_max = 3.0*m_1gdl*g_1gdl;

%% Quadri_Sub_Por_Partes_PID_R2025a and Quadri_Victor_combination_PID_R2025a
m_quad = 1.0;
g_quad = 9.81;
quad_x0 = zeros(12,1);
quad_int0 = zeros(6,1);
quad_t_stop = 60;       % 60 s run for the delayed-y sigmoid mission
quad_sigmoid_k = 1.0;
quad_z_ref = 3.0;       % z_d amplitude, center 4 (see ref_quad_local_pid.m)
quad_x_ref = 1.0;       % x_d amplitude, center 5
quad_y_ref = 1.5;       % y_d amplitude, center 5, 15 s delay
quad_psi_ref = 0.0;

% Original PD gains from Datos_quadri_Victor*.m, extended with integral terms.
kp_z = 40;     ki_z = 2.0;   kd_z = 5;
kp_x = 1.6;    ki_x = 0.08;  kd_x = 5;
kp_y = 3;      ki_y = 0.10;  kd_y = 2;
kp_psi = 7;    ki_psi = 0.20; kd_psi = 4;
kp_theta = 120; ki_theta = 1.5; kd_theta = 8;
kp_phi = 40;   ki_phi = 1.0; kd_phi = 8;

quad_tilt_limit = deg2rad(35);
quad_den_min = 0.25;
quad_u_min = 0.0;
quad_u_max = 3.0*m_quad*g_quad;
quad_tau_psi_limit = 20.0;
quad_tau_theta_limit = 80.0;
quad_tau_phi_limit = 80.0;
quad_int_xy_lim = 5.0;
quad_int_z_lim = 5.0;
quad_int_att_lim = 2.0;

%% Quadrotor_model_2020_PID_R2025a parameters
m_q2020 = 0.9;
g_q2020 = 9.81;
Ixx_q2020 = 0.01;
Iyy_q2020 = 0.01;
Izz_q2020 = 0.03;
q2020_x0 = [0.1; 0.0; -0.1; 0.0; 0.0; 0.0; 0.1; 0.0; 0.0; 0.0; 0.0; 0.0];
q2020_int0 = zeros(6,1);
q2020_t_stop = 50;
q2020_ref_omega = 0.1;

% Original PD gains from Values_Quadrotor_model.m, extended with integral terms.
kp_z_2020 = 40;      ki_z_2020 = 2.0;   kd_z_2020 = 5;
kp_x_2020 = 1.6;     ki_x_2020 = 0.08;  kd_x_2020 = 2;
kp_y_2020 = 3;       ki_y_2020 = 0.10;  kd_y_2020 = 2;
kp_phi_2020 = 40;    ki_phi_2020 = 1.0; kd_phi_2020 = 8;
kp_psi_2020 = 7;     ki_psi_2020 = 0.20; kd_psi_2020 = 4;
kp_theta_2020 = 120; ki_theta_2020 = 1.5; kd_theta_2020 = 8;

q2020_tilt_limit = deg2rad(35);
q2020_den_min = 0.25;
q2020_u_min = 0.0;
q2020_u_max = 3.0*m_q2020*g_q2020;
q2020_tau_psi_limit = 20.0;
q2020_tau_theta_limit = 80.0;
q2020_tau_phi_limit = 80.0;
q2020_int_xy_lim = 5.0;
q2020_int_z_lim = 5.0;
q2020_int_att_lim = 2.0;


%% Packed parameter vectors used by generated MATLAB Function blocks
% Editing the scalar values above and rebuilding updates these vectors.
pid1_param_vec = [pid_dt; m_1gdl; g_1gdl; theta_1gdl; phi_1gdl; ...
    pid1_ref_k; pid1_z_ref_amplitude; pid1_z_ref_center; ...
    Kp_1gdl; Ki_1gdl; Kd_1gdl; pid1_int_limit; pid1_T_min; pid1_T_max];

quad_param_vec = [pid_dt; m_quad; g_quad; quad_sigmoid_k; ...
    quad_z_ref; quad_x_ref; quad_y_ref; quad_psi_ref; ...
    kp_z; ki_z; kd_z; kp_x; ki_x; kd_x; kp_y; ki_y; kd_y; ...
    kp_psi; ki_psi; kd_psi; kp_theta; ki_theta; kd_theta; kp_phi; ki_phi; kd_phi; ...
    quad_tilt_limit; quad_den_min; quad_u_min; quad_u_max; ...
    quad_tau_psi_limit; quad_tau_theta_limit; quad_tau_phi_limit; ...
    quad_int_xy_lim; quad_int_z_lim; quad_int_att_lim];

q2020_param_vec = [pid_dt; m_q2020; g_q2020; q2020_ref_omega; ...
    kp_z_2020; ki_z_2020; kd_z_2020; kp_x_2020; ki_x_2020; kd_x_2020; ...
    kp_y_2020; ki_y_2020; kd_y_2020; kp_phi_2020; ki_phi_2020; kd_phi_2020; ...
    kp_psi_2020; ki_psi_2020; kd_psi_2020; kp_theta_2020; ki_theta_2020; kd_theta_2020; ...
    q2020_tilt_limit; q2020_den_min; q2020_u_min; q2020_u_max; ...
    q2020_tau_psi_limit; q2020_tau_theta_limit; q2020_tau_phi_limit; ...
    q2020_int_xy_lim; q2020_int_z_lim; q2020_int_att_lim];
