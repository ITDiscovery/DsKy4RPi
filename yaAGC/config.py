# config.py

# --- Network Configuration ---
AGC_HOST = 'localhost'
AGC_PORT = 19798
READ_TIMEOUT = 0.05

# --- GPIO Configuration (BCM Numbering) ---
# Matching piDSKY4.py
DIO = 19
CLK = 13
STB_LIST = [26, 6, 5]  # The order matters! [Board 0, Board 1, Board 2]

# --- AGC Channels (Octal) ---
CHAN_DISPLAY = 0o10   
CHAN_LAMPS   = 0o11   
CHAN_TEST    = 0o13   
CHAN_KEYPAD  = 0o15   
CHAN_FLAGS   = 0o163  

# --- Keypad Mapping (Raw TM1638 byte -> Char) ---
# Derived from 'keyDict' and 'charxlate' in piDSKY4.py
KEY_MAP = {
    1: '\n', 2: 'R', 3: 'C', 4: 'P', 5: 'K',
    6: '9', 7: '6', 8: '3', 9: '8', 10: '5',
    11: '2', 12: '7', 13: '4', 14: '1',
    15: '+', 16: '-', 17: '0', 18: 'V', 19: 'N'
}

# --- TM1638 Raw Key Codes (for lookup) ---
# Maps the raw byte array [x,0,0,0] or [0,x,0,0] etc to an ID 1-19
KEY_BYTES = {
    (4,0,0,0): 1,  (64,0,0,0): 2,  (0,4,0,0): 3,  (0,64,0,0): 4,
    (0,0,4,0): 5,  (0,0,64,0): 6,  (0,0,0,4): 7,  (0,0,0,64): 8,
    (2,0,0,0): 9,  (32,0,0,0): 10, (0,2,0,0): 11, (0,32,0,0): 12,
    (0,0,2,0): 13, (0,0,32,0): 14, (0,0,0,2): 15, (0,0,0,32): 16,
    (1,0,0,0): 17, (0,1,0,0) : 18, (16,0,0,0): 19
}

# --- Display Decoding (Agc Code -> String) ---
DIGIT_CODE = {
    0: " ", 21: "0", 3: "1", 25: "2", 27: "3", 15: "4",
    30: "5", 28: "6", 19: "7", 29: "8", 31: "9"
}

# --- GPIO Pin Definitions (BCM Numbers) ---
# Lamps: Pins 11(17), 13(27), 15(22)
# Switches: Pins 36(16), 38(20), 40(21)

GPIO_PINS = {
    # Try this mapping first: Latch, Clock, Data order
    'L_LATCH': 20,  # Pin 38
    'L_CLK':   21,  # Pin 40
    'L_DATA':  16,  # Pin 36

    'S_LATCH': 16,  # Pin 36
    'S_CLK':   20,  # Pin 38
    'S_DATA':  21   # Pin 40
}