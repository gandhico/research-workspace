"""
build_scene.py  --  compose the heterogeneous race world with MjSpec.

World  = ground + 7 gates (track.py) + start podium
Fleet  = Skydio X2 (MuJoCo Menagerie), CF2 rotor-level design model (ACC 2027 project),
         Omnicopter (C:\\Research\\omnicopter model), coaxial Y6 (y6_hexa project)
Each vehicle MJCF is attached UNCHANGED under a name prefix ("x2/", "cf2/", "omni/", "y6/");
only collision bits are edited so vehicles hit gates and ground but not each other
("ghost" time-trial: aerodynamic and contact interaction between drones is out of scope).

Every vehicle gets the same two onboard cameras, mounted on its body:
  <p>fpv  : forward RGB camera, 90 deg FOV, 15 deg up-tilt (racing-FPV style)
  <p>dvs  : same optical centre, 346x260 DAVIS-like geometry (event emulator input)

    python build_scene.py            -> models/race_world.xml (+ prints fleet table)
"""
import pathlib
import numpy as np
import mujoco

import track

HERE = pathlib.Path(__file__).resolve().parent
VEH = HERE / "models" / "vehicles"

FLEET = {
    #  prefix : (file, root body, start offset on the podium [m], camera mount [m] in body frame)
    "x2":   (VEH / "skydio_x2" / "x2.xml",               "x2",    (0.0,  1.5), (0.20, 0.0, 0.03)),
    "cf2":  (VEH / "cf2_rotor" / "cf2_rotor.xml",        "cf2",   (0.0,  0.5), (0.04, 0.0, 0.01)),
    "omni": (VEH / "omnicopter" / "omnidrone.xml",       "drone", (0.0, -0.5), (0.0, 0.0, 0.0)),   # set below
    "y6":   (VEH / "y6_coaxial" / "y6_coaxial.xml",      "y6",    (0.0, -1.5), (0.18, 0.0, -0.02)),
}
VEHICLE_CONTYPE, VEHICLE_CONAFF = 2, 1      # vehicle-vehicle: no contact; vehicle-world: contact
WORLD_CONTYPE, WORLD_CONAFF = 1, 2
CF2_AUTHORITY = 1.7   # CF2 per-rotor ceiling x1.7 (0.149 N): declared design assumption, see README


def _cam_axes(tilt_deg):
    """MuJoCo camera looks along -z_cam, image-up +y_cam.  Forward (+x body), tilted up."""
    a = np.radians(tilt_deg)
    fwd = np.array([np.cos(a), 0, np.sin(a)])
    up = np.array([-np.sin(a), 0, np.cos(a)])
    xc = np.cross(up, -fwd)            # x_cam = y_cam x z_cam, z_cam = -fwd
    return np.concatenate([xc, up])


def add_gate(spec, name, c, yaw_deg, mat_a, mat_b):
    """Square frame of 4 bars, alternating dark/bright segments (strong edges for the DVS)."""
    b = spec.worldbody.add_body(name=name, pos=list(c))
    q = np.zeros(4); mujoco.mju_axisAngle2Quat(q, [0, 0, 1], np.radians(yaw_deg)); b.quat = q
    h, w, d = track.GATE_INNER/2, track.GATE_BORDER, track.GATE_DEPTH/2
    seg = 5
    for side, (axis, off) in enumerate([("y", h + w/2), ("y", -(h + w/2)), ("z", h + w/2), ("z", -(h + w/2))]):
        L = 2*h + 2*w
        for k in range(seg):
            t = -L/2 + (k + 0.5)*L/seg
            if axis == "y":      # horizontal bars (top/bottom): along gate-local y
                pos, size = [0, t, off], [d, L/seg/2, w/2]
            else:                # vertical bars (left/right): along gate-local z
                pos, size = [0, off, t], [d, w/2, L/seg/2]
            g = b.add_geom(type=mujoco.mjtGeom.mjGEOM_BOX, pos=pos, size=size,
                           material=(mat_a if (k + side) % 2 == 0 else mat_b))
            g.contype, g.conaffinity = WORLD_CONTYPE, WORLD_CONAFF
    # legs to the ground (visual) and a translucent pass-plane marker (no collision)
    z0 = c[2] - h - w
    for sy in (-1, 1):
        leg = b.add_geom(type=mujoco.mjtGeom.mjGEOM_CYLINDER, fromto=[0, sy*(h + w/2), -z0 + 0.0, 0, sy*(h + w/2), -h - w],
                         size=[0.04, 0, 0], rgba=[0.3, 0.3, 0.32, 1])
        leg.contype, leg.conaffinity = WORLD_CONTYPE, WORLD_CONAFF
    return b


def build(out=HERE / "models" / "race_world.xml", fleet=tuple(FLEET)):
    spec = mujoco.MjSpec()
    spec.modelname = "neuromorphic_heterogeneous_race"
    spec.option.timestep = 0.002
    spec.compiler.degree = False
    spec.visual.global_.offwidth, spec.visual.global_.offheight = 1280, 720
    spec.visual.map.znear, spec.visual.map.zfar = 0.005, 200.0
    spec.visual.map.shadowclip = 40
    spec.visual.quality.shadowsize = 4096

    spec.add_texture(name="sky", type=mujoco.mjtTexture.mjTEXTURE_SKYBOX, builtin=mujoco.mjtBuiltin.mjBUILTIN_GRADIENT,
                     rgb1=[0.55, 0.70, 0.90], rgb2=[0.95, 0.97, 1.0], width=512, height=512)
    spec.add_texture(name="floor", type=mujoco.mjtTexture.mjTEXTURE_2D, builtin=mujoco.mjtBuiltin.mjBUILTIN_CHECKER,
                     rgb1=[0.30, 0.32, 0.34], rgb2=[0.40, 0.42, 0.44], width=512, height=512)
    fl = spec.add_material(name="floor", texrepeat=[30, 30], reflectance=0.05)
    fl.textures[mujoco.mjtTextureRole.mjTEXROLE_RGB] = "floor"
    spec.add_material(name="gate_a", rgba=[0.95, 0.35, 0.05, 1])     # orange
    spec.add_material(name="gate_b", rgba=[0.06, 0.06, 0.08, 1])     # black
    spec.add_material(name="pad", rgba=[0.55, 0.07, 0.16, 1])

    wb = spec.worldbody
    spec.worldbody.add_light(name="sun", pos=[0, 0, 30], dir=[0.3, 0.2, -1], type=mujoco.mjtLightType.mjLIGHT_DIRECTIONAL,
                             castshadow=True, diffuse=[0.8, 0.8, 0.8])
    g = wb.add_geom(name="ground", type=mujoco.mjtGeom.mjGEOM_PLANE, size=[40, 40, 0.1], material="floor")
    g.contype, g.conaffinity = WORLD_CONTYPE, WORLD_CONAFF
    p = wb.add_geom(name="podium", type=mujoco.mjtGeom.mjGEOM_BOX, pos=list(track.START + [0, 0, 0.025]),
                    size=[0.9, 2.4, 0.025], material="pad")
    p.contype, p.conaffinity = WORLD_CONTYPE, WORLD_CONAFF
    for i, (name, c, yaw) in enumerate(track.GATES):
        add_gate(spec, f"gate{i+1}", c, yaw, "gate_a", "gate_b")
    # spectator cameras
    wb.add_camera(name="overview", pos=[-22, -24, 16], mode=mujoco.mjtCamLight.mjCAMLIGHT_TARGETBODYCOM,
                  targetbody="gate4", fovy=55)
    wb.add_camera(name="splits_cam", pos=[0, -4, 4.5], mode=mujoco.mjtCamLight.mjCAMLIGHT_TARGETBODY,
                  targetbody="gate4", fovy=60)

    for pre in fleet:
        path, root, (dx, dy), mount = FLEET[pre]
        child = mujoco.MjSpec.from_file(str(path))
        if pre == "cf2":                                   # authority study scale (declared)
            for a in child.actuators:
                a.ctrlrange = [0.0, 0.0875*CF2_AUTHORITY]
        for gm in child.geoms:                             # ghost fleet: no vehicle-vehicle contacts
            if gm.contype or gm.conaffinity:
                gm.contype, gm.conaffinity = VEHICLE_CONTYPE, VEHICLE_CONAFF
        for lt in list(child.lights):                      # drop the source scenes' own lights / floors
            child.delete(lt)
        for gm in list(child.worldbody.geoms):
            child.delete(gm)
        body = child.body(root)
        # onboard cameras (body frame).  Omnicopter: its "upright" pose is +90 deg about Y
        # (see omnicopter HOVER_GUIDE), so its forward axis in its own body frame differs.
        if pre == "omni":
            body.add_camera(name="fpv", pos=[0, 0, 0.0], xyaxes=[0, -1, 0, 1, 0, 0], fovy=90)   # placeholder, fixed below
        else:
            ax = _cam_axes(15.0)
            body.add_camera(name="fpv", pos=list(mount), xyaxes=list(ax), fovy=90)
            body.add_camera(name="dvs", pos=list(mount), xyaxes=list(ax), fovy=75)
        if pre == "omni":                                  # no legs: rest the hull on the podium
            body.pos = [0.0, 0.0, 0.50]
        frame = spec.worldbody.add_frame(pos=list(track.START + [dx, dy, 0.05]))
        frame.attach_body(body, pre + "/", "")
    if "omni" in fleet:
        _fix_omni_cameras(spec)
    model = spec.compile()
    out.write_text(spec.to_xml())
    return spec, model


def _fix_omni_cameras(spec):
    """Omnicopter body frame = world frame rotated +90 deg about Y at rest, so world +x (forward)
    is body +z and world +z (up) is body -x.  Mount the cameras on the forward face."""
    body = spec.body("omni/drone")
    R_bw = np.array([[0, 0, -1], [0, 1, 0], [1, 0, 0]], float)   # body<-world for Ry(+90)
    ax = _cam_axes(15.0)
    xc_w, yc_w = ax[:3], ax[3:]
    xc_b, yc_b = R_bw @ xc_w, R_bw @ yc_w
    for cam in list(body.cameras):
        spec.delete(cam)
    mount_w = np.array([0.40, 0.0, 0.0])
    body.add_camera(name="omni/fpv", pos=list(R_bw @ mount_w), xyaxes=list(np.r_[xc_b, yc_b]), fovy=90)
    body.add_camera(name="omni/dvs", pos=list(R_bw @ mount_w), xyaxes=list(np.r_[xc_b, yc_b]), fovy=75)


if __name__ == "__main__":
    spec, m = build()
    print(f"compiled: nbody {m.nbody}, ngeom {m.ngeom}, nu {m.nu}, ncam {m.ncam}")
    d = mujoco.MjData(m); mujoco.mj_forward(m, d)
    for pre in FLEET:
        root = FLEET[pre][1]
        b = m.body(f"{pre}/{root}")
        acts = [m.actuator(i).name for i in range(m.nu) if m.actuator(i).name.startswith(pre + "/")]
        print(f"  {pre:5s} mass {m.body_subtreemass[b.id]:6.3f} kg  actuators {len(acts)}  "
              f"pos {np.round(d.xpos[b.id], 2)}  cams {[m.camera(i).name for i in range(m.ncam) if m.camera(i).name.startswith(pre)]}")
