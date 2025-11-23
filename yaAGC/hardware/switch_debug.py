"""
switch_debug.py
Raw Bit Inspector for 74HC165 Input Chains.
"""
import gpiod
import time
import sys
from gpiod.line import Direction, Value

# --- CONFIG (Matches your updates) ---
PIN_CLK = 17
PIN_DATA = 27
PIN_LATCH = 22
CHIP_PATH = "/dev/gpiochip4"
READ_COUNT = 32  # Reading 32 bits to be safe (4 chips worth)

def main():
    print(f"--- 74HC165 RAW DEBUG ---")
    print(f"CLK: {PIN_CLK} | DATA: {PIN_DATA} | LATCH: {PIN_LATCH}")
    print(f"Reading {READ_COUNT} bits per cycle.")
    print("Press Ctrl+C to quit.\n")

    try:
        # Setup Lines
        config = {
            PIN_CLK: gpiod.LineSettings(direction=Direction.OUTPUT, output_value=Value.INACTIVE),
            PIN_LATCH: gpiod.LineSettings(direction=Direction.OUTPUT, output_value=Value.ACTIVE),
            PIN_DATA: gpiod.LineSettings(direction=Direction.INPUT)
        }

        with gpiod.request_lines(CHIP_PATH, consumer="sw_debug", config=config) as request:
            while True:
                # 1. PULSE LATCH (Capture Inputs)
                # Active LOW pulse
                request.set_value(PIN_LATCH, Value.INACTIVE) 
                # time.sleep(0.000001) # Tiny delay for stability
                request.set_value(PIN_LATCH, Value.ACTIVE)

                # 2. READ LOOP
                bits = []
                for i in range(READ_COUNT):
                    # Read Data Pin
                    val = request.get_value(PIN_DATA)
                    bits.append(1 if val == Value.ACTIVE else 0)

                    # Pulse Clock (Rising Edge shifts next bit in)
                    request.set_value(PIN_CLK, Value.ACTIVE)
                    request.set_value(PIN_CLK, Value.INACTIVE)

                # 3. DISPLAY
                # Group into bytes for readability
                bit_str = "".join(str(b) for b in bits)
                
                # Visual logic: 1 is usually "Open" (Pull-up), 0 is "Pressed" (Grounded)
                # We will print raw first.
                sys.stdout.write(f"\rRaw Stream: {bit_str}  [Press a button!]")
                sys.stdout.flush()
                
                time.sleep(0.1)

    except KeyboardInterrupt:
        print("\n\nTest Complete.")
    except Exception as e:
        print(f"\nError: {e}")

if __name__ == "__main__":
    main()