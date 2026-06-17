# ======================== FINAL CODE WITH FULL FUNCTIONALITY =======================

import streamlit as st
import cv2
import tempfile
import time
import os
import sys
from datetime import datetime
from PIL import Image
import threading

# Import your modules
from caption_module import generate_caption_and_speak
from math_solver import MathSolver
from Image_classifier import ImageClassifier
from tts_manager import TTSManager
from stt_module import recognize_speech

# ====================== PAGE CONFIG ======================
st.set_page_config(
    page_title="Educational Vision Assistant",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ====================== DARK BLUE THEME CSS WITH SMALLER TEXT ======================
st.markdown("""
<style>
    /* Dark Blue Theme */
    .main {
        background-color: #0a0e27;
        color: #ffffff;
    }
    
    .stApp {
        background-color: #0a0e27;
    }
    
    /* Header Styling - REDUCED SIZE */
    .main-header {
        font-size: 2.2rem;
        font-weight: bold;
        text-align: center;
        padding: 1.8rem;
        background: linear-gradient(135deg, #1e3a8a 0%, #1e40af 50%, #2563eb 100%);
        border-radius: 20px;
        color: white;
        margin-bottom: 1.5rem;
        box-shadow: 0 8px 16px rgba(30, 58, 138, 0.4);
        border: 2px solid #3b82f6;
    }
    
    /* Subtitle - REDUCED SIZE */
    .subtitle {
        text-align: center;
        font-size: 1rem;
        color: #ffffff;
        margin-bottom: 1.5rem;
        padding: 1rem;
        background-color: #000000;
        border-radius: 15px;
        border: 2px solid #1e40af;
    }
    
    /* Stats Box - REDUCED SIZE */
    .stat-box {
        background: #000000;
        padding: 1rem;
        border-radius: 15px;
        border: 2px solid #1e40af;
        margin: 0.8rem 0;
        box-shadow: 0 4px 8px rgba(30, 64, 175, 0.3);
    }
    
    .stat-label {
        color: #93c5fd;
        font-size: 0.85rem;
        margin-bottom: 0.3rem;
        font-weight: 600;
    }
    
    .stat-value {
        color: #3b82f6;
        font-size: 1.8rem;
        font-weight: bold;
    }
    
    /* Success Box - REDUCED SIZE */
    .success-box {
        background: #000000;
        border: 2px solid #22c55e;
        padding: 1.2rem;
        border-radius: 15px;
        margin: 0.8rem 0;
        box-shadow: 0 4px 8px rgba(34, 197, 94, 0.3);
    }
    
    .success-box h2 {
        font-size: 1.3rem;
        margin-bottom: 0.5rem;
    }
    
    .success-box h1 {
        font-size: 1.8rem;
        margin-top: 0.5rem;
    }
    
    /* Error Box - REDUCED SIZE */
    .error-box {
        background: #000000;
        border: 2px solid #ef4444;
        padding: 1.2rem;
        border-radius: 15px;
        margin: 0.8rem 0;
        box-shadow: 0 4px 8px rgba(239, 68, 68, 0.3);
    }
    
    /* Warning Box - REDUCED SIZE */
    .warning-box {
        background: #000000;
        border: 2px solid #f59e0b;
        padding: 1.2rem;
        border-radius: 15px;
        margin: 0.8rem 0;
        box-shadow: 0 4px 8px rgba(245, 158, 11, 0.3);
    }
    
    /* Info Box - REDUCED SIZE */
    .info-box {
        background: #000000;
        border: 2px solid #3b82f6;
        padding: 1.2rem;
        border-radius: 15px;
        margin: 0.8rem 0;
        box-shadow: 0 4px 8px rgba(59, 130, 246, 0.3);
        text-align: center;
    }
    
    .info-box h3 {
        font-size: 1.2rem;
        margin: 0;
    }
    
    /* Listening Mode Box - REDUCED SIZE */
    .listening-box {
        background: linear-gradient(135deg, #1e3a8a 0%, #1e40af 100%);
        border: 3px solid #3b82f6;
        padding: 2rem;
        border-radius: 20px;
        margin: 1.5rem 0;
        text-align: center;
        animation: glow 2s infinite;
    }
    
    .listening-box h1 {
        font-size: 1.8rem;
        margin-top: 0.8rem;
    }
    
    .listening-box p {
        font-size: 1rem;
    }
    
    @keyframes glow {
        0%, 100% { box-shadow: 0 0 20px rgba(59, 130, 246, 0.5); }
        50% { box-shadow: 0 0 40px rgba(59, 130, 246, 0.8); }
    }
    
    /* Button Styling - REDUCED SIZE */
    .stButton>button {
        width: 100%;
        height: 3.2rem;
        font-size: 1.1rem;
        font-weight: bold;
        border-radius: 15px;
        background: linear-gradient(135deg, #1e3a8a 0%, #2563eb 100%);
        color: white;
        border: 2px solid #3b82f6;
        box-shadow: 0 6px 12px rgba(30, 58, 138, 0.4);
        transition: all 0.3s;
    }
    
    .stButton>button:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 16px rgba(59, 130, 246, 0.6);
        background: linear-gradient(135deg, #2563eb 0%, #3b82f6 100%);
    }
    
    /* Countdown Display - REDUCED SIZE */
    .countdown {
        font-size: 4rem;
        font-weight: bold;
        text-align: center;
        color: #3b82f6;
        text-shadow: 0 0 30px rgba(59, 130, 246, 0.8);
        animation: pulse 1s infinite;
        margin: 1.5rem 0;
    }
    
    @keyframes pulse {
        0%, 100% { 
            opacity: 1;
            transform: scale(1);
        }
        50% { 
            opacity: 0.7;
            transform: scale(1.15);
        }
    }
    
    /* History Item - REDUCED SIZE */
    .history-item {
        background-color: #000000;
        padding: 1.2rem;
        border-radius: 15px;
        margin: 0.8rem 0;
        border: 2px solid #1e40af;
        box-shadow: 0 4px 8px rgba(30, 64, 175, 0.3);
    }
    
    .history-item h4 {
        font-size: 1rem;
        margin-bottom: 0.5rem;
    }
    
    .history-item p {
        font-size: 0.95rem;
    }
    
    /* Microphone Icon - REDUCED SIZE */
    .mic-icon {
        font-size: 3.5rem;
        animation: pulse 1.5s infinite;
    }
    
    /* Exit Box */
    .exit-box {
        background: linear-gradient(135deg, #dc2626 0%, #ef4444 100%);
        border: 3px solid #f87171;
        padding: 2rem;
        border-radius: 20px;
        margin: 1.5rem 0;
        text-align: center;
        animation: glow-red 2s infinite;
    }
    
    @keyframes glow-red {
        0%, 100% { box-shadow: 0 0 20px rgba(239, 68, 68, 0.5); }
        50% { box-shadow: 0 0 40px rgba(239, 68, 68, 0.8); }
    }
    
    /* Video Container */
    .video-container {
        background-color: #000000;
        border: 3px solid #1e40af;
        border-radius: 15px;
        padding: 20px;
        margin: 20px 0;
    }
    
    /* Footer - REDUCED SIZE */
    .footer {
        text-align: center;
        color: #93c5fd;
        padding: 1.5rem;
        margin-top: 2rem;
        border-top: 2px solid #1e40af;
        font-size: 0.9rem;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #000000;
        border-right: 2px solid #1e40af;
    }
    
    /* Make all text white/light and smaller */
    .stMarkdown, p, span, div {
        color: #ffffff;
        font-size: 0.95rem;
    }
    
    /* Reduce heading sizes */
    h1 { font-size: 1.8rem; }
    h2 { font-size: 1.5rem; }
    h3 { font-size: 1.2rem; }
    h4 { font-size: 1rem; }
</style>
""", unsafe_allow_html=True)

# ====================== SESSION STATE INITIALIZATION ======================
def init_session_state():
    """Initialize all session state variables"""
    if 'stats' not in st.session_state:
        st.session_state.stats = {
            'images_captured': 0,
            'math_solved': 0,
            'diagrams_described': 0,
            'errors': 0
        }
    
    if 'history' not in st.session_state:
        st.session_state.history = []
    
    if 'classifier' not in st.session_state:
        st.session_state.classifier = None
    
    if 'math_solver' not in st.session_state:
        st.session_state.math_solver = None
    
    if 'tts' not in st.session_state:
        st.session_state.tts = TTSManager()
    
    if 'audio_enabled' not in st.session_state:
        st.session_state.audio_enabled = True
    
    if 'initialized' not in st.session_state:
        st.session_state.initialized = False
    
    if 'listening_mode' not in st.session_state:
        st.session_state.listening_mode = False
    
    if 'last_command' not in st.session_state:
        st.session_state.last_command = ""
    
    if 'auto_listen' not in st.session_state:
        st.session_state.auto_listen = True  # Auto-start listening
    
    if 'exit_requested' not in st.session_state:
        st.session_state.exit_requested = False

# ====================== TTS HELPER ======================
def speak(text):
    """Speak text to user"""
    if st.session_state.tts and st.session_state.tts.is_available():
        if st.session_state.get('audio_enabled', True):
            st.session_state.tts.speak(text, prepare=True)

# ====================== AUTO MODEL LOADING ======================
def auto_load_models():
    """Automatically load AI models on startup"""
    if not st.session_state.initialized:
        with st.spinner("🔄 Initializing system... Please wait..."):
            speak("Initializing Educational Vision Assistant. Please wait.")
            
            classifier = None
            math_solver = None
            
            # Load Classifier
            try:
                classifier = ImageClassifier()
                if classifier.is_available():
                    st.success("✅ Image Classifier loaded")
                else:
                    st.warning("⚠️ Image classifier not available")
            except Exception as e:
                st.error(f"❌ Classifier error: {e}")
            
            # Load Math Solver
            try:
                math_solver = MathSolver()
                st.success("✅ Math Solver loaded")
            except Exception as e:
                st.error(f"❌ Math Solver error: {e}")
            
            # Save to session state
            st.session_state.classifier = classifier
            st.session_state.math_solver = math_solver
            st.session_state.initialized = True
            
            # Auto-start listening after initialization
            st.session_state.auto_listen = True
            st.session_state.listening_mode = True
            
            # Inform user
            speak("System initialized successfully. Starting listening mode. Say capture image to begin, or exit to close the application.")
            st.success("✅ System Ready! Listening mode activated automatically")
            
            time.sleep(1)

# ====================== EXIT APPLICATION ======================
def exit_application():
    """Gracefully exit the application"""
    st.session_state.exit_requested = True
    speak("Closing Educational Vision Assistant. Goodbye!")
    
    st.markdown("""
    <div class="exit-box">
        <h1 style="color: white; margin-top: 0.8rem;">👋 Application Closing</h1>
        <p style="color: #fecaca; font-size: 1rem;">Thank you for using Educational Vision Assistant</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Add delay to allow voice message to play
    time.sleep(3)
    
    # Stop the Streamlit server
    st.stop()

# ====================== IMAGE CAPTURE WITH COUNTDOWN ======================
def capture_image_with_countdown(timeout=10):
    """
    Capture image with automatic countdown
    
    Args:
        timeout: Countdown duration
    
    Returns:
        str: Path to captured image or None
    """
    speak(f"Opening camera. Image will be captured automatically in {timeout} seconds.")
    
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        speak("Error. Cannot access camera.")
        st.error("❌ Cannot access webcam")
        return None
    
    # Create placeholders for live feed and countdown
    video_placeholder = st.empty()
    countdown_placeholder = st.empty()
    
    start_time = time.time()
    captured_frame = None
    
    # Countdown tracking for voice feedback
    countdown_spoken = {10: False, 5: False, 3: False, 2: False, 1: False}
    
    while True:
        ret, frame = cap.read()
        if not ret:
            speak("Error. Failed to capture from camera.")
            break
        
        elapsed = time.time() - start_time
        remaining = int(timeout - elapsed)
        
        # Voice countdown at key moments
        if st.session_state.audio_enabled and remaining > 0:
            if remaining == 10 and not countdown_spoken[10]:
                speak("10 seconds")
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
        
        # Add countdown overlay on video
        display_frame = frame.copy()
        cv2.putText(display_frame, f"Capturing in: {remaining}s", 
                   (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (59, 130, 246), 3)
        
        # Convert BGR to RGB for Streamlit
        display_frame_rgb = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
        video_placeholder.image(display_frame_rgb, channels="RGB", use_container_width=True)
        
        # Show countdown number
        if remaining > 0:
            countdown_placeholder.markdown(
                f'<div class="countdown">{remaining}</div>', 
                unsafe_allow_html=True
            )
        
        # Auto-capture after timeout
        if elapsed >= timeout:
            captured_frame = frame
            speak("Image captured successfully.")
            break
        
        time.sleep(0.1)
    
    # Cleanup
    cap.release()
    video_placeholder.empty()
    countdown_placeholder.empty()
    
    if captured_frame is not None:
        # Save captured image
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_file:
            cv2.imwrite(tmp_file.name, captured_frame)
            return tmp_file.name
    
    return None

# ====================== IMAGE PROCESSING ======================
def process_image(image_path):
    """Process captured/uploaded image with voice feedback"""
    if not os.path.exists(image_path):
        speak("Error. Image file not found.")
        st.error("❌ Image file not found")
        st.session_state.stats['errors'] += 1
        return False
    
    st.session_state.stats['images_captured'] += 1
    
    try:
        # Show image
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown('<div class="info-box"><h3>📸 Captured Image</h3></div>', 
                       unsafe_allow_html=True)
            st.image(image_path, use_container_width=True)
        
        with col2:
            # Classify image
            with st.spinner("🔍 Analyzing image type..."):
                speak("Analyzing image.")
                
                if st.session_state.classifier and st.session_state.classifier.is_available():
                    image_type = st.session_state.classifier.classify_image(
                        image_path, 
                        confidence_threshold=0.70
                    )
                else:
                    image_type = 'diagram'
            
            # Route to appropriate processor
            if image_type == 'math':
                st.markdown('<div class="info-box"><h3>🔢 Math Problem Detected</h3></div>', 
                           unsafe_allow_html=True)
                speak("Math problem detected.")
                result = process_math(image_path)
            else:
                st.markdown('<div class="info-box"><h3>🖼️ Diagram/Image Detected</h3></div>', 
                           unsafe_allow_html=True)
                speak("Diagram or image detected.")
                result = process_diagram(image_path)
            
            # Add to history
            if result:
                history_entry = {
                    'timestamp': datetime.now(),
                    'type': image_type,
                    'image_path': image_path,
                    'result': result
                }
                st.session_state.history.insert(0, history_entry)
        
        return result
        
    except Exception as e:
        speak("Error occurred while processing image.")
        st.error(f"❌ Processing error: {e}")
        st.session_state.stats['errors'] += 1
        return False

def process_math(image_path):
    """Process math problem with voice feedback"""
    if st.session_state.math_solver is None:
        speak("Math solver not available. Switching to diagram description.")
        return process_diagram(image_path)
    
    try:
        with st.spinner("🧮 Solving math problem..."):
            result = st.session_state.math_solver.solve_from_image(
                image_path, 
                use_tts=st.session_state.audio_enabled,
                use_ai_explanation=True
            )
            
            if result is not None:
                st.session_state.stats['math_solved'] += 1
                
                st.markdown(f"""
                <div class="success-box">
                    <h2 style="color: #22c55e;">✅ Solution Complete!</h2>
                    <h1 style="color: #3b82f6; margin-top: 0.5rem;">Answer: {result}</h1>
                </div>
                """, unsafe_allow_html=True)
                
                return str(result)
            else:
                speak("Could not solve. Trying diagram description.")
                return process_diagram(image_path)
                
    except Exception as e:
        speak("Math solving failed.")
        st.error(f"❌ Error: {e}")
        return process_diagram(image_path)

def process_diagram(image_path):
    """Process diagram/image with voice feedback"""
    try:
        with st.spinner("🖼️ Generating description..."):
            caption = generate_caption_and_speak(image_path)
            
            if caption:
                st.session_state.stats['diagrams_described'] += 1
                
                st.markdown(f"""
                <div class="success-box">
                    <h2 style="color: #22c55e;">✅ Description Generated</h2>
                    <p style="color: #ffffff; font-size: 1rem; margin-top: 0.8rem; line-height: 1.6;">{caption}</p>
                </div>
                """, unsafe_allow_html=True)
                
                return caption
            else:
                speak("Could not generate description.")
                st.error("❌ Description failed")
                st.session_state.stats['errors'] += 1
                return None
                
    except Exception as e:
        speak("Description generation failed.")
        st.error(f"❌ Error: {e}")
        st.session_state.stats['errors'] += 1
        return None

# ====================== VOICE COMMAND PROCESSING ======================
def process_voice_command():
    """Listen for voice command and execute"""
    st.markdown("""
    <div class="listening-box">
        <div class="mic-icon">🎤</div>
        <h1 style="color: white; margin-top: 0.8rem;">Listening...</h1>
        <p style="color: #93c5fd; font-size: 1rem;">Say "capture image" or "exit" to close</p>
    </div>
    """, unsafe_allow_html=True)
    
    speak("Listening for your command.")
    
    # Get voice input
    command = recognize_speech()
    
    if command:
        st.session_state.last_command = command
        st.success(f"✅ You said: '{command}'")
        
        # Process command
        command_lower = command.lower()
        
        if "capture" in command_lower or "tasveer" in command_lower or "image" in command_lower:
            speak("Capturing image now.")
            image_path = capture_image_with_countdown(timeout=10)
            
            if image_path:
                process_image(image_path)
            else:
                speak("Image capture failed.")
                st.error("❌ Capture failed")
                st.session_state.stats['errors'] += 1
        
        elif "exit" in command_lower or "quit" in command_lower or "close" in command_lower or "stop" in command_lower:
            speak("Exit command received. Closing application.")
            exit_application()
            return
        
        elif "stats" in command_lower or "statistics" in command_lower:
            speak_stats()
        
        elif "history" in command_lower:
            speak("Showing history.")
            st.info("📜 Check the History tab below")
        
        else:
            speak("Command not recognized. Please say capture image, stats, history, or exit.")
            st.warning("⚠️ Command not recognized")
            
        # Auto-restart listening after command processing (except exit)
        if not st.session_state.exit_requested:
            st.session_state.listening_mode = True
            st.rerun()
    else:
        speak("No speech detected. Please try again.")
        st.warning("⚠️ No speech detected")
        # Auto-restart listening
        st.session_state.listening_mode = True
        st.rerun()

def speak_stats():
    """Speak current statistics"""
    stats = st.session_state.stats
    message = (f"Session statistics. Images captured: {stats['images_captured']}. "
               f"Math problems solved: {stats['math_solved']}. "
               f"Diagrams described: {stats['diagrams_described']}.")
    speak(message)

# ====================== STATISTICS DISPLAY ======================
def show_stats():
    """Display session statistics in sidebar"""
    st.sidebar.markdown("### 📊 Statistics")
    
    # Calculate success rate
    success_rate = 0
    if st.session_state.stats['images_captured'] > 0:
        successes = (st.session_state.stats['math_solved'] + 
                    st.session_state.stats['diagrams_described'])
        success_rate = (successes / st.session_state.stats['images_captured']) * 100
    
    # Display stats
    col1, col2 = st.sidebar.columns(2)
    
    with col1:
        st.markdown(f"""
        <div class="stat-box">
            <div class="stat-label">Images</div>
            <div class="stat-value">{st.session_state.stats['images_captured']}</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class="stat-box">
            <div class="stat-label">Math</div>
            <div class="stat-value">{st.session_state.stats['math_solved']}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="stat-box">
            <div class="stat-label">Diagrams</div>
            <div class="stat-value">{st.session_state.stats['diagrams_described']}</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class="stat-box">
            <div class="stat-label">Success</div>
            <div class="stat-value">{success_rate:.0f}%</div>
        </div>
        """, unsafe_allow_html=True)

# ====================== MAIN APPLICATION ======================
def main():
    """Main Streamlit application"""
    
    # Initialize
    init_session_state()
    
    # Check if exit was requested
    if st.session_state.get('exit_requested', False):
        exit_application()
    
    # Header
    st.markdown('<div class="main-header">🎓 Educational Vision Assistant</div>', 
                unsafe_allow_html=True)
    
    st.markdown("""
    <div class="subtitle">
        🔊 <strong>Voice-Controlled System for Visually Impaired Students</strong><br>
        Auto-listening mode activated | Say "capture image" or "exit" to close
    </div>
    """, unsafe_allow_html=True)
    
    # Auto-load models on first run
    auto_load_models()
    
    # Sidebar
    with st.sidebar:
        st.markdown("### ⚙️ Controls")
        
        # System status
        if st.session_state.initialized:
            if st.session_state.listening_mode:
                status_text = "🎤 LISTENING MODE ACTIVE"
                status_color = "#22c55e"
            else:
                status_text = "✅ SYSTEM READY"
                status_color = "#3b82f6"
                
            st.markdown(f"""
            <div class="success-box" style="text-align: center;">
                <h3 style="color: {status_color};">{status_text}</h3>
                <p style="font-size: 0.85rem; color: #93c5fd;">Say 'exit' to close</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Audio toggle
        audio_enabled = st.checkbox(
            "🔊 Voice Feedback", 
            value=True,
            help="Enable/disable text-to-speech"
        )
        st.session_state.audio_enabled = audio_enabled
        
        st.markdown("---")
        show_stats()
        
        st.markdown("---")
        
        # Manual controls
        st.markdown("### 🎯 Manual Controls")
        
        if st.button("📸 Capture Image Now", use_container_width=True):
            speak("Manual capture initiated.")
            image_path = capture_image_with_countdown(timeout=10)
            if image_path:
                process_image(image_path)
        
        if st.button("🔄 Restart Listening", use_container_width=True):
            st.session_state.listening_mode = True
            st.rerun()
        
        if st.button("🔴 Exit Application", use_container_width=True):
            exit_application()
        
        st.markdown("---")
        
        # Reset button
        if st.button("🔄 Reset Stats"):
            st.session_state.stats = {
                'images_captured': 0,
                'math_solved': 0,
                'diagrams_described': 0,
                'errors': 0
            }
            speak("Statistics reset.")
            st.rerun()
    
    # Main content area
    if not st.session_state.initialized:
        st.markdown("""
        <div class="warning-box">
            <h2>⏳ Initializing System...</h2>
            <p>Please wait while we load the AI models</p>
        </div>
        """, unsafe_allow_html=True)
        return
    
    # Auto-start listening after initialization
    if st.session_state.initialized and st.session_state.auto_listen and not st.session_state.exit_requested:
        st.session_state.listening_mode = True
        st.session_state.auto_listen = False  # Only auto-start once
    
    # Show listening interface if activated
    if st.session_state.listening_mode and not st.session_state.exit_requested:
        process_voice_command()
    
    # Show last command
    if st.session_state.last_command:
        st.markdown(f"""
        <div class="info-box">
            <h3>Last Command: "{st.session_state.last_command}"</h3>
        </div>
        """, unsafe_allow_html=True)
    
    # History Section
    st.markdown("---")
    st.markdown("## 📜 Recent History")
    
    if not st.session_state.history:
        st.markdown("""
        <div class="info-box">
            <p>No history yet. Say "capture image" to get started!</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        for i, entry in enumerate(st.session_state.history[:3]):  # Show last 3
            with st.expander(
                f"🕐 {entry['timestamp'].strftime('%H:%M:%S')} - {entry['type'].upper()}",
                expanded=(i == 0)
            ):
                col1, col2 = st.columns([1, 2])
                
                with col1:
                    if os.path.exists(entry['image_path']):
                        st.image(entry['image_path'], use_container_width=True)
                
                with col2:
                    st.markdown(f"""
                    <div class="history-item">
                        <h4 style="color: #3b82f6;">Result:</h4>
                        <p style="color: #ffffff; font-size: 0.95rem;">{entry['result']}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if st.button(f"🔊 Speak", key=f"speak_{i}"):
                        speak(str(entry['result']))
    
    # Footer
    st.markdown("""
    <div class="footer">
        <p><strong>Educational Vision Assistant</strong></p>
        <p>🔊 Always listening | Say 'exit' to close | AI vision for education</p>
    </div>
    """, unsafe_allow_html=True)

# ====================== RUN APPLICATION ======================
if __name__ == "__main__":
    main()


