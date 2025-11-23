# hardware/interface.py
import time
import config
# Import the raw driver you placed in the hardware folder
from .TMBoards import TMBoards 

class DskyHardware:
    def __init__(self):
        # Initialize with pins from config
        self.tm = TMBoards(config.DIO, config.CLK, config.STB_LIST, 3)
        self.tm.clearDisplay()
        
        # State tracking for edge detection (Key press vs Hold)
        self.last_key_state = [0, 0, 0, 0]
        self.pressed_pro = False
        self.time_pro = 0

        # Mapping DSKY logical names to TM1638 Segment Indices
        # Derived from piDSKY4.py outputFromAGC
        self.digit_map = {
            'V1': 14, 'V2': 15,
            'N1': 6,  'N2': 7,
            'M1': 22, 'M2': 23,
            '11': 17, # Row 1
            '12': 18, '13': 19, 'S1': 16, # Row 1 (S1 is Sign 1)
            '14': 20, '15': 21,
            '21': 9,  '22': 10, 'S2': 8,  # Row 2
            '23': 11, '24': 12,
            '25': 13, '31': 1,          # Note the jump to index 1!
            '32': 2,  '33': 3,  'S3': 0,  # Row 3
            '34': 4,  '35': 5
        }

    def clear_all(self):
        self.tm.clearDisplay()

    def get_key_event(self):
        """
        Reads keys and returns a character ONLY on a new press.
        Returns None if no change or key released.
        """
        # Use the robust raw read from your updated library
        # '0' implies we only read the first board (Strobe 26)
        current_keys = self.tm.read_keys_raw(0)
        
        char_to_send = None
        
        # Logic taken from piDSKY4.py: get_char_keyboard_nonblock
        if current_keys == self.last_key_state:
            return None # No change
            
        if current_keys == [0, 0, 0, 0]:
            # Key Release Detected
            self.last_key_state = [0, 0, 0, 0]
            print("[HW] Key Released")
            return 'K' # Special code for Key Release
        
        # If we are here, a NEW key was pressed
        self.last_key_state = current_keys
        
        # Convert list/tuple to tuple for dict lookup
        key_tuple = tuple(current_keys)
        
        key_id = config.KEY_BYTES.get(key_tuple)
        if key_id:
            char_to_send = config.KEY_MAP.get(key_id)
            print(f"[HW] Key Pressed: {char_to_send} {current_keys}")

            # PRO Special Handling (fake press/release logic from original)
            if char_to_send in ['P', 'p']:
                self.pressed_pro = True
                self.time_pro = time.time()
        
        return char_to_send

    def check_pro_release(self):
        """Handles the automatic release of the PRO key after 0.75s"""
        if self.pressed_pro and (time.time() > self.time_pro + 0.75):
            self.pressed_pro = False
            return 'PR' # The code for PRO Release
        return None

    def set_digit(self, position, value_code):
        """
        position: 'V1', 'N2', '11', 'S1', etc.
        value_code: The AGC 5-bit code (int) or a string ("+", "-")
        """
        index = self.digit_map.get(position)
        if index is None: return

        # 1. Determine the character to show
        if isinstance(value_code, int):
            # Default to space " " if code is unknown, NOT "?"
            char_str = config.DIGIT_CODE.get(value_code, " ") 
        else:
            char_str = value_code 

        # 2. Hardware compatibility fix
        # 7-segment displays cannot show "+", so map it to Blank.
        if char_str == "+":
            char_str = " "

        # 3. Safety Write
        try:
            self.tm.segments[index] = char_str
        except ValueError:
            # If TMBoards still hates the character, show nothing instead of crashing
            print(f"[HW] Warning: skipped unsupported char '{char_str}' at {position}")
            self.tm.segments[index] = " "
            
    def set_sign(self, row, value_byte):
        """
        Updates the +/- signs.
        row: 1, 2, or 3
        value_byte: The raw byte from AGC (bit 10 determines sign)
        """
        # Logic from outputFromAGC aaaa=7,6,5,4,2,1
        # This is simplified; the main loop will extract the bit
        sign_char = " "
        if value_byte != 0: # If bit is set
            sign_char = "+" if row == 1 else "+" # Logic usually varies by row in AGC, handling in main
            # Wait, standard AGC logic:
            # + is usually code 1, - is code 2 in specific registers
            # But here we just receive a bit.
            # Let's just allow passing the string directly.
            pass