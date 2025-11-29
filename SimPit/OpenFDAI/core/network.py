import socket
import threading
import time

class OrbiterClient:
    def __init__(self, host='127.0.0.1', port=37777, connect=True):
        self.host = host
        self.port = port
        self.connected = False
        self.running = True
        
        # Shared Telemetry (Thread-Safe)
        self.pitch = 0.0
        self.yaw = 0.0
        self.roll = 0.0
        
        if connect:
            self._thread = threading.Thread(target=self._worker, daemon=True)
            self._thread.start()

    def _worker(self):
        """Background loop to fetch data from Real Orbiter."""
        while self.running:
            if not self.connected:
                self._connect()
                time.sleep(1)
                continue

            try:
                # 1. Batch Request
                # We ask for PITCH, YAW, and BANK (Roll) in one packet.
                # Note: Orbiter angles are usually radians or degrees depending on the plugin.
                # Standard Orb:Connect usually returns degrees.
                msg = b'GET PITCH\nGET YAW\nGET BANK\n' 
                self.sock.sendall(msg)
                
                # 2. Receive Response
                # We expect roughly 3 lines of numbers, e.g.:
                # "10.5\r\n90.2\r\n-4.5\r\n"
                data = self.sock.recv(1024).decode('ascii')
                
                # 3. Parse
                self._parse_batch(data)
                
                # 60 FPS Target (0.016s), but network jitter matters.
                # 0.03 is ~30Hz which is safe for Wi-Fi.
                time.sleep(0.03) 
                
            except Exception as e:
                print(f"Network Error: {e}")
                self.connected = False
                self.sock.close()

    def _connect(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(2.0)
            self.sock.connect((self.host, self.port))
            
            # Handshake (Standard OrbConnect usually sends a banner)
            # We just read it and throw it away to clear the buffer.
            try:
                banner = self.sock.recv(1024) 
                print(f"Connected to Orbiter: {banner.decode('ascii').strip()}")
            except:
                pass
                
            self.connected = True
        except:
            print(f"Searching for Orbiter at {self.host}...")

    def _parse_batch(self, data):
        """
        Parses a newline-separated list of numbers.
        Expected format:
        12.5
        95.1
        -0.4
        """
        try:
            lines = data.strip().split('\n')
            if len(lines) >= 3:
                # Convert strings to floats
                # Note: 'strip()' removes \r characters if Windows sent them
                p = float(lines[0].strip())
                y = float(lines[1].strip())
                r = float(lines[2].strip())
                
                # Update State
                self.pitch = p
                self.yaw = y
                self.roll = r
        except ValueError:
            pass # Garbage data (incomplete packet), ignore this frame