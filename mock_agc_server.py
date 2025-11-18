#!/usr/bin/python3
import socket
import time
import datetime

# --- TIMESTAMP LOGGER ---
def log(msg):
    """Prints a message with a timestamp."""
    now = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print(f"[{now}] {msg}")
# --------------------------

HOST = 'localhost'
PORT = 19798 

def create_packet(channel, value):
    """Helper function to correctly build a 4-byte yaAGC packet."""
    b1 = 0x00 | ((channel >> 3) & 0x0F)
    b2 = 0x40 | ((channel << 3) & 0x38) | ((value >> 12) & 0x07)
    b3 = 0x80 | ((value >> 6) & 0x3F)
    b4 = 0xC0 | (value & 0x3F)
    return bytes([b1, b2, b3, b4])

# --- Test Packets ---
test_packets = [
    create_packet(8, 20509), # " 8" on Verb
    create_packet(8, 18553), # "12" on Noun
    create_packet(8, 24836), # VEL/PROG lamps
    create_packet(9, 4),     # UPLINK ACTY
    create_packet(115, 72),  # TEMP/OPR ERR
]
clear_packets = [
    create_packet(8, 0),
    create_packet(9, 0),
    create_packet(115, 0),
]

log(f"Mock AGC Server (Interactive) starting on {HOST}:{PORT}...")

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((HOST, PORT))
    s.listen()
    log("Waiting for DSKY to connect...")
    
    conn, addr = s.accept()
    with conn:
        log(f"DSKY connected from {addr}")
        conn.setblocking(False) 

        packet_index = 0
        clearing_index = 0
        last_packet_time = time.time()
        packet_delay = 2.0 # Slow pace so you can see what's happening

        try:
            while True:
                # 1. RECV DATA (INPUT MODE)
                try:
                    while True: # Read all available data
                        data = conn.recv(1024) 
                        if not data:
                            raise socket.error("Client disconnected") 
                        
                        # --- THIS IS THE NEW PART ---
                        # Print the raw hex of what the DSKY sent us.
                        # Ideally, if you press a key, data will show up here.
                        log(f" << RECEIVED KEY DATA: {data.hex()}")
                        # ----------------------------

                except socket.error as e:
                    if e.errno == 11 or e.errno == 115: 
                        pass # No data, this is normal
                    else:
                        raise # Real error

                # 2. SEND DATA (OUTPUT MODE)
                # We'll just cycle the lights slowly so you know it's alive
                now = time.time()
                if (now - last_packet_time) > packet_delay:
                    
                    if packet_index < len(test_packets):
                        packet = test_packets[packet_index]
                        log(f" >> Sending packet {packet_index+1}")
                        conn.sendall(packet)
                        packet_index += 1
                        last_packet_time = now
                    
                    elif clearing_index < len(clear_packets):
                        if clearing_index == 0:
                            log(" >> Clearing lamps...")
                        packet = clear_packets[clearing_index]
                        conn.sendall(packet)
                        clearing_index += 1
                        last_packet_time = now
                    
                    else:
                        # Restart the light show
                        packet_index = 0
                        clearing_index = 0
                        log(" >> Restarting light cycle...")

                time.sleep(0.01) 
        
        except socket.error as e:
            if e.errno == 32: # Broken pipe
                log("Pi-DSKY disconnected early.")
            elif "Client disconnected" in str(e):
                log("Pi-DSKY disconnected.")
            else:
                log(f"Socket error: {e}")

log("Mock AGC Server shutting down.")