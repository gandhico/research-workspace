# Why shunting conductance can be large yet its modulation invisible to the decoder

This derivation distinguishes the total conductance from the switch chi that adds input dependence. It is not a new flight-stability theorem.

## 1. The canonical high-gate branch is persistent

For normalized nonnegative current, zero rest/reversal potentials, and nonnegative initial membrane state, the implemented membrane step preserves v >= 0. With gamma=2 and v_th=1, if r >= 1/2 then v - 1 + 2r >= 0 and the gate target b >= 1/2. The gate update is a convex combination of r and b because h/tau_r=0.1. Thus r >= 1/2 is forward invariant. More strongly, r >= 0.9 implies b >= sigmoid(40) > 0.9 and that interval is also invariant. The clipped logistic argument does not change these inequalities.

Once r is near one, positive threshold feedback supports the high-gate branch even when shunting conductance lowers the voltage. This explains persistent activity without claiming every unit reaches that branch in every mission.

At r approximately one and constant current I, the membrane quasi-equilibrium is

    v* = I / [1 + tau (g0 + chi g1 I)].

For tau=.05, g0=120 and g1=30, this is I/(7+1.5 chi I). Conductance is therefore NOT negligible relative to the leak. Yet gamma=2 gives gate argument approximately 50(v*+1), which lies deep in the upper sigmoid regime. Changes in v can become nearly invisible in r and a. G=1e5 additionally clips a at r=1e-5, far below the high-gate branch.

## 2. A constant activity basis has an exact reduced decoder recursion

Suppose a_k=a_bar is constant over an interval, and elementwise decoder projection is inactive. Define z_k=W_k a_bar and s_k=clip(z_k,-1,1). Multiplying the actual direct PES update by a_bar gives exactly

    z_(k+1) = (1-lambda_W) z_k
              + eta ||a_bar||^2 [y*_k - clip(z_k,-1,1)].

If readout clipping is also inactive, this becomes a first-order target filter:

    z_(k+1) = [1-lambda_W-eta||a_bar||^2] z_k
              + eta||a_bar||^2 y*_k.

For six fully saturated activities, ||a_bar||^2=6; the pole is .995199, the equivalent time constant is -h/log(.995199) approximately .104 s, and the DC gain is .0048/.004801 approximately .999792. This is an exact discrete direct-backend reduction under the stated conditions; it is not a global equivalence for transient/varying features, active weight projection, or the delayed Nengo teaching graph.

This also explains why constant saturated activity can still produce time-varying residuals: the decoder is driven by a time-varying error target. It does not prove learned plant inversion, a neuron-specific advantage, or parameter convergence.

## 3. What varying G does and does not isolate

Before activity clipping, a=G r. Holding eta fixed scales the instantaneous learning contribution to the same-feature decoded output as eta G^2 ||r||^2. Once clipped, that quadratic relation no longer applies. Hence a gain sweep with fixed eta combines representation/clipping and effective adaptation speed. G does not directly change the intrinsic differential equations, but it can change their input trajectory through the closed loop.

Weakening gamma changes the intrinsic feedback and may prevent persistence of the high-gate branch. Tests with gamma=0 or .5 are NEW structural/parameter regimes, not replication of the frozen gamma=2 architecture. Open-loop state sensitivity and closed-loop tracking benefit must be evaluated separately.
