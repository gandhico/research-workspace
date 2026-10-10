function state_next = fcn(state, ctrl, p)
%#codegen
h = p(1);
T = ctrl(1);
k1 = dyn_1gdl(state, T, p);
k2 = dyn_1gdl(state + 0.5*h*k1, T, p);
k3 = dyn_1gdl(state + 0.5*h*k2, T, p);
k4 = dyn_1gdl(state + h*k3, T, p);
state_next = state + (h/6.0)*(k1 + 2.0*k2 + 2.0*k3 + k4);
end

function dx = dyn_1gdl(x, T, p)
m = p(2);
g = p(3);
theta = p(4);
phi = p(5);
z_dot = x(2);
z_ddot = (T/m)*cos(theta)*cos(phi) - g;
dx = [z_dot; z_ddot];
end
