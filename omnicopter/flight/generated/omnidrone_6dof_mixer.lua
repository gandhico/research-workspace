-- Omnidrone 6DoF mixer for ArduPilot Copter (FRAME_CLASS 16, SCR_ENABLE 1)
-- Generated 2026-11-04T20:10:11Z by hardware/ardupilot/make_6dof_mixer.py
-- Twin XML sha256 6303b7b90a40c15c9da68f4ea1f0924b4f8f3fd7bb1ad670d77f3c232a136de6
-- AP forward = world x at the twin hover attitude; FRD axes in MuJoCo body coords:
--   forward = ( 0.000000,  0.000000,  1.000000)
--   right   = ( 0.000000, -1.000000,  0.000000)
--   down    = ( 1.000000,  0.000000,  0.000000)
-- Motor map: ArduPilot MotorK (SERVO function 32+K) -> twin rotor_N. CONFIRM ON HARDWARE.
-- Reversible motors: ESCs must run bidirectional/3D (1500 us = stop). MOT_YAW_HEADROOM/1000 sets
-- the reversal deadzone (capped at 0.25) in this mixer.
-- Physical scale at Tmax=10.000 N/rotor: throttle 1.0 = 45.734 N up; roll/pitch/yaw 1.0 = 5.6983 N*m
-- Twin hover throttle estimate (mass 2.500 kg, unverified): 0.536
--                         Roll        Pitch       Yaw         Throttle    Forward     Right     Rev  Order
Motors_6DoF:add_motor(0, -0.267949, -1.000000, -0.732051,  0.980357,  1.322149,  0.363403, true, 1)  -- Motor1 = twin rotor_1
Motors_6DoF:add_motor(1,  1.000000, -0.267949,  0.732051, -0.986625, -0.365235,  1.332431, true, 2)  -- Motor2 = twin rotor_2
Motors_6DoF:add_motor(2, -1.000000,  0.267949,  0.732051, -0.993733,  0.373685, -1.320316, true, 3)  -- Motor3 = twin rotor_3
Motors_6DoF:add_motor(3,  0.267949,  1.000000, -0.732051,  1.000000, -1.330599, -0.375518, true, 4)  -- Motor4 = twin rotor_4
Motors_6DoF:add_motor(4, -0.267949, -1.000000,  0.732051,  0.980357, -1.374620, -0.349343, true, 5)  -- Motor5 = twin rotor_5
Motors_6DoF:add_motor(5,  1.000000, -0.267949, -0.732051, -0.986625,  0.351176, -1.384902, true, 6)  -- Motor6 = twin rotor_6
Motors_6DoF:add_motor(6, -1.000000,  0.267949, -0.732051, -0.993733, -0.359626,  1.372787, true, 7)  -- Motor7 = twin rotor_7
Motors_6DoF:add_motor(7,  0.267949,  1.000000,  0.732051,  1.000000,  1.383070,  0.361458, true, 8)  -- Motor8 = twin rotor_8

assert(Motors_6DoF:init(8), 'unable to setup 8 motors')

-- First flights: translate by tilting like a normal copter (standard position-controller
-- assumptions). Switch both to true later for attitude-independent translation.
attitude_control:set_forward_enable(false)
attitude_control:set_lateral_enable(false)

motors:set_frame_string("Omnidrone 6DoF (twin-derived)")
gcs:send_text(6, "Omnidrone 6DoF mixer loaded")
