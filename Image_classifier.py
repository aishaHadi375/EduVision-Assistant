# ======================== Final Code   =====================

"""
Image Classifier 
It Uses a single CLIP inference for accurate score comparison (Math vs. Diagram)
Retains improved prompts and higher confidence threshold
 Reduced false positives by requiring a clear winner (confidence gap)
"""

import os
from PIL import Image
import torch
from transformers import CLIPProcessor, CLIPModel

print("🧠 Initializing Enhanced CLIP Classifier (Accurate Scoring)...")

class ImageClassifier:
    """Smart classifier with improved and accurate scoring logic."""
    
    def __init__(self, use_gpu=False):
        """Initialize with better settings and CLIP model."""
        print("📦 Loading CLIP model...")
        
        try:
            # It will use the Clip model
            self.model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
            self.processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
            
            self.device = "cuda" if use_gpu and torch.cuda.is_available() else "cpu"
            self.model.to(self.device)
            
            self.available = True
            print(f"✅ CLIP initialized on {self.device.upper()}")
            
        except Exception as e:
            print(f" CLIP failed to load: {e}")
            # Ensure the required libraries are installed if this fails
            print(" Try: pip install transformers torch pillow")
            self.available = False

    # --- PROMTS DEFINITION ---
    # it will Define the prompt for each class like for image as well as for math problem.
    MATH_DESCRIPTIONS = [
        "a handwritten mathematical equation with numbers, variables, operators, equals signs, and mathematical symbols like x, y, plus, minus, multiply, divide",
        "a printed mathematical formula with algebraic expressions, calculus notation, integrals, derivatives, or equations to solve",
        "a math problem written on paper or whiteboard showing arithmetic, algebra, geometry calculations, or mathematical work",
        "a scientific or engineering diagram primarily composed of formulas and mathematical symbols"
    ]
    
    DIAGRAM_DESCRIPTIONS = [
        "an educational diagram, illustration, or photograph showing biological structures, anatomical parts, or scientific concepts",
        "a labeled scientific diagram with arrows, text labels, and visual explanations of natural phenomena or processes",
        "a picture, drawing, or image depicting real-world objects, animals, plants, body parts, or educational illustrations",
        "a flowchart, bar chart, graph, or schematic drawing"
    ]
    # --------------------------

    def classify_image(self, image_path, confidence_threshold=0.70):
        """
        Enhanced classification using single-pass scoring for accuracy.
        
        Args:
            image_path: Path to image
            confidence_threshold: Minimum confidence for the chosen category (default: 0.70)
        
        Returns:
            'math' or 'diagram'
        """
        if not self.available:
            print("CLIP model is unavailable, defaulting to 'diagram'")
            return 'diagram'
        
        try:
            image = Image.open(image_path).convert("RGB")
            
            # We combine *all* text prompts into a single list so everything is scored
            # together in one pass. This makes the probabilities directly comparable.
            all_descriptions = self.MATH_DESCRIPTIONS + self.DIAGRAM_DESCRIPTIONS
            math_count = len(self.MATH_DESCRIPTIONS)
            
            # The image is compared against every description at once
            inputs = self.processor(
                text=all_descriptions,
                images=image,
                return_tensors="pt",
                padding=True
            ).to(self.device)
            
            with torch.no_grad():
                outputs = self.model(**inputs)
                logits_per_image = outputs.logits_per_image
                # Apply softmax across *all* descriptions so probabilities add up to 1
                probs = logits_per_image.softmax(dim=1)[0] # [0] for the first (and only) image

            # 1. Sum probabilities for the Math Category
            # This is the sum of probabilities for the first 'math_count' prompts
            math_score = probs[:math_count].sum().item()
            
            # 2. Sum probabilities for the Diagram Category
            # This is the sum of probabilities for the rest of the prompts
            diagram_score = probs[math_count:].sum().item()
            
            # Since the total probability sums to 1, these scores are directly comparable!

            print(f"📊 Classification Scores (Summed Probabilities):")
            print(f"   Math: {math_score:.2%}")
            print(f"   Diagram: {diagram_score:.2%}")
            
            # ✅ Stricter comparison logic
            confidence_gap = 0.15  # Math must be 15% higher to classify as math
            
            if math_score > diagram_score + confidence_gap and math_score >= confidence_threshold:
                classification = 'math'
                confidence = math_score
            else:
                # Default to diagram (safer for blind users and less confident results)
                classification = 'diagram'
                confidence = diagram_score
            
            print(f"✓ Classified as: {classification.upper()} (confidence: {confidence:.2%})")
            
            # ✅ Warn if confidence is low (using a combined confidence metric)
            if max(math_score, diagram_score) < 0.6:
                print(f"⚠️ Low overall confidence - defaulting to 'diagram' for safety")
                return 'diagram'
            
            return classification
                
        except Exception as e:
            print(f"⚠️ Classification error: {e}")
            return 'diagram' # Safe default

    # The helper method _test_category is now redundant and can be removed, 
    # but we'll keep the classify_with_details method for debug.

    def classify_with_details(self, image_path):
        """
        Get detailed classification information using the accurate single-pass logic.
        
        Returns:
            dict with classification, confidences, and recommendations
        """
        if not self.available:
            return {
                'classification': 'diagram',
                'math_confidence': 0.5,
                'diagram_confidence': 0.5,
                'recommendation': 'CLIP unavailable - defaulting to diagram'
            }
        
        try:
            image = Image.open(image_path).convert("RGB")
            
            all_descriptions = self.MATH_DESCRIPTIONS + self.DIAGRAM_DESCRIPTIONS
            math_count = len(self.MATH_DESCRIPTIONS)

            # --- Single Inference Pass ---
            inputs = self.processor(
                text=all_descriptions,
                images=image,
                return_tensors="pt",
                padding=True
            ).to(self.device)
            
            with torch.no_grad():
                outputs = self.model(**inputs)
                logits_per_image = outputs.logits_per_image
                probs = logits_per_image.softmax(dim=1)[0]

            math_score = probs[:math_count].sum().item()
            diagram_score = probs[math_count:].sum().item()
            
            confidence_gap = 0.15
            
            if math_score > diagram_score + confidence_gap:
                classification = 'math'
                confidence = math_score
            else:
                classification = 'diagram'
                confidence = diagram_score
            
            # Generate recommendation
            if confidence > 0.8:
                recommendation = f"High confidence ({confidence:.2%}) - definitely {classification}"
            elif confidence > 0.65:
                recommendation = f"Good confidence ({confidence:.2%}) - likely {classification}"
            else:
                recommendation = f"Low confidence ({confidence:.2%}) - uncertain, defaulting to {classification}"
            
            return {
                'classification': classification,
                'math_confidence': math_score,
                'diagram_confidence': diagram_score,
                'confidence': confidence,
                'recommendation': recommendation
            }
            
        except Exception as e:
            return {
                'classification': 'diagram',
                'math_confidence': 0.5,
                'diagram_confidence': 0.5,
                'recommendation': f'Error during detailed classification: {e}'
            }
    
    def is_available(self):
        """Check if classifier is ready"""
        return self.available


# ============ DEBUG/TESTING FUNCTIONS ============

def classify_with_debug(classifier, image_path):
    """Helper function to debug classification"""
    if not os.path.exists(image_path):
        print(f"⚠️ Test image not found at: {image_path}")
        return 'diagram'
        
    print("\n" + "="*70)
    print("🔍 DETAILED CLASSIFICATION ANALYSIS")
    print("="*70)
    
    details = classifier.classify_with_details(image_path)
    
    print(f"\nResults:")
    print(f"  Math confidence: {details['math_confidence']:.2%}")
    print(f"  Diagram confidence: {details['diagram_confidence']:.2%}")
    print(f"  Final classification: {details['classification'].upper()}")
    print(f"  Recommendation: {details['recommendation']}")
    print("="*70 + "\n")
    
    return details['classification']


# Test Execution
if __name__ == "__main__":
    print("="*60)
    print("Testing Enhanced CLIP Classifier (Accurate Scoring)")
    print("="*60)
    
    # Set use_gpu=True if you have CUDA installed for faster processing
    classifier = ImageClassifier(use_gpu=False) 
    
    if not classifier.is_available():
        print("❌ Classifier not available. Please install dependencies.")
        exit(1)
    
    # --- IMPORTANT ---
    # The code below requires these three image files to exist in the same directory:
    # "captured.jpg", "test_math.png", and "test_diagram.png"
    # If they don't exist, the test loop will skip them.
    # ---
    test_images = [
        "captured.jpg",  # Placeholder for a real image
        "img1.jpg", # Placeholder for a true math image
        "img2.jpg", # Placeholder for a true math image
        "img 3.png" # Placeholder for a true diagram image
    ]
    
    for img_path in test_images:
        if os.path.exists(img_path):
            print(f"\n{'='*60}")
            print(f"📸 Testing: {img_path}")
            print('='*60)
            
            # We use the debug function which calls the core logic inside
            result = classify_with_debug(classifier, img_path)
            print(f"🎯 Final Classification: {result.upper()}\n")
        else:
            print(f"\n⚠️ Image not found: {img_path} - Skipping test.")
    
    print(f"\n{'='*60}")
    print("Testing complete!")
    print('='*60)