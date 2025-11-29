import sys
import os
from inputs import get_gamepad, UnpluggedError

# This clears the terminal screen (Linux/Mac vs Windows)
def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

print("--- INPUT VISUALIZER ---")
print("Move sticks/buttons to identify them.")
print("Press CTRL+C to exit.")
print("Waiting for data...")

state = {}

try:
    while True:
        events = get_gamepad()
        should_refresh = False
        
        for event in events:
            # Only track Absolute axes (Sticks/Triggers) and Keys (Buttons)
            if event.ev_type in ['Absolute', 'Key']:
                # Update the state dictionary with the new value
                state[event.code] = event.state
                should_refresh = True
        
        # Only redraw the screen if something changed
        if should_refresh:
            clear_screen()
            print("--- DETECTED INPUTS ---")
            # Sort keys so they don't jump around
            for code in sorted(state.keys()):
                value = state[code]
                
                # Visual bar for analog axes
                bar = ""
                if "ABS" in code:
                    # Simple graphic representation
                    # Assuming typical range -32k to 32k OR 0 to 255
                    # This is just a visual aid, math doesn't need to be perfect
                    if abs(value) > 256: 
                        # Likely 16-bit (-32768 to 32767)
                        norm = (value + 32768) / 65535
                    else: 
                        # Likely 8-bit (0 to 255)
                        norm = value / 255
                    
                    fill = int(norm * 20)
                    bar = f"[{'#' * fill}{'-' * (20 - fill)}]"

                print(f"{code:<20}: {value:<10} {bar}")

except KeyboardInterrupt:
    print("\nExiting.")
except UnpluggedError:
    print("\nError: No gamepad found.")