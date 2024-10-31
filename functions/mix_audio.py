
from pydub import AudioSegment
import random

def mix_music_and_voice(volume_strength):

    track = random.randint(1, 13)
    print(track)

    # Load audio files
    background_music = AudioSegment.from_file("music/music" + str(track) + ".mp3")
    speaker_voice = AudioSegment.from_file("data/audio/tts_audio.mp3")

    #Adjust the volume of the speaker voice
    if volume_strength == "low":
        speaker_voice = speaker_voice + 8
    elif volume_strength == "medium":
        speaker_voice = speaker_voice + 1
    else:
        pass

    # Adjust the volume of the background music
    background_music = background_music - 8  # Lower the volume by 10dB (approximately 30%)

    # Add 3 seconds of silence to the beginning of the speaker voice
    silence = AudioSegment.silent(duration=3000)  # 3 seconds of silence
    speaker_voice = silence + speaker_voice

    # Calculate the total length required for the background music
    total_length = len(speaker_voice) + 3000  # Duration of speaker voice plus 3 seconds

    # Loop the background music to match the total length required
    looped_background_music = background_music * (total_length // len(background_music) + 1)
    looped_background_music = looped_background_music[:total_length].fade_out(duration=3000)

    # Overlay the speaker voice on top of the background music
    combined = looped_background_music.overlay(speaker_voice)

    # Export the mixed audio
    combined.export("data/audio/mixed_audio.mp3", format="mp3")

