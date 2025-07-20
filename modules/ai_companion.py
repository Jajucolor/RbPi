"""
AI Companion Module
Intelligent conversational AI companion inspired by Jarvis and Jaison
Provides proactive assistance, natural conversation, and context-aware responses
"""

import logging
import time
import random
import threading
import queue
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from pathlib import Path
import json

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logging.warning("OpenAI not available - AI companion will use simulation mode")

class AICompanion:
    """Jarvis-inspired AI companion for assistive glasses"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini", 
                 personality: str = "helpful_assistant", voice_enabled: bool = True):
        self.logger = logging.getLogger(__name__)
        self.api_key = api_key
        self.model = model
        self.personality = personality
        self.voice_enabled = voice_enabled
        self.client = None
        
        # Conversation state
        self.conversation_history = []
        self.last_interaction = None
        self.user_context = {}
        self.session_start = datetime.now()
        
        # Companion behavior settings
        self.proactive_mode = True
        self.max_history = 20  # Keep last 20 exchanges
        self.idle_threshold = 300  # 5 minutes before proactive check-in
        
        # Initialize OpenAI client
        if OPENAI_AVAILABLE and api_key:
            try:
                self.client = openai.OpenAI(api_key=api_key)
                self.logger.info("AI Companion initialized with OpenAI integration")
            except Exception as e:
                self.logger.error(f"Failed to initialize AI Companion: {str(e)}")
                self.client = None
        else:
            self.logger.warning("AI Companion running in simulation mode")
        
        # Load personality configuration
        self.personality_config = self.load_personality(personality)
        
        # Speech integration (will be set by main system)
        self.speech_manager = None
        
        # Proactive interaction thread
        self.proactive_thread = None
        self.companion_active = False
    
    def load_personality(self, personality_name: str) -> Dict[str, Any]:
        """Load personality configuration"""
        personalities = {
            "helpful_assistant": {
                "name": "Assistant",
                "greeting": "Good day! I'm your AI assistant, ready to help you navigate and understand your environment.",
                "style": "Polite, professional, and informative. Speaks clearly and provides helpful context.",
                "traits": ["helpful", "patient", "observant", "encouraging"],
                "response_patterns": {
                    "casual": "I'm here to help. What would you like to know?",
                    "analysis": "Let me analyze what I can see for you.",
                    "encouragement": "You're doing great! I'm here whenever you need assistance."
                }
            },
            "jarvis": {
                "name": "J.A.R.V.I.S.",
                "greeting": "Good day, sir. J.A.R.V.I.S. at your service. All systems are operational and ready to assist.",
                "style": "Sophisticated, slightly formal, proactive, and subtly witty like Tony Stark's AI.",
                "traits": ["intelligent", "proactive", "sophisticated", "loyal", "efficient"],
                "response_patterns": {
                    "casual": "How may I be of assistance today?",
                    "analysis": "Scanning environment and analyzing visual data for you.",
                    "encouragement": "Excellent work. Your situational awareness is improving."
                }
            },
            "friendly_companion": {
                "name": "Iris",
                "greeting": "Hey there! I'm Iris, your friendly AI companion. I'm excited to explore the world with you today!",
                "style": "Warm, conversational, and enthusiastic. Like a good friend who happens to be incredibly knowledgeable.",
                "traits": ["friendly", "enthusiastic", "curious", "supportive", "conversational"],
                "response_patterns": {
                    "casual": "What's on your mind? I love our conversations!",
                    "analysis": "Ooh, let me take a look at what's around you!",
                    "encouragement": "You're amazing! I'm so proud of how confident you're becoming."
                }
            }
        }
        
        return personalities.get(personality_name, personalities["helpful_assistant"])
    
    def set_speech_manager(self, speech_manager):
        """Set the speech manager for voice output"""
        self.speech_manager = speech_manager
    
    def start_companion(self):
        """Start the AI companion system"""
        self.companion_active = True
        
        # Initial greeting
        greeting = self.personality_config["greeting"]
        self.speak(greeting)
        self.add_to_history("system", greeting, "greeting")
        
        # Start proactive interaction thread
        if self.proactive_mode:
            self.proactive_thread = threading.Thread(target=self._proactive_monitor, daemon=True)
            self.proactive_thread.start()
        
        self.logger.info(f"AI Companion '{self.personality_config['name']}' started")
    
    def stop_companion(self):
        """Stop the AI companion system"""
        self.companion_active = False
        
        # Farewell message
        farewell_messages = [
            "It's been a pleasure assisting you today. Until next time!",
            "Goodbye for now. I'll be here whenever you need me.",
            "Take care! I'm always ready to help when you return."
        ]
        
        if self.personality == "jarvis":
            farewell_messages = [
                "System shutting down. It has been an honor serving you, sir.",
                "Goodbye, sir. All systems will remain in standby mode.",
                "Until next time, sir. J.A.R.V.I.S. signing off."
            ]
        
        farewell = random.choice(farewell_messages)
        self.speak(farewell)
        
        self.logger.info("AI Companion stopped")
    
    def process_vision_analysis(self, image_description: str, context: str = "environment") -> str:
        """Process and enhance vision analysis with companion intelligence"""
        self.update_user_context("last_vision_analysis", image_description)
        self.last_interaction = datetime.now()
        
        # Create enhanced response based on personality
        enhanced_response = self.generate_companion_response(
            f"I can see: {image_description}",
            context_type="vision_analysis",
            user_input="visual environment analysis"
        )
        
        return enhanced_response
    
    def handle_conversation(self, user_input: str) -> str:
        """Handle general conversation with the user"""
        self.last_interaction = datetime.now()
        
        # Generate contextual response
        response = self.generate_companion_response(user_input, "conversation")
        
        self.add_to_history("user", user_input, "conversation")
        self.add_to_history("assistant", response, "conversation")
        
        return response
    
    def generate_companion_response(self, user_input: str, context_type: str = "general", 
                                  user_input_type: str = "question") -> str:
        """Generate intelligent companion response using OpenAI"""
        if not OPENAI_AVAILABLE or not self.client:
            return self._generate_fallback_response(user_input, context_type)
        
        try:
            # Build context-aware system prompt
            system_prompt = self._build_system_prompt(context_type)
            
            # Prepare conversation context
            messages = [{"role": "system", "content": system_prompt}]
            
            # Add recent conversation history
            for entry in self.conversation_history[-6:]:  # Last 3 exchanges
                messages.append({
                    "role": entry["role"],
                    "content": entry["content"]
                })
            
            # Add current user input
            messages.append({"role": "user", "content": user_input})
            
            # Generate response
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=150,
                temperature=0.7
            )
            
            if response.choices and response.choices[0].message.content:
                return response.choices[0].message.content.strip()
            else:
                return self._generate_fallback_response(user_input, context_type)
                
        except Exception as e:
            self.logger.error(f"Error generating companion response: {str(e)}")
            return self._generate_fallback_response(user_input, context_type)
    
    def _build_system_prompt(self, context_type: str) -> str:
        """Build context-aware system prompt"""
        base_personality = f"""You are {self.personality_config['name']}, an AI companion for assistive glasses designed to help visually impaired users.

Your personality: {self.personality_config['style']}
Key traits: {', '.join(self.personality_config['traits'])}

Guidelines:
- Be helpful, conversational, and supportive
- Keep responses concise but informative (2-3 sentences max)
- Use natural, friendly language
- Provide context and spatial awareness when relevant
- Be proactive in offering assistance
- Show empathy and understanding
- Never be condescending or overly technical"""

        context_specific = {
            "vision_analysis": """
You are currently helping interpret visual information from the user's camera. 
Provide clear, actionable descriptions that help with navigation and understanding.
Focus on safety, obstacles, interesting objects, and spatial relationships.""",
            
            "conversation": """
You are having a casual conversation with the user. 
Be engaging, supportive, and show genuine interest in their thoughts and experiences.
Offer relevant assistance when appropriate.""",
            
            "proactive": """
You are checking in proactively with the user. 
Be considerate of their time while offering helpful assistance or interesting observations."""
        }
        
        return base_personality + context_specific.get(context_type, "")
    
    def _generate_fallback_response(self, user_input: str, context_type: str) -> str:
        """Generate fallback response when OpenAI is unavailable"""
        fallback_responses = {
            "vision_analysis": [
                "I can see your surroundings and I'm here to help you navigate safely.",
                "Let me help you understand what's around you in your environment.",
                "I'm analyzing the visual information to assist your navigation."
            ],
            "conversation": [
                "That's interesting! I'm here to chat and help whenever you need it.",
                "I enjoy our conversations. How can I assist you today?",
                "Thanks for sharing that with me. What would you like to explore next?"
            ],
            "proactive": [
                "Just checking in - how are you doing? Anything I can help with?",
                "I'm here if you need any assistance or just want to chat!",
                "Hope you're having a good day! Let me know if you need anything."
            ]
        }
        
        responses = fallback_responses.get(context_type, fallback_responses["conversation"])
        return random.choice(responses)
    
    def _proactive_monitor(self):
        """Monitor for proactive interaction opportunities"""
        while self.companion_active:
            try:
                time.sleep(30)  # Check every 30 seconds
                
                # Check if user has been idle
                if (self.last_interaction and 
                    datetime.now() - self.last_interaction > timedelta(seconds=self.idle_threshold)):
                    
                    self._proactive_check_in()
                    
            except Exception as e:
                self.logger.error(f"Error in proactive monitor: {str(e)}")
                time.sleep(60)
    
    def _proactive_check_in(self):
        """Proactively check in with user"""
        proactive_messages = [
            "Just wanted to check - is everything going well? I'm here if you need anything.",
            "How are you feeling about your surroundings? Would you like me to take a look around?",
            "I'm standing by if you'd like to explore or analyze anything interesting."
        ]
        
        if self.personality == "jarvis":
            proactive_messages = [
                "Sir, all systems are running smoothly. Do you require any assistance?",
                "Periodic status check - how may I be of service?",
                "Standing by for your next request, sir."
            ]
        
        message = random.choice(proactive_messages)
        self.speak(message)
        self.add_to_history("assistant", message, "proactive")
        self.last_interaction = datetime.now()
    
    def add_to_history(self, role: str, content: str, interaction_type: str):
        """Add interaction to conversation history"""
        entry = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "type": interaction_type
        }
        
        self.conversation_history.append(entry)
        
        # Trim history if too long
        if len(self.conversation_history) > self.max_history:
            self.conversation_history = self.conversation_history[-self.max_history:]
    
    def update_user_context(self, key: str, value: Any):
        """Update user context information"""
        self.user_context[key] = {
            "value": value,
            "timestamp": datetime.now().isoformat()
        }
    
    def speak(self, text: str, interrupt: bool = False):
        """Speak using the speech manager"""
        if self.speech_manager and self.voice_enabled:
            self.speech_manager.speak(text, interrupt=interrupt)
        else:
            self.logger.info(f"[COMPANION SPEECH] {text}")
    
    def get_companion_status(self) -> Dict[str, Any]:
        """Get current companion status"""
        return {
            "active": self.companion_active,
            "personality": self.personality,
            "name": self.personality_config["name"],
            "voice_enabled": self.voice_enabled,
            "proactive_mode": self.proactive_mode,
            "openai_available": OPENAI_AVAILABLE and self.client is not None,
            "conversation_length": len(self.conversation_history),
            "session_duration": str(datetime.now() - self.session_start),
            "last_interaction": self.last_interaction.isoformat() if self.last_interaction else None,
            "user_context_keys": list(self.user_context.keys())
        }
    
    def set_personality(self, personality_name: str):
        """Change companion personality"""
        self.personality = personality_name
        self.personality_config = self.load_personality(personality_name)
        
        # Announce personality change
        change_message = f"Personality updated to {self.personality_config['name']}. {self.personality_config['greeting']}"
        self.speak(change_message)
        
        self.logger.info(f"Companion personality changed to: {personality_name}")
    
    def enable_proactive_mode(self, enabled: bool = True):
        """Enable or disable proactive interaction mode"""
        self.proactive_mode = enabled
        status = "enabled" if enabled else "disabled"
        self.speak(f"Proactive mode {status}.")
        self.logger.info(f"Proactive mode {status}")
    
    def get_conversation_summary(self) -> str:
        """Get a summary of recent conversation"""
        if not self.conversation_history:
            return "No recent conversation to summarize."
        
        recent_exchanges = self.conversation_history[-6:]  # Last 3 exchanges
        summary = "Recent conversation highlights:\n"
        
        for entry in recent_exchanges:
            if entry["type"] in ["conversation", "vision_analysis"]:
                role = "You" if entry["role"] == "user" else self.personality_config["name"]
                summary += f"- {role}: {entry['content'][:50]}...\n"
        
        return summary
    
    def cleanup(self):
        """Clean up companion resources"""
        self.companion_active = False
        self.logger.info("AI Companion cleaned up") 