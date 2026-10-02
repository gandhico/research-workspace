"""Small continuous-time algebraic Riccati helper.

SciPy is used when available. A NumPy Hamiltonian fallback is included because
the local Codex runtime used for this scaffold may not have SciPy installed.
"""

from __future__ import annotations

import numpy as np


def solve_continuous_are(a: np.ndarray, b: np.ndarray, q: np.ndarray, r: float) -> np.ndarray:
    """Solve A'P + PA - PBR^-1B'P + Q = 0 for the stabilizing P."""

    try:
        from scipy.linalg import solve_continuous_are as scipy_care  # type: ignore

        return np.asarray(scipy_care(a, b, q, np.array([[r]], dtype=float)), dtype=float)
    except Exception:
        return _solve_continuous_are_hamiltonian(a, b, q, r)


def _solve_continuous_are_hamiltonian(
    a: np.ndarray, b: np.ndarray, q: np.ndarray, r: float
) -> np.ndarray:
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    q = np.asarray(q, dtype=float)
    inv_r = 1.0 / float(r)
    h = np.block(
        [
            [a, -b @ b.T * inv_r],
            [-q, -a.T],
        ]
    )
    eigvals, eigvecs = np.linalg.eig(h)
    stable = np.real(eigvals) < 0.0
    if int(np.sum(stable)) != a.shape[0]:
        raise RuntimeError("Hamiltonian CARE fallback could not isolate stable subspace")

    z = eigvecs[:, stable]
    x = z[: a.shape[0], :]
    y = z[a.shape[0] :, :]
    p = np.real(y @ np.linalg.inv(x))
    p = 0.5 * (p + p.T)
    if np.any(np.linalg.eigvalsh(p) <= 0.0):
        raise RuntimeError("CARE solution is not positive definite")
    return p
