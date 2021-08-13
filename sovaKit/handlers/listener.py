import sys
sys.path.append("../main/")

import queue
from functools import partial

import soundfile
from array import array
from sys import byteorder
import threading
import asyncio
import time
import struct

import numpy as np
import pyaudio
import wave
import webrtcvad

import params


_uint16 = 2 ** 15

filename = "LISTENER_TEST.wav"
SHORT_NORMALIZE = (1.0/32768.0)
data = []


class Listener:
    def __init__(self, sample_rate):
        self.sample_rate = sample_rate
        self.channels = params.RESPEAKER_CHANNELS
        self.audio_type = None
        self._receiver = []


    def listen(self, block_size, block_stride, in_background=True):
        assert block_stride <= block_size

        block_size_samples = ms2samples(block_size, self.sample_rate)
        block_stride_samples = ms2samples(block_stride, self.sample_rate)

        start_new_thread(self._send_signal, (self._receiver, ))

        generator = self.generate_samples(block_size_samples, block_stride_samples, in_background)

        return generator


    def generate_samples(self, block_size_samples, block_stride_samples, in_background):
        raise NotImplementedError


    @staticmethod
    def _send_signal(receiver):
        signal = input()
        receiver.append(signal)


class DeviceListener(Listener):
    def __init__(self, sample_rate):
        super(DeviceListener, self).__init__(sample_rate)
        
        self.device_idx = params.RESPEAKER_INDEX

        self.chunk_size = 480

        self.audio_type = pyaudio.paInt16

        self.interface = pyaudio.PyAudio()
        
        self.buffer = queue.Queue()
        
        self.stream = self.interface.open(
            format=self.audio_type, channels=self.channels, rate=self.sample_rate,
            input=True, input_device_index=self.device_idx, frames_per_buffer=self.chunk_size,
            stream_callback=self._device_callback,
        )
        print("micro is ready")


    def __enter__(self):
        self.init_interface()
        return self


    def __exit__(self, type, val, traceback):
        print("terminate for choice")
        #self.terminate()


    def init_interface(self):
        if self.interface is None:
            self.interface = pyaudio.PyAudio()
      


    def terminate(self):
        if self.interface is not None:
            self.interface.terminate()

        

    def generate_samples(self, block_size_samples, block_stride_samples, in_background=True):
        buffer = []

        stream = self._listen_device()
        
        vad = webrtcvad.Vad(1)
        
        is_speech = True
        
        for chunk in stream:                     
            if(is_speech):
                accumulate = len(buffer) < block_size_samples
                if accumulate:
                    buffer = chunk if not isinstance(buffer, np.ndarray) else np.concatenate((buffer, chunk))
                    continue
                block = buffer[:block_size_samples]
                yield block
                    
                buffer = buffer[block_size_samples:]
                

    def _listen_device(self):
        
        wf = wave.open(filename, 'wb')
        wf.setnchannels(self.channels)
        wf.setsampwidth(self.interface.get_sample_size(self.audio_type))
        wf.setframerate(self.sample_rate)
        
        buffer = self._listen_device_buffer()

        try:
            for block in buffer:
                yield block
        except Exception as e:
            print(e)
        finally:
            self._receiver = []


    def _listen_device_buffer(self):
        while not self._receiver:
            try:
                chunk = array("h", self.buffer.get(timeout=2))
            except queue.Empty:
                print("break")
                break

            if byteorder == "big":
                chunk.byteswap()

            yield np.array(chunk, dtype=np.float32) / _uint16
            
    def _listen_device_buffer_2(self):            
        while not self._receiver:
            try:
                chunk = array("h", self.buffer.get(timeout=2))
                print("queue size: ", self.buffer.qsize())
            except queue.Empty:
                print("break")
                break

            if byteorder == "big":
                chunk.byteswap()

            yield chunk.tobytes()


    def _device_callback(self, in_data, *_):
        self.buffer.put(in_data)
        return None, pyaudio.paContinue
    
    
    async def stream_mic(self):
        buffer = self._listen_device_buffer_2()
        
        try:
            for block in buffer:
                yield block
        except Exception as e:
            print(e)
        finally:
            print("ending")
            

    
def start_new_thread(func, args):
    thread = threading.Thread(target=func, args=args, daemon=True)
    thread.start()


def ms2samples(duration_ms, sample_rate):
    return int(sample_rate / 1e3 * duration_ms)

def get_RMS(block):
    count = len(block)
    return np.sqrt(sum([(block[i])**2 for i in range(count)])/count)

def conv(frames):
    a = np.fromstring(frames, dtype=np.int16)
    y = list(range(a.size))
    del y[1::2]
    a = np.delete(a, y)
    return a.tobytes()
    #print(y)

def get_rms_bytes(block):
    count = len(block) // 2
    format = "{}h".format(count)
    shorts = struct.unpack(format, block)
    sum_squares = 0
    for sample in shorts:
        n = sample * SHORT_NORMALIZE
        sum_squares += n*n
    return (sum_squares / count) ** 0.5
