from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import ExecuteProcess, LogInfo


def generate_launch_description():
    # ----------------------------------------------------------------------
    # AUTONOMOUS bring-up.
    #
    # This is a copy of quanser_state_Estimator.launch.py with the two
    # joystick nodes (joy_node + joy2qcar2/joy_control_node) REMOVED.
    #
    # Why: joy_control_node publishes to /qcar2_motor_speed_cmd continuously,
    # sending throttle=0 whenever the deadman button is not held. That second
    # publisher fought QCarControlNode on the same topic and cancelled the
    # throttle, so the car only crept. With the joystick nodes gone, the
    # controller is the sole publisher, and the estimator's 1 s joystick
    # timeout makes it switch to "AUTONOMOUS SUBSCRIBER fallback" on its own.
    #
    # SAFETY: removing the joystick also removes the manual arm/deadman path.
    # Keep the physical e-stop within reach while testing. For a setup where
    # joystick and autonomous coexist, use a command mux instead (see notes).
    # ----------------------------------------------------------------------
    return LaunchDescription([
        LogInfo(msg=[
            '\n' + '=' * 60 + '\n',
            'QCar State Estimator - AUTONOMOUS Mode (no joystick)\n',
            '=' * 60 + '\n',
            'Joystick publisher disabled; QCarControlNode drives the motor.\n',
            'Keep the e-stop within reach.\n',
            '=' * 60 + '\n'
        ]),

        # QCar Hardware Interface (silent)
        Node(
            package='qcar2_nodes',
            executable='qcar2_hardware',
            name='qcar2_hardware',
            output='log',
            emulate_tty=False,
            arguments=['--ros-args', '--log-level', 'ERROR'],
        ),

        # LiDAR Node (silent)
        Node(
            package='qcar2_nodes',
            executable='lidar',
            name='lidar',
            output='log',
            emulate_tty=False,
            arguments=['--ros-args', '--log-level', 'ERROR'],
        ),

        # --- joy_node and joy_control_node intentionally OMITTED ---
        # They were the second publisher on /qcar2_motor_speed_cmd.

        # RF2O Laser Odometry (silent)
        ExecuteProcess(
            cmd=['ros2', 'launch', 'rf2o_laser_odometry', 'rf2o_laser_odometry.launch.py'],
            output='log',
            shell=True,
            additional_env={'RCUTILS_LOGGING_SEVERITY': 'ERROR'},
        ),

        # State Estimator Node (show output)
        Node(
            package='quanser_state_estimator',
            executable='quanser_state_estimator_node',
            name='quanser_state_estimator_node',
            output='screen',
            emulate_tty=True,
            arguments=['--ros-args', '--log-level', 'INFO'],
            parameters=[{
                'controller_update_rate': 100,
            }],
        ),

        # Your controller (sole publisher of /qcar2_motor_speed_cmd).
        # Remove this block if you prefer to run it by hand in a second
        # terminal with `ros2 run QCarControlNode node`.
        Node(
            package='QCarControlNode',
            executable='node',
            name='qcar_control_node',
            output='screen',
            emulate_tty=True,
            parameters=[{
                'controller': 'CONTROLLER_1',
                'cruise_speed': 0.30,
                'goal_radius': 0.25,
            }],
        ),
    ])
