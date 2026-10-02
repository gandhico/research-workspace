"""MuJoCo model of the Quanser 3 DOF Gyroscope, generated from params.py.

All bodies share the gimbal centre (balanced gimbals, so gravity exerts no
moment), and the geoms are visual only (inertia comes from explicit <inertial>).
Joints and actuators:
    psi   gray frame, hinge z, unactuated (encoder only on the real device)
    theta red gimbal, hinge y, motor 3 (omitted when red_locked=True)
    phi   blue gimbal, hinge x, motor 2 (torque, |tau| <= kt*Imax)
    spin  disc, hinge y, motor 1 as a speed loop (velocity servo, torque-limited)
The disc spins about +y at positive speed, which reproduces Quanser's sign
convention Jx phi'' = tau2 + h psi', Jz psi'' = -h phi'.
"""
from __future__ import annotations

import mujoco

from .params import PARAMS, QuanserGyroParams


def build_xml(p: QuanserGyroParams = PARAMS, red_locked: bool = True,
              b_psi: float = 0.0, b_phi: float = 0.0, b_theta: float = 0.0,
              spin_kv: float = 0.5, timestep: float = 5e-4) -> str:
    disc_tau = p.kt_disc * p.i_max
    red_joint = "" if red_locked else \
        f'<joint name="theta" type="hinge" axis="0 1 0" damping="{b_theta}" range="-1.4 1.4" limited="true"/>'
    red_motor = "" if red_locked else \
        f'<motor name="tau3" joint="theta" ctrllimited="true" ctrlrange="{-p.tau_max} {p.tau_max}"/>'
    r = p.r_disc
    return f"""
<mujoco model="quanser_3dof_gyroscope">
  <compiler angle="radian" inertiafromgeom="false" autolimits="true"/>
  <option timestep="{timestep}" integrator="RK4" gravity="0 0 -9.81"/>
  <visual><global offwidth="1280" offheight="720"/></visual>
  <default><geom contype="0" conaffinity="0"/></default>
  <asset>
    <texture name="grid" type="2d" builtin="checker" rgb1=".85 .85 .85" rgb2=".75 .75 .75" width="512" height="512"/>
    <material name="grid" texture="grid" texrepeat="6 6"/>
    <material name="gray" rgba=".55 .55 .58 1"/>
    <material name="red" rgba=".80 .15 .15 1"/>
    <material name="blue" rgba=".15 .35 .85 1"/>
    <material name="disc" rgba=".85 .75 .20 1"/>
    <material name="mark" rgba=".1 .1 .1 1"/>
  </asset>
  <worldbody>
    <light pos="0 -1 2" dir="0 .5 -1" diffuse=".9 .9 .9"/>
    <geom name="floor" type="plane" size="1 1 .01" pos="0 0 -0.45" material="grid"/>
    <geom name="pedestal" type="cylinder" size="0.03 0.09" pos="0 0 -0.36" material="gray"/>
    <body name="gray_frame">
      <joint name="psi" type="hinge" axis="0 0 1" damping="{b_psi}"/>
      <inertial pos="0 0 0" mass="1.5" diaginertia="0.03 0.03 {p.gray_Izz}"/>
      <geom type="box" size="0.012 0.30 0.012" pos="0 0 -0.26" material="gray"/>
      <geom type="box" size="0.012 0.012 0.14" pos="0 0.29 -0.13" material="gray"/>
      <geom type="box" size="0.012 0.012 0.14" pos="0 -0.29 -0.13" material="gray"/>
      <body name="red_gimbal">
        {red_joint}
        <inertial pos="0 0 0" mass="0.9" diaginertia="{p.red_Ixx} {p.red_Iyy} {p.red_Izz}"/>
        <geom type="box" size="0.19 0.012 0.012" pos="0 0.27 0" material="red"/>
        <geom type="box" size="0.19 0.012 0.012" pos="0 -0.27 0" material="red"/>
        <geom type="box" size="0.012 0.27 0.012" pos="0.19 0 0" material="red"/>
        <geom type="box" size="0.012 0.27 0.012" pos="-0.19 0 0" material="red"/>
        <body name="blue_gimbal">
          <joint name="phi" type="hinge" axis="1 0 0" damping="{b_phi}"/>
          <inertial pos="0 0 0" mass="0.4" diaginertia="{p.blue_Ixx} {p.blue_Iyy} {p.blue_Izz}"/>
          <geom type="box" size="0.17 0.01 0.01" pos="0 0 0.10" material="blue"/>
          <geom type="box" size="0.17 0.01 0.01" pos="0 0 -0.10" material="blue"/>
          <geom type="box" size="0.01 0.01 0.10" pos="0.17 0 0" material="blue"/>
          <geom type="box" size="0.01 0.01 0.10" pos="-0.17 0 0" material="blue"/>
          <body name="disc">
            <joint name="spin" type="hinge" axis="0 1 0"/>
            <inertial pos="0 0 0" mass="{p.m_disc}" diaginertia="{p.Jd_t} {p.Jd} {p.Jd_t}"/>
            <geom type="cylinder" size="{r} 0.008" euler="1.5708 0 0" material="disc"/>
            <geom type="box" size="{0.9 * r} 0.0085 0.006" material="mark"/>
          </body>
        </body>
      </body>
    </body>
  </worldbody>
  <actuator>
    <motor name="tau2" joint="phi" ctrllimited="true" ctrlrange="{-p.tau_max} {p.tau_max}"/>
    {red_motor}
    <velocity name="disc_speed" joint="spin" kv="{spin_kv}" forcelimited="true" forcerange="{-disc_tau} {disc_tau}"/>
  </actuator>
</mujoco>
"""


def load(**kw) -> tuple[mujoco.MjModel, mujoco.MjData]:
    m = mujoco.MjModel.from_xml_string(build_xml(**kw))
    return m, mujoco.MjData(m)


def qadr(m: mujoco.MjModel, joint: str) -> tuple[int, int]:
    j = m.joint(joint)
    return int(j.qposadr[0]), int(j.dofadr[0])
