import threading
import time
import sys
from typing import Callable, Dict, Optional, Tuple

try:
    from inputs import get_gamepad, UnpluggedError
except ImportError:
    print("CRITICAL: 'inputs' library not found. Install with: pip3 install inputs")
    sys.exit(1)

# ==============================================================================
# --- CONFIGURATION (Based on "RED MODE" Data) ---
# ==============================================================================

# Format: "EVENT_CODE": ("LOGICAL_NAME", MIN_VAL, MAX_VAL, INVERT_BOOL)
DEFAULT_AXIS_MAP = {
    # LEFT STICK
    "ABS_X":        ("RCS_YAW",       0, 255, False), # 0=Left, 255=Right -> -1.0 to 1.0
    "ABS_Y":        ("RCS_PITCH",     0, 255, False), # 0=Up, 255=Down    -> -1.0 (Nose Down) to 1.0 (Nose Up)
    
    # RIGHT STICK
    "ABS_RX":       ("RCS_ROLL",      0, 255, False), # 0=Left, 255=Right -> -1.0 to 1.0
    "ABS_RZ":       ("MAIN_THROTTLE", 0, 255, True)   # 0=Up, 255=Down    -> Inverted so Up=1.0 (Full), Down=-1.0 (Zero)
}

# Format: "EVENT_CODE": "LOGICAL_NAME"
DEFAULT_BUTTON_MAP = {
    "BTN_TRIGGER": "JOY_TRIGGER", # Button 1
    "BTN_THUMB":   "JOY_BTN_2",
    "BTN_THUMB2":  "JOY_BTN_3",
    "BTN_TOP":     "JOY_BTN_4",
    "BTN_TOP2":    "JOY_BTN_5",
    "BTN_PINKIE":  "JOY_BTN_6",
    "BTN_BASE":    "JOY_BTN_7",
    "BTN_BASE2":   "JOY_BTN_8",
    "BTN_BASE3":   "JOY_BTN_9",
    "BTN_BASE4":   "JOY_BTN_10"
}

class JoystickController:
    def __init__(self, 
                 callback_func: Callable[[str, float], None], 
                 axis_map: Dict = DEFAULT_AXIS_MAP, 
                 btn_map: Dict = DEFAULT_BUTTON_MAP,
                 deadzone: float = 0.05, 
                 sensitivity: float = 0.01):
        
        self.callback = callback_func
        self.axis_map = axis_map
        self.btn_map = btn_map
        self.deadzone = deadzone
        self.sensitivity = sensitivity
        
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._last_values: Dict[str, float] = {}

    def _normalize(self, raw_val: int, min_v: int, max_v: int, invert: bool) -> float:
        # Clamp value to known range
        raw_val = max(min(raw_val, max_v), min_v)
        
        # Map to -1.0 ... 1.0
        norm = 2 * ((raw_val - min_v) / (max_v - min_v)) - 1.0
        
        if invert:
            norm = -norm
        return norm

    def _monitor_loop(self):
        print("[JOY] Joystick Thread Started (RED MODE CONFIG).")
        while self._running:
            try:
                events = get_gamepad()
                for event in events:
                    
                    # --- AXIS HANDLER ---
                    if event.ev_type == 'Absolute' and event.code in self.axis_map:
                        log_name, min_v, max_v, invert = self.axis_map[event.code]
                        val = self._normalize(event.state, min_v, max_v, invert)
                        
                        if abs(val) < self.deadzone: val = 0.0
                        
                        last_val = self._last_values.get(log_name, -999.0)
                        if abs(val - last_val) > self.sensitivity:
                            self._last_values[log_name] = val
                            self.callback(log_name, val)

                    # --- BUTTON HANDLER ---
                    elif event.ev_type == 'Key' and event.code in self.btn_map:
                        log_name = self.btn_map[event.code]
                        # event.state: 1 = Pressed, 0 = Released
                        self.callback(log_name, float(event.state))

            except UnpluggedError:
                print("[JOY] Unplugged. Retrying...")
                time.sleep(5)
            except Exception as e:
                print(f"[JOY] Error: {e}")
                time.sleep(1)

    def start(self):
        if self._running: return
        self._running = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False

# --- DIAGNOSTIC MODE ---
if __name__ == "__main__":
    print("--- JOYSTICK RED MODE TEST ---")
    print("Ensure joystick LED is RED.")
    
    def test_cb(axis, val):
        if "BTN" in axis:
             print(f"BUTTON: {axis} = {int(val)}")
        else:
             # Visualization
             bar = [" "] * 21
             idx = int((val + 1) * 10) # 0 to 20
             idx = max(0, min(20, idx))
             bar[idx] = "|"
             print(f"AXIS: {axis:<15} {val:>6.3f} [{''.join(bar)}]")

    joy = JoystickController(callback_func=test_cb)
    try:
        joy.start()
        while True: time.sleep(1)
    except KeyboardInterrupt:
        joy.stop()