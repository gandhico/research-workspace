"""Verify the narrow ideal-axis common-Lyapunov certificates in the 2026-10-06 note."""

from itertools import product

import numpy as np


def check_axis(name: str, omega_n: float, p11: float) -> None:
    p = np.array([[p11, 2.0], [2.0, 1.0]])
    k_p_nom_over_j = 2.0 * omega_n**2
    k_d_nom_over_j = 2.0 * 0.95 * omega_n
    q_margins = []
    for m_p, m_d in product((0.5, 1.5), (1.0, 1.5)):
        a = np.array(
            [[0.0, 0.5], [-m_p * k_p_nom_over_j, -m_d * k_d_nom_over_j]]
        )
        q_margins.append(np.linalg.eigvalsh(-(a.T @ p + p @ a))[0])
    p_margin = np.linalg.eigvalsh(p)[0]
    q_margin = min(q_margins)
    assert p_margin > 0 and q_margin > 0
    print(f"{name}: lambda_min(P)={p_margin:.8f}, min vertex lambda_min(Q)={q_margin:.8f}")


if __name__ == "__main__":
    check_axis("roll/pitch", 4.0, 102.0)
    check_axis("yaw", 3.5, 82.0)
