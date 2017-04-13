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


ALGORITHM_LIST = [Sweep_Left, Sweep_Right]
