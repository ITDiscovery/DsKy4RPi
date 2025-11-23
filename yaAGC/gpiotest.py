import sys
import time
import gpiod
from gpiod.line import Direction, Value

# Default chip based on your previous config
CHIP_PATH = "/dev/gpiochip4"

def main():
    if len(sys.argv) < 2:
        print(f"Usage: python3 pin_verify.py <BCM_PIN_NUMBER>")
        print("Example: python3 pin_verify.py 11")
        sys.exit(1)

    try:
        target_pin = int(sys.argv[1])
    except ValueError:
        print("Error: Pin number must be an integer.")
        sys.exit(1)

    print(f"--- PIN VERIFICATION TOOL ---")
    print(f"Target: GPIO {target_pin} on {CHIP_PATH}")
    print(f"Action: Toggling HIGH/LOW every 2 seconds.")
    print("Use your multimeter/LED now.")
    print("Press Ctrl+C to stop.\n")

    try:
        # Configure the single pin as Output
        config = {
            target_pin: gpiod.LineSettings(
                direction=Direction.OUTPUT, 
                output_value=Value.INACTIVE
            )
        }

        # Request the line
        with gpiod.request_lines(
            CHIP_PATH,
            consumer="pin_verify",
            config=config
        ) as request:
            
            while True:
                # Set HIGH
                request.set_value(target_pin, Value.ACTIVE)
                print(f"GPIO {target_pin}: HIGH (3.3V) ***")
                time.sleep(2)

                # Set LOW
                request.set_value(target_pin, Value.INACTIVE)
                print(f"GPIO {target_pin}: LOW  (0V)")
                time.sleep(2)

    except OSError as e:
        print(f"\nError: Could not access GPIO {target_pin}.")
        print("Check if the pin is already in use by another script.")
        print(f"System message: {e}")
    except KeyboardInterrupt:
        print("\nTest stopped.")

if __name__ == "__main__":
    main()