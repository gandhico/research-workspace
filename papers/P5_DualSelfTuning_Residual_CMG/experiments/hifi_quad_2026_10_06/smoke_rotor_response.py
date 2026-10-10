"""Tiny exact-off MuJoCo check for the L1 rotor-response variant."""

from __future__ import annotations

import sys
from pathlib import Path

import mujoco
import numpy as np


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from hifi.rotor_response import RotorResponse  # noqa: E402


SCENES = {
    "x2": Path(r"C:\Research\papers\ACC2027_Gate_Residual_Control\third_party\mujoco_menagerie\skydio_x2\scene.xml"),
    "cf2_design": Path(r"C:\Research\papers\ACC2027_Gate_Residual_Control\models\cf2_rotor_design\scene.xml"),
}


def verify_scene(name: str, path: Path) -> None:
    model = mujoco.MjModel.from_xml_path(str(path))
    model.opt.timestep = 0.0005  # study clock; does not modify the XML
    direct = mujoco.MjData(model)
    variant = mujoco.MjData(model)
    f_max = model.actuator_ctrlrange[:, 1].copy()
    rotor = RotorResponse(f_max=f_max, tau_s=np.zeros(4))
    command = np.full(4, float(model.body_mass[1]) * 9.81 / 4)
    assert np.all(command <= f_max)
    for _ in range(200):
        direct.ctrl[:] = command
        variant.ctrl[:] = rotor.step(command, model.opt.timestep)
        assert np.array_equal(direct.ctrl, variant.ctrl)
        mujoco.mj_step(model, direct)
        mujoco.mj_step(model, variant)
        assert np.array_equal(direct.qpos, variant.qpos)
        assert np.array_equal(direct.qvel, variant.qvel)
    print(name, "zero-lag exact L0 parity: 200 steps")

    # Synthetic response test only: no X2/CF2 time constant has been identified.
    tau = 0.03
    rotor = RotorResponse(f_max=f_max, tau_s=np.full(4, tau))
    response = rotor.step(f_max, tau * np.log(2))
    assert np.allclose(response, 0.25 * f_max, rtol=0, atol=1e-14)
    print(name, "synthetic one-time-constant response: quarter force at half speed")

    direct = mujoco.MjData(model)
    lagged = mujoco.MjData(model)
    direct.qpos[2] = lagged.qpos[2] = 1.0
    mujoco.mj_forward(model, direct)
    mujoco.mj_forward(model, lagged)
    rotor = RotorResponse(f_max=f_max, tau_s=np.full(4, tau))
    for _ in range(200):
        direct.ctrl[:] = command
        lagged.ctrl[:] = rotor.step(command, model.opt.timestep)
        mujoco.mj_step(model, direct)
        mujoco.mj_step(model, lagged)
    assert np.all(np.isfinite(lagged.qpos))
    assert lagged.qpos[2] < direct.qpos[2]
    print(name, "synthetic lag changes MuJoCo altitude by", round(float(direct.qpos[2] - lagged.qpos[2]), 6), "m")


if __name__ == "__main__":
    for key, scene in SCENES.items():
        verify_scene(key, scene)
