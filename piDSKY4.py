#!/usr/bin/python3
# Copyright:    None, placed in the PUBLIC DOMAIN by its author (Ron Burkey)
#               Modified by Peter Nichols www.itdiscovery.info
# Filename:     piDSKY3.py
# Purpose:      To drive the RPi DSKY 2x7 and 4x7 board that use the TM1638 LED driver.
# Reference:    http://www.ibiblio.org/apollo/developer.html
# Mod history:  2017-11-17 RSB  Began.
#               2017-11-21 RSB  Updated with some fixes to the PRO and NOUN
#               keys that had been identified for piDSKY2.py.
#       2017-12-02 RSB  Replaced the entire program with a stripped form
#               of piDSKY2.py (in which all hardware-specific stuff
#               has been removed), because it was easier than 
#               back-porting bug-fixes.
#       2018-01-06 MAS  Switched the TEMP light to use channel 163 instead
#               of channel 11.
#       2020-05-05 Began modification of piDSKY.py to drive designed circuit board.
#
# In this skeleton form, the script acts as kind of a console-based DSKY, in which
# you can use keyboard keys (0 1 2 3 4 5 6 7 8 9 + - V N C P K R Enter) as surrogates
# for DSKY pushbuttons, and all DSKY-related outputs from yaAGC are simply parsed and
# displayed in textual form, though the idea is that in general, you'd rip out all of 
# that DSKY-specific stuff and replace it with whatever you wanted.
#
# The parts which need to be modified to be target-system specific are the 
# outputFromAGC() and inputsForAGC() functions, which are in the section *after* the following
# section.  The immediately following section, on the other hand, has some utility functions I use
# for the default outputFromAGC() and inputsForAGC() functions I provide, and
# can be deleted if they're not useful for the specific implementation desired.
#
# To run the program in its present form, you have to use yaAGC, and optionally
# yaDSKY2 (if you want to see the graphical DSKY and piPeripheral.py working in
# parallel).  To do that, assuming you had a directory setup in which all of the
# appropriate files could be found, you could run (presumably from different consoles)
#
#   yaDSKY2 --cfg=LM.ini --port=19797
#   yaAGC --core=Luminary099.bin --port=19797 --cfg=LM.ini
#   piDSKY.py
#
# If you didn't want to use yaDSKY2, then this stuff could all be run in a pure
# command-line environment without a GUI desktop.

import time
import os
import signal
import sys
import argparse
import threading
import termios
import fcntl
import socket
import datetime # <-- ADDED
from RPi5_TM1638 import TMBoards

# --- NEW TIMESTAMP LOGGER ---
def log(msg):
    """Prints a message with a timestamp (unless quiet mode is on)."""
    if not args.quiet:
        now = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print(f"[{now}] {msg}")
# --------------------------

DIO = 19
CLK = 13
STB = 26,6,5
TM = TMBoards(DIO, CLK, STB, 3)
TM.clearDisplay()

# Parse command-line arguments.
cli = argparse.ArgumentParser()
cli.add_argument("--host", help="Host address of yaAGC, defaulting to localhost.")
cli.add_argument("--port", help="Port for yaAGC, defaulting to 19798.", type=int)
cli.add_argument("--slow", help="For use on really slow host systems.")
cli.add_argument("--quiet", action="store_true", help="Suppress operational logging.")
args = cli.parse_args()

# Responsiveness settings.
if args.slow:
    PULSE = 0.25
    lampDeadtime = 0.25
else:
    PULSE = 0.05
    lampDeadtime = 0.1

# Characteristics of the host and port being used for yaAGC communications.  
if args.host:
    TCP_IP = args.host
else:
    TCP_IP = 'localhost'
if args.port:
    TCP_PORT = args.port
else:
    TCP_PORT = 19798

###################################################################################
# Some utilities I happen to use in my sample hardware abstraction functions, but
# not of value outside of that, unless you happen to be implementing DSKY functionality
# in a similar way.

# Given a 3-tuple (channel,value,mask), creates packet data and sends it to yaAGC.
def packetize(tuple):
    outputBuffer = bytearray(4)
    # First, create and output the mask command.
    outputBuffer[0] = 0x20 | ((tuple[0] >> 3) & 0x0F)
    outputBuffer[1] = 0x40 | ((tuple[0] << 3) & 0x38) | ((tuple[2] >> 12) & 0x07)
    outputBuffer[2] = 0x80 | ((tuple[2] >> 6) & 0x3F)
    outputBuffer[3] = 0xC0 | (tuple[2] & 0x3F)
    s.send(outputBuffer)
    # Now, the actual data for the channel.
    outputBuffer[0] = 0x00 | ((tuple[0] >> 3) & 0x0F)
    outputBuffer[1] = 0x40 | ((tuple[0] << 3) & 0x38) | ((tuple[1] >> 12) & 0x07)
    outputBuffer[2] = 0x80 | ((tuple[1] >> 6) & 0x3F)
    outputBuffer[3] = 0xC0 | (tuple[1] & 0x3F)
    s.send(outputBuffer)

# This particular function parses various keystrokes, like '0' or 'V' and creates
# packets as if they were DSKY keypresses.  It should be called occasionally as
# parseDskyKey(0) if there are no keystrokes, in order to make sure that the PRO
# key gets released.  

# The return value of this function is
# a list ([...]), of which each element is a 3-tuple consisting of an AGC channel
# number, a value for that channel, and a bitmask that tells which bit-positions
# of the value are valid.  The returned list can be empty.  For example, a
# return value of 
#   [ ( 0o15, 0o31, 0o37 ) ]
# would indicate that the lowest 5 bits of channel 15 (octal) were valid, and that
# the value of those bits were 11001 (binary), which collectively indicate that
# the KEY REL key on a DSKY is pressed.
resetCount = 0
def parseDskyKey(ch):
    global resetCount
    if ch == 'R':
        resetCount += 1
        if resetCount >= 5:
            log("Exiting ...")
            return ""
    elif ch != "":
        resetCount = 0
    returnValue = []
    if ch == '0':
        returnValue.append( (0o15, 0o20, 0o37) )
    elif ch == '1':
        returnValue.append( (0o15, 0o1, 0o37) )
    elif ch == '2':
            returnValue.append( (0o15, 0o2, 0o37) )
    elif ch == '3':
            returnValue.append( (0o15, 0o3, 0o37) )
    elif ch == '4':
            returnValue.append( (0o15, 0o4, 0o37) )
    elif ch == '5':
            returnValue.append( (0o15, 0o5, 0o37) )
    elif ch == '6':
            returnValue.append( (0o15, 0o6, 0o37) )
    elif ch == '7':
            returnValue.append( (0o15, 0o7, 0o37) )
    elif ch == '8':
            returnValue.append( (0o15, 0o10, 0o37) )
    elif ch == '9':
            returnValue.append( (0o15, 0o11, 0o37) )
    elif ch == '+':
            returnValue.append( (0o15, 0o32, 0o37) )
    elif ch == '-':
            returnValue.append( (0o15, 0o33, 0o37) )
    elif ch == 'V':
            returnValue.append( (0o15, 0o21, 0o37) )
    elif ch == 'N':
            returnValue.append( (0o15, 0o37, 0o37) )
    elif ch == 'R':
            returnValue.append( (0o15, 0o22, 0o37) )
    elif ch == 'C':
            returnValue.append( (0o15, 0o36, 0o37) )
    elif ch == 'P':
            returnValue.append( (0o32, 0o00000, 0o20000) )
    elif ch == 'p' or ch == 'PR':
            returnValue.append( (0o32, 0o20000, 0o20000) )
    elif ch == 'K':
            returnValue.append( (0o15, 0o31, 0o37) )
    elif ch == '\n':
        returnValue.append( (0o15, 0o34, 0o37) )
    return returnValue  

# This function turns keyboard echo on or off.
def echoOn(control):
    fd = sys.stdin.fileno()
    new = termios.tcgetattr(fd)
    if control:
        log("Keyboard echo on")
        new[3] |= termios.ECHO
    else:
        log("Keyboard echo off")
        new[3] &= ~termios.ECHO
    termios.tcsetattr(fd, termios.TCSANOW, new)
echoOn(False)

# This function is a non-blocking read of a single character from the
# keyboard.  Returns either the key value (such as '0' or 'V'), or else
# the value "" if no key was pressed.  Note:  fakes a "key" 
# 'PR' 0.75 seconds after a key 'p' or 'P'.  This is in lieu of PRO
# press and release events.  Is is possible to get keypress and release
# events or other equivalent data from the Python "keyboard" module, but
# I didn't know about it at first, and am too lazy to go back and add
# that support.
pressedPRO = False
pressedKEY = [0,0,0,0]
timePRO = 0

def get_char_keyboard_nonblock():
    global pressedPRO, timePRO, pressedKEY
    fd = sys.stdin.fileno()
    oldterm = termios.tcgetattr(fd)
    newattr = termios.tcgetattr(fd)
    newattr[3] = newattr[3] & ~termios.ICANON & ~termios.ECHO
    termios.tcsetattr(fd, termios.TCSANOW, newattr)
    oldflags = fcntl.fcntl(fd, fcntl.F_GETFL)
    fcntl.fcntl(fd, fcntl.F_SETFL, oldflags | os.O_NONBLOCK)
    c = ""
    try:
            c = sys.stdin.read(1)
    except IOError: pass
    termios.tcsetattr(fd, termios.TCSAFLUSH, oldterm)
    fcntl.fcntl(fd, fcntl.F_SETFL, oldflags)

    # TM1638 Dictionary
    keyDict = {}
    keyDict[1] = [4,0,0,0]
    keyDict[2] = [64,0,0,0]
    keyDict[3] = [0,4,0,0]
    keyDict[4] = [0,64,0,0]
    keyDict[5] = [0,0,4,0]
    keyDict[6] = [0,0,64,0]
    keyDict[7] = [0,0,0,4]
    keyDict[8] = [0,0,0,64]
    keyDict[9] = [2,0,0,0]
    keyDict[10] = [32,0,0,0]
    keyDict[11] = [0,2,0,0]
    keyDict[12] = [0,32,0,0]
    keyDict[13] = [0,0,2,0]
    keyDict[14] = [0,0,32,0]
    keyDict[15] = [0,0,0,2]
    keyDict[16] = [0,0,0,32]
    keyDict[17] = [1,0,0,0]
    keyDict[18] = [16,0,0,0]
    keyDict[19] = [0,1,0,0]

    charxlate = {}
    charxlate[1] = "\n"
    charxlate[2] = "R"
    charxlate[3] = "C"
    charxlate[4] = "P"
    charxlate[5] = "K"
    charxlate[6] = "9"
    charxlate[7] = "6"
    charxlate[8] = "3"
    charxlate[9] = "8"
    charxlate[10] = "5"
    charxlate[11] = "2"
    charxlate[12] = "7"
    charxlate[13] = "4"
    charxlate[14] = "1"
    charxlate[15] = "+"
    charxlate[16] = "-"
    charxlate[17] = "0"
    charxlate[18] = "V"
    charxlate[19] = "N"

    # Get from key TM1638 using the stable method
    keyval = TM.read_keys_raw(0)

    # --- NEW KEY LOGIC WITH DEBUGGING ---
    if keyval == pressedKEY:
        # No change in state, do nothing.
        c = ""
    elif keyval == [0, 0, 0, 0]:
        # A key was released. Reset pressedKEY and return "no key".
        pressedKEY = [0, 0, 0, 0]
        c = ""
    else:
        # A new state is entered.
        
        # Check if the key was released (keyval = [0,0,0,0] is the released state)
        if keyval == [0, 0, 0, 0]:
             # We just released a key. Send the KEY REL signal.
             c = 'K' # 'K' is the character for KEY REL
             pressedKEY = [0, 0, 0, 0]
             log("Key Release Detected: Sending K")
        else:
             # A key is pressed. Send the key.
             pressedKEY = keyval # Update the state
             for x in range(1, 20):
                 if (keyval == keyDict[x]):
                     c = charxlate[x]
                     log(f"Key Press Detected: {c} {keyval}")
                     break

    if c == 'p' or c == 'P':
        pressedPRO = True
        timePRO = time.time()
    if c == "" and pressedPRO and time.time() > timePRO + 0.75:
        pressedPRO = False
        c = 'PR'
    return c


# LampStatuses is for whether or not it is currently lit.
# This information isn't actually used for anything, but can be useful in a 
# specific hardware model as a way to know which lamp statuses have changed.
lampStatuses = {
    "TEMP" : { "isLit" : False },
    "GIMBAL LOCK" : { "isLit" : False },
    "PROG" : { "isLit" : False },
    "RESTART" : { "isLit" : False },
    "TRACKER" : { "isLit" : False },
    "ALT" : { "isLit" : False },
    "VEL" : { "isLit" : False },
    "UPLINK ACTY" : { "isLit" : False },
    "NO ATT" : { "isLit" : False },
    "DSKY STANDBY" : { "isLit" : False },
    "KEY REL" : { "isLit" : False },
    "OPR ERR" : { "isLit" : False },
    "PRIO DSP" : { "isLit" : False },
    "NO DAP" : { "isLit" : False }
}
# For modifying the lampStatuses[] array.
# The following dictionary gives, for each indicator lamp:
# LampDict is the conversion for what register on the TM1638 lights each lamp.
# Lamps 1-8 and 9-16 is lit sending a different value to the same register.

def updateLampStatuses(key, value):
	global lampStatuses
	if key in lampStatuses:
		lampStatuses[key]["isLit"] = value

# Converts a 5-bit code in channel 010 to " ", "0", ..., "9".
def codeToString(code):
    if code == 0:
        return " "
    elif code == 21:
        return "0"
    elif code == 3:
        return "1"
    elif code == 25:
        return "2"
    elif code == 27:
        return "3"
    elif code == 15:
        return "4"
    elif code == 30:
        return "5"
    elif code == 28:
        return "6"
    elif code == 19:
        return "7"
    elif code == 29:
        return "8"
    elif code == 31:
        return "9"
    return "?"

vText = "  "
nText = "  "
vnFlashing = False
vnTimer = ""
vnCurrentlyON = True
def vnFlashingHandler():
    global vnFlashing, vnTimer, vnCurrentlyOn
    if vnFlashing:
        vnCurrentlyOn = not vnCurrentlyOn
        if vnCurrentlyOn:
            TM.segments[14] = nText
            TM.segments[22] = vText
        else:
            TM.segments[14] = "  "
            TM.segmetns[22] = "  "
    vnTimer = threatding.Timer(0.75, vnFlashingHandler)
    vnTimer.start()

def vnFlashingStop():
    global vnFlashing, vnTimer, vnCurrentlyOn
    if vnFlashing:
        #vnTimer.cancel()
        TM.segments[14] = nText
        TM.segments[22] = vText
        vnFlashing = False

###################################################################################
# Hardware abstraction / User-defined functions.  Also, any other platform-specific
# initialization.

# This function is automatically called periodically by the event loop to check for 
# conditions that will result in sending messages to yaAGC that are interpreted
# as changes to bits on its input channels.  For test purposes, it simply polls the
# keyboard, and interprets various keystrokes as DSKY keys if present.  The return
# value is supposed to be a list of 3-tuples of the form
#   [ (channel0,value0,mask0), (channel1,value1,mask1), ...]
# and may be en empty list.  
def inputsForAGC():
    ch = get_char_keyboard_nonblock()
    ch = ch.upper()
    if ch == '_':
        ch = '-'
    elif ch == '=':
        ch = '+'
    else:
        returnValue = parseDskyKey(ch)
    if len(returnValue) > 0:
            log("Sending to yaAGC: " + oct(returnValue[0][1]) + "(mask " + oct(returnValue[0][2]) + ") -> channel " + oct(returnValue[0][0]))
    return returnValue

def updateLamps():
    # If there were actual hardware, this is where you could use
    # lampStatus[] to control the lamps.
    TM.sendCommand(0x44,0)
    if (lampStatuses["TEMP"]["isLit"] == True):
        if (lampStatuses["UPLINK ACTY"]["isLit"] == True):
            TM.sendData(1,3,0)
        else:
            TM.sendData(1,1,0)
    else:
        if (lampStatuses["UPLINK ACTY"]["isLit"] == True):
           TM.sendData(1,2,0)
        else:
           TM.sendData(1,0,0)
    if (lampStatuses["GIMBAL LOCK"]["isLit"] == True):
        if (lampStatuses["NO ATT"]["isLit"] == True):
            TM.sendData(3,3,0)
        else:
            TM.sendData(3,1,0)
    else:
        if (lampStatuses["NO ATT"]["isLit"] == True):
           TM.sendData(3,2,0)
        else:
           TM.sendData(3,0,0)
    if (lampStatuses["PROG"]["isLit"] == True):
        if (lampStatuses["DSKY STANDBY"]["isLit"] == True):
            TM.sendData(5,3,0)
        else:
            TM.sendData(5,1,0)
    else:
        if (lampStatuses["DSKY STANDBY"]["isLit"] == True):
           TM.sendData(5,2,0)
        else:
           TM.sendData(5,0,0)
    if (lampStatuses["RESTART"]["isLit"] == True):
        if (lampStatuses["KEY REL"]["isLit"] == True):
            TM.sendData(7,3,0)
        else:
            TM.sendData(7,1,0)
    else:
        if (lampStatuses["KEY REL"]["isLit"] == True):
           TM.sendData(7,2,0)
        else:
           TM.sendData(7,0,0)
    if (lampStatuses["TRACKER"]["isLit"] == True):
        if (lampStatuses["OPR ERR"]["isLit"] == True):
            TM.sendData(9,3,0)
        else:
            TM.sendData(9,1,0)
    else:
        if (lampStatuses["OPR ERR"]["isLit"] == True):
           TM.sendData(9,2,0)
        else:
           TM.sendData(9,0,0)
    if (lampStatuses["ALT"]["isLit"] == True):
        if (lampStatuses["PRIO DSP"]["isLit"] == True):
            TM.sendData(0x0b,3,0)
        else:
            TM.sendData(0x0b,1,0)
    else:
        if (lampStatuses["PRIO DSP"]["isLit"] == True):
           TM.sendData(0x0b,2,0)
        else:
           TM.sendData(0x0b,0,0)
    if (lampStatuses["VEL"]["isLit"] == True):
        if (lampStatuses["NO DAP"]["isLit"] == True):
            TM.sendData(0x0d,3,0)
        else:
            TM.sendData(0x0d,1,0)
    else:
        if (lampStatuses["NO DAP"]["isLit"] == True):
           TM.sendData(0x0d,2,0)
        else:
           TM.sendData(0x0d,0,0)
    return
updateLamps()

# This function is called by the event loop only when yaAGC has written
# to an output channel.  The function should do whatever it is that needs to be done
# with this output data, which is not processed additionally in any way by the 
# generic portion of the program. As a test, I simply display the outputs for 
# those channels relevant to the DSKY.
last10 = 1234567
last11 = 1234567
last13 = 1234567
last163 = 1234567
plusMinusState1 = 0
plusMinusState2 = 0
plusMinusState3 = 0
def outputFromAGC(channel, value):
    # These lastNN values are just used to cut down on the number of messages printed,
    # when the same value is output over and over again to the same channel, because
    # that makes debugging harder.  
    global last10, last11, last13, last163, plusMinusState1, plusMinusState2, plusMinusState3, vnFlashing
    if (channel == 0o13):
        value &= 0o3000
    if (channel == 0o10 and value != last10) or (channel == 0o11 and value != last11) or (channel == 0o13 and value != last13) or (channel == 0o163 and value != last163):
        if channel == 0o10:
            last10 = value
            aaaa = (value >> 11) & 0x0F
            b = (value >> 10) & 0x01
            ccccc = (value >> 5) & 0x1F
            ddddd = value & 0x1F
            if aaaa != 12:
                sc = codeToString(ccccc)
                sd = codeToString(ddddd)
            if aaaa == 11:
                log(sc + " -> M1   " + sd + " -> M2")
                TM.segments[22] = sc
                TM.segments[23] = sd
            elif aaaa == 10:
                log(sc + " -> V1   " + sd + " -> V2")
                vText = sc + sd
                TM.segments[14] = sc
                TM.segments[15] = sd
            elif aaaa == 9:
                log(sc + " -> N1   " + sd + " -> N2")
                nText = sc + sd
                TM.segments[6] = sc
                TM.segments[7] = sd
            elif aaaa == 8:
                log("          " + sd + " -> 11")
                TM.segments[17] = sd
            elif aaaa == 7:
                plusMinus = "  "
                if b != 0:
                    plusMinus = "1+"
                    plusMinusState1 |= 1
                    TM.segments[16] = " "
                else:
                    plusMinusState1 &= ~1
                log(sc + " -> 12   " + sd + " -> 13   " + plusMinus)
                TM.segments[18] = sc
                TM.segments[19] = sd # <--!! BUG FIX: Was 'sc'
            elif aaaa == 6:
                plusMinus = "  "
                if b != 0:
                    plusMinus = "1-"
                    plusMinusState1 |= 2
                    TM.segnents[16] = "-"
                else:
                    plusMinusState1 &= ~2
                log(sc + " -> 14   " + sd + " -> 15   " + plusMinus)
                TM.segments[20] = sc
                TM.segments[21] = sd
            elif aaaa == 5:
                plusMinus = "  "
                if b != 0:
                    plusMinus = "2+"
                    plusMinusState2 |= 1
                    TM.segments[8] = " "
                else:
                    plusMinusState2 &= ~1
                log(sc + " -> 21   " + sd + " -> 22   " + plusMinus)
                TM.segments[9] = sc
                TM.segments[10] = sd
            elif aaaa == 4:
                plusMinus = "  "
                if b != 0:
                    plusMinus = "2-"
                    plusMinusState2 |= 2
                    TM.segments[8] = "-"
                else:
                    plusMinusState2 &= ~2
                log(sc + " -> 23   " + sd + " -> 24   " + plusMinus)
                TM.segments[11] = sc
                TM.segments[12] = sd
            elif aaaa == 3:
                log(sc + " -> 25   " + sd + " -> 31")
                TM.segments[13] = sc
                TM.segments[1] = sd
            elif aaaa == 2:
                plusMinus = "  "
                if b != 0:
                    plusMinus = "3+"
                    plusMinusState3 |= 1
                    TM.segments[0] = " "
                else:
                    plusMinusState3 &= ~1
                log(sc + " -> 32   " + sd + " -> 33   " + plusMinus)
                TM.segments[2] = sc
                TM.segments[3] = sd
            elif aaaa == 1:
                plusMinus = "  "
                if b != 0:
                    plusMinus = "3-"
                    plusMinusState3 |= 2
                    TM.segments[0] = "-"
                else:
                    plusMinusState3 &= ~2
                log(sc + " -> 34   " + sd + " -> 35   " + plusMinus)
                TM.segments[4] = sc
                TM.segments[5] = sd
            elif aaaa == 12:
                vel = "VEL OFF         "
                if (value & 0x04) != 0:
                    vel = "VEL ON          "
                    updateLampStatuses("VEL", True)
                else:
                    updateLampStatuses("VEL", False)
                noAtt = "NO ATT OFF      "
                if (value & 0x08) != 0:
                    noAtt = "NO ATT ON       "
                    updateLampStatuses("NO ATT", True)
                else:
                    updateLampStatuses("NO ATT", False)
                alt = "ALT OFF         "
                if (value & 0x10) != 0:
                    alt = "ALT ON          "
                    updateLampStatuses("ALT", True)
                else:
                    updateLampStatuses("ALT", False)
                gimbalLock = "GIMBAL LOCK OFF "
                if (value & 0x20) != 0:
                    gimbalLock = "GIMBAL LOCK ON  "
                    updateLampStatuses("GIMBAL LOCK", True)
                else:
                    updateLampStatuses("GIMBAL LOCK", False)
                tracker = "TRACKER OFF     "
                if (value & 0x80) != 0:
                    tracker = "TRACKER ON      "
                    updateLampStatuses("TRACKER", True)
                else:
                    updateLampStatuses("TRACKER", False)
                prog = "PROG OFF        "
                if (value & 0x100) != 0:
                    prog = "PROG ON         "
                    updateLampStatuses("PROG", True)
                else:
                    updateLampStatuses("PROG", False)
                log(vel + "   " + noAtt + "   " + alt + "   " + gimbalLock + "   " + tracker + "   " + prog)
                updateLamps()
        elif channel == 0o11:
            last11 = value
            compActy = "COMP ACTY OFF   "
            TM.sendCommand(0x44,0)
            if (value & 0x02) != 0:
                compActy = "COMP ACTY ON    "
                TM.sendCommand(0x44,0)
                TM.sendData(0x0f,1,0)
            else:
                TM.sendData(0x0f,0,0)
            uplinkActy = "UPLINK ACTY OFF "
            if (value & 0x04) != 0:
                uplinkActy = "UPLINK ACTY ON  "
                TM.sendCommand(0x44,0)
                updateLampStatuses("UPLINK ACTY", True)
            else:
                updateLampStatuses("UPLINK ACTY", False)
            flashing = "V/N NO FLASH    "
            # !! UNCOMMENTED V/N FLASHING LOGIC !!
            if (value & 0x20) != 0:
               if not vnFlashing:
                   vnFlashing = True
                   vnCurrentlyOn = True
                   vnTimer = threading.Timer(0.75, vnFlashingHandler)
                   vnTimer.start()
               flashing = "V/N Flash     "
            else:
               if vnFlashing != False:
                   vnFlashingStop()
            log(compActy + "   " + uplinkActy + "   " + "   " + flashing)
            updateLamps()
        elif channel == 0o13:
            last13 = value
            test = "DSKY TEST       "
            if (value & 0x200) == 0:
                test = "DSKY NO TEST    "
            log(test)
            updateLamps()
        elif channel == 0o163:
            last163 = value
            if (value & 0x08) != 0:
                temp = "TEMP ON         "
                updateLampStatuses("TEMP", True)
            else:
                temp = "TEMP OFF        "
                updateLampStatuses("TEMP", False)
            if (value & 0o400) != 0:
                standby = "DSKY STANDBY ON "
                updateLampStatuses("DSKY STANDBY", True)
            else:
                standby = "DSKY STANDBY OFF"
                updateLampStatuses("DSKY STANDBY", False)
            if (value & 0o20) != 0:
                keyRel = "KEY REL ON      "
                updateLampStatuses("KEY REL", True)
            else:
                keyRel = "KEY REL OFF     "
                updateLampStatuses("KEY REL", False)
            if (value & 0o100) != 0:
                oprErr = "OPR ERR FLASH   "
                # This logic is just "ON" - flashing is handled by the server
                updateLampStatuses("OPR ERR", True) 
            else:
                oprErr = "OPR ERR OFF     "
                updateLampStatuses("OPR ERR", False)
            if (value & 0o200) != 0:
                restart = "RESTART ON    "
                updateLampStatuses("RESTART", True)
            else:
                restart = "RESTART OFF     "
                updateLampStatuses("RESTART", False)
            log(temp + "   " + standby + "   " + keyRel + "   " + oprErr + "   " + restart)
        else:
            log("Received from yaAGC: " + oct(value) + " -> channel " + oct(channel))
    return

###################################################################################
# Generic initialization (TCP socket setup).  Has no target-specific code, and 
# shouldn't need to be modified unless there are bugs.

def connectToAGC():
    global s  # Make s a global variable
    while True:
        try:
            # Create a new socket object each time
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            
            # This prevents the "false positive" connect by reusing the address
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            # Use a default (blocking) socket to connect.
            # This will wait or fail with "Connection refused".
            s.connect((TCP_IP, TCP_PORT))
            
            # NOW that we are connected, set it to non-blocking
            s.setblocking(0) 
            
            log(f"Connected to yaAGC ({TCP_IP}:{TCP_PORT})")
            return True # Return success
        
        except socket.error as msg:
            if msg.errno == 111: # Connection refused
                log("Could not connect to yaAGC (Connection refused), retrying...")
            else:
                log(f"Could not connect to yaAGC ({TCP_IP}:{TCP_PORT}), error: {msg}")
            
            time.sleep(2) # Wait 2 seconds before retrying
            
            # Clean up the failed socket
            s.close()

###################################################################################
# Event loop.  Just check periodically for output from yaAGC (in which case the
# user-defined callback function outputFromAGC is executed) or data in the 
# user-defined function inputsForAGC (in which case a message is sent to yaAGC).
# But this section has no target-specific code, and shouldn't need to be modified
# unless there are bugs.
def eventLoop():
    # Buffer for a packet received from yaAGC.
    packetSize = 4
    inputBuffer = bytearray(packetSize)
    leftToRead = packetSize
    view = memoryview(inputBuffer)
    
    didSomething = False
    
    # --- Grace Period Timer ---
    # We will not check for keys for the first 1.5 seconds
    # to allow the TM1638 to stabilize after display writes.
    start_time = time.time()
    grace_period_ended = False
    # --- END ---
    
    # We are already connected, so we go straight to the event loop.
    while True:
        if not didSomething:
            time.sleep(PULSE)
        didSomething = False
        
        # --- FIX: Set numNewBytes to -1 to start ---
        numNewBytes = -1 # Use -1 to indicate "no read yet"
        
        # Check for packet data received from yaAGC and process it.
        try:
            numNewBytes = s.recv_into(view, leftToRead)
        except socket.error as e:
            # 11 = Resource temporarily unavailable, 115 = Operation now in progress
            if e.errno == 11 or e.errno == 115: 
                pass # <--- THIS IS THE FIX. (Was numNewBytes = 0)
            else:
                log(f"Socket error on recv: {e}")
                return False # Critical error, disconnect
        except Exception as e:
            log(f"Unexpected error on recv: {e}")
            return False

        if numNewBytes == 0:
            # An orderly shutdown from the server returns 0 bytes
            # This is now ONLY triggered by a real disconnect.
            log("yaAGC server has disconnected.")
            return True # Signal to reconnect

        if numNewBytes > 0:
            view = view[numNewBytes:]
            leftToRead -= numNewBytes
            if leftToRead == 0:
                # Prepare for next read attempt.
                view = memoryview(inputBuffer)
                leftToRead = packetSize
                # Parse the packet just read, and call outputFromAGC().
                # Start with a sanity check.
                ok = 1
                if (inputBuffer[0] & 0xF0) != 0x00:
                    ok = 0
                elif (inputBuffer[1] & 0xC0) != 0x40:
                    ok = 0
                elif (inputBuffer[2] & 0xC0) != 0x80:
                    ok = 0
                elif (inputBuffer[3] & 0xC0) != 0xC0:
                    ok = 0
                # Packet has the various signatures we expect.
                if ok == 0:
                    if inputBuffer[0] != 0xff or inputBuffer[1] != 0xff or inputBuffer[2] != 0xff or inputBuffer[2] != 0xff:
                        if inputBuffer[0] != 0xff:
                            log("Illegal packet: " + hex(inputBuffer[0]) + " " + hex(inputBuffer[1]) + " " + hex(inputBuffer[2]) + " " + hex(inputBuffer[3]))
                        for i in range(1,packetSize):
                            if (inputBuffer[i] & 0xF0) == 0:
                                j = 0
                                for k in range(i,4):
                                    inputBuffer[j] = inputBuffer[k]
                                    j += 1
                                view = view[j:]
                                leftToRead = packetSize - j
                else:
                    channel = (inputBuffer[0] & 0x0F) << 3
                    channel |= (inputBuffer[1] & 0x38) >> 3
                    value = (inputBuffer[1] & 0x07) << 12
                    value |= (inputBuffer[2] & 0x3F) << 6
                    value |= (inputBuffer[3] & 0x3F)
                    outputFromAGC(channel, value)
                didSomething = True
        
        
        # --- Check if grace period is over ---
        if not grace_period_ended:
            if (time.time() - start_time) > 1.5:
                log("Keypad grace period ended. Polling enabled.")
                grace_period_ended = True
        # --- END ---

        # Check for locally-generated data
        if grace_period_ended: # Only poll for keys AFTER grace period
            try:
                externalData = inputsForAGC()
                if externalData == "":
                    echoOn(True)
                    return False # User quit
                for i in range(0, len(externalData)):
                    packetize(externalData[i])
                    didSomething = True
            except socket.error as e:
                log(f"Socket error on send: {e}")
                return True # Disconnected, signal to reconnect
            except Exception as e:
                log(f"Unexpected error on send: {e}")
                return False # Critical error

# !! NEW MASTER LOOP !!
try:
    while True:
        if connectToAGC(): # Wait for a connection
            # Discard the first spurious read to stabilize the chip.
            log("Priming TM1638 keypad...")
            TM.sendCommand(0x42, 0)
            _ = TM.getData(0)
            if not eventLoop(): # Run the loop until it exits
                # eventLoop returned False, means a critical error or user quit
                break
        
        log("Restarting connection loop...")
        s.close() # Ensure socket is closed
        TM.clearDisplay() # Clear DSKY on disconnect
        updateLamps() # Will clear lamps
        time.sleep(3) # Pause before retrying

except KeyboardInterrupt:
    log("\nExiting by user request.")
    if 's' in globals():
        s.close()
    echoOn(True)
    TM.clearDisplay()
    os._exit(0)

os._exit(0)