#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
from datetime import datetime, timedelta
import pytz
from rpi_TM1638 import TMBoards

DIO = 19
CLK = 13
STB = 26,6,5
TM = TMBoards(DIO,CLK,STB,3)
BRIGHT = 2
SECSFLAG = 0

utc_tz = pytz.utc
cst_tz = pytz.timezone("America/Chicago")

# Timezone Delta for Tokyo
tzd = 9
tzd_delay = 0

LampDict = {0x01,0x03,0x05,0x07,0x09,0x0b,0x0d,0x0f}
KeyDict = {}
KeyDict[1] = [4,0,0,0]
KeyDict[2] = [64,0,0,0]
KeyDict[3] = [0,4,0,0]
KeyDict[4] = [0,64,0,0]
KeyDict[5] = [0,0,4,0]
KeyDict[6] = [0,0,64,0]
KeyDict[7] = [0,0,0,4]
KeyDict[8] = [0,0,0,64]
KeyDict[9] = [2,0,0,0]
KeyDict[10] = [32,0,0,0]
KeyDict[11] = [0,2,0,0]
KeyDict[12] = [0,32,0,0]
KeyDict[13] = [0,0,2,0]
KeyDict[14] = [0,0,32,0]
KeyDict[15] = [0,0,0,2]
KeyDict[16] = [0,0,0,32]
KeyDict[17] = [1,0,0,0]
KeyDict[18] = [16,0,0,0]
KeyDict[19] = [0,1,0,0]

TM.clearDisplay()
TM.turnOn(BRIGHT)

while True:

    #Get Keypress
    TM.sendCommand(0x42,0)
    keyval = TM.getData(0)
    keynum = 0
    if (keyval != [0,0,0,0]):
        #print (keyval)
        for x in KeyDict:
            if (KeyDict[x] == keyval):
                keynum = x
                #TM.segments[22] = "{:02}".format(keynum)
    # Verb Key Changes Brightnes
    if keynum == 18:
       BRIGHT = BRIGHT + 1
       if BRIGHT == 8:
            BRIGHT = 0
       TM.turnOn(BRIGHT)
    # + Key Adds 1 to 3rd Line TZ
    if keynum == 15:
        tzd = tzd + 1
        tzd_delay = 100
        if tzd == 13:
             tzd = -12
    # - Key Subs 1 to 3rd Line TZ
    if keynum == 16:
        tzd_delay = 100
        tzd = tzd -1
        if tzd == -13:
             tzd = 12

    # Display TZDs in 16,8,0
    if (tzd_delay > 0):
       TM.segments[16] = str(tzd).zfill(2)
       tzd_delay = tzd_delay -1
    else:
       TM.segments[16] = "  "

    # KeyRel Key Turns on Secs
    if keynum == 5:
        if SECSFLAG == 0:
            SECSFLAG = 1
        else:
            SECSFLAG = 0
    if SECSFLAG:
        TM.segments[22] = utc_now.strftime("%S")
    else:
        TM.segments[22] = "  "



    cst_now = cst_tz.localize(datetime.now())
    utc_now = cst_now.astimezone(utc_tz)
    tzd_now = utc_now + timedelta(hours=tzd)

    TM.segments[14] = utc_now.strftime("%m")
    TM.segments[6] = utc_now.strftime("%d")
    TM.segments[10] = utc_now.strftime("%H.%M")
    TM.segments[18] = tzd_now.strftime("%H.%M")
    TM.segments[2] = cst_now.strftime("%H.%M")
    time.sleep(0.1)
