"""
Speech-to-Text Module - It will Take the user commands through microphone and 
convert it into the text

"""

import speech_recognition as sr
import sounddevice as sd
import numpy as np
import time


def recognize_speech(lang="en-US", timeout=5):
    """
    Capture audio from microphone and return recognized text.
    
    Args:
        lang: Language code (default: "en-US")
        timeout: Recording duration in seconds
    
    Returns:
        str: Recognized text in lowercase, or empty string on failure
    """
    recognizer = sr.Recognizer()
    samplerate = 16000
    
    print("🎙️ Listening...")
    
    try:
        # It will Capture audio using sounddevice
        audio_data = sd.rec(
            int(timeout * samplerate), 
            samplerate=samplerate, 
            channels=1, 
            dtype='int16'
        )
        sd.wait()  # It will Wait for recording to complete
        
        # Convert to format expected by speech_recognition
        audio_np = np.squeeze(audio_data)
        audio = sr.AudioData(audio_np.tobytes(), samplerate, 2)
        
        # It will Try English language  first
        try:
            text_en = recognizer.recognize_google(audio, language="en-US")
            print(f" English Detected: {text_en}")
            return text_en.lower()
        except sr.UnknownValueError:
            # Ifenglish is not detected then it will Fallback to Urdu
            try:
                text_ur = recognizer.recognize_google(audio, language="ur-PK")
                print(f"🗣️ Urdu Detected: {text_ur}")
                return text_ur.lower()
            except sr.UnknownValueError:
                print("Could not understand audio.")
                return ""
            except Exception as e:
                print(f" Urdu recognition error: {e}")
                return ""
                
    except Exception as e:
        print(f"⚠️ Microphone Error: {e}")
        return ""


def test_microphone():
    """Test function to verify microphone is working"""
    print("=" * 60)
    print("Testing Microphone")
    print("=" * 60)
    print("Please say something...")
    
    text = recognize_speech()
    
    if text:
        print(f" Success! Recognized: '{text}'")
    else:
        print(" No speech detected or failed to recognize")
    
    print("=" * 60)
    return text


if __name__ == "__main__":
    # Run test when executed directly
    print("\n🔧 Speech Recognition Module Test\n")
    
    # Test 1: it will test the basic commands of the system like capture image
    print("Test 1: Say 'capture image' or 'exit'")
    result1 = test_microphone()
    
    time.sleep(1)
    
    # Test 2: it will test the Urdu speech  recognition
    print("\nTest 2: Say 'tasveer lo' or 'band karo' (Urdu)")
    result2 = test_microphone()
    
    print("\n✅ Testing complete!")
