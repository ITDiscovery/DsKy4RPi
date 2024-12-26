#KIM 1 Hardware Abstraction

from rpi_TM1638 import TMBoards
from py65emu.cpu import CPU
from py65emu.mmu import MMU

DIO = 19
CLK = 13
STB = 26,6,5
TM = TMBoards(DIO,CLK,STB,3)
BRIGHT = 2
SECSFLAG = 0

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

