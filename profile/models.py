from dataclasses import dataclass, asdict, field
from typing import List
import json
from datetime import datetime


@dataclass
class UserProfile:
    user_id: str
    diet_type: str = "omnivore"
    allergies: List[str] = field(default_factory=list)
    disliked_ingredients: List[str] = field(default_factory=list)
    cuisine_preferences: List[str] = field(default_factory=list)
    max_cooking_time: int = 60
    skill_level: str = "beginner"
    weekly_budget: float = 100.0
    currency: str = "EUR"
    household_size: int = 2
    sustainability_priority: str = "balanced"
    country: str = "France"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'UserProfile':
        if 'disliked_ingredients' in data and isinstance(data['disliked_ingredients'], list):
            data['disliked_ingredients'] = [i for i in data['disliked_ingredients'] if i and i.strip()]
        
        defaults = {
            'diet_type': 'omnivore',
            'allergies': [],
            'disliked_ingredients': [],
            'cuisine_preferences': [],
            'max_cooking_time': 60,
            'skill_level': 'beginner',
            'weekly_budget': 100.0,
            'currency': 'EUR',
            'household_size': 2,
            'sustainability_priority': 'balanced',
            'country': 'France',
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        for key, default_value in defaults.items():
            if key not in data:
                data[key] = default_value
        
        return cls(**data)
    
    def update(self, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = datetime.now().isoformat()
    
    def is_vegetarian(self) -> bool:
        return self.diet_type in ["vegetarian", "vegan"]
    
    def is_vegan(self) -> bool:
        return self.diet_type == "vegan"
    
    def has_allergy(self, ingredient: str) -> bool:
        return ingredient.lower() in [a.lower() for a in self.allergies]
    
    def dislikes(self, ingredient: str) -> bool:
        return ingredient.lower() in [d.lower() for d in self.disliked_ingredients]
