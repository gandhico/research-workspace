from __future__ import annotations

from pathlib import Path


HARDWARE = {
    "pendulum": {
        "status": "existing Python Qube interface; adapter validation required on the lab PC",
        "entrypoint": Path(r"C:\Research\pendulum\runners\run_online_qube.py"),
        "safety": "Keep voltage limits and hardware arming in the existing runner.",
    },
    "qcar": {
        "status": "existing PAL hardware runner; camera pipeline is classical HSV, not SNN",
        "entrypoint": Path(r"C:\Research\qcar\01_Code\hardware\qcar2_unified_lane_control_hardware_v1.py"),
        "safety": "The existing --armed interlock remains mandatory.",
    },
    "hover3dof": {
        "status": "QUARC/Simulink interface only; Python HIL adapter not implemented",
        "entrypoint": Path(r"C:\Research\hover3dof\3DOF_Hover"),
        "safety": "Requires encoder/analog-channel map, voltage bounds, and kill switch validation.",
    },
}


def hardware_status(platform_name: str) -> dict:
    value = HARDWARE[platform_name].copy()
    value["entrypoint"] = str(value["entrypoint"])
    value["exists"] = Path(value["entrypoint"]).exists()
    value["armed"] = False
    return value

