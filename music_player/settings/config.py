import os
import json
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

SETTINGS_FILE = os.path.join(
    os.path.expanduser("~"), ".antigravity_music_player_settings.json"
)

class ConfigService:
    """
    Manages persistent application settings using a local JSON file.
    """
    _defaults: Dict[str, Any] = {
        "last_folder": "",
        "volume": 70,
        "is_muted": False,
        "repeat_mode": 0,  # 0: OFF, 1: ALL, 2: ONE
        "shuffle": False
    }

    @classmethod
    def load(cls) -> Dict[str, Any]:
        """Loads settings from disk, falling back to defaults if not found."""
        if not os.path.exists(SETTINGS_FILE):
            return cls._defaults.copy()
        try:
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Ensure all default keys exist
                settings = cls._defaults.copy()
                settings.update(data)
                return settings
        except Exception as e:
            logger.error(f"Failed to load settings from {SETTINGS_FILE}: {e}")
            return cls._defaults.copy()

    @classmethod
    def save(cls, settings: Dict[str, Any]) -> None:
        """Saves settings to disk."""
        try:
            with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=4)
        except Exception as e:
            logger.error(f"Failed to save settings to {SETTINGS_FILE}: {e}")
