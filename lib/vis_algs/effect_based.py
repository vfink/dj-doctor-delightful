import numpy as np
import scipy.signal as signal
from renderers.teensy import serial_constants
import utils
from vis_algs import vis_alg_base

import random as rd
from music_processors.bpm_detection import BPMDetector

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
        # print(freq)
        #FREQ AVG TESTING
        self.freq_buffer = np.roll(self.freq_buffer, -1, axis=0)
        self.freq_buffer[-1] = np.reshape(freq, (1,len(self.freq_vals)))

        freq_avg = np.average(self.freq_buffer, axis=0)
        freq_avg_val = zip(freq_avg, self.freq_vals, freq)
        freq_avg_val = sorted(freq_avg_val, key=lambda tup: tup[0], reverse=True)

        if sum(freq) > 0:
            base = peakutils.baseline(freq_avg, 2)
        else:
            base = 0


        # sub = peakutils.indexes(freq_avg[7:19], thres=.8, min_dist=2) + 14
        # low = peakutils.indexes(freq_avg[20:31], thres=.8, min_dist=2) + 20
        # mid = peakutils.indexes(freq_avg[32:130], thres=.5, min_dist=2) + 32
        # high = peakutils.indexes(freq_avg[200:1200], thres=.5, min_dist=2) + 200
        #
        # # subpeaks = peakutils.indexes(freq_avg-base, thres=.8, min_dist=10)
        # #subpeaks = np.concatenate((sub,low,mid,high))
        # subpeaks = [self.get_highest_ind(sub, freq_avg, 7), self.get_highest_ind(low, freq_avg, 20), self.get_highest_ind(mid, freq_avg, 31), self.get_highest_ind(high, freq_avg, 200)]
        # for i in range(0, len(freq_avg)):
        #     if freq[i] < freq_avg[i]:
        #         freq[i] = 0
        #     if i not in subpeaks:
        #          #freq_avg[i] = 0
        #         freq[i] = 0

        # f_diff = np.absolute(np.diff(np.vstack((freq_avg, freq)), axis = 0))
        #
        return (freq_avg/max(freq_avg), freq/max(freq))
        # return np.reshape(f_diff, (len(self.freq_vals),))

        #AUTO CORRELATION TESTING
        # self.auto_buffer = np.roll(self.auto_buffer, -1, axis=0)
        # self.auto_buffer[-1] = freq[20]
        #
        # auto = self.autocorr(self.auto_buffer)
        #
        # # number of samples to bpm
        # sec_per_beat = np.arange(len(auto))/((self.sample_rate/self.nsamples)*60)
        # auto_lag = np.flip((1/sec_per_beat), 0)
        #
        # auto = np.flip(auto, 0)
        #
        # return (auto_lag,auto/max(auto))

        #CORRELATION TESTING
        # self.l_buffer = np.roll(self.l_buffer, -1, axis=0)
        # #self.l_buffer[-1] = self.s_buffer[0]
        # self.l_buffer[-1] = freq[20]**2
        #
        # # self.s_buffer = np.roll(self.s_buffer, -1, axis=0)
        # # self.s_buffer[-1] = freq[20]
        #
        # a = max(self.l_buffer)
        # if self.max_l < a:
        #      self.max_l = a
        #
        # corr = np.correlate(self.l_buffer, self.s_buffer, mode='same')
        #
        # # if sum(corr) > 0:
        # #     base = peakutils.baseline(corr, 2)
        # # else:
        # #     base = 0
        # #
        # # corr = corr-base
        # # corr = corr/max(corr)
        # #
        # # pre_filter = corr
        # # #indexes = peakutils.indexes(corr, thres=.4, min_dist=1)
        # # window = signal.general_gaussian(5, p=0.5, sig=20)
        # # filtered = signal.fftconvolve(window, corr)
        # # corr = (np.average(corr) / np.average(filtered)) * filtered
        # #
        # # pre_peak = np.copy(corr)
        # # subpeaks = peakutils.indexes(corr, thres=.4, min_dist=1)
        # # for i in range(0, len(corr)):
        # #     if i not in subpeaks:
        # #         corr[i] = 0
        #
        # sec_corr_lag = np.arange(len(corr))/(self.sample_rate/self.nsamples)
        # min_corr_lag = sec_corr_lag/60
        # corr_lag = min_corr_lag * self.bpm
        #
        # a = max(corr)
        # if self.max_corr < a:
        #      self.max_corr = a
        #
        # return (corr_lag, corr/self.max_corr, self.l_buffer/self.max_l)

        # print('###')
        if len(subpeaks) > 0:
        #     ind = 0
        #     x = np.zeros(len(subpeaks))
        #     for i in subpeaks:
        #         print("peak at {0}Hz".format(self.freq_vals[i]))
        #         if freq_avg[i]*1.25 < freq[i]:
        #             x[ind] = 1
        #         ind = ind + 1

            x = np.zeros(4)
            for i in range(4):
                if freq_avg[subpeaks[i]] == 0:
                    f = 1
                else:
                    f = freq_avg[subpeaks[i]]
                x[i] = freq[subpeaks[i]]/f

            self.effect_manager.colorSections([0], utils.hsv_to_hex(0, 1, x[0]))
            self.effect_manager.colorSections([1], utils.hsv_to_hex(.8, 1, x[3]))
            self.effect_manager.colorSections([2], utils.hsv_to_hex(.6, 1, x[2]))
            self.effect_manager.colorSections([3], utils.hsv_to_hex(.3, 1, x[1]))
            self.effect_manager.colorSections([4], utils.hsv_to_hex(.8, 1, x[3]))
            self.effect_manager.colorSections([5], utils.hsv_to_hex(0, 1, x[0]))
            self.effect_manager.colorSections([6], utils.hsv_to_hex(.3, 1, x[1]))
            self.effect_manager.colorSections([7], utils.hsv_to_hex(.6, 1, x[2]))
        else:
            self.effect_manager.colorSections(np.arange(8), utils.hsv_to_hex(0, 1, 0))

        if self.cur_time() - self.times[-1] >= self.period*4:
            if rd.randint(0, 1):
                self.effect_manager.strobeSection([0, 2, 4, 6])
            else:
                self.effect_manager.strobeSection([1, 3, 5, 7])
            self.log_time()
            print("BPM: {0}".format(self.bpm))

        tmp_dict = self.effect_manager.get_light_Dict()

        if len(self.snake.get_light_Dict()) == 0:
            start = rd.randint(0, self.nlights-200)
            length = rd.randint(1,20)
            velocity = rd.randint(1, 5)
            duration = rd.randint(50, 200)
            self.snake = snake(color = utils.hsv_to_hex((rd.random()/10), 1, 1),
                                nlights = self.nlights, start = start,
                                length=length, velocity=velocity,
                                duration= duration)
        else:
            self.snake.update()
            for i in self.snake.get_light_Dict().keys():
                tmp_dict[i] = self.snake.get_light_Dict()[i]

        final_hex_vals = []
        for i in range(self.nlights):
            final_hex_vals.append(tmp_dict[i])

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
        print(self.s_buffer)
        print(self.bpm)

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
