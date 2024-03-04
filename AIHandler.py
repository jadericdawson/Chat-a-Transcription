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
from pydub import AudioSegment
from pydub.silence import detect_nonsilent
from tqdm import tqdm
import http.client
import json
import pyaudio
import os


os.environ["OPENAI_API_KEY"] = ""
os.environ["SERPER_API_KEY"] = ""
os.environ["WEATHER_API_KEY"] = ""
client = OpenAI(
    api_key="",
)
client.models.list()
client.models

import http.client
import json


class AIHandler:
    def __init__(self):
        persistant_thread_ID ="thread_FzRgxzxOAAX8xCO2qCI3vCqS"
        #self.weather_agent_thread = client.beta.threads.retrieve(f"{persistant_thread_ID}")
        self.weather_agent_thread = client.beta.threads.create()
        print(self.weather_agent_thread.id)
        self.assistant = client.beta.assistants.create(
            instructions="You are a helpful assistant. Use the provided functions to answer questions. You only know the English language.",
            model="gpt-4-1106-preview",
            tools=[{
                "type": "function",
                "function": {
                    "name": "getCurrentWeather",
                    "description": "Get the weather in location. Use this information to answer users questions about the weather in a creative and fun manner. Example terms: '°F' = 'degrees Fahrenheit', 'SSW' = 'South-SouthWest'",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "location": {"type": "string", "description": "The city and state e.g. San Francisco, CA"},
                            "unit": {"type": "string", "enum": ["c", "f"]}
                        },
                        "required": ["location"]
                    }
                }
            },{
                "type": "function",
                "function": {
                    "name": "getforcastWeather",
                    "description": "Get the weather forcast in location."
                    "Use this information to answer users questions about the furture or forcast"
                    "weather in a creative and fun manner. Example terms: '°F' = 'degrees Fahrenheit', 'SSW' = 'South-SouthWest'",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "location": {"type": "string", "description": "The city and state e.g. San Francisco, CA"},
                            "unit": {"type": "string", "enum": ["c", "f"]}
                        },
                        "required": ["location"]
                    }
                }
            },{
                "type": "function",
                "function": {
                    "name": "getNickname",
                    "description": "Get the nickname of a city",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "location": {"type": "string", "description": "The city and state e.g. San Francisco, CA. This is where I live."},
                        },
                        "required": ["location"]
                    }
                } 
            },{
                "type": "function",
                "function": {
                    "name": "new_thread_ID",
                    "description": "Get a new assistant thread ID.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                        },
                        "required": []
                    }
                } 
            },{
                "type": "function",
                "function": {
                    "name": "get_time",
                    "description": "Get the current time, report in AM/PM. Say nothing else.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                        },
                        "required": []
                    }
                } 
            }]
        )

    def pretty_print(messages):
        print("# Messages")
        for m in messages:
            print(f"{m.role}: {m.content[0].text.value}")
        print()

    def wait_on_run(self, run):
        while run.status == "queued" or run.status == "in_progress":
            run = client.beta.threads.runs.retrieve(
                thread_id=self.weather_agent_thread.id,
                run_id=run.id,
            )
            time.sleep(0.5)
        return run
    def wait_on_run_new_ID(self, run):
        while run.status == "queued" or run.status == "in_progress":
            run = client.beta.threads.runs.retrieve(
                thread_id=self.old_thread.id,
                run_id=run.id,
            )
            time.sleep(0.5)
        return run
    
    def new_thread_ID(self):
        persistant_thread_ID = client.beta.threads.create()
        return persistant_thread_ID

    def run_AI(self, transcript_text):
        message = client.beta.threads.messages.create(
            thread_id=self.weather_agent_thread.id,
            role="user",
            content=transcript_text
        )
        print(message.content)
        run = client.beta.threads.runs.create(
            thread_id=self.weather_agent_thread.id,
            assistant_id=self.assistant.id,
            instructions="Please answer the users questions."
        )
        run = self.wait_on_run(run)
        print(run.status)
        # Process tool calls if action is required
        if run.status == "requires_action":
            tool_calls = run.required_action.submit_tool_outputs.tool_calls
            tool_outputs = []
            for call in tool_calls:
                if call.function.name == "getCurrentWeather":
                    # Extract parameters from the tool call
                    arguments = json.loads(call.function.arguments)
                    location = arguments.get("location")
                    # Call your imported weather function
                    weather_data = get_current_weather(location)
                    # Convert to JSON string
                    json_output = json.dumps(weather_data)
                    # Append to tool_outputs
                    tool_outputs.append({
                        "tool_call_id": call.id,
                        "output": json_output  # Make sure this is JSON-formatted
                    })
                if call.function.name == "getforcastWeather":
                    # Extract parameters from the tool call
                    arguments = json.loads(call.function.arguments)
                    location = arguments.get("location")
                    # Call your imported weather function
                    forcast_data = get_forcast_weather(location)
                    # Convert to JSON string
                    json_output = json.dumps(forcast_data)
                    # Append to tool_outputs
                    tool_outputs.append({
                        "tool_call_id": call.id,
                        "output": json_output  # Make sure this is JSON-formatted
                    })                    
                elif call.function.name == "new_thread_ID":
                    # Handle new_thread_ID tool call
                    new_thread_id = self.new_thread_ID()
                    self.old_thread = self. weather_agent_thread
                    self.weather_agent_thread = new_thread_id
                    # Convert to JSON string or appropriate format
                    print(new_thread_id)
                    #json_output = json.dumps({"thread_id": new_thread_id})
                    tool_outputs.append({
                        "tool_call_id": call.id,
                        "output": f"Your new thread ID is: {new_thread_id.id}."
                    })
                    run = client.beta.threads.runs.submit_tool_outputs(
                        thread_id=self.old_thread.id,
                        run_id=run.id,
                        tool_outputs=tool_outputs
                    )
                    run = self.wait_on_run_new_ID(run)
                    return client.beta.threads.messages.list(thread_id=self.old_thread.id, order="asc")
                elif call.function.name == "getNickname":
                    print("I'll not give you a nickname!!!")
                    tool_outputs.append({
                        "tool_call_id": call.id,
                        "output": "I shall not give you a nickname! Ask another question!"  # Make sure this is JSON-formatted
                    })
                elif call.function.name == "get_time":
                    edt = pytz.timezone('America/New_York')
                    current_time_edt = datetime.now(pytz.utc).astimezone(edt)
                    tool_outputs.append({
                        "tool_call_id": call.id,
                        "output": f"The current time is {current_time_edt}. Report in AM/PM and say nothing else."
                    })                    
                else:
                    print("Unable to handle tool call for:", call.function.name)
                            # Submit tool outputs


            # Submit tool outputs
            run = client.beta.threads.runs.submit_tool_outputs(
                thread_id=self.weather_agent_thread.id,
                run_id=run.id,
                tool_outputs=tool_outputs
            )
            run = self.wait_on_run(run)
        
        #print(client.beta.threads.messages.list(thread_id=self.weather_agent_thread.id, order="asc"))
        return client.beta.threads.messages.list(thread_id=self.weather_agent_thread.id, order="asc")
