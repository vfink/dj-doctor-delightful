from renderers.teensy.light_sender import LightSender
import utils


if __name__ == '__main__':
    total_leds = 10
    lights = LightSender(nlights=total_leds)
    lights.configure()
