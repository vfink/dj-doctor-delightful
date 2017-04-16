import numpy as np
import scipy.signal as signal
from renderers.teensy import serial_constants
import utils
from vis_algs import vis_alg_base

import random as rd
import time
import peakutils

class EffectAlgorithm(vis_alg_base.VisualizationAlgorithm):

    def __init__(self, bpm, nlights, initial_hex_vals):
        self.bpm = bpm
        self.period = 1/(bpm/60)
        self.nlights = nlights
        self.final_hex_vals = initial_hex_vals

        self.times = []
        self.log_time()
        self.done = 0

    def freq_to_hex(self):
        pass

    def update(self):
        for i in range(self.nlights):
            self.final_hex_vals[i] = (utils.hsv_to_hex(0, 1, 1))

        return self.final_hex_vals

class Sweep_Left(EffectAlgorithm):
    def __init__(self, bpm, nlights, initial_hex_vals):
        super().__init__(bpm, nlights, initial_hex_vals)
        self.count = 0
        self.string_len = nlights//4
        self.update_range = np.arange(0, self.string_len)
        self.color = rd.random()

    def update(self):
        if self.cur_time() - self.times[-1] >= self.period/2:
        # if True:
            if self.count >= 4:
                self.count = 0
                self.color = rd.random()

            self.update_range = np.arange(self.count*self.string_len, (self.count*self.string_len) + self.string_len)

            self.count = self.count + 1

            self.log_time()

        for i in self.update_range:
            self.final_hex_vals[i] = (utils.hsv_to_hex(self.color , 1, 1))

        if self.count == 4:
            self.done = 1
        return self.final_hex_vals

class Sweep_Right(EffectAlgorithm):
    def __init__(self, bpm, nlights, initial_hex_vals):
        super().__init__(bpm, nlights, initial_hex_vals)
        self.count = 3
        self.string_len = nlights//4
        self.update_range = np.arange(self.count*self.string_len, (self.count*self.string_len) + self.string_len)
        self.color = rd.random()

    def update(self):
        if self.cur_time() - self.times[-1] >= self.period/2:
        # if True:
            if self.count < 0:
                self.done = 1
                self.count = 3
                self.color = rd.random()

            self.update_range = np.arange(self.count*self.string_len, (self.count*self.string_len) + self.string_len)

            self.count = self.count - 1

            self.log_time()

        for i in self.update_range:
            self.final_hex_vals[i] = (utils.hsv_to_hex(self.color, 1, 1))

        if self.count == -1:
            self.done = 1
        return self.final_hex_vals

def update_string(led, string, string_len):
    #return np.arange(string*string_len, (string*string_len) + string_len)
    return led + string*string_len


class Gradient_Sweep(EffectAlgorithm):
    def __init__(self, bpm, nlights, initial_hex_vals):
        super().__init__(bpm, nlights, initial_hex_vals)
        self.string_len = nlights//4
        print(self.string_len)

        self.color_matrix = np.zeros((self.string_len, self.string_len))
        a = rd.randint(0, 100)/100
        b = rd.randint(0, 100)/100
        if a > b:
            self.color1 = b
            self.color2 = a
        else:
            self.color1 = a
            self.color2 = b
        self.shift = 0
        self.shifter = self.string_len//16
        self.shift_count = 0
        self.shift_array = [0, 10, 20, 30]

        for x in range(self.string_len):
            for y in range(self.string_len):
                self.color_matrix[x,y] = (np.sqrt(x**2 + y**2)/np.sqrt(self.string_len**2 + self.string_len**2)) * (self.color2 - self.color1) + self.color1
                #print(self.color_matrix[x,y])

    def update(self):
        #print(self.shift)
        #print('FUCK')
        if self.cur_time() - self.times[-1] >= self.period/4:
        # if True:
            self.log_time()

            # if self.shift_count >= 8:
            #     if self.shifter >= 10:
            #         self.shifter = 0
            #     self.shift_count = 0

        #if self.cur_time() - self.times[-1] >= self.period/8:
            #print(self.shift)
            self.shift = self.shift + self.shifter
            for i in range(len(self.shift_array)):
                self.shift_array[i] = self.shift_array[i] + self.shifter

                if self.shift_array[i] >= self.string_len:
                    self.shift_count = self.shift_count + 1
                    if self.shift_count >= 3:
                        self.done = 1
                    self.shift_array[i] = self.shift_array[i] - self.string_len

            # if self.shift >= self.string_len:
            #     self.done = 0
            #     self.shift = self.string_len
            #     self.shift = 0
            # if self.shift < 0:
            #     self.shift = 0

        #print(self.shift_array)

        for i in range(4):
            for l in range(self.string_len):
                #print('l: {0}'.format(l))
                #print('shift: {0}'.format(self.shift+i))
                self.final_hex_vals[update_string(l, i, self.string_len)] = utils.hsv_to_hex(self.color_matrix[self.shift_array[i],l], 1, 1)

        return self.final_hex_vals

class Chase_Down(EffectAlgorithm):
    def __init__(self, bpm, nlights, initial_hex_vals):
        self.color = rd.random()
        for i in range(len(initial_hex_vals)):
            initial_hex_vals[i] = utils.hsv_to_hex(self.color, 0, 0)
        super().__init__(bpm, nlights, initial_hex_vals)
        self.count = 0
        self.string_len = nlights//4

    def update(self):
        if self.cur_time() - self.times[-1] >= self.period/4:
        # if True:
            self.count = self.count + 10
            if self.count >= self.string_len:
                self.done = 1
                self.count = 0
                self.color = rd.random()
            self.log_time()

        for i in range(4):
            for l in range(self.count):
                self.final_hex_vals[update_string(l, i, self.string_len)] = utils.hsv_to_hex(self.color, 1, 1)

        return self.final_hex_vals

class Expanding_Stars(EffectAlgorithm):
    def __init__(self, bpm, nlights, initial_hex_vals):
        self.color = rd.random()
        for i in range(len(initial_hex_vals)):
            initial_hex_vals[i] = utils.hsv_to_hex(self.color, 0, 0)
        super().__init__(bpm, nlights, initial_hex_vals)
        self.count = 0
        self.string_len = nlights//4
        self.color_matrix = np.zeros((self.string_len, 4))
        self.color_matrix[rd.randint(0, self.string_len)][rd.randint(0, 4)] = rd.random()

    def update(self):
        if self.cur_time() - self.times[-1] >= self.period/4:
        # if True:
            self.count = self.count + 10
            if self.count >= self.string_len:
                self.done = 1
                self.count = 0
                self.color = rd.random()
            self.log_time()

            for string in range(4):
                for led in range(self.string_len):
                    self.final_hex_vals[string*self.string_len+led] = self.color_matrix[led][string]

            for string in range(4):
                for led in range(self.string_len):
                    self.final_hex_vals[string*self.string_len+led] = self.color_matrix[led][string]

        return self.final_hex_vals

#flashy strobe blobs
#mega twinkle

ALGORITHM_LIST = [Sweep_Left, Sweep_Right, Gradient_Sweep, Chase_Down, Expanding_Stars]
