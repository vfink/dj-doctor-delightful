from renderers.pyqt.spectrogram_widget import SpectrogramWidget
from samplers.pyaudio_sampler_async import PyAudioSamplerAsync
from spectrum_analyzers.spectrum_analyzers import WindowedSTFT
from music_processors.bpm_detection import *

from PyQt5 import QtGui
from PyQt5.QtCore import QObject, pyqtSignal

import sys
import numpy
from multiprocessing import Process, Queue, Event

if __name__ == '__main__':

    # Sampler params
    pa_device_index = None
    sample_rate = 44100
    #sampleMultiplier = 200
    #nsamples = 4096
    sampleMultiplier = 3
    nsamples = 882000
    max_freq = 5

    # Instantiate sampler and spectrum analyzer
    sampler = PyAudioSamplerAsync(pa_device_index, sample_rate, nsamples,
            sampleMultiplier)

    bpmDetector = BPMDetector(sampler.rate, sampler.nsamples, sampleMultiplier)

    # spectrum_analyzer = WindowedSTFT(sampler.nsamples, sampler.rate,
    #         logscale=True)

    spectrum_analyzer = WindowedSTFT(bpmDetector.effectiveNSamples,
                bpmDetector.effectiveRate,logscale=True)

    app = QtGui.QApplication([])
    #spectrogram_widget = SpectrogramWidget(spectrum_analyzer, max_freq)

#Spectrogram
    # Add spectrum getter function to the widget
    # def get_spectrum():
    #     return spectrum_analyzer.get_spectrum(sampler.read_chunk())
    # spectrogram_widget.get_spectrum = get_spectrum

    bpm_widget = BPMWidgetAsync(spectrum_analyzer)

    bpm_widget.read_collected.connect(bpm_widget.update)

    sampler.signal = bpm_widget.read_collected

#Spectrogram BPM with FFT
    def get_spectrum(chunk):
        return spectrum_analyzer.get_spectrum(bpmDetector.updateFFTBPM(chunk))
        #return spectrum_analyzer.get_spectrum(bpmDetector.updateFFTBPM(bpmDetector.consolidate(10, sampler)))
    #spectrogram_widget.get_spectrum = get_spectrum
    bpm_widget.get_spectrum = get_spectrum

    #while(True):
        #beat = bpmDetector.update(sampler.read_chunk())
        #print(beat)
        #out = bpmDetector.updateFFTBPM(sampler.read_chunk())
    # def get_spectrum():
    #     s = []
    #     for i in range(0, sampleMultiplier):
    #         s = s + list(sampler.read_chunk())
    #     return bpmDetector.updateAutoBPM(s)
    # bpm_widget.get_spectrum = get_spectrum

    # Starts QtTimer.singleShot update loop
    # s = []
    # for i in range(0, sampleMultiplier):
    #     s = s + list(sampler.read_chunk())
    #
    # bpmDetector.setBigChunk(s)

    #spectrogram_widget.update()
    def async_stream_read(q, event, sampler, sampleMultiplier):
        while event.is_set():
            s = []
            print(type(sampler))
            print(sampleMultiplier)
            sys.stdout.flush()
            for i in range(0, sampleMultiplier):
                print(i)
                sys.stdout.flush()
                s = s + list(sampler.read_chunk())
                print('BLEEEH')
                sys.stdout.flush()
            print('okay')
            sys.stdout.flush()
            q.put(s)

        print(event.is_set())
        sys.stdout.flush()
        q.close()

    # q = Queue()
    # continueProcess = Event()
    # continueProcess.set()
    # p = Process(target=async_stream_read, args=(q,continueProcess, sampler, sampleMultiplier))
    #
    # p.start()
    # s = []
    # sCount = 0
    # while True:
    #     if sCount == sampleMultiplier:
    #         bpm_widget.updateGraph(s)
    #         s=[]
    #         sCount = 0
    #     else:
    #         s = s + list(sampler.read_chunk())
    #         sCount = sCount + 1

    sampler.start()

    # Start the app
    print('Entering blocking PyQt5 GUI')
    app.exec_()

    # continueProcess.clear()
    # p.join()

    print('Exiting blocking PyQt5 GUI')
