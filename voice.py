
import requests
import streamlit as st
from os import environ
import config as c

if c.run_mode == "local":
    voice_api_key = st.secrets.elevenlabs_key
else:
    voice_api_key = environ.get("elevenlabs_key")

text = """Ah, behold the elusive Homo sapiens in their natural habitat: the corporate 
meeting room. Here, we witness a fascinating display of social grooming, where the alpha 
speaker pontificates on the essence of "psychological safety." Yes, dear viewers, 
it's all about feeling warm and fuzzy inside while navigating the treacherous waters of 
office politics.
"""


def text_to_speech(text, voice, stability, similarity_boost):

    import requests

    CHUNK_SIZE = 1024
    url = "https://api.elevenlabs.io/v1/text-to-speech/" + voice

    headers = {
    "Accept": "audio/mpeg",
    "Content-Type": "application/json",
    "xi-api-key": voice_api_key
    }

    data = {
    "text": text,
    "model_id": "eleven_multilingual_v2",
    "voice_settings": {
        "stability":stability,
        "similarity_boost": similarity_boost
    }
    }

    response = requests.post(url, json=data, headers=headers)
    with open('tts_audio.mp3', 'wb') as f:
        for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
            if chunk:
                f.write(chunk)
