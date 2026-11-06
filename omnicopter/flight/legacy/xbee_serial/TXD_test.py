import serial
import time

ser = serial.Serial("COM5", 57600)

for i in range(20):
    msg = f"TEST {i}\r\n".encode()
    print("Sending:", msg)
    ser.write(msg)
    ser.flush()
    time.sleep(0.5)

ser.close()