
import streamlit as st
from openai import OpenAI
import config as c

client = OpenAI(api_key = st.secrets.openai_key)

# Whisper OpenAI

def transcribe_with_whisper_openai(file, file_name):

	transcription = client.audio.transcriptions.create(
		model = "whisper-1", 
		file = file, 
		response_format = "text",
		prompt = ""
	)

	transcribed_content = transcription

	return transcribed_content
