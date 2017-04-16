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
            white = utils.hsv_to_hex(0, 0, .1)
            num_array += [white] * 4
        else:
            color = utils.hsv_to_hex(.13, 1, 1)
            num_array += [color] * 4
    return num_array

def rainbow(num_leds):
    num_array = []
    for num in range(int(num_leds/4)):
        if num%6 == 0:
            color = utils.hsv_to_hex(0, 1, 1)
        elif num%6 == 1:
            color = utils.hsv_to_hex(.13, 1, 1)
        elif num%6 == 2:
            color = utils.hsv_to_hex(.20, 1, 1)
        elif num%6 == 3:
            color = utils.hsv_to_hex(.35, 1, 1)
        elif num%6 == 4:
            color = utils.hsv_to_hex(.60, 1, 1)
        elif num%6 == 5:
            color = utils.hsv_to_hex(.75, 1, 1)
        num_array += [color] * 4
    return num_array

class Switch_Left(EffectAlgorithm):
    def __init__(self, bpm, nlights, initial_hex_vals):
        super().__init__(bpm, nlights, initial_hex_vals)
        self.count = 0
        self.string_len = nlights//8
        self.update_range = np.arange(0, self.string_len)
        self.color1 = rd.random()
        self.color2 = rd.random()
        self.color = self.color1

    def update(self):
        if self.cur_time() - self.times[-1] >= self.period:
            if self.count >= 8:
                self.count = 0
                self.color = rd.random()

            self.update_range = np.arange(self.count*self.string_len, (self.count*self.string_len) + self.string_len)

            if self.color == self.color1:
                self.color = self.color2
            else:
                self.color = self.color1

            self.count = self.count + 1

            self.log_time()

        for i in self.update_range:
            self.final_hex_vals[i] = (utils.hsv_to_hex(self.color , 1, 1))

        if self.count == 8:
            self.done = 1
        return self.final_hex_vals

class Switch_Right(EffectAlgorithm):
    def __init__(self, bpm, nlights, initial_hex_vals):
        super().__init__(bpm, nlights, initial_hex_vals)
        self.count = 7
        self.string_len = nlights//8
        self.update_range = np.arange(self.count*self.string_len, (self.count*self.string_len) + self.string_len)
        self.color1 = rd.random()
        self.color2 = rd.random()
        self.color = self.color1

    def update(self):
        if self.cur_time() - self.times[-1] >= self.period:
            if self.count < 0:
                self.done = 1
                self.count = 7
                self.color = rd.random()

            self.update_range = np.arange(self.count*self.string_len, (self.count*self.string_len) + self.string_len)

            self.count = self.count - 1

            self.log_time()

            if self.color == self.color1:
                self.color = self.color2
            else:
                self.color = self.color1

        for i in self.update_range:
            self.final_hex_vals[i] = (utils.hsv_to_hex(self.color, 1, 1))

        if self.count == -1:
            self.done = 1
        return self.final_hex_vals



class Sweep_Left(EffectAlgorithm):
    def __init__(self, bpm, nlights, initial_hex_vals):
        super().__init__(bpm, nlights, initial_hex_vals)
        self.count = 0
        self.string_len = nlights//4
        self.update_range = np.arange(0, self.string_len)
        self.color = rd.random()

    def update(self):
        if self.cur_time() - self.times[-1] >= self.period:
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
            self.done = 1
        return self.final_hex_vals

class Merge_Left_Bomber(EffectAlgorithm):
    def __init__(self, bpm, nlights, initial_hex_vals):
        super().__init__(bpm, nlights, bomber(nlights))
        self.count = 0
        self.measure_count = 0

    def update(self):
        if self.cur_time() - self.times[-1] >= self.period/24:
            if self.count >= 48:
                self.count = 0
                self.measure_count += 1

            self.final_hex_vals = np.roll(self.final_hex_vals,1)
            self.count = self.count + 1

            self.log_time()

        if self.measure_count == 2:
            self.done = 1
        return self.final_hex_vals

class Merge_Left_Spectrum(EffectAlgorithm):
    def __init__(self, bpm, nlights, initial_hex_vals):
        super().__init__(bpm, nlights, color_spectrum(nlights))
        self.count = 0
        self.measure_count = 0

    def update(self):
        if self.cur_time() - self.times[-1] >= self.period/24:
            if self.count >= 48:
                self.count = 0
                self.measure_count += 1

            self.final_hex_vals = np.roll(self.final_hex_vals,1)
            self.count = self.count + 1

            self.log_time()

        if self.measure_count == 2:
            self.done = 1
        return self.final_hex_vals

class Merge_Right_Bomber(EffectAlgorithm):
    def __init__(self, bpm, nlights, initial_hex_vals):
        super().__init__(bpm, nlights, bomber(nlights))
        self.count = 0
        self.measure_count = 0

    def update(self):
        if self.cur_time() - self.times[-1] >= self.period/24:
            if self.count >= 48:
                self.count = 0
                self.measure_count += 1

            self.final_hex_vals = np.roll(self.final_hex_vals,-1)
            self.count = self.count + 1

            self.log_time()

        if self.measure_count == 2:
            self.done = 1
        return self.final_hex_vals

class Merge_Right_Spectrum(EffectAlgorithm):
    def __init__(self, bpm, nlights, initial_hex_vals):
        super().__init__(bpm, nlights, color_spectrum(nlights))
        self.count = 0
        self.measure_count = 0

    def update(self):
        if self.cur_time() - self.times[-1] >= self.period/24:
            if self.count >= 48:
                self.count = 0
                self.measure_count += 1

            self.final_hex_vals = np.roll(self.final_hex_vals,-1)
            self.count = self.count + 1

            self.log_time()

        if self.measure_count == 2:
            self.done = 1
        return self.final_hex_vals

class Merge_Right_Rainbow(EffectAlgorithm):
    def __init__(self, bpm, nlights, initial_hex_vals):
        super().__init__(bpm, nlights, rainbow(nlights))
        self.count = 0
        self.measure_count = 0

    def update(self):
        if self.cur_time() - self.times[-1] >= self.period/24:
            if self.count >= 48:
                self.count = 0
                self.measure_count += 1

            self.final_hex_vals = np.roll(self.final_hex_vals,-1)
            self.count = self.count + 1

            self.log_time()

        if self.measure_count == 2:
            self.done = 1
        return self.final_hex_vals


ALGORITHM_LIST = [Sweep_Left, Sweep_Right, Merge_Left_Spectrum, Merge_Left_Bomber,
                  Merge_Right_Spectrum,Merge_Right_Bomber,Switch_Left,Switch_Right, Merge_Right_Rainbow]
