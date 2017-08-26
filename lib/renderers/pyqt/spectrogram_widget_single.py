import utils

import numpy as np
import pyqtgraph as pg
import pyaudio
from PyQt5 import QtCore, QtGui

import matplotlib.pyplot as plt

import peakutils

class SpectrogramWidget(pg.PlotWidget):

    def __init__(self, spectrum_analyzer, spectrum, median_bins, peaks, max_freq=22000):
        super(SpectrogramWidget, self).__init__()

        self.max_freq = max_freq

        freqs = spectrum_analyzer.get_freqs()

        nyquist_freq = freqs[-1]
        print('Nyquist freq:', nyquist_freq)
        print('Raw number of freqs:', len(freqs))

        self.crop_index = len(freqs)
        if max_freq < nyquist_freq:
            self.crop_index = int(len(freqs) * max_freq / nyquist_freq)
            freqs = freqs[:self.crop_index]
        #print('Crop Freq: {0}'.format(spectrum_analyzer.freq_dict[self.crop_index]))
        self.freqs = freqs

        print('Max freq:', freqs[-1])
        print('Number of freqs:', len(freqs))

        # Make image
        self.img = pg.ImageItem()
        self.addItem(self.img)

        # Get chunk size and sample rate from spectrum analyzer
        self.nsamples = spectrum_analyzer.nsamples
        sample_rate = spectrum_analyzer.sample_rate

        # Instantiate image array
        #self.spectrum = spectrum[:self.crop_index]
        self.freq_ind = 0
        self.chunk_ind = 1
        self.img_array = np.zeros((spectrum.shape[self.chunk_ind], self.crop_index))

        # Get colormap
        np_cmap = plt.get_cmap('viridis')
        cmap = utils.get_pyqt_cmap(np_cmap)
        lut = cmap.getLookupTable(0.0, 1.0, 256, alpha=False)

        # Set colormap
        self.img.setLookupTable(lut)
        lowest = min(spectrum.flatten())
        highest = max(spectrum.flatten())

        print(highest)
        print(lowest)
        p10 = np.percentile(spectrum.flatten(), 50)
        p90 = np.percentile(spectrum.flatten(), 99)
        self.img.setLevels([p10,p90])

        # Setup the correct scaling for y-axis
        yscale = (freqs[-1] / self.img_array.shape[1])
        self.img.scale(self.nsamples / sample_rate, yscale)


        self.setLabel('left', 'Frequency', units='Hz')

        print(self.img_array[0,:].shape)
        print(spectrum[:,0].shape)

        for i in range(0, spectrum.shape[self.chunk_ind]):
            self.img_array[i,:] = spectrum[0:self.crop_index,i]
            self.img.setImage(self.img_array, autoLevels=False)

        # Coloring Highest median freq bins
        p90_bins = np.percentile(median_bins, 90)
        # for i in range(self.crop_index):
        #     self.img_array[:,i] = self.img_array[:,i] - median_bins[i]
            # if median_bins[i] >= p90_bins:
            #     for c in range(spectrum.shape[self.chunk_ind]):
            #         if self.img_array[c,i] >= p90:
            #             self.img_array[c,i] = self.img_array[c,i]
            #         else:
            #             self.img_array[c,i] = .2
            # else:
            #     for c in range(spectrum.shape[self.chunk_ind]):
            #         self.img_array[c,i] = self.img_array[c,i]*.25


        self.last_spectrum = self.img_array[i,:]
        self.show()

    def update(self):

        pos = self.get_spectrum()
        # print(spectrum)
        if pos > 0:
            self.img_array[(pos-1),:] = np.copy(self.last_spectrum)

        self.last_spectrum = np.copy(self.img_array[pos,:])

        self.img_array[pos,:] = np.ones(self.img_array.shape[1]) * 10

        self.img.setImage(self.img_array, autoLevels=False)

        QtCore.QTimer.singleShot(1, self.update)  # QUICKLY repeat
