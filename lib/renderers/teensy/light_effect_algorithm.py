import numpy as np
import math
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

def color_full(num_leds, color = rd.random()):
    num_array = []
    for num in range(num_leds):
        num_array.append(utils.hsv_to_hex(color,1,1))
    return num_array

def color_spectrum(num_leds):
    num_array = []
    for num in range(num_leds):
        color_num = num/num_leds
        color = utils.hsv_to_hex(color_num,1,1)
        num_array.append(color)
    return num_array

def bomber(num_leds):
    num_array = []
    for num in range(int(num_leds/4)):
        if num% 2:
            color = utils.hsv_to_hex(.25,1,1)
            num_array += [color] * 4
        else:
            white = utils.hsv_to_hex(0, 0, .1)
            num_array += [white] * 4
    return num_array

num_lights = 500



class Sweep_Left(EffectAlgorithm):
    def __init__(self, bpm, nlights, initial_hex_vals):
        super().__init__(bpm, nlights, initial_hex_vals)
        self.count = 0
        self.string_len = nlights//4
        self.update_range = np.arange(0, self.string_len)
        self.color = rd.random()

    def update(self):
        if self.cur_time() - self.times[-1] >= self.period/12:
            if self.count >= 4:
                self.count = 0
                self.color = rd.random()

            self.update_range = np.arange(self.count*self.string_len, (self.count*self.string_len) + self.string_len)

            self.count = self.count + 1

            self.log_time()

        for i in self.update_range:
            self.final_hex_vals[i] = (utils.hsv_to_hex(self.color , 1, 1))

        if self.count == 4:
            print('should be done')
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
        if self.cur_time() - self.times[-1] >= self.period:
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
            print('should be done')
            self.done = 1
        return self.final_hex_vals

class Merge_Left(EffectAlgorithm):
    def __init__(self, bpm, nlights, initial_hex_vals):
        super().__init__(bpm, nlights, initial_hex_vals)
        self.count = 0
        self.measure_count = 0

    def update(self):
        if self.cur_time() - self.times[-1] >= self.period/12:
            if self.count >= 48:
                self.count = 0
                self.measure_count += 1

            self.final_hex_vals = np.roll(self.final_hex_vals,1)
            self.count = self.count + 1

            self.log_time()

        if self.measure_count == 4:
            print('should be done')
            self.done = 1
        return self.final_hex_vals


ALGORITHM_LIST = [(Sweep_Left,color_full(num_lights)), (Sweep_Right,color_full(num_lights)), (Merge_Left,color_spectrum(num_lights)), (Merge_Left,bomber(num_lights))]
