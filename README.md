# DsKy4RPi #
Apollo DsKy for Raspberry Pi

Will contain source, libraries and build notes for Apollo DsKy board for Rasperry Pi. I've seen a bunch of these boards created for Arudino, which is hugely limited, and can't run AGC simulators and other software. I've created a board via EasyEDA, which can be designed on their servers and they will create and send you a minimum of 5. I've stashed the board designs here also.

Design Goals:

1. Not a slave to the actual Apollo DsKy, as close as feasible. 
     * 3 sets of 5 Digits with a 1 and plus/minus.
     * 19 key switches
     * 15 LEDs
2. Raspberry Pi: chain 3 TM1638's together and use the same ports as T Hilaire's software.
     * DataIO on GPIO19 (Pin 35)
     * Clk on GPIO13 (Pin 33)
     * STB U1 on GPIO26 (Pin 37)
     * STB U2 on GPIO6 (Pin 31)
     * STB U3 on GPIO5 (Pin 29)
3. Additional adds:
     * Extended the 40 pin GPIO header to allow a male header or easy soldering of additional parts.
     * Extra header breakouts: Serial, SPI
     * Connection headers to allow additional switch banks to be connected: Since U2 and U3 keyboard connections where not needed, I broke out those to a header which will allow an additional 60 keys (not switches) to be connected. 

# Hardware Configuration #

## 7 Segment Addressing ##

| Col 1/1 | Col 1/2 | Col 2/1 | Col 2/2 | Col 3/1 | Col 3/2 |
| ------- | ------ | ------ | ----- | ------ | ------ |
| Blank | Blank | Blank | Blank | U3 GR7 | U3 GR8 |
| U2 GR7 | U2 GR8 | Blank | Blank | U1 GR7 | U1 GR8 |
| U3 GR6 | U3 GR1 | U3 GR2 | U3 GR3 | U3 GR4 | U3 GR5 |
| U2 GR6 | U2 GR1 | U2 GR2 | U2 GR3 | U2 GR4 | U3 GR5 |
| U1 GR6 | U1 GR1 | U1 GR2 | U1 GR3 | U1 GR4 | U3 GR5 |


## LED Addressing ##

| IC | Digit | Segment | Location | Meaning | Register | Value |
| ---- | ---- | --- | ---------- | ----------- | ----- |
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
| ---| ---- | --- | ---------- | ----------- |
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



https://github.com/thilaire/rpi-TM1638
http://www.bgmicro.com/para-light-c-562g-dual-7-segment-readout.aspx

https://www.ibiblio.org/apollo/developer.html#sendrecv_Protocol
(see Table of I/O Channels

## yaAGC Installation on Raspberry Pi Buster ##
Pre-Requisites:
'''
sudo apt-get install wx3.0-headers libwxgtk3.0-dev libsdl-dev libncurses5-dev liballegro4-dev git sudo apt-get tcl tk
'''
Compilation:  
'''
git clone --depth 1 https://github.com/virtualagc/virtualagc
cd virtualagc
make clean install
'''
