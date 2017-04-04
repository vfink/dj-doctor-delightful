import numpy as np
import utils

class NoteFilter(object):
    def __init__(self, sample_rate, nsamples, start=24, end=96):
        self.note_freqs = utils.gen_note_freqs(start, end)
        self.sample_rate = sample_rate
        self.nsamples = nsamples
        self.freqs = np.arange((nsamples / 2) + 1, dtype=np.int32) / (nsamples / sample_rate)

        #create a closeness array, each index contains a number 0 - 1 representing
        #how close to a musical note a frequency bin is
        p_thres = 1
        closeness = []
        for f in self.freqs:
            closest_bin = p_thres
            for nf in self.note_freqs:
                pdiff = (nf - f)/nf * 100

                if abs(pdiff) < closest_bin:
                    closest_bin = abs(pdiff)

                #if pdiff starts to exceed threshold, save closest_bin scaled
                #0-1 in the closeness array and then break nf loop
                if p_thres < pdiff:
                    break

            if closest_bin >= p_thres:
                closeness.append(0)
            else:
                #print("f={0}, nf={1}, pdiff={2}".format(f, nf, closest_bin))
                closeness.append((p_thres - closest_bin)/p_thres)

        self.closeness = closeness

        self.farness = []
        for c in self.closeness:
            self.farness.append(1-c)

    #suppress frequency bins corresponding to musical note frequencies
    def suppress_notes(self, samples):
        s = zip(self.farness, samples)
        new_s = []
        for i in s:
            new_s.append(i[0]*i[1])

        return new_s

    #enchance frequency bins corresponding to musical note frequencies
    def enhance_notes(self, samples):
        s = zip(self.closeness, samples)
        new_s = []
        for i in s:
            # print("close={0}, sample={1}, mult={2}".format(i[0], i[1], i[1]*i[0]))
            new_s.append(i[0]*i[1])
        #print(new_s)
        return new_s
