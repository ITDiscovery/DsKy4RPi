import gpiod
from gpiod.line import Direction, Value

# Setup for Pi 5 (gpiochip4)
chip = gpiod.Chip("gpiochip4")

# Map our lines
# 21 = CLK, 20 = LATCH, 16 = DATA
lines = chip.get_lines([21, 20, 16])

# Configure as OUTPUT, initially LOW
lines.request(consumer="dvm_test", config={
    21: gpiod.LineSettings(direction=Direction.OUTPUT, output_value=Value.INACTIVE),
    20: gpiod.LineSettings(direction=Direction.OUTPUT, output_value=Value.INACTIVE),
    16: gpiod.LineSettings(direction=Direction.OUTPUT, output_value=Value.INACTIVE)
})

def set_pins(clk, latch, data):
    # Helper to set values easily (0 or 1)
    vals = {
        21: Value.ACTIVE if clk else Value.INACTIVE,
        20: Value.ACTIVE if latch else Value.INACTIVE,
        16: Value.ACTIVE if data else Value.INACTIVE
    }
    lines.set_values(vals)
    print(f"Set -> CLK:{clk} LATCH:{latch} DATA:{data}")