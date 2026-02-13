import serial
import time
import os

# Lazy Arduino serial helper. Configure port via ARDUINO_PORT env var if needed.
_ARDUINO_PORT = os.getenv("ARDUINO_PORT", "/dev/cu.usbmodem1201")
_ARDUINO_BAUD = int(os.getenv("ARDUINO_BAUD", "9600"))
_ser = None


def _open_serial():
    global _ser
    if _ser is not None:
        return _ser
    try:
        _ser = serial.Serial(_ARDUINO_PORT, _ARDUINO_BAUD, timeout=1)
        time.sleep(2)
        print(f"Opened Arduino on {_ARDUINO_PORT} @{_ARDUINO_BAUD}")
    except Exception as e:
        print(f"Could not open Arduino serial {_ARDUINO_PORT}: {e}")
        _ser = None
    return _ser


def _send_raw(s: str):
    ser = _open_serial()
    if ser is None:
        return False
    try:
        ser.write(s.encode("utf-8"))
        ser.flush()
        return True
    except Exception as e:
        print(f"Failed to write to Arduino: {e}")
        return False


def send_wave_command():
    """Send the simple wave command. Arduino will run servo wave."""
    # terminate with newline so Arduino processes immediately
    ok = _send_raw("W\n")
    if ok:
        print("Sent WAVE command to Arduino")
    return ok


def send_lcd_message(line1: str, line2: str = ""):
    """Send a message to be displayed on the 16x2 LCD.

    Format: M<line1>|<line2>\n
    Lines will be truncated to 16 chars on the Arduino side.
    """
    # sanitize newlines
    l1 = line1.replace('\n', ' ') if line1 else ""
    l2 = line2.replace('\n', ' ') if line2 else ""
    payload = f"M{l1}|{l2}\n"
    ok = _send_raw(payload)
    if ok:
        print(f"Sent LCD message: '{l1}' / '{l2}'")
    return ok


def send_gesture(gesture_name: str, payload: dict | None = None):
    """High-level: send an appropriate LCD message and optional wave action for a gesture."""
    mapping = {
        "wave": ("Ciao,", "Nigger"),
        "thumbs_up": ("Grazie del", "like!"),
        "middle_finger": ("F*ck you", "Nigger"),
        "peace": ("Peace", "hello"),
        "open_palm": ("STOP!", ""),
        "yolo": ("Yolo", "Californiaaa!"),
    }

    # If the gesture is a count like '3 fingers' send that directly
    if gesture_name.endswith(" fingers"):
        txt = gesture_name
        send_lcd_message(txt, "")
        return True

    pair = mapping.get(gesture_name, (gesture_name.replace('_', ' ').title(), ""))
    sent = send_lcd_message(pair[0], pair[1])
    # For wave also trigger servo
    if gesture_name == "wave":
        send_wave_command()
    return sent

