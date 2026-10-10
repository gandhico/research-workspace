function [cmd, err, int_next] = fcn(t, ref, state, int_state, p)
%#codegen
pid_dt = p(1);
m = p(2);
g = p(3);
kp_z = p(5); ki_z = p(6); kd_z = p(7);
kp_x = p(8); ki_x = p(9); kd_x = p(10);
kp_y = p(11); ki_y = p(12); kd_y = p(13);
kp_phi = p(14); ki_phi = p(15); kd_phi = p(16);
kp_psi = p(17); ki_psi = p(18); kd_psi = p(19);
kp_theta = p(20); ki_theta = p(21); kd_theta = p(22);
tilt_limit = p(23);
den_min = p(24);
u_min = p(25);
u_max = p(26);
tau_psi_limit = p(27);
tau_theta_limit = p(28);
tau_phi_limit = p(29);
int_xy_lim = p(30);
int_z_lim = p(31);
int_att_lim = p(32);

x = state(1); dx = state(2);
y = state(3); dy = state(4);
z = state(5); dz = state(6);
psi = state(7); dpsi = state(8);
theta = state(9); dtheta = state(10);
phi = state(11); dphi = state(12);

ex = ref(1) - x;
edx = ref(2) - dx;
ey = ref(3) - y;
edy = ref(4) - dy;
ez = ref(5) - z;
edz = -dz;
epsi = wrap_pi(ref(7) - psi);
edpsi = -dpsi;

integ_new = int_state;
integ_new(1) = sat(int_state(1) + pid_dt*ex, int_xy_lim);
integ_new(2) = sat(int_state(2) + pid_dt*ey, int_xy_lim);
integ_new(3) = sat(int_state(3) + pid_dt*ez, int_z_lim);
integ_new(4) = sat(int_state(4) + pid_dt*epsi, int_att_lim);

ax_cmd = kp_x*ex + ki_x*integ_new(1) + kd_x*edx;
ay_cmd = kp_y*ey + ki_y*integ_new(2) + kd_y*edy;
uz_cmd = kp_z*ez + ki_z*integ_new(3) + kd_z*edz;

theta_d = atan2(ax_cmd, g);
phi_d = atan2(-ay_cmd*cos(theta), g);
theta_d = sat(theta_d, tilt_limit);
phi_d = sat(phi_d, tilt_limit);

etheta = theta_d - theta;
edtheta = -dtheta;
ephi = phi_d - phi;
edphi = -dphi;
integ_new(5) = sat(int_state(5) + pid_dt*etheta, int_att_lim);
integ_new(6) = sat(int_state(6) + pid_dt*ephi, int_att_lim);

u_unsat = (m*g + uz_cmd)/max(cos(theta)*cos(phi), den_min);
u = min(max(u_unsat, u_min), u_max);

tau_psi_unsat = kp_psi*epsi + ki_psi*integ_new(4) + kd_psi*edpsi;
tau_theta_unsat = kp_theta*etheta + ki_theta*integ_new(5) + kd_theta*edtheta;
tau_phi_unsat = kp_phi*ephi + ki_phi*integ_new(6) + kd_phi*edphi;

tau_psi = sat(tau_psi_unsat, tau_psi_limit);
tau_theta = sat(tau_theta_unsat, tau_theta_limit);
tau_phi = sat(tau_phi_unsat, tau_phi_limit);

cmd = [u; tau_psi; tau_theta; tau_phi; theta_d; phi_d; ax_cmd; ay_cmd; uz_cmd];
err = [ex; ey; ez; epsi; etheta; ephi; integ_new(1); integ_new(2); integ_new(3); integ_new(4); integ_new(5); integ_new(6)];
int_next = integ_new;
end

function y = sat(x, lim)
y = min(max(x, -lim), lim);
end

function y = wrap_pi(x)
y = mod(x + pi, 2*pi) - pi;
end
