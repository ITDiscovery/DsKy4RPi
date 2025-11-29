import gpiod
import time
from gpiod.line import Direction, Value, Bias
from typing import Optional, Tuple

# --- HARDWARE CONSTANTS ---

# BlinkinBoard (74HC595/74HC165)
BB_DEFAULT_LED_CLK = 21
BB_DEFAULT_LED_LATCH = 20
BB_DEFAULT_LED_DATA = 16
BB_DEFAULT_SW_CLK = 17
BB_DEFAULT_SW_LATCH = 22
BB_DEFAULT_SW_DATA = 27
BB_CONSUMER = "blinkin_driver"

# TM1638 (DSKY Interface)
TM_DEFAULT_DIO = 19
TM_DEFAULT_CLK = 13
TM_DEFAULT_STB = (26, 6, 5)  # Can be a single pin or a tuple of pins
TM_CONSUMER = "rpi-TM1638"
TM_READ_MODE = 0x02
TM_WRITE_MODE = 0x00
TM_INCR_ADDR = 0x00
TM_FIXED_ADDR = 0x04
TM_CLOCK_DELAY = 10e-6 # 10us delay for TM1638 bit-banging

class UnifiedSimPitDriver:
    """
    Unified Driver for Blinkin' Board (74HC595/74HC165) and TM1638-based DSKY
    hardware, utilizing a single gpiod.request_lines() call to prevent 
    "Device or resource busy" errors.
    """

    def __init__(self, 
                 # Global Config
                 chip_name: str = "gpiochip4",
                 
                 # BlinkinBoard (BB) Output Config (74HC595)
                 bb_led_clk: int = BB_DEFAULT_LED_CLK, 
                 bb_led_latch: int = BB_DEFAULT_LED_LATCH, 
                 bb_led_data: int = BB_DEFAULT_LED_DATA,
                 num_led_chips: int = 5,
                 led_inversion_mask: int = 0x0,
                 
                 # BlinkinBoard (BB) Input Config (74HC165)
                 bb_sw_clk: int = BB_DEFAULT_SW_CLK,
                 bb_sw_latch: int = BB_DEFAULT_SW_LATCH,
                 bb_sw_data: int = BB_DEFAULT_SW_DATA,
                 num_switch_chips: int = 4,
                 sw_inversion_mask: int = 0x0,

                 # TM1638 Config
                 tm_dio: int = TM_DEFAULT_DIO,
                 tm_clk: int = TM_DEFAULT_CLK,
                 tm_stb: Tuple[int, ...] = TM_DEFAULT_STB,
                 tm_brightness: int = 3,
                 
                 # Timing Tuning
                 bb_latch_delay: float = 0.000001, # 1us
                 bb_clock_delay: float = 0.000004): # 4us
        
        # 1. Store Pin and Logic Config
        
        # BB Pins
        self.bb_led_clk = bb_led_clk
        self.bb_led_latch = bb_led_latch
        self.bb_led_data = bb_led_data
        self.bb_sw_clk = bb_sw_clk
        self.bb_sw_latch = bb_sw_latch
        self.bb_sw_data = bb_sw_data
        
        # TM Pins
        self.tm_dio = tm_dio
        self.tm_clk = tm_clk
        self.tm_stb = tm_stb if isinstance(tm_stb, tuple) else (tm_stb,)
        self.tm_brightness = tm_brightness

        # Logic Config
        self.num_led_bits = num_led_chips * 8
        self.num_sw_bits = num_switch_chips * 8
        self._chip_path = f"/dev/{chip_name}"
        
        self.led_inversion_mask = led_inversion_mask
        self.sw_inversion_mask = sw_inversion_mask
        
        self.bb_latch_delay = bb_latch_delay
        self.bb_clock_delay = bb_clock_delay
        
        self._led_buffer = 0
        self.request: Optional[gpiod.LineRequest] = None

        # 2. Perform Single Hardware Initialization
        self._initialize_hardware()
        
        # 3. Initialize TM1638 state
        # Clk and Stb <- High for every TM
        self._set_tm_stb(True, None)
        self._set(self.tm_clk, True) # Set CLK high
        self.turnOn(self.tm_brightness)
        self.clearDisplay()

    def _initialize_hardware(self):
        """
        Performs the single gpiod.request_lines() call for all pins.
        """
        try:
            config = {}
            
            # --- BB OUTPUTS (74HC595) ---
            # Latch ACTIVE (High), Clock/Data INACTIVE (Low)
            config[self.bb_led_latch] = gpiod.LineSettings(
                direction=Direction.OUTPUT, output_value=Value.ACTIVE)
            config[self.bb_led_clk] = gpiod.LineSettings(
                direction=Direction.OUTPUT, output_value=Value.INACTIVE)
            config[self.bb_led_data] = gpiod.LineSettings(
                direction=Direction.OUTPUT, output_value=Value.INACTIVE)
            
            # --- BB INPUTS (74HC165) ---
            # Idle State: Latch HIGH, Clock LOW. Data is INPUT.
            config[self.bb_sw_latch] = gpiod.LineSettings(
                direction=Direction.OUTPUT, output_value=Value.ACTIVE)
            config[self.bb_sw_clk] = gpiod.LineSettings(
                direction=Direction.OUTPUT, output_value=Value.INACTIVE)
            config[self.bb_sw_data] = gpiod.LineSettings(direction=Direction.INPUT) 

            # --- TM1638 PINS ---
            # CLK is always output, default low (INACTIVE)
            config[self.tm_clk] = gpiod.LineSettings(
                direction=Direction.OUTPUT, output_value=Value.INACTIVE)
            
            # STB lines are always output, default low (INACTIVE)
            for pin in self.tm_stb:
                config[pin] = gpiod.LineSettings(
                    direction=Direction.OUTPUT, output_value=Value.INACTIVE)

            # DIO is output by default (will be reconfigured for reads)
            config[self.tm_dio] = gpiod.LineSettings(
                direction=Direction.OUTPUT, output_value=Value.INACTIVE)

            # Request all lines at once
            self.request = gpiod.request_lines(
                self._chip_path,
                consumer=f"{BB_CONSUMER}_{TM_CONSUMER}",
                config=config
            )
        except Exception as e:
            raise RuntimeError(f"Hardware Init Failed on {self._chip_path}: {e}")

    def __enter__(self): return self
    def __exit__(self, exc_type, exc_value, traceback): self.close()

    def close(self):
        """Cleans up and releases all GPIO resources."""
        if self.request:
            try:
                # Clear BB LEDs
                self.clear_leds()
                self.update_leds()
                # Turn off TM1638 displays
                self.turnOff()
                self.clearDisplay()
            except Exception:
                pass 
            
            self.request.release()
            self.request = None

    # --- UNIFIED LOW LEVEL GPIO HELPERS (Used by both sub-systems) ---
    def _set(self, pin: int, state: bool):
        """Sets a GPIO pin's output state."""
        if not self.request: return
        self.request.set_value(pin, Value.ACTIVE if state else Value.INACTIVE)

    def _get(self, pin: int) -> int:
        """Gets a GPIO pin's input state (0 or 1)."""
        if not self.request: return 0
        return 1 if self.request.get_value(pin) == Value.ACTIVE else 0

    def _reconfigure_dio(self, direction: Direction, pull_up: bool = False):
        """Internal helper to change TM DIO line direction."""
        if not self.request: return
        if direction == Direction.INPUT:
            settings = gpiod.LineSettings(
                direction=Direction.INPUT,
                bias=Bias.PULL_UP if pull_up else Bias.DISABLED
            )
        else: # Output
            settings = gpiod.LineSettings(
                direction=Direction.OUTPUT, output_value=Value.INACTIVE
            )
            
        try:
            self.request.reconfigure_lines(config={self.tm_dio: settings})
        except Exception as e:
            raise RuntimeError(f"Failed to reconfigure TM DIO pin {self.tm_dio}. Error: {e}") from e


    # ==========================================
    # BLINKINBOARD SUB-SYSTEM (74HC595/74HC165)
    # ==========================================
    
    # --- OUTPUT SUB-SYSTEM (LEDs) ---
    
    def set_all_leds(self, val: int): self._led_buffer = val
    
    def clear_leds(self): 
        """Helper to clear the internal LED buffer to zero."""
        self._led_buffer = 0
    
    def update_leds(self):
        """Push the current buffer state to the physical LEDs (74HC595)."""
        if not self.request: return
        
        phys_val = self._led_buffer ^ self.led_inversion_mask

        # 1. Open Latch (Low)
        self._set(self.bb_led_latch, False)
        
        # 2. Shift Data (MSB First: Bit N-1 down to 0)
        for i in range(self.num_led_bits - 1, -1, -1):
            bit = (phys_val >> i) & 1
            self._set(self.bb_led_data, bool(bit))
            self._set(self.bb_led_clk, True)
            self._set(self.bb_led_clk, False)
        
        # 3. Close Latch (High)
        self._set(self.bb_led_latch, True)

    def set_led(self, index: int, state: bool):
        """Set a single LED bit in the buffer (Does not update hardware)."""
        if 0 <= index < self.num_led_bits:
            if state: self._led_buffer |= (1 << index)
            else: self._led_buffer &= ~(1 << index)

    def clear_leds(self): self._led_buffer = 0
    def fill_leds(self): self._led_buffer = (1 << self.num_led_bits) - 1
    def set_all_leds(self, val: int): self._led_buffer = val

    # --- INPUT SUB-SYSTEM (Switches) ---
    
    def read_switches(self) -> int:
        """
        Reads 74HC165 input chain.
        Returns 32-bit integer representing switch states.
        """
        if not self.request: return 0

        # 1. LATCH SEQUENCE (Pulse LOW)
        self._set(self.bb_sw_latch, False)
        time.sleep(self.bb_latch_delay)     
        self._set(self.bb_sw_latch, True)
        time.sleep(self.bb_latch_delay)     

        # 2. SHIFT SEQUENCE
        raw_val = 0
        
        # Read MSB First (Standard for daisy-chain)
        for i in range(self.num_sw_bits - 1, -1, -1):
            # Sample Data
            bit = self._get(self.bb_sw_data)
            
            if bit:
                raw_val |= (1 << i)

            # Pulse Clock
            self._set(self.bb_sw_clk, True)
            time.sleep(self.bb_clock_delay)
            self._set(self.bb_sw_clk, False)
            time.sleep(self.bb_clock_delay)

        # 3. Apply Inversion Mask
        return raw_val ^ self.sw_inversion_mask


    # ==========================================
    # TM1638 SUB-SYSTEM (DSKY Keypad/Display)
    # ==========================================

    def _set_tm_stb(self, value: bool, TMindex: Optional[int]):
        """Set all or one TM1638 Strobe line to Value"""
        val = Value.ACTIVE if value else Value.INACTIVE
        if TMindex is None:
            for pin in self.tm_stb:
                self._set(pin, value)
        else:
            self._set(self.tm_stb[TMindex], value)

    def _setDataMode(self, wr_mode, addr_mode):
        """Set the data modes"""
        self._sendByte(0x40 | wr_mode | addr_mode)

    def _sendByte(self, data):
        """Send a byte to the TM1638 (Stb must be Low) - LSB-first"""
        delay = TM_CLOCK_DELAY

        for _ in range(8):
            self._set(self.tm_clk, False)
            time.sleep(delay)
            self._set(self.tm_dio, bool(data & 1))
            data >>= 1
            self._set(self.tm_clk, True)
            time.sleep(delay)

    def _getByte(self):
        """
        Receive a byte from the TM1638 (DIO must be in input mode)
        Uses MSB-first logic.
        """
        temp = 0
        delay = TM_CLOCK_DELAY

        for _ in range(8):
            temp >>= 1  # MSB-first
            
            self._set(self.tm_clk, False)
            time.sleep(delay)
            
            if self._get(self.tm_dio):
                temp |= 0x80 # MSB-first
                
            self._set(self.tm_clk, True)
            time.sleep(delay)
            
        return temp

    def clearDisplay(self, TMindex: Optional[int] = None):
        """Turn off every LED and segment on the TM1638 board(s)."""
        self._set_tm_stb(False, TMindex)
        self._setDataMode(TM_WRITE_MODE, TM_INCR_ADDR)
        self._sendByte(0xC0) # Set address to 0x00
        for _ in range(16): # 16 bytes for display memory
            self._sendByte(0x00)
        self._set_tm_stb(True, TMindex)

    def turnOff(self, TMindex: Optional[int] = None):
        """Turn off the display (Command 0x80)"""
        self.sendCommand(0x80, TMindex)

    def turnOn(self, brightness: int, TMindex: Optional[int] = None):
        """Turn on the display and set the brightness (Command 0x88 | brightness)"""
        self.sendCommand(0x88 | (brightness & 7), TMindex)

    def sendCommand(self, cmd: int, TMindex: Optional[int]):
        """Send a control command to the TM1638."""
        self._set_tm_stb(False, TMindex)
        self._sendByte(cmd)
        self._set_tm_stb(True, TMindex)

    def sendData(self, addr: int, data: int, TMindex: Optional[int]):
        """Send a data byte to a specific address in the TM1638 display RAM."""
        # 1. Send data command (fixed address mode)
        self._set_tm_stb(False, TMindex)
        self._setDataMode(TM_WRITE_MODE, TM_FIXED_ADDR)
        self._set_tm_stb(True, TMindex)
        
        # 2. Send address and data
        self._set_tm_stb(False, TMindex)
        self._sendByte(0xC0 | addr)
        self._sendByte(data)
        self._set_tm_stb(True, TMindex)

    def getData(self, TMindex: Optional[int]):
        """
        Get the data (buttons) of the TM1638.
        ASSUMES the "Read Key" command (0x42) has *already* been sent
        and STB is already LOW (as is the case in the original TM1638s.py read_keys_raw).
        """
        # 1. Reconfigure DIO to INPUT with PULL_UP
        self._reconfigure_dio(Direction.INPUT, pull_up=True)

        # 2. Wait for chip to prepare data (Twait)
        time.sleep(20e-6)
        
        # 3. Read four bytes (MSB-first)
        b = []
        for _ in range(4):
            b.append(self._getByte())

        # 4. Reconfigure DIO back to OUTPUT
        self._reconfigure_dio(Direction.OUTPUT)
        
        return b
    
    def read_keys_raw(self, TMindex: int = 0, stabilization_delay: float = 0.001) -> list:
        """
        Reads the key matrix data (4 bytes) from a specific TM1638 board.
        This is the method used by the higher-level TMBoards class.
        """
        # 1. Lower STrobe (Select board)
        self._set_tm_stb(False, TMindex)
        
        # 2. Send Read Command (0x42)
        self._sendByte(0x42)
        
        # 3. Wait for stabilization
        time.sleep(stabilization_delay)
        
        # 4. Read the data (getData handles DIO pin switch)
        keys = self.getData(TMindex)
        
        # 5. Raise STrobe (End Transaction)
        self._set_tm_stb(True, TMindex)
        
        return keys