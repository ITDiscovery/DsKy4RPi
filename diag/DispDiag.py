# coding=utf-8

"""This file shows some use of the rpi_TM1638 librairy"""
import sys, random
from time import sleep
from rpi_TM1638 import TMBoards

# my GPIO settings
# (one TM1638 board connected to GPIO19 for dataIO, GPIO13 for Clock, and GPIO26 for the STB)
DIO = 19
CLK = 13
STB = 26,6,5
# STB = 26,6,5   # in case you have two TM1638 boards, connected to GPIO06 and GPIO26

# initialeze TM1638
TM = TMBoards(DIO, CLK, STB, 3)

TM.clearDisplay()

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

# Get the arguments (if any)


# LED Test Routine -led
def led():
    for x in LampDict:
        TM.segments[22] = "{:02}".format(x)
        TM.sendCommand(0x44,0)
        # First Bank of LEDs
        TM.sendData(x,1,0)
        sleep(1)
        # Second Bank of LEDs
        TM.segments[22] = "{:02}".format(x+1)
        TM.sendData(x,2,0)
        sleep(1)
        # Turn off LEDs
        TM.sendData(x,0,0)


def d3():
# 7 Segment Test for numbers (works)
	TM.segments[0] = "8.8.8.8.8.8.8.8."
	sleep(3)
	for x in range(99):
		TM.segments[0] = "{:06}".format(x)
		TM.segments[6] = "{:02}".format(x)
		sleep(.05)
def d2():
	TM.segments[8] = "8.8.8.8.8.8.8.8."
	sleep(3)
	for x in range(99):
		TM.segments[8] = "{:06}".format(x)
		TM.segments[14] = "{:02}".format(x)
		sleep(.05)

def d1():
	TM.segments[16] = "8.8.8.8.8.8.8.8."
	sleep(3)
	for x in range(99):
                TM.segments[16] = "{:06}".format(x)
                TM.segments[22] = "{:02}".format(x)
                sleep(.05)

def all():
	TM.segments[0] = "8.8.8.8.8.8.8.8."
	TM.segments[8] = "8.8.8.8.8.8.8.8."
	TM.segments[16] = "8.8.8.8.8.8.8.8."
	sleep(3)
	TM.segments[0] = "        "
	TM.segments[8] = "        "
	TM.segments[16] = "        "
	for x in range(0,24):
		for y in range(0,9):
			TM.segments[x,y] = True
			sleep(.2)
			TM.segments[x,y] = False
def fun():
	while True:
		TM.segments[0] = "{:08}".format(random.randrange(99999999))
		TM.segments[8] = "{:08}".format(random.randrange(99999999))
		TM.segments[16] = "{:08}".format(random.randrange(99999999))
		sleep(.5)
def keypress():
# Get Keypress -sw
	while True:
		sleep(.001)
		TM.sendCommand(0x42,0)
		keyval = TM.getData(0)
		keynum = 0
		if (keyval != [0,0,0,0]):
			#print (keyval)
			for x in KeyDict:
				if (KeyDict[x] == keyval):
					keynum = x
		TM.segments[4] = "{:02}".format(keynum)

def main():
	if (len(sys.argv) < 2):
		d3()
		d2()
		d1()
		led()
		all()
		keypress()
	else:
		if (sys.argv[1]=="-d3"):
			d3()
		if (sys.argv[1]=="-d2"):
			d2()
		if (sys.argv[1]=="-d1"):
			d1()
		if (sys.argv[1]=="-led"):
			led()
		if (sys.argv[1]=="-sw"):
			keypress()
		if (sys.argv[1]=="-all"):
			all()
		if (sys.argv[1]=="-fun"):
			fun()
		else:
			all()

if __name__ == "__main__":
	main()
