import colorsys
import wave

import numpy as np
import pyqtgraph as pg


def read_wave(wave_path, nseconds):

    wave_reader = wave.open(wave_path, 'rb')
    sample_rate = wave_reader.getframerate()
    nchannels = wave_reader.getnchannels()
    nframes = nseconds * sample_rate

    samples = wave_reader.readframes(nframes)
    a = np.fromstring(samples, dtype=np.int16)
    a = a[::nchannels]
    return a, sample_rate


def get_pyqt_cmap(numpy_cmap):
    rgb = np.round(np.array(numpy_cmap.colors) * 256).astype(dtype=np.ubyte)
    stops = np.linspace(0, 1, len(rgb))
    return pg.ColorMap(stops, rgb)


class CircularBuffer(object):
    def __init__(self, n, dtype=float):
        self.n = n
        self.i = 0
        self.tape = np.zeros(self.n, dtype=dtype)

    def write(self, data):
        self.tape[self.i] = data
        self.update_i()

    def update_i(self):
        self.i = self.next_i()

    def next_i(self):
        return 0 if self.i == self.n - 1 else self.i + 1

    def prev_i(self):
        return self.n - 1 if self.i == 0 else self.i - 1

    def oldest(self):
        return self.tape[self.next_i()]

    def newest(self):
        return self.tape[self.prev_i()]


class CircularChunkBuffer(object):
    def __init__(self, n, chunk, dtype=float):
        self.n = n
        self.chunk = chunk
        self.i = 0
        self.tape = np.zeros(self.n * self.chunk, dtype=dtype)

    def write(self, data):
        self.tape[self.i * self.chunk:(self.i+1) * self.chunk] = data
        self.update_i()

    def update_i(self):
        self.i = self.next_i()

    def next_i(self):
        return 0 if self.i == self.n - 1 else self.i + 1

    def prev_i(self):
        return self.n - 1 if self.i == 0 else self.i - 1

    def oldest(self):
        return self.tape[self.next_i()]

    def newest(self):
        return self.tape[self.prev_i()]

    def unwind(self):
        return np.roll(self.tape, -self.i * self.chunk)


# rgb_val is between 0 and 255
def val_to_hex_str(rgb_val):

    representation = str(hex(rgb_val))[2:]
    if (len(representation) == 1):
        representation = "0" + representation
    return representation


def hsv_to_hex(h, s, v):
    (r, g, b) = colorsys.hsv_to_rgb(h, s, v)
    (R, G, B) = int(255 * r), int(255 * g), int(255 * b)
    hexval = "#" + val_to_hex_str(R) + val_to_hex_str(G) + val_to_hex_str(B)
    return hexval

def hsv_to_rgb(h,s,v):
    (r, g, b) = colorsys.hsv_to_rgb(h, s, v)
    (R, G, B) = int(255 * r), int(255 * g), int(255 * b)
    return (R, G, B)

def rgb_to_hex(rgb):
    return '#' + ''.join(map(val_to_hex_str, rgb))


def hex_to_rgb(hex_str):
    if len(hex_str) >= 7:
        hex_str = hex_str[1:]
    r_str, g_str, b_str = hex_str[0:2], hex_str[2:4], hex_str[4:6]
    return (int(r_str, 16), int(g_str, 16), int(b_str, 16))

def dim_hex_color(hex_str, dim):
    rgb = hex_to_rgb(hex_str)
    r = int(rgb[0] * dim)
    g = int(rgb[1] * dim)
    b = int(rgb[2] * dim)

    return rgb_to_hex((r,g,b))

def convex_poly_ramp(x, d=2):
    return -(x - 1) ** 2 + 1

#generates an array of musical note frequencies in a range of MIDI numbers
#defaults to a range from C1 to C7
def gen_note_freqs(start=24, end=96):
    notes =[]
    for i in range(start, end+1):
        note = 2**((i-69)/12) * 440
        notes.append(note)

    return notes

#takes a BPM and outputs the seconds between beats
def bpm_to_period(bpm):
    return (1/bpm)*60

#takes a sample rate and nsamples and returns seconds between samples
def samples_to_period(sample_rate, nsamples):
    return nsamples/sample_rate
