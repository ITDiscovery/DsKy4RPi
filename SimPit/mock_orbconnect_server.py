import socket
import threading
import time
import curses
import sys

HOST = '0.0.0.0'
PORT = 37777

STATE = {
    "status": "Stopped", "client": "None", "inputs": {}, "sim_outputs": {}, "logs": [],
    "last_msg": "Waiting...", "msg_count": 0,
    
    # --- DSKY ---
    "reg_noun": "37", "reg_verb": "16", "reg_prog": "99",
    "reg_r1": "-88888", "reg_r2": "-88888", "reg_r3": "-88888",
    "show_noun": True, "show_verb": True, "show_prog": True,
    "show_r1": True, "show_r2": True, "show_r3": True,
    
    "lights": {
        "TempLit": False, "UplinkActyLit": False, "GimbalLockLit": False, "NoAttLit": False,
        "ProgLit": False, "StbyLit": False, "RestartLit": False, "KeyRelLit": False,
        "TrackerLit": False, "OprErrLit": False, "AltLit": False, "PrioDspLit": False,
        "VelLit": False, "NoDapLit": False, "CompActyLit": False
    },
    
    # --- BLINKINBOARD ---
    "blinkin": {
        "MasterAlarmSwitch:State": False, "GNSystemLit": False, "CESACLit": False,
        "CESDCLit": False, "EngineStopLit": False, "RCS_TCALit": False, "RCS_ASCLit": False,
        "EngineStartLit": False, "SPS_ReadyLit": False, "UllageLit": False,
        "AbortLit": False, "AbortStageLit": False,
        "WatchdogLit": False, "HeaterLit": False, "GlycolLit": False
    },

    # --- JOYSTICK STATE (Restored) ---
    "joy": {
        "RCS_YAW": 0.0, "RCS_PITCH": 0.0, "RCS_ROLL": 0.0, "MAIN_THROTTLE": 0.0,
        "JOY_TRIGGER": 0, "JOY_BTN_2": 0, "JOY_BTN_3": 0, "JOY_BTN_4": 0, "JOY_BTN_5": 0,
        "JOY_BTN_6": 0, "JOY_BTN_7": 0, "JOY_BTN_8": 0, "JOY_BTN_9": 0, "JOY_BTN_10": 0
    }
}

def log_message(msg):
    STATE["logs"].append(f"[{time.strftime('%H:%M:%S')}] {msg}")
    if len(STATE["logs"]) > 6: STATE["logs"].pop(0)

def handle_client(conn, addr):
    STATE["status"] = "Connected"; STATE["client"] = f"{addr[0]}:{addr[1]}"
    conn.settimeout(0.05)
    try:
        conn.sendall(b"OK:ORBITER_2024_NASSP\n")
        buffer = ""
        while True:
            try:
                chunk = conn.recv(4096)
                if not chunk: break
                buffer += chunk.decode('ascii', errors='ignore')
                
                while '\n' in buffer:
                    msg, buffer = buffer.split('\n', 1)
                    msg = msg.strip()
                    if not msg: continue
                    
                    STATE["msg_count"] += 1
                    STATE["last_msg"] = msg[:60]
                    
                    if msg.startswith("SET:"):
                        try:
                            k, v = msg[4:].split('=', 1)
                            # Route to Joystick or Generic Inputs
                            if k in STATE["joy"]:
                                STATE["joy"][k] = float(v)
                            else:
                                STATE["inputs"][k] = v
                        except: pass
                    
                    elif msg.startswith("GET:"):
                        response = "0"
                        clean = msg.replace("GET:NASSP:", "").replace("GET:", "")
                        
                        if clean in STATE["blinkin"]: 
                            response = "1" if STATE["blinkin"][clean] else "0"
                        elif "Lit" in msg and "DSKY:" in msg:
                            dk = clean.replace("DSKY:", "")
                            if dk in STATE["lights"]: response = "1" if STATE["lights"][dk] else "0"
                        elif "Noun" in msg: response = STATE["reg_noun"] if STATE["show_noun"] else "  "
                        elif "Verb" in msg: response = STATE["reg_verb"] if STATE["show_verb"] else "  "
                        elif "Prog" in msg: response = STATE["reg_prog"] if STATE["show_prog"] else "  "
                        elif "R1" in msg: response = STATE["reg_r1"] if STATE["show_r1"] else "      "
                        elif "R2" in msg: response = STATE["reg_r2"] if STATE["show_r2"] else "      "
                        elif "R3" in msg: response = STATE["reg_r3"] if STATE["show_r3"] else "      "
                        
                        STATE["sim_outputs"][msg] = response
                        conn.sendall((response + "\n").encode('ascii'))
            except socket.timeout: continue
            except ConnectionResetError: break
    except Exception as e: log_message(f"Err: {e}")
    finally: STATE["status"] = "Listening..."; conn.close()

def server_thread():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        s.bind((HOST, PORT)); s.listen(5)
        while True:
            conn, addr = s.accept()
            handle_client(conn, addr)
    except: pass

def draw_dashboard(stdscr):
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_RED, -1)
    curses.init_pair(2, curses.COLOR_GREEN, -1)
    curses.init_pair(3, curses.COLOR_CYAN, -1) 
    curses.init_pair(4, curses.COLOR_YELLOW, -1)
    curses.init_pair(5, curses.COLOR_WHITE, -1)
    
    stdscr.nodelay(True); curses.curs_set(0)
    
    t = threading.Thread(target=server_thread, daemon=True); t.start()
    
    while True:
        try:
            key = stdscr.getch()
            # --- INPUTS ---
            if key == ord('n'): STATE["show_noun"] = not STATE["show_noun"]
            elif key == ord('v'): STATE["show_verb"] = not STATE["show_verb"]
            elif key == ord('p'): STATE["show_prog"] = not STATE["show_prog"]
            elif key == ord('1'): STATE["show_r1"] = not STATE["show_r1"]
            elif key == ord('2'): STATE["show_r2"] = not STATE["show_r2"]
            elif key == ord('3'): STATE["show_r3"] = not STATE["show_r3"]
            
            elif key == ord('4'): STATE["lights"]["TempLit"] = not STATE["lights"]["TempLit"]
            elif key == ord('5'): STATE["lights"]["GimbalLockLit"] = not STATE["lights"]["GimbalLockLit"]
            elif key == ord('6'): STATE["lights"]["ProgLit"] = not STATE["lights"]["ProgLit"]
            elif key == ord('7'): STATE["lights"]["RestartLit"] = not STATE["lights"]["RestartLit"]
            elif key == ord('8'): STATE["lights"]["TrackerLit"] = not STATE["lights"]["TrackerLit"]
            elif key == ord('9'): STATE["lights"]["AltLit"] = not STATE["lights"]["AltLit"]
            elif key == ord('0'): STATE["lights"]["VelLit"] = not STATE["lights"]["VelLit"]
            elif key == ord('-'): STATE["lights"]["CompActyLit"] = not STATE["lights"]["CompActyLit"]
            elif key == ord('y'): STATE["lights"]["UplinkActyLit"] = not STATE["lights"]["UplinkActyLit"]
            elif key == ord('u'): STATE["lights"]["NoAttLit"] = not STATE["lights"]["NoAttLit"]
            elif key == ord('i'): STATE["lights"]["StbyLit"] = not STATE["lights"]["StbyLit"]
            elif key == ord('o'): STATE["lights"]["KeyRelLit"] = not STATE["lights"]["KeyRelLit"]
            elif key == ord('h'): STATE["lights"]["OprErrLit"] = not STATE["lights"]["OprErrLit"]
            elif key == ord('j'): STATE["lights"]["PrioDspLit"] = not STATE["lights"]["PrioDspLit"]
            elif key == ord('k'): STATE["lights"]["NoDapLit"] = not STATE["lights"]["NoDapLit"]

            elif key == ord('m'): STATE["blinkin"]["MasterAlarmSwitch:State"] = not STATE["blinkin"]["MasterAlarmSwitch:State"]
            elif key == ord('q'): STATE["blinkin"]["GNSystemLit"] = not STATE["blinkin"]["GNSystemLit"]
            elif key == ord('w'): STATE["blinkin"]["CESACLit"] = not STATE["blinkin"]["CESACLit"]
            elif key == ord('e'): STATE["blinkin"]["CESDCLit"] = not STATE["blinkin"]["CESDCLit"]
            elif key == ord('r'): STATE["blinkin"]["EngineStopLit"] = not STATE["blinkin"]["EngineStopLit"]
            elif key == ord('a'): STATE["blinkin"]["EngineStartLit"] = not STATE["blinkin"]["EngineStartLit"]
            elif key == ord('s'): STATE["blinkin"]["SPS_ReadyLit"] = not STATE["blinkin"]["SPS_ReadyLit"]
            elif key == ord('d'): STATE["blinkin"]["UllageLit"] = not STATE["blinkin"]["UllageLit"]
            elif key == ord('z'): STATE["blinkin"]["AbortLit"] = not STATE["blinkin"]["AbortLit"]
            elif key == ord('x'): STATE["blinkin"]["AbortStageLit"] = not STATE["blinkin"]["AbortStageLit"]
            elif key == ord('c'): STATE["blinkin"]["WatchdogLit"] = not STATE["blinkin"]["WatchdogLit"]
            elif key == ord('b'): STATE["blinkin"]["GlycolLit"] = not STATE["blinkin"]["GlycolLit"]
            
            elif key == ord('`'): sys.exit(0)
        except: pass

        stdscr.erase()
        h, w = stdscr.getmaxyx()
        
        def draw_chk(y, x, label, is_on, color):
            if x + len(label) + 2 > w: return
            mark = "[*]" if is_on else "[ ]"
            attr = curses.color_pair(color) | curses.A_BOLD if is_on else curses.color_pair(5) | curses.A_DIM
            try: stdscr.addstr(y, x, f"{mark} {label}", attr)
            except: pass

        # --- HEADER ---
        status_color = curses.color_pair(2) if "Connected" in STATE["status"] else curses.color_pair(1)
        stdscr.addstr(0, 0, f"SRV: {STATE['status']}", status_color | curses.A_BOLD)
        stdscr.addstr(0, 25, f"CLIENT: {STATE['client']}", curses.color_pair(3))

        # --- DSKY SECTION ---
        try:
            stdscr.addstr(2, 0, "--- DSKY DISPLAY (Top) ---", curses.color_pair(3) | curses.A_BOLD)
            fmt = lambda x: curses.color_pair(4) | curses.A_BOLD if x else curses.color_pair(5) | curses.A_DIM
            stdscr.addstr(3, 2, "PROG      VERB      NOUN", curses.color_pair(5))
            stdscr.addstr(4, 3, STATE["reg_prog"] if STATE["show_prog"] else "--", fmt(STATE["show_prog"]))
            stdscr.addstr(4, 13, STATE["reg_verb"] if STATE["show_verb"] else "--", fmt(STATE["show_verb"]))
            stdscr.addstr(4, 23, STATE["reg_noun"] if STATE["show_noun"] else "--", fmt(STATE["show_noun"]))
            stdscr.addstr(5, 10, STATE["reg_r1"] if STATE["show_r1"] else "      ", fmt(STATE["show_r1"]))
            stdscr.addstr(6, 10, STATE["reg_r2"] if STATE["show_r2"] else "      ", fmt(STATE["show_r2"]))
            stdscr.addstr(7, 10, STATE["reg_r3"] if STATE["show_r3"] else "      ", fmt(STATE["show_r3"]))

            L = STATE["lights"]
            draw_chk(2, 40, "TEMP(4)", L["TempLit"], 4);    draw_chk(2, 55, "UPLINK(y)", L["UplinkActyLit"], 5)
            draw_chk(3, 40, "GIMBAL(5)", L["GimbalLockLit"], 4); draw_chk(3, 55, "NO ATT(u)", L["NoAttLit"], 5)
            draw_chk(4, 40, "PROG(6)", L["ProgLit"], 4);    draw_chk(4, 55, "STBY(i)", L["StbyLit"], 5)
            draw_chk(5, 40, "RESTART(7)", L["RestartLit"], 4); draw_chk(5, 55, "KEY REL(o)", L["KeyRelLit"], 5)
            draw_chk(6, 40, "TRACK(8)", L["TrackerLit"], 4); draw_chk(6, 55, "OPR ERR(h)", L["OprErrLit"], 5)
            draw_chk(7, 40, "ALT(9)", L["AltLit"], 4);      draw_chk(7, 55, "PRIO DSP(j)", L["PrioDspLit"], 5)
            draw_chk(8, 40, "VEL(0)", L["VelLit"], 4);      draw_chk(8, 55, "NO DAP(k)", L["NoDapLit"], 5)
            draw_chk(9, 40, "COMP ACT(-)", L["CompActyLit"], 4)
        except: pass

        # --- BLINKIN SECTION ---
        y_off = 11
        try:
            stdscr.addstr(y_off, 0, "--- BLINKINBOARD (Bottom) ---", curses.color_pair(3) | curses.A_BOLD)
            BL = STATE["blinkin"]
            draw_chk(y_off+1, 0, "MASTER ALARM (m)", BL["MasterAlarmSwitch:State"], 1)
            draw_chk(y_off+2, 0, "GN SYS (q)", BL["GNSystemLit"], 1); draw_chk(y_off+2, 20, "CES AC (w)", BL["CESACLit"], 1)
            draw_chk(y_off+2, 40, "CES DC (e)", BL["CESDCLit"], 1); draw_chk(y_off+2, 60, "ENG STOP (r)", BL["EngineStopLit"], 1)
            draw_chk(y_off+3, 0, "ENG START (a)", BL["EngineStartLit"], 2); draw_chk(y_off+3, 20, "SPS RDY (s)", BL["SPS_ReadyLit"], 2)
            draw_chk(y_off+3, 40, "ULLAGE (d)", BL["UllageLit"], 2); draw_chk(y_off+3, 60, "WATCHDOG (c)", BL["WatchdogLit"], 3)
            draw_chk(y_off+4, 0, "ABORT (z)", BL["AbortLit"], 1); draw_chk(y_off+4, 20, "ABT STG (x)", BL["AbortStageLit"], 1)
            draw_chk(y_off+4, 40, "GLYCOL (b)", BL["GlycolLit"], 4)
        except: pass

        # --- 3-POS SWITCHES (Input) ---
        sy = y_off + 6
        try:
            stdscr.addstr(sy, 0, "--- 3-POS SWITCHES (Input) ---", curses.color_pair(3) | curses.A_BOLD)
            
            switches = [
                ("EngineArmSwitch", "ENG ARM"), ("SCContSwitch",    "SC CONT"),
                ("OptZeroSwitch",   "OPT ZERO"), ("ImuPwrSwitch",    "IMU PWR")
            ]
            
            for i, (key, label) in enumerate(switches):
                val = STATE["inputs"].get(key, "?")
                state_text = "[???]"
                attr = curses.color_pair(5)
                
                if val == '0': 
                    state_text = "[DWN]"
                    attr = curses.color_pair(1) # Red/Yellowish
                elif val == '1': 
                    state_text = "[CTR]"
                    attr = curses.color_pair(5) # White
                elif val == '2': 
                    state_text = "[UP ]"
                    attr = curses.color_pair(2) | curses.A_BOLD # Green
                
                stdscr.addstr(sy + 1 + i, 0, f"{label:<15} {state_text}", attr)
        except: pass

        # --- MOMENTARY BUTTONS ---
        try:
            stdscr.addstr(sy, 40, "--- BUTTONS ---", curses.color_pair(3) | curses.A_BOLD)
            btns = [("AbortButton", "ABORT"), ("AbortStageButton", "ABORT STG")]
            for i, (key, label) in enumerate(btns):
                val = STATE["inputs"].get(key, "0")
                state_text = "[PUSHED]" if val == '1' else "[......]"
                attr = curses.color_pair(1) | curses.A_BOLD if val == '1' else curses.color_pair(5) | curses.A_DIM
                stdscr.addstr(sy + 1 + i, 40, f"{label:<12} {state_text}", attr)
        except: pass

        # --- JOYSTICK SECTION (Restored) ---
        col_joy = 75
        if w > (col_joy + 20):
            try:
                stdscr.vline(2, col_joy-2, '|', h-4)
                y = 2
                stdscr.addstr(y, col_joy, "--- JOYSTICK ---", curses.color_pair(4))
                J = STATE["joy"]
                
                def draw_mini_bar(by, bx, label, val):
                    width = 12
                    norm = int((val + 1.0) / 2.0 * width)
                    norm = max(0, min(width, norm))
                    bar = ["."] * (width + 1)
                    bar[norm] = "|"
                    color = curses.color_pair(5)
                    if abs(val) > 0.05: color = curses.color_pair(3) | curses.A_BOLD
                    stdscr.addstr(by, bx, f"{label:<4} {''.join(bar)} {val:+.2f}", color)

                y+=1; draw_mini_bar(y, col_joy, "YAW", J["RCS_YAW"])
                y+=1; draw_mini_bar(y, col_joy, "PIT", J["RCS_PITCH"])
                y+=1; draw_mini_bar(y, col_joy, "ROL", J["RCS_ROLL"])
                
                y+=1
                t_val = J["MAIN_THROTTLE"]
                t_w = 12
                t_n = int(t_val * t_w)
                t_bar = ["|"] * t_n + ["."] * (t_w - t_n)
                stdscr.addstr(y, col_joy, f"THR  {''.join(t_bar)} {t_val:.2f}")

                y+=2
                stdscr.addstr(y, col_joy, "BTN: ", curses.color_pair(5))
                btns = [J[k] for k in J if "BTN" in k or "TRIG" in k]
                # Show first 8 bits
                btn_str = "".join(["1" if b else "." for b in btns[:8]])
                stdscr.addstr(y, col_joy+5, btn_str, curses.color_pair(2) | curses.A_BOLD)
            except: pass
        else:
             # Warning if window too narrow for Joy
             try: stdscr.addstr(h-2, col_joy-20, "Widen -> Joy", curses.color_pair(1))
             except: pass

        # --- FOOTER ---
        try:
            stdscr.hline(h-2, 0, '-', w)
            ctr = STATE["msg_count"]
            safe_msg = STATE["last_msg"][:w-25]
            stdscr.addstr(h-1, 0, f"RX[{ctr}]: {safe_msg}", curses.color_pair(4))
        except: pass

        stdscr.refresh(); time.sleep(0.05)

if __name__ == "__main__":
    try: curses.wrapper(draw_dashboard)
    except: pass