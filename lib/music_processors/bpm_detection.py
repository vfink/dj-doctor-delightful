import numpy as np
import math

from PyQt5.QtWidgets import (QApplication, QDesktopWidget, QWidget, QMainWindow,
    QAction, qApp, QMenuBar, QMessageBox, QFileDialog, QPushButton, QLabel,
    QHBoxLayout, QVBoxLayout, QTextEdit, QSizePolicy)

from PyQt5 import QtCore, QtGui

import pyqtgraph as pg

import utils

import pyaudio

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
        self.miniChunk = 128
        self.effectiveNSamples = (nsamples*sampleMultiplier)/self.miniChunk
        self.effectiveRate = sampleRate/self.miniChunk

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





class BPMWidget(pg.PlotWidget):

    def __init__(self, spectrum_analyzer,):
        super(BPMWidget, self).__init__()

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
