import serial
from renderers.teensy import serial_constants
import utils
import os
import sys
import random as rd
import numpy as np

class LightSender(object):

    def __init__(self,
            serial_port=serial_constants.SERIAL_ADDR,
            nlights=serial_constants.TOTAL_LEDS):

        self.nlights = nlights
        # self.nlights = 400
        # self.nlights = nlights
        # self.nlights = 500

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
        self.configure_hue = 0

    def strobe(self):
        i = 0
        strobe_cycle = 2
        one_shot = True
        while one_shot:
            one_shot = False
            i += 1
            if i % strobe_cycle < strobe_cycle / 2:
                data = chr(100) * (self.nlights * 3)
            else:
                data = chr(0) * (self.nlights * 3)
            self.send_rgb(data.encode())

        return True

    def fetch_rgb(self):
        hex_colors = self.get_hex_arr()
        for i, hex_color in enumerate(hex_colors):
            rgbtuple = utils.hex_to_rgb(hex_color)
            self.data[3 * i:3 * i + 3] = rgbtuple



    def send_rgb(self, data):
        self.serial.write(data)
        x = 'L'.encode()
        self.serial.write(x)
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

    def configure(self):
        print('Set LED Strip length')
        print('type "+[number]" to increse length by that number of LEDs')
        print('type "-[number]" to increse length by that number of LEDs')
        print('type done to return result')

        self.send_rgb(self.data)
        total_leds = 0
        done_input = 'not done'
        while done_input != str('done'):
            a = input()
            if a[0] == '+':
                add_leds = a[1:len(a)]
                print('add ' + add_leds)
                total_leds = total_leds + int(add_leds)
                print("{0} LEDS".format(total_leds))
            elif a[0] == '-':
                add_leds = a[1:len(a)]
                print('subtract ' + add_leds)
                total_leds = total_leds - int(add_leds)
                print("{0} LEDS".format(total_leds))
            elif a == str('done'):
                done_input = a
                continue

            self.nlights = total_leds
            self.data = bytearray([0] * (self.nlights * 3))
            tmp_hue = self.configure_hue + rd.randint(0, 100)/25
            if self.configure_hue > 1:
                self.configure_hue = 0
            else:
                self.configure_hue = tmp_hue
            for i in range(self.nlights):
                rgbtuple = utils.hsv_to_rgb(self.configure_hue, 1, 1)
                self.data[3 * i:3 * i + 3] = rgbtuple

            self.send_rgb(self.data)

            print('type "+[number]" to increse length by that number of LEDs')
            print('type "-[number]" to increse length by that number of LEDs')
            print('type done to return result')




        print("{0} LEDS".format(total_leds))

        print('Set Walls')
        print('Enter Number of walls')
        num_walls = eval(input())

        for big_wall in range(0, num_walls):
            done_input = 'not done'
            segment_leds = self.nlights//num_walls
            wall_inds = [list(range(0, 10))]
            while done_input != str('done'):
                for wall in wall_inds:
                    print(wall)
                first = wall_inds[-1][0]
                last = wall_inds[-1][-1]
                print('Make wall {0} a single color'.format(big_wall))
                print('type "+[number]" to grow color')
                print('type "+[number]" to shrink color')
                print('type "new" to save a section and start a new one')
                print('type done to return result')
                a = input()
                if a[0] == '+':
                    add_leds = a[1:len(a)]
                    print('add ' + add_leds)
                    wall_inds[-1].extend(list(range(last,last + int(add_leds)+1)))
                    print(last)
                elif a[0] == '-':
                    add_leds = a[1:len(a)]
                    print('subtract ' + add_leds)
                    del wall_inds[-1][last - int(add_leds):last+1]
                    print(last)
                elif a == str('done'):
                    done_input = a
                    continue
                elif a == str('new'):
                    print("[{0}:{1}]".format(first,last))
                    bleh = list(range(last+1, last+10))
                    wall_inds.append(bleh)
                elif a == str('flip'):
                     tmp = first
                     first = last
                     last = tmp

                wall_inds[-1] = list(range(first, last+1))
                hue1 = rd.randint(0, 40)/100
                hue2 =  rd.randint(60, 100)/100
                for i in range(self.nlights):
                    in_wall = False
                    for wall in wall_inds:
                        if i in wall:
                            in_wall = True
                            break

                    if in_wall:
                        rgbtuple = utils.hsv_to_rgb(hue1, 1, 1)
                    else:
                        rgbtuple = utils.hsv_to_rgb(hue2, 1, 1)

                    self.data[3 * i:3 * i + 3] = rgbtuple

                self.send_rgb(self.data)
