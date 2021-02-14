#Phong Nguyen
#Valentine Hollywood makeup light project
#!/usr/bin/python
import time
import RPi.GPIO as GPIO
import pyaudio
from os import environ, path
from pocketsphinx.pocketsphinx import *
from sphinxbase.sphinxbase import *

MODELDIR = "/home/pi/pocketsphinx-python/pocketsphinx/model/"
DATADIR = "/home/pi/pocketsphinx-python/pocketsphinx/test/data/"

config = Decoder.default_config()
config.set_string('-hmm', path.join(MODELDIR, 'en-us/en-us'))
config.set_string('-lm', 'lang_models/assistant/assistant.lm')
config.set_string('-dict', 'lang_models/assistant/assistant.dic')
config.set_string('-logfn', '/dev/null')
decoder = Decoder(config)

p = pyaudio.PyAudio()
stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=1024)
stream.start_stream()

in_speech_bf = False
decoder.start_utt()

# Setup GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# GPIO 14 for less light, hold for color change
GPIO.setup(14, GPIO.OUT)
GPIO.output(14, GPIO.LOW)
# GPIO 15 for turn light on and off
GPIO.setup(15, GPIO.OUT)
GPIO.output(15, GPIO.LOW)
# GPIO 18 for more light, hold for color change
GPIO.setup(18, GPIO.OUT)
GPIO.output(18, GPIO.HIGH)
# GPIO 23 for assistant's listening state
GPIO.setup(23, GPIO.OUT)
GPIO.output(23, GPIO.LOW)

# light state
light = 0
# change color state
change_color = 0

# Assistant listen flag
assistant_f = 0
# press button flag
p_button_f = 0
# hold button flag
h_button_f = 0

# assistant_counter
assistant_c = 0
# press button counter
p_button_c = 0
# hold button counter
h_button_c = 0
count = 0
while True:
    try:
        # ================= COUNTER INCREMENT ========
        if assistant_f == 1:
            assistant_c += 0.1

        if p_button_f == 1:
            p_button_c += 0.1
            print("\npress button:" + str(p_button_c))

        if h_button_f == 1:
            h_button_c += 0.1
            print("\nhold button:" + str(h_button_c))
        
        #===============================================


        #================ RESET =========================
        # reset assistant counter
        if assistant_c >140:
            assistant_f = 0
            assistant_c = 0
            if GPIO.input(23) == 1:
                GPIO.output(23, GPIO.LOW)

        # # reset press button counter
        if p_button_c > 1.5:
            p_button_f = 0
            p_button_c = 0
            if GPIO.input(18) == 0:
                GPIO.output(18, GPIO.HIGH)
            if GPIO.input(14) == 1:
                GPIO.output(14, GPIO.LOW)
            if GPIO.input(15) == 1:
                GPIO.output(15, GPIO.LOW)

        # # reset press button counter
        if h_button_c > 10:
            h_button_f = 0
            h_button_c = 0
            if GPIO.input(18) == 0:
                GPIO.output(18, GPIO.HIGH)
            if GPIO.input(14) == 1:
                GPIO.output(14, GPIO.LOW)
            if GPIO.input(15) == 1:
                GPIO.output(15, GPIO.LOW)
        #=====================================================

        buf = stream.read(1024, exception_on_overflow=False)
        if buf:
            decoder.process_raw(buf, False, False)
            if decoder.get_in_speech() != in_speech_bf:
                in_speech_bf = decoder.get_in_speech()
                if not in_speech_bf:
                    decoder.end_utt()

                    print('Result:', decoder.hyp().hypstr)

                    # decoding speech to string
                    mystr = decoder.hyp().hypstr
                    decoder.start_utt()

                    # find keyword in string
                    s_assistant = mystr.find("ASSISTANT")
                    s_light_on = mystr.find("LIGHTS ON")
                    s_light_off = mystr.find("LIGHTS OFF")
                    s_change_color = mystr.find("CHANGE COLOR")
                    s_more_light = mystr.find("BRIGHTER")
                    s_less_light = mystr.find("LESS LIGHT")

                    # Assistant is being called
                    if (s_assistant >= 0):
                        assistant_f = 1
                        GPIO.output(23, GPIO.HIGH)

                    # Assistant is listening then do stuff
                    if assistant_f == 1:

                        if (s_light_on >= 0 and p_button_f == 0 and h_button_f == 0):
                            GPIO.output(15, GPIO.HIGH)
                            p_button_f = 1

                        if (s_light_off >= 0 and p_button_f == 0 and h_button_f == 0):
                            GPIO.output(15, GPIO.HIGH)
                            p_button_f = 1

                        if (s_less_light >= 0 and p_button_f == 0 and h_button_f == 0):
                            print("18 low")
                            GPIO.output(18, GPIO.LOW)
                            p_button_f = 1

                        if (s_more_light >= 0 and p_button_f == 0 and h_button_f == 0):
                            print("14 high")
                            GPIO.output(14, GPIO.HIGH)
                            p_button_f = 1

                        if (s_change_color >= 0 and p_button_f == 0 and h_button_f == 0):
                            if change_color == 0:
                                change_color = 1
                                print("change color 1")
                                print("14 high long")
                                GPIO.output(14, GPIO.HIGH)
                                h_button_f = 1

                            else:
                                change_color = 0
                                GPIO.output(18, GPIO.LOW)
                                h_button_f = 1


        else:
            break
    except KeyboardInterrupt:
        print("Keyboard interrupted")
        GPIO.cleanup()
        sys.exit(0)
GPIO.cleanup()
decoder.end_utt()
