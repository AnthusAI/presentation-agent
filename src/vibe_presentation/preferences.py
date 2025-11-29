"""
Preferences management for DeckBot.

Stores user preferences in a YAML dotfile (.deckbot.yaml) in the project root.
"""

import os
import yaml
from typing import Any, Optional


class PreferencesManager:
    """Manages user preferences stored in YAML format."""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize preferences manager.
        
        Args:
            config_path: Path to config file. Defaults to .deckbot.yaml in project root.
        """
        if config_path:
            self.config_path = config_path
        else:
            # Default to project root
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            self.config_path = os.path.join(project_root, '.deckbot.yaml')
        
        self._ensure_config_exists()
    
    def _ensure_config_exists(self):
        """Create config file with defaults if it doesn't exist."""
        if not os.path.exists(self.config_path):
            defaults = {
                'theme': 'system',
                'color_theme': 'miami'  # Default color theme
            }
            self._write_config(defaults)
    
    def _read_config(self) -> dict:
        """Read the config file."""
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
                return config if config else {}
        except Exception as e:
            print(f"Error reading config: {e}")
            return {}
    
    def _write_config(self, config: dict):
        """Write the config file."""
        try:
            with open(self.config_path, 'w') as f:
                yaml.dump(config, f, default_flow_style=False, sort_keys=False)
        except Exception as e:
            print(f"Error writing config: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a preference value.
        
        Args:
            key: Preference key (e.g., 'theme')
            default: Default value if key doesn't exist
            
        Returns:
            The preference value or default
        """
        config = self._read_config()
        return config.get(key, default)
    
    def set(self, key: str, value: Any):
        """
        Set a preference value.
        
        Args:
            key: Preference key
            value: Preference value
        """
        config = self._read_config()
        config[key] = value
        self._write_config(config)
    
    def get_all(self) -> dict:
        """Get all preferences."""
        return self._read_config()
    
    def update(self, preferences: dict):
        """
        Update multiple preferences at once.
        
        Args:
            preferences: Dictionary of preferences to update
        """
        config = self._read_config()
        config.update(preferences)
        self._write_config(config)
    
    def delete(self, key: str) -> bool:
        """
        Delete a preference.
        
        Args:
            key: Preference key to delete
            
        Returns:
            True if deleted, False if key didn't exist
        """
        config = self._read_config()
        if key in config:
            del config[key]
            self._write_config(config)
            return True
        return False

