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
            color = utils.hsv_to_hex(.07, 1, 1)
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

def every_other(num_leds):
    num_array = []
    for num in range(num_leds):
        if num% 2:
            white = utils.hsv_to_hex(0, 0, .1)
            num_array += [white]
        else:
            color = utils.hsv_to_hex(.07, 1, 1)
            num_array += [color]
    return num_array

class Switch_Left(EffectAlgorithm):

    def __init__(self, bpm, nlights, initial_hex_vals):
        super().__init__(bpm, nlights, initial_hex_vals)
        self.count = 1
        self.string_len = nlights // 4
        self.update_range1 = np.arange(0 , self.string_len // 2)
        self.update_range2 = np.arange(self.string_len // 2, self.string_len)
        self.color1 = rd.random()
        self.color2 = rd.random()

    def update(self):
        if self.cur_time() - self.times[-1] >= self.period:
            if self.count >= 4:
                self.done = 1
                self.count = 0
                self.color = rd.random()

            self.update_range1 = np.arange(self.count * self.string_len,
                                           (self.count * self.string_len) + self.string_len // 2)
            self.update_range2 = np.arange(self.count * self.string_len + self.string_len // 2,
                                           (self.count * self.string_len) + self.string_len)

            self.count = self.count + 1

            self.log_time()

            new_color = self.color1
            self.color1 = self.color2
            self.color2 = new_color

        for i in self.update_range1:
            self.final_hex_vals[i] = (utils.hsv_to_hex(self.color1, 1, 1))
        for i in self.update_range2:
            self.final_hex_vals[i] = (utils.hsv_to_hex(self.color2, 1, 1))

        if self.count == 4:
            self.done = 1
        return self.final_hex_vals

class Switch_Right(EffectAlgorithm):
    def __init__(self, bpm, nlights, initial_hex_vals):
        super().__init__(bpm, nlights, initial_hex_vals)
        self.count = 2
        self.string_len = nlights // 4
        self.update_range1 = np.arange(0 , self.string_len // 2)
        self.update_range2 = np.arange(self.string_len // 2, self.string_len)
        self.color1 = rd.random()
        self.color2 = rd.random()

    def update(self):
        if self.cur_time() - self.times[-1] >= self.period:
            if self.count < 0:
                self.done = 1
                self.count = 3
                self.color = rd.random()

            self.update_range1 = np.arange(self.count*self.string_len,
                                           (self.count*self.string_len) + self.string_len//2)
            self.update_range2 = np.arange(self.count * self.string_len + self.string_len//2,
                                           (self.count * self.string_len) + self.string_len)

            self.count = self.count - 1

            self.log_time()

            new_color = self.color1
            self.color1 = self.color2
            self.color2 = new_color

        for i in self.update_range1:
            self.final_hex_vals[i] = (utils.hsv_to_hex(self.color1, 1, 1))
        for i in self.update_range2:
            self.final_hex_vals[i] = (utils.hsv_to_hex(self.color2, 1, 1))

        if self.count == -1:
            self.done = 1
        return self.final_hex_vals

#flashy strobe blobs
#mega twinkle

class Merge_Left_Bomber(EffectAlgorithm):
    def __init__(self, bpm, nlights, initial_hex_vals):
        super().__init__(bpm, nlights, bomber(nlights))
        self.count = 0
        self.measure_count = 0

    def update(self):
        if self.cur_time() - self.times[-1] >= self.period/4:
            if self.count >= 8:
                self.count = 0
                self.measure_count += 1

            self.final_hex_vals = np.roll(self.final_hex_vals,4)
            self.count = self.count + 1

            self.log_time()

        if self.measure_count == 1:
            self.done = 1
        return self.final_hex_vals

class Merge_Left_Spectrum(EffectAlgorithm):
    def __init__(self, bpm, nlights, initial_hex_vals):
        super().__init__(bpm, nlights, color_spectrum(nlights))
        self.string_len = nlights//4
        self.count = 0
        self.measure_count = 0

    def update(self):
        if self.cur_time() - self.times[-1] >= self.period/4:
            if self.count >= 8:
                self.count = 0
                self.measure_count += 1

            self.final_hex_vals = np.roll(self.final_hex_vals,(self.string_len//2))
            self.count = self.count + 1

            self.log_time()

        if self.measure_count == 1:
            self.done = 1
        return self.final_hex_vals

class Merge_Right_Bomber(EffectAlgorithm):
    def __init__(self, bpm, nlights, initial_hex_vals):
        super().__init__(bpm, nlights, bomber(nlights))
        self.count = 0
        self.measure_count = 0

    def update(self):
        if self.cur_time() - self.times[-1] >= self.period/4:
            if self.count >= 8:
                self.count = 0
                self.measure_count += 1

            self.final_hex_vals = np.roll(self.final_hex_vals,-4)
            self.count = self.count + 1

            self.log_time()

        if self.measure_count == 1:
            self.done = 1
        return self.final_hex_vals

class Merge_Right_Spectrum(EffectAlgorithm):
    def __init__(self, bpm, nlights, initial_hex_vals):
        super().__init__(bpm, nlights, color_spectrum(nlights))
        self.string_len = nlights//4
        self.count = 0
        self.measure_count = 0

    def update(self):
        if self.cur_time() - self.times[-1] >= self.period/4:
            if self.count >= 8:
                self.count = 0
                self.measure_count += 1

            self.final_hex_vals = np.roll(self.final_hex_vals,-(self.string_len//2))
            self.count = self.count + 1

            self.log_time()

        if self.measure_count == 1:
            self.done = 1
        return self.final_hex_vals

class Merge_Right_Rainbow(EffectAlgorithm):
    def __init__(self, bpm, nlights, initial_hex_vals):
        super().__init__(bpm, nlights, rainbow(nlights))
        self.count = 0
        self.measure_count = 0

    def update(self):
        if self.cur_time() - self.times[-1] >= self.period/4:
            if self.count >= 8:
                self.count = 0
                self.measure_count += 1

            self.final_hex_vals = np.roll(self.final_hex_vals,-4)
            self.count = self.count + 1

            self.log_time()

        if self.measure_count == 1:
            self.done = 1
        return self.final_hex_vals

class Merge_Left_Rainbow(EffectAlgorithm):
    def __init__(self, bpm, nlights, initial_hex_vals):
        super().__init__(bpm, nlights, rainbow(nlights))
        self.count = 0
        self.measure_count = 0

    def update(self):
        if self.cur_time() - self.times[-1] >= self.period/4:
            if self.count >= 8:
                self.count = 0
                self.measure_count += 1

            self.final_hex_vals = np.roll(self.final_hex_vals,4)
            self.count = self.count + 1

            self.log_time()


            self.log_time()

        if self.measure_count == 1:
            self.done = 1
        return self.final_hex_vals

class AC_Current(EffectAlgorithm):
    def __init__(self, bpm, nlights, initial_hex_vals):
        super().__init__(bpm, nlights, every_other(nlights))
        self.count = 0
        self.measure_count = 0

    def update(self):
        if self.cur_time() - self.times[-1] >= self.period:
            if self.count >= 4:
                self.count = 0
                self.measure_count += 1

            self.final_hex_vals = np.roll(self.final_hex_vals,1)
            self.count = self.count + 1

            self.log_time()

        if self.measure_count == 1:
            self.done = 1
        return self.final_hex_vals



ALGORITHM_LIST = [Sweep_Left, Sweep_Right, Gradient_Sweep, Chase_Down,
                    Merge_Left_Spectrum, Merge_Left_Bomber, Merge_Right_Spectrum,
                    Merge_Right_Bomber,Switch_Left,Switch_Right, Merge_Right_Rainbow,
                    Merge_Left_Rainbow, AC_Current]
