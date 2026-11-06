import serial
import time

PORT = "COM5"
BAUD = 57600

ser = serial.Serial(
    PORT,
    BAUD,
    timeout=0.2,
    rtscts=False,
    dsrdtr=False,
    xonxoff=False
)

print(f"Listening to {PORT} at {BAUD}...")
print("Power the Cube and leave the XBee link connected.\n")

end_time = time.time() + 15
total = 0

while time.time() < end_time:
    waiting = ser.in_waiting

    if waiting:
        data = ser.read(waiting)
        total += len(data)

        print(f"Received {len(data)} bytes:")
        print(data.hex(" "))
    else:
        time.sleep(0.05)

ser.close()

print(f"\nTOTAL RECEIVED: {total} bytes")