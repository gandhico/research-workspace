"""Regression check for the Omnicopter rotor frames and actuator directions."""
from pathlib import Path

import mujoco
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
MODELS = (
    ROOT / "omnidrone.xml",
    ROOT / "mjmodel.xml",
)

# Body-frame axes derived from the diagonal beam directions and the planar
# square-beam face normals present in Omnidrone.stl.
C = 1.0 / np.sqrt(3.0)
A = (3.0 + np.sqrt(3.0)) / 6.0
B = (3.0 - np.sqrt(3.0)) / 6.0
EXPECTED_Z = {
    1: (-C, -B, A),
    2: (C, -A, -B),      # -90 degrees about local X
    3: (C, A, B),        # 180 degrees about local X
    4: (-C, B, -A),      # +90 degrees about local X
    5: (-C, B, -A),      # -90 degrees about local X
    6: (C, A, B),        # 180 degrees about local X
    7: (C, -A, -B),      # +90 degrees about local X
    8: (-C, -B, A),
}


def check(path: Path) -> None:
    model = mujoco.MjModel.from_xml_path(str(path))
    data = mujoco.MjData(model)
    mujoco.mj_forward(model, data)
    body_id = model.body("drone").id
    world_from_body = data.xmat[body_id].reshape(3, 3)
    columns = []

    for number in range(1, 9):
        site_id = model.site(f"rotor_{number}").id
        world_from_site = data.site_xmat[site_id].reshape(3, 3)
        body_from_site = world_from_body.T @ world_from_site
        beam = model.site_pos[site_id] / np.linalg.norm(model.site_pos[site_id])
        expected_z = np.asarray(EXPECTED_Z[number])

        np.testing.assert_allclose(body_from_site[:, 0], beam, atol=2e-9)
        np.testing.assert_allclose(body_from_site[:, 2], expected_z, atol=2e-9)
        np.testing.assert_allclose(body_from_site.T @ body_from_site, np.eye(3), atol=2e-9)
        np.testing.assert_allclose(np.linalg.det(body_from_site), 1.0, atol=2e-9)

        actuator_id = model.actuator(f"thrust_{number}").id
        np.testing.assert_allclose(model.actuator_gear[actuator_id, :3], (0, 0, 1))
        force = body_from_site @ model.actuator_gear[actuator_id, :3]
        arm = model.site_pos[site_id] - model.body_ipos[body_id]
        torque = np.cross(arm, force) + body_from_site @ model.actuator_gear[actuator_id, 3:]
        columns.append(np.r_[force, torque])

    matrix = np.column_stack(columns)
    target = np.r_[-model.body_mass.sum() * world_from_body.T @ model.opt.gravity, np.zeros(3)]
    hover = np.linalg.lstsq(matrix, target, rcond=None)[0]
    bounded = np.all(hover >= model.actuator_ctrlrange[:, 0]) and np.all(
        hover <= model.actuator_ctrlrange[:, 1]
    )
    print(path)
    print("  rotor frame geometry: PASS")
    print(f"  wrench matrix rank: {np.linalg.matrix_rank(matrix)}")
    print(f"  unconstrained initial-pose hover controls [N]: {np.round(hover, 6)}")
    print(f"  inside configured actuator bounds: {bool(bounded)}")


if __name__ == "__main__":
    for model_path in MODELS:
        check(model_path)
