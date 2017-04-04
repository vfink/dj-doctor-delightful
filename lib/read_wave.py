import matplotlib.pyplot as plt
import numpy as np
import peakutils
from peakutils.plot import plot as pplot
import wave
import math
import time

from renderers.pyqt.spectrogram_widget import SpectrogramWidget
from spectrum_analyzers.spectrum_analyzers import WindowedSTFT

import pyaudio

from PyQt5 import QtGui
from PyQt5.QtCore import QObject, pyqtSlot

def differences(l):
    diffList = []
    for i in range(1, len(l)):
        diffList.append(l[i] - l[i-1])

    return diffList

def norm(l):
    s = 0
    for i in l:
        s = s + abs(i)**2

    return math.sqrt(s)

def detectBeat(samples, sample_rate, miniChunk):
    nsamples = len(samples)
    miniSample = []
    #miniChunk = 128
    win = np.hanning(nsamples//miniChunk)
    output = []
    for i in range(0, len(samples)):
        if len(miniSample) == miniChunk:
            diff = differences(miniSample)
            n = norm(diff)
            output.append(n)
            miniSample = [samples[i]]
        else:
            miniSample.append(samples[i])

    if len(miniSample) == miniChunk:
        diff = differences(miniSample)
        n = norm(diff)
        output.append(norm)

    print('nsamples:{0}\nchunksize:{1}\n {0} // {1} = {2}'.format(
        nsamples, miniChunk, nsamples // miniChunk))

    print('len(output){0}'.format(len(output)))


    spec = abs(np.fft.rfft(output * win) / nsamples)

    effective_nsamples = nsamples // miniChunk
    effective_sr = sample_rate // miniChunk
    freqs = np.arange((effective_nsamples // 2) + 1, dtype=np.int32) / (effective_nsamples / effective_sr)

    return spec, freqs, output

if __name__ == '__main__':
    bpmGuesses = []

    wave_path = '/Users/davidgomez/Documents/Personal/Vengaboys_-_Boom_Boom_Boom_Boom.wav'
    nseconds = 20
    miniChunk = 128
    wave_reader = wave.open(wave_path, 'rb')

    sample_rate = wave_reader.getframerate()

    nframes = nseconds * sample_rate
    #print('nframes:', nframes, '\n')
    samples = wave_reader.readframes(nframes//2)
    # freqs = np.arange((nframes / 2) + 1, dtype=np.int32) / (nframes / sample_rate)



    a = np.fromstring(samples, dtype=np.int16)


    #spectrogram view
    # wave_reader.rewind()
    #
    # app = QtGui.QApplication([])
    # spectrogram_widget = SpectrogramWidget(spectrum_analyzer, 4000)
    #
    # # Add spectrum getter function to the widget
    # def get_spectrum():
    #     data = wave_reader.readframes(nframes)
    #
    #     if len(data) > 0:
    #         samples = np.fromstring(data, dtype=np.int16)
    #         print(len(samples))
    #         return spectrum_analyzer.get_spectrum(samples)
    #     else:
    #         return False
    #
    # spectrogram_widget.get_spectrum = get_spectrum
    # spectrogram_widget.update()
    # app.exec_()
    # wave_reader.close()


    b, freqs, output = detectBeat(a, sample_rate, miniChunk)
    bpm = list(freqs*60)
    b = list(b)
    first = 0
    last = 0
    for i in bpm:
        if i > 75 and first == 0:
            first = bpm.index(i)
        if i > 270 and last == 0:
            last = bpm.index(i)
            break

    bpm = bpm[first:last]
    b = b[first:last]
    tempo = bpm[b.index(max(b))]
    print(tempo)

    indexes = []

    beatChunk = 128
    for i in range(0, len(output)//beatChunk):
        section = output[i*beatChunk:(i*beatChunk)+beatChunk]
        subpeaks = peakutils.indexes(np.asarray(section), thres=.9, min_dist=100)
        for p in subpeaks:
            indexes.append(p+(i*beatChunk))

    #plt.figure()
    x = np.arange(0, len(output))
    print(indexes)
    # pplot(x, np.asarray(output), indexes)
    # plt.show()

    samplesPerBeat = int(1/((tempo/60)*(1/sample_rate)))
    print(samplesPerBeat)
    # plt.figure()
    # plt.plot(bpm, b)
    # plt.show()
    #
    # plt.figure()
    # plt.plot(output)
    #
    # for i in indexes:
    #     plt.axvline(i, color='r')
    #
    # plt.show()

    start = indexes[20]*miniChunk
    end = start + samplesPerBeat*4
    #plt.figure()
    #plt.plot(a)

    for i in indexes:
        if i == indexes[20]:
            print(i*miniChunk)
            print((i*miniChunk)+samplesPerBeat*4)
            plt.axvline(i*miniChunk, color='g')
            plt.axvline((i*miniChunk)+samplesPerBeat*16, color='g')
        else:
            plt.axvline(i*miniChunk, color='r')

    # plt.show()
    # maxCorrs = []
    # for i in range(1, 8):
    #     s1 = indexes[20]*miniChunk
    #     e1 = s1 + samplesPerBeat*4
    #     s2 = indexes[20+i]*miniChunk
    #     e2 = s2 + samplesPerBeat*4
    #     corr = np.correlate(np.asarray(a[s1:e1]), np.asarray(a[s2:e2]), 'same')

    #plt.figure()
    #plt.plot(corr)
    #plt.show()

    s1 = indexes[20]*miniChunk
    e1 = s1 + samplesPerBeat*4

    s2 = indexes[24]*miniChunk
    e2 = s2 + samplesPerBeat*4

    s3 = indexes[26]*miniChunk
    e3 = s3 + samplesPerBeat*4

    s4 = indexes[32]*miniChunk
    e4 = s4 + samplesPerBeat*4

    spectrum_analyzer = WindowedSTFT(len(a[s1:e1]), sample_rate,
            logscale=False)
    spectrum = spectrum_analyzer.get_spectrum(a[s1:e1])
    spectrum2 = spectrum_analyzer.get_spectrum(a[s2:e2])
    spectrum3 = spectrum_analyzer.get_spectrum(a[s3:e3])
    spectrum4 = spectrum_analyzer.get_spectrum(a[s4:e4])

    peaks = peakutils.indexes(spectrum, thres=.5)

    for i in range(0, len(spectrum)):
        if i in peaks:
            pass
        else:
            pass
            #spectrum[i] = 0

    x = np.arange(0, len(spectrum))
    plt.figure()
    plt.plot(x, spectrum, x, spectrum2, x, spectrum3, x, spectrum4, linewidth=1)
    plt.show()



    # CHUNK = 1024
    # p = pyaudio.PyAudio()
    # stream = p.open(format=p.get_format_from_width(wave_reader.getsampwidth()),
    #             channels=wave_reader.getnchannels(),
    #             rate=wave_reader.getframerate(),
    #             output=True)

    # start = indexes[7]*miniChunk
    # end = start + samplesPerBeat*4
    # stream.write(a[start:end])
    # time.sleep(0.5)
    #
    # start = indexes[20]*miniChunk
    # end = start + samplesPerBeat*16
    # stream.write(a[start:end])
    # time.sleep(0.5)

    # stop stream (4)
    # stream.stop_stream()
    # stream.close()

    # close PyAudio (5)
    # p.terminate()
