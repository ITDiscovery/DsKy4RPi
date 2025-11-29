import socket
import time
import math

# Configuration
HOST = '0.0.0.0'  # Listen on all network interfaces
PORT = 37777      # Standard Orbiter port

def run_mock_server():
    # 1. Setup the Socket
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # Allow the port to be reused immediately after restart (prevents "Address already in use" errors)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        server_sock.bind((HOST, PORT))
        server_sock.listen(1)
        print(f"--- MOCK ORBITER SERVER LISTENING ON {PORT} ---")
        print("Waiting for OpenFDAI connection...")
        
        while True:
            # 2. Wait for a client (OpenFDAI) to connect
            conn, addr = server_sock.accept()
            print(f"Connected to client at {addr}")
            
            t = 0.0 # Time counter for animation
            
            try:
                while True:
                    # 3. Receive Data
                    # The client sends: "GET PITCH\nGET YAW\nGET BANK\n"
                    data = conn.recv(1024)
                    if not data: 
                        break # Client closed connection
                    
                    request = data.decode('ascii')
                    
                    # 4. Check if it's the correct request
                    # We check for PITCH as a sanity check
                    if "GET PITCH" in request:
                        # 5. Generate Synthetic Tumbling Data
                        # Pitch: Sine wave (-90 to +90)
                        pitch = math.sin(t) * 90
                        
                        # Yaw: Linear rotation (0 to 360 loop)
                        yaw = (t * 10) % 360
                        
                        # Roll: Slow oscillation (-180 to +180)
                        roll = math.cos(t / 2) * 180
                        
                        # 6. Format Response
                        # The client expects three lines of text, one number per line.
                        # We use \r\n to mimic a Windows server perfectly.
                        response = f"{pitch:.2f}\r\n{yaw:.2f}\r\n{roll:.2f}\r\n"
                        
                        conn.sendall(response.encode('ascii'))
                    
                    # Increment time for the next frame
                    t += 0.05
                    
                    # Simulate 20-30Hz update rate
                    time.sleep(0.03)
                    
            except (ConnectionResetError, BrokenPipeError):
                print("Client disconnected. Waiting for new connection...")
            finally:
                conn.close()
                
    except KeyboardInterrupt:
        print("\nStopping Mock Server.")
    except Exception as e:
        print(f"Server Error: {e}")
    finally:
        server_sock.close()

if __name__ == "__main__":
    run_mock_server()