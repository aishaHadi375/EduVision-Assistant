#  =========================  FinalCode ===========================
"""
Caption Module - This is the module for generating image descriptions using gemini Flash model.
"""

import os
from PIL import Image
from dotenv import load_dotenv
import google.generativeai as genai
from tts_manager import TTSManager

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


class ProductionImageTutor:
    
    def __init__(self, gemini_api_key=None, gemini_model=None):
        self.gemini_api_key = gemini_api_key or GEMINI_API_KEY
        
        # We are using the gemini 2.5 model as default one
        default_model = "gemini-2.5-flash"
        self.gemini_model = (gemini_model or default_model).strip()
        if self.gemini_model.startswith("models/"):
            self.gemini_model = self.gemini_model.split("/", 1)[1]

        # this line will initiliaze  TTSManager for speech
        self.tts = TTSManager()
        
        # Check if API key is available
        self.gemini_available = self.gemini_api_key is not None

    def _load_image(self, path):
        """ This will Load an image from file path"""
        try:
            return Image.open(path)
        except Exception as e:
            print(f"⚠️ Error loading image: {e}")
            return None

    def _explain_with_gemini(self, image):
        """ Now we will use Gemini API to Generate explanation for the image"""
        try:
            if not self.gemini_api_key:
                raise ValueError("Missing GEMINI_API_KEY in .env")

            genai.configure(api_key=self.gemini_api_key)

            prompt = (
                "You are a kind educational tutor for blind students. "
                "Describe the image clearly and simply in natural spoken language. "
                "Keep it under 200 words for better comprehension."
            )

            model = genai.GenerativeModel(self.gemini_model)
            response = model.generate_content([prompt, image])

            explanation = response.text.strip() if hasattr(response, "text") else None
            
            if not explanation:
                return None

            return explanation

        except Exception as e:
            print(f"⚠️ Gemini error: {e}")
            return None

    def explain_image(self, image_path):
        """Generate explanation for an image"""
        image = self._load_image(image_path)
        if image is None:
            return None

        return self._explain_with_gemini(image)

    def speak(self, text):
        
        # Now we will use TTSManager for speaking the results aloud
        
        if self.tts.is_available():
            # we will chunked speech for long descriptions 
            if len(text) > 200:
                self.tts.speak_chunks(text, chunk_size=150)
            else:
                self.tts.speak(text, prepare=False)  

    def generate_caption_and_speak(self, image_path):
        """It will generate description and then speak it aloud
          so that blind user can understand it easily
        """
        explanation = self.explain_image(image_path)
        if explanation:
            print(f"📝 Description: {explanation}")
            self.speak(explanation)
        else:
            error_msg = "Could not generate description for this image"
            print(f"⚠️ {error_msg}")
            self.speak(error_msg)
        
        return explanation



tutor = ProductionImageTutor()

def generate_caption_and_speak(image_path):
    """Convenience function for generating captions"""
    return tutor.generate_caption_and_speak(image_path)