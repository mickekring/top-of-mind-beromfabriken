from pathlib import Path
from openai import OpenAI
import streamlit as st

client = OpenAI(api_key = st.secrets.openai_key)

speech_file_path = Path(__file__).parent / "speech.mp3"
response = client.audio.speech.create(
  model="tts-1-hd",
  voice="nova", #nova - onyx ok
  input="Jag vill verkligen berömma Anna för att hon alltid är så snäll och hjälpsam. Hon finns alltid där när jag behöver henne och ställer upp utan krångel. Hon är rak, tydlig och en riktigt pålitlig kollega."
)

response.stream_to_file(speech_file_path)