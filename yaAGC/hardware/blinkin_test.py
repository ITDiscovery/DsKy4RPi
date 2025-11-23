#!/usr/bin/env python3
"""
blinkin_test.py
Final Vetting Tool for IMSAI/Blinkin' Hardware.
Commands: monitor, on, off, walk, set <val>
"""

import time
import sys
import argparse
from blinkin_driver import BlinkinBoard

def parse_args():
    parser = argparse.ArgumentParser(description="Blinkin' Board Hardware Test")
    
    # LED Pins (Default: 21, 20, 16)
    parser.add_argument("--led-clk", type=int, default=21, help="LED Clock Pin")
    parser.add_argument("--led-latch", type=int, default=20, help="LED Latch Pin")
    parser.add_argument("--led-data", type=int, default=16, help="LED Data Pin")
    parser.add_argument("--led-chips", type=int, default=5, help="Num LED Chips (Default: 5)")
    
    # Switch Pins (Default: 17, 22, 27)
    parser.add_argument("--sw-clk", type=int, default=17, help="Switch Clock Pin")
    parser.add_argument("--sw-latch", type=int, default=22, help="Switch Latch Pin")
    parser.add_argument("--sw-data", type=int, default=27, help="Switch Data Pin")
    parser.add_argument("--sw-chips", type=int, default=4, help="Num Switch Chips (Default: 4)")
    
    return parser.parse_args()

def print_menu():
    print("\n--- Command Menu ---")
    print("  monitor         -> Watch switches in real-time (Ctrl+C to stop)")
    print("  on              -> Turn ALL LEDs ON")
    print("  off             -> Turn ALL LEDs OFF")
    print("  walk            -> Walk a single bit (0.5s delay)")
    print("  set <hex/int>   -> Set specific pattern (e.g. 'set FF' or 'set 255')")
    print("  q               -> Quit")

def do_monitor(board: BlinkinBoard):
    print("\n--- MONITOR MODE ---")
    print("Press switches to see changes. Press Ctrl+C to return to menu.")
    last_val = -1
    try:
        while True:
            val = board.read_switches()
            if val != last_val:
                # Print Hex and Binary (32-bit padded)
                print(f"Switches: {hex(val)}  (Bin: {val:032b})")
                last_val = val
            time.sleep(0.05) # 20Hz polling
    except KeyboardInterrupt:
        print("\nStopped.")

def do_walk(board: BlinkinBoard):
    print(f"\nWalking {board.num_led_bits} bits (0.5s delay)...")
    try:
        for i in range(board.num_led_bits):
            board.clear_leds()
            board.set_led(i, True)
            board.update_leds()
            print(f"\rBit {i} ON", end="")
            time.sleep(0.5) 
        print("\nDone.")
    except KeyboardInterrupt:
        print("\nCancelled.")
    finally:
        board.clear_leds()
        board.update_leds()

def main():
    args = parse_args()
    print("Initializing Driver...")
    
    try:
        with BlinkinBoard(
            led_clk=args.led_clk, led_latch=args.led_latch, led_data=args.led_data,
            num_led_chips=args.led_chips,
            sw_clk=args.sw_clk, sw_latch=args.sw_latch, sw_data=args.sw_data,
            num_switch_chips=args.sw_chips
        ) as board:
            
            # Start clean
            board.clear_leds()
            board.update_leds()
            print("Hardware Ready.")
            
            while True:
                try:
                    cmd_raw = input("\nBlinkin> ").strip().lower()
                    parts = cmd_raw.split()
                    if not parts: continue
                    cmd = parts[0]

                    if cmd in ['q', 'exit', 'quit']:
                        break
                        
                    elif cmd == 'monitor':
                        do_monitor(board)
                        
                    elif cmd == 'on':
                        board.fill_leds()
                        board.update_leds()
                        print("All LEDs ON.")

                    elif cmd == 'off':
                        board.clear_leds()
                        board.update_leds()
                        print("All LEDs OFF.")
                        
                    elif cmd == 'walk':
                        do_walk(board)

                    elif cmd == 'set':
                        if len(parts) < 2:
                            print("Usage: set <value> (e.g. 'set FF' or 'set 123')")
                            continue
                        try:
                            # Auto-detect base (0x for hex, plain for int)
                            val_str = parts[1]
                            val = int(val_str, 16) if 'x' not in val_str and any(c in 'abcdef' for c in val_str) else int(val_str, 0)
                            
                            board.set_all_leds(val)
                            board.update_leds()
                            print(f"Set LEDs to {hex(val)}")
                        except ValueError:
                            print("Invalid number format.")

                    else:
                        print("Unknown command.")
                        print_menu()

                except KeyboardInterrupt:
                    print("\nQuitting.")
                    break
                    
    except Exception as e:
        print(f"\nCRITICAL ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()