
KWS = "sova"

#sova_full
WINDOW = 4
THRESHOLD = 0.75 
BLOCK_SIZE = 1750
BLOCK_STRIDE = 300


button = False
BUTTON_GPIO = 12

#  ws ws_v2 file_asr_button file_asr_THRESHOLD
ASR_MODEL = "ws_v2"
for_old_nframes = 3000

ws_url = ""

WS_auth_type = ""
WS_auth_token = ""

tts_url = ""

bot_init_url = ""
bot_request_url = ""

bot_UUID = ""

tts_headers = {
}


tts_voice = ""
tts_options = {

}

RESPEAKER_RATE = 16000
RESPEAKER_CHANNELS = 1
RESPEAKER_WIDTH = 2
RESPEAKER_INDEX = 1 # refer to input device id
SPEAKER_RATE = 22050
SPEAKER_CHANNELS = 1
WS_RATE = 8000

model_path = r"../sova_full"

answer_cut = None#70
