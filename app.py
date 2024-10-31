
# Python imports
import os
import hmac
from os import environ
from datetime import datetime
from sys import platform
import hashlib
from concurrent.futures import ThreadPoolExecutor

# External imports
import streamlit as st
from openai import OpenAI

# Local imports
from functions.transcribe import transcribe_with_whisper_openai
from functions.llm import process_text_openai
from functions.voice import text_to_speech
from functions.mix_audio import mix_music_and_voice
from functions.split_audio import split_audio_to_chunks
from functions.styling import page_configuration, page_styling
import prompts as p
import config as c


### INITIAL VARIABLES

# Creates folder if they don't exist
os.makedirs("data/audio", exist_ok=True) # Where audio/video files are stored for transcription
os.makedirs("data/audio/audio_chunks", exist_ok=True) # Where audio/video files are stored for transcription


st.session_state["pwd_on"] = st.secrets.pwd_on

### PASSWORD

if st.session_state["pwd_on"] == "true":

    def check_password():

        passwd = st.secrets["password"]

        def password_entered():

            if hmac.compare_digest(st.session_state["password"], passwd):
                st.session_state["password_correct"] = True
                del st.session_state["password"]  # Don't store the password.
            else:
                st.session_state["password_correct"] = False

        if st.session_state.get("password_correct", False):
            return True

        st.text_input("Lösenord", type="password", on_change=password_entered, key="password")
        if "password_correct" in st.session_state:
            st.error("😕 Ooops. Fel lösenord.")
        return False


    if not check_password():
        st.stop()


# Check and set default values if not set in session_state
# of Streamlit

if "spoken_language" not in st.session_state: # What language source audio is in
    st.session_state["spoken_language"] = "Automatiskt"
if "file_name_converted" not in st.session_state: # Audio file name
    st.session_state["file_name_converted"] = None
if "gpt_template" not in st.session_state: # Audio file name
    st.session_state["gpt_template"] = "Ljus röst - Glad, positiv och svär gärna"
if "llm_temperature" not in st.session_state:
    st.session_state["llm_temperature"] = c.llm_temp
if "llm_chat_model" not in st.session_state:
    st.session_state["llm_chat_model"] = c.llm_model
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

page_configuration()
page_styling()


def main():

    global translation
    global model_map_transcribe_model


    ### SIDEBAR

    st.sidebar.markdown(
        f"""# Berömfabriken
Det här är en av flera prototyper som togs fram till projektet 'Top of Mind: 
Jämställdhet i industrins vardag.  
https://www.ri.se/sv/vad-vi-gor/projekt/top-of-mind-jamstalldhet-i-industrins-vardag

---

Micke Kring
RISE

mikael.kring@ri.se

---

Version: {c.app_version}  
Uppdaterad: {c.app_updated}

        """
        )


    ### ### ### ### ### ### ### ### ### ### ###
    ### MAIN PAGE
    
    topcol1, topcol2 = st.columns([2, 2], gap="large")

    with topcol1:
        # Title
        st.markdown(f"""## :material/thumb_up: {c.app_name}""")
        st.markdown("""Klicka på __mikrofonsymbolen__ här under för att spela in ditt beröm till din kollega. När du är 
            klar trycker du på __stoppsymbolen__. Vänta tills ditt tal gjorts om till text och 
            välj sedan en mall för beröm.""")

        
    with topcol2:

        with st.expander(":material/help: Vill du ha tips?"):
            st.markdown("""__Att ge beröm till en kollega kan kännas lite pinsamt, men forskning har visat att 
det kan få oss att må bättre på jobbet och att vi till och med blir mer produktiva. 
Att få höra att kollegor värdesätter och uppmärksammar en ökar ens välmående helt enkelt.__

Det viktigaste är att det kommer från hjärtat och ett spontant beröm kommer du långt med.
Men om du vill ha några tips, så försök att vara specifik. Berätta vad det är du tycker din 
kollega gör så bra och hur det får dig att känna. I stället för att bara säga ‘bra jobbat’, 
nämn något konkret, som ‘jag uppskattar verkligen att du kan hålla lugnet under press.’ 

Du kan också ge beröm både för prestationer och egenskaper. Du kan berömma hur någon löser 
ett problem, men även deras samarbetsförmåga, empati eller hur de stöttar andra i teamet.

Kom ihåg att även vara jämställd i hur du ger beröm. Se till att alla får erkännande för 
sina insatser, oavsett kön, titel eller bakgrund. Det hjälper till att skapa ett mer 
inkluderande arbetsklimat.

Och till sist, var ärlig. Människor känner av när beröm är genuint. Så när du ser något bra – säg det!
Att regelbundet ge beröm bygger upp tillit, respekt och en arbetsplats där alla känner sig 
sedda och uppskattade.
""")


    maincol1, maincol2 = st.columns([2, 2], gap="large")


    with maincol1:

        st.markdown("#### Beröm din kollega")

        audio = st.experimental_audio_input("Spela in ett röstmeddelande", label_visibility = "collapsed")

        if audio:
            current_file_hash = compute_file_hash(audio)

            # If the uploaded file hash is different from the one in session state, reset the state
            if "file_hash" not in st.session_state or st.session_state.file_hash != current_file_hash:
                st.session_state.file_hash = current_file_hash
                
                if "transcribed" in st.session_state:
                    del st.session_state.transcribed

            if "transcribed" not in st.session_state:

                with st.status('Delar upp ljudfilen i mindre bitar...'):
                    chunk_paths = split_audio_to_chunks(audio)

                # Transcribe chunks in parallel
                with st.status('Transkriberar alla ljudbitar. Det här kan ta ett tag beroende på lång inspelningen är...'):
                    with ThreadPoolExecutor() as executor:
                        # Open each chunk as a file object and pass it to transcribe_with_whisper_openai
                        transcriptions = list(executor.map(
                            lambda chunk: transcribe_with_whisper_openai(open(chunk, "rb"), os.path.basename(chunk)), 
                            chunk_paths
                        )) 
                        # Combine all the transcriptions into one
                        st.session_state.transcribed = "\n".join(transcriptions)
            
            st.markdown("#### Ditt beröm")
            st.write(st.session_state.transcribed)



    with maincol2:

        st.markdown("#### Skapa AI-beröm")

        if "transcribed" in st.session_state:

            system_prompt = ""

            gpt_template = st.selectbox(
                "Välj mall", 
                ["Välj mall", 
                 "Ljus röst - Glad, positiv och svär gärna",
                 "Ljus röst - Korrekt myndighetsperson",
                 "Djup röst - Fåordig men glad och rolig",
                 "Djup röst - Skojfrisk och svärande"

                 ],
                index=[
                 "Ljus röst - Glad, positiv och svär gärna",
                 "Ljus röst - Korrekt myndighetsperson",
                 "Djup röst - Fåordig men glad och rolig",
                 "Djup röst - Skojfrisk och svärande"
                ].index(st.session_state["gpt_template"]),
            )

            if gpt_template == "Ljus röst - Glad, positiv och svär gärna":
                system_prompt = p.ljus_rost_1
            
            elif gpt_template == "Ljus röst - Korrekt myndighetsperson":
                system_prompt = p.ljus_rost_2
            
            elif gpt_template == "Djup röst - Fåordig men glad och rolig":
                system_prompt = p.djup_rost_1

            elif gpt_template == "Djup röst - Skojfrisk och svärande":
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
                
                if gpt_template == "Ljus röst - Glad, positiv och svär gärna": # Sanna uppåt

                    voice = "4xkUqaR9MYOJHoaC1Nak"
                    stability = 0.3
                    similarity_boost = 0.86
                    
                    with st.spinner(text="Läser in din text..."):
                        tts_audio = text_to_speech(full_response, voice, stability, similarity_boost)

                    with st.spinner(text="Mixar musik och röst..."):
                            mix_music_and_voice("low")
                            st.audio("data/audio/mixed_audio.mp3", format="audio/mpeg", loop=False)
                
                elif gpt_template == "Ljus röst - Korrekt myndighetsperson": # Sanna

                    voice = "aSLKtNoVBZlxQEMsnGL2"
                    stability = 0.5
                    similarity_boost = 0.75
                    
                    with st.spinner(text="Läser in din text..."):
                        tts_audio = text_to_speech(full_response, voice, stability, similarity_boost)

                    with st.spinner(text="Mixar musik och röst..."):
                            mix_music_and_voice("low")
                            st.audio("data/audio/mixed_audio.mp3", format="audio/mpeg", loop=False)

                elif gpt_template == "Djup röst - Fåordig men glad och rolig": # Jonas

                    voice = "e6OiUVixGLmvtdn2GJYE"
                    stability = 0.71
                    similarity_boost = 0.48
                    
                    with st.spinner(text="Läser in din text..."):
                        tts_audio = text_to_speech(full_response, voice, stability, similarity_boost)

                    with st.spinner(text="Mixar musik och röst..."):
                            mix_music_and_voice("high")
                            st.audio("data/audio/mixed_audio.mp3", format="audio/mpeg", loop=False)

                elif gpt_template == "Djup röst - Skojfrisk och svärande": # Dave

                    voice = "m8oYKlEB8ecBLgKRMcwy"
                    stability = 0.5
                    similarity_boost = 0.6
                    
                    with st.spinner(text="Läser in din text..."):
                        tts_audio = text_to_speech(full_response, voice, stability, similarity_boost)

                    with st.spinner(text="Mixar musik och röst..."):
                            mix_music_and_voice("medium")
                            st.audio("data/audio/mixed_audio.mp3", format="audio/mpeg", loop=False)
                
                else:
                    pass
                

if __name__ == "__main__":
    main()



