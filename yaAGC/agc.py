# agc.py
import socket
import time
import config

class AgcClient:
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setblocking(0)  # Non-blocking mode
        self.connected = False

    def connect(self):
        """Attempts to connect to yaAGC. Returns True if successful."""
        try:
            self.sock.connect((config.AGC_HOST, config.AGC_PORT))
            print(f"[AGC] Connected to {config.AGC_HOST}:{config.AGC_PORT}")
            self.connected = True
            return True
        except socket.error:
            # It's normal to fail if server isn't ready
            return False

    def send_key(self, key_char):
        """Encodes a character and sends it to Channel 15 (Keypad)."""
        # Protocol: We send 3-tuples: (Channel, Value, Mask)
        # We can look up the octal codes for characters here
        
        val = 0
        if key_char.isdigit():
            val = int(key_char)
            if val == 8: val = 0o10
            elif val == 9: val = 0o11
        elif key_char == '+': val = 0o32
        elif key_char == '-': val = 0o33
        elif key_char == 'V': val = 0o21
        elif key_char == 'N': val = 0o37
        elif key_char == 'R': val = 0o22
        elif key_char == 'C': val = 0o36
        elif key_char == 'P': val = 0o20000 # Special handling for PRO usually needed
        elif key_char == '\n': val = 0o34 # Enter
        
        # For standard keys (Channel 15), the mask is usually 0o37 (5 bits)
        self._send_packet(config.CHAN_KEYPAD, val, 0o37)
        print(f"[AGC] Sent Key: {key_char} (Val: {oct(val)})")

    def _send_packet(self, channel, value, mask):
        """Low-level packet packer (from original script)."""
        if not self.connected: return
        
        outputBuffer = bytearray(4)
        # Mask Packet
        outputBuffer[0] = 0x20 | ((channel >> 3) & 0x0F)
        outputBuffer[1] = 0x40 | ((channel << 3) & 0x38) | ((mask >> 12) & 0x07)
        outputBuffer[2] = 0x80 | ((mask >> 6) & 0x3F)
        outputBuffer[3] = 0xC0 | (mask & 0x3F)
        try:
            self.sock.send(outputBuffer)
            
            # Data Packet
            outputBuffer[0] = 0x00 | ((channel >> 3) & 0x0F)
            outputBuffer[1] = 0x40 | ((channel << 3) & 0x38) | ((value >> 12) & 0x07)
            outputBuffer[2] = 0x80 | ((value >> 6) & 0x3F)
            outputBuffer[3] = 0xC0 | (value & 0x3F)
            self.sock.send(outputBuffer)
        except BrokenPipeError:
            print("[AGC] Disconnected")
            self.connected = False

    def read(self):
        """Reads available data. Returns list of (channel, value)."""
        if not self.connected: return []
        
        packet_size = 4
        buffer = bytearray(packet_size)
        results = []
        
        try:
            # In non-blocking, this might return fewer bytes or raise error
            data = self.sock.recv(1024) 
            if not data: return []
            
            # Process chunks of 4 bytes
            # (This is a simplified reader; robust implementations handle partial packets,
            # but this works for localhost speeds usually)
            for i in range(0, len(data), 4):
                pkt = data[i:i+4]
                if len(pkt) < 4: break
                
                # Validate signatures
                if (pkt[0] & 0xF0) == 0x00 and (pkt[3] & 0xC0) == 0xC0:
                    channel = (pkt[0] & 0x0F) << 3
                    channel |= (pkt[1] & 0x38) >> 3
                    value = (pkt[1] & 0x07) << 12
                    value |= (pkt[2] & 0x3F) << 6
                    value |= (pkt[3] & 0x3F)
                    results.append((channel, value))
                    
            return results
            
        except BlockingIOError:
            return []
        except socket.error:
            self.connected = False
            return []