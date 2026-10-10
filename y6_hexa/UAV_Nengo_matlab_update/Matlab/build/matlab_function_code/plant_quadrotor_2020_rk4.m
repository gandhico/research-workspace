function state_next = fcn(state, cmd, p)
%#codegen
h = p(1);
k1 = dyn_quad2020(state, cmd, p);
k2 = dyn_quad2020(state + 0.5*h*k1, cmd, p);
k3 = dyn_quad2020(state + 0.5*h*k2, cmd, p);
k4 = dyn_quad2020(state + h*k3, cmd, p);
state_next = state + (h/6.0)*(k1 + 2.0*k2 + 2.0*k3 + k4);
end

function dX = dyn_quad2020(x, cmd, p)
m = p(2);
g = p(3);
u = cmd(1);
tau_psi = cmd(2);
tau_theta = cmd(3);
tau_phi = cmd(4);
psi = x(7); theta = x(9); phi = x(11);

dX = zeros(12,1);
dX(1) = x(2);
dX(2) = u*(sin(phi)*sin(psi) + cos(phi)*cos(psi)*sin(theta))/m;
dX(3) = x(4);
dX(4) = u*(cos(phi)*sin(theta)*sin(psi) - cos(psi)*sin(phi))/m;
dX(5) = x(6);
dX(6) = u*(cos(theta)*cos(phi))/m - g;
dX(7) = x(8);
dX(8) = tau_psi;
dX(9) = x(10);
dX(10) = tau_theta;
dX(11) = x(12);
dX(12) = tau_phi;
end
