from collections import deque
from scipy.io.wavfile import write

import numpy as np
import tensorflow as tf
import wave
import pyaudio
import time

from listener import DeviceListener, ms2samples

filename = "SPOTTER_TEST.wav"

CHUNK=4096



class Keyword:
    def __init__(self, name, window_size, score_threshold):
        self.name = name

        self.window_size = window_size
        self.window = deque(maxlen=window_size)
        self.score_threshold = score_threshold


    def update(self, score):
        self.window.append(score)


    @property
    def activated(self):
        activation = False
        print(np.median(self.window))
        if np.median(self.window) >= self.score_threshold:
            activation = True
            self.window.clear()

        return activation


class Spotter:
    def __init__(self, sample_rate, plotter=None):
        self.sample_rate = sample_rate
        self.plotter = plotter


    def _burn_in(self, model, block_size_samples):
        arr = np.random.rand(block_size_samples)
        model(self.to_tensor(arr))


    def spot(self, *args, **kwargs):
        raise NotImplementedError


    @staticmethod
    def get_activation_times(timeline, block_stride):
        timeline = np.where(timeline)[0] * block_stride
        return list(timeline)


    @staticmethod
    def get_activation_intervals(timeline, block_stride, block_size):
        timeline.append(False)
        intervals = []

        start = end = 0
        prev = False
        for i, pred in enumerate(timeline):
            if pred and not prev:
                start = i * block_stride
            elif not pred and prev:
                end = i * block_stride + block_size
                intervals.append([start, end])
                start = end = 0

            prev = pred

        return intervals


    def _spot_on_stream(self, model, keywords, stream, show):
        activations = {key.name: [] for key in keywords.keys()}
        scores = {key.name: [] for key in keywords.keys()}
        
        data = np.ndarray((0,), dtype = np.float32)
        time_start = time.time()

        for i, block in enumerate(stream):
            data = np.concatenate((data,block))
            block = self.to_tensor(block)
            prediction = model(block, training=False)[0].numpy()

            _score_dict = {key.name: 0 for key in keywords.keys()}
            for key, value in keywords.items():
                score = prediction[value]

                key.update(score)
                activations[key.name].append(key.activated)
                
                print(activations[key.name][-1])
                
                if activations[key.name][-1] is True:
                    print(activations[key.name][-1])
                    write(filename, 16000, data)
                    return True
                
                #if(time.time() - time_start > 30):
                 #   write(filename, 16000, data)
                  #  return False
                
                scores[key.name].append(round(score, 2))

                if show and self.plotter is not None:
                    _score_dict[key.name] = score
                    self.plotter.plot(_score_dict)

        if show and self.plotter is not None:
            self.plotter.plot(None)

        #return activations, scores
        return False


    @staticmethod
    def to_tensor(audio):
        tensor = tf.cast(audio[None, :], tf.float32)
        return tensor
    

            
