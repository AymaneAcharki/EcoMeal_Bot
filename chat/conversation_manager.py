import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import config


class ConversationManager:
    def __init__(self):
        self.archive_dir: Path = config.CONVERSATIONS_DIR
        self.archive_dir.mkdir(parents=True, exist_ok=True)

    def create_new(self, messages: List[Dict] = None) -> Dict:
        conv_id = f"conv_{uuid.uuid4().hex[:8]}"
        now = datetime.now().isoformat()
        conversation = {
            "id": conv_id,
            "title": "New Conversation",
            "messages": messages or [],
            "stats": {"messages": 0, "recipes": 0},
            "created_at": now,
            "updated_at": now
        }
        return conversation

    def archive(self, conversation: Dict) -> None:
        conv_id = conversation.get("id", "unknown")
        conversation["updated_at"] = datetime.now().isoformat()
        filepath = self.archive_dir / f"{conv_id}.json"
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(conversation, f, indent=2, ensure_ascii=False)

    def load(self, conv_id: str) -> Optional[Dict]:
        filepath = self.archive_dir / f"{conv_id}.json"
        if not filepath.exists():
            return None
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, KeyError):
            return None

    def delete(self, conv_id: str) -> None:
        filepath = self.archive_dir / f"{conv_id}.json"
        if filepath.exists():
            filepath.unlink()

    def list_all(self) -> List[Dict]:
        conversations = []
        for filepath in sorted(self.archive_dir.glob("conv_*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                conversations.append({
                    "id": data.get("id", filepath.stem),
                    "title": data.get("title", "Untitled"),
                    "messages_count": len(data.get("messages", [])),
                    "recipes_count": data.get("stats", {}).get("recipes", 0),
                    "created_at": data.get("created_at", ""),
                    "updated_at": data.get("updated_at", "")
                })
            except (json.JSONDecodeError, KeyError):
                continue
        return conversations

    def auto_title(self, messages: List[Dict]) -> str:
        for msg in messages:
            if msg.get("role") == "user":
                content = msg.get("content", "").strip()
                if content:
                    title = content[:50]
                    if len(content) > 50:
                        title += "..."
                    return title
        return "New Conversation"

    def compute_stats(self, messages: List[Dict]) -> Dict:
        user_msgs = [m for m in messages if m.get("role") == "user"]
        recipes = [m for m in messages if m.get("type") == "recipe"]
        return {
            "messages": len(messages),
            "recipes": len(recipes)
        }
