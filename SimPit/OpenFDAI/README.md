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
