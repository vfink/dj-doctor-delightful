LEDS_PER_STRIP = 167
LEDS_LAST_STRIP = 149
NUM_STRIPS = 8
TOTAL_LEDS = LEDS_PER_STRIP * (NUM_STRIPS - 1) + LEDS_LAST_STRIP
TOTAL_BYTES = TOTAL_LEDS * 3
BAUD = 115200
SERIAL_ADDR = '/dev/ttyACM0'
