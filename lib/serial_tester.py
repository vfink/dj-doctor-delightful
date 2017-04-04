from renderers.teensy.light_sender import LightSender
from renderers.teensy.light_effect_manager import *

import sys
import os
import time
import colorsys
import random as rd

if __name__ == '__main__':
    devices = os.listdir('/dev')
    teensy = 0
    for i in devices:
        if 'cu.usbmodem' in i:
            print(i)
            teensy = '/dev/' + i;

    sender = LightSender(serial_port = teensy);
    effect = EffectManager();

    c = 0
    while(True):
        if c == 6:
            sender.send_light_dict(effect.get_light_Dict())
            effect.strobeSection([2,4,6])
            time.sleep(.25)
            sender.send_light_dict(effect.get_light_Dict())
            effect.colorSections([0,1,2,4,5,6,7], utils.hsv_to_rgb(7/8, 1, .25))
            sender.send_light_dict(effect.get_light_Dict())
            c = 0;

        c = c+1;
        effect.colorSections([0], utils.hsv_to_rgb((rd.random()/10), 1, .25))
        effect.colorSections([1], utils.hsv_to_rgb((rd.random()/10), 1, .25))
        effect.colorSections([2], utils.hsv_to_rgb((rd.random()/10), 1, .25))
        effect.colorSections([3], utils.hsv_to_rgb((rd.random()/10), 1, .25))
        effect.colorSections([4], utils.hsv_to_rgb((rd.random()/10), 1, .25))
        effect.colorSections([5], utils.hsv_to_rgb((rd.random()/10), 1, .25))
        effect.colorSections([6], utils.hsv_to_rgb((rd.random()/10), 1, .25))
        effect.colorSections([7], utils.hsv_to_rgb((rd.random()/10), 1, .25))

    time.sleep(.5)
