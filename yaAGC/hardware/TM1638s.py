#!/usr/bin/env python3
"""
Contains the class TM1638s
It's a low-level class to manipulate a TM1638 board

Modernized for Python 3 and the gpiod v2 API (Raspberry Pi 5)
(Based on extensive debugging)
"""

import gpiod
from gpiod.line import Direction, Value, Bias, Edge
from time import sleep  # <-- Correctly imported
import time # <-- Import time as well, just in case

# some constant to command the TM1638
READ_MODE = 0x02
WRITE_MODE = 0x00
INCR_ADDR = 0x00
FIXED_ADDR = 0x04

# Consumer name for gpiod
CONSUMER = "rpi-TM1638"


class TM1638s:
    """TM1638s class"""

    def __init__(self, dio, clk, stb, brightness=1, gpio_chip_name="gpiochip0"):
        """
        Initialize a TM1638 (or some chained TM1638s)
        :param dio: Data I/O GPIO
        :param clk: clock GPIO
        :param stb: Chip Select GPIO -> a tuple or a single int
        :param brightness: brightness of the display (between 0 and 7)
        :param gpio_chip_name: The name of the GPIO chip (e.g., "gpiochip0")
        """

        # store the GPIOs
        self._dio_pin = dio
        self._clk_pin = clk
        if isinstance(stb, int):
            self._stb_pins = (stb,)
        else:
            self._stb_pins = tuple(stb)
        
        self._chip_path = f"/dev/{gpio_chip_name}"
        self.request = None # Placeholder

        try:
            # Build a configuration dictionary for all pins
            config = {}
            
            # CLK is always output, default low (INACTIVE)
            config[self._clk_pin] = gpiod.LineSettings(
                direction=Direction.OUTPUT, output_value=Value.INACTIVE
            )
            
            # STB lines are always output, default low (INACTIVE)
            for pin in self._stb_pins:
                config[pin] = gpiod.LineSettings(
                    direction=Direction.OUTPUT, output_value=Value.INACTIVE
                )

            # DIO is output by default
            config[self._dio_pin] = gpiod.LineSettings(
                direction=Direction.OUTPUT, output_value=Value.INACTIVE
            )

            # Request all lines at once
            self.request = gpiod.request_lines(
                self._chip_path,
                consumer=CONSUMER,
                config=config
            )

        except Exception as e:
            if self.request:
                self.request.__exit__(None, None, None) # Use __exit__
            raise RuntimeError(f"Failed to request GPIO lines from '{self._chip_path}'. Error: {e}") from e

        # Clk and Stb <- High for every TM
        self._setStb(True, None)
        self.request.set_value(self._clk_pin, Value.ACTIVE) # Set CLK high

        # init the displays
        self.turnOn(brightness)
        self.clearDisplay()

    def _reconfigure_dio(self, direction, pull_up=False):
        """Internal helper to change DIO line direction."""
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
            self.request.reconfigure_lines(config={self._dio_pin: settings})
        except Exception as e:
            raise RuntimeError(f"Failed to reconfigure DIO pin {self._dio_pin}. Error: {e}") from e


    def close(self):
        """
        Cleans up and releases GPIO resources.
        """
        if self.request:
            try:
                # Try to put displays in a safe state
                self.turnOff()
                self.clearDisplay()
            except Exception:
                pass  # Ignore errors during close
            
            # Release all requested lines by manually calling __exit__
            self.request.__exit__(None, None, None)
            self.request = None

    def __del__(self):
        """Ensure resources are freed when object is deleted."""
        self.close()

    def __enter__(self):
        """Context manager enter."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

    def clearDisplay(self, TMindex=None):
        """Turn off every led"""
        self._setStb(False, TMindex)
        self._setDataMode(WRITE_MODE, INCR_ADDR)
        self._sendByte(0xC0)
        for _ in range(16):
            self._sendByte(0x00)
        self._setStb(True, TMindex)


    def turnOff(self, TMindex=None):
        """Turn off (physically) the leds."""
        self.sendCommand(0x80, TMindex)


    def turnOn(self, brightness, TMindex=None):
        """Turn on the display and set the brightness"""
        self.sendCommand(0x88 | (brightness & 7), TMindex)

    # ==========================
    # Communication with the TM
    # ==========================
    def sendCommand(self, cmd, TMindex):
        """Send a command"""
        self._setStb(False, TMindex)
        self._sendByte(cmd)
        self._setStb(True, TMindex)


    def sendData(self, addr, data, TMindex):
        """Send a data at address addr"""
        self._setStb(False, TMindex)
        self._setDataMode(WRITE_MODE, FIXED_ADDR)
        self._setStb(True, TMindex)
        
        self._setStb(False, TMindex)
        self._sendByte(0xC0 | addr)
        self._sendByte(data)
        self._setStb(True, TMindex)

    def getData(self, TMindex):
        """
        Get the data (buttons) of the TM.
        ASSUMES the "Read Key" command (0x42) has *already* been sent
        and STB is already LOW.
        """
        # 1. Reconfigure DIO to INPUT with PULL_UP
        self._reconfigure_dio(Direction.INPUT, pull_up=True)

        # 2. Wait for chip to prepare data (Twait)
        sleep(20e-6) # 20us (FIXED: was time.sleep)
        
        # 3. Read four bytes (MSB-first, as we proved)
        b = []
        for _ in range(4):
            b.append(self._getByte()) # <-- Calls the one, correct _getByte

        # 4. Reconfigure DIO back to OUTPUT
        self._reconfigure_dio(Direction.OUTPUT)
        
        # NOTE: We do NOT control STB here. The calling function must do it.
        return b
    
    def read_keys_raw(self, TMindex=0, stabilization_delay=0.001):
        """
        Performs the full, stabilized key read sequence: 
        Send command, wait for stabilization, read data, then toggle STB.
        """
        # 1. Lower STrobe (Select board)
        self._setStb(False, TMindex)
        
        # 2. Send Read Command (0x42)
        self._sendByte(0x42)
        
        # 3. Wait for stabilization (The necessary hardware fix)
        time.sleep(stabilization_delay)
        
        # 4. Read the data
        # getData handles the DIO pin configuration switch (Input -> Output)
        keys = self.getData(TMindex)
        
        # 5. Raise STrobe (End Transaction)
        self._setStb(True, TMindex)
        
        return keys

    # ==================
    # Internal functions
    # ==================
    def _setStb(self, value, TMindex):
        """Set all or one Stb line to Value"""
        val = Value.ACTIVE if value else Value.INACTIVE
        if TMindex is None:
            for pin in self._stb_pins:
                self.request.set_value(pin, val)
        else:
            self.request.set_value(self._stb_pins[TMindex], val)


    def _setDataMode(self, wr_mode, addr_mode):
        """Set the data modes"""
        self._sendByte(0x40 | wr_mode | addr_mode)

    def _sendByte(self, data):
        """Send a byte (Stb must be Low) - LSB-first"""
        val_low = Value.INACTIVE
        val_high = Value.ACTIVE
        delay = 10e-6 # 10us delay

        for _ in range(8):
            self.request.set_value(self._clk_pin, val_low)
            sleep(delay)
            self.request.set_value(self._dio_pin, val_high if (data & 1) else val_low)
            data >>= 1
            self.request.set_value(self._clk_pin, val_high)
            sleep(delay)

    def _getByte(self):
        """
        Receive a byte (DIO must be in input mode)
        Uses MSB-first logic (proved by testing)
        """
        temp = 0
        val_low = Value.INACTIVE
        val_high = Value.ACTIVE
        delay = 10e-6 # 10us delay

        for _ in range(8):
            temp >>= 1  # MSB-first
            
            self.request.set_value(self._clk_pin, val_low)
            sleep(delay)
            
            if self.request.get_value(self._dio_pin) == val_high:
                temp |= 0x80 # MSB-first
                
            self.request.set_value(self._clk_pin, val_high)
            sleep(delay)
            
        return temp
