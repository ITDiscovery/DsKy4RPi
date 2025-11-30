import socket
import threading
import time

class OrbiterClient:
    def __init__(self, host='192.168.2.229', port=37777):
        # Configuration
        self.host = host
        self.port = port
        
        # Shared Telemetry (Thread-Safe enough for visualization)
        self.pitch = 0.0
        self.yaw = 0.0
        self.roll = 0.0
        
        # Flags
        self.connected = False
        self.running = True
        self.sock = None
        
        # Start the background listener
        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._thread.start()

    def _connect(self):
        """Establishes the TCP connection to the Windows PC."""
        try:
            # Create a TCP/IP socket
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(2.0) # 2 second timeout for connection attempts
            self.sock.connect((self.host, self.port))
            print(f"[NET] Connected to Orbiter at {self.host}:{self.port}")
            self.connected = True
            return True
        except Exception as e:
            print(f"[NET] Connection failed: {e}")
            self.connected = False
            return False

    def _worker(self):
        """Robust Background loop to fetch data."""
        while self.running:
            if not self.connected:
                self._connect()
                time.sleep(2)
                continue

            try:
                # 1. Send Request (Batch)
                msg = b'FOCUS:Pitch\r\nFOCUS:Heading\r\nFOCUS:Bank\r\n'
                self.sock.sendall(msg)
                
                # 2. Receive Data (Drain the buffer)
                # We loop to catch split packets
                full_response = ""
                try:
                    while True:
                        # Non-blocking peek/read logic is complex in Python threading.
                        # Simplest robust way for this setup: Read once with a short timeout,
                        # or just read a larger chunk.
                        chunk = self.sock.recv(4096).decode('ascii')
                        if not chunk: break # Server closed connection
                        full_response += chunk
                        
                        # If we have 3 equals signs, we likely have the full batch
                        if full_response.count('=') >= 3: 
                            break
                except socket.timeout:
                    pass # We got what we got, move on

                # 3. Parse whatever we got
                if full_response:
                    lines = full_response.strip().split('\n')
                    for line in lines:
                        if '=' in line:
                            parts = line.split('=')
                            if len(parts) == 2:
                                key = parts[0].strip()
                                try:
                                    val_radians = float(parts[1].strip())
                                    val_degrees = val_radians * 57.2958 # Rad -> Deg
                                    
                                    if "Pitch" in key:   self.pitch = val_degrees
                                    elif "Heading" in key: self.yaw = val_degrees
                                    elif "Bank" in key:    self.roll = val_degrees
                                except ValueError:
                                    pass

                # 4. Pace the loop (10Hz is safer for Wi-Fi)
                time.sleep(0.1) 
                
            except Exception as e:
                print(f"[NET] Connection Lost: {e}")
                self.connected = False
                if self.sock: 
                    try: self.sock.close()
                    except: pass