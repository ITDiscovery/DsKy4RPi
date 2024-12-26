KIM-1 Emulator

This platform seems to be a great candidate to emulate a KIM-1 6502 trainer.
There is a 6502C emulator code set.

Should be fun to do in Python?
https://github.com/docmarionum1/py65emu/tree/main

https://web.archive.org/web/20220831205542/http://users.telenet.be/kim1-6502/

KIM-1 has two 6530's
U2: PA0-6,PB1-4   To Keyboard and Display
    PB????    To Tape and TTY

U3: Application Connector


KIM-1 Memory Map

0000-00FF   RAM used for zero page and indirect memory addressing
            operation.
0100-01FF   RAM used for stack processing and for absolute 
            addressing.
0200-3FFF   Normally RAM (1K)
4000-7FFF   Normally I/O
8000-FFF9   Program storage normally ROM.
FFFA        Vector low address for NMI.
FFFB        Vector high address for NMI.
FFFC        Vector low address for RESET.
FFFD        Vector high address for RESET.
FFFE        Vector low address for IRQ + BRK.
FFFF        Vector high address for IRQ + BRK.

| ADDRESS |      AREA      | LABEL |              FUNCTION               |
|         |                |       |                                     |
|  00EF   |                | PCL   | Program Counter - Low Order Byte    |
|  00F0   |                | PGH   | Program Counter - High Order Byte   |
|  00F1   |     Machine    | P     | Status Register                     |
|  00F2   |     Register   | SF    | Stack Pointer                       |
|         |     Storage    |       |                                     |
|  00F3   |     Buffer     | A     | Accumulator                         |
|  00F4   |                | Y     | Y-Index Register                    |
|  00F5   |                | X     | X-Index Register                    |
|  1700   |                | PAD   | 6530-003 A Data Register            |
|  1701   |   Application  | PADD  | 6530-003 A Data Direction Register  |
|  1702   |        I/O     | PBD   | 6530-003 B Data Register            |
|  1703   |                | PBDD  | 6530-003 B Data Direction Register  |
|  1704   |                |       | 6530-003 Interval Timer             |
|         | Interval Timer |       |   (See Section 1.6 of               |
|         |                |       |    Hardware Manual)                 |
|  170F   |                |       |                                     |
|  17F5   |                | SAL   | Starting Address - Low Order Byte   |
|  17F6   |   Audio Tape   | SAH   | Starting Address - High Order Byte  |
|  17F7   |   Load & Dump  | EAL   | Ending Address - Low Order Byte     |
|  17F8   |                | EAH   | Ending Address - High Order Byte    |
|  17F9   |                | ID    | File Identification Number          |
|  l7FA   |                | NMIL  | NMI Vector - Low Order Byte         |
|  l7FB   |                | NMIH  | NMI Vector - High Order Byte        |
|  l7FC   |   Interrupt    | RSTL  | RST Vector - Low Order Byte         |
|         |    Vectors     |       |                                     |
|  17FD   |                | RSTH  | RST Vector - High Order Byte        |
|  l7FE   |                | IRQL  | IRQ Vector - Low Order Byte         |
|  17FF   |                | IRQH  | IRQ Vector - High Order Byte        |
|  1800   |                | DUMPT | Start Address - Audio Tape Dump     |
|         |  Audio Tape    |       |                                     |
|  1873   |                | LOADT | Start Address - Audio Tape Load     |
|  1C00   | STOP Key + SST |       | Start Address for NMI using KIM     |
|         |                |       | "Save Nachine" Routine (Load in     |
|         |                |       | 17FA & 17FB)                        |
|  17F7   |   Paper Tape   | EAL   | Ending Address - Low Order Byte     |
|  17F8   |    Dump (Q)    | EAH   | Ending Address - High Order Byte    |

Special Memory Addresses


#Get Keypress
#TM.sendCommand(0x42,0)
#keyval = TM.getData(0)
#keynum = 0
#if (keyval != [0,0,0,0]):
    #print (keyval)
    #for x in KeyDict:
    #if (KeyDict[x] == keyval):
    #keynum = x

#Top Row: TM.segments[4]
#4th Row Left:  TM.segments[14]
#4th Row Right: TM.segments[6]
#3nd Row:    TM.segments[18]
#2nd Row:    TM.segments[10]
#Bottom Row: TM.segments[2]

f = open("KIM1.rom", "rb")  # Open your rom

# define your blocks of memory.  Each tuple is
# (start_address, length, readOnly=True, value=None, valueOffset=0)
m = MMU([
        (0x00, 0x200), # Create RAM with 512 bytes
        (0x1000, 0x4000, True, f) # Create ROM starting at 0x1000 with your program.
        ])

# Create the CPU with the MMU and the starting program counter address
# You can also optionally pass in a value for stack_page, which defaults
# to 1, meaning the stack will be from 0x100-0x1ff.  As far as I know this
# is true for all 6502s, but for instance in the 6507 used by the Atari
# 2600 it is in the zero page, stack_page=0.
c = CPU(mmu, 0x1000)

# Do this to execute one instruction
c.step()

# You can check the registers and memory values to determine what has changed
#print(c.r.a) 	# A register
#print(c.r.x) 	# X register
#print(c.r.y) 	# Y register
#print(c.r.s) 	# Stack Pointer
#print(c.r.pc) 	# Program Counter
#print(c.cc)     # Print the number of cycles that passed during the last step.
# This number resets for each call to `.step()`
#print(c.r.getFlag('C')) # Get the value of a flag from the flag register.
#print(mmu.read(0xff)) # Read a value from memory

#KIM-1 Keycodes
# curkey==0 is 0xFF: illegal keycode 
# curkey>='0') & (curkey <='9')) send curkey;
#  if ((curkey>='A') & (curkey <='F')) return(curkey-'A'+10);
#  0x10; // AD address mode
#  0x11; // DA data mode
#  '+' // 0x12 step
#  CTRL-G 0x13 GO
#  CTRL-P 0x14 PC mode
#  CTRL-R Reset is hardware interupt and should be handled in main loop!
#  CTRL-T for ST key is NMI and should be handled in main loop!

#RIOT2 explanation: better emulation of LED display through simulated hardware rather than 2014's ROM patch
#The RIOT-002 chip is used to drive the LEDs, read the keypad, and control TTY and tape.
#KIM Uno only emulates the LED driver and timer hardware; the keypad, TTY and tape are emulated on a higher abstraction level in the ROM
#On the real KIM-1, the keyboard columns are PA0-PA6 and the rows are selected through 
#     the display  columns are PA0-PA6 and the segment led is decoded from PB 0000 1110
#     teletype mode is detected when  = 1.
#     teletype uses PB0, PB5, PA7
#1740 Data port A            Selects pattern to show on a segment LED (PA0-6) and TTY (PA7)
#1741 Data Direction port A  Are the GPIO pins set to input or output?
#1742 Data port B            Selects which of the 6 segment LEDs is lit up (PB1-3), 
#                            and also: PB0 (TTY), PB4 ???, PB5 (TTY/tape input?), PB 6(RIOT internal, ChipSelect), PB7 (tape output)
#1743 Data direction port B  Are the GPIO pins set to input or output?