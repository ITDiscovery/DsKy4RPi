# 🚀 Project Apollo Sim-Pit: NASSP/Orbiter 2024 I/O Bridge

This repository contains the Python client and hardware mapping necessary to interface a physical Apollo-style control panel (using Raspberry Pi and shift registers) with the **Project Apollo - NASSP** simulation running on the **Orbiter 2024** flight simulator.

## ⚙️ 1. System Architecture Overview

The core challenge of this project is bridging the native Windows C++ simulation to the Linux/GPIO hardware over a network connection.

The Raspberry Pi acts as a **Protocol Bridge**, translating low-level hardware changes (input/output) into high-level, string-based network commands used by the `orb:connect` API. There are several physical peices of hardware that the Raspberry Pi will bridge to orb:connect"

* DSKY4Pi: Board that provides 7 Segment Display, 19 key matrix, and 16 LEDs, predominantly driven by the AGC.
* Blinkinboard: A board that provides 40 LEDs and 32 individual switch channels.
* USB Joystick, using PyGame

### Hardware Chain:
**Physical Switches & LEDs** (74HCTxxx Chips and TM1638 LED Driver) ➡️ **Raspberry Pi (Python Client)** ➡️ **TCP/IP Network (orb:connect)** ➡️ **Intel iMac (Orbiter 2024 / NASSP)**

---

## 💡 2. DSKY Mapping and Telemetry Specification

The DSKY interface is handled primarily by a **TM1638 module** (for segments and LEDs) and a **BlinkinBoard** (for auxiliary switches).

### A. DSKY Display Segment Mapping (Output)

The DSKY numeric display segments are addressed directly on the TM1638 via the segment index (`TM.segments[x]`).

| Display Field | DSKY Register | Segment Start Index (`TM.segments[x]`) | Notes |
| :--- | :--- | :--- | :--- |
| **Program** | - | RowCol 1/1 (Not Displayed) | Used for P00-P99 |
| **Verb/Noun** | V/N | Col 1/1 - Col 2/2 | 1/1 = V1, 1/2 = V2, 2/1 = N1, 2/2 = N2 |
| **Register R1** | R1 | Col 3/1 - Col 5/5 | 3/1 = R1 sign, 3/2 = R1 digit 1, etc. |
| **Register R2** | R2 | Col 6/1 - Col 8/5 | 6/1 = R2 sign, 6/2 = R2 digit 1, etc. |
| **Register R3** | R3 | Col 9/1 - Col 11/5 | 9/1 = R3 sign, 9/2 = R3 digit 1, etc. |

### B. DSKY LED Addressing (Output)

The indicator lights are mapped to LEDs on the TM1638 modules. The client polls the NASSP status and sets the corresponding TM1638 LED.

| Indicator | DSKY Code Location | TM1638 Board | TM1638 LED Index (`TM.leds[x]`) |
| :--- | :--- | :--- | :--- |
| **TEMP** | U191 | Board 1 | 0 |
| **GIMBAL LOCK** | U192 | Board 1 | 1 |
| **PROG** | U193 | Board 1 | 2 |
| **RESTART** | U194 | Board 1 | 3 |
| **TRACKER** | U195 | Board 1 | 4 |
| **ALT** | U196 | Board 1 | 5 |
| **VEL** | U197 | Board 1 | 6 |
| **COMP ACTIVITY** | U198 | Board 1 | 7 |
| **UPLINK ACTIVITY** | U1101 | Board 2 | 8 |
| **NO ATT** | U1102 | Board 2 | 9 |
| **STBY** | U1103 | Board 2 | 10 |
| **KEY REL** | U1104 | Board 2 | 11 |
| **OPR ERR** | U1105 | Board 2 | 12 |

### C. TM1638 Keypad Input Mapping (Input)

The raw key codes reported by the TM1638 driver are translated into NASSP string commands.

| Raw TM1638 Key Code | DSKY Key Name | NASSP String Name (Input Target) |
| :--- | :--- | :--- |
| **1** | ENTER | `DskySwitchEnter` |
| **2** | RESET | `DskySwitchReset` |
| **3** | CLEAR | `DskySwitchClear` |
| **4** | PROCEED | `DskySwitchProg` |
| **5** | KEY REL | `DskySwitchKeyRel` |
| **6** | NINE | `DskySwitchNine` |
| **7** | SIX | `DskySwitchSix` |
| **8** | THREE | `DskySwitchThree` |
| **9** | EIGHT | `DskySwitchEight` |
| **10** | FIVE | `DskySwitchFive` |
| **11** | TWO | `DskySwitchTwo` |
| **12** | SEVEN | `DskySwitchSeven` |
| **13** | FOUR | `DskySwitchFour` |
| **14** | ONE | `DskySwitchOne` |
| **15** | PLUS | `DskySwitchPlus` |
| **16** | MINUS | `DskySwitchMinus` |
| **17** | ZERO | `DskySwitchZero` |
| **18** | NOUN | `DskySwitchNoun` |
| **19** | VERB | `DskySwitchVerb` |

## 💻 3. I/O Translation Table (Input & Output)

This table defines the definitive string identifiers used for communication via the `orb:connect` interface. These strings map directly to the `Register()` calls found in the NASSP source code (e.g., `saturnpanel.cpp`, `lempanel.cpp`).

### A. DSKY & AGC Input Commands (SET)

To simulate a physical key press, the Python client must send a command string to **SET** the corresponding switch name to the 'pressed' state (`=1`) and then immediately send the 'released' state (`=0`).

| Function / Key | NASSP Registered String Name | `orb:connect` Command Format (Input) |
| :--- | :--- | :--- |
| **ENTER Key** | `DskySwitchEnter` | `SET:DskySwitchEnter=1` |
| **VERB Key** | `DskySwitchVerb` | `SET:DskySwitchVerb=1` |
| **NOUN Key** | `DskySwitchNoun` | `SET:DskySwitchNoun=1` |
| **PROCEED Key** | `DskySwitchProg` | `SET:DskySwitchProg=1` |
| **Numeric Key '1'** | `DskySwitchOne` | `SET:DskySwitchOne=1` |
| **Numeric Key '0'** | `DskySwitchZero` | `SET:DskySwitchZero=1` |
| **Master Alarm Reset** | `MasterAlarmSwitch` | `SET:MasterAlarmSwitch=1` |
| **CM Engine Arm** | `EngineArmSwitch` (CSM) | `SET:EngineArmSwitch=1` (Center) |
| **LM Abort Button** | `LMAbortButton` | `SET:LMAbortButton=1` |

### B. Core Switches and Controls (SET Commands)

These inputs control major vessel systems, often requiring two- or three-position states.

| Control | NASSP Registered String Name | State Value Interpretation |
| :--- | :--- | :--- |
| **IMU Cage Switch** | `IMUGuardedCageSwitch` | `1` (Unguarded/Up), `0` (Guarded/Down) |
| **LV Guidance Switch** | `LVGuidanceSwitch` | `1` (Up/PGNS), `0` (Down/Manual) |
| **CM/LM Mode Control** | `CMCModeSwitch` (CSM) / `ModeControlPGNSSwitch` (LM) | `0`: Down, `1`: Center, `2`: Up |
| **Manual Att. Roll** | `ManualAttRollSwitch` | `0`: Down, `1`: Center, `2`: Up |
| **RCS X-Feed** | `RCSXFeedSwitch` (LM) | `0`: Down, `1`: Center, `2`: Up |
| **LM Main SOV A** | `RCSMainSovASwitch` (LM) | `0`: Down, `1`: Center, `2`: Up |

### C. Indicator and Telemetry Outputs (GET Variables)

To illuminate physical LEDs or update displays, the Python client must send a **GET** command to fetch the current status of these NASSP variables.

| Status / Light | NASSP Accessor Method (C++) | NASSP Telemetry Variable (GET Format) | Notes |
| :--- | :--- | :--- | :--- |
| **KB REL Light** | `KbRelLit()` (DSKY) | `GET:NASSP:DSKY:KbRelLit` | Boolean status (1 or 0) |
| **PROG Light** | `ProgLit()` (DSKY) | `GET:NASSP:DSKY:ProgLit` | Boolean status (1 or 0) |
| **Opr Err Light** | `OprErrLit()` (DSKY) | `GET:NASSP:DSKY:OprErrLit` | Boolean status (1 or 0) |
| **R1 Register Value** | `GetR1()` (DSKY) | `GET:NASSP:DSKY:R1` | Returns a 7-character octal string |
| **PIPA Temp** | (Mapped to internal sensor) | `GET:s10A96` | Returns floating point value (e.g., "105.00") |
| **Main Bus A Volts** | (Mapped to sensor output) | `GET:s11A57` | Returns voltage value (e.g., "28.01 V") |

---

## ⚙️ 4. Development Notes (Python Client)

The Python client should utilize the standard `socket` module to handle the TCP/IP connection to `orb:connect`.

* **Communication Protocol:** The `orb:connect` interface communicates over TCP sockets, sending and receiving simple ASCII strings.
* **Loop:** The client should run a continuous loop: read all switch inputs, send **SET** commands, and then fetch all necessary **GET** variables to update the physical outputs.
* **Error Handling:** Implement robust retry logic, as networking latency can interrupt the data stream.
* 
# Orbiter SimPit Interface - Version 3.0

**Status:** Stable / Archived
**Date:** November 2025
**Hardware:** Raspberry Pi (GPIO Chip 4), DSKY (TM1638), BlinkinBoard (Shift Registers)

## 1. System Overview
This project bridges physical cockpit hardware to Orbiter Space Flight Simulator (via `orb:connect`). It uses a unified, thread-safe Python driver to manage multiple SPI-like chains simultaneously to prevent resource conflicts.

### Hardware Stack
* **Controller:** Raspberry Pi 4
* **Display:** 3x TM1638 LED & Key Modules (Chained)
* **I/O Board:** "BlinkinBoard" (5x 74HC595 Output, 4x 74HC165 Input)
* **Inputs:** 3-Position Toggle Switches, Momentary Arcade Buttons, DSKY Keypad
* **Outputs:** 7-Segment Displays, Status LEDs (Red/Green/Blue/Yellow)

## 2. GPIO Pinout (BCM Numbering)

| Signal | Pin | Description |
| :--- | :--- | :--- |
| **Blinkin Out** | | **74HC595 Chain (LEDs)** |
| `BB_CLK` | 21 | Shift Clock |
| `BB_LATCH` | 20 | Storage Latch |
| `BB_DATA` | 16 | Data Out (MOSI) |
| **Blinkin In** | | **74HC165 Chain (Switches)** |
| `BB_CLK_IN` | 17 | Shift Clock |
| `BB_LATCH_IN` | 22 | Parallel Load (Latch) |
| `BB_DATA_IN` | 27 | Data In (MISO) |
| **DSKY** | | **TM1638 Chain** |
| `TM_CLK` | 13 | Clock |
| `TM_DIO` | 19 | Data I/O |
| `TM_STB[0]` | 26 | Strobe - **Board 0 (Bottom)** |
| `TM_STB[1]` | 6 | Strobe - **Board 1 (Middle)** |
| `TM_STB[2]` | 5 | Strobe - **Board 2 (Top)** |

## 3. Configuration Maps

### DSKY Layout
* **Board 2 (Top):** Register 1 (Digits 0-5), PROG (Digits 6-7), Status Indicators.
* **Board 1 (Mid):** Register 2 (Digits 0-5), VERB (Digits 6-7).
* **Board 0 (Bot):** Register 3 (Digits 0-5), NOUN (Digits 6-7), Keypad Input.

### BlinkinBoard LED Map (Outputs)
* **Red Row:** Bits 0-7 (Master Alarm, G/N, CES, Engine Stop)
* **Green Row:** Bits 8-15 (Eng Start, SPS Ready, Ullage)
* **Arcade:** Bits 16-17 (Abort, Abort Stage)
* **Blue:** Bit 32 (Watchdog)
* **Yellow:** Bits 34-35 (Heater, Glycol)

### Switch Input Map
* **Toggle 1 (Engine Arm):** Bits 2 (Up) / 3 (Down)
* **Toggle 2 (SC Cont):** Bits 0 (Up) / 1 (Down)
* **Toggle 3 (Opt Zero):** Bits 4 (Up) / 5 (Down)
* **Toggle 4 (IMU Pwr):** Bits 6 (Up) / 7 (Down)
* **Abort Button:** Bit 8
* **Abort Stage:** Bit 9

## 4. Software Architecture
* **`UnifiedSimPitDriver.py`**: Low-level hardware driver. Manages `gpiod` requests and bit-banging for both TM1638 and Shift Registers.
* **`orbiter_bridge.py`**: Main client.
    * `input_loop`: Polls switches/keys, detects state changes, sends `SET` commands.
    * `output_loop`: Requests `GET` telemetry, updates display/LED buffers.
* **`mock_orbconnect_server.py`**: Simulates Orbiter. Provides a Curses-based dashboard to toggle virtual lights and view switch inputs.

## 5. Usage
1.  **Start Server:** `python3 mock_orbconnect_server.py`
2.  **Start Bridge:** `python3 orbiter_bridge.py`
3.  **Verify:** Toggle keys on Server to light LEDs. Flip physical switches to see input on Server.
