"""
Bot configuration storage
Persists bot configurations to disk for restart capability
"""
import json
import os
from typing import Dict, Optional, List

STORAGE_FILE = "bots_config.json"


class BotStorage:
    """Persistent storage for bot configurations"""
    
    def __init__(self, storage_file: str = STORAGE_FILE):
        self.storage_file = storage_file
        self.configs: Dict[str, dict] = self._load()
    
    def _load(self) -> Dict[str, dict]:
        """Load bot configurations from disk"""
        if not os.path.exists(self.storage_file):
            return {}
        
        try:
            with open(self.storage_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading bot configs: {e}")
            return {}
    
    def _save(self):
        """Save bot configurations to disk"""
        try:
            with open(self.storage_file, 'w') as f:
                json.dump(self.configs, f, indent=2)
        except Exception as e:
            print(f"Error saving bot configs: {e}")
    
    def save_bot(self, bot_id: str, bot_token: str, app_token: str,
                 signing_secret: str, agent_url: str, channel_id: Optional[str] = None):
        """Save a bot configuration"""
        self.configs[bot_id] = {
            "bot_token": bot_token,
            "app_token": app_token,
            "signing_secret": signing_secret,
            "agent_url": agent_url,
            "channel_id": channel_id
        }
        self._save()
    
    def get_bot(self, bot_id: str) -> Optional[dict]:
        """Get a bot configuration"""
        return self.configs.get(bot_id)
    
    def delete_bot(self, bot_id: str):
        """Delete a bot configuration"""
        if bot_id in self.configs:
            del self.configs[bot_id]
            self._save()
    
    def list_bots(self) -> List[str]:
        """List all bot IDs"""
        return list(self.configs.keys())
    
    def get_all(self) -> Dict[str, dict]:
        """Get all bot configurations"""
        return self.configs.copy()