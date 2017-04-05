import numpy as np
import math

from PyQt5.QtWidgets import (QApplication, QDesktopWidget, QWidget, QMainWindow,
    QAction, qApp, QMenuBar, QMessageBox, QFileDialog, QPushButton, QLabel,
    QHBoxLayout, QVBoxLayout, QTextEdit, QSizePolicy)

from PyQt5 import QtCore, QtGui

import pyqtgraph as pg

import utils

import pyaudio
import peakutils
import time

import matplotlib.pyplot as plt

class BPMDetector():

    def __init__(self, sampleRate, nsamples, sampleMultiplier):
        self.rate = sampleRate
        self.avgEnergy = 0
        self.energySamples = [1]
        self.sampleWindow = 100
        self.variance = 0
        self.lastPeak = 0
        self.sampleCount = 0
        self.C = 0;
        self.tempoDict = {};
        for i in range(80, 181, 5):
            self.tempoDict[i] = 0
        self.tempoSampleCount = 0

        self.nSamples = nsamples
        self.miniChunk = 256
        self.sampleMultiplier = sampleMultiplier
        self.effectiveNSamples = (nsamples*sampleMultiplier)//self.miniChunk
        self.effectiveRate = sampleRate//self.miniChunk
        self.sample_buffer = []

        freqs = np.arange((self.effectiveNSamples // 2) + 1, dtype=np.int32) / (self.effectiveNSamples / self.effectiveRate)
        bpm = list(freqs*60)
        print("BPM Resolution: {0}".format(bpm[1]))

        first = 0
        last = 0
        for i in bpm:
            if i > 80 and first == 0:
                first = bpm.index(i)
            if i > 160 and last == 0:
                last = bpm.index(i)
                break

        self.bpm = bpm[first:last]
        print("#BPMs: {0}".format(len(self.bpm)))
        self.first = first
        self.last = last

        self.tempo = 120

        # self.k_list = []
        # for i in self.bpm:
        #     self.k_list.append(self.bpm_to_k(i))


    def update(self, sample):
        sampleEnergy = 0
        for i in sample:
            sampleEnergy = sampleEnergy + i**2

        #print("sampleEnergy: {0}".format(sampleEnergy))
        if len(self.energySamples) < self.sampleWindow:
            self.energySamples.insert(0, sampleEnergy)
        else:
            self.energySamples.insert(0, sampleEnergy)
            self.energySamples.pop()

        if(self.energySamples[0] < self.energySamples[1] and self.energySamples[1] > self.energySamples[2]):
            sampleDist = self.sampleCount/(self.rate/2)
            tempo = (1/sampleDist)/60
            self.sampleCount = 1
        else:
            tempo = None
            self.sampleCount = self.sampleCount + 1

        if tempo != None:
            roundTempo = self.roundToBase(tempo)

            if roundTempo in self.tempoDict:
                if roundTempo/2 in self.tempoDict:
                    self.tempoDict[roundTempo/2] = self.tempoDict[roundTempo/2] + 1
                else:
                    self.tempoDict[roundTempo] = self.tempoDict[roundTempo] + 2
            else:
                if roundTempo/2 in self.tempoDict:
                    self.tempoDict[roundTempo/2] = self.tempoDict[roundTempo/2] + 1

            #print(self.tempoDict)
            print(roundTempo)
            maximum = max(self.tempoDict, key=self.tempoDict.get)
            print(maximum, self.tempoDict[maximum])

        self.tempoSampleCount = self.tempoSampleCount + 1;

        if self.tempoSampleCount > 20:
            self.tempoSampleCount = 0
            print("MINUS")
            for k,v in self.tempoDict.items():
                if self.tempoDict[k] > 0:
                    self.tempoDict[k] = self.tempoDict[k] - 1

        self.avgEnergy = sum(self.energySamples)/len(self.energySamples)

    def roundToBase(self, x, base=5):
        return int(base * round(float(x)/base))

    def getAverage(self):
        return self.avgEnergy

    def getVariance(self):
        return self.variance

    def getC(self):
        return self.C

    def differences(self, list):
        diffList = []
        for i in range(1, len(list)):
            diffList.append(list[i] - list[i-1])

        return diffList

    def norm(self, l):
        s = 0
        for i in l:
            s = s + abs(i)**2

        return math.sqrt(s)

    def updateFFTBPM(self, sampleChunk):
        miniSample = []
        miniChunk = self.miniChunk
        output = []
        for i in range(0, len(sampleChunk)):
            if len(miniSample) == miniChunk:
                diff = self.differences(miniSample)
                norm = self.norm(diff)
                output.append(norm)
                miniSample = [sampleChunk[i]]
            else:
                miniSample.append(sampleChunk[i])

        if len(miniSample) == miniChunk:
            diff = self.differences(miniSample)
            norm = self.norm(diff)
            output.append(norm)

        return output

    def updateAutoBPM(self, sampleChunk):
        print("auto")
        return list(np.correlate(sampleChunk, sampleChunk, "same"))

    def setBigChunk(self, bigChunk):
        self.bigChunk = bigChunk

    def consolidate(self, delay, sampler):
        s = []
        for i in range(0, delay):
            del self.bigChunk[0:self.nSamples]
            self.bigChunk = self.bigChunk + list(sampler.read_chunk())

        return self.bigChunk

    def detect_beat(self, inc_samples):
        # START = time.clock()
        chunked_samples = np.split(np.asarray(inc_samples), len(inc_samples)/self.miniChunk)
        for i in chunked_samples:
            diff = np.diff(i)
            n = self.norm(diff)
            self.sample_buffer.append(n)

        #self.sample_buffer.append(inc_samples)
        if len(self.sample_buffer) <= self.effectiveNSamples:
            return [0]*len(self.bpm)
        else:
            del self.sample_buffer[0:self.nSamples//self.miniChunk]

        # print("diffs: {0}".format(time.clock()-START))
        sample_rate = self.rate
        miniChunk = self.miniChunk
        nsamples = self.effectiveNSamples
        miniSample = []
        #miniChunk = 128
        #win = np.hanning(nsamples//miniChunk)
        win = np.hanning(self.effectiveNSamples)
        #output = []
        START = time.clock()
        # for i in range(0, len(samples)):
        #     if len(miniSample) == miniChunk:
        #         #diff = self.differences(miniSample)
        #         diff = np.diff(miniSample)
        #         n = self.norm(diff)
        #         output.append(n)
        #         miniSample = [samples[i]]
        #     else:
        #         miniSample.append(samples[i])
        #
        # if len(miniSample) == miniChunk:
        #     #diff = self.differences(miniSample)
        #     diff = np.diff(miniSample)
        #     n = self.norm(diff)
        #     output.append(n)

        # print('nsamples:{0}\nchunksize:{1}\n {0} // {1} = {2}'.format(
        #     nsamples, miniChunk, nsamples // miniChunk))
        #
        # print('len(output){0}'.format(len(output)))

        # START = time.clock()
        spec = abs(np.fft.rfft(self.sample_buffer * win) / self.effectiveNSamples)
        # print("fft: {0}".format(time.clock()-START))
        #spec = output

        # sample_input = output * win
        # spec = []
        # for i in self.k_list:
        #     spec.append(self.single_fft(sample_input, i))

        b = list(spec)
        b = b[self.first:self.last]

        # blep = zip(self.bpm, b)
        #
        # blep = sorted(blep, key=lambda tup: tup[1])
        # print("#1#")
        # count = 0
        # for i in blep:
        #     print("BPM: {0}, Powah: {1}".format(int(i[0]), i[1]))
        #     count = count+1
        # print("###")
        #

        subpeaks = peakutils.indexes(np.asarray(b), thres=.6, min_dist=2)
        # for i in subpeaks:
        #     print(self.bpm[i])

        top_bpm = []
        top_b = []
        for i in subpeaks:
            top_bpm.append(self.bpm[i])
            top_b.append(b[i])

        if sum(top_b) != 0:
            avg_tempo = np.average(top_bpm, weights=top_b)
        else:
            avg_tempo = self.tempo

        for i in range(len(b)):
            far_from_calc = abs(self.tempo-self.bpm[i])/250.0
            far_from_120 = abs(120-self.bpm[i])/250.0
            far_from_instant = abs(avg_tempo-self.bpm[i])/1000.0
            b[i] = b[i] * (1 - far_from_calc - far_from_120 - far_from_instant)


        # subpeaks = peakutils.indexes(np.asarray(b), thres=.6, min_dist=2)
        # print("###")
        # for i in subpeaks:
        #     print(self.bpm[i])
        #
        # print("###")

        # top_bpm = []
        # top_b = []
        # for i in subpeaks:
        #     top_bpm.append(self.bpm[i])
        #     top_b.append(b[i])
        #
        # avg_tempo = np.average(top_bpm, weights=top_b)
        # print("Avg Tempo: {0}".format(avg_tempo))

        tempo = self.bpm[b.index(max(b))]

        blep = zip(self.bpm, b)

        blep = sorted(blep, key=lambda tup: tup[1])
        # print("#2#")
        # count = 0
        # for i in blep:
        #     print("BPM: {0}, Powah: {1}".format(int(i[0]), i[1]))
        #     count = count+1
        # print("###")

        self.tempo = tempo

        return b

    def single_fft(self, samples, k):
        n = 0
        X = 0
        for x_n in samples:
            X = X + (x_n * np.exp((-1j*2*np.pi*k*n)/self.effectiveNSamples))
            n = n + 1

        return abs(X/self.effectiveNSamples)

    def bpm_to_k(self, bpm):
        freq = 1.0/(bpm/60.0)
        return int(freq*self.effectiveNSamples/self.effectiveRate)




class BPMWidget(pg.PlotWidget):

    def __init__(self, spectrum_analyzer, BPMDetector):
        super(BPMWidget, self).__init__()

        self.audioX = [0]
        self.audioY = [0]

        # Get chunk size and sample rate from spectrum analyzer
        self.nsamples = spectrum_analyzer.nsamples
        sample_rate = spectrum_analyzer.sample_rate
        self.bpm = BPMDetector.bpm
        #audioPlot = self.plotItem.plot(x=self.bpm, y=self.bpm)

        self.graph = self.plot(x=self.bpm, y=self.bpm)

        self.setLabel('left', 'Magnitude')
        self.setLabel('bottom', 'Tempo', units='BPM')
        self.show()

    def update(self):

        spectrum = self.get_spectrum()
        p90 = np.percentile(spectrum, 90)
        for i in range(0,len(spectrum)):
            if spectrum[i] < p90:
                spectrum[i] = 0

        # Roll down one and replace leading edge with new data

        #self.audioX[-1:] = range(self.audioX[len(self.audioX)-1], len(spectrum)+self.audioX[len(self.audioX)-1]+1)
        #self.audioY[-1:] = spectrum
        #

        #self.audioX = list(np.roll(self.audioX, self.nsamples))
        #self.audioY = list(np.roll(self.audioY, self.nsamples))

        #self.audioPlot.setData(self.audioY)

        self.graph.setData(self.bpm,spectrum)

        QtCore.QTimer.singleShot(1, self.update)  # QUICKLY repeat

    def updateGraph(self, samples):
        print(len(samples))
        spectrum = self.get_spectrum(samples)
        self.graph.setData(self.bpm,spectrum)
        print("update")
        QtCore.QTimer.singleShot(1, self.asshole)

    def asshole(self):
        pass


class BPMWidgetAsync(pg.PlotWidget):

    read_collected = QtCore.pyqtSignal(np.ndarray)

    def __init__(self, spectrum_analyzer,):
        super(BPMWidgetAsync, self).__init__()

        self.audioX = [0]
        self.audioY = [0]

        # Get chunk size and sample rate from spectrum analyzer
        self.nsamples = spectrum_analyzer.nsamples
        sample_rate = spectrum_analyzer.sample_rate
        self.bpm = spectrum_analyzer.get_freqs()*60
        #audioPlot = self.plotItem.plot(x=self.bpm, y=self.bpm)

        self.graph = self.plot(x=self.bpm, y=self.bpm)

        self.setLabel('left', 'Magnitude')
        self.setLabel('bottom', 'Tempo', units='BPM')
        self.show()

    def update(self, chunk):
        spectrum = self.get_spectrum(chunk)

        # p90 = np.percentile(spectrum, 90)
        # for i in range(0,len(spectrum)):
        #     if spectrum[i] < p90:
        #         spectrum[i] = 0

        bpm = list(self.bpm)
        b = list(spectrum)
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

        # Roll down one and replace leading edge with new data

        #self.audioX[-1:] = range(self.audioX[len(self.audioX)-1], len(spectrum)+self.audioX[len(self.audioX)-1]+1)
        #self.audioY[-1:] = spectrum
        #

        #self.audioX = list(np.roll(self.audioX, self.nsamples))
        #self.audioY = list(np.roll(self.audioY, self.nsamples))

        #self.audioPlot.setData(self.audioY)

        self.graph.setData(bpm,b)

        #QtCore.QTimer.singleShot(1, self.update)  # QUICKLY repeat
