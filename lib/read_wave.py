import matplotlib.pyplot as plt
import scipy.signal as sig
from scipy.cluster.vq import vq, kmeans, whiten, kmeans2
import numpy as np
import peakutils
from peakutils.plot import plot as pplot
import wave
import math
import time
import struct
import utils

from renderers.pyqt.spectrogram_widget_single import SpectrogramWidget
from spectrum_analyzers.spectrum_analyzers import WindowedSTFT, CQT

import pyaudio
import soundfile as sf


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

def matplotSpectrogram(freq_data, sample_rate, nsamples, jumps=[], tagged_jumps='a'):
    beat_period = utils.bpm_to_period(138)
    sample_period = utils.samples_to_period(sample_rate, nsamples)

    t = np.arange(freq_data.shape[1])
    f = np.arange(freq_data.shape[0])

    z = freq_data[:-1, :-1]

    color_dict = {0:'r', 1:'g', 2:'y', 3:'b', 4:'c'}
    plt.pcolormesh(t, f, z)
    if tagged_jumps != 'a':
        for j,t in tagged_jumps:
            plt.axvline(x=j, linewidth=1, alpha=.5, color=color_dict[t])
    else:
        for j in jumps:
            plt.axvline(x=j, linewidth=1, alpha=.5, color='r')

    aud = plt.axvline(x=0, linewidth=1, color='g')
    plt.show()
    return aud

def updateSpectrogram(fig, aud_line):
    aud_line.set_xdata([aud_line.get_xdata()[0] + 1, aud_line.get_xdata()[1] + 1] )
    fig.canvas.draw()


if __name__ == '__main__':
    bpmGuesses = []

    wave_path = '/Users/davidgomez/Documents/Personal/Vengaboys_-_Boom_Boom_Boom_Boom.wav'
    start_delay = 20
    nseconds = 60
    miniChunk = 128
    wave_reader2 = wave.open(wave_path, 'r')
    wave_reader = sf.SoundFile(wave_path, 'rb')

    #sample_rate = wave_reader.getframerate()
    sample_rate = wave_reader.samplerate
    nsamples = 4096

    nframes = nseconds * sample_rate
    #print('nframes:', nframes, '\n')
    # samples = wave_reader.readframes(nframes//2)
    # print(len(samples))
    # freqs = np.arange((nframes / 2) + 1, dtype=np.int32) / (nframes / sample_rate)


    start_delay = int(start_delay * nsamples/sample_rate)
    wave_reader.seek(start_delay)
    #spectrogram view
    #wave_reader.rewind()

    app = QtGui.QApplication([])

    #spectrum_analyzer = WindowedSTFT(nsamples, sample_rate)
    spectrum_analyzer = CQT(nsamples, sample_rate, n_octaves=9, bins_per_octave=24)

    # print(nseconds)
    # print(nseconds // (nsamples/sample_rate))
    # print((nsamples/sample_rate))
    capture_chunks = int(nseconds // (nsamples/sample_rate))
    print("capture_chunks: {0}".format(capture_chunks))
    print("len freqs: {0}".format(len(spectrum_analyzer.freqs)))

    #array for all the frequency data in the song chunk
    #Each column is one chunk of samples, each row is a frequency
    full_spectrum = np.zeros((len(spectrum_analyzer.freqs), capture_chunks))
    full_spectrum_avg_power = np.zeros(capture_chunks)
    full_spectrum_avg_power_std = np.zeros(capture_chunks)
    spectrum_samples = []
    #Capture all nsamples frequency chunks
    for i in range(0, capture_chunks):
        #samples = wave_reader.readframes(nsamples)
        samples = wave_reader.read(frames = nsamples)[:,0]
        #samples = struct.unpack("<h", samples)
        spectrum = spectrum_analyzer.get_spectrum(samples)
        spectrum_samples.append(wave_reader2.readframes(nsamples))

        full_spectrum[:,i] = spectrum
        full_spectrum_avg_power[i] = np.average(spectrum)
        full_spectrum_avg_power_std[i] = np.std(spectrum)

    total_avg = np.average(full_spectrum_avg_power)
    sample_power_std = np.std(full_spectrum_avg_power)
    sample_power_diff_std = np.std(np.diff(full_spectrum_avg_power))


    # plt.figure(1)
    # plt.figure(2)
    # matplotSpectrogram(full_spectrum, sample_rate, nsamples)
    # plt.show()

    #compute average of each frequency bin
    avg_bins = np.average(full_spectrum, axis=1)
    freq_std = np.std(full_spectrum, axis=1)

    p90_bins = np.percentile(avg_bins, 95)
    avg_bins_ind = []
    for i in range(len(avg_bins)):
        if avg_bins[i] >= p90_bins:
            avg_bins_ind.append(i)
            # print("bigg: {0}".format(median_bins[i]))
        else:
            pass
            # print("smol: {0}".format(median_bins[i]))

    jumps = []
    beats = []
    for c in range(len(full_spectrum.T)):
        # full_spectrum[:,c] = full_spectrum[:,c] - avg_bins - full_spectrum_avg_power[c]
        if c > 0:
            tmp1 = full_spectrum_avg_power_std[c] - full_spectrum_avg_power[c]
            tmp2 = full_spectrum_avg_power_std[c-1] - full_spectrum_avg_power[c-1]
            if tmp1 - tmp2 > 1*sample_power_diff_std:
                jumps.append(c)
                beats.append(full_spectrum[:,c]-avg_bins)


        for f in range(len(full_spectrum[:,c])):
            if full_spectrum[f,c] - full_spectrum_avg_power[c] > full_spectrum_avg_power_std[c] and full_spectrum[f,c] - avg_bins[f] > freq_std[f]:
                full_spectrum[f,c] = full_spectrum[f,c] * 10



    beat_period = utils.bpm_to_period(138)
    sample_period = utils.samples_to_period(sample_rate, nsamples)

    xaxe = np.arange(0, 299)*sample_period/beat_period

    # fig = plt.figure()
    # plt.plot(xaxe,test_seg_sum[:,1],xaxe,test_seg_sum[:,2], xaxe,test_seg_sum[:,3], xaxe,test_seg_sum[:,4])
    # plt.show()

    curr_pos = 0
    plots = []
    def key_event(e):
        global curr_pos

        if e.key == "right":
            curr_pos = curr_pos + 1
        elif e.key == "left":
            curr_pos = curr_pos - 1
        else:
            return
        curr_pos = curr_pos % len(plots)

        ax.cla()
        ax.plot(plots[curr_pos][0], plots[curr_pos][1])
        fig.canvas.draw()

    # fig = plt.figure()
    # fig.canvas.mpl_connect('key_press_event', key_event)
    # ax = fig.add_subplot(111)
    # ax.plot(xaxe,test_seg_sum[:,0])


    # fig = plt.figure()
    # ax = fig.add_subplot(111)
    aud_line = matplotSpectrogram(full_spectrum, sample_rate, nsamples, jumps)

    # sums = np.ones(len(beats))
    # ind = 0
    # for i in beats:
    #     sums[ind] = sum(i)
    #     ind = ind + 1

    # beat_sum = zip(beats, sums)
    # beat_sum = sorted(beat_sum, key=lambda tup: tup[1])
    #
    # differences = np.ones(len(beat_sum))
    # percentile = 10
    # cur_bin =  np.percentile(sums, percentile)
    # cur_sum = beat_sum[0][1]
    # count = 0
    # for b,s in beat_sum:
    #     if s < cur_bin:
    #         differences[count] = sum((b - cur_sum))
    #         # sums[count] = cur_sum
    #     else:
    #         percentile = percentile + 10
    #         if percentile > 100:
    #             percentile = 100
    #         cur_bin =  np.percentile(sums, percentile)
    #         cur_sum = s
    #         differences[count] = sum((b - cur_sum))
    #         # sums[count] = cur_sum
    #
    #     count = count + 1

    # plt.scatter(sums, differences)
    # plt.show()

    full_spectrum = np.zeros((len(spectrum_analyzer.freqs), len(beats)))
    whitened = whiten(beats)
    centroid,labels = kmeans2(whitened,4)
    tagged_jumps = []
    test_samples = []
    c = 0
    s = 0
    for j in jumps:
        if labels[c] == 0:
            full_spectrum[:,s] = beats[c]
            test_samples.append(spectrum_samples[c])
            s = s + 1
        #tagged_jumps.append((j,labels[c]))
        c = c + 1

    c = 0
    for j in jumps:
        if labels[c] == 1:
            full_spectrum[:,s] = beats[c]
            test_samples.append(spectrum_samples[c])
            s = s + 1
        c = c + 1

    c = 0
    for j in jumps:
        if labels[c] == 2:
            full_spectrum[:,s] = beats[c]
            test_samples.append(spectrum_samples[c])
            s = s + 1
        c = c + 1

    c = 0
    for j in jumps:
        if labels[c] == 3:
            full_spectrum[:,s] = beats[c]
            test_samples.append(spectrum_samples[c])
            s = s + 1
        c = c + 1


    matplotSpectrogram(full_spectrum, sample_rate, nsamples)

    ts = 0

    def callback(in_data, frame_count, time_info, status):
        global ts
        data = test_samples[ts]
        ts = ts + 1
        return (data, pyaudio.paContinue)

    p = pyaudio.PyAudio()
    stream = p.open(format=p.get_format_from_width(wave_reader2.getsampwidth()),
                channels=wave_reader2.getnchannels(),
                rate=wave_reader2.getframerate(),
                output=True,
                stream_callback=callback)

    stream.start_stream()
    # wait for stream to finish (5)
    while stream.is_active():
        time.sleep(0.1)

    # stop stream (6)
    stream.stop_stream()
    stream.close()
    wave_reader2.close()
    # close PyAudio (7)
    p.terminate()

    peaks = []
    spectrogram_widget = SpectrogramWidget(spectrum_analyzer, full_spectrum, avg_bins, peaks, 22000)

    wave_reader.close()
    wave_reader = wave.open(wave_path, 'rb')

    p = pyaudio.PyAudio()
    spectrogram_widget.stream = p.open(format=p.get_format_from_width(wave_reader.getsampwidth()),
                channels=wave_reader.getnchannels(),
                rate=wave_reader.getframerate(),
                output=True)

    spectrogram_widget.wave_reader = wave_reader
    spectrogram_widget.wave_reader.setpos(start_delay)
    spectrogram_widget.line_count = 0
    # Add spectrum getter function to the widget
    def get_spectrum():
        spectrogram_widget.stream.write(spectrogram_widget.wave_reader.readframes(nsamples))
        spectrogram_widget.line_count = spectrogram_widget.line_count + 1
        return spectrogram_widget.line_count

    # while aud_line.get_xdata()[0] < full_spectrum.shape[1]:
    #     updateSpectrogram(fig, aud_line);
    #     stream.write(wave_reader.readframes(nsamples))

    # spectrogram_widget.get_spectrum = get_spectrum
    # spectrogram_widget.update()
    app.exec_()

    wave_reader.close()
    spectrogram_widget.wave_reader.close()


    # b, freqs, output = detectBeat(a, sample_rate, miniChunk)
    # bpm = list(freqs*60)
    # b = list(b)
    # first = 0
    # last = 0
    # for i in bpm:
    #     if i > 75 and first == 0:
    #         first = bpm.index(i)
    #     if i > 270 and last == 0:
    #         last = bpm.index(i)
    #         break
    #
    # bpm = bpm[first:last]
    # b = b[first:last]
    # tempo = bpm[b.index(max(b))]
    # print(tempo)
    #
    # indexes = []
    #
    # beatChunk = 128
    # for i in range(0, len(output)//beatChunk):
    #     section = output[i*beatChunk:(i*beatChunk)+beatChunk]
    #     subpeaks = peakutils.indexes(np.asarray(section), thres=.9, min_dist=100)
    #     for p in subpeaks:
    #         indexes.append(p+(i*beatChunk))
    #
    # #plt.figure()
    # x = np.arange(0, len(output))
    # print(indexes)
    # # pplot(x, np.asarray(output), indexes)
    # # plt.show()
    #
    # samplesPerBeat = int(1/((tempo/60)*(1/sample_rate)))
    # print(samplesPerBeat)
    # # plt.figure()
    # # plt.plot(bpm, b)
    # # plt.show()
    # #
    # # plt.figure()
    # # plt.plot(output)
    # #
    # # for i in indexes:
    # #     plt.axvline(i, color='r')
    # #
    # # plt.show()
    #
    # start = indexes[20]*miniChunk
    # end = start + samplesPerBeat*4
    # #plt.figure()
    # #plt.plot(a)
    #
    # for i in indexes:
    #     if i == indexes[20]:
    #         print(i*miniChunk)
    #         print((i*miniChunk)+samplesPerBeat*4)
    #         plt.axvline(i*miniChunk, color='g')
    #         plt.axvline((i*miniChunk)+samplesPerBeat*16, color='g')
    #     else:
    #         plt.axvline(i*miniChunk, color='r')
    #
    # # plt.show()
    # # maxCorrs = []
    # # for i in range(1, 8):
    # #     s1 = indexes[20]*miniChunk
    # #     e1 = s1 + samplesPerBeat*4
    # #     s2 = indexes[20+i]*miniChunk
    # #     e2 = s2 + samplesPerBeat*4
    # #     corr = np.correlate(np.asarray(a[s1:e1]), np.asarray(a[s2:e2]), 'same')
    #
    # #plt.figure()
    # #plt.plot(corr)
    # #plt.show()
    #
    # s1 = indexes[20]*miniChunk
    # e1 = s1 + samplesPerBeat*4
    #
    # s2 = indexes[24]*miniChunk
    # e2 = s2 + samplesPerBeat*4
    #
    # s3 = indexes[26]*miniChunk
    # e3 = s3 + samplesPerBeat*4
    #
    # s4 = indexes[32]*miniChunk
    # e4 = s4 + samplesPerBeat*4
    #
    # spectrum_analyzer = WindowedSTFT(len(a[s1:e1]), sample_rate,
    #         logscale=False)
    # spectrum = spectrum_analyzer.get_spectrum(a[s1:e1])
    # spectrum2 = spectrum_analyzer.get_spectrum(a[s2:e2])
    # spectrum3 = spectrum_analyzer.get_spectrum(a[s3:e3])
    # spectrum4 = spectrum_analyzer.get_spectrum(a[s4:e4])
    #
    # peaks = peakutils.indexes(spectrum, thres=.5)
    #
    # for i in range(0, len(spectrum)):
    #     if i in peaks:
    #         pass
    #     else:
    #         pass
    #         #spectrum[i] = 0
    #
    # x = np.arange(0, len(spectrum))
    # plt.figure()
    # plt.plot(x, spectrum, x, spectrum2, x, spectrum3, x, spectrum4, linewidth=1)
    # plt.show()



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
