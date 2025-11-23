# dsky_main.py
import time
import sys
import config
from agc import AgcClient
from hardware.interface import DskyHardware

def main():
    print("--- PiDSKY Phase 3 Driver ---")
    
    # 1. Initialize Hardware
    try:
        dsky = DskyHardware()
        print("[Main] Hardware Initialized")
    except Exception as e:
        print(f"[Error] Hardware init failed: {e}")
        sys.exit(1)

    # 2. Initialize Network
    agc = AgcClient()
    
    # 3. Connect Loop
    while not agc.connected:
        if agc.connect():
            break
        dsky.set_digit('V1', 21) # Show '0' on Verb to indicate waiting
        time.sleep(2)

    dsky.clear_all()
    print("[Main] System Ready. Starting Event Loop.")

    # 4. Event Loop
    try:
        while True:
            # --- A. Handle Network Input (Downlink) ---
            packets = agc.read() # Returns list of (channel, value)
            
            for channel, val in packets:
                # Channel 010: Digits
                if channel == config.CHAN_DISPLAY:
                    handle_display(dsky, val)
                
                # Channel 011: Lamps (DSKY Status)
                elif channel == config.CHAN_LAMPS:
                    # handle_lamps(dsky, val) # To be implemented with Blinkin Lights
                    pass
                
                # Channel 163: Flags (PROG, OPR ERR)
                elif channel == config.CHAN_FLAGS:
                    pass 

            # --- B. Handle Keypad Input (Uplink) ---
            # Check for physical key press
            key = dsky.get_key_event()
            if key:
                agc.send_key(key)
            
            # Check for auto-PRO release
            pro_release = dsky.check_pro_release()
            if pro_release:
                agc.send_key(pro_release)

            time.sleep(0.05) # Pulse delay

    except KeyboardInterrupt:
        print("\n[Main] Exiting...")
        dsky.clear_all()
        sys.exit(0)

def handle_display(dsky, value):
    """Parses Channel 10 words into digits."""
    # Extract fields (Logic from piDSKY4.py)
    row_id = (value >> 11) & 0x0F
    sign_bit = (value >> 10) & 0x01
    char_left = (value >> 5) & 0x1F
    char_right = value & 0x1F

    if row_id == 11: # M1, M2
        dsky.set_digit('M1', char_left)
        dsky.set_digit('M2', char_right)
    elif row_id == 10: # V1, V2
        dsky.set_digit('V1', char_left)
        dsky.set_digit('V2', char_right)
    elif row_id == 9: # N1, N2
        dsky.set_digit('N1', char_left)
        dsky.set_digit('N2', char_right)
    elif row_id == 8: # Digit 11
        dsky.set_digit('11', char_right)
    elif row_id == 7: # R1: 12, 13 + Sign
        dsky.set_digit('12', char_left)
        dsky.set_digit('13', char_right)
        dsky.set_digit('S1', "+" if sign_bit else " ")
    elif row_id == 6: # R1: 14, 15 - Sign
        dsky.set_digit('14', char_left)
        dsky.set_digit('15', char_right)
        if sign_bit: dsky.set_digit('S1', "-")
    elif row_id == 5: # R2: 21, 22 + Sign
        dsky.set_digit('21', char_left)
        dsky.set_digit('22', char_right)
        dsky.set_digit('S2', "+" if sign_bit else " ")
    elif row_id == 4: # R2: 23, 24 - Sign
        dsky.set_digit('23', char_left)
        dsky.set_digit('24', char_right)
        if sign_bit: dsky.set_digit('S2', "-")
    elif row_id == 3: # R2: 25, R3: 31
        dsky.set_digit('25', char_left)
        dsky.set_digit('31', char_right)
    elif row_id == 2: # R3: 32, 33 + Sign
        dsky.set_digit('32', char_left)
        dsky.set_digit('33', char_right)
        dsky.set_digit('S3', "+" if sign_bit else " ")
    elif row_id == 1: # R3: 34, 35 - Sign
        dsky.set_digit('34', char_left)
        dsky.set_digit('35', char_right)
        if sign_bit: dsky.set_digit('S3', "-")

if __name__ == "__main__":
    main()