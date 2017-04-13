from renderers.pyqt.line_widget import LineWidget
from samplers.pyaudio_sampler import PyAudioSampler
from spectrum_analyzers.spectrum_analyzers import WindowedSTFT, CQT
from spectrum_analyzers.note_filter import NoteFilter
from music_processors.bpm_detection import *
from vis_algs.effect_based import Visualizer



from PyQt5 import QtGui
from PyQt5.QtCore import QObject, pyqtSlot

import sys
import numpy

if __name__ == '__main__':

    # Sampler params
    pa_device_index = None
    sample_rate = 44100
    sampleMultiplier = 400
    nsamples = 4096
    max_freq = 10000

    # Instantiate sampler and spectrum analyzer
    sampler = PyAudioSampler(pa_device_index, sample_rate, nsamples)

    note_filt = NoteFilter(sampler.nsamples, sampler.rate)

    bpm_detector = BPMDetector(sampler.rate, sampler.nsamples, sampleMultiplier)

    # spectrum_analyzer = WindowedSTFT(sampler.nsamples, sampler.rate,
    #         logscale=False)
    spectrum_analyzer = CQT(sampler.nsamples, sampler.rate, n_octaves=8, bins_per_octave=24)

    vis = Visualizer(1600, spectrum_analyzer)

    app = QtGui.QApplication([])

    line_widget = LineWidget(spectrum_analyzer)

#line plot of freq averages
    def get_spectrum():
        chunk = sampler.read_chunk()
        bpm_detector.detect_beat(chunk)
        vis.update_bpm(bpm_detector.tempo)
        return vis.freq_to_hex(spectrum_analyzer.get_spectrum(chunk))

    line_widget.get_spectrum = get_spectrum



    line_widget.update_power()

    # Start the app
    print('Entering blocking PyQt5 GUI')
    app.exec_()

    print('Exiting blocking PyQt5 GUI')
