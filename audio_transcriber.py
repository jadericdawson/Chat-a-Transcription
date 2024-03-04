
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
from speak import Speak


global tools
global last_question_time
import os
os.environ["OPENAI_API_KEY"] = ""
os.environ["SERPER_API_KEY"] = ""
os.environ["WEATHER_API_KEY"] = ""
client = OpenAI(
    api_key="",
)
client.models.list()
client.models



class AudioTranscriber:
    def __init__(self, audio_file_path):
        # Initialize any required variables or load resources
        self.audio_file_path = audio_file_path
        self.ai_handler_instance = AIHandler()

    def check_audio_size(self, file_path):
        audio_file = eyed3.load(file_path)
        if audio_file is None:  # Ensure the audio file is loaded correctly
            return 0
        return audio_file.info.size_bytes

    def split_audio(self, file_path, target_size_bytes=15 * 1024 * 1024, silence_thresh=-40, min_silence_len=700, keep_silence=400):
        print("Splitting audio...")
        file_extension = os.path.splitext(file_path)[1].lower()

        if file_extension in ['.m4a', '.mp3']:
            audio = AudioSegment.from_file(file_path, format=file_extension.replace('.', ''))
        else:
            raise ValueError("Unsupported file format. Only MP3 and M4A formats are supported.")

        # Calculate target duration in milliseconds
        audio_bitrate = audio.frame_rate * audio.frame_width * 8 * audio.channels
        target_duration_ms = (target_size_bytes * 1000 * 8) / audio_bitrate

        # Split audio based on silence
        chunks = split_on_silence(audio, 
                                  min_silence_len=min_silence_len, 
                                  silence_thresh=silence_thresh, 
                                  keep_silence=keep_silence, 
                                  seek_step=1)

        # Initialize tqdm progress bar
        pbar = tqdm(total=len(chunks), desc="Processing Chunks")

        # Refine chunks to target size
        refined_chunks = []
        current_chunk = AudioSegment.empty()
        for chunk in chunks:
            if len(current_chunk) + len(chunk) < target_duration_ms:
                current_chunk += chunk
            else:
                # Split chunk if adding it exceeds target duration
                split_point = target_duration_ms - len(current_chunk)
                before, after = chunk[:split_point], chunk[split_point:]
                current_chunk += before
                refined_chunks.append(current_chunk)
                current_chunk = after
            pbar.update(1)  # Update progress for each processed chunk
        if len(current_chunk) > 0:
            refined_chunks.append(current_chunk)

        pbar.close()  # Close the progress bar

        print("Finished splitting audio.")
        return refined_chunks
    
    
    def Run_Transcription(self, user_input):
        #Initalize the AI

        if not user_input:
            user_input = ""
        execute_AI = self.ai_handler_instance.run_AI(user_input)
        response_text = ""
        
        response = execute_AI.data[-1].content
        
        # Check if the response is not empty and has the expected structure
        if response and isinstance(response, list) and hasattr(response[0], 'text'):
            response_text = response[0].text.value
        else:
            response_text = "Unable to extract the summary."

        
        print("\n\n")

        return response_text
    
    def transcribe_audio(self):
                # Check if the audio file size exceeds the 25MB threshold
        if self.check_audio_size(self.audio_file_path) > 15 * 1024 * 1024:
            # If it does, split the audio into segments
            print("Audio file greater than 25MB. Chunking into smaller segments for processing...")
            audio_segments = self.split_audio(self.audio_file_path)
            all_transcriptions = ""
            for i, segment in tqdm(enumerate(audio_segments), total=len(audio_segments), desc="Processing Segments"):
                # Export each segment to a temporary file for processing
                segment_file_path = f"temp_segment_{i}.mp3"
                segment.export(segment_file_path, format="mp3")
                
                # Now, process each segment file for transcription
                with open(segment_file_path, "rb") as seg_file:
                    transcription_response = client.audio.transcriptions.create(
                        model="whisper-1", 
                        file=seg_file
                    )
                    # Assuming the transcription was successful, append the text
                    if transcription_response:
                        all_transcriptions += transcription_response.text + " "
                
                # Optional: Delete the temporary segment file if desired
                os.remove(segment_file_path)
        else:
            # Process the entire file as a single segment if under the size threshold
            with open(self.audio_file_path, "rb") as audio_file:
                transcription_response = client.audio.transcriptions.create(
                    model="whisper-1", 
                    file=audio_file
                )
                if transcription_response:
                    all_transcriptions = transcription_response.text
        return all_transcriptions 





    def clean_transcript(self, all_transcriptions):
        # Now, all_transcriptions contains the concatenated transcript of all segments
        print("Transcription: ", all_transcriptions)

        # Assuming that the transcription response returns a dictionary-like object
        # Check if transcription was successful
        transcript_text_1 = all_transcriptions
        instructions = """Please read the following meeting transcript. Summarize the most important topics as bullet points. 
            Then create a bullet point list of action items. Put a lot of effort in outlining all details of the meeting.\n 
            Do not make any assumptions. You only know the details provided in the meeting. Do not make anything up. Organize based
            on topic, not individuals. Use Markdown formatting. Many individuals are involved in the meeting. Be careful when developing
            and understanding of the conversation. I'll tip you $10 to do your best to be accurate and througho.
            The following transcript is the entire meeting: \n\n"""
        print(instructions + all_transcriptions)


        transcript_text = all_transcriptions


        #Stopwords transcript reduction
        SsStopwords = set(nltk.corpus.stopwords.words('english')) # load generic stopwords
        #print(f'stopwords:{len(SsStopwords)}')
        #print(sorted(SsStopwords))
        import contractions


        print("<<<<<<<<<<<<<<<<<contractions>>>>>>>>>>>>>>>>")
        removed_contractions_1 = contractions.fix(all_transcriptions)
        print("<<<<<<<<<<<<<<<<<tokenizing>>>>>>>>>>>>>>>>")
        tokens_1 = nltk.tokenize.word_tokenize(removed_contractions_1)
        print("<<<<<<<<<<<<<<<<<token for token>>>>>>>>>>>>>>>>")
        filtered_tokens_transcript_1 = [token for token in tokens_1 if token.lower() not in SsStopwords]
        print("<<<<<<<<<<<<<<<<<join>>>>>>>>>>>>>>>>")
        cleaned_filtered_tokens_transcript_1 = ' '.join(filtered_tokens_transcript_1)
        print("Cleaned_1: ", cleaned_filtered_tokens_transcript_1)
        print("<<<<<<<<<<<<<<<<<Run_Transcription>>>>>>>>>>>>>>>>")
        run_transcript_1 = self.Run_Transcription(instructions + cleaned_filtered_tokens_transcript_1)
        full_reply_content = run_transcript_1
        print("<<<<<<<<<<<<<<<<<AI_Reply>>>>>>>>>>>>>>>>")
        AI_Reply = self.Run_Transcription("Full transcript: " + full_reply_content + """
                                    I'll give you a $10 tip to provide a single Meeting Summary and a single Action Items section in your respose.
                                    I also want you to be clear, concise, and brief. Only present the most important and actionable information.""")
        print('AI_Reply:\n\n', AI_Reply)
        Speak(AI_Reply[:4000])
        return cleaned_filtered_tokens_transcript_1







