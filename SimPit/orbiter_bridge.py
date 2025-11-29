import socket
import time
import threading
import sys
from typing import Dict, Tuple, List, Optional

# --- HARDWARE IMPORTS ---
try:
    from UnifiedSimPitDriver import UnifiedSimPitDriver
except ImportError:
    try:
        from hardware.UnifiedSimPitDriver import UnifiedSimPitDriver
    except ImportError:
        print("CRITICAL ERROR: Could not find 'UnifiedSimPitDriver.py'.")
        sys.exit(1)

# Import the new Joystick Driver
try:
    from hardware.joystick import JoystickController
except ImportError:
    print("CRITICAL: Could not find 'hardware/joystick.py'")
    sys.exit(1)

# ==============================================================================
# --- CONFIGURATION ---
# ==============================================================================

ORBITER_HOST = '127.0.0.1' # Localhost if running Mock Server on same Pi
ORBITER_PORT = 37777
GPIO_CHIP_NAME = "gpiochip4"

# --- DEBUG FLAGS ---
DEBUG_JOYSTICK = False  # <--- Set to True to see joystick prints in console

# Pins
BB_CLK = 21; BB_LATCH = 20; BB_DATA_OUT = 16
BB_DATA_IN = 27; BB_CLK_IN = 17; BB_LATCH_IN = 22
TM_CLK = 13; TM_DIO = 19; TM_STB = (26, 6, 5) 

# --- DSKY CONFIG ---
DSKY_INDICATOR_BOARD = 0 

TM1638_FONT: Dict[str, int] = {
    ' ': 0b00000000, '0': 0b00111111, '1': 0b00000110, '2': 0b01011011, 
    '3': 0b01001111, '4': 0b01100110, '5': 0b01101101, '6': 0b01111101, 
    '7': 0b00000111, '8': 0b01111111, '9': 0b01101111, '+': 0b01000110,
    '-': 0b01000000, '_': 0b00001000,
}

TM_KEY_DECODE: Dict[Tuple[int, ...], str] = {
    (4, 0, 0, 0): "DskySwitchEnter",   (64, 0, 0, 0): "DskySwitchReset",
    (0, 4, 0, 0): "DskySwitchClear",   (0, 64, 0, 0): "DskySwitchProg",
    (0, 0, 4, 0): "DskySwitchKeyRel",  (0, 0, 64, 0): "DskySwitchNine",
    (0, 0, 0, 4): "DskySwitchSix",     (0, 0, 0, 64): "DskySwitchThree",
    (2, 0, 0, 0): "DskySwitchEight",   (32, 0, 0, 0): "DskySwitchFive",
    (0, 2, 0, 0): "DskySwitchTwo",     (0, 32, 0, 0): "DskySwitchSeven",
    (0, 0, 2, 0): "DskySwitchFour",    (0, 0, 32, 0): "DskySwitchOne",
    (0, 0, 0, 2): "DskySwitchPlus",    (0, 0, 0, 32): "DskySwitchMinus",
    (1, 0, 0, 0): "DskySwitchZero",    (16, 0, 0, 0): "DskySwitchNoun",
    (0, 1, 0, 0): "DskySwitchVerb"
}

DSKY_LED_PAIRS = {
    1:  ("GET:NASSP:DSKY:TempLit",       "GET:NASSP:DSKY:UplinkActyLit"),
    3:  ("GET:NASSP:DSKY:GimbalLockLit", "GET:NASSP:DSKY:NoAttLit"),
    5:  ("GET:NASSP:DSKY:ProgLit",       "GET:NASSP:DSKY:StbyLit"),
    7:  ("GET:NASSP:DSKY:RestartLit",    "GET:NASSP:DSKY:KeyRelLit"),
    9:  ("GET:NASSP:DSKY:TrackerLit",    "GET:NASSP:DSKY:OprErrLit"),
    11: ("GET:NASSP:DSKY:AltLit",        "GET:NASSP:DSKY:PrioDspLit"),
    13: ("GET:NASSP:DSKY:VelLit",        "GET:NASSP:DSKY:NoDapLit"),
    15: ("GET:NASSP:DSKY:CompActyLit",   None) 
}

BLINKIN_INDICATOR_MAP: Dict[str, int] = {
    "GET:MasterAlarmSwitch:State": 37, "GET:NASSP:GNSystemLit": 36, "GET:NASSP:CESACLit": 39,
    "GET:NASSP:CESDCLit": 38, "GET:NASSP:EngineStopLit": 31, "GET:NASSP:RCS_TCALit": 30,
    "GET:NASSP:RCS_ASCLit": 29, "GET:NASSP:EngineStartLit": 24, "GET:NASSP:SPS_ReadyLit": 23,
    "GET:NASSP:UllageLit": 22, "GET:NASSP:AbortLit": 0, "GET:NASSP:AbortStageLit": 1,
    "GET:NASSP:WatchdogLit": 27, "GET:NASSP:HeaterLit": 17, "GET:NASSP:GlycolLit": 16
}

THREE_POS_SWITCHES = {
    "Sw1_Engine": ((1 << 2), (1 << 3), "EngineArmSwitch"), 
    "Sw2_SCCont": ((1 << 0), (1 << 1), "SCContSwitch"), 
    "Sw3_OptZero": ((1 << 4), (1 << 5), "OptZeroSwitch"),
    "Sw4_ImuPwr":  ((1 << 6), (1 << 7), "ImuPwrSwitch"),
}
THREE_POS_STATE_LOGIC = { (0, 0): 1, (1, 0): 0, (0, 1): 2, (1, 1): 1 }

MOMENTARY_SWITCHES: Dict[int, str] = {
    8: "AbortButton", 9: "AbortStageButton"
}

DSKY_DIGIT_MAP = {
    "R1": (2, 0, 6), "PROG": (2, 6, 2), "R2": (1, 0, 6), 
    "VERB": (1, 6, 2), "R3": (0, 0, 6), "NOUN": (0, 6, 2)
}

# ==============================================================================
# --- ORBITER BRIDGE ---
# ==============================================================================

class OrbiterBridge:
    def __init__(self, driver: UnifiedSimPitDriver):
        self.driver = driver
        self.running = False
        self.net_lock = threading.Lock(); self.hw_lock = threading.Lock()  
        self.orbiter_socket: Optional[socket.socket] = None
        
        self.last_tm_key_tuple = (0, 0, 0, 0)
        self.last_toggle_states = {}
        self.last_blinkin_bits = 0 

        # --- JOYSTICK INIT ---
        # Initialize the joystick controller with our callback
        self.joy = JoystickController(callback_func=self.handle_joystick_input)
        
        with self.hw_lock: self.driver.clearDisplay()

    def connect_network(self) -> bool:
        print(f"Connecting to {ORBITER_HOST}:{ORBITER_PORT}...")
        try:
            self.orbiter_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.orbiter_socket.connect((ORBITER_HOST, ORBITER_PORT))
            self.orbiter_socket.settimeout(0.1)
            print("Connected.")
            return True
        except socket.error:
            self.orbiter_socket = None
            return False

    def send_command(self, cmd: str) -> Optional[str]:
        with self.net_lock:
            if not self.orbiter_socket: return None
            try:
                self.orbiter_socket.sendall((cmd + '\n').encode('ascii'))
                # We do NOT wait for a response for SET commands to speed up Joystick traffic
                if cmd.startswith("SET:"): 
                    return "OK"
                
                # Only wait for response on GET commands
                response = b''
                while True:
                    chunk = self.orbiter_socket.recv(1024)
                    if not chunk: break
                    response += chunk
                    if b'\n' in chunk: break
                return response.decode('ascii').strip('\n\r')
            except (socket.timeout, socket.error): 
                return None

    # --- JOYSTICK CALLBACK ---
    def handle_joystick_input(self, axis_name: str, value: float):
        """
        Called by the Joystick Thread whenever an axis or button changes.
        """
        cmd = ""
        
        # 1. Handle Throttle Logic (-1.0 to 1.0  ->  0.0 to 1.0)
        if axis_name == "MAIN_THROTTLE":
            throttle_val = (value + 1.0) / 2.0
            cmd = f"SET:MAIN_THROTTLE={throttle_val:.3f}"
            
        # 2. Handle Buttons (SET:JOY_BTN_1=1)
        elif "JOY_" in axis_name:
            cmd = f"SET:{axis_name}={int(value)}"
            
        # 3. Handle RCS (Standard -1.0 to 1.0)
        else:
            cmd = f"SET:{axis_name}={value:.3f}"

        # DEBUG OUTPUT
        if DEBUG_JOYSTICK:
            print(f"[JOY] Sending: {cmd}")

        self.send_command(cmd)

    def update_dsky_digits(self, field_name: str, value_str: str):
        if field_name not in DSKY_DIGIT_MAP or value_str is None: return
        board_idx, start_digit, max_len = DSKY_DIGIT_MAP[field_name]
        cleaned_val = value_str.replace('=', '').replace('R1', '').replace('R2', '').replace('R3', '')
        for i in range(max_len):
            char = cleaned_val[i] if i < len(cleaned_val) else ' '
            addr = (start_digit + i) * 2
            if addr <= 14: self.driver.sendData(addr, TM1638_FONT.get(char, 0), TMindex=board_idx)

    def input_loop(self):
        while self.running:
            if not self.orbiter_socket:
                time.sleep(1); continue
            try:
                with self.hw_lock:
                    current_blinkin = self.driver.read_switches()
                    raw_keys = tuple(self.driver.read_keys_raw(TMindex=0)) 

                # TM1638 Keys
                if raw_keys != self.last_tm_key_tuple:
                    if raw_keys in TM_KEY_DECODE: self.send_command(f"SET:{TM_KEY_DECODE[raw_keys]}=1")
                    elif self.last_tm_key_tuple in TM_KEY_DECODE: self.send_command(f"SET:{TM_KEY_DECODE[self.last_tm_key_tuple]}=0")
                    self.last_tm_key_tuple = raw_keys

                # Blinkin Switches
                for uid, (m_up, m_down, name) in THREE_POS_SWITCHES.items():
                    b_up = 1 if (current_blinkin & m_up) else 0
                    b_down = 1 if (current_blinkin & m_down) else 0
                    curr = THREE_POS_STATE_LOGIC.get((b_down, b_up), 1)
                    if curr != self.last_toggle_states.get(uid, -1):
                        self.send_command(f"SET:{name}={curr}")
                        self.last_toggle_states[uid] = curr

                # Blinkin Buttons
                changed_bits = current_blinkin ^ self.last_blinkin_bits
                for bit_idx, name in MOMENTARY_SWITCHES.items():
                    mask = (1 << bit_idx)
                    if changed_bits & mask:
                        is_pressed = (current_blinkin & mask) != 0
                        val = "1" if is_pressed else "0"
                        self.send_command(f"SET:{name}={val}")

                self.last_blinkin_bits = current_blinkin
                time.sleep(0.02)
            except Exception: pass

    def output_loop(self):
        while self.running:
            if not self.orbiter_socket:
                time.sleep(1); continue
            try:
                # Batch DSKY Data
                dsky_data = {
                    "PROG": self.send_command("GET:NASSP:DSKY:Prog"),
                    "VERB": self.send_command("GET:NASSP:DSKY:Verb"),
                    "NOUN": self.send_command("GET:NASSP:DSKY:Noun"),
                    "R1":   self.send_command("GET:NASSP:DSKY:R1"),
                    "R2":   self.send_command("GET:NASSP:DSKY:R2"),
                    "R3":   self.send_command("GET:NASSP:DSKY:R3")
                }
                
                # Batch LEDs
                blinkin_states = {}
                for key, bit_idx in BLINKIN_INDICATOR_MAP.items():
                    blinkin_states[key] = (bit_idx, self.send_command(key) == "1")

                dsky_led_values = {}
                for addr, (key_a, key_b) in DSKY_LED_PAIRS.items():
                    val = 0
                    if key_a and self.send_command(key_a) == "1": val += 1 
                    if key_b and self.send_command(key_b) == "1": val += 2 
                    dsky_led_values[addr] = val

                with self.hw_lock:
                    for field, val in dsky_data.items():
                        if val is not None: self.update_dsky_digits(field, val)
                    
                    for addr, val in dsky_led_values.items():
                        self.driver.sendData(addr, val, TMindex=DSKY_INDICATOR_BOARD)

                    for key, (bit_idx, is_lit) in blinkin_states.items():
                        self.driver.set_led(bit_idx, is_lit)
                    self.driver.update_leds()
                time.sleep(0.1)
            except Exception as e: pass

if __name__ == "__main__":
    try:
        with UnifiedSimPitDriver(chip_name=GPIO_CHIP_NAME, bb_led_clk=BB_CLK, bb_led_latch=BB_LATCH, bb_led_data=BB_DATA_OUT, bb_sw_clk=BB_CLK_IN, bb_sw_latch=BB_LATCH_IN, bb_sw_data=BB_DATA_IN, tm_clk=TM_CLK, tm_dio=TM_DIO, tm_stb=TM_STB, num_led_chips=5, num_switch_chips=4) as hw:
            print("Bridge Initialized.")
            bridge = OrbiterBridge(hw)
            bridge.running = True
            
            # 1. Start Input Thread (Switches)
            t_in = threading.Thread(target=bridge.input_loop, daemon=True)
            t_in.start()
            
            # 2. Start Output Thread (Displays)
            t_out = threading.Thread(target=bridge.output_loop, daemon=True)
            t_out.start()
            
            # 3. Start Joystick Thread
            print("Starting Joystick...")
            bridge.joy.start()

            while True:
                if not bridge.orbiter_socket: 
                    bridge.connect_network()
                time.sleep(1)
                
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as e:
        print(f"Fatal: {e}")
        sys.exit(1)