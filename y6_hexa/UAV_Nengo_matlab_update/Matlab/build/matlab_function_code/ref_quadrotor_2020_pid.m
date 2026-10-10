function ref = fcn(t, p)
%#codegen
omega = p(4);
x_ref = sin(omega*t);
dx_ref = omega*cos(omega*t);
y_ref = sin(omega*t);
dy_ref = omega*cos(omega*t);
[z_ref, dz_ref] = z_schedule(t);
psi_ref = 0.0;
ref = [x_ref; dx_ref; y_ref; dy_ref; z_ref; dz_ref; psi_ref];
end

function [z_ref, dz_ref] = z_schedule(t)
if t < 10.0
    z_ref = t/10.0;
    dz_ref = 0.1;
elseif t < 20.0
    z_ref = 1.0;
    dz_ref = 0.0;
elseif t < 30.0
    z_ref = 1.0 + (0.5 - 1.0)*(t - 20.0)/(30.0 - 20.0);
    dz_ref = -0.05;
else
    z_ref = 0.5;
    dz_ref = 0.0;
end
end
