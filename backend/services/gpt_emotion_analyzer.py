import os
import openai
import httpx
import json
from typing import Dict, List, Tuple

class GPTEmotionAnalyzer:
    """GPT-4.1-mini based emotion analyzer for movie recommendations"""
    
    def __init__(self):
        """Initialize the GPT-4.1-mini emotion analyzer"""
        # Clear proxy environment variables to prevent httpx issues
        os.environ.pop('HTTP_PROXY', None)
        os.environ.pop('HTTPS_PROXY', None)
        os.environ.pop('http_proxy', None)
        os.environ.pop('https_proxy', None)
        os.environ.pop('NO_PROXY', None)
        os.environ.pop('no_proxy', None)
        
        # OpenAI API key is already set in environment
        api_key = os.getenv('OPENAI_API_KEY')
        base_url = os.getenv('OPENAI_API_BASE')
        
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        # Create custom httpx client without any proxy settings
        # This prevents the 'proxies' parameter error
        custom_http_client = httpx.Client(
            timeout=30.0,
            # No proxies parameter - let httpx handle it internally
        )
        
        # Initialize OpenAI client with custom HTTP client
        self.client = openai.OpenAI(
            api_key=api_key,
            http_client=custom_http_client
        )
        
        # Set base URL separately if provided
        if base_url:
            self.client.base_url = base_url
        
        # Define mood categories for movie recommendations
        self.mood_categories = [
            "action", "adventure", "comedy", "drama", "horror", 
            "romance", "thriller", "sci-fi", "fantasy", "documentary",
            "feel-good", "uplifting", "calming", "energetic", "nostalgic"
        ]
    
    def analyze_emotion(self, text: str) -> Dict:
        """
        Analyze emotion using GPT-4.1-mini
        
        Args:
            text (str): User input text describing their mood/feelings
            
        Returns:
            Dict: Analysis results with emotions and movie moods
        """
        try:
            print(f"DEBUG: Starting emotion analysis for text: {text}")
            
            # Create optimized prompt for emotion analysis
            prompt = self._create_analysis_prompt(text)
            print(f"DEBUG: Created prompt: {prompt[:100]}...")
            
            # Call GPT-4.1-mini API
            response = self.client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {"role": "system", "content": "You are an expert emotion analyst and movie recommendation specialist."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,  # Lower temperature for more consistent results
                max_tokens=500
            )
            
            print(f"DEBUG: GPT response received: {response.choices[0].message.content[:100]}...")
            
            # Parse the response
            result = self._parse_gpt_response(response.choices[0].message.content)
            print(f"DEBUG: Parsed result type: {type(result)}, value: {result}")
            
            # Ensure result is a dictionary
            if not isinstance(result, dict):
                print(f"ERROR: Unexpected result type: {type(result)}, value: {result}")
                result = self._fallback_analysis(text)
                print(f"DEBUG: Fallback result: {result}")
            
            # Add confidence score
            result['confidence'] = self._calculate_confidence(text, result)
            result['analysis_method'] = 'gpt-4.1-mini'
            
            print(f"DEBUG: Final result: {result}")
            return result
            
        except Exception as e:
            print(f"ERROR: GPT analysis failed: {e}")
            print(f"ERROR: Exception type: {type(e)}")
            import traceback
            traceback.print_exc()
            # Fallback to basic analysis if GPT fails
            fallback_result = self._fallback_analysis(text)
            print(f"DEBUG: Exception fallback result: {fallback_result}")
            return fallback_result
    
    def _create_analysis_prompt(self, text: str) -> str:
        """Create optimized prompt for GPT-3.5 Turbo"""
        mood_list = ", ".join(self.mood_categories)
        
        prompt = f"""
Analyze the emotional state and movie preferences from this user input: "{text}"

Please provide a detailed analysis in the following JSON format:

{{
    "primary_emotions": {{
        "joy": 0.0-1.0,
        "sadness": 0.0-1.0,
        "anger": 0.0-1.0,
        "fear": 0.0-1.0,
        "surprise": 0.0-1.0,
        "excitement": 0.0-1.0,
        "calmness": 0.0-1.0,
        "nostalgia": 0.0-1.0
    }},
    "movie_moods": {{
        "action": 0.0-1.0,
        "adventure": 0.0-1.0,
        "comedy": 0.0-1.0,
        "drama": 0.0-1.0,
        "horror": 0.0-1.0,
        "romance": 0.0-1.0,
        "thriller": 0.0-1.0,
        "sci-fi": 0.0-1.0,
        "fantasy": 0.0-1.0,
        "feel-good": 0.0-1.0,
        "uplifting": 0.0-1.0,
        "calming": 0.0-1.0,
        "energetic": 0.0-1.0,
        "nostalgic": 0.0-1.0
    }},
    "context_analysis": {{
        "energy_level": "low/medium/high",
        "social_preference": "alone/with_others/either",
        "time_preference": "short/medium/long",
        "complexity_preference": "simple/moderate/complex"
    }},
    "reasoning": "Brief explanation of why these moods were selected"
}}

Focus on understanding:
1. The user's current emotional state
2. What type of movie experience they're seeking
3. The intensity and energy level they want
4. Any specific preferences mentioned

Return only valid JSON without any additional text.
"""
        return prompt
    
    def _parse_gpt_response(self, response_text: str) -> Dict:
        """Parse GPT response and extract structured data"""
        try:
            print(f"DEBUG: _parse_gpt_response called with: {response_text[:100]}...")
            
            # Ensure response_text is a string
            if not isinstance(response_text, str):
                print(f"ERROR: Unexpected response type: {type(response_text)}")
                return self._create_fallback_structure()
            
            # Clean the response text
            response_text = response_text.strip()
            if response_text.startswith('```json'):
                response_text = response_text[7:]
            if response_text.endswith('```'):
                response_text = response_text[:-3]
            
            print(f"DEBUG: Cleaned response text: {response_text[:100]}...")
            
            # Parse JSON
            result = json.loads(response_text)
            print(f"DEBUG: JSON parsed successfully: {result}")
            
            # Ensure result is a dictionary
            if not isinstance(result, dict):
                print(f"ERROR: Parsed result is not a dictionary: {type(result)}")
                return self._create_fallback_structure()
            
            # Validate and normalize the structure
            normalized_result = {
                'emotions': result.get('primary_emotions', {}),
                'moods': result.get('movie_moods', {}),
                'context': result.get('context_analysis', {}),
                'reasoning': result.get('reasoning', 'Analysis completed'),
                'raw_response': result
            }
            
            print(f"DEBUG: Normalized result: {normalized_result}")
            return normalized_result
            
        except json.JSONDecodeError as e:
            print(f"ERROR: JSON parsing failed: {e}")
            print(f"ERROR: Response text: {response_text}")
            # Return a basic structure if parsing fails
            fallback = self._create_fallback_structure()
            print(f"DEBUG: JSON decode fallback: {fallback}")
            return fallback
        except Exception as e:
            print(f"ERROR: Unexpected error in _parse_gpt_response: {e}")
            import traceback
            traceback.print_exc()
            fallback = self._create_fallback_structure()
            print(f"DEBUG: General exception fallback: {fallback}")
            return fallback
    
    def _calculate_confidence(self, text: str, result: Dict) -> float:
        """Calculate confidence score based on analysis quality"""
        confidence = 0.85  # Base confidence for GPT-4.1-mini
        
        # Increase confidence for longer, more descriptive text
        if len(text.split()) > 5:
            confidence += 0.1
        
        # Increase confidence if multiple moods are identified
        mood_count = sum(1 for score in result.get('moods', {}).values() if score > 0.3)
        if mood_count >= 2:
            confidence += 0.05
        
        # Cap at 0.95
        return min(confidence, 0.95)
    
    def _fallback_analysis(self, text: str) -> Dict:
        """Fallback analysis if GPT fails"""
        # Simple keyword-based analysis as fallback
        text_lower = text.lower()
        
        moods = {}
        emotions = {}
        
        # Basic keyword matching
        if any(word in text_lower for word in ['excited', 'action', 'adventure', 'thrilling']):
            moods['action'] = 0.8
            moods['adventure'] = 0.7
            emotions['excitement'] = 0.8
        
        if any(word in text_lower for word in ['romantic', 'love', 'romance']):
            moods['romance'] = 0.9
            emotions['joy'] = 0.6
        
        if any(word in text_lower for word in ['funny', 'comedy', 'laugh', 'humor']):
            moods['comedy'] = 0.8
            emotions['joy'] = 0.7
        
        if any(word in text_lower for word in ['sad', 'depressed', 'down', 'upset']):
            moods['drama'] = 0.6
            moods['uplifting'] = 0.8  # Recommend uplifting content
            emotions['sadness'] = 0.7
        
        return {
            'emotions': emotions,
            'moods': moods,
            'context': {
                'energy_level': 'medium',
                'social_preference': 'either',
                'time_preference': 'medium',
                'complexity_preference': 'moderate'
            },
            'reasoning': 'Fallback keyword-based analysis',
            'confidence': 0.6,
            'analysis_method': 'fallback'
        }
    
    def _create_fallback_structure(self) -> Dict:
        """Create basic structure when parsing fails"""
        return {
            'emotions': {'joy': 0.5},
            'moods': {'feel-good': 0.7, 'comedy': 0.6},
            'context': {
                'energy_level': 'medium',
                'social_preference': 'either',
                'time_preference': 'medium',
                'complexity_preference': 'moderate'
            },
            'reasoning': 'Default recommendation due to parsing error',
            'confidence': 0.5,
            'analysis_method': 'fallback'
        }

# Test the analyzer
if __name__ == "__main__":
    analyzer = GPTEmotionAnalyzer()
    
    # Test cases
    test_inputs = [
        "I'm feeling excited and want something action-packed",
        "I'm a bit sad and need something uplifting",
        "I want something romantic for date night",
        "I'm stressed and need something calming",
        "I want to laugh and forget my problems"
    ]
    
    print("Testing GPT-4.1-mini Emotion Analyzer:")
    print("=" * 50)
    
    for i, test_input in enumerate(test_inputs, 1):
        print(f"\nTest {i}: {test_input}")
        result = analyzer.analyze_emotion(test_input)
        
        print(f"Method: {result.get('analysis_method', 'unknown')}")
        print(f"Confidence: {result.get('confidence', 0):.2f}")
        print(f"Top Emotions: {dict(sorted(result['emotions'].items(), key=lambda x: x[1], reverse=True)[:3])}")
        print(f"Top Moods: {dict(sorted(result['moods'].items(), key=lambda x: x[1], reverse=True)[:3])}")
        print(f"Reasoning: {result.get('reasoning', 'N/A')}")

