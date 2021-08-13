# -*- coding: utf-8 -*-
"""
Created on Wed Mar 10 12:59:28 2021

"""
import params
import os

from record21_tt import Recorder, client_ws
import time
import asyncio, argparse


WAVE_INPUT_FILENAME = "result.wav"

a = Recorder(params.RESPEAKER_RATE)

#print(params.keywords)

loop=0

try:
    while 1:
        if loop is 0:
            print("KWS")
            
            if params.KWS == r"sova":
                print("sova") 
                for i in range(12): 
                    a.set_LED(i,3,3,0)                
           #     time.sleep(2)
                a.kws_check()
                        
        
        if params.ASR_MODEL == "ws_v2":
            loop = asyncio.get_event_loop().run_until_complete(client_ws(params.WS_RATE, params.ws_url, None, a))
            
        if loop is 1:
            for i in range(3):
                a.set_LED(i,3,0,0)
            a.play_audio(WAVE_INPUT_FILENAME)
except KeyboardInterrupt:
    #dev.cleanup()
    #dev.clear_strip()
    for i in range(3):
        a.set_LED(i,0,0,0)
    pass
    print("Goodbye")
