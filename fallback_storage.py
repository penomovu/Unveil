"""
Fallback storage system for when database is not available
Uses JSON files for persistence
"""

import json
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class FallbackStorage:
    """JSON-based fallback storage"""
    
    def __init__(self):
        self.data_dir = 'data'
        os.makedirs(self.data_dir, exist_ok=True)
        
        self.writeups_file = os.path.join(self.data_dir, 'writeups.json')
        self.models_file = os.path.join(self.data_dir, 'models.json')
        
        # Initialize files if they don't exist
        self._init_files()
    
    def _init_files(self):
        """Initialize JSON files"""
        if not os.path.exists(self.writeups_file):
            self._save_json(self.writeups_file, [])
            
        if not os.path.exists(self.models_file):
            self._save_json(self.models_file, [])
    
    def _load_json(self, filepath):
        """Load JSON data"""
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load {filepath}: {e}")
            return []
    
    def _save_json(self, filepath, data):
        """Save JSON data"""
        try:
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            return True
        except Exception as e:
            logger.error(f"Failed to save {filepath}: {e}")
            return False
    
    def save_writeup(self, title, content, source, url=None, category=None, tags=None, difficulty=None):
        """Save writeup to JSON file"""
        writeups = self._load_json(self.writeups_file)
        
        writeup = {
            'id': len(writeups) + 1,
            'title': title,
            'content': content,
            'source': source,
            'url': url,
            'category': category,
            'tags': tags,
            'difficulty': difficulty,
            'created_at': datetime.now().isoformat()
        }
        
        writeups.append(writeup)
        
        if self._save_json(self.writeups_file, writeups):
            return writeup['id']
        return None
    
    def get_writeups(self, limit=100):
        """Get writeups from JSON file"""
        writeups = self._load_json(self.writeups_file)
        return writeups[-limit:]  # Return most recent
    
    def save_model(self, name, version, model_type, model_data, config_data=None, tokenizer_data=None):
        """Save model to JSON file"""
        models = self._load_json(self.models_file)
        
        # Deactivate existing models
        for model in models:
            model['is_active'] = False
        
        model = {
            'id': len(models) + 1,
            'name': name,
            'version': version,
            'model_type': model_type,
            'model_data': model_data.decode('utf-8') if isinstance(model_data, bytes) else str(model_data),
            'config_data': config_data,
            'is_active': True,
            'created_at': datetime.now().isoformat(),
            'download_count': 0
        }
        
        models.append(model)
        
        if self._save_json(self.models_file, models):
            return model['id']
        return None
    
    def get_active_model(self):
        """Get active model"""
        models = self._load_json(self.models_file)
        for model in models:
            if model.get('is_active'):
                return model
        return None
    
    def update_model_usage(self, model_id, response_time):
        """Update model usage stats"""
        models = self._load_json(self.models_file)
        for model in models:
            if model['id'] == model_id:
                model['download_count'] = model.get('download_count', 0) + 1
                model['last_used'] = datetime.now().isoformat()
                break
        
        self._save_json(self.models_file, models)

# Global fallback instance
fallback_storage = FallbackStorage()