import sys
import time

import settings

from samplers.sampler_base import SamplerABC
from spectrum_analyzers.spectrum_analyzer_base import SpectrumAnalyzerABC
from vis_algs.vis_alg_base import VisualizationAlgorithmABC
from music_processors.bpm_detection import BPMDetector


class ToolStack(object):

    def __init__(self, sampler_class, spectrum_analyzer_class, vis_alg_class, renderer_class, bpm_detection_class):
        args = [sampler_class, spectrum_analyzer_class, vis_alg_class, bpm_detection_class]
        abcs = [SamplerABC, SpectrumAnalyzerABC, VisualizationAlgorithmABC, BPMDetector]
        assert all(issubclass(arg, t) for arg, t in zip(args, abcs))
        self.sampler_class = sampler_class
        self.spectrum_analyzer_class = spectrum_analyzer_class
        self.vis_alg_class = vis_alg_class
        self.renderer_class = renderer_class
        self.bpm_detection_class = bpm_detection_class

        self.pa_device_index = None
        self.sample_rate = 44100 * 2

    def start(self):

        self.sampler = self.sampler_class(self.pa_device_index, self.sample_rate)
        self.spectrum_analyzer = self.spectrum_analyzer_class(self.sampler.nsamples, self.sampler.rate)

        self.renderer = self.renderer_class()
        self.vis_alg = self.vis_alg_class(self.renderer.nlights)

        self.bpm_detector = self.bpm_detection_class(self.sampler.rate, self.sampler.nsamples, 100)


        def get_hex_arr():
            try:
                chunk = self.sampler.read_chunk()
                self.vis_alg.update_bpm(self.bpm_detector.detect_beat(chunk))

                return self.vis_alg.freq_to_hex(
                        self.spectrum_analyzer.get_spectrum(chunk))
            except:
                self.close()
                raise


        self.renderer.get_hex_arr = get_hex_arr
        self.renderer.start()

    def close(self):
        self.renderer.close()
        self.sampler.close()
