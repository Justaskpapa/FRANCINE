import tempfile
import sounddevice as sd
import numpy as np
import soundfile as sf
import whisper
import pyttsx3
import asyncio
import json
from pathlib import Path
import time

# NEW: Import webrtcvad
import webrtcvad # Using webrtcvad-wheels

# Load config for voice settings
CONFIG_PATH = Path("./config.json")
CONFIG = {}
if CONFIG_PATH.exists():
    try:
        with open(CONFIG_PATH, 'r') as f:
            CONFIG = json.load(f)
    except json.JSONDecodeError:
        print("Warning: config.json is corrupted. Using default voice settings.")

# Voice configuration settings
VAD_ENABLED = CONFIG.get("vad", True)
LISTEN_TIMEOUT = CONFIG.get("listen_timeout", 5.0) # Max seconds to listen if VAD isn't used
WAKE_WORD = CONFIG.get("wake_word", "francine").lower() # Ensure lowercase for comparison
ALWAYS_ON = CONFIG.get("always_on", True) # Default to always on if not specified

# Load Whisper model once globally for efficiency.
try:
    MODEL = whisper.load_model('base') # 'base' is a good balance for speed/accuracy
except Exception as e:
    print(f"CRITICAL ERROR: Failed to load Whisper model: {e}. Please ensure 'base' model is downloaded.")
    MODEL = None


def whisper_listen() -> str:
    """
    Listens for audio input and converts it to text using Whisper.
    Supports VAD and wake word detection based on config.
    """
    if MODEL is None:
        print("Whisper model not loaded. Cannot perform speech-to-text.")
        return ""

    fs = 16000 # Sample rate
    frame_duration = 30 # ms per frame for VAD
    frame_size = int(fs * frame_duration / 1000) # Bytes per frame for VAD

    # VAD instance
    vad_detector = webrtcvad.Vad(3) # Aggressiveness: 0 (least) to 3 (most)

    print("Listening...")
    frames = []
    silent_frames = 0
    
    # Use a non-blocking stream for VAD
    with sd.RawInputStream(samplerate=fs, channels=1, dtype='int16', blocksize=frame_size) as stream:
        start_time = time.time()
        while True:
            data, overflowed = stream.read(frame_size)
            if overflowed:
                print("Warning: Audio input buffer overflowed!")
            
            # Ensure frame data is correct size for VAD
            if len(data) < frame_size: # Not enough data for a full frame
                time.sleep(0.001) # Small sleep to prevent busy-waiting
                continue

            is_speech = vad_detector.is_speech(data.tobytes(), fs)
            
            if is_speech:
                frames.append(data)
                silent_frames = 0
            elif len(frames) > 0: # If we have started recording, count silent frames
                silent_frames += 1
            
            # Stop condition: silence after speech, or timeout
            # 0.5 seconds of silence (approx 16 frames for 30ms frames)
            if VAD_ENABLED and len(frames) > 0 and silent_frames > (fs / frame_size * 0.5):
                print("Detected end of speech (VAD).")
                break
            
            if not VAD_ENABLED and (time.time() - start_time > LISTEN_TIMEOUT):
                print(f"Listening timeout ({LISTEN_TIMEOUT}s) reached.")
                break
            
            if VAD_ENABLED and (time.time() - start_time > LISTEN_TIMEOUT * 2) and len(frames) == 0: # Max listen time if only silence
                print(f"Max listen time ({LISTEN_TIMEOUT*2}s) reached with no speech.")
                return "" # Return empty if no speech detected at all

            # Small sleep to prevent busy-waiting if loop is very tight
            time.sleep(0.001) # Keep this small sleep to prevent high CPU usage in tight loop

    if not frames:
        return ""

    audio_data = np.frombuffer(b''.join(frames), dtype='int16')
    
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=True) as f:
        try:
            sf.write(f.name, audio_data, fs)
            result_text = MODEL.transcribe(f.name).get('text', '').strip()
            
            # Basic wake word detection (if enabled and not always_on)
            if not ALWAYS_ON and WAKE_WORD and WAKE_WORD in result_text.lower():
                print(f"Wake word '{WAKE_WORD}' detected.")
                return result_text.lower().replace(WAKE_WORD, '').strip() # Remove wake word
            elif not ALWAYS_ON and WAKE_WORD and WAKE_WORD not in result_text.lower():
                print("Wake word not detected. Ignoring input.")
                return "" # Ignore if wake word not present in non-always-on mode
            
            return result_text
        except Exception as e:
            print(f"Error during audio transcription: {e}. Check Whisper model and audio file.")
            return ""


async def tts_speak(txt: str) -> None:
    """
    Converts text to speech using pyttsx3 and plays it.
    This function is blocking and will be run in a separate thread via asyncio.to_thread.
    """
    def _speak_blocking(text_to_speak):
        try:
            engine = pyttsx3.init()
            engine.say(text_to_speak)
            engine.runAndWait()
        except Exception as e:
            print(f"Error during text-to-speech: {e}. Check pyttsx3 installation and audio output.")

    await asyncio.to_thread(_speak_blocking, txt)
