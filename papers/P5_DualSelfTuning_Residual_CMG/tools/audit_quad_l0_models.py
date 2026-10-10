"""Small reproducible audit of the two unchanged quadrotor MuJoCo L0 models."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import mujoco


ACC = Path(r"C:\Research\papers\ACC2027_Gate_Residual_Control")
OUT = Path(__file__).resolve().parents[1] / "docs" / "TWIN_L0_AUDIT_2026-10-06.json"
MODELS = {
    "x2": ACC / "third_party" / "mujoco_menagerie" / "skydio_x2" / "scene.xml",
    "cf2_design": ACC / "models" / "cf2_rotor_design" / "scene.xml",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit(name: str, scene: Path) -> dict:
    model = mujoco.MjModel.from_xml_path(str(scene))
    body = 1  # each scene contains one free quadrotor body
    assert model.nu == 4 and model.nbody == 2
    rotor_sites = [mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, f"thrust{i}") for i in range(1, 5)]
    assert all(site >= 0 for site in rotor_sites)
    sites = [model.site_pos[site].tolist() for site in rotor_sites]
    gear = model.actuator_gear[:, :6].tolist()
    ctrl = model.actuator_ctrlrange.tolist()
    mass = float(model.body_mass[body])
    max_thrust = sum(float(item[1]) for item in ctrl)
    return {
        "name": name,
        "scene_path": str(scene),
        "scene_sha256": sha256(scene),
        "body_xml_sha256": sha256(scene.parent / ("x2.xml" if name == "x2" else "cf2_rotor.xml")),
        "body_mass_kg": mass,
        "body_inertia_diagonal_kg_m2": model.body_inertia[body].tolist(),
        "xml_timestep_s": float(model.opt.timestep),
        "rotor_site_positions_body_m": sites,
        "actuator_gear": gear,
        "rotor_force_ctrl_ranges_N": ctrl,
        "hover_force_per_rotor_N": mass * 9.81 / 4,
        "static_total_thrust_to_weight": max_thrust / (mass * 9.81),
        "fidelity": "L0 ideal instantaneous force design model; no motor/battery/estimator calibration asserted",
    }


if __name__ == "__main__":
    result = {
        "date": "2026-10-06",
        "models": {name: audit(name, path) for name, path in MODELS.items()},
        "cf2_authority_variants": {
            "stock_xml": 1.0,
            "P5_study": 1.5,
            "racing_study": 1.7,
            "interpretation": "declared force-limit design multipliers, not measured hardware capability",
        },
        "warning": "This file inventories compiled L0 models; it does not validate high-fidelity digital twins.",
    }
    OUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(OUT)
    for name, item in result["models"].items():
        print(name, "mass", item["body_mass_kg"], "T/W", round(item["static_total_thrust_to_weight"], 3))
