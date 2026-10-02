# Mathematics and parity contract

For current (J_k), voltage (v_k), and reset gate (r_k), define

\[
\theta_{\mathrm{eff},k}=\theta_v-\gamma r_k,\qquad
r_\infty=\sigma\!\left(\alpha(v_k-\theta_{\mathrm{eff},k})\right).
\]

The implemented gate map is

\[
r_{k+1}=\operatorname{clip}_{[0,1]}\left[
r_\infty+(r_k-r_\infty)e^{-\Delta t/\tau_r}\right].
\]

With (G_{k+1}=g_k r_{k+1}^2), where (g_k=g_r) for HyperLIF and
(g_k=g_0+g_1|J_k|) for Adaptive HyperLIF, freeze (J_k,G_{k+1}) over one
sample. Then

\[
\lambda_k=\tau_m^{-1}+G_{k+1},\qquad
b_k=v_{\rm rest}/\tau_m+J_k/\tau_m+G_{k+1}v_{\rm reset,eff},
\]

\[
v_{k+1}=v_k e^{-\lambda_k\Delta t}
+\frac{b_k}{\lambda_k}\left(1-e^{-\lambda_k\Delta t}\right).
\]

This is an exact exponential step for the frozen scalar voltage ODE and an
operator-split approximation of the coupled ((v,r)) system. Calling it the
"exact HyperLIF ODE solution" would be mathematically too strong.

Two event observables are supported and must be distinguished:

\[
o_{k+1}=\mathbf 1[v_{k+1}\geq\theta_e],\qquad
z_{k+1}=\mathbf 1[v_k<\theta_e\leq v_{k+1}].
\]

The published snnTorch/APEX-v2 architecture harness and its Julia parity
fixtures use threshold occupancy `o` (`event_mode=:occupancy`). The
standalone/Nengo reference uses upward crossings `z`
(`event_mode=:upcrossing`). Occupancy can mark many consecutive samples for a
single threshold entry; therefore historical occupancy totals are not physical
spike counts and cannot by themselves establish event-driven energy savings.

For the recurrent architecture,

\[
J_k=W_{\rm in}x_k+b_{\rm in}+W_{\rm rec}z_{k-1}.
\]

For the offline delay architecture,

\[
J_{h,k}=\sum_{\ell=1}^{L}d_{h,\ell}\,\bar J_{h,k+\ell-c},
\quad c=\lceil L/2\rceil,
\]

which reproduces symmetric PyTorch padding but is noncausal when
(\ell>c). The online form replaces the index by (k-(\ell-1)).

The existing CUDA APEX-v2 shared-weight fixtures already pass for dense,
recurrent, and centered-delay HyperLIF/Adaptive-HyperLIF configurations at
feature tolerance (10^{-4}) and logit tolerance (10^{-3}). This portable
package adds deterministic CPU tests and explicitly exposes the causal/offline
distinction. Gradient parity remains future work.
