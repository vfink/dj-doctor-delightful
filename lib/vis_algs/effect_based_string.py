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


        self.current_algorithm = ALGORITHM_LIST[0](self.bpm, self.nlights, self.hex_vals)
        self.algo_beats = 1
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

    def pick_dtyd_algorithm(self, alg_list):
        #this is not a good function, i am hardcoding based on current alg names
        found = False
        while (found is False):
            result = alg_list[rd.randint(0, len(alg_list)-1)]
            if (result!=self.current_algorithm):
                #check for similar algs
                if (self.current_algorithm==Merge_Left_Rainbow and result==Merge_Right_Rainbow):
                    pass
                elif (self.current_algorithm==Merge_Right_Rainbow and result==Merge_Left_Rainbow):
                    pass
                elif (self.current_algorithm==Merge_Left_Bomber and result==Merge_Right_Bomber):
                    pass
                elif (self.current_algorithm==Merge_Right_Bomber and result==Merge_Left_Bomber):
                    pass
                else:
                    #print("new alg: ", result)
                    found = True
                    return result

    def freq_to_hex(self, freq):

        power = np.sum(20*np.log10(freq))
        # self.power_buffer = np.roll(self.power_buffer, -1, axis=0)
        # self.power_buffer[-1] = power
        # power_avg = np.average(self.power_buffer, axis=0)

        #FREQ AVG TESTING
        # print(freq)
        self.freq_buffer = np.roll(self.freq_buffer, -1, axis=0)
        self.freq_buffer[-1] = np.reshape(freq**2, (1,len(self.freq_vals)))

        freq_avg = np.average(self.freq_buffer, axis=0)
        freq_avg_val = zip(freq_avg, self.freq_vals, freq, np.arange(0, len(freq_avg)))
        freq_avg_val = sorted(freq_avg_val, key=lambda tup: tup[0], reverse=True)

        if sum(freq) > 0:
            base = peakutils.baseline(freq_avg, 2)
        else:
            base = 0

        low_end = 0
        low_avg = 0
        for i,j,k,u in freq_avg_val:
            if j < 70:
                continue
            low_end = low_end + k
            low_avg = low_avg + i
            # print('freq: {0}, Ind: {1}'.format(j, u))
            if j > 400:
                break

        # print('low_end: {0}'.format(low_end))
        # print('low_avg: {0}'.format(low_avg))

        self.l_buffer = np.roll(self.l_buffer, -1, axis=0)
        #self.l_buffer[-1] = self.s_buffer[0]
        # self.l_buffer[-1] = freq[20]**2
        self.l_buffer[-1] = low_end

        # self.s_buffer = np.roll(self.s_buffer, -1, axis=0)
        # self.s_buffer[-1] = freq[20]

        a = max(self.l_buffer)
        if self.max_l < a:
             self.max_l = a

        corr = np.correlate(self.l_buffer, self.s_buffer, mode='same')

        # if sum(corr) > 0:
        #     base = peakutils.baseline(corr, 2)
        # else:
        #     base = 0
        #
        # corr = corr-base
        # corr = corr/max(corr)
        #
        # pre_filter = corr
        # #indexes = peakutils.indexes(corr, thres=.4, min_dist=1)
        # window = signal.general_gaussian(5, p=0.5, sig=20)
        # filtered = signal.fftconvolve(window, corr)
        # corr = (np.average(corr) / np.average(filtered)) * filtered
        #
        # pre_peak = np.copy(corr)
        # subpeaks = peakutils.indexes(corr, thres=.4, min_dist=1)
        # for i in range(0, len(corr)):
        #     if i not in subpeaks:
        #         corr[i] = 0

        sec_corr_lag = np.arange(len(corr))/(self.sample_rate/self.nsamples)
        min_corr_lag = sec_corr_lag/60
        corr_lag = min_corr_lag * self.bpm

        a = max(corr)
        if self.max_corr < a:
             self.max_corr = a

        freq_diff = self.freq_buffer[-2] - self.freq_buffer[-1]

        if freq_diff[freq_avg_val[0][3]] < 0:
            freq_diff[freq_avg_val[0][3]] = 0

        self.power_buffer = np.roll(self.power_buffer, 1)
        self.power_buffer[0] = freq_diff[freq_avg_val[0][3]]

        butts = np.copy(self.power_buffer)
        subpeaks = peakutils.indexes(self.power_buffer, thres=.4, min_dist=1)
        for i in range(0, len(self.power_buffer)):
            if i not in subpeaks:
                butts[i] = 0
        #
        # if sum(butts[0:2]) > 0:
            #print('kapow')




        if sum(butts[0:2]) > 0:
            if self.current_algorithm.done and self.algo_beats > 8:
                self.algo_beats = 1
                print('boom')
                self.current_algorithm = self.pick_dtyd_algorithm(ALGORITHM_LIST)(self.bpm, self.nlights, self.hex_vals)
                # self.current_algorithm = ALGORITHM_LIST[3](self.bpm, self.nlights, self.hex_vals)
                print(type(self.current_algorithm))

            final_hex_vals = self.current_algorithm.update()
        else:
            final_hex_vals = self.current_algorithm.update()
            # final_hex_vals = self.hex_vals

        if self.cur_time() - self.times[-1] >= self.period:
            self.log_time()
            print("BPM: {0}".format(self.bpm))
            self.algo_beats = self.algo_beats + 1

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
