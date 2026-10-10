function [ctrl, err, int_next] = fcn(t, ref, state, int_state, p)
%#codegen
pid_dt = p(1);
m = p(2);
g = p(3);
Kp = p(9);
Ki = p(10);
Kd = p(11);
int_limit = p(12);
T_min = p(13);
T_max = p(14);

z = state(1);
dz = state(2);
e = ref(1) - z;
edot = ref(2) - dz;
e_int = min(max(int_state(1) + pid_dt*e, -int_limit), int_limit);

feedforward = m*g;
T_unsat = Kp*e + Ki*e_int + Kd*edot + feedforward;
T = min(max(T_unsat, T_min), T_max);

ctrl = [T; T_unsat; feedforward; e; e_int; edot];
err = [e; e_int; edot];
int_next = e_int;
end
