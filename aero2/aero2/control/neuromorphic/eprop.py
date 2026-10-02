"""Python e-prop training for Adaptive HyperLIF networks.

Replicates the Julia gate-eligibility learning (docs/10 §4;
`01_Adaptive_HyperLIF/04_..._Gate_Eligibility/docs/METHODS.md`) in pure numpy.
Architecture-first: this provides the *trainable* HyperLIF stack so the gate is
learned (not fixed) — the prerequisite for showing HyperLIF's advantage on the
digital twin and hardware. Results-tuning comes later.

Three-factor e-prop (Bellec et al. 2020):  dL/dW_ji ≈ Σ_t L_j(t)·ψ_j(t)·ε_ji(t)
  ε_ji  per-synapse eligibility = membrane-filtered presynaptic trace:
        ε_ji ← decay_j·ε_ji + (1-decay_j)/(1+G_j)·x_i   (≈ ∂v_j/∂W_ji)
  ψ_j   post-synaptic eligibility factor (the HyperLIF gate's own sensitivity ∂r_{t+1}/∂v_t):
        gate_exact : (1-κ)·α·r*(1-r*)        exact gate Jacobian  (parameter-free)
        gate_temp  : (1-κ)·α_elig·g(1-g)     temperature bridge (anneal α_elig: 2 → α)
        surrogate  : α_learn·s(1-s)           heuristic surrogate gradient (bootstrap)
  L_j   learning signal via spatial credit assignment:
        exact : W_next^T routed error    ss : sign(W_next)^T    dfa : B·e_out (fixed random)
Neuron: Adaptive HyperLIF (METHODS Eqs 2-7), exact-linear voltage + gate relaxation.

Validated: readout gradient is exact vs finite differences; gate_exact ψ equals the
finite-difference gate Jacobian; hidden e-prop gradient correlates with BPTT.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from aero2.config import hyperlif as cfg


def _sigmoid(x):
    return 1.0 / (1.0 + np.exp(-np.clip(x, -700.0, 700.0)))


@dataclass
class HyperLIFParams:
    tau: float = cfg.EPROP_TAU
    tau_r: float = cfg.EPROP_TAU_R
    alpha: float = cfg.EPROP_ALPHA
    gamma: float = cfg.EPROP_GAMMA
    g_base: float = cfg.EPROP_G_BASE
    beta: float = cfg.EPROP_BETA
    v_thresh: float = 1.0
    dt: float = cfg.EPROP_DT
    alpha_surrogate: float = cfg.EPROP_ALPHA_SURROGATE


class HyperLIFLayer:
    """Adaptive HyperLIF neurons with trainable input weights + e-prop eligibility.

    After each `forward_step`, `psi` (n_out), `elig` (n_out×n_in) and `elig_b`
    (n_out) hold the factors for the e-prop gradient of THIS step's output r.
    """

    def __init__(self, n_in, n_out, params, bias=0.0, seed=0):
        self.n_in, self.n_out, self.p = n_in, n_out, params
        rng = np.random.default_rng(seed)
        self.W = rng.normal(0.0, 1.0 / np.sqrt(n_in), (n_out, n_in))
        self.b = np.full(n_out, float(bias))
        self.reset()

    def reset(self):
        self.v = np.zeros(self.n_out)
        self.r = np.zeros(self.n_out)
        self._E = np.zeros((self.n_out, self.n_in))   # ∂v_t/∂W eligibility (carried)
        self._Eb = np.zeros(self.n_out)               # ∂v_t/∂b eligibility
        self.psi = np.zeros(self.n_out)
        self.elig = np.zeros((self.n_out, self.n_in))  # snapshot used by this step's grad
        self.elig_b = np.zeros(self.n_out)

    def forward_step(self, x_in, psi_rule="gate_exact", alpha_elig=None):
        p = self.p
        x_in = np.asarray(x_in, dtype=float)
        I = self.W @ x_in + self.b
        kappa = np.exp(-p.dt / p.tau_r)
        eff = p.v_thresh - p.gamma * self.r
        rstar = _sigmoid(p.alpha * (self.v - eff))             # PRE-update v

        if psi_rule == "gate_exact":
            self.psi = (1.0 - kappa) * p.alpha * rstar * (1.0 - rstar)
        elif psi_rule == "gate_temp":
            ae = p.alpha if alpha_elig is None else float(alpha_elig)
            g = _sigmoid(ae * (self.v - eff))
            self.psi = (1.0 - kappa) * ae * g * (1.0 - g)
        else:  # surrogate
            s = _sigmoid(p.alpha_surrogate * (self.v - p.v_thresh))
            self.psi = p.alpha_surrogate * s * (1.0 - s)

        # snapshot eligibility matching this step's psi (∂v_t/∂W from history)
        self.elig = self._E.copy()
        self.elig_b = self._Eb.copy()

        r_new = np.clip(self.r * kappa + rstar * (1.0 - kappa), 0.0, 1.0)
        G = (p.g_base + p.beta * np.abs(I)) * r_new ** 2
        tau_eff = p.tau / (1.0 + G)
        decay = np.exp(-p.dt / tau_eff)
        v_inf = I / (1.0 + G)
        self.v = v_inf + (self.v - v_inf) * decay
        self.r = r_new

        # advance membrane eligibility: ∂v_{t+1}/∂W ≈ decay·∂v_t/∂W + (1-decay)/(1+G)·x
        gain = (1.0 - decay) / (1.0 + G)                       # (n_out,)
        self._E = decay[:, None] * self._E + gain[:, None] * x_in[None, :]
        self._Eb = decay * self._Eb + gain
        return self.r


class EpropSNN:
    """Feedforward Adaptive-HyperLIF hidden stack + linear readout, trained by e-prop."""

    def __init__(self, n_in, hidden=(64,), n_out=1, params=None,
                 psi_rule="gate_exact", credit="exact", hidden_bias=0.0, seed=0):
        self.p = params or HyperLIFParams()
        self.psi_rule, self.credit = psi_rule, credit
        rng = np.random.default_rng(seed)
        sizes = [n_in] + list(hidden)
        self.layers = [HyperLIFLayer(sizes[i], sizes[i + 1], self.p, bias=hidden_bias, seed=seed + i + 1)
                       for i in range(len(hidden))]
        self.W_out = rng.normal(0.0, 1.0 / np.sqrt(sizes[-1]), (n_out, sizes[-1]))
        self.b_out = np.zeros(n_out)
        self.n_out = n_out
        self.B = [rng.normal(0.0, 1.0 / np.sqrt(n_out), (l.n_out, n_out)) for l in self.layers]  # DFA

    def reset(self):
        for l in self.layers:
            l.reset()

    def forward_step(self, x_in, psi_rule=None, alpha_elig=None):
        rule = psi_rule or self.psi_rule
        h = np.asarray(x_in, dtype=float)
        for l in self.layers:
            h = l.forward_step(h, psi_rule=rule, alpha_elig=alpha_elig)
        return self.W_out @ h + self.b_out, h

    def _deltas(self, e):
        """Per-layer d_l = L_l ⊙ ψ_l (the post-factor times the routed error)."""
        if self.credit == "dfa":
            return [(self.B[i] @ e) * self.layers[i].psi for i in range(len(self.layers))]
        fb_out = np.sign(self.W_out) if self.credit == "ss" else self.W_out
        d = [None] * len(self.layers)
        Lsig = fb_out.T @ e
        for li in reversed(range(len(self.layers))):
            d[li] = Lsig * self.layers[li].psi
            fb = np.sign(self.layers[li].W) if self.credit == "ss" else self.layers[li].W
            Lsig = fb.T @ d[li]
        return d

    def gradients(self, U, Y, alpha_elig=None):
        """e-prop gradients (dW_out, db_out, [dW_l], [db_l]) for loss = 0.5 Σ‖y−Y‖²."""
        U = np.asarray(U, dtype=float)
        Y = np.asarray(Y, dtype=float).reshape(len(U), -1)
        self.reset()
        dW = [np.zeros_like(l.W) for l in self.layers]
        db = [np.zeros_like(l.b) for l in self.layers]
        dWo = np.zeros_like(self.W_out)
        dbo = np.zeros_like(self.b_out)
        for t in range(len(U)):
            y, h = self.forward_step(U[t], alpha_elig=alpha_elig)
            e = y - Y[t]
            dWo += np.outer(e, h)
            dbo += e
            for li, d_l in enumerate(self._deltas(e)):
                dW[li] += d_l[:, None] * self.layers[li].elig       # L·ψ·ε   (per-synapse)
                db[li] += d_l * self.layers[li].elig_b
        return dWo, dbo, dW, db

    def loss(self, U, Y):
        U = np.asarray(U, dtype=float)
        Y = np.asarray(Y, dtype=float).reshape(len(U), -1)
        self.reset()
        tot = 0.0
        for t in range(len(U)):
            y, _ = self.forward_step(U[t])
            e = y - Y[t]
            tot += 0.5 * float(e @ e)
        return tot

    def fit(self, U, Y, epochs=60, lr=0.05, clip=1.0, anneal=None, verbose=False):
        U = np.asarray(U, dtype=float)
        Y = np.asarray(Y, dtype=float).reshape(len(U), -1)
        T = len(U)
        losses = []
        for ep in range(epochs):
            ae = None
            if self.psi_rule == "gate_temp" and anneal:
                a0, a1 = anneal
                ae = a0 + (a1 - a0) * ep / max(1, epochs - 1)
            dWo, dbo, dW, db = self.gradients(U, Y, alpha_elig=ae)
            losses.append(2.0 * self.loss(U, Y) / T)            # report mean squared error

            lr_t = lr * 0.5 * (1.0 + np.cos(np.pi * ep / max(1, epochs))) if anneal else lr

            def _step(W, g):
                g = g / T
                nrm = np.linalg.norm(g)
                if nrm > clip:
                    g = g * (clip / nrm)
                return W - lr_t * g

            self.W_out = _step(self.W_out, dWo)
            self.b_out = self.b_out - lr_t * dbo / T
            for li, l in enumerate(self.layers):
                l.W = _step(l.W, dW[li])
                l.b = l.b - lr_t * db[li] / T
            if verbose and ep % max(1, epochs // 5) == 0:
                print(f"  epoch {ep:3d}  mse={losses[-1]:.6f}")
        return losses

    def predict(self, U):
        self.reset()
        U = np.asarray(U, dtype=float)
        out = np.zeros((len(U), self.n_out))
        for t in range(len(U)):
            out[t], _ = self.forward_step(U[t])
        return out


__all__ = ["HyperLIFParams", "HyperLIFLayer", "EpropSNN"]
