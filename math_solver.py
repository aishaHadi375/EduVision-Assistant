# ================= FINAL CODE WITH TTS FUNCTIONALITY====================

from tts_manager import TTSManager

try:
    from latex2sympy2 import latex2sympy
except Exception:
    latex2sympy = None

import sympy as sp
from sympy import Eq, Integral, Derivative, Sum, MatrixBase, symbols
from sympy.parsing.latex import parse_latex
from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application
from PIL import Image
import os
import re
import time
import hashlib
import json
from pathlib import Path

# OCR modules
try:
    from pix2text import Pix2Text
except Exception:
    Pix2Text = None

try:
    from pix2tex.cli import LatexOCR
except Exception:
    LatexOCR = None

# Gemini Integration (OPTIONAL)
try:
    import google.generativeai as genai
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    if GEMINI_API_KEY:
        genai.configure(api_key=GEMINI_API_KEY)
        try:
            # ✅ UPDATED: Using Gemini 2.5 Flash (latest)
            gemini_model = genai.GenerativeModel("gemini-2.5-flash")
            print("✅ Gemini 2.5 Flash loaded (OPTIONAL - solver works without it)")
        except Exception as e:
            gemini_model = None
            print(f"⚠ Gemini init failed: {e}")
            print("   → Continuing with local processing only")
    else:
        gemini_model = None
        print("⚠ GEMINI_API_KEY not found. Using local processing only.")
except Exception as e:
    gemini_model = None
    print(f"⚠ Gemini not available: {e}")
    print("   → Using local processing (no API needed)")


class ResponseCache:
    """Cache responses to avoid duplicate API calls"""
    
    def __init__(self, cache_file="gemini_cache.json"):
        self.cache_file = Path(cache_file)
        self.cache = self._load_cache()
    
    def _load_cache(self):
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def _save_cache(self):
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, indent=2)
        except Exception as e:
            print(f"⚠ Cache save failed: {e}")
    
    def _hash_key(self, text):
        return hashlib.md5(text.encode()).hexdigest()
    
    def get(self, prompt):
        key = self._hash_key(prompt)
        cached = self.cache.get(key)
        if cached:
            return cached.get('response')
        return None
    
    def set(self, prompt, response):
        key = self._hash_key(prompt)
        self.cache[key] = {
            'response': response,
            'timestamp': time.time()
        }
        self._save_cache()


class OCRToLatex:
    """FIXED: Enhanced OCR with better expression selection"""
    
    def __init__(self):
        self.p2t = None
        self.lm2latex = None
        
        if Pix2Text is not None:
            try:
                self.p2t = Pix2Text()
                print("✅ Pix2Text OCR loaded")
            except Exception as e:
                print(f"⚠ Pix2Text init failed: {e}")
                
        if LatexOCR is not None:
            try:
                self.lm2latex = LatexOCR()
                print("✅ LatexOCR loaded")
            except Exception as e:
                print(f"⚠ LatexOCR init failed: {e}")

    def recognize(self, image_path_or_pil):
        """Extract LaTeX from image with smart expression selection"""
        if self.p2t is not None:
            try:
                result = self.p2t.recognize(image_path_or_pil)
                
                # Handle different result types
                if isinstance(result, str):
                    return self._select_best_expression(result)
                if isinstance(result, dict):
                    text = result.get("latex", result.get("text", str(result)))
                    return self._select_best_expression(text)
                if isinstance(result, list) and result:
                    all_text = []
                    for item in result:
                        if isinstance(item, dict):
                            all_text.append(item.get("latex", item.get("text", str(item))))
                        else:
                            all_text.append(str(item))
                    combined = "\n".join(all_text)
                    return self._select_best_expression(combined)
                return self._select_best_expression(str(result))
            except Exception as e:
                print(f"⚠ Pix2Text failed: {e}")

        # Fallback to LatexOCR
        if self.lm2latex is not None:
            try:
                if isinstance(image_path_or_pil, Image.Image):
                    return self.lm2latex(image_path_or_pil)
                else:
                    pil_img = Image.open(image_path_or_pil)
                    return self.lm2latex(pil_img)
            except Exception as e:
                print(f"⚠ LatexOCR failed: {e}")

        raise RuntimeError("No OCR engine available. Install: pip install pix2text")
    
    def _select_best_expression(self, ocr_text):
        """
        FIXED: Extract individual expressions from multi-line/matrix OCR output
        Handles cases like: \begin{matrix} eq1 \\ integral \\ geometry \end{matrix}
        """
        if not isinstance(ocr_text, str):
            ocr_text = str(ocr_text)
        
        print(f"\n🔍 Raw OCR output:\n{ocr_text}\n")
        
        # Step 1: Remove matrix wrappers and split by lines
        ocr_text = re.sub(r'\\begin\{matrix\}', '', ocr_text)
        ocr_text = re.sub(r'\\end\{matrix\}', '', ocr_text)
        ocr_text = re.sub(r'\\begin\{array\}.*?\\end\{array\}', '', ocr_text, flags=re.DOTALL)
        
        # Split by line breaks (\\)
        lines = re.split(r'\\\\', ocr_text)
        
        # Step 2: Extract expressions from each line
        expressions = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Remove common non-math symbols
            cleaned_line = re.sub(r'\\because|\\therefore', '', line)
            cleaned_line = re.sub(r'\\text\{.*?\}', '', cleaned_line)
            
            # Remove geometric notation
            cleaned_line = re.sub(r'\\angle\s*\d*\s*[A-Z]*', '', cleaned_line)
            cleaned_line = re.sub(r'\\triangle', '', cleaned_line)
            
            # Extract from $ delimiters if present
            dollar_matches = re.findall(r'\$\$?(.*?)\$\$?', cleaned_line, re.DOTALL)
            if dollar_matches:
                for match in dollar_matches:
                    match = match.strip()
                    if match and self._is_valid_math(match):
                        expressions.append(match)
            else:
                # No delimiters - clean and add if valid math
                cleaned_line = self._clean_expression(cleaned_line)
                if cleaned_line and self._is_valid_math(cleaned_line):
                    expressions.append(cleaned_line)
        
        # If no expressions found, try to extract from original text
        if not expressions:
            # Look for integrals
            integral_matches = re.findall(r'\\int.*?d\s*[a-z]', ocr_text, re.IGNORECASE)
            if integral_matches:
                expressions.extend([self._clean_expression(m) for m in integral_matches])
            
            # Look for equations
            equation_matches = re.findall(r'[^\\=]+=[^\\=]+', ocr_text)
            if equation_matches:
                expressions.extend([self._clean_expression(m) for m in equation_matches])
            
            # If still nothing, return cleaned original
            if not expressions:
                return self._clean_expression(ocr_text)
        
        # Step 3: Score and select best expression
        def complexity_score(expr):
            score = 0
            
            # High value for calculus
            score += expr.count('\\int') * 20
            score += expr.count('\\sum') * 18
            score += expr.count('\\lim') * 15
            score += expr.count('\\frac') * 10
            
            # Medium value for algebra
            score += expr.count('^') * 5
            score += len(re.findall(r'[a-z]', expr, re.IGNORECASE)) * 2
            
            # Basic operators
            score += expr.count('+') * 1
            score += expr.count('-') * 1
            score += expr.count('*') * 1
            
            # Bonus for equations
            if '=' in expr and not self._is_trivial_equation(expr):
                score += 8
            
            # Penalty for trivial equations
            if self._is_trivial_equation(expr):
                score -= 100
            
            # Penalty for geometric notation
            if re.search(r'\\angle|\\triangle|\\parallel', expr):
                score -= 80
            
            # Penalty for very short expressions
            if len(expr) < 5:
                score -= 30
            
            return score
        
        # Score all expressions
        scored = [(expr, complexity_score(expr)) for expr in expressions]
        scored.sort(key=lambda x: x[1], reverse=True)
        
        # Display results
        print(f"📝 Found {len(expressions)} expression(s):")
        for i, (expr, score) in enumerate(scored, 1):
            marker = "✓ SELECTED" if i == 1 else ""
            display_expr = expr[:70] + "..." if len(expr) > 70 else expr
            print(f"   {i}. {display_expr} (score: {score}) {marker}")
        
        # Return best expression (if score is reasonable)
        if scored and scored[0][1] > -50:
            return scored[0][0]
        elif expressions:
            return expressions[0]
        else:
            return self._clean_expression(ocr_text)
    
    def _is_valid_math(self, expr):
        """Check if expression contains mathematical content"""
        # Must have at least one of these
        math_indicators = [
            r'\\int', r'\\sum', r'\\frac', r'\\lim',  # Calculus
            r'[a-z]', r'\^', r'=',  # Algebra
            r'\+', r'-', r'\*', r'/'  # Basic operators
        ]
        return any(re.search(pattern, expr, re.IGNORECASE) for pattern in math_indicators)
    
    def _is_trivial_equation(self, expr):
        """Check if equation is trivial (like 1/2 = 1/2)"""
        if '=' not in expr:
            return False
        
        parts = expr.split('=')
        if len(parts) != 2:
            return False
        
        left = parts[0].strip()
        right = parts[1].strip()
        
        # Check if both sides are identical
        if left == right:
            return True
        
        # Check if both sides are just simple fractions/numbers
        simple_pattern = r'^[\d\s\\/\{\}\\frac]+$'
        if re.match(simple_pattern, left) and re.match(simple_pattern, right):
            return True
        
        return False
    
    def _clean_expression(self, expr):
        """Clean up a single expression"""
        if not isinstance(expr, str):
            expr = str(expr)
        
        # Remove non-math elements
        expr = re.sub(r'\\because|\\therefore', '', expr)
        expr = re.sub(r'\\text\{.*?\}', '', expr)
        expr = re.sub(r'\\angle\s*\d*\s*[A-Z]*', '', expr)
        expr = re.sub(r'\\triangle', '', expr)
        
        # Clean whitespace
        expr = re.sub(r'\s+', ' ', expr).strip()
        
        # Remove leading/trailing non-math characters
        expr = re.sub(r'^[^\w\\$\(]+', '', expr)
        expr = re.sub(r'[^\w\\$\)\}]+$', '', expr)
        
        return expr


class MathSolver:
    """FIXED: Robust solver with better LaTeX parsing and TTS Manager"""
    
    def __init__(self, use_gemini=True):
        self.ocr = OCRToLatex()
        self.use_gemini = use_gemini and (gemini_model is not None)
        self.cache = ResponseCache()
        
        # ✅ Use TTSManager (no threading issues)
        self.tts = TTSManager()
        
        # Stats
        self.api_calls_made = 0
        self.cache_hits = 0
        self.quota_errors = 0

    def speak(self, text):
        """✅ Simple TTS wrapper - always blocks until complete"""
        if self.tts.is_available():
            self.tts.speak(text, prepare=True)

    def _sanitize_latex(self, latex_str):
        """FIXED: Enhanced LaTeX cleaning with matrix/multi-line handling"""
        if not isinstance(latex_str, str):
            latex_str = str(latex_str)

        s = latex_str.strip()
        
        # Remove matrix/array wrappers
        s = re.sub(r'\\begin\{matrix\}', '', s)
        s = re.sub(r'\\end\{matrix\}', '', s)
        s = re.sub(r'\\begin\{array\}.*?\\end\{array\}', '', s, flags=re.DOTALL)
        
        # Remove line breaks
        s = s.replace('\\\\', ' ')
        
        # Remove non-math symbols
        s = re.sub(r'\\because|\\therefore|\\angle', '', s)
        
        # Fix common OCR spacing issues
        s = re.sub(r'(?<=\d)\s+(?=\d)', '', s)  # "1 1" → "11"
        s = re.sub(r'd\s+x', 'dx', s)
        s = re.sub(r'd\s+([a-zA-Z])', r'd\1', s)
        
        # Remove delimiters
        s = s.replace('$$', '').replace('$', '')
        s = s.replace(r'\[', '').replace(r'\]', '')
        
        # Clean commands
        s = re.sub(r'\\displaystyle|\\textstyle|\\left|\\right', '', s)
        s = re.sub(r'\\,|\\;|\\:|\\!|\\quad|\\qquad', ' ', s)
        
        # Normalize operators
        s = s.replace(r'\cdot', '*')
        s = s.replace(r'\times', '*')
        s = s.replace(r'\div', '/')
        
        # Final cleanup
        s = re.sub(r'\s+', ' ', s).strip()
        
        return s, s

    def _call_gemini_safe(self, prompt):
        """Call Gemini with quota error handling"""
        if not self.use_gemini or gemini_model is None:
            return None
        
        # Check cache
        cached = self.cache.get(prompt)
        if cached:
            self.cache_hits += 1
            print(f"💾 Cache hit! (Saved API call)")
            return cached
        
        try:
            print(f"🌐 Calling Gemini API...")
            response = gemini_model.generate_content(prompt)
            result = response.text.strip()
            
            self.cache.set(prompt, result)
            self.api_calls_made += 1
            return result
            
        except Exception as e:
            error_str = str(e)
            if '429' in error_str or 'quota' in error_str.lower():
                self.quota_errors += 1
                print(f"⚠ Gemini quota exceeded (error #{self.quota_errors})")
                print("   → Continuing with local processing...")
                self.use_gemini = False
            else:
                print(f"⚠ Gemini error: {error_str[:200]}")
            
            return None

    def _get_local_explanation(self, expr, result):
        """Generate explanation WITHOUT using API"""
        lines = []
        
        if isinstance(expr, Integral):
            lines.append("📚 Step-by-Step Solution (Local):")
            lines.append("")
            lines.append("Step 1: Identify the integral")
            lines.append(f"   We need to find: {expr}")
            lines.append("")
            lines.append("Step 2: Apply integration rules")
            integrand = expr.args[0]
            var = expr.args[1][0]
            
            if integrand.is_Pow and integrand.base == var:
                power = integrand.exp
                lines.append(f"   Using power rule: ∫ x^n dx = x^(n+1)/(n+1) + C")
                lines.append(f"   Here n = {power}")
            elif integrand.is_Add:
                lines.append(f"   Using sum rule: ∫(f+g)dx = ∫f dx + ∫g dx")
                lines.append(f"   Split into {len(integrand.args)} terms")
                for i, term in enumerate(integrand.args, 1):
                    lines.append(f"      Term {i}: {term}")
            else:
                lines.append(f"   Integrating: {integrand}")
            
            lines.append("")
            lines.append("Step 3: Compute the antiderivative")
            lines.append(f"   Result: {result}")
            
        elif isinstance(expr, Derivative):
            lines.append("📚 Step-by-Step Solution (Local):")
            lines.append("")
            lines.append("Step 1: Identify the derivative")
            lines.append(f"   We need to find: {expr}")
            lines.append("")
            lines.append("Step 2: Apply differentiation rules")
            func = expr.args[0]
            
            if func.is_Pow:
                power = func.exp
                lines.append(f"   Using power rule: d/dx(x^n) = n*x^(n-1)")
                lines.append(f"   Here n = {power}")
            else:
                lines.append(f"   Differentiating: {func}")
            
            lines.append("")
            lines.append("Step 3: Final result")
            lines.append(f"   Result: {result}")
            
        elif isinstance(expr, Eq):
            lines.append("📚 Step-by-Step Solution (Local):")
            lines.append("")
            lines.append("Step 1: Identify the equation")
            lines.append(f"   Solve: {expr}")
            lines.append("")
            lines.append("Step 2: Isolate variables")
            lines.append(f"   Variables: {expr.free_symbols}")
            lines.append("")
            lines.append("Step 3: Solutions")
            lines.append(f"   Result: {result}")
        else:
            lines.append("📚 Solution:")
            lines.append(f"   Simplified: {result}")
        
        return "\n".join(lines)

    def _parse_latex(self, latex_str):
        """FIXED: Multiple parsing strategies with fallbacks"""
        print(f"🔍 Parsing: {latex_str[:100]}...")

        # Strategy 1: Try latex2sympy2 first (most robust)
        if latex2sympy is not None:
            try:
                result = latex2sympy(latex_str)
                print("✓ Parsed with latex2sympy2")
                return result
            except Exception as e:
                print(f"  ✗ latex2sympy2: {str(e)[:80]}")

        # Strategy 2: Try direct parse_latex
        try:
            result = parse_latex(latex_str)
            print("✓ Parsed with parse_latex")
            return result
        except Exception as e:
            print(f"  ✗ parse_latex: {str(e)[:80]}")

        # Strategy 3: Sanitize and retry
        try:
            sanitized, _ = self._sanitize_latex(latex_str)
            print(f"  Trying sanitized: {sanitized[:100]}")
            result = parse_latex(sanitized)
            print("✓ Parsed (sanitized)")
            return result
        except Exception as e:
            print(f"  ✗ Sanitized parse: {str(e)[:80]}")
        
        # Strategy 4: Extract specific patterns
        # Try integral extraction
        try:
            integral_match = re.search(r'\\int\s*\(?(.*?)\)?\s*d\s*([a-z])', latex_str, re.IGNORECASE)
            if integral_match:
                integrand = integral_match.group(1).strip()
                var = integral_match.group(2).strip()
                integral_expr = f"\\int {integrand} d{var}"
                print(f"  Trying extracted integral: {integral_expr}")
                result = parse_latex(integral_expr)
                print("✓ Parsed extracted integral")
                return result
        except Exception as e:
            print(f"  ✗ Integral extraction: {str(e)[:80]}")
        
        # Strategy 5: Try equation extraction
        try:
            eq_match = re.search(r'([^\\=]+)=([^\\=]+)', latex_str)
            if eq_match:
                left = eq_match.group(1).strip()
                right = eq_match.group(2).strip()
                # Clean both sides
                left = re.sub(r'(?<=\d)\s+(?=\d)', '', left)
                right = re.sub(r'(?<=\d)\s+(?=\d)', '', right)
                eq_expr = f"{left}={right}"
                print(f"  Trying extracted equation: {eq_expr}")
                result = parse_latex(eq_expr)
                print("✓ Parsed extracted equation")
                return result
        except Exception as e:
            print(f"  ✗ Equation extraction: {str(e)[:80]}")
        
        raise RuntimeError(f"Could not parse LaTeX after all strategies: {latex_str}")

    def _solve_expression(self, expr, latex_str, use_ai_explanation=True, use_tts=False):
        """✅ Solve with proper TTS - no threading issues"""
        if isinstance(expr, list) and len(expr) > 0:
            expr = expr[0]

        print(f"\n📊 Expression type: {type(expr).__name__}")
        print(f"   Content: {expr}")
        
        result = None
        explanation = None

        try:
            # Solve based on type
            if isinstance(expr, Eq):
                print("\n🔢 Solving equation...")
                variables = list(expr.free_symbols)
                result = sp.solve(expr, variables if variables else [sp.Symbol('x')])
                
            elif isinstance(expr, Integral):
                print("\n∫ Computing integral...")
                result = expr.doit()
                if not any(len(limit) > 2 for limit in expr.limits):
                    result = result + sp.Symbol('C')
                    
            elif isinstance(expr, Derivative):
                print("\n∂ Computing derivative...")
                result = expr.doit()
                
            elif isinstance(expr, sp.logic.boolalg.BooleanFalse):
                print("\n⚠ This is a FALSE statement (invalid equation)")
                return "FALSE - The equation is not valid"
                
            else:
                print("\n🔧 Simplifying...")
                result = sp.simplify(expr)
            
            print(f"✓ Computed: {result}")
            
            # ✅ Get explanation FIRST (before speaking)
            if use_ai_explanation and self.use_gemini:
                print("\n🤖 Getting AI explanation...")
                prompt = f"""Explain this math solution in 3 clear steps (max 150 words):

Problem: {expr}
Solution: {result}

Format:
Step 1: [What to do]
Step 2: [How to solve]
Step 3: [Final answer]"""
                
                explanation = self._call_gemini_safe(prompt)
                if not explanation:
                    print("→ Using local explanation")
                    explanation = self._get_local_explanation(expr, result)
            else:
                explanation = self._get_local_explanation(expr, result)
            
            # Print explanation
            if explanation:
                print("\n" + "="*70)
                print(explanation)
                print("="*70)
            
            # ✅ Now speak EVERYTHING (if TTS enabled)
            if use_tts and explanation:
                print("\n🔊 Speaking explanation...")
                # Use chunked speech for long explanations
                self.tts.speak_chunks(explanation, chunk_size=150)
                
                # Then speak final answer
                final_msg = f"The final answer is: {result}"
                print(f"\n🔊 {final_msg}")
                self.speak(final_msg)
            
            return result
            
        except Exception as e:
            print(f"⚠ Solving failed: {e}")
            import traceback
            traceback.print_exc()
            return None

    def solve_from_image(self, image_path, use_tts=True, use_ai_explanation=True):
        """Main solver - works with or without Gemini"""
        print("\n" + "="*70)
        print("🔢 ROBUST MATH SOLVER")
        print("="*70)
        print(f"Mode: {'AI-Powered' if self.use_gemini else 'Local Processing'}")
        print("="*70)

        try:
            # Step 1: OCR
            print("\nStep 1: Running OCR...")
            if use_tts:
                self.speak("Extracting expression.")
            
            raw_ocr = self.ocr.recognize(image_path)
            print(f"\nExtracted LaTeX: {raw_ocr}\n")

            # Step 2: Parse
            print("Step 2: Parsing LaTeX...")
            if use_tts:
                self.speak("Parsing expression.")
            expr = self._parse_latex(raw_ocr)
            print(f"✓ Parsed: {expr}\n")

            # Step 3: Solve
            print("Step 3: Solving...")
            if use_tts:
                self.speak("Solving.")
            result = self._solve_expression(expr, raw_ocr, use_ai_explanation, use_tts)

            # Final
            print("\n" + "="*70)
            print("🎯 FINAL ANSWER")
            print("="*70)
            print(f"{result}\n")
            
            # Stats
            print(f"📊 Session Stats:")
            print(f"   API calls: {self.api_calls_made}")
            print(f"   Cache hits: {self.cache_hits}")
            print(f"   Quota errors: {self.quota_errors}")
            print()

            # ✅ Final answer already spoken in _solve_expression
            # No need to speak again here

            return result

        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            if use_tts:
                self.speak("Error occurred")
            import traceback
            traceback.print_exc()
            return None


# ==================== MAIN ====================

if __name__ == "__main__":
    import sys
    
    # Initialize solver
    solver = MathSolver(use_gemini=True)
    
    # Get image path
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
    else:
        test_paths = [
            "captured.jpg",
            "saved.png",
            "math_problem.png",
        ]
        
        image_path = None
        for path in test_paths:
            if os.path.exists(path):
                image_path = path
                print(f"✓ Found image: {path}")
                break
        
        if image_path is None:
            print("="*70)
            print("❌ No image found!")
            print("="*70)
            print("\nUsage:")
            print("  python math_solver.py <image_path>")
            print("\nExamples:")
            print("  python math_solver.py captured.jpg")
            print('  python math_solver.py "C:/Users/hp/Desktop/math.png"')
            print("\nOr place an image named 'captured.jpg' in current directory")
            print("="*70)
            sys.exit(1)
    
    if not os.path.exists(image_path):
        print(f"❌ Image not found: {image_path}")
        sys.exit(1)
    
    print(f"\n🚀 Processing: {image_path}")
    
    # Solve
    result = solver.solve_from_image(
        image_path, 
        use_tts=True,
        use_ai_explanation=True
    )
    
    if result:
        print("\n✅ Solution complete!")
    else:
        print("\n⚠ Could not solve")