import sys
sys.path.append("../handlers/")
sys.path.append("../models/")

import warnings

warnings.filterwarnings('ignore')

import params

import os
import time
import json
import requests
import pyaudio
import pygame
import wave
import numpy as np
import webrtcvad
import struct
import queue
#from tts import test_tts

from apa102 import APA102
from gpiozero import LED


from scipy.io.wavfile import write

from base64 import b64decode


#import RPi.GPIO as GPIO
#from gpiozero import Button

import websockets
import asyncio, argparse
from yarl import URL
from aiohttp import ClientSession


if params.KWS == r"sova":
    from collections import OrderedDict, deque
    from copy import deepcopy
    from tensorflow import keras
    from listener import DeviceListener, ms2samples
    from spotter import Spotter, Keyword


WAVE_OUTPUT_FILENAME = "output.wav"
WAVE_INPUT_FILENAME = "result.wav"
SHORT_NORMALIZE = (1.0/32768.0)
THRESHOLD = 0.005

        
def conv(frames):
    a = np.fromstring(frames, dtype=np.int16)
    y = list(range(a.size))
    del y[1::2]
    a = np.delete(a, y)
    return a.tobytes()
    #print(y)

        
async def client_ws(sample_rate, address, file, a):

    #960 байт
    s_chunk = b'\x00\x00'*480
    #a.device_listener.buffer.queue.clear()
    ws_data = []
    vad = webrtcvad.Vad(3)
    speech_start = False
    prev_pharse = ''
    
    a.set_LED(0,0,3,0)
    a.set_LED(1,0,0,0)
    a.set_LED(2,0,0,0)

    with a.device_listener as listener:
        buffer = listener.stream_mic()
        listener.buffer.queue.clear()
        time1=time.time()
        time_session = time.time()
        print("STREAM!")
        scheme = "wss" if URL("//" + address).port == 443 else "ws"
        
        async with ClientSession() as session:
            url = str(URL("%s://%s" % (scheme, address)).with_query(sample_rate=params.WS_RATE))
            print("This?")
            async with session.ws_connect(url) as ws:
                print("Connected ...")
    
                await ws.send_json({
                    "auth_type": params.WS_auth_type,
                    "auth_token": params.WS_auth_token,
                    "sample_rate": params.WS_RATE
                })
    
                assert (await ws.receive_json())["response"] == 0
                
                #на случай долгого подключения к сокетам можно очищать здесь
                #listener.buffer.queue.clear()
                
                async for frames in buffer:
                
                    #if(listener.buffer.qsize()<50):
                    
                    is_speech = vad.is_speech(frames, params.RESPEAKER_RATE)
                    
                    print("speech: ", is_speech)
                    
                    if(is_speech):       
                        a.set_LED(1,0,3,0)
                        a.set_LED(2,0,3,0)
                        ws_data.append(conv(frames))
                    else:
                        a.set_LED(1,0,0,0)
                        a.set_LED(2,0,0,0)
                        ws_data.append(s_chunk)
                        
                    
                    if(listener.buffer.qsize() > 1):
                            continue
                            
                    
                        
                    await ws.send_bytes(b''.join(ws_data))
                    text = await ws.receive_str()
                    print("data sent", len(ws_data))
                    ws_data.clear()                                       
                        
                    if(time.time()-time1-10>0):         
                        print("Noo")
                        return 0
                    
                    if (len(json.loads(text)['results']) > 0  and json.loads(text)['results'][0]['event'] == 3):
                        speech_start = True
                        prev_pharse = json.loads(text)['results'][0]['alternatives'][0]['text']
                        print(json.loads(text)['results'][0]['alternatives'][0]['text'], json.loads(text)['results'][0]['final'])
                        time1=time.time()
                        
                        #если final == False
                        error = listener.buffer.qsize()
                        if error > 50:
                            error = error - 50
                            listener.buffer.queue=queue.deque(list(listener.buffer.queue)[error:])
                            
                        if json.loads(text)['results'][0]['final'] == True:
                            await a.init(json.loads(text)['results'][0]['alternatives'][0]['text'])
                            return 1
                            
                        print(speech_start, prev_pharse)
                            
                    if(speech_start):
                        if(time.time()-time_session - 5 > 0):
                            print(prev_pharse)                             
                            await a.init(prev_pharse)
                            print("sent prev phrase")
                            return 1

                            
                await ws.send_str("/EOP")
                output = await ws.receive_json()
    
                for result in output["results"]:
                    print(result)
                    


class Recorder:
    def __init__(self, sample_rate):                
        
        if params.KWS == r"sova":
            self.model = keras.models.load_model(params.model_path, compile = False)
            print("model loaded")
            
        self.device_listener = DeviceListener(sample_rate)
        
        self.dev = APA102(3, 10, 11, 8)
        self.time_next=time.time()

    def set_LED(self, N, R, G, B):
        self.dev.set_pixel(N,R,G,B)
        self.dev.show()

    def kws_check(self):  
        print("Start kws_check")    
        spotter = Spotter(sample_rate = 16000)
        sova = Keyword("sova", params.WINDOW, params.THRESHOLD)
        keywords = OrderedDict({sova: 2})
        spotter._burn_in(self.model, ms2samples(params.BLOCK_SIZE, 16000))
        with self.device_listener as listener:
            stream = listener.listen(params.BLOCK_SIZE, params.BLOCK_STRIDE)
            timeline = spotter._spot_on_stream(self.model, keywords, stream, False) 
        return timeline     

    def play_audio(self, name_file):
        pygame.init()
        pygame.mixer.init(frequency=params.SPEAKER_RATE, size=-16, channels=params.SPEAKER_CHANNELS)
        pygame.mixer.music.load(name_file)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
             continue
        pygame.mixer.quit()
        pygame.quit()
        return 0
        
        
    async def init(self, req_text):
        for i in range(3):
            self.set_LED(i, 0,0,3)
        url = params.bot_init_url
        response = requests.request("POST", url, json={"uuid": params.bot_UUID})
        print('check')
        #print(response.json())
        json_response = response.json()
        my_cuid = json_response['result']['cuid']
        url2 = params.bot_request_url
        response2 = requests.request("POST", url2, json={"uuid": params.bot_UUID, "cuid": my_cuid, "text": req_text})
        json_response2 = response2.json()
        my_text = json_response2['result']['text']['value']
        for i in range(3):
            self.set_LED(i, 0,0,0)
        if params.answer_cut is not None:
        
            if len(my_text)>params.answer_cut:
                #my_text[51]='\0'
                print(my_text[:params.answer_cut])
                self.test_tts(my_text[:params.answer_cut])
            else:
                print(my_text)
                self.test_tts(my_text)   
        else: 
            print(my_text)
            self.test_tts(my_text) 

    def tts(self, text, voice, options:dict=None):
        url = params.tts_url
        payload = {"voice": voice, "text": text}

        if options is not None:
            payload.update(options)


 
        response = requests.request("POST", url, headers=params.tts_headers, data=json.dumps(payload))
 
        if response:
            response = json.loads(response.text)["response"][0]
            time = response["synthesis_time"]
            audio = b64decode(response["response_audio"].encode("utf-8"))
            return audio, time
        else:
            return
    
    def test_tts(self, tts_text):

        result = self.tts(tts_text, params.tts_voice, params.tts_options)
        if result is None:
            print("Error")
    
        audio, time = result
    
        with open("result.wav", "wb") as f:
            f.write(audio)
