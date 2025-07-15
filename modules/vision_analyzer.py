"""
Vision Analyzer Module
Handles OpenAI Vision API integration for image analysis
"""

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
    """Handles image analysis using OpenAI's Vision API"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini"):
        self.logger = logging.getLogger(__name__)
        self.api_key = api_key
        self.model = model
        self.client = None
        
        # Initialize OpenAI client
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
        """
        Encode image to base64 string
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Base64 encoded image string or None if failed
        """
        try:
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            self.logger.error(f"Failed to encode image {image_path}: {str(e)}")
            return None
    
    def analyze_image(self, image_path: str, custom_prompt: Optional[str] = None) -> Optional[str]:
        """
        Analyze image using OpenAI Vision API
        
        Args:
            image_path: Path to the image file
            custom_prompt: Optional custom prompt for analysis
            
        Returns:
            Analysis description or None if failed
        """
        if not Path(image_path).exists():
            self.logger.error(f"Image file not found: {image_path}")
            return None
        
        if not OPENAI_AVAILABLE or not self.client:
            return self.simulate_analysis(image_path)
        
        try:
            # Encode image
            base64_image = self.encode_image(image_path)
            if not base64_image:
                return None
            
            # Prepare the prompt
            prompt = custom_prompt or self.get_default_prompt()
            
            # Make API call
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
        """Get the default prompt for vision analysis"""
        return """You are assisting a visually impaired person. Analyze this image and provide a clear, concise description of what you see. Focus on:

1. Important objects, people, and obstacles
2. The general environment and setting
3. Any text or signs that are visible
4. Potential hazards or things to be aware of
5. Navigation information if relevant

Keep your response under 50 words and speak directly to the person as if you are their helpful assistant. Be specific and practical."""
    
    def simulate_analysis(self, image_path: str) -> str:
        """
        Simulate image analysis for testing purposes
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Simulated analysis description
        """
        self.logger.info(f"Simulating analysis for {image_path}")
        
        # Generate different responses based on time to make it more realistic
        import time
        import random
        
        responses = [
            "I can see an indoor environment with furniture and good lighting. There appears to be a clear path ahead with no immediate obstacles.",
            "This looks like an outdoor area with trees and a walkway. The path appears clear with some benches visible on the sides.",
            "I can see a kitchen or dining area with a table and chairs. There are no obvious hazards in the immediate area.",
            "This appears to be a hallway or corridor with walls on both sides. The path looks clear for walking.",
            "I can see an office or workspace with desks and equipment. The lighting is good and the area appears safe to navigate."
        ]
        
        # Add some randomness to make it feel more realistic
        time.sleep(random.uniform(2, 4))  # Simulate API delay
        
        return random.choice(responses)
    
    def analyze_with_specific_focus(self, image_path: str, focus_area: str) -> Optional[str]:
        """
        Analyze image with specific focus area
        
        Args:
            image_path: Path to the image file
            focus_area: Specific area to focus on (e.g., "navigation", "text", "people")
            
        Returns:
            Focused analysis description
        """
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
        """
        Analyze multiple images in batch
        
        Args:
            image_paths: List of image file paths
            
        Returns:
            Dictionary with image paths as keys and analysis results as values
        """
        results = {}
        
        for image_path in image_paths:
            self.logger.info(f"Analyzing image: {image_path}")
            result = self.analyze_image(image_path)
            results[image_path] = result
            
        return results
    
    def get_analysis_stats(self) -> dict:
        """Get statistics about the analyzer"""
        return {
            "api_available": OPENAI_AVAILABLE and self.client is not None,
            "model": self.model,
            "client_initialized": self.client is not None,
            "mode": "production" if (OPENAI_AVAILABLE and self.client) else "simulation"
        } 