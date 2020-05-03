# Software Construction Notes

CM Commander yaDSKY connnects to Port 19697
CM Navigation DSKY 19698
LM connection to DSKY is Port 19797 

Monitoring the commander's DSKY channel is done by:
```
sudo tcpdump -X -i lo port 19697
```
Each data packet consists of 4 bytes, arranged in bit-fields as follows (in order of transmission):
00utpppp 01pppddd 10dddddd 11dddddd

## Look for Channel 10 (Octal) for driving 7 Segment DSKY

### Table 1 - Value to Location Conversion
| Area | AAAA | B | CCCCC Represents | DDDDD  Represents |
|-----|---------|------|------------------|--------------------|
| 1 | 1011 (binary) or 11 (decimal) | - | PROG1 | PROG2 |
| 2 | 1010 (binary) or 10 (decimal) | - | VERB1 | VERB2 |
| 3 | 1001 (binary) or 9 (decimal) | - | NOUN1 | NOUN2 |
| 4 | 1000 (binary) or 8 (decimal) | - |   | DATA1-2 |
| 5 | 0111 (binary) or 7 (decimal) | DATA1-1 Blank | DATA1-3 | DATA1-4 |
| 6 | 0110 (binary) or 6 (decimal) | DATA1-1 - | DATA1-5 | DATA1-6 |
| 7 | 0101 (binary) or 5 (decimal) | DATA2-1 Blank | DATA2-2 | DATA2-3 |
| 8 | 0100 (binary) or 4 (decimal) | DATA2-2 - | DATA2-4 | DATA2-5 |
| 9 | 0011 (binary) or 3 (decimal) | DATA3-1 Blank | DATA2-6 | DATA3-2 |
| 10 | 0010 (binary) or 2 (decimal) | DATA3-1 Blank | DATA3-3 | DATA3-4 |
| 11 | 0001 (binary) or 1 (decimal) | DATA3-1 - | DATA3-5 | DATA3-6 |
|  | 1100 (binary) = 12 (decimal) | 	Lamps: | | |
|  | Bit 1 | PRIO DISP | LED? |
|  | Bit 2 | NO DAP | LED? |
|  | Bit 3 | VEL | LED6 |
|  | Bit 4 | NO ATT | LED10 |
|  | Bit 5 | ALT | LED7 |
|  | Bit 6 | GIMBAL LOCK | LED2 |
|  | Bit 8 | TRACKER | LED5 |
|  | Bit 9 | PROG | LED3 |

### Table 2 - Value to Character Conversion
| Value for CCCCC or DDDDD | Displays as |
|------------------------|-----------|
| 00000 (binary) = 0 (decimal) | Blank |
| 10101 (binary) = 21 (decimal) | 0 |
| 00011 (binary) = 3 (decimal) | 1 |
| 11001 (binary) = 25 (decimal)|  2 |
| 11011 (binary) = 27 (decimal) | 3 |
| 01111 (binary) = 15 (decimal) | 4 |
| 11110 (binary) = 30 (decimal) | 5 |
| 11100 (binary) = 28 (decimal) | 6 |
| 10011 (binary) = 19 (decimal) | 7 |
| 11101 (binary) = 29 (decimal) | 8 |
| 11111 (binary) = 31 (decimal) | 9 |

Ex: 
|                   | aaaa b ccccc ddddd | aaaa b ccccc ddddd | aaaa b ccccc ddddd |
| "+12345" in Data1 | 1000 0 00000 00011 | 0111 1 11001 11011 | 0110 0 01111 11110 (binary) |
| ------------------|--------------------|--------------------|----------------------------|
|                   | Area4   N/C   1    | Area5    2     3   | Area6    4     5 |
| "-98765: in Data2 | 0101 0 11111 11101 | 0100 1 10011 11100 | 0011 ? 11110 ????? |
|                   | Area7    9     8   | Area8    7     6   | Area9    5     ? | 

## Look at Channel 11 (octal)
Contains various flag bits used for driving individual indicator lamps, and for other purposes.  Bits 1-7 are latching, while bits 8-15 are presumably one-time strobes. The bits which are relevant to proposed Virtual AGC software are:

| Output Bit |  Usage | haDSKY | 
|------------|--------|--------|
| 2 | COMP ACTY | LED8 |
| 3 | UPLINK ACTY | LED9 |
| 4 | TEMP | LED5 |
| 5 | KEY REL | LED12 |
| 6 | Flashes VERB/NOUN display |  |
| 7 | OPR ERR | LED13 |

## Look for Channel 0163 (Octal) for from CPU to DSKY
Bit 1: AGC
Bit 4: Temp (LED5)
Bit 5: KEY REL (LED12)
Bit 6: VERB/NOUN
But 7: OPER ERR
Bit 8: RESTART
Bit 9: STBY (LED11)
Bit 10: EL

## Look at Channel 15 (octal) 
Used for inputting keystrokes from the DSKY. There are 19 keys, and a 5-bit keycode appears in bits 5-1 of this input channel.  A keystroke triggers interrupt #5, causing the software to examine the channel. However, the interrupt mechanism occurs entirely within yaAGC, and should not be of concern to a DSKY developer. I believe that the keycode appears when the key is newly pressed, and then disappears, but I can't prove that at the moment.

| Key | Keycode | SW | Code |
|----|--------------|------|-------|
| 0 | 10000 (binary) = 16 (decimal) | 17 | 1,0,0,0 |
| 1 | 00001 (binary) = 1 (decimal)  | 14 | 0,0,32,0 |
| 2 | 00010 (binary) = 2 (decimal) | 11 | 0,2,0,0 |
| 3 | 00011 (binary) = 3 (decimal) | 8 | 0,0,0,64 |
| 4 | 00100 (binary) = 4 (decimal) | 13 | 0,0,2,0 |
| 5 | 00101 (binary) = 5 (decimal) | 10 | 32,0,0,0 |
| 6 | 00110 (binary) = 6 (decimal) | 7 | 0,0,0,4 |
| 7 | 00111 (binary) = 7 (decimal) | 12 | 0,32,0,0 |
| 8 | 01000 (binary) = 8 (decimal) | 9 | 2,0,0,0 |
| 9 | 01001 (binary) = 9 (decimal) | 6 | 0,0,64,0 |
| VERB | 10001 (binary) = 17 (decimal) | 18 | 16,0,0,0 |
| RSET | 10010 (binary) = 18 (decimal) | 2 | 64,0,0,0 | 
| KEY REL | 11001 (binary) = 25 (decimal) | 5 | 0,0,4,0 |
| + | 11010 (binary) = 26 (decimal) | 15 | 0,0,0,2 |
| - | 11011 (binary) = 27 (decimal) | 16 | 0,0,0,32 |
| ENTR | 11100 (binary) = 28 (decimal) | 1 | 4,0,0,0 |
| CLR | 11110 (binary) = 30 (decimal) | 3 | 0,4,0,0 |
| NOUN | 11111 (binary) = 31 (decimal) | 19 | 0,1,0,0 |
| PRO or STBY | (See below.) | 4 | 0,64,0,0 | 

Input Channel 32 (octal)
Bit 14 set indicates that the PRO (STBY) key is currently pressed.  The logic is inverted, so that the bit becomes 0 when the key is pressed, and is 1 when the key is not pressed.

The other bits of this channel relate to the engines, and will not be described here since Virtual AGC presently includes no engine simulations.
