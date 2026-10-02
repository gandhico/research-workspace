from __future__ import annotations

import math
import time

import numpy as np
import rclpy
from rclpy.node import Node

from geometry_msgs.msg import PoseStamped, Pose2D
from qcar2_interfaces.msg import MotorCommands
from pal.utilities.math import wrap_to_pi
from transforms3d.euler import quat2euler

# Controllers + shared data contracts live alongside this file in the package.
# This relative import works when launched via `ros2 run` (recommended).
from .controllers import (
    LaneState,
    SMCLaneController,
    ImageNMPCController,
    build_default_args,
)


class QCarControlNode(Node):
    def __init__(self):
        super().__init__('qcar_control_node')

        # --- Controller selector (ROS parameter) ---
        # CONTROLLER_1 -> SMC, CONTROLLER_2 -> NMPC, 3/4 -> simple P fallback.
        # Override at launch, e.g.:
        #   ros2 run QCarControlNode node --ros-args -p controller:=CONTROLLER_2
        self.valid_controllers = (
            "CONTROLLER_1", "CONTROLLER_2", "CONTROLLER_3", "CONTROLLER_4",
        )
        self.declare_parameter("controller", "CONTROLLER_1")
        requested = self.get_parameter("controller").get_parameter_value().string_value
        if requested not in self.valid_controllers:
            self.get_logger().warn(
                f"Unknown controller '{requested}'. "
                f"Valid: {self.valid_controllers}. Falling back to CONTROLLER_1."
            )
            requested = "CONTROLLER_1"
        self.active_controller = requested

        # --- Tunables (gains live in controllers.build_default_args) ---
        self.args = build_default_args()
        # These four are the ones you'll most often want to change on the car,
        # so they're ROS parameters. Override at launch, e.g.:
        #   --ros-args -p cruise_speed:=0.4 -p max_steering:=0.5
        self.declare_parameter("cruise_speed", 0.30)
        self.declare_parameter("max_speed", 0.50)
        self.declare_parameter("max_steering", float(self.args.max_steering))
        self.declare_parameter("goal_radius", 0.25)

        self.cruise_speed = self.get_parameter("cruise_speed").value  # Units: m/s
        self.max_speed = self.get_parameter("max_speed").value        # Hard clamp on speed (m/s)
        self.max_steering = self.get_parameter("max_steering").value  # rad
        self.goal_radius = self.get_parameter("goal_radius").value    # m; stop within this
        self.min_speed_scale = 0.20

        # Keep controllers' steering limit in sync with the node parameter.
        self.args.max_steering = float(self.max_steering)

        # --- Controller instances ---
        self.controllers = {
            "CONTROLLER_1": SMCLaneController(self.args),
            "CONTROLLER_2": ImageNMPCController(self.args),
        }

        # --- Subscribers ---
        self.pose_subscriber = self.create_subscription(
            PoseStamped, '/qcar_pose_ekf', self.pose_callback, 10
        )
        self.waypoint_subscriber = self.create_subscription(
            Pose2D, '/a_star_waypoint', self.waypoint_callback, 10
        )

        # --- Publisher ---
        self.cmd_publisher = self.create_publisher(
            MotorCommands, '/qcar2_motor_speed_cmd', 10
        )

        # --- State ---
        self.current_x = None
        self.current_y = None
        self.current_yaw = None
        self.target_x = 0.0
        self.target_y = 0.0

        # --- Memory for derivative / rate terms ---
        self.prev_lane_error = 0.0
        self.prev_steering = 0.0
        
        # Capture initial time to prevent a dt spike on the second execution frame
        self.last_time = time.monotonic()

        # --- Control loop timer (50 Hz) ---
        self.timer = self.create_timer(0.02, self.control_loop)
        self.get_logger().info(
            f"QCarControlNode up. controller={self.active_controller} "
            f"cruise_speed={self.cruise_speed} max_speed={self.max_speed} "
            f"max_steering={self.max_steering} goal_radius={self.goal_radius}"
        )

    # ------------------------------------------------------------------ #
    # Callbacks
    # ------------------------------------------------------------------ #
    def pose_callback(self, msg: PoseStamped):
        self.current_x = msg.pose.position.x
        self.current_y = msg.pose.position.y
        q = msg.pose.orientation
        _, _, yaw = quat2euler([q.w, q.x, q.y, q.z])
        self.current_yaw = wrap_to_pi(yaw)

    def waypoint_callback(self, msg: Pose2D):
        self.target_x = msg.x
        self.target_y = msg.y

    # ------------------------------------------------------------------ #
    # Pose + waypoint  ->  lane-style errors
    # ------------------------------------------------------------------ #
    def _build_lane_state(self, dt: float):
        """Transform the target into the vehicle frame and produce a LaneState.

        Vehicle frame: x forward, y to the LEFT.
          lane_error = lateral offset of target (left positive)
          slope_xy   = heading error to target (rad)
        """
        dx = self.target_x - self.current_x
        dy = self.target_y - self.current_y
        dist = math.hypot(dx, dy)

        cos_y = math.cos(self.current_yaw)
        sin_y = math.sin(self.current_yaw)
        
        y_v = -sin_y * dx + cos_y * dy            # lateral offset of target, +left
        heading_err = wrap_to_pi(math.atan2(dy, dx) - self.current_yaw)  # +left

        # SIGN CONVENTION (verified on the stand):
        # The controllers' law is steering = -k*error, and on THIS QCar a
        # negative steering command turns the car RIGHT. With "target to the
        # left" defined as positive, the raw output drove the car AWAY from the
        # target (error grew). Negating both error terms aligns the controller
        # frame with the actuator so the car steers TOWARD the target.
        # (Feeding the negated errors -- rather than negating the final output --
        # keeps NMPC's previous_steering / rate-limit bookkeeping consistent.)
        lane_error = -float(y_v)
        slope_for_ctrl = -float(heading_err)

        d_lane_error = (lane_error - self.prev_lane_error) / max(dt, 1e-6)
        self.prev_lane_error = lane_error

        state = LaneState(
            lane_error=lane_error,
            d_lane_error=float(d_lane_error),
            slope_xy=slope_for_ctrl,
            loop_dt=float(dt),
            previous_steering=float(self.prev_steering),
        )
        return state, dist, heading_err

    # ------------------------------------------------------------------ #
    # Main loop
    # ------------------------------------------------------------------ #
    def control_loop(self):
        # Gate: wait for pose data.
        if self.current_x is None or self.current_yaw is None:
            return

        # Real elapsed time
        now = time.monotonic()
        dt = 0.02 if self.last_time is None else max(now - self.last_time, 1e-3)
        self.last_time = now

        state, dist, heading_err = self._build_lane_state(dt)

        # --- DEBUG INPUT DATA (Acelerado a 1 Hz para no saturar) ---
        self.get_logger().info(
            f"\n[DATA IN] "
            f"Pose: ({self.current_x:.2f}, {self.current_y:.2f}, Yaw: {self.current_yaw:.2f} rad) | "
            f"Target: ({self.target_x:.2f}, {self.target_y:.2f}) | "
            f"Dist: {dist:.2f}m\n"
            f"[LANE STATE] "
            f"Error Lateral: {state.lane_error:.3f}m | "
            f"Derivada Error: {state.d_lane_error:.3f} | "
            f"Error Rumbo: {state.slope_xy:.3f} rad | dt: {state.loop_dt:.4f}s",
            throttle_duration_sec=1.0
        )

        speed_cmd = 0.0
        steering_cmd = 0.0

        # --- SLOT 1: SMC ---
        if self.active_controller == "CONTROLLER_1":
            out = self.controllers["CONTROLLER_1"].step(state)
            steering_cmd = out.raw_steering

        # --- SLOT 2: NMPC ---
        elif self.active_controller == "CONTROLLER_2":
            out = self.controllers["CONTROLLER_2"].step(state)
            steering_cmd = out.raw_steering

        # --- SLOT 3: placeholder (simple proportional) ---
        elif self.active_controller == "CONTROLLER_3":
            steering_cmd = -self.args.pid_kp * state.lane_error

        # --- SLOT 4: placeholder (simple proportional) ---
        elif self.active_controller == "CONTROLLER_4":
            steering_cmd = -self.args.pid_kp * state.lane_error

        # --- Clamp steering and remember it (NMPC needs previous_steering) ---
        steering_cmd = float(np.clip(steering_cmd, -self.max_steering, self.max_steering))
        self.prev_steering = steering_cmd

        # --- Speed policy: cruise, eased off in turns, stop at the goal ---
        turn_scale = 1.0
        if dist <= self.goal_radius:
            speed_cmd = 0.0
            speed_reason = f"STOP@GOAL (dist {dist:.2f} <= goal_radius {self.goal_radius:.2f})"
        else:
            turn_scale = 1.0 - abs(heading_err) / (math.pi / 2.0)
            turn_scale = float(np.clip(turn_scale, self.min_speed_scale, 1.0))
            speed_cmd = float(np.clip(self.cruise_speed * turn_scale, 0.0, self.max_speed))
            if turn_scale <= self.min_speed_scale + 1e-6:
                speed_reason = f"CRUISE-CLAMPED (big heading err, turn_scale={turn_scale:.2f})"
            else:
                speed_reason = f"CRUISE (turn_scale={turn_scale:.2f})"

        # --- NaN guard: never publish garbage to hardware ---
        if not (math.isfinite(speed_cmd) and math.isfinite(steering_cmd)):
            self.get_logger().warn("Non-finite command computed; commanding stop.")
            speed_cmd, steering_cmd = 0.0, 0.0
            speed_reason = "STOP@NAN"

        # --- DEBUG OUTPUT DATA (Acelerado a 1 Hz sincronizado) ---
        self.get_logger().info(
            f"[DATA OUT] "
            f"Ctrl Activo: {self.active_controller} | "
            f"Cmd Dirección: {steering_cmd:.3f} rad ({math.degrees(steering_cmd):.1f}°) | "
            f"Cmd Velocidad: {speed_cmd:.3f} m/s | "
            f"Motivo Velocidad: {speed_reason}",
            throttle_duration_sec=1.0
        )

        self.publish_commands(speed_cmd, steering_cmd)

    # ------------------------------------------------------------------ #
    # Publishing
    # ------------------------------------------------------------------ #
    def publish_commands(self, speed, steering):
        cmd = MotorCommands()
        
        # Confección de vectores paralelos para la API hardware de QCar2
        cmd.motor_names = ["steering_angle", "motor_throttle"]
        
        # Mapeo idéntico al orden de nombres: [rad, m/s]
        cmd.values = [float(steering), float(speed)]
        
        self.cmd_publisher.publish(cmd)


def main(args=None):
    rclpy.init(args=args)
    node = QCarControlNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        # Safe stop on exit.
        try:
            node.publish_commands(0.0, 0.0)
        except Exception:
            pass
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()