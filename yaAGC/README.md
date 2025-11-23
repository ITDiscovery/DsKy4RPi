# PiDSKY Phase 3 Driver

## 1. Project Overview
This project serves as the hardware driver for a physical DSKY (Display & Keyboard) replica. It interfaces with the **yaAGC** (Yet Another Apollo Guidance Computer) simulator via TCP, translating network packets into physical GPIO signals for 7-segment displays, status lamps, and keypad inputs.

## 2. File Structure
* **`main.py`**: The application entry point. It initializes the `DskyHardware` and `AgcClient`, then enters an infinite event loop to handle bi-directional data (Downlink from AGC, Uplink from Keypad).
* **`agc.py`**: Manages the TCP network connection. It connects to the AGC simulator (default port 19798) using non-blocking sockets and handles the packing/unpacking of AGC channel data (Channels 010, 011, 013, 015, 163).
* **`config.py`**: Central configuration file containing:
    * **Network**: Host IP and Port settings.
    * **GPIO**: Raspberry Pi BCM pin mappings for strobe lines, data, and clocks.
    * **Mappings**: Translation tables for Octal-to-Character decoding and raw hardware key codes.

## 3. Features
* **Non-Blocking I/O**: Ensures the physical display updates remain fluid even if network packets are delayed.
* **Channel 10 Decoding**: fully implements the parsing of AGC Channel 10 words to
