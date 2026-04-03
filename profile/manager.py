import json
from pathlib import Path
from typing import Optional
from .models import UserProfile
from .defaults import DEFAULT_PROFILE
import config


class ProfileManager:
    def __init__(self, profiles_dir: Optional[Path] = None):
        self.profiles_dir = profiles_dir or config.PROFILES_DIR
        self.profiles_dir.mkdir(parents=True, exist_ok=True)
    
    def get_profile_path(self, user_id: str) -> Path:
        return self.profiles_dir / f"{user_id}.json"
    
    def profile_exists(self, user_id: str) -> bool:
        return self.get_profile_path(user_id).exists()
    
    def load_profile(self, user_id: str) -> UserProfile:
        profile_path = self.get_profile_path(user_id)
        
        if not profile_path.exists():
            return self.create_default_profile(user_id)
        
        try:
            with open(profile_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return UserProfile.from_dict(data)
        except (json.JSONDecodeError, KeyError) as e:
            return self.create_default_profile(user_id)
    
    def save_profile(self, profile: UserProfile) -> bool:
        try:
            profile_path = self.get_profile_path(profile.user_id)
            with open(profile_path, 'w', encoding='utf-8') as f:
                json.dump(profile.to_dict(), f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            return False
    
    def create_default_profile(self, user_id: str) -> UserProfile:
        default_data = {"user_id": user_id, **DEFAULT_PROFILE}
        profile = UserProfile.from_dict(default_data)
        self.save_profile(profile)
        return profile
    
    def delete_profile(self, user_id: str) -> bool:
        profile_path = self.get_profile_path(user_id)
        if profile_path.exists():
            profile_path.unlink()
            return True
        return False
    
    def list_profiles(self) -> list:
        profiles = []
        for profile_file in self.profiles_dir.glob("*.json"):
            try:
                with open(profile_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                profiles.append({
                    "user_id": data.get("user_id"),
                    "created_at": data.get("created_at"),
                    "diet_type": data.get("diet_type")
                })
            except:
                pass
        return profiles
