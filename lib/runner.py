from factory_sequential import ToolStack
from renderers.pyqt.light_sim import QTLightSim, QTLightSimStrings
from renderers.teensy.light_sender import LightSender
from samplers.pyaudio_sampler import PyAudioSampler
from spectrum_analyzers.spectrum_analyzers import WindowedSTFT, CQT
from vis_algs.effect_based_string import Visualizer
from music_processors.bpm_detection import BPMDetector

if __name__ == '__main__':
    app = ToolStack(
            PyAudioSampler,                     # Audio sampler
            CQT,						# Spectrum analyzer
            Visualizer,   						# Visualization algorithm
            LightSender,                        # Light simulator / Light serial sender
            BPMDetector)                        # BPM Dectector
    app.start()
