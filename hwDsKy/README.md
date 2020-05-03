# Construction Notes

CM Commander yaDSKY connnects to Port 19697
CM Navigation DSKY 19698
LM connection to DSKY is Port 19797 

Monitoring the commander's channel is done by:
```
socat TCP:127.0.0.1:19697
```

Look for Channel 0163 (Octal) for from CPU to DSKY
Bit 1: AGC
Bit 4: Temp
Bit 5: KEY REL
Bit 6: VERB/NOUN
But 7: OPER ERR
Bit 8: RESTART
Bit 9: STBY
Bit 10: EL

Look for Channel 10 (Octal) for driving 7 Segment DSKY

sign Data1 = 1
Data1 = 11,12,13,14,15
sign Data2 = 2
Data2 = 21,22,23,24,25
sign Data3 = 3
Data3 = 31,32,33,34,35

### Table 1 - Value to Character Conversion
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

### Table 2 - Value to Location Conversion
| AAAA | B | CCCCC Represents | DDDDD  Represents |
|---------|------|------------------|--------------------|
| 1011 (binary) or 11 (decimal) | - | PROG1 | PROG2 |
| 1010 (binary) or 10 (decimal)	| - | VERB1 | VERB2 |
| 1001 (binary) or 9 (decimal)	| - | NOUN1 | NOUN2 |
| 1000 (binary) or 8 (decimal)	| - |   | DATA1-1 |
| 0111 (binary) or 7 (decimal) | 1+ DATA1-0 | DATA1-2 | DATA1-3 |
| 0110 (binary) or 6 (decimal) | 1- | DATA1-4 | DATA1-5 |
| 0101 (binary) or 5 (decimal)	2+
Digit 21
Digit 22
0100 (binary) = 4 (decimal)	2-
Digit 23
Digit 24
0011 (binary) = 3 (decimal)	
Digit 25
Digit 31
0010 (binary) = 2 (decimal)	3+
Digit 32
Digit 33
0001 (binary)  = 1 (decimal)	3-
Digit 34
Digit 35
1100 (binary) = 12 (decimal)	This is an exception, departing from the BCCCCCDDDDD pattern.  Instead:
Bit 1 lights the "PRIO DISP" indicator.
Bit 2 lights the "NO DAP" indicator.
Bit 3 lights the  "VEL" indicator.
Bit 4 lights the "NO ATT" indicator.
Bit 5 lights the  "ALT" indicator.
Bit 6 lights the "GIMBAL LOCK" indicator.
Bit 8 lights the "TRACKER" indicator.
Bit 9 lights the "PROG" indicator.

Ex: "+12345" in Data1 10000 00000 00011, 01111 11001 11011, 01100 01111 11110 (binary)
