from pymavlink import mavutil
import time

PORT = "COM5"
BAUD = 57600

print(f"Opening {PORT} at {BAUD} baud...")

master = mavutil.mavlink_connection(
    PORT,
    baud=BAUD
)

print("Waiting up to 15 seconds for a MAVLink heartbeat...")

heartbeat = master.recv_match(
    type="HEARTBEAT",
    blocking=True,
    timeout=15
)

if heartbeat:
    print("\nSUCCESS!")
    print("MAVLink heartbeat received.")
    print(f"System ID: {master.target_system}")
    print(f"Component ID: {master.target_component}")
    print(heartbeat)
else:
    print("\nFAILED.")
    print("No MAVLink heartbeat received on COM5.")