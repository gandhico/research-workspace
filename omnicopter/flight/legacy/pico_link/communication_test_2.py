import time
from pymavlink import mavutil

# ============================================================
# SETTINGS
# ============================================================

UDP_PORT = 14550

# Number of GCS heartbeats sent as a visible PC -> Pico test
GCS_HEARTBEAT_COUNT = 5
GCS_HEARTBEAT_DELAY = 0.5


# ============================================================
# START
# ============================================================

print("=" * 65)
print("MAVLink UDP / Pico W / Cube Orange Diagnostic Test")
print("=" * 65)


# ============================================================
# RECEIVE CONNECTION
# Pico -> PC
# ============================================================

print(f"\nListening for MAVLink on UDP port {UDP_PORT}...")

rx_connection = mavutil.mavlink_connection(
    f"udpin:0.0.0.0:{UDP_PORT}",
    source_system=255,
    source_component=190,
)


# ============================================================
# WAIT FOR HEARTBEAT
# ============================================================

print("Waiting for Cube heartbeat...")

heartbeat = rx_connection.wait_heartbeat(timeout=15)

if heartbeat is None:
    rx_connection.close()
    raise TimeoutError(
        "No heartbeat received from Cube."
    )


# ============================================================
# GET CUBE IDS
# ============================================================

target_system = heartbeat.get_srcSystem()
target_component = heartbeat.get_srcComponent()

print("\n===== HEARTBEAT RECEIVED =====")

print("System ID:", target_system)
print("Component ID:", target_component)
print("Autopilot:", heartbeat.autopilot)
print("Vehicle type:", heartbeat.type)


# ============================================================
# MAVLINK VERSION / SIGNING INFORMATION
# ============================================================

print("\n===== MAVLINK PROTOCOL INFORMATION =====")

raw_packet = heartbeat.get_msgbuf()

mavlink_version = "Unknown"

if raw_packet and len(raw_packet) > 0:

    first_byte = raw_packet[0]

    if first_byte == 0xFD:
        mavlink_version = "MAVLink 2"

    elif first_byte == 0xFE:
        mavlink_version = "MAVLink 1"


print("Protocol:", mavlink_version)

try:
    heartbeat_signed = heartbeat.get_signed()
except Exception as error:
    heartbeat_signed = None
    print("Could not determine signing status:", error)

try:
    signing_link_id = heartbeat.get_link_id()
except Exception as error:
    signing_link_id = None
    print("Could not determine signing link ID:", error)


print("Heartbeat signed:", heartbeat_signed)
print("Signing link ID:", signing_link_id)


if heartbeat_signed is True:

    print()
    print("WARNING:")
    print("The Cube heartbeat contains a MAVLink2 signature.")
    print("Unsigned commands from this Python program may be rejected.")
    print("MAVLink signing is now a strong candidate for the problem.")

elif heartbeat_signed is False:

    print()
    print("The received heartbeat is NOT signed.")
    print("MAVLink signing is less likely to be the cause.")
    print("The Pico TX -> Cube RX path should be investigated next.")


# ============================================================
# LOCAL UDP INFORMATION
# ============================================================

print("\n===== LOCAL UDP INFORMATION =====")

try:
    print(
        "Local UDP socket:",
        rx_connection.port.getsockname()
    )
except Exception as error:
    print(
        "Could not read local UDP socket:",
        error
    )


# ============================================================
# DETECT PICO IP
# ============================================================

print("\n===== UDP CLIENT DETECTION =====")

clients = getattr(
    rx_connection,
    "clients",
    None
)

print("Known UDP clients:", clients)

pico_ip = None
pico_source_port = None


if clients:

    client_list = list(clients)

    if len(client_list) > 0:

        first_client = client_list[0]

        try:
            pico_ip = first_client[0]
            pico_source_port = first_client[1]

        except Exception:
            pass


if pico_ip is None:

    rx_connection.close()

    raise RuntimeError(
        "\nCould not automatically determine Pico IP.\n"
        "Look at the Pico Serial Monitor for:\n"
        "'Pico IP: xxx.xxx.xxx.xxx'"
    )


print("Detected Pico IP:", pico_ip)
print("Pico source UDP port:", pico_source_port)

print(
    f"Commands will be explicitly sent to "
    f"{pico_ip}:{UDP_PORT}"
)


# ============================================================
# CREATE EXPLICIT OUTPUT CONNECTION
# PC -> PICO
# ============================================================

print("\n===== CREATING PC -> PICO UDP CONNECTION =====")

tx_connection = mavutil.mavlink_connection(
    f"udpout:{pico_ip}:{UDP_PORT}",
    source_system=255,
    source_component=190,
)

print(
    f"UDP output connection created: "
    f"PC -> {pico_ip}:{UDP_PORT}"
)


# ============================================================
# TEST 0
# PC -> PICO TRANSMISSION
# ============================================================

print("\n===== TEST 0: PC -> PICO UDP TRANSMISSION =====")

print(
    f"Sending {GCS_HEARTBEAT_COUNT} "
    "GCS heartbeats..."
)

print()
print("WATCH THE PICO SERIAL MONITOR.")
print("The 'PC -> Cube' byte counter should increase.")
print()


for i in range(GCS_HEARTBEAT_COUNT):

    tx_connection.mav.heartbeat_send(
        mavutil.mavlink.MAV_TYPE_GCS,
        mavutil.mavlink.MAV_AUTOPILOT_INVALID,
        0,
        0,
        mavutil.mavlink.MAV_STATE_ACTIVE,
    )

    print(
        f"GCS heartbeat "
        f"{i + 1}/{GCS_HEARTBEAT_COUNT} sent"
    )

    time.sleep(GCS_HEARTBEAT_DELAY)


print("\nFinished GCS heartbeat transmission.")

time.sleep(1)


# ============================================================
# TEST 1
# REQUEST MAV_SYSID
# ============================================================

print("\n===== TEST 1: PARAMETER REQUEST =====")

print(
    f"Requesting MAV_SYSID from "
    f"system {target_system}, "
    f"component {target_component}"
)


tx_connection.mav.param_request_read_send(
    target_system,
    target_component,
    b"MAV_SYSID",
    -1,
)


print("PARAM_REQUEST_READ sent.")

parameter_received = False

deadline = time.time() + 7


while time.time() < deadline:

    message = rx_connection.recv_match(
        blocking=True,
        timeout=1
    )

    if message is None:
        continue

    message_type = message.get_type()


    # --------------------------------------------------------
    # PARAMETER VALUE
    # --------------------------------------------------------

    if message_type == "PARAM_VALUE":

        try:

            if isinstance(message.param_id, bytes):

                parameter_name = (
                    message.param_id
                    .decode("utf-8")
                    .rstrip("\x00")
                )

            else:

                parameter_name = (
                    str(message.param_id)
                    .rstrip("\x00")
                )

        except Exception:

            parameter_name = str(message.param_id)


        print(
            "PARAM_VALUE received:",
            parameter_name,
            "=",
            message.param_value
        )


        if parameter_name == "MAV_SYSID":

            parameter_received = True

            print(
                "\nSUCCESS: Cube responded "
                "to parameter request!"
            )

            break


    # --------------------------------------------------------
    # STATUS TEXT
    # --------------------------------------------------------

    elif message_type == "STATUSTEXT":

        try:

            if isinstance(message.text, bytes):

                text = (
                    message.text
                    .decode("utf-8")
                    .rstrip("\x00")
                )

            else:

                text = str(message.text)

        except Exception:

            text = str(message.text)


        print(
            "STATUSTEXT:",
            text
        )


if not parameter_received:

    print(
        "\nFAILED: No MAV_SYSID "
        "PARAM_VALUE received."
    )


# ============================================================
# TEST 2
# REQUEST AUTOPILOT_VERSION
# ============================================================

print("\n===== TEST 2: AUTOPILOT_VERSION =====")

command = mavutil.mavlink.MAV_CMD_REQUEST_MESSAGE


tx_connection.mav.command_long_send(
    target_system,
    target_component,
    command,
    0,  # Confirmation

    # param1 = message ID requested
    mavutil.mavlink.MAVLINK_MSG_ID_AUTOPILOT_VERSION,

    0,
    0,
    0,
    0,
    0,
    0,
)


print("MAV_CMD_REQUEST_MESSAGE sent.")
print("Requested AUTOPILOT_VERSION.")


deadline = time.time() + 8

received_ack = False
received_version = False


while time.time() < deadline:

    message = rx_connection.recv_match(
        blocking=True,
        timeout=1
    )

    if message is None:
        continue

    message_type = message.get_type()


    # --------------------------------------------------------
    # COMMAND ACKNOWLEDGEMENT
    # --------------------------------------------------------

    if message_type == "COMMAND_ACK":

        print("\nCOMMAND_ACK received:")

        print(
            "Command:",
            message.command
        )

        print(
            "Result code:",
            message.result
        )


        if message.command == command:

            received_ack = True

            result_enum = (
                mavutil.mavlink.enums[
                    "MAV_RESULT"
                ].get(message.result)
            )


            if result_enum is not None:

                print(
                    "Result:",
                    result_enum.name
                )

            else:

                print(
                    "Unknown result:",
                    message.result
                )


    # --------------------------------------------------------
    # AUTOPILOT VERSION
    # --------------------------------------------------------

    elif message_type == "AUTOPILOT_VERSION":

        received_version = True

        print(
            "\nSUCCESS: "
            "AUTOPILOT_VERSION received!"
        )

        print(message)


    # --------------------------------------------------------
    # STATUS TEXT
    # --------------------------------------------------------

    elif message_type == "STATUSTEXT":

        try:

            if isinstance(message.text, bytes):

                text = (
                    message.text
                    .decode("utf-8")
                    .rstrip("\x00")
                )

            else:

                text = str(message.text)

        except Exception:

            text = str(message.text)


        print(
            "STATUSTEXT:",
            text
        )


    if received_ack and received_version:
        break


if not received_ack:

    print(
        "\nNo COMMAND_ACK received."
    )


if not received_version:

    print(
        "No AUTOPILOT_VERSION received."
    )


# ============================================================
# TEST 3
# SAMPLE MORE INCOMING PACKETS FOR SIGNING
# ============================================================

print("\n===== TEST 3: INCOMING MAVLINK SIGNING SAMPLE =====")

print(
    "Sampling incoming Cube messages for 5 seconds..."
)

sample_deadline = time.time() + 5

signed_messages = 0
unsigned_messages = 0
mavlink1_messages = 0
mavlink2_messages = 0
total_messages = 0


while time.time() < sample_deadline:

    message = rx_connection.recv_match(
        blocking=True,
        timeout=0.5
    )

    if message is None:
        continue

    if message.get_type() == "BAD_DATA":
        continue


    total_messages += 1

    packet = message.get_msgbuf()


    if packet and len(packet) > 0:

        if packet[0] == 0xFD:
            mavlink2_messages += 1

        elif packet[0] == 0xFE:
            mavlink1_messages += 1


    try:

        if message.get_signed():

            signed_messages += 1

        else:

            unsigned_messages += 1

    except Exception:

        pass


print("\nSigning sample results:")

print(
    "Total messages:",
    total_messages
)

print(
    "MAVLink 1 messages:",
    mavlink1_messages
)

print(
    "MAVLink 2 messages:",
    mavlink2_messages
)

print(
    "Signed messages:",
    signed_messages
)

print(
    "Unsigned messages:",
    unsigned_messages
)


# ============================================================
# FINAL SUMMARY
# ============================================================

print("\n")
print("=" * 65)
print("TEST SUMMARY")
print("=" * 65)

print(
    "Cube -> PC heartbeat:       PASS"
)

print(
    "PC -> Pico destination:    "
    f"{pico_ip}:{UDP_PORT}"
)

print(
    "Initial MAVLink protocol:  ",
    mavlink_version
)

print(
    "Initial heartbeat signed:  ",
    heartbeat_signed
)

print(
    "Signing link ID:           ",
    signing_link_id
)


if parameter_received:

    print(
        "Parameter request:        PASS"
    )

else:

    print(
        "Parameter request:        FAIL"
    )


if received_ack:

    print(
        "Command acknowledgement: PASS"
    )

else:

    print(
        "Command acknowledgement: FAIL"
    )


if received_version:

    print(
        "AUTOPILOT_VERSION:        PASS"
    )

else:

    print(
        "AUTOPILOT_VERSION:        FAIL"
    )


print(
    "Signed incoming messages:  ",
    signed_messages
)

print(
    "Unsigned incoming messages:",
    unsigned_messages
)

print("=" * 65)


# ============================================================
# INTERPRETATION
# ============================================================

print("\n===== INTERPRETATION =====")


if signed_messages > 0 or heartbeat_signed is True:

    print()
    print("MAVLink signing was detected.")
    print()
    print(
        "The Cube is sending signed MAVLink2 packets."
    )

    print(
        "Your Python TX connection is currently not "
        "configured with the Cube's signing key."
    )

    print(
        "This can cause ArduPilot to ignore commands "
        "even though telemetry is received."
    )


elif (
    not parameter_received
    and not received_ack
):

    print()
    print(
        "Incoming MAVLink messages appear unsigned."
    )

    print(
        "PC -> Pico UDP communication has already "
        "been verified by the Pico byte counter."
    )

    print()
    print(
        "The next area to test is:"
    )

    print(
        "Pico GP0 TX -> Cube TELEM RX"
    )

    print()
    print(
        "Recommended next test:"
    )

    print(
        "Disconnect Cube TX/RX and perform a "
        "Pico GP0 -> GP1 UART loopback test."
    )


elif parameter_received:

    print()
    print(
        "Bidirectional MAVLink communication "
        "is working."
    )


# ============================================================
# CLOSE
# ============================================================

tx_connection.close()
rx_connection.close()

print("\nConnections closed.")