from pymavlink import mavutil
import time
import sys
import os
import math

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
TEST_TIME = 10.0

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

# Motor commands always use count=1; count>1 is a sequential test.
# The controller retains earlier outputs while another motor is selected.
COMMAND_LEASE = 0.8  # seconds; firmware stops ALL outputs after link loss
ACK_TIMEOUT = 0.3
OUTPUT_DWELL = 0.06  # allow the FC output loop to apply each command

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
# RESPONSIVE CONSOLE AND EMERGENCY STOP
# ============================================================

class EmergencyStop(Exception):
    pass


class Console:
    """Read individual keys without a keyboard package or a reader thread."""

    def __enter__(self):
        if not sys.stdin.isatty():
            raise RuntimeError("Run in an interactive terminal (PowerShell, CMD, or Terminal).")
        self.saved_terminal = None
        if os.name == "nt":
            import msvcrt
            self.windows_keys = msvcrt
        else:
            import termios
            import tty
            self.termios = termios
            self.saved_terminal = termios.tcgetattr(sys.stdin.fileno())
            tty.setcbreak(sys.stdin.fileno())
        return self

    def __exit__(self, *exc):
        if self.saved_terminal is not None:
            self.termios.tcsetattr(
                sys.stdin.fileno(), self.termios.TCSADRAIN, self.saved_terminal
            )

    def key(self):
        if os.name == "nt":
            if not self.windows_keys.kbhit():
                return None
            char = self.windows_keys.getwch()
            if char in ("\x00", "\xe0"):
                self.windows_keys.getwch()  # consume the second half of special keys
                return None
            return char
        import select
        if select.select([sys.stdin], [], [], 0)[0]:
            char = os.read(sys.stdin.fileno(), 1).decode("utf-8", "ignore")
            if not char:
                raise EOFError("Console input closed")
            return char
        return None

    def poll_stop(self):
        # Bound the work even if someone holds down another key.
        for _ in range(32):
            char = self.key()
            if char is None:
                break
            if char == "\x03":
                raise KeyboardInterrupt
            if char.lower() == "e":
                raise EmergencyStop

    def line(self, prompt, emergency_enabled=True):
        print(prompt, end="", flush=True)
        chars = []
        while True:
            char = self.key()
            if char is None:
                time.sleep(0.02)
                continue
            if char == "\x03":
                raise KeyboardInterrupt
            if char in ("\x04", "\x1a"):
                raise EOFError("Console input closed")
            if emergency_enabled and char.lower() == "e":
                print("\nE pressed.")
                raise EmergencyStop
            if char in ("\r", "\n"):
                print()
                return "".join(chars).strip()
            if char in ("\b", "\x7f"):
                if chars:
                    chars.pop()
                    print("\b \b", end="", flush=True)
            elif char.isprintable():
                chars.append(char)
                print(char, end="", flush=True)


def responsive_wait(seconds, console):
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        console.poll_stop()
        time.sleep(min(0.02, max(0, end - time.monotonic())))
    console.poll_stop()


def from_cube(message):
    return (message.get_srcSystem() == target_system
            and message.get_srcComponent() == target_component)


def decode_statustext(message):
    text = message.text
    if isinstance(text, bytes):
        return text.decode("utf-8", "replace").rstrip("\x00")
    return str(text).rstrip("\x00")


def send_motor_command(motor, pwm, timeout):
    tx_connection.mav.command_long_send(
        target_system, target_component, MAV_CMD_DO_MOTOR_TEST, 0,
        motor, THROTTLE_TYPE, pwm, timeout, 1, TEST_ORDER, 0,
    )


def stop_all(reason="STOP ALL MOTORS"):
    """Cancel the FC's shared motor-test session, then request disarm.

    A zero-duration motor-test command expires the entire session on the
    next FC motor-test update, including outputs latched by earlier commands.
    Repeat in case UDP drops a packet. Never send 0% / 1000 as a stop.
    This is a drive stop, not a guarantee of active ESC electrical braking.
    """
    print(f"\n{reason}", flush=True)
    errors = []
    for _ in range(3):
        try:
            send_motor_command(1, NEUTRAL_PWM, 0.0)
        except Exception as exc:
            errors.append(str(exc))
        try:
            tx_connection.mav.command_long_send(
                target_system, target_component,
                mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM, 0,
                0, 0, 0, 0, 0, 0, 0,
            )
        except Exception as exc:
            errors.append(str(exc))
        time.sleep(0.05)
    if errors:
        print("Stop transmission error:", errors[-1])
    print("Stop/disarm requests sent. Verify every motor has stopped.")


def parse_motors(text):
    tokens = text.replace(",", " ").split()
    if not tokens:
        raise ValueError("Choose at least one motor.")
    motors = [int(token) for token in tokens]
    if any(motor < 1 or motor > NUMBER_OF_MOTORS for motor in motors):
        raise ValueError("Motor numbers must be 1 through 8.")
    if len(set(motors)) != len(motors):
        raise ValueError("Do not repeat motor numbers.")
    return sorted(motors)


def throttle_value(percent, direction):
    if not math.isfinite(percent) or not 0 <= percent <= 100:
        raise ValueError("Power must be a finite percentage from 0 to 100.")
    if direction not in ("f", "r"):
        raise ValueError("Direction must be f or r.")
    sign = 1 if direction == "f" else -1
    return round(NEUTRAL_PWM + sign * 500 * percent / 100)


def require_disarmed(console):
    # Discard cached heartbeats and require a fresh one before each test.
    for _ in range(1000):
        if rx_connection.recv_match(type="HEARTBEAT", blocking=False) is None:
            break
    deadline = time.monotonic() + 3
    while time.monotonic() < deadline:
        console.poll_stop()
        message = rx_connection.recv_match(blocking=False)
        if message is not None and from_cube(message) and message.get_type() == "HEARTBEAT":
            if message.base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED:
                raise RuntimeError("Vehicle is armed. Disarm before testing.")
            return
        time.sleep(0.01)
    raise RuntimeError("No fresh Cube heartbeat; refusing to start.")


def command_and_ack(motor, pwm, console):
    # One command at a time: MAVLink ACKs contain no motor number.
    for _ in range(1000):
        if rx_connection.recv_match(type="COMMAND_ACK", blocking=False) is None:
            break
    console.poll_stop()
    send_motor_command(motor, pwm, COMMAND_LEASE)
    deadline = time.monotonic() + ACK_TIMEOUT
    while time.monotonic() < deadline:
        console.poll_stop()
        message = rx_connection.recv_match(blocking=False)
        if message is None:
            time.sleep(0.01)
            continue
        if not from_cube(message):
            continue
        kind = message.get_type()
        if kind == "COMMAND_ACK" and message.command == MAV_CMD_DO_MOTOR_TEST:
            if message.result != mavutil.mavlink.MAV_RESULT_ACCEPTED:
                raise RuntimeError(f"Motor {motor} command rejected (result {message.result}).")
            # The FC stores only the most recent motor-test command. Give
            # its output task time to apply this motor before selecting another.
            responsive_wait(OUTPUT_DWELL, console)
            return
        if kind == "STATUSTEXT":
            text = decode_statustext(message)
            print("Cube:", text)
            if "finished motor test" in text.lower() or "motor test: cancelled" in text.lower():
                raise RuntimeError("Cube ended the motor test unexpectedly.")
    raise RuntimeError(f"No motor-test ACK for motor {motor}; stopping all outputs.")


def test_motors(motors, percent, direction, console, duration=TEST_TIME):
    # Validate everything before sending even a neutral/start command.
    if not motors or any(type(m) is not int or not 1 <= m <= NUMBER_OF_MOTORS for m in motors):
        raise ValueError("Invalid motor selection.")
    if len(set(motors)) != len(motors):
        raise ValueError("Duplicate motor selection.")
    if not math.isfinite(duration) or not 0 < duration <= 600:
        raise ValueError("Duration must be greater than 0 and at most 600 seconds.")
    pwm = throttle_value(percent, direction)
    require_disarmed(console)
    try:
        send_gcs_heartbeat()
        # Initialize all outputs to neutral, with only one active test session.
        command_and_ack(1, NEUTRAL_PWM, console)
        for motor in motors:
            command_and_ack(motor, pwm, console)
        print("Selected motors running together. PRESS E TO STOP (no Enter).", flush=True)
        # Duration starts after the selected motors have all been commanded.
        deadline = time.monotonic() + duration
        next_heartbeat = time.monotonic() + 1
        while time.monotonic() < deadline:
            for motor in motors:
                console.poll_stop()
                if time.monotonic() >= deadline:
                    break
                if time.monotonic() >= next_heartbeat:
                    send_gcs_heartbeat()
                    next_heartbeat = time.monotonic() + 1
                # All selected motor outputs stay latched between updates.
                # Refresh the FC's shared timeout. Link/process loss stops the
                # entire session after COMMAND_LEASE, rather than running on.
                command_and_ack(motor, pwm, console)
    finally:
        stop_all("TEST ENDED - STOPPING ALL MOTORS")


# ============================================================
# MAIN MENU
# ============================================================

print("\n" + "=" * 65)
print("OCTACOPTER MOTOR TEST READY")
print("=" * 65)
print("1-8 = single motor | s = selected motors together | a = all together")
print("f/r direction is relative to ESC configuration; verify actual CW/CCW.")
print("E = emergency stop without Enter. Ctrl+C = stop and quit.")
print("Keep this terminal focused. Keyboard stop requires a working link.")
print("Neutral stops drive; it does not guarantee active electrical braking.")

try:
    with Console() as console:
        while True:
            try:
                print("\n---------------------------------------")
                choice = console.line("Motor 1-8, s, a, or q: ").lower()
                if choice == "q":
                    break
                if choice == "s":
                    motors = parse_motors(console.line("Motor numbers (example 1,3,5): "))
                elif choice == "a":
                    motors = list(range(1, NUMBER_OF_MOTORS + 1))
                else:
                    motors = parse_motors(choice)
                    if len(motors) != 1:
                        raise ValueError("Use s to select several motors.")
                direction = console.line("Direction f = forward, r = reverse [f]: ").lower() or "f"
                power_text = console.line(f"Power percent 0-100 [{TEST_POWER * 100:g}]: ")
                percent = float(power_text) if power_text else TEST_POWER * 100
                pwm = throttle_value(percent, direction)
                print(f"\nMotors: {motors}")
                print(f"Direction: {'forward' if direction == 'f' else 'reverse'}")
                print(f"Power: {percent:g}% | DShot-3D command: {pwm}")
                print(f"Duration: {TEST_TIME:g} seconds together (starts slightly staggered).")
                if console.line("Type RUN to start: ").upper() != "RUN":
                    print("Test cancelled.")
                    continue
                test_motors(motors, percent, direction, console)
            except EmergencyStop:
                stop_all("EMERGENCY STOP - ALL MOTORS")
                print("Emergency stop latched. No test can run until reset.")
                # E is ordinary text here: outputs have already been stopped,
                # and no motor commands are issued while awaiting this reset.
                while True:
                    reset = console.line(
                        "Type RESET to return to menu, or q to quit: ",
                        emergency_enabled=False,
                    ).upper()
                    if reset == "Q":
                        raise EOFError("Quit after emergency stop")
                    if reset == "RESET":
                        break
                    print("Emergency stop remains latched.")
            except (ValueError, RuntimeError) as exc:
                stop_all("TEST REFUSED / ABORTED")
                print(exc)
except (KeyboardInterrupt, EOFError):
    print("\nStop and quit requested.")
finally:
    try:
        stop_all("EXIT - STOPPING ALL MOTORS")
    finally:
        tx_connection.close()
        rx_connection.close()
        print("Connections closed.")
