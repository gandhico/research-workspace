import socket
import time

# ============================================================
# SETTINGS
# ============================================================

PC_PORT = 14550
PICO_IP = "192.168.1.143"
PICO_PORT = 14550

TEST_MESSAGE = b"PICO_UART_LOOPBACK_TEST_123456789"


# ============================================================
# UDP SOCKET
# ============================================================

sock = socket.socket(
    socket.AF_INET,
    socket.SOCK_DGRAM
)

sock.setsockopt(
    socket.SOL_SOCKET,
    socket.SO_REUSEADDR,
    1
)

sock.bind(
    ("0.0.0.0", PC_PORT)
)

sock.settimeout(5)


print("=" * 60)
print("PICO W UART LOOPBACK TEST")
print("=" * 60)

print()
print("PC listening on UDP port:", PC_PORT)
print("Pico destination:", f"{PICO_IP}:{PICO_PORT}")

print()
print("Required wiring:")
print("Pico GP0 TX  --->  Pico GP1 RX")
print()

time.sleep(1)


# ============================================================
# SEND TEST DATA
# ============================================================

print("Sending:")
print(TEST_MESSAGE)

sock.sendto(
    TEST_MESSAGE,
    (PICO_IP, PICO_PORT)
)


# ============================================================
# WAIT FOR ECHO
# ============================================================

print()
print("Waiting for Pico UART echo...")

try:

    data, address = sock.recvfrom(2048)

    print()
    print("Received UDP packet from:", address)

    print("Received:")
    print(data)

    print()
    print("Sent bytes:    ", len(TEST_MESSAGE))
    print("Received bytes:", len(data))


    if data == TEST_MESSAGE:

        print()
        print("=" * 60)
        print("LOOPBACK TEST: PASS")
        print("=" * 60)

        print()
        print("The following path is working:")
        print()
        print("PC")
        print("  -> Wi-Fi UDP")
        print("  -> Pico")
        print("  -> Serial1 TX / GP0")
        print("  -> jumper")
        print("  -> Serial1 RX / GP1")
        print("  -> Pico")
        print("  -> Wi-Fi UDP")
        print("  -> PC")

    else:

        print()
        print("=" * 60)
        print("LOOPBACK TEST: PARTIAL / DATA MISMATCH")
        print("=" * 60)

        print()
        print("Data returned, but it does not match")
        print("the transmitted test message.")

        print()
        print("Expected:")
        print(TEST_MESSAGE)

        print()
        print("Received:")
        print(data)


except socket.timeout:

    print()
    print("=" * 60)
    print("LOOPBACK TEST: FAIL")
    print("=" * 60)

    print()
    print("Nothing came back from the Pico UART.")

    print()
    print("Check:")
    print("1. GP0 is connected directly to GP1")
    print("2. Pico firmware is running")
    print("3. Pico IP is still 192.168.1.143")
    print("4. Serial1 is configured for GP0 TX / GP1 RX")


finally:

    sock.close()

    print()
    print("Socket closed.")