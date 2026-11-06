"""Read-only model inspection. No controller and no source XML modifications."""
from pathlib import Path
import argparse
import json
import time

import mujoco
import numpy as np

HERE = Path(__file__).resolve().parent
PROJECT = Path(r"C:\Research\papers\ACC2027_Gate_Residual_Control")
MENAGERIE = PROJECT / "third_party/mujoco_menagerie"
MODELS = {
    "omni": (HERE.parent / "omnidrone.xml", "drone"),
    "x2": (MENAGERIE / "skydio_x2/scene.xml", "x2"),
    "cf2": (MENAGERIE / "bitcraze_crazyflie_2/scene.xml", "cf2"),
    "cf2-rotor": (PROJECT / "models/cf2_rotor_design/scene.xml", "cf2"),
}


def load(name):
    path, body = MODELS[name]
    model = mujoco.MjModel.from_xml_path(str(path))
    data = mujoco.MjData(model)
    mujoco.mj_forward(model, data)
    return model, data, model.body(body).id


def inspect(name):
    model, data, bid = load(name)
    rotation = data.xmat[bid].reshape(3, 3)
    com = data.xipos[bid]
    columns, actuators = [], []
    # All four supported models have site transmissions, fixed unit gain,
    # no activation dynamics, and a single free rigid body.
    for aid in range(model.nu):
        assert model.actuator_trntype[aid] == mujoco.mjtTrn.mjTRN_SITE
        assert model.actuator_gaintype[aid] == mujoco.mjtGain.mjGAIN_FIXED
        assert model.actuator_gainprm[aid, 0] == 1
        assert model.actuator_dyntype[aid] == mujoco.mjtDyn.mjDYN_NONE
        sid = int(model.actuator_trnid[aid, 0])
        site_rotation = data.site_xmat[sid].reshape(3, 3)
        force = site_rotation @ model.actuator_gear[aid, :3]
        torque = np.cross(data.site_xpos[sid] - com, force)
        torque += site_rotation @ model.actuator_gear[aid, 3:]
        columns.append(np.r_[rotation.T @ force, rotation.T @ torque])
        actuators.append({
            "name": model.actuator(aid).name,
            "site": model.site(sid).name,
            "position_body_m": model.site_pos[sid].tolist(),
            "force_body_per_control": (rotation.T @ force).tolist(),
            "gear_site": model.actuator_gear[aid].tolist(),
            "control_range": model.actuator_ctrlrange[aid].tolist(),
            "control_limited": bool(model.actuator_ctrllimited[aid]),
        })
    matrix = np.column_stack(columns)
    target = np.r_[rotation.T @ (-model.body_mass.sum() * model.opt.gravity), np.zeros(3)]
    hover = np.linalg.lstsq(matrix, target, rcond=None)[0]
    residual = matrix @ hover - target
    feasible = bool(np.all(hover >= model.actuator_ctrlrange[:, 0] - 1e-9)
                    and np.all(hover <= model.actuator_ctrlrange[:, 1] + 1e-9)
                    and np.linalg.norm(residual) < 1e-8)
    # Verify wrench prediction against MuJoCo's acceleration at an airborne pose.
    # Translation alone preserves the initial attitude and allocation matrix.
    data.qpos[2] += 2.0
    data.ctrl[:] = hover
    mujoco.mj_forward(model, data)
    result = {
        "model": name, "xml": str(MODELS[name][0]), "mujoco_version": mujoco.__version__,
        "nq": model.nq, "nv": model.nv, "nu": model.nu,
        "mass_kg": float(model.body_mass.sum()),
        "com_body_m": model.body_ipos[bid].tolist(),
        "principal_inertia_kg_m2": model.body_inertia[bid].tolist(),
        "inertial_frame_quaternion_wxyz": model.body_iquat[bid].tolist(),
        "initial_qpos": model.qpos0.tolist(),
        "timestep_s": model.opt.timestep,
        "integrator": mujoco.mjtIntegrator(model.opt.integrator).name,
        "density": model.opt.density, "viscosity": model.opt.viscosity,
        "sensors": [model.sensor(i).name for i in range(model.nsensor)],
        "actuators": actuators,
        "wrench_matrix_body_COM_rows_Fx_Fy_Fz_Mx_My_Mz": matrix.tolist(),
        "wrench_rank": int(np.linalg.matrix_rank(matrix)),
        "force_rank": int(np.linalg.matrix_rank(matrix[:3])),
        "initial_attitude_hover_controls": hover.tolist(),
        "hover_feasible": feasible,
        "hover_wrench_residual": residual.tolist(),
        "airborne_hover_qacc": data.qacc.tolist(),
        "airborne_contacts": data.ncon,
    }
    if name == "omni":
        gid = model.geom("drone_geom").id
        mid = int(model.geom_dataid[gid])
        start, count = model.mesh_vertadr[mid], model.mesh_vertnum[mid]
        vertices = model.mesh_vert[start:start + count]
        world_vertices = vertices @ data.geom_xmat[gid].reshape(3, 3).T + data.geom_xpos[gid]
        body_vertices = (world_vertices - data.xpos[bid]) @ data.xmat[bid].reshape(3, 3)
        result["mesh_body_bounds_m"] = [body_vertices.min(0).tolist(), body_vertices.max(0).tolist()]
    return result


def camera(model, data, bid):
    cam = mujoco.MjvCamera()
    mujoco.mjv_defaultCamera(cam)
    cam.lookat[:] = data.xipos[bid]
    cam.distance = 1.65 if model.body_mass.sum() > 0.1 else 0.32
    cam.azimuth, cam.elevation = 135, -22
    return cam


def options():
    opt = mujoco.MjvOption()
    opt.sitegroup[:] = 1
    opt.frame = mujoco.mjtFrame.mjFRAME_SITE
    opt.label = mujoco.mjtLabel.mjLABEL_SITE
    return opt


def configure_visuals(model):
    length = 0.06 if model.body_mass.sum() > 0.1 else 0.012
    model.vis.scale.framelength = length / model.stat.meansize
    model.vis.scale.framewidth = length * 0.035 / model.stat.meansize


def view(name, simulate):
    import mujoco.viewer
    model, data, bid = load(name)
    configure_visuals(model)
    if simulate:
        print("Native simulation: Space pauses, Backspace resets. Zero control is not hover.", flush=True)
        mujoco.viewer.launch(model, data)
        return
    print("DESIGN VIEW: physics is held at the XML initial pose. Close the window to exit.", flush=True)
    print("Site frames: red=X, green=Y, blue=Z. Use --simulate for native physics controls.", flush=True)
    with mujoco.viewer.launch_passive(model, data) as viewer:
        with viewer.lock():
            cam = camera(model, data, bid)
            viewer.cam.lookat[:] = cam.lookat
            viewer.cam.distance = cam.distance
            viewer.cam.azimuth, viewer.cam.elevation = cam.azimuth, cam.elevation
            viewer.opt.sitegroup[:] = 1
            viewer.opt.frame = mujoco.mjtFrame.mjFRAME_SITE
            viewer.opt.label = mujoco.mjtLabel.mjLABEL_SITE
        while viewer.is_running():
            viewer.sync()
            time.sleep(1 / 60)


def render(name):
    from PIL import Image
    model, data, bid = load(name)
    configure_visuals(model)
    model.vis.global_.offwidth, model.vis.global_.offheight = 1200, 900
    cam, opt = camera(model, data, bid), options()
    output = HERE / "output"
    output.mkdir(exist_ok=True)
    with mujoco.Renderer(model, height=900, width=1200) as renderer:
        renderer.update_scene(data, camera=cam, scene_option=opt)
        path = output / f"{name}_design.png"
        Image.fromarray(renderer.render()).save(path)
        print(path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model", choices=[*MODELS, "all"], default="all", nargs="?")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--view", action="store_true", help="Frozen design viewer with labeled site axes")
    mode.add_argument("--simulate", action="store_true", help="Native MuJoCo simulation; no controller")
    mode.add_argument("--render", action="store_true", help="Save labeled PNGs")
    args = parser.parse_args()
    if args.view or args.simulate:
        if args.model == "all":
            parser.error("Choose a single model for an interactive window")
        view(args.model, args.simulate)
    elif args.render:
        for name in MODELS if args.model == "all" else [args.model]:
            render(name)
    else:
        results = [inspect(name) for name in MODELS] if args.model == "all" else [inspect(args.model)]
        output = HERE / "output"
        output.mkdir(exist_ok=True)
        (output / "model_audit.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
        for r in results:
            print(f"{r['model']}: mass={r['mass_kg']:.6g} kg, DOFs={r['nv']}, actuators={r['nu']}, wrench rank={r['wrench_rank']}, dt={r['timestep_s']}")
            print("  COM:", np.round(r["com_body_m"], 7), "inertia:", np.round(r["principal_inertia_kg_m2"], 8))
            print("  Initial-attitude hover:", np.round(r["initial_attitude_hover_controls"], 6), "feasible:", r["hover_feasible"])
            print("  Airborne hover acceleration:", np.round(r["airborne_hover_qacc"], 9))
        print(output / "model_audit.json")
