from pymavlink import mavutil
import time
import sys

# ============================================================
# SETTINGS
# ============================================================

UDP_PORT = 14550

# Normalized test power:
# 0.00 = neutral (1500)
# 1.00 = maximum positive-direction command (2000)
#
# Start LOW.
TEST_POWER = 0.10

# Seconds each motor runs
TEST_TIME = 3.0

NUMBER_OF_MOTORS = 8

# ArduPilot motor-test command
MAV_CMD_DO_MOTOR_TEST = 209

# Throttle type:
# 0 = percentage
# 1 = direct PWM
# 2 = pilot throttle
THROTTLE_TYPE = 1

# PWM-equivalent values; ArduPilot converts these to DShot-3D.
NEUTRAL_PWM = 1500
MAX_PWM = 2000

# One motor at a time
MOTOR_COUNT = 1

# Default motor-test order
TEST_ORDER = 0


# ============================================================
# START
# ============================================================

print("=" * 65)
print("ARDUPILOT OCTACOPTER MOTOR TEST")
print("=" * 65)

print()
print("IMPORTANT:")
print(" - REMOVE ALL PROPELLERS")
print(" - Vehicle must remain DISARMED")
print(" - ESC battery must be connected")
print(" - Close Mission Planner")
print()

confirmation = input(
    "Type YES to confirm ALL propellers are removed: "
).strip().upper()

if confirmation != "YES":
    print("Motor test cancelled.")
    sys.exit(0)


# ============================================================
# RECEIVE CONNECTION
# PICO -> PC
# ============================================================

print()
print(f"Listening for MAVLink on UDP port {UDP_PORT}...")

rx_connection = mavutil.mavlink_connection(
    f"udpin:0.0.0.0:{UDP_PORT}",
    source_system=255,
    source_component=190,
)


# ============================================================
# WAIT FOR CUBE
# ============================================================

print("Waiting for Cube heartbeat...")

heartbeat = rx_connection.wait_heartbeat(
    timeout=15
)

if heartbeat is None:
    rx_connection.close()

    raise TimeoutError(
        "No heartbeat received from Cube."
    )


target_system = heartbeat.get_srcSystem()
target_component = heartbeat.get_srcComponent()

print()
print("Connected!")
print("System ID:", target_system)
print("Component ID:", target_component)


# ============================================================
# CHECK ARMING STATE
# ============================================================

armed = bool(
    heartbeat.base_mode
    & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED
)

if armed:

    print()
    print("ERROR: VEHICLE IS ARMED.")
    print("Disarm before performing a motor test.")

    rx_connection.close()
    sys.exit(1)

print("Vehicle is DISARMED.")


# ============================================================
# DETECT PICO IP
# ============================================================

clients = getattr(
    rx_connection,
    "clients",
    None
)

if not clients:

    rx_connection.close()

    raise RuntimeError(
        "Could not determine Pico W IP address."
    )


client_list = list(clients)

pico_ip = client_list[0][0]
pico_port = client_list[0][1]

print()
print("Detected Pico IP:", pico_ip)
print("Pico UDP port:", pico_port)


# ============================================================
# TRANSMIT CONNECTION
# PC -> PICO
# ============================================================

tx_connection = mavutil.mavlink_connection(
    f"udpout:{pico_ip}:{UDP_PORT}",
    source_system=255,
    source_component=190,
)

print(
    f"PC -> Pico connection ready: "
    f"{pico_ip}:{UDP_PORT}"
)


# ============================================================
# SEND GCS HEARTBEAT
# ============================================================

def send_gcs_heartbeat():

    tx_connection.mav.heartbeat_send(
        mavutil.mavlink.MAV_TYPE_GCS,
        mavutil.mavlink.MAV_AUTOPILOT_INVALID,
        0,
        0,
        mavutil.mavlink.MAV_STATE_ACTIVE,
    )


send_gcs_heartbeat()


# ============================================================
# 6DoF / DSHOT-3D CONFIGURATION CHECK
# ============================================================
# This version targets FRAME_CLASS=16 and SERVO_BLH_3DMASK=255.
# Never use 0% / 1000 as a stop on reversible outputs.

def read_parameter(name, timeout=3.0):

    for _ in range(3):

        tx_connection.mav.param_request_read_send(
            target_system,
            target_component,
            name.encode(),
            -1
        )

        deadline = time.time() + timeout / 3

        while time.time() < deadline:

            message = rx_connection.recv_match(
                type="PARAM_VALUE",
                blocking=True,
                timeout=0.2
            )

            if message is None:
                continue

            if (message.get_srcSystem() != target_system
                    or message.get_srcComponent() != target_component):
                continue

            param_id = message.param_id

            if isinstance(param_id, bytes):
                param_id = param_id.decode("utf-8", "ignore")

            if param_id.rstrip("\x00") == name:
                return message.param_value

    return None


frame_class = read_parameter("FRAME_CLASS")
reversible_mask = read_parameter("SERVO_BLH_3DMASK")

print()
print("FRAME_CLASS:", frame_class)
print("SERVO_BLH_3DMASK:", reversible_mask)


if frame_class != 16 or reversible_mask != 255:

    print()
    print("REFUSING: expected FRAME_CLASS=16 and SERVO_BLH_3DMASK=255.")
    print("Configuration is missing or differs from the DShot-3D setup.")
    print("No motor-test commands were sent.")
    tx_connection.close()
    rx_connection.close()
    sys.exit(1)


# The reversible mask addresses physical outputs, not motor test numbers.
# Confirm all eight motors are assigned to those reversible outputs.
motor_functions = [
    read_parameter(f"SERVO{channel}_FUNCTION")
    for channel in range(1, 9)
]

if None in motor_functions or sorted(motor_functions) != list(range(33, 41)):

    print("REFUSING: outputs 1-8 must contain Motor1 through Motor8 once each.")
    print("SERVO1..8_FUNCTION:", motor_functions)
    print("No motor-test commands were sent.")
    tx_connection.close()
    rx_connection.close()
    sys.exit(1)


print("DShot-3D outputs verified: 1500 neutral, 1550 at 10% positive power.")


# ============================================================
# CLEAR OLD ACK MESSAGES
# ============================================================

def clear_old_acks():

    while rx_connection.recv_match(
        type="COMMAND_ACK",
        blocking=False
    ):
        pass


# ============================================================
# PRINT STATUS TEXT
# ============================================================

def decode_statustext(message):

    try:

        if isinstance(message.text, bytes):

            return (
                message.text
                .decode("utf-8")
                .rstrip("\x00")
            )

        return str(message.text)

    except Exception:

        return str(message.text)


# ============================================================
# TEST MOTOR
# ============================================================

def test_motor(
    motor_number,
    power=TEST_POWER,
    duration=TEST_TIME
):

    if motor_number < 1 or motor_number > NUMBER_OF_MOTORS:

        print("Invalid motor number.")
        return False


    if power < 0.0 or power > 1.0:

        print(
            "Power must be between "
            "0.0 and 1.0."
        )

        return False


    # Positive half of the reversible range; zero power is neutral.
    throttle_percent = power * 100.0
    throttle_pwm = round(NEUTRAL_PWM + power * (MAX_PWM - NEUTRAL_PWM))


    print()
    print("=" * 55)
    print(f"TESTING MOTOR {motor_number}")
    print("=" * 55)

    print(
        f"Power:    {throttle_percent:.1f}%"
    )

    print(
        f"Duration: {duration:.1f} seconds"
    )

    print()


    clear_old_acks()

    send_gcs_heartbeat()

    time.sleep(0.1)


    # --------------------------------------------------------
    # SEND MAV_CMD_DO_MOTOR_TEST
    # --------------------------------------------------------

    tx_connection.mav.command_long_send(

        target_system,
        target_component,

        MAV_CMD_DO_MOTOR_TEST,

        0,                  # confirmation

        motor_number,       # param1: motor number
        THROTTLE_TYPE,      # param2: throttle type
        throttle_pwm,       # param3: PWM-equivalent DShot-3D throttle
        duration,           # param4: timeout
        MOTOR_COUNT,        # param5: motor count
        TEST_ORDER,         # param6: test order
        0                   # param7: unused
    )


    print(
        "MAV_CMD_DO_MOTOR_TEST sent."
    )

    print(
        "Waiting for Cube response..."
    )


    # ========================================================
    # WAIT FOR ACK
    # ========================================================

    ack_received = False
    accepted = False

    deadline = time.time() + 3


    while time.time() < deadline:

        message = rx_connection.recv_match(
            blocking=True,
            timeout=0.25
        )

        if message is None:
            continue

        message_type = message.get_type()


        # ----------------------------------------------------
        # COMMAND ACK
        # ----------------------------------------------------

        if message_type == "COMMAND_ACK":

            if (
                message.command
                != MAV_CMD_DO_MOTOR_TEST
            ):
                continue


            ack_received = True


            result_enum = (
                mavutil.mavlink.enums[
                    "MAV_RESULT"
                ].get(message.result)
            )


            if result_enum is not None:

                result_name = result_enum.name

            else:

                result_name = str(
                    message.result
                )


            print()
            print("COMMAND_ACK received")
            print(
                "Result:",
                result_name
            )


            if (
                message.result
                == mavutil.mavlink.MAV_RESULT_ACCEPTED
            ):

                accepted = True

            break


        # ----------------------------------------------------
        # STATUS TEXT
        # ----------------------------------------------------

        elif message_type == "STATUSTEXT":

            print(
                "Cube:",
                decode_statustext(message)
            )


    if not ack_received:

        print()
        print(
            "WARNING: No COMMAND_ACK received."
        )

        return False


    if not accepted:

        print()
        print("Motor test REJECTED.")

        return False


    print()
    print("Motor test ACCEPTED.")

    print(
        f"Motor {motor_number} should now "
        f"run for {duration:.1f} seconds."
    )


    # ========================================================
    # MONITOR WHILE MOTOR IS RUNNING
    # ========================================================

    stop_deadline = time.time() + duration + 2.0


    while time.time() < stop_deadline:

        message = rx_connection.recv_match(
            blocking=True,
            timeout=0.25
        )


        if message is None:
            continue


        if message.get_type() == "STATUSTEXT":

            text = decode_statustext(message)

            print(
                "Cube:",
                text
            )


            if "finished motor test" in text.lower():

                break


    print()
    print(
        f"Motor {motor_number} test finished."
    )

    return True


# ============================================================
# EMERGENCY STOP
# ============================================================

def emergency_stop():

    print()
    print("EMERGENCY STOP")


    # Command DShot-3D neutral with a very short timeout
    for motor_number in range(
        1,
        NUMBER_OF_MOTORS + 1
    ):

        tx_connection.mav.command_long_send(

            target_system,
            target_component,

            MAV_CMD_DO_MOTOR_TEST,

            0,

            motor_number,
            THROTTLE_TYPE,  # direct PWM-equivalent mode
            NEUTRAL_PWM,    # 1500 = DShot-3D neutral
            0.1,        # short timeout
            1,
            0,
            0
        )


    # Also request disarm as a backup
    tx_connection.mav.command_long_send(

        target_system,
        target_component,

        mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,

        0,

        0,      # DISARM
        0,      # do NOT force
        0,
        0,
        0,
        0,
        0
    )

    time.sleep(0.5)

    print(
        "Stop/disarm commands sent."
    )


# ============================================================
# MAIN MENU
# ============================================================

print()
print("=" * 65)
print("OCTACOPTER MOTOR TEST READY")
print("=" * 65)

print()
print(
    f"Test power:    "
    f"{TEST_POWER * 100:.1f}%"
)

print(
    f"Test duration: "
    f"{TEST_TIME:.1f} seconds"
)

print()


try:

    while True:

        print()
        print("---------------------------------------")
        print("Choose motor:")
        print()
        print("  1  2  3  4  5  6  7  8")
        print()
        print("  q = quit")
        print("---------------------------------------")
        print()


        choice = input(
            "Motor number: "
        ).strip().lower()


        if choice == "q":
            break


        try:

            motor = int(choice)

        except ValueError:

            print(
                "Enter a number from 1 to 8."
            )

            continue


        if (
            motor < 1
            or motor > NUMBER_OF_MOTORS
        ):

            print(
                "Enter a number from 1 to 8."
            )

            continue


        print()
        print(
            f"Selected MOTOR {motor}"
        )

        print(
            f"Power = "
            f"{TEST_POWER * 100:.1f}%"
        )


        confirmation = input(
            f"Type RUN to test MOTOR {motor}: "
        ).strip().upper()


        if confirmation != "RUN":

            print(
                "Motor test cancelled."
            )

            continue


        test_motor(
            motor,
            TEST_POWER,
            TEST_TIME
        )


        time.sleep(1)


# ============================================================
# CTRL+C
# ============================================================

except KeyboardInterrupt:

    print()
    print("CTRL+C detected.")


# ============================================================
# CLEANUP
# ============================================================

finally:

    emergency_stop()

    tx_connection.close()
    rx_connection.close()

    print()
    print("Motor testing finished.")
    print("Connections closed.")