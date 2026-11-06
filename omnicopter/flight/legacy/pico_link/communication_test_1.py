import time
from pymavlink import mavutil

UDP_PORT = 14550

print(f"Listening for MAVLink on UDP port {UDP_PORT}...")

connection = mavutil.mavlink_connection(
    f"udpin:0.0.0.0:{UDP_PORT}",
    source_system=255,
    source_component=190,
)

heartbeat = connection.wait_heartbeat(timeout=15)

if heartbeat is None:
    raise TimeoutError(
        "No heartbeat received. Check that Mission Planner is closed."
    )

print(
    "Connected to system",
    connection.target_system,
    "component",
    connection.target_component,
)

# Advertise this Python program as a ground-control component.
connection.mav.heartbeat_send(
    mavutil.mavlink.MAV_TYPE_GCS,
    mavutil.mavlink.MAV_AUTOPILOT_INVALID,
    0,
    0,
    mavutil.mavlink.MAV_STATE_ACTIVE,
)

# Safely request AUTOPILOT_VERSION.
command = mavutil.mavlink.MAV_CMD_REQUEST_MESSAGE

connection.mav.command_long_send(
    connection.target_system,
    connection.target_component,
    command,
    0,  # Confirmation
    mavutil.mavlink.MAVLINK_MSG_ID_AUTOPILOT_VERSION,
    0,
    0,
    0,
    0,
    0,
    0,
)

print("AUTOPILOT_VERSION request sent")

deadline = time.time() + 10
received_ack = False
received_version = False

while time.time() < deadline:
    message = connection.recv_match(blocking=True, timeout=1)

    if message is None:
        continue

    message_type = message.get_type()

    if (
        message_type == "COMMAND_ACK"
        and message.command == command
    ):
        received_ack = True

        result = mavutil.mavlink.enums["MAV_RESULT"].get(
            message.result
        )

        result_name = (
            result.name if result is not None else str(message.result)
        )

        print("Command acknowledgement:", result_name)

    elif message_type == "AUTOPILOT_VERSION":
        received_version = True
        print("Received AUTOPILOT_VERSION:")
        print(message)

    if received_ack and received_version:
        break

if not received_ack:
    print("No command acknowledgement received")

if not received_version:
    print("No AUTOPILOT_VERSION message received")

connection.close()