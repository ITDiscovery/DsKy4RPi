# DsKy4RPi
Apollo DsKy for Raspberry Pi

Will contain source, libraries and build notes for Apollo DsKy board for Rasperry Pi. I've seen a bunch of these boards created for Arudino, which is hugely limited, and can't run AGC simulators and other software. I've created a board via EasyEDA, which can be designed on their servers and they will create and send you a minimum of 5. I've stashed the board designs here also.

Design Goals:

1. Not a slave to the actual Apollo DsKy, as close as feasible. 
  a. 3 sets of 5 Digits with a 1 and plus/minus.
  b. 19 key switches
  c. 15 LEDs
2. Raspberry Pi: chain 3 TM1638's together and use the same ports as T Hilaire's software.
   DataIO on GPIO19 (Pin 35)
   Clk on GPIO13 (Pin 37)
   STB U1 on GPIO26 (Pin 37)
   STB U2 on GPIO6 (Pin 31)
   STB U3 on GPIO5 (Pin 29)
3. Additional adds:
   a. Extended the 40 pin GPIO header to allow a male header or easy soldering of additional parts.
   b. Extra header breakouts: Serial, SPI
   c. Connection headers to allow additional switch banks to be connected: Since U2 and U3 keyboard connections where not needed, I broke out those to a header which will allow an additional 60 keys (not switches) to be connected. 

https://github.com/thilaire/rpi-TM1638

https://www.ibiblio.org/apollo/developer.html#sendrecv_Protocol
(see Table of I/O Channels

##yaAGC Installation on Raspberry Pi Buster##
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
