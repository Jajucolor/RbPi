"""
Configuration Manager Module
Handles configuration settings and API keys for the assistive glasses system
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

class ConfigManager:
    """Manages configuration settings for the assistive glasses system"""
    
    def __init__(self, config_file: str = "config.json"):
        self.logger = logging.getLogger(__name__)
        self.config_file = Path(config_file)
        self.config = {}
        self.default_config = {
            "openai": {
                "api_key": "",
                "model": "gpt-4o-mini",
                "max_tokens": 300,
                "temperature": 0.3
            },
            "camera": {
                "width": 1920,
                "height": 1080,
                "quality": 85,
                "auto_focus": True
            },
            "speech": {
                "rate": 150,
                "volume": 0.9,
                "voice_id": "",
                "interrupt_on_capture": False
            },
            "system": {
                "capture_interval": 3,
                "log_level": "INFO",
                "save_images": True,
                "save_analysis": True
            },
            "hardware": {
                "button_pin": 18,
                "led_pin": 24,
                "shutdown_pin": 3,
                "debounce_time": 0.2
            },
            "companion": {
                "model": "gpt-4o-mini",
                "personality": "inta",
                "voice_enabled": True,
                "proactive_mode": True,
                "idle_threshold": 180,
                "constant_listening": True,
                "conversation_priority": True
            }
        }
        
        # Load configuration
        self.load_config()
    
    def load_config(self):
        """Load configuration from file or create default"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    self.config = json.load(f)
                self.logger.info(f"Configuration loaded from {self.config_file}")
                
                # Merge with defaults to ensure all keys exist
                self.config = self._merge_configs(self.default_config, self.config)
            else:
                self.logger.warning(f"Config file {self.config_file} not found, creating default")
                self.config = self.default_config.copy()
                self.save_config()
                
        except Exception as e:
            self.logger.error(f"Error loading configuration: {str(e)}")
            self.logger.info("Using default configuration")
            self.config = self.default_config.copy()
    
    def save_config(self):
        """Save current configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=4)
            self.logger.info(f"Configuration saved to {self.config_file}")
            
        except Exception as e:
            self.logger.error(f"Error saving configuration: {str(e)}")
    
    def _merge_configs(self, default: Dict[str, Any], user: Dict[str, Any]) -> Dict[str, Any]:
        """Merge user config with default config"""
        merged = default.copy()
        
        for key, value in user.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                merged[key] = self._merge_configs(merged[key], value)
            else:
                merged[key] = value
                
        return merged
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation
        
        Args:
            key: Configuration key (e.g., 'openai.api_key')
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        try:
            keys = key.split('.')
            value = self.config
            
            for k in keys:
                if isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    return default
                    
            return value
            
        except Exception as e:
            self.logger.error(f"Error getting config key '{key}': {str(e)}")
            return default
    
    def set(self, key: str, value: Any, save: bool = True):
        """
        Set configuration value using dot notation
        
        Args:
            key: Configuration key (e.g., 'openai.api_key')
            value: Value to set
            save: Whether to save to file immediately
        """
        try:
            keys = key.split('.')
            config_ref = self.config
            
            # Navigate to the parent of the target key
            for k in keys[:-1]:
                if k not in config_ref:
                    config_ref[k] = {}
                config_ref = config_ref[k]
            
            # Set the final key
            config_ref[keys[-1]] = value
            
            if save:
                self.save_config()
                
            self.logger.info(f"Configuration updated: {key} = {value}")
            
        except Exception as e:
            self.logger.error(f"Error setting config key '{key}': {str(e)}")
    
    def get_openai_key(self) -> Optional[str]:
        """Get OpenAI API key from config or environment"""
        # Try config file first
        api_key = self.get('openai.api_key')
        
        if api_key:
            return api_key
        
        # Try environment variable
        env_key = os.getenv('OPENAI_API_KEY')
        if env_key:
            return env_key
        
        # Try loading from separate key file
        key_file = Path('.openai_key')
        if key_file.exists():
            try:
                with open(key_file, 'r') as f:
                    key = f.read().strip()
                    if key:
                        return key
            except Exception as e:
                self.logger.error(f"Error reading key file: {str(e)}")
        
        self.logger.warning("No OpenAI API key found in config, environment, or key file")
        return None
    
    def set_openai_key(self, api_key: str):
        """Set OpenAI API key"""
        self.set('openai.api_key', api_key)
    
    def get_camera_config(self) -> Dict[str, Any]:
        """Get camera configuration"""
        return self.get('camera', {})
    
    def get_speech_config(self) -> Dict[str, Any]:
        """Get speech configuration"""
        return self.get('speech', {})
    
    def get_system_config(self) -> Dict[str, Any]:
        """Get system configuration"""
        return self.get('system', {})
    
    def get_hardware_config(self) -> Dict[str, Any]:
        """Get hardware configuration"""
        return self.get('hardware', {})
    
    def update_from_dict(self, updates: Dict[str, Any]):
        """Update configuration from dictionary"""
        for key, value in updates.items():
            self.set(key, value, save=False)
        self.save_config()
    
    def reset_to_defaults(self):
        """Reset configuration to defaults"""
        self.logger.info("Resetting configuration to defaults")
        self.config = self.default_config.copy()
        self.save_config()
    
    def validate_config(self) -> Dict[str, bool]:
        """Validate configuration settings"""
        validation_results = {}
        
        # Validate OpenAI API key
        api_key = self.get_openai_key()
        validation_results['openai_key'] = api_key is not None and len(api_key) > 0
        
        # Validate camera settings
        camera_config = self.get_camera_config()
        width = camera_config.get('width')
        height = camera_config.get('height')
        quality = camera_config.get('quality')
        
        validation_results['camera_width'] = isinstance(width, int) and width > 0
        validation_results['camera_height'] = isinstance(height, int) and height > 0
        validation_results['camera_quality'] = isinstance(quality, int) and 1 <= quality <= 100
        
        # Validate speech settings
        speech_config = self.get_speech_config()
        rate = speech_config.get('rate')
        volume = speech_config.get('volume')
        
        validation_results['speech_rate'] = isinstance(rate, int) and rate > 0
        validation_results['speech_volume'] = isinstance(volume, (int, float)) and 0 <= volume <= 1
        
        # Validate system settings
        system_config = self.get_system_config()
        interval = system_config.get('capture_interval')
        
        validation_results['capture_interval'] = isinstance(interval, (int, float)) and interval > 0
        
        return validation_results
    
    def get_config_summary(self) -> Dict[str, Any]:
        """Get a summary of current configuration"""
        return {
            "config_file": str(self.config_file),
            "config_exists": self.config_file.exists(),
            "openai_key_configured": self.get_openai_key() is not None,
            "camera_resolution": f"{self.get('camera.width')}x{self.get('camera.height')}",
            "speech_rate": self.get('speech.rate'),
            "capture_interval": self.get('system.capture_interval'),
            "validation_results": self.validate_config()
        }
    
    def export_config(self, export_path: str):
        """Export configuration to file"""
        try:
            export_file = Path(export_path)
            
            # Remove sensitive information for export
            export_config = self.config.copy()
            if 'openai' in export_config and 'api_key' in export_config['openai']:
                export_config['openai']['api_key'] = "[REDACTED]"
            
            with open(export_file, 'w') as f:
                json.dump(export_config, f, indent=4)
            
            self.logger.info(f"Configuration exported to {export_file}")
            
        except Exception as e:
            self.logger.error(f"Error exporting configuration: {str(e)}")
    
    def import_config(self, import_path: str):
        """Import configuration from file"""
        try:
            import_file = Path(import_path)
            
            if not import_file.exists():
                self.logger.error(f"Import file {import_file} not found")
                return
            
            with open(import_file, 'r') as f:
                imported_config = json.load(f)
            
            # Merge with current config
            self.config = self._merge_configs(self.config, imported_config)
            self.save_config()
            
            self.logger.info(f"Configuration imported from {import_file}")
            
        except Exception as e:
            self.logger.error(f"Error importing configuration: {str(e)}")
    
    def __str__(self) -> str:
        """String representation of configuration"""
        return f"ConfigManager(file={self.config_file}, keys={list(self.config.keys())})" 