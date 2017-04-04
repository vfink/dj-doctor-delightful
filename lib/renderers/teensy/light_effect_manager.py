from renderers.teensy import serial_constants
import utils

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
                    self.lightDict[ledNum] = utils.hsv_to_rgb(1, 0, 1)

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
                c = dim_hex_color(color, 1-count*0.05)
                self.lightDict[i] = color;
                count = count + 1
        else:
            for i in self.lightDict.keys():
                self.lightDict[i] = color;


    #moves the snake, start and deathIndex should not require overlapping from
    #the last index in the LED array to the 0th.
    def update():
        for i in self.lightDict.keys():
            if i+self.velocity >= self.deathIndex:
                self.lightDict[i+self.velocity] = self.lightDict[i]
            del self.lightDict[i]

    def get_light_Dict():
        return self.lightDict
