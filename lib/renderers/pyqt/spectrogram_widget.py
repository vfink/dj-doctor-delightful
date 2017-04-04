import utils

import numpy as np
import pyqtgraph as pg
import pyaudio
from PyQt5 import QtCore, QtGui

import matplotlib.pyplot as plt

import peakutils

class SpectrogramWidget(pg.PlotWidget):

    def __init__(self, spectrum_analyzer, max_freq=22000):
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

        self.freqs = freqs

        print('Max freq:', freqs[-1])
        print('Number of freqs:', len(freqs))
        print(self.freqs*60)

        # Make image
        self.img = pg.ImageItem()
        self.addItem(self.img)

        # Get chunk size and sample rate from spectrum analyzer
        nsamples = spectrum_analyzer.nsamples
        sample_rate = spectrum_analyzer.sample_rate

        # Instantiate image array
        self.img_array = np.zeros((150, self.crop_index))

        # Get colormap
        np_cmap = plt.get_cmap('viridis')
        cmap = utils.get_pyqt_cmap(np_cmap)
        lut = cmap.getLookupTable(0.0, 1.0, 256, alpha=False)

        # Set colormap
        self.img.setLookupTable(lut)
        self.img.setLevels([30,60])

        # Setup the correct scaling for y-axis
        yscale = (freqs[-1] / self.img_array.shape[1])*60
        self.img.scale(nsamples / sample_rate, yscale)

        self.setLabel('left', 'BPM', units='BPM')

        self.show()

    def update(self):

        spectrum = self.get_spectrum()[:self.crop_index]
        # print(spectrum)

        if type(spectrum) != bool:
            p10 = np.percentile(spectrum, 10)
            p90 = np.percentile(spectrum, 90)

            #print('p10:', p10, '\tp90:', p90, '\t\tmin:', spectrum.min(), '\tmax:', spectrum.max())
            # peaks = peakutils.indexes(spectrum, thres=.5)
            #
            # for i in range(0, len(spectrum)):
            #     if i in peaks:
            #         pass
            #     else:
            #         spectrum[i] = 0
            # count = 0
            # for i in self.freqs:
            #     print('BPM: ', i*60, '  Mag: ', spectrum[count])
            #     count = count + 1

            # Roll down one and replace leading edge with new data
            self.img_array = np.roll(self.img_array, -1, 0)
            self.img_array[-1:] = spectrum

            self.img.setImage(self.img_array, autoLevels=False)

            QtCore.QTimer.singleShot(1, self.update)  # QUICKLY repeat
        else:
            pass
