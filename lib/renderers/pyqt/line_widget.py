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

class LineWidget(pg.PlotWidget):

    def __init__(self, spectrum_analyzer):
        super(LineWidget, self).__init__()

        self.audioX = [0]
        self.audioY = [0]

        # Get chunk size and sample rate from spectrum analyzer
        self.freqs = spectrum_analyzer.get_freqs()
        #audioPlot = self.plotItem.plot(x=self.bpm, y=self.bpm)

        #graph two lines with same x
        # self.graph = self.plot(x=self.freqs, y=self.freqs, pen=(0,2))
        # self.graph2 = self.plot(x=self.freqs, y=self.freqs, pen=(1,2))
        #self.graph = self.plot(x=self.freqs, y=self.freqs, pen=(0,2))
        #self.graph2 = self.plot(x=self.freqs, y=self.freqs, pen=(1,2))

        self.power = np.arange(100)
        self.power_plot = self.plotItem.plot(x=np.arange(100), y=self.power)

        self.setLabel('left', 'Magnitude')
        self.setLabel('bottom', 'Freq', units='Hz')
        self.show()

    def update(self):

        spectrum = self.get_spectrum()
        # print("spectrum len: {0}".format(len(spectrum)))
        # print("freq len: {0}".format(len(self.freqs)))
        # p90 = np.percentile(spectrum, 90)
        # for i in range(0,len(spectrum)):
        #     if spectrum[i] < p90:
        #         spectrum[i] = 0

        # Roll down one and replace leading edge with new data

        #self.audioX[-1:] = range(self.audioX[len(self.audioX)-1], len(spectrum)+self.audioX[len(self.audioX)-1]+1)
        #self.audioY[-1:] = spectrum
        #

        #self.audioX = list(np.roll(self.audioX, self.nsamples))
        #self.audioY = list(np.roll(self.audioY, self.nsamples))

        #self.audioPlot.setData(self.audioY)

        #graph two lines with same x
        self.graph.setData(self.freqs,spectrum[0], pen=(0,2))
        self.graph2.setData(self.freqs,spectrum[1], pen=(1,2))

        QtCore.QTimer.singleShot(1, self.update)  # QUICKLY repeat

    def update2(self):

        spectrum = self.get_spectrum()
        # print("spectrum len: {0}".format(len(spectrum)))
        # print("freq len: {0}".format(len(self.freqs)))
        # p90 = np.percentile(spectrum, 90)
        # for i in range(0,len(spectrum)):
        #     if spectrum[i] < p90:
        #         spectrum[i] = 0

        # Roll down one and replace leading edge with new data

        #self.audioX[-1:] = range(self.audioX[len(self.audioX)-1], len(spectrum)+self.audioX[len(self.audioX)-1]+1)
        #self.audioY[-1:] = spectrum
        #

        #self.audioX = list(np.roll(self.audioX, self.nsamples))
        #self.audioY = list(np.roll(self.audioY, self.nsamples))

        self.audioPlot.setData(self.power)


        #graph two lines with same x
        # self.graph.setData(self.freqs,spectrum[0], pen=(0,2))
        # self.graph2.setData(self.freqs,spectrum[1], pen=(1,2))

        QtCore.QTimer.singleShot(1, self.update2)  # QUICKLY repeat

    def update_power(self):

        spectrum = self.get_spectrum()
        # print("spectrum len: {0}".format(len(spectrum)))
        # print("freq len: {0}".format(len(self.freqs)))
        # p90 = np.percentile(spectrum, 90)
        # for i in range(0,len(spectrum)):
        #     if spectrum[i] < p90:
        #         spectrum[i] = 0

        # Roll down one and replace leading edge with new data

        #self.audioX[-1:] = range(self.audioX[len(self.audioX)-1], len(spectrum)+self.audioX[len(self.audioX)-1]+1)
        #self.audioY[-1:] = spectrum
        #

        #self.audioX = list(np.roll(self.audioX, self.nsamples))
        #self.audioY = list(np.roll(self.audioY, self.nsamples))
        self.power = np.roll(self.power, 1)
        self.power[0] = spectrum

        #self.audioPlot.setData(self.audioY)
        self.power_plot.setData(self.power)

        #graph arbitrary x and y
        # self.graph.setData(spectrum[0],spectrum[1])

        #self.graph.setData(spectrum[0], spectrum[1], pen=(0,3))
        #self.graph2.setData(spectrum[0], spectrum[2], pen=(2,3))

        #graph two lines with same x
        # self.graph.setData(self.freqs,spectrum[0], pen=(0,2))
        # self.graph2.setData(self.freqs,spectrum[1], pen=(1,2))

        QtCore.QTimer.singleShot(1, self.update_power)  # QUICKLY repeat
