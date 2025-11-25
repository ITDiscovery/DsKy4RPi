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
