"""Read-only board identification. Opens each Q8-USB board and reads its
serial-number string property. NO channel I/O -- does not read encoders,
does not write analog/digital outputs, does not touch motors. Safe to run
regardless of E-stop / amplifier / propeller-shield state.
"""
from quanser.hardware import HIL, HILError, StringProperty

for identifier in ["0", "1"]:
    try:
        card = HIL()
        card.open("q8_usb", identifier)
        try:
            serial = card.get_string_property(StringProperty.SERIAL_NUMBER, 64)
            print(f"q8_usb identifier={identifier}: serial={serial!r}")
        except HILError as ex:
            print(f"q8_usb identifier={identifier}: opened, but could not read serial: {ex.get_error_message()}")
        finally:
            card.close()
    except HILError as ex:
        print(f"q8_usb identifier={identifier}: could not open: {ex.get_error_message()}")
