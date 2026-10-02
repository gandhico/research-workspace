# Predicted closed-loop bias of the quadrature dither estimate (pre-run)

Closed-loop bias of the v3/v4 quadrature lock-in estimate (written before any 6-DOF pilot run).

Small-angle axis model at the dither frequency: J th'' + k_w th' + (k_q/2) th = d, since e_q ~ th/2.
With d = A sin wt and z_c = LPF(omega cos wt) -> A Im H(jw)/2, H = jw / (k - J w^2 + j k_w w):
    s_quad = -2 j w z_c / A = j w^2 (J w^2 - k) / ((k - J w^2)^2 + (k_w w)^2)     (k = k_q/2)
Open loop (k = k_w = 0) gives j/J. The known-controller estimate inverts the complex response:
    1/H = k_w + j (J w^2 - k)/w   ->   J = (w Im(1/H) + k) / w^2


| platform | loop | true j/J (x,y,z) | predicted quadrature s_hat (x,y,z) | v4 target m=1/s_hat | correct m=J/j |
|---|---|---|---|---|---|
| x2 | quat (wn 4,4,3.5) | 1.66, 1.44, 0.42 | 1.59, 1.41, 0.42 | 0.63, 0.71, 2.38 | 0.60, 0.70, 2.38 |
| x2 | 6dof tuned (wn 20,20,17.5) | 1.66, 1.44, 0.42 | 0.70, 0.90, 0.42 | 1.42, 1.11, 2.41 | 0.60, 0.70, 2.38 |
| cf2-rotor | quat (wn 4,4,3.5) | 1.00, 1.00, 1.00 | 0.99, 0.99, 1.00 | 1.01, 1.01, 1.00 | 1.00, 1.00, 1.00 |
| cf2-rotor | 6dof tuned (wn 24,24,20.4) | 1.00, 1.00, 1.00 | 0.62, 0.73, 0.85 | 1.61, 1.37, 1.18 | 1.00, 1.00, 1.00 |
