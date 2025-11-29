# OpenFDAI

**A Standalone Virtual FDAI (Flight Director Attitude Indicator) for Orbiter 2024.**

OpenFDAI is a Python-based flight instrument designed for hardware simulator cockpits (SimPits). It renders a smooth, high-framerate 3D "Navball" on a Raspberry Pi (or PC) by receiving telemetry from a main Orbiter 2024 simulation via TCP.

It is designed to be lightweight, portable, and entirely decoupled from physical hardware drivers, making it easy to run on a secondary display or a dedicated Raspberry Pi 5.

---

## Features

* **Real-Time 3D Rendering:** Uses OpenGL (via PyGame) for smooth 60fps animation.
* **Networked:** Connects to Orbiter 2024 using the standard `Orb:Connect` protocol over TCP.
* **Hardware Accelerated:** Optimized for Raspberry Pi 4 and 5 (VideoCore GPU).
* **Configurable:** Easy toggle for IP addresses, window size, and axis inversion.
* **Mock Mode:** Includes a standalone "Mock Server" to test the display without needing to launch the full simulator.

## Prerequisites

### Hardware
* **Client:** Raspberry Pi (4 or 5 recommended) or any PC running Python 3.
* **Server:** Windows PC running [Orbiter Space Flight Simulator 2024](http://orbit.medphys.ucl.ac.uk/) with the `Orb:Connect` plugin installed.

### Software Dependencies
OpenFDAI requires Python 3 and the following libraries:

```bash
sudo apt-get update
sudo apt-get install python3-pip libsdl2-2.0-0
pip3 install pygame PyOpenGL

2. Connecting to Orbiter (Live Operation)
Launch Orbiter 2024 on your Windows PC.

Ensure the Orb:Connect module is enabled in the "Modules" tab.

Start a simulation scenario.

Edit openfdai.py and set SERVER_IP to your Windows PC's IP address.

Run the client on your Pi.

DSKY Tech Update
Custom Gem
Here is a comprehensive README.md for your OpenFDAI project. It covers installation, configuration, and the testing workflow we established.

Markdown
# OpenFDAI

**A Standalone Virtual FDAI (Flight Director Attitude Indicator) for Orbiter 2024.**

OpenFDAI is a Python-based flight instrument designed for hardware simulator cockpits (SimPits). It renders a smooth, high-framerate 3D "Navball" on a Raspberry Pi (or PC) by receiving telemetry from a main Orbiter 2024 simulation via TCP.

It is designed to be lightweight, portable, and entirely decoupled from physical hardware drivers, making it easy to run on a secondary display or a dedicated Raspberry Pi 5.

---

## Features

* **Real-Time 3D Rendering:** Uses OpenGL (via PyGame) for smooth 60fps animation.
* **Networked:** Connects to Orbiter 2024 using the standard `Orb:Connect` protocol over TCP.
* **Hardware Accelerated:** Optimized for Raspberry Pi 4 and 5 (VideoCore GPU).
* **Configurable:** Easy toggle for IP addresses, window size, and axis inversion.
* **Mock Mode:** Includes a standalone "Mock Server" to test the display without needing to launch the full simulator.

## Prerequisites

### Hardware
* **Client:** Raspberry Pi (4 or 5 recommended) or any PC running Python 3.
* **Server:** Windows PC running [Orbiter Space Flight Simulator 2024](http://orbit.medphys.ucl.ac.uk/) with the `Orb:Connect` plugin installed.

### Software Dependencies
OpenFDAI requires Python 3 and the following libraries:

```bash
sudo apt-get update
sudo apt-get install python3-pip libsdl2-2.0-0
pip3 install pygame PyOpenGL
Installation
Clone the Repository:

Bash
git clone [https://github.com/ITDiscovery/DsKy4RPi.git](https://github.com/ITDiscovery/DsKy4RPi.git)
cd DsKy4RPi/OpenFDAI
Add Assets: You need an equirectangular projection map for the ball texture.

Create an assets folder.

Place your texture file named navball_8k.png inside it.

(Note: You can download standard Navball textures from KSP or Orbiter community sites).

Bash
mkdir assets
# Example placeholder command:
wget -O assets/navball_8k.png [https://example.com/path/to/texture.jpg](https://example.com/path/to/texture.jpg)
Configuration
All configuration is handled at the top of openfdai.py. Open it with a text editor:

Python
# Network Settings
SERVER_IP   = "192.168.1.100"  # IP of your Windows PC running Orbiter
SERVER_PORT = 37777            # Default OrbConnect port

# Display Settings
WIN_WIDTH   = 800
WIN_HEIGHT  = 800
FULLSCREEN  = False            # Set True for dedicated SimPit screens

# Flight Dynamics
INVERT_PITCH = False           # Toggle if the ball rotates the wrong way
INVERT_YAW   = False
INVERT_ROLL  = False
Usage
1. Running the Mock Server (Testing)
To test the graphics without launching Orbiter, use the included mock server. It generates synthetic "tumbling" data.

Terminal 1:

Bash
python3 mockfdai_server.py
Terminal 2:

Bash
python3 openfdai.py
2. Connecting to Orbiter (Live Operation)
Launch Orbiter 2024 on your Windows PC.

Ensure the Orb:Connect module is enabled in the "Modules" tab.

Start a simulation scenario.

Edit openfdai.py and set SERVER_IP to your Windows PC's IP address.

Run the client on your Pi.

Directory Structure

OpenFDAI/
├── assets/
│   └── navball_8k.png       # The texture skin for the sphere
├── core/
│   ├── __init__.py
│   ├── graphics.py          # PyGame & OpenGL rendering logic
│   └── network.py           # TCP Client & Telemetry parsing
├── openfdai.py              # Main entry point & Configuration
└── mockfdai_server.py       # Standalone testing server

Troubleshooting
"Connection Refused": Check that SERVER_IP is correct and that Orbiter is running with the Orb:Connect module active.
"FileNotFoundError": Ensure assets/navball_8k.png exists.
Ball is all one color: Ensure glColor3f(1.0, 1.0, 1.0) is being called before gluSphere in graphics.py.
Lag on Raspberry Pi: Ensure you are using the GL driver (run sudo raspi-config > Advanced Options > GL Driver > GL (Fake KMS) or Full KMS).

License
Public Domain / MIT. Free for use in any SimPit project.
