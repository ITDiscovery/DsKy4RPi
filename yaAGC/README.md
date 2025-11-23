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
* **Channel 10 Decoding**: fully implements the parsing of AGC Channel 10 words to update the Verb, Noun, and Registers (R1, R2, R3) with sign handling.
* **Keypad Uplink**: Maps physical key presses (via TM1638 or similar) to AGC-compatible octal key codes, including special handling for the 'PRO' key.

## 4. Configuration
All hardware and network settings are adjustable in `config.py`.

### Network
Modify `AGC_HOST` and `AGC_PORT` to match the machine running `yaAGC`.
```python
AGC_HOST = 'localhost'
AGC_PORT = 19798

### Hardware (GPIO)
Pin assignments follow the BCM numbering scheme.

* Strobe List: Defines the order of display modules (STB_LIST).
* Control Pins: Defines specific pins for DIO and CLK.

The generic DSKY driver is in the hardware directory.
