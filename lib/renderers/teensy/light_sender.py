import serial
from renderers.teensy import serial_constants
import utils
import os

class LightSender(object):

    def __init__(self,
            serial_port=serial_constants.SERIAL_ADDR,
            nlights=serial_constants.TOTAL_LEDS):

        # self.nlights = nlights
        self.nlights = 400

        try:
            self.serial = serial.Serial(
                    serial_port, serial_constants.BAUD, timeout=1)
        except serial.serialutil.SerialException:
            devices = os.listdir('/dev')
            teensy = 0
            for i in devices:
                if 'cu.usbmodem' in i:
                    print(i)
                    teensy = '/dev/' + i

            serial_port = teensy
            self.serial = serial.Serial(
                    serial_port, serial_constants.BAUD, timeout=1)

        self.data = bytearray([0] * (self.nlights * 3))

    def strobe(self):
        i = 0
        strobe_cycle = 2
        while True:
            i += 1
            if i % strobe_cycle < strobe_cycle / 2:
                data = chr(100) * (self.nlights * 3)
            else:
                data = chr(0) * (self.nlights * 3)
            self.send_rgb(data.encode())

    def fetch_rgb(self):
        hex_colors = self.get_hex_arr()
        for i, hex_color in enumerate(hex_colors):
            rgbtuple = utils.hex_to_rgb(hex_color)
            self.data[3 * i:3 * i + 3] = rgbtuple

    def send_rgb(self, data):
        self.serial.write(data)
        self.serial.flush()

    def send_light_dict(self, light_dict):
        for k,v in light_dict.items():
            if v != None:
                x = 'L'.encode()
                self.serial.write(x)
                output = []
                i0 = k & 255 #low order bits
                i1 = (k & 65280) >> 8 #high order bits
                output.append(i0)
                output.append(i1)
                output.append(v[0])
                output.append(v[1])
                output.append(v[2])
                self.serial.write(output)
        self.serial.flush()

    def update(self):
        while True:
            self.fetch_rgb()
            self.send_rgb(self.data)

    def start(self):
        if self.get_hex_arr is None:
            raise Exception('Pls assign me a get_hex_arr func')

        self.update()
        self.app.exec_()

    def close(self):
        self.serial.close()
