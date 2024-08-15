
### Berömdrömmen
app_version = "0.1.1"
### Author: Micke Kring
### Contact: mikael.kring@ri.se


import os
from os import environ
import streamlit as st
from datetime import datetime
from sys import platform
import hashlib
from openai import OpenAI

# Streamlit Audio recorder
from audiorecorder import audiorecorder

from functions import convert_to_mono_and_compress
from transcribe import transcribe_with_whisper_openai
from llm import process_text, process_text_openai, process_text_openai_image_prompt
from voice import text_to_speech
import prompts as p
from image import create_image
from mix_audio import mix_music_and_voice

### INITIAL VARIABLES

# Creates folder if they don't exist
os.makedirs("audio", exist_ok=True) # Where audio/video files are stored for transcription
os.makedirs("text", exist_ok=True) # Where transcribed document are beeing stored


# Check and set default values if not set in session_state
# of Streamlit

if "spoken_language" not in st.session_state: # What language source audio is in
    st.session_state["spoken_language"] = "Automatiskt"
if "file_name_converted" not in st.session_state: # Audio file name
    st.session_state["file_name_converted"] = None
if "gpt_template" not in st.session_state: # Audio file name
    st.session_state["gpt_template"] = "Ljus röst 1"
if "llm_temperature" not in st.session_state:
    st.session_state["llm_temperature"] = 0.8
if "llm_chat_model" not in st.session_state:
    st.session_state["llm_chat_model"] = "gpt-4o"
if "audio_file" not in st.session_state:
    st.session_state["audio_file"] = False


# Checking if uploaded or recorded audio file has been transcribed
def compute_file_hash(uploaded_file):

    print("\nSTART: Check if audio file has been transcribed - hash")

    # Compute the MD5 hash of a file
    hasher = hashlib.md5()
    
    for chunk in iter(lambda: uploaded_file.read(4096), b""):
        hasher.update(chunk)
    uploaded_file.seek(0)  # Reset the file pointer to the beginning

    print("DONE: Check if audio file has been transcribed - hash")
    
    return hasher.hexdigest()



### MAIN APP ###########################


# Page configuration
st.set_page_config(
    page_title="Drömfabriken",
    layout="wide",
    page_icon="❤️",
    initial_sidebar_state="collapsed")

# CSS styling

st.markdown("""
<style>
            
h1 {
    padding: 0rem 0px 1rem;
}
            
[alt="user avatar"] {
    height: 2.8rem;
    width: 2.8rem;
    border-radius: 50%;
}
            
[alt="assistant avatar"] {
    height: 2.8rem;
    width: 2.8rem;
    border-radius: 50%;
}
            
[aria-label="Chat message from user"] {
    background: #ffffff;
    padding: 10px;
    border-radius: 0.5rem;
}
            
[aria-label="Chat message from assistant"] {
    padding: 10px;
}
      
.st-emotion {
    display: flex;
    align-items: flex-start;
    gap: 0.5rem;
    padding: 1rem;
    border-radius: 0.5rem;
    background-color: rgb(255 255 255);
}

[data-testid="block-container"] {
    padding-left: 3rem;
    padding-right: 3rem;
    padding-top: 0rem;
    padding-bottom: 0rem;
    margin-bottom: -7rem;
}
            
.block-container {
    padding-top: 3rem;
    padding-bottom: 2rem;
}

</style>
""", unsafe_allow_html=True)

### ### ### ###



def main():

    global translation
    global model_map_transcribe_model


    ### SIDEBAR

    ###### SIDEBAR SETTINGS

    st.sidebar.header("Inställningar")
    st.sidebar.markdown("")

    # Dropdown menu - choose source language of audio
    spoken_language = st.sidebar.selectbox(
            "Välj språk som talas", 
            ["Automatiskt", "Svenska", "Engelska", "Franska", "Tyska", "Spanska"],
            index=["Automatiskt", "Svenska", "Engelska", "Franska", "Tyska", "Spanska"].index(st.session_state["spoken_language"]),
        )

    model_map_spoken_language = {
            "Automatiskt": None,
            "Svenska": "sv",
            "Engelska": "en",
            "Franska": "fr",
            "Tyska": "de",
            "Spanska": "sp"

        }

    # Update the session_state directly
    st.session_state["spoken_language"] = spoken_language

    st.sidebar.markdown(
        "#"
        )


    ### ### ### ### ### ### ### ### ### ### ###
    ### MAIN PAGE
    
    topcol1, topcol2 = st.columns([2, 2], gap="large")

    with topcol1:
        # Title
        st.markdown("""
            # BERÖMDRÖMMEN
            Tryck på knappen __Spela in__ här under och ge ditt beröm till din kollega. När du är 
            klar trycker du på __Stoppa__. Vänta tills ditt tal gjorts om till text och 
            välj sedan en mall för beröm.
            """)
        
    with topcol2:

        st.link_button("Ge feedback", "https://forms.office.com/e/MWb69j7Be2")

        print()

        #with st.expander("Inställningar", expanded=False):
            #st.markdown("##### Inställningar")

        #    llm_model = st.selectbox(
        #        'Välj språkmodell', 
        #        ["GPT-4o", "LLaMa3 70B", "LLaMa3 8B"],
        #        index=["GPT-4o", "LLaMa3 70B", "LLaMa3 8B"].index(st.session_state["llm_chat_model"]),
        #    )

        #    llm_temp = st.slider(
        #        'Temperatur',
        #        min_value = 0.0,
        #        max_value = 1.0,
        #        step = 0.1,
        #        value = st.session_state["llm_temperature"],
        #    )

            # Update the session_state directly
        #    st.session_state["llm_chat_model"] = llm_model
        #    st.session_state["llm_temperature"] = llm_temp
            
        #    model_map = {
        #        "GPT-4o": "gpt-4o",
        #        "LLaMa3 8B": "llama3-8b-8192", 
        #        "LLaMa3 70B": "llama3-70b-8192"
        #    }

        #create_an_image = st.toggle("Skapa bild till den bearbetade texten")

            #st.button("Rensa", type="primary")
            #if st.button("Rensa"):
            #    st.session_state["file_name_converted"] = None
            #    gpt_template = "Välj mall"

    


    maincol1, maincol2 = st.columns([2, 2], gap="large")


    with maincol1:

        st.markdown("### Beröm din kollega")
        # CREATE TWO TABS FOR FILE UPLOAD VS RECORDED AUDIO    

        tab1, tab2 = st.tabs(["Spela in", "Ladda upp ljudfil"])


        # FILE UPLOADER

        with tab1:

            # Creates the audio recorder
            audio = audiorecorder(start_prompt="Spela in", stop_prompt="Stoppa", pause_prompt="", key=None)

            # The rest of the code in tab2 works the same way as in tab1, so it's not going to be
            # commented.
            if len(audio) > 0:

                # To save audio to a file, use pydub export method
                audio.export("audio/local_recording.wav", format="wav")

                # Open the saved audio file and compute its hash
                with open("audio/local_recording.wav", 'rb') as file:
                    current_file_hash = compute_file_hash(file)

                # If the uploaded file hash is different from the one in session state, reset the state
                if "file_hash" not in st.session_state or st.session_state.file_hash != current_file_hash:
                    st.session_state.file_hash = current_file_hash
                    
                    if "transcribed" in st.session_state:
                        del st.session_state.transcribed

                if "transcribed" not in st.session_state:
                
                    with st.spinner('Din ljudfil är lite stor. Jag ska bara komprimera den lite först...'):
                        st.session_state.file_name_converted = convert_to_mono_and_compress("audio/local_recording.wav", "local_recording.wav")
                        st.success('Inspelning komprimerad och klar. Startar transkribering.')

                    with st.spinner('Transkriberar. Det här kan ta ett litet tag beroende på hur lång inspelningen är...'):
                        st.session_state.transcribed = transcribe_with_whisper_openai(st.session_state.file_name_converted, 
                            "local_recording.mp3",
                            model_map_spoken_language[st.session_state["spoken_language"]]
                            )

                        st.success('Transkribering klar.')

                        st.balloons()

                local_recording_name = "local_recording.mp3"
                #document = Document()
                #document.add_paragraph(st.session_state.transcribed)

                #document.save('text/' + local_recording_name + '.docx')

                #with open("text/local_recording.mp3.docx", "rb") as template_file:
                #    template_byte = template_file.read()
                
                st.markdown("### Ditt beröm")
                
                if st.session_state.file_name_converted is not None:
                    st.audio(st.session_state.file_name_converted, format='audio/wav')
                
                st.write(st.session_state.transcribed)


        
        # AUDIO RECORDER ###### ###### ######

        with tab2:
            
            uploaded_file = st.file_uploader(
                "Ladda upp din ljud- eller videofil här",
                type=["mp3", "wav", "flac", "mp4", "m4a", "aifc"],
                help="Max 10GB stora filer", label_visibility="collapsed",
                )


            if uploaded_file:

                # Checks if uploaded file has already been transcribed
                current_file_hash = compute_file_hash(uploaded_file)

                # If the uploaded file hash is different from the one in session state, reset the state
                if "file_hash" not in st.session_state or st.session_state.file_hash != current_file_hash:
                    st.session_state.file_hash = current_file_hash
                    
                    if "transcribed" in st.session_state:
                        del st.session_state.transcribed

                
                # If audio has not been transcribed
                if "transcribed" not in st.session_state:

                    # Sends audio to be converted to mp3 and compressed
                    with st.spinner('Din ljudfil är lite stor. Jag ska bara komprimera den lite först...'):
                        st.session_state.file_name_converted = convert_to_mono_and_compress(uploaded_file, uploaded_file.name)
                        st.success('Inspelning komprimerad och klar. Startar transkribering.')

                # Transcribes audio with Whisper
                    with st.spinner('Transkriberar. Det här kan ta ett litet tag beroende på hur lång inspelningen är...'):
                        st.session_state.transcribed = transcribe_with_whisper_openai(st.session_state.file_name_converted, 
                            uploaded_file.name,
                            model_map_spoken_language[st.session_state["spoken_language"]])
                        st.success('Transkribering klar.')

                        st.balloons()

                
                st.markdown("### Ladda upp ditt beröm")
                
                if st.session_state.file_name_converted is not None:
                    st.audio(st.session_state.file_name_converted, format='audio/wav')
                
                st.write(st.session_state.transcribed)

            


    with maincol2:

        st.markdown("### Skapa AI-beröm")

        if "transcribed" in st.session_state:

            system_prompt = ""

            gpt_template = st.selectbox(
                "Välj mall", 
                ["Välj mall", 
                 "Ljus röst 1",
                 "Ljus röst 2",
                 "Djup röst 1",
                 "Djup röst 2"

                 ],
                index=[
                 "Ljus röst 1",
                 "Ljus röst 2",
                 "Djup röst 1",
                 "Djup röst 2"
                ].index(st.session_state["gpt_template"]),
            )

            if gpt_template == "Ljus röst 1":
                system_prompt = p.ljus_rost_1
            
            elif gpt_template == "Ljus röst 2":
                system_prompt = p.ljus_rost_2
            
            elif gpt_template == "Djup röst 1":
                system_prompt = p.djup_rost_1

            elif gpt_template == "Djup röst 2":
                system_prompt = p.djup_rost_2


            with st.popover("Visa prompt"):
                st.write(system_prompt)


            if gpt_template != "Välj mall":
                
                llm_model = st.session_state["llm_chat_model"]
                llm_temp = st.session_state["llm_temperature"]
                
                if "llama" in llm_model:
                    full_response = process_text(llm_model, llm_temp, system_prompt, st.session_state.transcribed)
                else:
                    full_response = process_text_openai(llm_model, llm_temp, system_prompt, st.session_state.transcribed)
                
                if gpt_template == "Ljus röst 1": # Sanna uppåt

                    voice = "4xkUqaR9MYOJHoaC1Nak"
                    stability = 0.3
                    similarity_boost = 0.86
                    
                    with st.spinner(text="Läser in din text..."):
                        tts_audio = text_to_speech(full_response, voice, stability, similarity_boost)

                    with st.spinner(text="Mixar musik och röst..."):
                            mix_music_and_voice("low")
                            st.audio("mixed_audio.mp3", format="audio/mpeg", loop=False)
                
                elif gpt_template == "Ljus röst 2": # Sanna

                    voice = "aSLKtNoVBZlxQEMsnGL2"
                    stability = 0.5
                    similarity_boost = 0.75
                    
                    with st.spinner(text="Läser in din text..."):
                        tts_audio = text_to_speech(full_response, voice, stability, similarity_boost)

                    with st.spinner(text="Mixar musik och röst..."):
                            mix_music_and_voice("low")
                            st.audio("mixed_audio.mp3", format="audio/mpeg", loop=False)

                elif gpt_template == "Djup röst 1": # Jonas

                    voice = "e6OiUVixGLmvtdn2GJYE"
                    stability = 0.71
                    similarity_boost = 0.48
                    
                    with st.spinner(text="Läser in din text..."):
                        tts_audio = text_to_speech(full_response, voice, stability, similarity_boost)

                    with st.spinner(text="Mixar musik och röst..."):
                            mix_music_and_voice("high")
                            st.audio("mixed_audio.mp3", format="audio/mpeg", loop=False)

                elif gpt_template == "Djup röst 2": # Dave

                    voice = "m8oYKlEB8ecBLgKRMcwy"
                    stability = 0.5
                    similarity_boost = 0.6
                    
                    with st.spinner(text="Läser in din text..."):
                        tts_audio = text_to_speech(full_response, voice, stability, similarity_boost)

                    with st.spinner(text="Mixar musik och röst..."):
                            mix_music_and_voice("medium")
                            st.audio("mixed_audio.mp3", format="audio/mpeg", loop=False)
                
                else:
                    pass

                #save_as_word(full_response)

                #with open("static/output.docx", "rb") as template_file:
                #    template_byte = template_file.read()
                
                #st.download_button(
                #    label = "Ladda ned wordfil",
                #    data = template_byte,
                #    file_name = "static/output.docx",
                #    mime = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                #)
                
                #if create_an_image:
                #    with st.container(border = True):
                #        with st.spinner(text="Skapar en bild..."):
                #            image_system_prompt = p.image_prompt
                #            image_prompt = process_text_openai_image_prompt(llm_model, 0.9, image_system_prompt, full_response)
                            
                #            created_image = create_image(image_prompt)
                #            st.image(created_image, image_prompt)
                

if __name__ == "__main__":
    main()



