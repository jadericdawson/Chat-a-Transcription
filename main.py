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
from AIHandler import AIHandler
from pydub import AudioSegment
from pydub.silence import detect_nonsilent
from tqdm import tqdm
import http.client
import json
import pyaudio
from audio_transcriber import AudioTranscriber
from speak import Speak
import os


def select_file(prompt):
    layout = [[sg.Text(prompt)], [sg.Input(), sg.FileBrowse()], [sg.OK(), sg.Cancel()]]
    window = sg.Window("File Select", layout)
    event, values = window.read()
    window.close()
    if event == "OK" and values[0]:
        return values[0]
    else:
        return None

# Define the function to write text to a file
def write_to_file(text, file_name):
    try:
        with open(file_name, 'w') as file:
            file.write(text)
        print("Transcript written to", file_name)
    except Exception as e:
        print("Error occurred while writing to file:", e)




def main():
    ai_handler_instance = AIHandler()  # Assuming AIHandler doesn't require arguments
    
    layout = [
        [sg.Text("Choose an option:")],
        [sg.Button("Use Existing Transcript"), sg.Button("Transcribe Audio File")]
    ]
    window = sg.Window("Transcription Tool", layout)
    
    event, values = window.read()
    window.close()
    
    if event == "Transcribe Audio File":
        audio_file_path = select_file("Select an audio file")
        if audio_file_path:
            print("Transcribing audio...")
            transcriber = AudioTranscriber(audio_file_path)  # Instantiate your AudioTranscriber with the path
            transcript_text = transcriber.transcribe_audio() # Transcribe
            print("Transcription Completed. \n\nTranscript Text:", transcript_text, "\n")
            if transcript_text:
                # Get the base name of the audio file (without extension)
                audio_file_name = os.path.splitext(os.path.basename(audio_file_path))[0]
                transcript_file_name = audio_file_name + ".txt"  # Create the transcript file name
                write_to_file(transcript_text, transcript_file_name)
                cleaned_transcript = transcriber.clean_transcript(transcript_text)
        else:
            sg.Popup("No file selected. Exiting.")
    elif event == "Use Existing Transcript":
        transcript_file_path = select_file("Select a transcript file")
        transcriber = AudioTranscriber(None)

        if transcript_file_path:
            # Assuming the transcript is a plain text file for simplicity
            try:
                with open(transcript_file_path, 'r') as file:
                    transcript_text = file.read()
                    print("Transcript Loaded. Transcript Text:", transcript_text)
                cleaned_transcript = transcriber.clean_transcript(transcript_text)
                AI_Reply = transcriber.Run_Transcription("Combine these previous replies into a single reply without duplication: " + cleaned_transcript + """
                    I'll give you a $10 tip to provide a single Meeting Summary and a single Action Items section in your respose.
                    I also want you to be clear, concise, and brief. Only present the most important and actionable information.""")
                print('AI_Reply:\n\n', AI_Reply)
                Speak(AI_Reply[:4000])
            except Exception as e:
                sg.Popup(f"Failed to read transcript file: {e}")
        else:
            sg.Popup("No file selected. Exiting.")
    else:
        sg.Popup("Invalid option selected. Exiting.")

    # Initialize a variable to control the loop
        
    continue_loop = True
    while continue_loop:
        # Get user input
        user_input = input("Ask questions on the imported transcript (type 'exit' to quit): ")

        # Check if user wants to exit
        if user_input.lower() == 'exit':
            # Set the loop control variable to False to exit the loop
            continue_loop = False
        else:
            # Print the user input
            #print("You entered:", user_input)
            # Ensure user_input is not None
            user_input = user_input if user_input is not None else ""
            # Ensure cleaned_transcript is not None
            cleaned_transcript = cleaned_transcript if cleaned_transcript is not None else ""

            run_transcribe = transcriber.Run_Transcription(
                "User input: " + user_input + "\n\n" +
                "The following text is the transcript of a meeting between many people. " +
                "Use the information found in the transcript to answer questions. " +
                "Do not make up anything. Do not make assumptions. " +
                "Transcript spelling of names may be wrong. User input is correct.\n" +
                "Transcript:\n" + cleaned_transcript
            )




            Speak(run_transcribe)




if __name__ == "__main__":
    main()
    
