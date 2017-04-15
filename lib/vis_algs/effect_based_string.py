import numpy as np
import scipy.signal as signal
from renderers.teensy import serial_constants
import utils
from vis_algs import vis_alg_base

import random as rd
from music_processors.bpm_detection import BPMDetector
from  renderers.teensy.light_effect_algorithm import *

import peakutils


class Visualizer(vis_alg_base.VisualizationAlgorithm):

    def __init__(self, nlights, spectrum_analyzer):
        super(Visualizer, self).__init__(nlights)
        self.effect_manager = EffectManager(nlights)
        self.snake = snake(color = utils.hsv_to_hex(0, 1, 1), nlights = nlights)
        self.log_time()
        self.freq_vals = spectrum_analyzer.get_freqs()
        self.freq_buffer_len = 100
        self.freq_buffer = np.zeros([self.freq_buffer_len, len(self.freq_vals)])

        self.hex_vals = []
        for i in range(self.nlights):
            self.hex_vals.append(utils.hsv_to_hex(0, 1, 1))

        self.sample_rate = spectrum_analyzer.sample_rate
        self.nsamples = spectrum_analyzer.nsamples
        self.auto_buffer_len = self.sample_rate*2//self.nsamples
        self.auto_buffer = np.zeros(self.auto_buffer_len)

        self.bpm = 0
        self.update_bpm(120)

        self.l_buffer_len = self.sample_rate*3//self.nsamples
        self.l_buffer = np.zeros(self.l_buffer_len)
        self.max_corr = 0
        self.max_l = 0

        self.power_buffer_len = self.sample_rate*2//self.nsamples
        self.power_buffer = np.zeros(self.power_buffer_len)

        self.current_algorithm = ALGORITHM_LIST[0][0](self.bpm, self.nlights, self.hex_vals)
        #self.s_buffer_len = self.sample_rate//(2*self.nsamples)
        #self.s_buffer = np.zeros(self.s_buffer_len)

        # count = 0
        # for i in self.freq_vals:
        #     print("{0} - {1}".format(count, i))
        #     count = count + 1

    def freq_to_hex2(self, freq):
        final_hex_vals = []
        b = sorted(list(range(self.nlights)) + list(range(self.nlights)) + list(range(self.nlights))+ list(range(self.nlights)))
        for i in range(self.nlights):

            final_hex_vals.append(utils.hsv_to_hex(freq[b[i]]/5000, 1, freq[b[i]]/5000))

        return final_hex_vals

    def freq_to_hex(self, freq):

        power = np.sum(20*np.log10(freq))
        self.power_buffer = np.roll(self.power_buffer, -1, axis=0)
        self.power_buffer[-1] = power
        power_avg = np.average(self.power_buffer, axis=0)

        #FREQ AVG TESTING
        # print(freq)
        self.freq_buffer = np.roll(self.freq_buffer, -1, axis=0)
        self.freq_buffer[-1] = np.reshape(freq, (1,len(self.freq_vals)))

        freq_avg = np.average(self.freq_buffer, axis=0)
        freq_avg_val = zip(freq_avg, self.freq_vals, freq)
        freq_avg_val = sorted(freq_avg_val, key=lambda tup: tup[0], reverse=True)

        if sum(freq) > 0:
            base = peakutils.baseline(freq_avg, 2)
        else:
            base = 0
        print(power_avg, power)
        if abs(power_avg-power) > power_avg*.2:
            final_hex_vals = self.current_algorithm.update()
            print('beat',self.current_algorithm.done)
            if self.current_algorithm.done:
                algorithm = ALGORITHM_LIST[rd.randint(0, len(ALGORITHM_LIST) - 1)]
                self.current_algorithm = algorithm[0](self.bpm, self.nlights, algorithm[1])
                #self.current_algorithm = ALGORITHM_LIST[3](self.bpm, self.nlights, self.hex_vals)
                print(type(self.current_algorithm))
        else:
            final_hex_vals = self.current_algorithm.update()

        if self.cur_time() - self.times[-1] >= self.period*4:
            self.log_time()
            print("BPM: {0}".format(self.bpm))

        self.hex_vals = final_hex_vals
        return final_hex_vals

    def update_s_buffer(self):
        samples_per_beat = int((1/(self.bpm/60)) * (self.sample_rate/self.nsamples))
        a = np.ones(samples_per_beat//4)
        b = np.zeros(samples_per_beat//4)
        b1 = np.concatenate((b, a))
        b2 = np.concatenate((b, a*.5))
        b3 = np.concatenate((b, a*.75))
        b4 = np.concatenate((b, a*.5))
        self.s_buffer = np.concatenate((b4, b3, b2, b1))
        #print(self.s_buffer)
        #print(self.bpm)

    def update_bpm(self, bpm):
        self.last_bpm = self.bpm
        self.bpm = bpm
        self.period = 1/(bpm/60)
        if self.bpm != self.last_bpm:
            self.update_s_buffer()

    def autocorr(self, x):
        result = np.correlate(x, x, mode='full')
        return result[result.size//2:]

    def get_highest_ind(self, indices, values, default):
        largest = -1
        largest_ind = 0
        for i in indices:
            if values[i] > largest:
                largest = values[i]
                largest_ind = i

        if largest == -1:
            largest_ind = default

        return largest_ind

class EffectManager(object):

    def __init__(self, nlights=serial_constants.TOTAL_LEDS):
        self.nlights = nlights #total number of LEDs
        a = list(range(self.nlights)) #list with index number for every led
        self.lightDict = dict.fromkeys(a) #dictionary {ledIndex: color}

        #LED indices for 8 separate segments
        g = [200, 420, 540, 660, 865, 1071, 1192]
        s0 = list(range(0,g[0]))
        s1 = list(range(g[0],g[1]))
        s2 = list(range(g[1],g[2]))
        s3 = list(range(g[2],g[3]))
        s4 = list(range(g[3],g[4]))
        s5 = list(range(g[4],g[5]))
        s6 = list(range(g[5],g[6]))
        s7 = list(range(g[6],self.nlights))

        #dictionary containing indices for leds in all segments
        self.sectionsDict = {0:s0, 1:s1, 2:s2, 3:s3, 4:s4, 5:s5, 6:s6, 7:s7}

    #color a single led
    def color_one(self, led, color):
        if led >= nlights:
            pass
        else:
            self.lightDict[led] = color

    #make all the LEDs in one section one color
    def colorSections(self, sectionList, color):
        for sectionNum in sectionList:
            for ledNum in self.sectionsDict[sectionNum]:
                self.lightDict[ledNum] = color

    #make all the LEDs in half a section one color
    #sectionTupleList should be (sectionNum, 0 or 1) 0 or 1 for different halves
    def colorHalfSections(self, sectionTupleList,  color):
        for sectionNum,half in sectionTupleList:
            count = 0
            for ledNum in self.sectionsDict[sectionNum]:
                if count < len(self.sectionsDict[sectionNum])//2 and half == 0:
                    self.lightDict[ledNum] = color
                elif count > len(self.sectionsDict[sectionNum])//2 and half == 1:
                    self.lightDict[ledNum] = color

                count = count + 1

    #turns every 3rd LED in a section on for a strobe effect
    def strobeSection(self, sectionList):
        for sectionNum in sectionList:
            for ledNum in self.sectionsDict[sectionNum]:
                if ledNum % 3 == 0:
                    self.lightDict[ledNum] = utils.hsv_to_hex(1, 0, 1)

    def toByteArray(self):
        output = []
        for k,v in self.lightDict.items():
            if v != None:
                x = 'L'.encode()
                output.append(x)
                i0 = k & 255 #low order bits
                i1 = (k & 65280) >> 8 #high order bits
                output.append(i0)
                output.append(i1)
                output.append(v[0])
                output.append(v[1])
                output.append(v[2])
        return bytearray(output)

    def get_light_Dict(self):
        return self.lightDict

#Generates a moving "snake" of light, length, velocity, and time of existance
#can be specified
class snake(object):
    def __init__(self, color, nlights=serial_constants.TOTAL_LEDS, start = 0,
                length = 1, velocity = 1, duration = 100, fade = True):
        self.nlights = nlights #total number of LEDs
        a = list(range(start, start+length)) #list with index number for leds in snake
        self.lightDict = dict.fromkeys(a) #dictionary {ledIndex: color}
        self.velocity = velocity
        self.length = length
        self.deathIndex = start + duration

        if fade:
            count = 0;
            for i in self.lightDict.keys():
                c = utils.dim_hex_color(color, 1-count*0.05)
                self.lightDict[i] = color;
                count = count + 1
        else:
            for i in self.lightDict.keys():
                self.lightDict[i] = color;


    #moves the snake, start and deathIndex should not require overlapping from
    #the last index in the LED array to the 0th.
    def update(self):
        tmp = {}
        for i in self.lightDict.keys():
            if i+self.velocity <= self.deathIndex:
                tmp[i+self.velocity] = self.lightDict[i]

        self.lightDict = tmp


    def get_light_Dict(self):
        return self.lightDict
