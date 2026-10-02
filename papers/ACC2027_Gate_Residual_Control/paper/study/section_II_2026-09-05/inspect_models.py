"""Inspect compiled, unmodified simulation models; no experiment is run."""
from pathlib import Path
import sys
import json
import numpy as np
import mujoco

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO/'src'))
from gra_control.platforms.drone import SPECS, _free_joint, _mixer

reports = []
for name in ['cf2', 'cf2-rotor', 'x2']:
    m = mujoco.MjModel.from_xml_path(str(SPECS[name].model))
    _, bid, qa, va = _free_joint(m)
    rotation = np.empty(9)
    mujoco.mju_quat2Mat(rotation, m.body_iquat[bid])
    rotation = rotation.reshape(3, 3)
    inertia_body = rotation @ np.diag(m.body_inertia[bid]) @ rotation.T
    info = dict(platform=name, mass_kg=float(m.body_mass.sum()), nq=m.nq, nv=m.nv,
        principal_inertias_kgm2=m.body_inertia[bid].tolist(), inertia_body_kgm2=inertia_body.tolist(),
        body_com=m.body_ipos[bid].tolist(), inertial_frame_quaternion=m.body_iquat[bid].tolist(),
        xml_integrator=str(mujoco.mjtIntegrator(m.opt.integrator)), density=m.opt.density,
        viscosity=m.opt.viscosity, gravity=m.opt.gravity.tolist(), timestep_xml=m.opt.timestep,
        sensor_count=m.nsensor, actuator_dyntype=m.actuator_dyntype.tolist(),
        gain=m.actuator_gainprm[:, 0].tolist(), ctrlrange=m.actuator_ctrlrange.tolist(),
        joint_damping=m.dof_damping.tolist(), fluid_shape_flags=m.geom_fluid[:, 0].tolist())
    if name != 'cf2':
        aids, B, Binv, limits = _mixer(m)
        info['mixer_B'] = B.tolist()
        info['site_positions'] = m.site_pos[m.actuator_trnid[aids, 0]].tolist()
        info['rotor_max_N_nominal'] = limits[:, 1].tolist()
        info['rotor_max_N_used'] = (limits[:, 1]*(1.5 if name == 'cf2-rotor' else 1.)).tolist()
        info['max_total_thrust_N_used'] = sum(info['rotor_max_N_used'])
        info['thrust_weight_ratio_used'] = info['max_total_thrust_N_used']/(m.body_mass.sum()*abs(m.opt.gravity[2]))
    reports.append(info)
output=Path(__file__).with_name('compiled_model_characteristics.json')
output.write_text(json.dumps(reports, indent=2)+'\n')
print(json.dumps(reports, indent=2))
