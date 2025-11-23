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

## 💻 2. I/O Translation Table (Input & Output)

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

## ⚙️ 3. Development Notes (Python Client)

The Python client should utilize the standard `socket` module to handle the TCP/IP connection to `orb:connect`.

* **Communication Protocol:** The `orb:connect` interface communicates over TCP sockets, sending and receiving simple ASCII strings.
* **Loop:** The client should run a continuous loop: read all switch inputs, send **SET** commands, and then fetch all necessary **GET** variables to update the physical outputs.
* **Error Handling:** Implement robust retry logic, as networking latency can interrupt the data stream.
