from openai import OpenAI
from pathlib import Path
import time
import pygame
import speech_recognition as sr
from get_weather import get_current_weather, get_forcast_weather
import json
from playsound import playsound
import threading
import time
import sys
from uuid import uuid4
from typing import List
import time
import pytz
from datetime import datetime
from AUTOGEN import AUTOGEN
from PLANNER import PLANNER
import nltk, pandas as pd
from collections import Counter
tmp = nltk.download(['gutenberg','stopwords'], quiet=True)
from pydub import AudioSegment
from pydub.silence import split_on_silence
from pydub.silence import detect_nonsilent
import eyed3
import PySimpleGUI as sg
from tqdm import tqdm
import AIHandler
from pydub import AudioSegment
from pydub.silence import detect_nonsilent
from tqdm import tqdm
import http.client
import json
import pyaudio
import os


# Initialize Pygame Mixer
pygame.mixer.init()

os.environ["OPENAI_API_KEY"] = ""
os.environ["SERPER_API_KEY"] = ""
os.environ["WEATHER_API_KEY"] = ""
client = OpenAI(
    api_key="",
)
client.models.list()
client.models


def play_audio(file_path):
    pygame.mixer.music.load(file_path)
    pygame.mixer.music.play()

    # Wait for the music to play before exiting the function
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)



# Initialize PyAudio
p = pyaudio.PyAudio()
stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=8192)


speech_file_path = Path(__file__).parent / "speech.mp3"   


def Speak(response_text):
    print(f"\n\nResponse text:\n\n {response_text}")
    print("\nConverting to audio..\n")
    
    # Say the response
    speech = client.audio.speech.create(
        model="tts-1",
        voice="onyx",
        input=response_text
    )
    print("Writing to file...\n")
    speech.stream_to_file(speech_file_path)
    
    print("Playing...\n")
    audio_thread = threading.Thread(target=play_audio, args=(str(speech_file_path),))
    audio_thread.start()

    # Interrupt option
    input("Press Enter to interrupt playback...\n")
    pygame.mixer.music.stop()  # This stops the playback
    
    # If needed, join the thread to ensure it has finished before continuing
    audio_thread.join()    
