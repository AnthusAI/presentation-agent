"""
Application state management for DeckBot.

**DEPRECATED**: This module is deprecated and will be removed in a future version.
State is now managed in the frontend via browser localStorage instead of
persistent backend state files.

Legacy functionality:
- Stored application state (current presentation, etc.) in a YAML dotfile (.deckbot_state.yaml) in the project root.
- Separated from user preferences to keep configuration and state distinct.
"""

import os
import yaml
import warnings
from typing import Any, Optional

# Issue deprecation warning when module is imported
warnings.warn(
    "StateManager is deprecated and will be removed in a future version. "
    "State is now managed in frontend localStorage.",
    DeprecationWarning,
    stacklevel=2
)


class StateManager:
    """Manages application state stored in YAML format."""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize state manager.
        
        Args:
            config_path: Path to state file. Defaults to .deckbot_state.yaml in project root.
        """
        if config_path:
            self.config_path = config_path
        else:
            # Default to project root
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            self.config_path = os.path.join(project_root, '.deckbot_state.yaml')
        
        self._ensure_config_exists()
    
    def _ensure_config_exists(self):
        """Create state file with defaults if it doesn't exist."""
        if not os.path.exists(self.config_path):
            defaults = {
                'current_presentation': None
            }
            self._write_config(defaults)
    
    def _read_config(self) -> dict:
        """Read the state file."""
        try:
            if not os.path.exists(self.config_path):
                return {}
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
                return config if config else {}
        except Exception as e:
            print(f"Error reading state: {e}")
            return {}
    
    def _write_config(self, config: dict):
        """Write the state file."""
        try:
            with open(self.config_path, 'w') as f:
                yaml.dump(config, f, default_flow_style=False, sort_keys=False)
        except Exception as e:
            print(f"Error writing state: {e}")
    
    def get_current_presentation(self) -> Optional[str]:
        """
        Get the name of the currently active presentation.
        
        Returns:
            Name of the presentation or None if none is active
        """
        config = self._read_config()
        return config.get('current_presentation')
    
    def set_current_presentation(self, name: str):
        """
        Set the currently active presentation.
        
        Args:
            name: Name of the presentation
        """
        config = self._read_config()
        config['current_presentation'] = name
        self._write_config(config)
        
    def clear_current_presentation(self):
        """Clear the currently active presentation state."""
        config = self._read_config()
        if 'current_presentation' in config:
            del config['current_presentation']
            self._write_config(config)
            
    def get_all(self) -> dict:
        """Get all state."""
        return self._read_config()





