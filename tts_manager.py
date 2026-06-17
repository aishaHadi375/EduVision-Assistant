# ============ WINDOWS-COMPATIBLE TTS (tts_manager.py) ============
"""
✅ FIXED for Windows: Reinitialize engine between speeches
pyttsx3 has a known bug where runAndWait() hangs after first call
"""

import pyttsx3
import time
import sys


class TTSManager:
    """
    Windows-compatible TTS with engine reinitialization
    ✅ Prevents freeze after first speech
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        
        self._initialized = True
        self.rate = 150
        self.volume = 0.9
        self.engine = None
        self.speech_count = 0
        
        # Test if TTS works
        try:
            test_engine = pyttsx3.init()
            test_engine.setProperty('rate', self.rate)
            test_engine.stop()
            del test_engine
            print("✅ TTS available")
            self.available = True
        except Exception as e:
            print(f"❌ TTS init failed: {e}")
            self.available = False
    
    def _create_engine(self):
        """
        ✅ KEY FIX: Create fresh engine for each speech
        Prevents Windows freeze bug
        """
        try:
            engine = pyttsx3.init()
            engine.setProperty('rate', self.rate)
            engine.setProperty('volume', self.volume)
            return engine
        except Exception as e:
            print(f"❌ Engine creation failed: {e}")
            return None
    
    def speak(self, text, prepare=True):
        """
        Speak with fresh engine each time
        ✅ Windows-compatible
        """
        if not self.available or not text:
            return False
        
        try:
            start_time = time.time()
            
            # Clean text
            if prepare:
                text = self._prepare_for_speech(text)
            
            # Limit length
            if len(text) > 500:
                text = text[:497] + "..."
            
            print(f"\n🔊 Speaking: {text[:60]}...")
            
            # ✅ Create NEW engine for this speech
            engine = self._create_engine()
            if not engine:
                return False
            
            # Speak
            engine.say(text)
            engine.runAndWait()
            
            # ✅ CRITICAL: Destroy engine after use
            engine.stop()
            del engine
            
            elapsed = time.time() - start_time
            self.speech_count += 1
            print(f"✅ Completed in {elapsed:.2f}s (total speeches: {self.speech_count})")
            
            # Small delay between speeches
            time.sleep(0.2)
            
            return True
            
        except Exception as e:
            print(f"❌ Speech error: {e}")
            # Clean up
            try:
                if 'engine' in locals():
                    engine.stop()
                    del engine
            except:
                pass
            return False
    
    def speak_chunks(self, text, chunk_size=100):
        """
        Speak long text in chunks
        Each chunk gets its own engine
        """
        if not text:
            return
        
        import re
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        current_chunk = ""
        chunks_spoken = 0
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) < chunk_size:
                current_chunk += sentence + " "
            else:
                if current_chunk.strip():
                    self.speak(current_chunk.strip(), prepare=True)
                    chunks_spoken += 1
                current_chunk = sentence + " "
        
        # Speak remaining
        if current_chunk.strip():
            self.speak(current_chunk.strip(), prepare=True)
            chunks_spoken += 1
        
        print(f"✅ Spoke {chunks_spoken} chunks")
    
    def _prepare_for_speech(self, text):
        """Convert math symbols to words"""
        replacements = {
            '**': ' to the power of ',
            '^': ' to the power of ',
            '*': ' times ',
            '×': ' times ',
            '÷': ' divided by ',
            '∫': ' integral of ',
            '∂': ' partial derivative of ',
            '∑': ' sum of ',
            'dx': ' dee x ',
            'dy': ' dee y ',
            'dt': ' dee t ',
            'sqrt': ' square root of ',
            '√': ' square root of ',
            '²': ' squared ',
            '³': ' cubed ',
            '=': ' equals ',
            '≈': ' approximately equals ',
            '≠': ' not equals ',
            '≤': ' less than or equal to ',
            '≥': ' greater than or equal to ',
            '<': ' less than ',
            '>': ' greater than ',
            '+': ' plus ',
            '−': ' minus ',
            '-': ' minus ',
            '/': ' divided by ',
            '\\': ' ',
            '(': ' ',
            ')': ' ',
        }
        
        speech = str(text)
        for symbol, word in replacements.items():
            speech = speech.replace(symbol, word)
        
        # Clean whitespace
        speech = ' '.join(speech.split())
        
        return speech
    
    def is_available(self):
        return self.available
    
    def test(self):
        """Test with multiple speeches"""
        print("\n" + "="*60)
        print("🧪 Testing TTS with multiple messages")
        print("="*60)
        
        test_phrases = [
            "First message: Testing text to speech",
            "Second message: The integral of x squared equals x cubed over 3",
            "Third message: Two plus two equals four"
        ]
        
        for i, phrase in enumerate(test_phrases, 1):
            print(f"\n--- Test {i}/3 ---")
            success = self.speak(phrase)
            
            if success:
                print(f"✅ Test {i} passed")
            else:
                print(f"❌ Test {i} FAILED - Stopping tests")
                return False
            
            # Pause between tests
            if i < len(test_phrases):
                print("⏳ Waiting 0.5s before next test...")
                time.sleep(0.5)
        
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED!")
        print("="*60)
        return True

# ============ IMMEDIATE TEST ============
if __name__ == "__main__":
    print("Starting TTS test...")
    print("You should hear 3 messages in sequence.\n")
    
    tts = TTSManager()
    
    if not tts.is_available():
        print("❌ TTS not available on this system")
        print("Check that you have audio output working")
        sys.exit(1)
    
    # Run full test
    success = tts.test()
    
    if success:
        print("\n✅ TTS is working perfectly!")
        print("You can now use it in your main application.")
    else:
        print("\n❌ TTS test failed")
        print("\nTroubleshooting:")
        print("1. Check your speakers/headphones")
        print("2. Try: pip install --upgrade pyttsx3")
        print("3. Try: pip install pywin32 --upgrade")
        sys.exit(1)


