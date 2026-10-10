function ref = fcn(t, p)
%#codegen
k = p(4);
z_amp = p(5);
x_amp = p(6);
y_amp = p(7);
psi_ref_value = p(8);

% --- Sigmoid trajectory mission ----------------------------------------
%   x_d(t) = x_amp / (1 + exp(-k*(t - 5)))                  center 5, no delay
%   z_d(t) = z_amp / (1 + exp(-k*(t - 4)))                  center 4, no delay
%   y_d(t) = 0                              for t <  y_delay
%          = y_amp / (1 + exp(-k*((t - y_delay) - 5)))      center 5, delayed
% Amplitudes (x_amp, y_amp, z_amp) and k come from params/victor_pid_params.m;
% the centers and the y-channel delay are defined here.
y_delay = 15.0;

[z_ref, dz_sigmoid] = sigmoid_ref(t, z_amp, k, 4.0);
[x_ref, dx_ref] = sigmoid_ref(t, x_amp, k, 5.0);
if t < y_delay
    y_ref = 0.0;
    dy_ref = 0.0;
else
    [y_ref, dy_ref] = sigmoid_ref(t - y_delay, y_amp, k, 5.0);
end

% The original Victor Fcn z controller damps measured dz only; it does not
% subtract dz_ref. Keep this channel zero to make that convention explicit.
dz_ref = 0.0;
psi_ref = psi_ref_value;
ref = [x_ref; dx_ref; y_ref; dy_ref; z_ref; dz_ref; psi_ref];
end

function [r, dr] = sigmoid_ref(t, amp, k, center)
q = exp(-k*(t - center));
den = 1.0 + q;
r = amp/den;
dr = amp*k*q/(den*den);
end
