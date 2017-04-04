import numpy as np
from renderers.teensy import serial_constants
import utils
from vis_algs import vis_alg_base

import random as rd
from music_processors.bpm_detection import BPMDetector



class Visualizer(vis_alg_base.VisualizationAlgorithm):

    def __init__(self, nlights):
        super(Visualizer, self).__init__(nlights)
        self.effect_manager = EffectManager(nlights)
        self.snake = snake(color = utils.hsv_to_hex(0, 1, 1), nlights = nlights)
        self.log_time()

    def freq_to_hex(self, freq):

        self.effect_manager.colorSections([0], utils.hsv_to_hex(0, 1, freq[20]))
        self.effect_manager.colorSections([1], utils.hsv_to_hex(.2, 1, freq[100]))
        self.effect_manager.colorSections([2], utils.hsv_to_hex(.3, 1, freq[200]))
        self.effect_manager.colorSections([3], utils.hsv_to_hex(.4, 1, freq[300]))
        self.effect_manager.colorSections([4], utils.hsv_to_hex(.5, 1, freq[400]))
        self.effect_manager.colorSections([5], utils.hsv_to_hex(.6, 1, freq[500]))
        self.effect_manager.colorSections([6], utils.hsv_to_hex(.7, 1, freq[600]))
        self.effect_manager.colorSections([7], utils.hsv_to_hex(.8, 1, freq[700]))

        if self.cur_time() - self.times[-1] >= self.period*4:
            self.effect_manager.strobeSection([0, 2, 4, 6])
            self.log_time()
            print(self.bpm)

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

    def update_bpm(self, bpm):
        self.bpm = bpm
        self.period = 1/(bpm/60)

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
