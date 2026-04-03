import json
from typing import List, Dict
from datetime import datetime
from pathlib import Path
import config


class ConversationHistory:
    def __init__(self, max_messages: int = 100):
        self.max_messages = max_messages
        self.messages: List[Dict] = []
        self.current_recipe: Dict = None
        self.recipes_history: List[Dict] = []
    
    def add_message(self, role: str, content: str, metadata: Dict = None):
        message = {
            'role': role,
            'content': content,
            'timestamp': datetime.now().isoformat(),
            'metadata': metadata or {}
        }
        
        self.messages.append(message)
        
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages:]
    
    def set_current_recipe(self, recipe: Dict):
        self.current_recipe = recipe
        self.recipes_history.append({
            'recipe': recipe,
            'timestamp': datetime.now().isoformat()
        })
        
        if len(self.recipes_history) > config.MAX_RECIPE_HISTORY:
            self.recipes_history = self.recipes_history[-config.MAX_RECIPE_HISTORY:]
    
    def get_current_recipe(self) -> Dict:
        return self.current_recipe
    
    def get_last_recipe(self) -> Dict:
        if self.recipes_history:
            return self.recipes_history[-1]['recipe']
        return None
    
    def get_messages(self, limit: int = None) -> List[Dict]:
        if limit:
            return self.messages[-limit:]
        return self.messages
    
    def get_context_for_llm(self, last_n: int = 10) -> List[Dict]:
        recent = self.messages[-last_n:] if len(self.messages) > last_n else self.messages
        
        context = []
        for msg in recent:
            context.append({
                'role': msg['role'],
                'content': msg['content']
            })
        
        return context
    
    def clear(self):
        self.messages = []
        self.current_recipe = None
    
    def save_to_file(self, filepath: Path):
        data = {
            'messages': self.messages,
            'current_recipe': self.current_recipe,
            'recipes_history': self.recipes_history,
            'saved_at': datetime.now().isoformat()
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def load_from_file(self, filepath: Path):
        if not filepath.exists():
            return
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.messages = data.get('messages', [])
            self.current_recipe = data.get('current_recipe')
            self.recipes_history = data.get('recipes_history', [])
        except (json.JSONDecodeError, KeyError):
            pass
    
    def get_shown_recipe_ids(self) -> List[int]:
        """Return IDs of recipes already shown in this conversation."""
        ids = []
        for entry in self.recipes_history:
            db_id = entry.get("recipe", {}).get("database_id")
            if db_id:
                ids.append(db_id)
        return ids

    def get_stats(self) -> Dict:
        return {
            'total_messages': len(self.messages),
            'user_messages': len([m for m in self.messages if m['role'] == 'user']),
            'assistant_messages': len([m for m in self.messages if m['role'] == 'assistant']),
            'recipes_generated': len(self.recipes_history),
            'first_message': self.messages[0]['timestamp'] if self.messages else None,
            'last_message': self.messages[-1]['timestamp'] if self.messages else None
        }
