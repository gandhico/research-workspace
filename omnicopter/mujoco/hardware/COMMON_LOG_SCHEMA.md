# Common physical--virtual log contract

Before comparison, both logs must use SI units, the MuJoCo world frame and the
MuJoCo body frame. Do not correct signs or time shifts by optimizing tracking
results after the experiment.

Required CSV columns:

| Field | Frame/unit | Meaning |
|---|---|---|
| `time_s` | synchronized monotonic seconds | Sample acquisition time, not receive time. |
| `x_m,y_m,z_m` | MuJoCo world, m | Body-origin position. |
| `q_w,q_x,q_y,q_z` | MuJoCo body attitude in world | Unit quaternion whose rotation maps body vectors into world coordinates; sign may flip without changing attitude. |
| `wx_rad_s,wy_rad_s,wz_rad_s` | MuJoCo body, rad/s | Angular velocity. |
| `thrust_1_N` … `thrust_8_N` | rotor convention, N | Realized or calibrated commanded signed thrust. |

Recommended fields include raw IMU, motion-capture pose, estimator pose,
voltage, current, ESC command, rotor speed, controller wrench, residual wrench,
saturation flags, sequence number, hardware timestamp, receive timestamp,
controller name/version, parameter-set hash and emergency-state flags.

Maintain raw logs unchanged. Frame conversion, resampling and calibration must
produce new derived files with a manifest and source hashes.
