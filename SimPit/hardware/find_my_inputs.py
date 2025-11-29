from inputs import get_gamepad
import sys

print("--- RAW INPUT DEBUGGER ---")
print("1. Move your joystick ONE axis at a time.")
print("2. Note the 'Code' that appears (e.g., ABS_X, ABS_RZ).")
print("3. Press CTRL+C to stop.")
print("--------------------------")

try:
    while True:
        events = get_gamepad()
        for event in events:
            # We only care about "Absolute" movement (sticks/sliders)
            if event.ev_type == 'Absolute':
                print(f"Code: {event.code:<15} State: {event.state}")
except KeyboardInterrupt:
    sys.exit(0)
except Exception as e:
    print(f"Error: {e}")