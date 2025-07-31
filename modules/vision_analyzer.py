import base64
import logging
import requests
from pathlib import Path
from typing import Optional
import json

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logging.warning("openai library not available - using simulation mode")

class VisionAnalyzer:
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini"):
        self.logger = logging.getLogger(__name__)
        self.api_key = api_key
        self.model = model
        self.client = None
        
        if OPENAI_AVAILABLE and api_key:
            try:
                self.client = openai.OpenAI(api_key=api_key)
                self.logger.info("OpenAI client initialized successfully")
            except Exception as e:
                self.logger.error(f"Failed to initialize OpenAI client: {str(e)}")
                self.client = None
        else:
            self.logger.warning("OpenAI not available or no API key provided - using simulation mode")
    
    def encode_image(self, image_path: str) -> Optional[str]:
        try:
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            self.logger.error(f"Failed to encode image {image_path}: {str(e)}")
            return None
    
    def analyze_image(self, image_path: str, custom_prompt: Optional[str] = None) -> Optional[str]:
        
        if not Path(image_path).exists():
            self.logger.error(f"Image file not found: {image_path}")
            return None
        
        if not OPENAI_AVAILABLE or not self.client:
            return self.simulate_analysis(image_path)
        
        try:
            # 이미지 형식
            base64_image = self.encode_image(image_path)
            if not base64_image:
                return None
  
            # 프롬프트
            prompt = custom_prompt or self.get_default_prompt()
 
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=300,
                temperature=0.3
            )
            
            if response.choices and response.choices[0].message.content:
                analysis = response.choices[0].message.content.strip()
                self.logger.info(f"Analysis completed successfully for {image_path}")
                return analysis
            else:
                self.logger.error("No content in API response")
                return None
                
        except Exception as e:
            self.logger.error(f"Error analyzing image with OpenAI: {str(e)}")
            return None
    
    def get_default_prompt(self) -> str:
        
        return """You are assisting a visually impaired person. Analyze this image and provide a clear, concise description of what you see. Focus on:

1. Important objects, people, and obstacles
2. The general environment and setting
3. Any text or signs that are visible
4. Potential hazards or things to be aware of
5. Navigation information if relevant

Keep your response under 50 words and speak directly to the person as if you are their helpful assistant. Be specific and practical."""
    
    def simulate_analysis(self, image_path: str) -> str:
        
        self.logger.info(f"Simulating analysis for {image_path}")
        
        
        import time
        import random
        
        responses = [
            "I can see an indoor environment with furniture and good lighting. There appears to be a clear path ahead with no immediate obstacles.",
            "This looks like an outdoor area with trees and a walkway. The path appears clear with some benches visible on the sides.",
            "I can see a kitchen or dining area with a table and chairs. There are no obvious hazards in the immediate area.",
            "This appears to be a hallway or corridor with walls on both sides. The path looks clear for walking.",
            "I can see an office or workspace with desks and equipment. The lighting is good and the area appears safe to navigate."
        ]        
        
        time.sleep(random.uniform(2, 4))  
        
        return random.choice(responses)
    
    def analyze_with_specific_focus(self, image_path: str, focus_area: str) -> Optional[str]:
        
        focus_prompts = {
            "navigation": "Focus on describing the path ahead, any obstacles, steps, or navigation aids that would help a visually impaired person move safely.",
            "text": "Focus on reading any text, signs, labels, or written information visible in the image.",
            "people": "Focus on describing any people in the image, their positions, and any social context that might be relevant.",
            "objects": "Focus on identifying and describing important objects, tools, or items that might be relevant to the person.",
            "hazards": "Focus on identifying any potential hazards, dangers, or things to be cautious about in the environment."
        }
        
        custom_prompt = focus_prompts.get(focus_area, self.get_default_prompt())
        return self.analyze_image(image_path, custom_prompt)
    
    def batch_analyze(self, image_paths: list) -> dict:
        
        results = {}
        
        for image_path in image_paths:
            self.logger.info(f"Analyzing image: {image_path}")
            result = self.analyze_image(image_path)
            results[image_path] = result
            
        return results
    
    def get_analysis_stats(self) -> dict:
        
        return {
            "api_available": OPENAI_AVAILABLE and self.client is not None,
            "model": self.model,
            "client_initialized": self.client is not None,
            "mode": "production" if (OPENAI_AVAILABLE and self.client) else "simulation"
        } 