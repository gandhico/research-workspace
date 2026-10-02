"""Limbic-system-inspired controller from the DILISIC paper."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .riccati import solve_continuous_are


@dataclass
class LISICParameters:
    """Tuning parameters for the fourth-order LISIC controller."""

    lambdas: tuple[float, float, float] = (125.0, 75.0, 15.0)
    k: float = 20.0
    q: float = 0.2
    q_i: float = 10.0
    r: float = 0.0018375
    rho: float = 0.035
    centers: np.ndarray = field(default_factory=lambda: np.linspace(-45.0, 45.0, 45))
    sigma: float = 45.0
    alpha_f: float = 1.0e-4
    beta_f: float = 1.0e-4
    alpha_h: float = 1.0e-4
    beta_h: float = 1.0e-4
    max_v_f: float = 1.0e5
    max_w_f: float = 1.0e5
    max_v_h: float = 1.0e5
    max_w_h: float = 1.0e5
    initial_h_hat: float = 1.2257456554640425
    h_hat_floor: float = 1.0e-3
    clip_basis_input: bool = True
    control_limit: float | None = 5.0e4

    def __post_init__(self) -> None:
        if 2.0 * self.rho**2 <= self.r:
            raise ValueError("LISIC requires 2*rho^2 > r for the robust Riccati term")
        self.centers = np.asarray(self.centers, dtype=float)


@dataclass
class LISICController:
    """Adaptive LISIC controller for a scalar fourth-order affine plant."""

    params: LISICParameters = field(default_factory=LISICParameters)

    def __post_init__(self) -> None:
        p = len(self.params.centers)
        self.v_f = np.zeros(p + 1)
        self.w_f = np.zeros(p)
        self.v_h = np.zeros(p + 1)
        self.w_h = np.zeros(p)
        self.xi = 0.0
        self.p_e = self._solve_robust_riccati()
        # Seed h_hat near the flexible-arm inverse gain used in the paper.
        # This is a reproduction aid; hardware runs should identify/calibrate it.
        self.v_h[-1] = self.params.initial_h_hat

    def _solve_robust_riccati(self) -> np.ndarray:
        p = self.params
        a_e = np.array([[-p.k, 0.0], [1.0, 0.0]], dtype=float)
        b_e = np.array([[1.0], [0.0]], dtype=float)
        q_e = np.diag([p.q, p.q_i])
        robust_r = p.rho**2 * p.r / (2.0 * p.rho**2 - p.r)
        return solve_continuous_are(a_e, b_e, q_e, robust_r)

    def basis(self, s: float) -> tuple[np.ndarray, np.ndarray]:
        p = self.params
        basis_s = float(np.clip(s, p.centers[0], p.centers[-1])) if p.clip_basis_input else s
        phi = np.exp(-((basis_s - p.centers) ** 2) / (p.sigma**2))
        phi_a = np.concatenate([phi, [float(np.max(phi))]])
        return phi, phi_a

    def estimates(self, s: float) -> tuple[float, float, np.ndarray, np.ndarray]:
        phi, phi_a = self.basis(s)
        f_hat = float(self.v_f @ phi_a - self.w_f @ phi)
        h_hat = float(self.v_h @ phi_a - self.w_h @ phi)
        h_hat = max(h_hat, self.params.h_hat_floor)
        return f_hat, h_hat, phi, phi_a

    def tracking_surface(self, x: np.ndarray, x_ref: np.ndarray) -> tuple[float, float]:
        """Return s and q_a for n=4 using e = x - x_ref."""

        e = np.asarray(x, dtype=float) - np.asarray(x_ref[:4], dtype=float)
        lambda_1, lambda_2, lambda_3 = self.params.lambdas
        s = e[3] + lambda_3 * e[2] + lambda_2 * e[1] + lambda_1 * e[0]
        q_a = -x_ref[4] + lambda_3 * e[3] + lambda_2 * e[2] + lambda_1 * e[1]
        return float(s), float(q_a)

    def robust_input(self, s: float) -> float:
        se = np.array([s, self.xi], dtype=float)
        b_e = np.array([1.0, 0.0], dtype=float)
        return -float(b_e @ self.p_e @ se) / self.params.r

    def control(self, x: np.ndarray, x_ref: np.ndarray) -> dict[str, float]:
        s, q_a = self.tracking_surface(x, x_ref)
        f_hat, h_hat, _, _ = self.estimates(s)
        u_r = self.robust_input(s)
        u = -h_hat * (f_hat + q_a + self.params.k * s - u_r)
        if self.params.control_limit is not None:
            u = float(np.clip(u, -self.params.control_limit, self.params.control_limit))
        return {
            "u": float(u),
            "s": s,
            "q_a": q_a,
            "u_r": u_r,
            "f_hat": f_hat,
            "h_hat": h_hat,
        }

    def update(self, dt: float, s: float, u_h: float) -> None:
        """Euler update for Eq. 11-style projected weight adaptation."""

        _, _, phi, phi_a = self.estimates(s)
        se = np.array([s, self.xi], dtype=float)
        bpe = float(np.array([1.0, 0.0]) @ self.p_e @ se)
        p = self.params

        self.v_f += dt * _projected_derivative(
            self.v_f, p.alpha_f * phi_a * max(bpe, 0.0), p.max_v_f
        )
        self.w_f += dt * _projected_derivative(
            self.w_f, -p.beta_f * phi * bpe, p.max_w_f
        )
        self.v_h += dt * _projected_derivative(
            self.v_h, p.alpha_h * phi_a * max(bpe * u_h, 0.0), p.max_v_h
        )
        self.w_h += dt * _projected_derivative(
            self.w_h, -p.beta_h * phi * bpe * u_h, p.max_w_h
        )

        self.v_f = _clip_norm(self.v_f, p.max_v_f)
        self.w_f = _clip_norm(self.w_f, p.max_w_f)
        self.v_h = _clip_norm(self.v_h, p.max_v_h)
        self.w_h = _clip_norm(self.w_h, p.max_w_h)
        self.xi += dt * s

    def weight_norms(self) -> dict[str, float]:
        return {
            "v_f": float(np.linalg.norm(self.v_f)),
            "w_f": float(np.linalg.norm(self.w_f)),
            "v_h": float(np.linalg.norm(self.v_h)),
            "w_h": float(np.linalg.norm(self.w_h)),
        }


def _projected_derivative(weights: np.ndarray, derivative: np.ndarray, bound: float) -> np.ndarray:
    norm = float(np.linalg.norm(weights))
    if norm < bound or bound <= 0.0:
        return derivative
    radial = float(weights @ derivative)
    if radial <= 0.0:
        return derivative
    return derivative - (radial / max(norm**2, 1.0e-12)) * weights


def _clip_norm(weights: np.ndarray, bound: float) -> np.ndarray:
    norm = float(np.linalg.norm(weights))
    if bound > 0.0 and norm > bound:
        return weights * (bound / norm)
    return weights
