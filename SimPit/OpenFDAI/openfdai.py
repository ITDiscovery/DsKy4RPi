import configparser
import sys
from core.network import OrbiterClient
from core.graphics import FDAIScreen

# --- CONFIGURATION DECLARATIONS ---

# Network Settings
SERVER_IP   = "127.0.0.1"  # Set to 'localhost' or the IP of your Windows PC
SERVER_PORT = 37777        # Default OrbConnect port

# Window Settings
WIN_WIDTH   = 400
WIN_HEIGHT  = 400
FULLSCREEN  = False        # Set to True for dedicated SimPit screens

# Asset Settings
TEXTURE_PATH = "assets/navball_8k.png"

# Flight Dynamics Tweaks
# Toggle these if the ball spins the wrong way compared to the real Orbiter
INVERT_PITCH = False
INVERT_YAW   = False 
INVERT_ROLL  = False

# Colors (R, G, B) - 0.0 to 1.0
OVERLAY_COLOR = (1.0, 0.6, 0.0) # NASA Orange

# ----------------------------------

def main():
    print(f"--- OpenFDAI | Target: {SERVER_IP}:{SERVER_PORT} ---")
    
    # 1. Start Network (Background Thread)
    # We pass the IP/Port from our declares above
    client = OrbiterClient(host=SERVER_IP, port=SERVER_PORT)
    
    # 2. Start Graphics (Main Thread)
    # We pass the size, fullscreen flag, and texture path
    screen = FDAIScreen(width=WIN_WIDTH, height=WIN_HEIGHT, fullscreen=FULLSCREEN)
    screen.texture_path = TEXTURE_PATH # Inject the path
    screen.overlay_color = OVERLAY_COLOR # Inject the color
    screen.init_display()
    
    running = True
    while running:
        # Apply Inversions if necessary
        p = client.pitch * (-1 if INVERT_PITCH else 1)
        y = client.yaw   * (-1 if INVERT_YAW   else 1)
        r = client.roll  * (-1 if INVERT_ROLL  else 1)

        # Draw Frame
        running = screen.draw(p, y, r)
    
    # Clean exit
    client.running = False
    sys.exit()

if __name__ == "__main__":
    main()