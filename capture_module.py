# ================= FINAL CODE WITH PROPER TTS===============
"""
Image Capture Module - This module willcapture an image from webcam using opencv whenever user said 
capture image comand.
It will also countdown through tts so that user will be awared of capture time that now my system 
will capture the image.

"""

import cv2
import time
from tts_manager import TTSManager


def capture_image(save_path="captured.jpg", timeout=10, show_window=True, use_audio=True):
    """
    Capture an image from the default webcam with audio guidance.
    
    Args:
        save_path: Path to save the captured image
        timeout: Seconds to wait before auto-capturing
        show_window: If False, don't attempt GUI window (headless mode)
        use_audio: If True, provide audio feedback during capture
    
    Returns:
        str: Path to saved image, or None on failure
    """
    
    # It will load  TTS Manager
    tts = TTSManager() if use_audio else None
    
    def speak(text):
        """Helper function for audio feedback"""
        if tts and tts.is_available():
            print(f"🔊 {text}")
            tts.speak(text, prepare=False)
    
    # It will Open camera
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("Cannot opened webcam.")
        speak("Error. Cannot opened camera.")
        return None
    
    print(f"📷 Camera opened. Press 'c' to capture or wait {timeout} seconds for auto-capture...")
    
    # It will Speak out the  initial instructions for the user
    speak(f"Camera ready. Press the letter C to capture now, or wait {timeout} seconds for automatic capture.")
    
    start_time = time.time()
    gui_desired = show_window
    countdown_spoken = {10: False, 5: False, 3: False, 2: False, 1: False}
    
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame.")
            speak("Error. Failed to capture from camera.")
            break
        
        elapsed = time.time() - start_time
        remaining = int(timeout - elapsed)
        
        # it will generate Audio  for countdown 
        if use_audio and remaining > 0:
            if remaining == 10 and not countdown_spoken[10]:
                speak("10 seconds remaining")
                countdown_spoken[10] = True
            elif remaining == 5 and not countdown_spoken[5]:
                speak("5 seconds")
                countdown_spoken[5] = True
            elif remaining == 3 and not countdown_spoken[3]:
                speak("3")
                countdown_spoken[3] = True
            elif remaining == 2 and not countdown_spoken[2]:
                speak("2")
                countdown_spoken[2] = True
            elif remaining == 1 and not countdown_spoken[1]:
                speak("1")
                countdown_spoken[1] = True
        
        # It will display the frame if GUI is available
        if gui_desired:
            try:
                # Add countdown overlay on video
                display_frame = frame.copy()
                text = f"Press 'C' to capture | Auto: {remaining}s"
                cv2.putText(display_frame, text, (10, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
                cv2.imshow("Live Feed - Edu Vision AI", display_frame)
            except cv2.error:
                print("⚠️ OpenCV built without GUI support. Using headless mode.")
                gui_desired = False
        
        # It will Manually capture an image whenever the user press 'c'.
        if gui_desired:
            key = cv2.waitKey(1) & 0xFF
            if key == ord('c') or key == ord('C'):
                cv2.imwrite(save_path, frame)
                print(f"✅ Image saved as {save_path}")
                speak("Image captured successfully.")
                break
        
        # Auto-capture after timeout
        if elapsed > timeout:
            cv2.imwrite(save_path, frame)
            print(f"✅ Image saved as {save_path} (auto-captured)")
            speak("Image captured automatically.")
            break
    
    # now it will release the camera and destroy all windows
    cap.release()
    if gui_desired:
        try:
            cv2.destroyAllWindows()
        except Exception:
            pass
    
    
    if use_audio:
        time.sleep(0.3)  
    
    return save_path


# ============ ALTERNATIVE: HEADLESS MODE WITH BETTER COUNTDOWN ============

def capture_image_headless(save_path="captured.jpg", countdown=5):
    """
    Simplified capture for environments without display.
    Perfect for blind users - audio-only interface.
    
    Args:
        save_path: Path to save the captured image
        countdown: Seconds to count down before capture
    
    Returns:
        str: Path to saved image, or None on failure
    """
    
    tts = TTSManager()
    
    def speak(text):
        if tts.is_available():
            print(f"🔊 {text}")
            tts.speak(text, prepare=False)
    
    # Open camera
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        speak("Error. Cannot access camera.")
        return None
    
    speak(f"Camera ready. Image will be captured in {countdown} seconds.")
    
    # Warm up camera
    for _ in range(5):
        cap.read()
        time.sleep(0.1)
    
    # It will generate Countdown
    for i in range(countdown, 0, -1):
        speak(str(i))
        time.sleep(1)
    
    # It will Capture the image
    ret, frame = cap.read()
    cap.release()
    
    if ret:
        cv2.imwrite(save_path, frame)
        print(f"✅ Image saved as {save_path}")
        speak("Image captured successfully.")
        return save_path
    else:
        speak("Error. Failed to capture image.")
        return None


# ============ TEST ============

if __name__ == "__main__":
    """Test the capture module"""
    print("=" * 60)
    print("📸 Testing Image Capture Module")
    print("=" * 60)
    print("\nChoose test mode:")
    print("1. Standard mode (with GUI and audio)")
    print("2. Headless mode (audio-only, auto countdown)")
    
    choice = input("\nEnter choice (1 or 2): ").strip()
    
    if choice == "2":
        print("\n🔊 Testing HEADLESS mode (audio-only)...")
        result = capture_image_headless("test_capture.jpg", countdown=5)
    else:
        print("\n🔊 Testing STANDARD mode...")
        result = capture_image("test_capture.jpg", timeout=10, use_audio=True)
    
    if result:
        print(f"\n✅ Test successful! Image saved to: {result}")
    else:
        print("\n❌ Test failed!")