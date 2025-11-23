# DsKy4RPi #
Apollo DsKy for Raspberry Pi

Will contain source, libraries and build notes for Apollo DsKy board for Rasperry Pi. I've seen a bunch of these boards created for Arudino, which is hugely limited, and can't run AGC simulators and other software. I've created a board via EasyEDA, which can be designed on their servers and they will create and send you a minimum of 5. I've stashed the board designs here also.

Design Goals:

1. Not a slave to the actual Apollo DsKy, as close as feasible. 
     * 3 sets of 6 Digits (elimiated the 1 and plus/minus, but I will have a mod to swap out 1st digit for a +/-)
     * 19 key switches
     * 15 LEDs + 1 "Panel LED"
2. Raspberry Pi: chain 3 TM1638's together and use the same ports as T Hilaire's software.
     * DataIO on GPIO19 (Pin 35)
     * Clk on GPIO13 (Pin 33)
     * STB U1 on GPIO26 (Pin 29)
     * STB U2 on GPIO6 (Pin 31)
     * STB U3 on GPIO5 (Pin 37)
3. Additional adds:
     * Extra header breakouts: 
        * Serial: 5V, TX, RX, Gnd
        * SPI: SPI_CE0_N (Pin 24),SPI_CE1_N (Pin 26), SPI_MOSI (Pin 19), SPI_MISO (Pin 21), SPI_CLK (Pin 23), Gnd
        * I2C: 3.3V, SDA1, SCL1, IC_SD (Pin 27), IC_SC (Pin 28), Gnd
     * Connection headers to allow additional switch banks to be connected: Since U1 and U2 keyboard connections where not needed, I broke out those to a header which will allow an additional 48 keys (not switches) to be connected. 
     * Panel Lighting switchable via GPIO 16 (Pin 36), this optional circuitry can have higher current LEDs (such as an Arcade button LED) driven by this circuit and is available at LED25.

4. New features:
     * Sim-Pit for Orbiter with Blinkinboard (in SimPit directory)
     * World clock (in diagram directory)
     * KIM-1 Simulator (in KimRPi directory)

## Supported AGC Functions

The **DsKy4RPi** fully implements the standard DSKY interface protocols, allowing for authentic interaction with the Apollo Guidance Computer simulation (yaAGC).

### Core DSKY Operations
The system supports the complete "Verb-Noun" syntax used by Apollo astronauts to communicate with the computer.
* **Verb/Noun/Program Display:** Full support for 7-segment display of current Program (PROG), Verb (VERB), and Noun (NOUN).
* **Data Registers (R1, R2, R3):**
    * Displays 5-digit octal or decimal data.
    * Handles sign bits (+/-) for R1, R2, and R3.
* **Keypad Input:**
    * **0-9**: Data entry.
    * **VERB/NOUN**: Command initiation.
    * **ENTR**: Execute command.
    * **CLR**: Clear data/error.
    * **PRO**: Proceed (confirm action).
    * **KEY REL**: Release Key (handover control).
    * **RSET**: Error Reset.

## 7 Segment Addressing ##

### Original DsKy
| Row | Col 1/1 | Col 1/2 | Col 2/1 | Col 2/2 | Col 3/1 | Col 3/2 |
| -- | ------- | ------ | ------ | ----- | ------ | ------ |
| A | Blank | Blank | Blank | Blank | Prog 1 | Prog 2 |
| B | Verb 1 | Verb 2 | Blank | Blank | Noun 1 | Noun 2 |
| 1 | Data 1 +/- | Data 1-1 | Data 1-2 | Data 1-3 | Data 1-4 | Data 1-5 |
| 2 | Data 2 +/- | Data 2-1 | Data 2-2 | Data 2-3 | Data 2-4 | Data 2-5 |
| 3 | Data 3 +/- | Data 3-1 | Data 3-2 | Data 3-3 | Data 3-4 | Data 3-5 |

### Digit to Driver
| Row | Col 1/1 | Col 1/2 | Col 2/1 | Col 2/2 | Col 3/1 | Col 3/2 |
| -- | ------- | ------ | ------ | ----- | ------ | ------ |
| A | Blank | Blank | Blank | Blank | U1 GR7 | U1 GR8 |
| B | U2 GR7 | U2 GR8 | Blank | Blank | U3 GR7 | U3 GR8 |
| 1 | U3 GR1 | U3 GR2 | U3 GR3 | U3 GR4 | U3 GR5 | U3 GR6 |
| 2 | U2 GR1 | U2 GR2 | U2 GR3 | U2 GR4 | U2 GR5 | U2 GR6 |
| 3 | U3 GR1 | U3 GR2 | U3 GR3 | U3 GR4 | U3 GR5 | U3 GR6 |

### 2x7 Version
| Row | Col 1/1 | Col 1/2 | Col 2/1 | Col 2/2 | Col 3/1 | Col 3/2 |
| -- | ------- | ------ | ------ | ----- | ------ | ------ |
| A | Blank | Blank | Blank | Blank | Prog1/2 |  |
| B | Verb1/2 |  | Blank | Blank | Noun1/2 |  |
| 1 | Data1-1/2 |  | Data1-3/4 |  | Data1-5/6 |  |
| 2 | Data2-1/2 |  | Data2-3/4 |  | Data2-5/6 |  |
| 3 | Data3-1/2 |  | Data3-3/4 |  | Data3-5/6 |  |

### 4x7 Version
| Row | Col 1/1 | Col 1/2 | Col 2/1 | Col 2/2 | Col 3/1 | Col 3/2 |
| -- | ------- | ------ | ------ | ----- | ------ | ------ |
| A | Blank | Blank | Blank | Blank | Prog1 | Prog2 |
| B | Verb1 | Verb2 | Blank | Blank | Noun1 | Noun2 |
| 1 | Data1-1 | Data1-2| Data1-3/6 | | | |
| 2 | Data2-1 | Data2-2 | Data1-3/6 | | | |
| 3 | Data3-1 | Data3-2 | Data1-3/6 | | | |

### virtualagc DSKY Code to TM.segments[x]
| Row | Col 1/1 | Col 1/2 | Col 2/1 | Col 2/2 | Col 3/1 | Col 3/2 |
| -- | ------- | ------ | ------ | ----- | ------ | ------ |
| A | Blank | Blank | Blank | Blank | M1-22 | M2-23 |
| B | V1-14 | V2-15 | Blank | Blank | N1-6 | N2-7 |
| 1 | +/-  = 16 | 11-17| 12-18 | 13-19 | 14-20 | 15-21 |
| 2 | +/- = 8 | 21-9 | 22-10 | 23-11 | 24-12 | 25-13 |
| 3 | +/- = 0 | 31-1 | 32-2 | 33-3 | 34-4 | 35-5 |

## LED Addressing ##
| IC | Digit | Segment | Location | Meaning | Register | Value |
| ---- | ---- | --- | ---------- | ----------- | ----- | ------ |
| U1 | 9 | 1 | LED1 | TEMP | 0x01 | 1 |
| U1 | 9 | 2 | LED2 | GIMBAL LOCK | 0x03 | 1 |
| U1 | 9 | 3 | LED3 | PROG | 0x05 | 1 |
| U1 | 9 | 4 | LED4 | RESTART | 0x07 | 1 |
| U1 | 9 | 5 | LED5 | TRACKER | 0x09 | 1 |
| U1 | 9 | 6 | LED6 | ALT | 0x0B | 1 |
| U1 | 9 | 7 | LED7 | VEL | 0x0D | 1 |
| U1 | 9 | 8 | LED8 | COMP ACTIVITY | 0x0F | 1 |
| U1 | 10 | 1 | LED9 | UPLINK ACTIVITY | 0x01 | 2 |
| U1 | 10 | 2 | LED10 | NO ATT | 0x03 | 2 |
| U1 | 10 | 3 | LED11 | STBY | 0x05 | 2 |
| U1 | 10 | 4 | LED11 | KEY REL | 0x07 | 2 |
| U1 | 10 | 5 | LED11 | OPR ERR | 0x09 | 2 |
| U1 | 10 | 6 | LED11 |  | 0x0B | 2 |
| U1 | 10 | 7 | LED11 |  | 0x0D | 2 |
| U1 | 10 | 8 | LED11 | Spare (Panel Lighting?) | 0x0F | 2 |

## KEY Addressing ##
| IC | GR | Key | Location | Meaning | Code |
| --- | ---- | --- | ---------- | ----------- | --- |
| U1 | 1 | 1 | SW1 | ENTR | 2 | 
| U1 | 1 | 2 | SW2 | RSET | 6 | 
| U1 | 1 | 3 | SW3 | CLR |
| U1 | 1 | 4 | SW4 | PROG |
| U1 | 1 | 5 | SW5 | KEY REL |
| U1 | 1 | 6 | SW6 | ENTR |
| U1 | 1 | 7 | SW7 | ENTR |
| U1 | 1 | 8 | SW8 | ENTR |
| U1 | 2 | 1 | SW9 | ENTR | 1 |
| U1 | 2 | 2 | SW10 | ENTR | 5 |
| U1 | 2 | 3 | SW11 | ENTR |
| U1 | 2 | 4 | SW12 | ENTR |
| U1 | 2 | 5 | SW13 | ENTR |
| U1 | 2 | 6 | SW14 | ENTR |
| U1 | 2 | 7 | SW15 | ENTR |
| U1 | 2 | 8 | SW16 | ENTR |
| U1 | 3 | 1 | SW17 | ENTR | 0 |
| U1 | 3 | 2 | SW18 | ENTR | 4 |
| U1 | 3 | 3 | SW19 | ENTR |



https://github.com/thilaire/rpi-TM1638 \
http://www.bgmicro.com/para-light-c-562g-dual-7-segment-readout.aspx \
https://www.ibiblio.org/apollo/developer.html#sendrecv_Protocol \

Components: \
https://lcsc.com/product-detail/LED-Drivers_TM-Shenzhen-Titan-Micro-Elec-TM1638_C19187.html?ref=editor&logined=true \

1x7 and 4x7 Segments: \
https://lcsc.com/product-detail/Led-Segment-Display_0-56-Digitron-red-RED_C109200.html?ref=editor&logined=true \
https://lcsc.com/product-detail/Led-Segment-Display_SM420561N_C141367.html?ref=editor&logined=true \
or \
2x7 Segments: \
http://www.bgmicro.com/para-light-c-562g-dual-7-segment-readout.aspx \

## yaAGC Installation on Raspberry Pi Buster ##
Pre-Requisites:
```
sudo apt-get install wx3.0-headers libwxgtk3.0-dev libsdl-dev libncurses5-dev liballegro4-dev git 
sudo apt-get tcl tk
```
Compilation:  
```
git clone --depth 1 https://github.com/virtualagc/virtualagc.git
cd virtualagc
make clean install
```
