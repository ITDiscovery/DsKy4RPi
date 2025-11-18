#!/usr/bin/python3
"""
File-Based Mock AGC Server with Physics Engine
Reads commands from 'landing.txt' and simulates flight data.

UPDATED: Fixed R1/R2 display to show full 5-digit precision.
"""
import socket
import time
import datetime
import os

HOST = 'localhost'
PORT = 19798

def log(msg):
    now = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print(f"[{now}] {msg}")

# --- Protocol Helpers ---
def create_packet(channel, value):
    b1 = 0x00 | ((channel >> 3) & 0x0F)
    b2 = 0x40 | ((channel << 3) & 0x38) | ((value >> 12) & 0x07)
    b3 = 0x80 | ((value >> 6) & 0x3F)
    b4 = 0xC0 | (value & 0x3F)
    return bytes([b1, b2, b3, b4])

def s_to_d(s):
    d = {' ': 0, '0': 21, '1': 3, '2': 25, '3': 27, '4': 15,
         '5': 30, '6': 28, '7': 19, '8': 29, '9': 31, '-': 0}
    return d.get(s, 0)

def create_display_packet(aaaa, c1, c2):
    value = (int(aaaa) << 11) | (s_to_d(c1) << 5) | s_to_d(c2)
    return create_packet(0o10, value)

def create_lamp_packet(lamp_name, state):
    state = int(state)
    if lamp_name == "PROG":    return create_packet(0o10, (12<<11) | (0x100 if state else 0))
    if lamp_name == "VEL":     return create_packet(0o10, (12<<11) | (0x04 if state else 0))
    if lamp_name == "UPLINK":  return create_packet(0o11, 0x04 if state else 0)
    if lamp_name == "RESTART": return create_packet(0o163, 0o200 if state else 0)
    if lamp_name == "TEMP":    return create_packet(0o163, 0x08 if state else 0)
    return b''

# --- Physics/Display Helpers ---
def update_r1_r2(conn, alt, vel):
    """
    Formats Altitude into R1 and Velocity into R2 with 5-digit precision.
    """
    # --- R1 (Altitude) ---
    # 5 Digits. Uses Reg 8, 7, 6.
    # Format: 50000 -> "50000"
    s_alt = f"{int(alt):05}"[-5:] 
    conn.sendall(create_display_packet(8, s_alt[0], s_alt[1]))
    conn.sendall(create_display_packet(7, s_alt[2], s_alt[3]))
    conn.sendall(create_display_packet(6, s_alt[4], " ")) 

    # --- R2 (Velocity) ---
    # 5 Digits. Uses Reg 5, 4, and the High Nibble of Reg 3.
    # Format: 05500 -> "05500"
    s_vel = f"{int(abs(vel)):05}"[-5:]
    conn.sendall(create_display_packet(5, s_vel[0], s_vel[1]))
    conn.sendall(create_display_packet(4, s_vel[2], s_vel[3]))
    
    # Register 3 is shared: [R2_Digit_5] [R3_Digit_1]
    # For this sim, we assume R3 Digit 1 is '0' or Space.
    conn.sendall(create_display_packet(3, s_vel[4], " "))

def run_simulation(conn, duration, start_alt, end_alt, start_vel, end_vel):
    """Interpolates Altitude and Velocity over Duration."""
    start_time = time.time()
    duration = float(duration)
    
    # --- FIX: Convert string inputs to floats immediately ---
    start_alt = float(start_alt)
    end_alt = float(end_alt)
    start_vel = float(start_vel)
    end_vel = float(end_vel)
    # --------------------------------------------------------
    
    # Send initial state immediately
    update_r1_r2(conn, start_alt, start_vel)
    
    while True:
        now = time.time()
        elapsed = now - start_time
        
        if elapsed >= duration:
            break # Done
            
        progress = elapsed / duration
        
        # Calculate current physics (Now using the pre-converted floats)
        cur_alt = start_alt + (end_alt - start_alt) * progress
        cur_vel = start_vel + (end_vel - start_vel) * progress
        
        # Update Display
        update_r1_r2(conn, cur_alt, cur_vel)
        
        # Check for Input (Keep connection alive)
        try:
            while True:
                data = conn.recv(1024)
                if not data: raise socket.error("Client disconnected")
                log(f"<< KEY INPUT: {data.hex()}")
        except socket.error as e:
            if e.errno not in [11, 115]: raise
        
        time.sleep(0.1) # Update 10 times a second (Smooth!)

# --- File Parser ---
def run_script(conn, filename):
    log(f"Running script: {filename}")
    with open(filename, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"): continue
            
            parts = [p.strip() for p in line.split(',')]
            cmd = parts[0].upper()

            if cmd == "LOG":
                log(parts[1])
            
            elif cmd == "WAIT":
                # Re-using the simulation logic for WAIT to keep display alive
                run_simulation(conn, parts[1], 0, 0, 0, 0) 
            
            elif cmd == "SIMULATE":
                # SIMULATE, Duration, StartAlt, EndAlt, StartVel, EndVel
                run_simulation(conn, parts[1], parts[2], parts[3], parts[4], parts[5])

            elif cmd == "DISP":
                pkt = create_display_packet(parts[1], parts[2], parts[3])
                conn.sendall(pkt)
                time.sleep(0.02)
            
            elif cmd == "LAMP":
                pkt = create_lamp_packet(parts[1], parts[2])
                if pkt: conn.sendall(pkt)

# --- Main Server ---
log(f"Server starting on {HOST}:{PORT}...")
try:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen()
        
        while True:
            log("Waiting for Pi-DSKY to connect...")
            try:
                conn, addr = s.accept()
                with conn:
                    log(f"Connected: {addr}")
                    conn.setblocking(False)
                    
                    run_script(conn, "landing.txt")
                    
                    log("Script complete. Listening for keys...")
                    while True:
                        try:
                           data = conn.recv(1024)
                           if not data: break
                           log(f"<< KEY INPUT: {data.hex()}")
                        except: pass
                        time.sleep(0.1)

            except socket.error as e:
                log(f"Disconnect/Error: {e}")
            except Exception as e:
                log(f"Script Error: {e}")

except KeyboardInterrupt:
    log("Shutting down.")