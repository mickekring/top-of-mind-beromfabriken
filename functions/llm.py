
import streamlit as st
from openai import OpenAI
import os
from os import environ

import config as c


def process_text_openai(model, temp, system_prompt, text):

    if c.deployment == "streamlit":
        client = OpenAI(api_key = st.secrets.openai_key)
    else:
        client = OpenAI(api_key = environ.get("openai_key"))
    
    with st.container(border = True):

            message_placeholder = st.empty()
            full_response = ""

            for response in client.chat.completions.create(
                model=model,
                temperature=temp,
                messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text}
                ],
                stream=True,
                ):
                    if response.choices[0].delta.content:
                        full_response += str(response.choices[0].delta.content)
                    message_placeholder.markdown(full_response + "▌") 
                    
            message_placeholder.markdown(full_response)
            return full_response
