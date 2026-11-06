import serial

try:
    s = serial.Serial("COM5", 57600, timeout=1)
    print("SUCCESS: COM5 opened")
    s.close()
except Exception as e:
    print("FAILED:", repr(e))