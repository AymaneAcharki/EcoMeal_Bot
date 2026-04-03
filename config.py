from pathlib import Path
import os

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
PROFILES_DIR = DATA_DIR / "profiles"
RECIPES_DIR = DATA_DIR / "recipes"
CONVERSATIONS_DIR = DATA_DIR / "conversations"

ALIMENTS_DB = DATA_DIR / "aliments.json"
RECIPES_DB = RECIPES_DIR / "recipes_db.json"
PRICES_DB = DATA_DIR / "prices.json"
SEASONS_DB = DATA_DIR / "seasons.json"
COUNTRY_CO2_DB = DATA_DIR / "country_co2.json"

# Load from .env file if exists
def load_env():
    env_file = BASE_DIR / ".env"
    if env_file.exists():
        with open(env_file, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ.setdefault(key.strip(), value.strip())

load_env()

# Provider: "lm_studio" or "huggingface"
LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "huggingface")

# LM Studio (local)
LM_STUDIO_BASE_URL = os.environ.get("LM_STUDIO_BASE_URL", "http://localhost:1234/v1")
LM_STUDIO_MODEL = os.environ.get("LM_STUDIO_MODEL", "qwen3.5:0.8b")

# Hugging Face (cloud)
HF_API_TOKEN = os.environ.get("HF_API_TOKEN", "")
HF_MODEL = os.environ.get("HF_MODEL", "Qwen/Qwen3.5-0.8B")

# Common settings
LLM_TEMPERATURE = 0.3
LLM_TOP_K = 40
LLM_TOP_P = 0.95
LLM_MIN_P = 0.05
LLM_REPEAT_PENALTY = 1.1
LLM_MAX_TOKENS_RECIPE = 800
LLM_MAX_TOKENS_GUIDED = 1500
LLM_MAX_TOKENS_CHAT = 1000
LLM_THINKING_ENABLED = False

# Aliases for backward compatibility
LM_STUDIO_TEMPERATURE = LLM_TEMPERATURE
LM_STUDIO_TOP_K = LLM_TOP_K
LM_STUDIO_TOP_P = LLM_TOP_P
LM_STUDIO_MIN_P = LLM_MIN_P
LM_STUDIO_REPEAT_PENALTY = LLM_REPEAT_PENALTY
LM_STUDIO_MAX_TOKENS_RECIPE = LLM_MAX_TOKENS_RECIPE
LM_STUDIO_MAX_TOKENS_GUIDED = LLM_MAX_TOKENS_GUIDED
LM_STUDIO_MAX_TOKENS_CHAT = LLM_MAX_TOKENS_CHAT
LM_STUDIO_THINKING_ENABLED = LLM_THINKING_ENABLED

CO2_THRESHOLDS = {
    "excellent": 0.5,
    "low": 1.5,
    "medium": 3.0,
    "high": 5.0,
    "very_high": float('inf')
}

CO2_LABELS = {
    "excellent": {"label": "Excellent", "color": "#27ae60", "emoji": "🌟"},
    "low": {"label": "Low", "color": "#2ecc71", "emoji": "✓"},
    "medium": {"label": "Medium", "color": "#f39c12", "emoji": "⚠"},
    "high": {"label": "High", "color": "#e67e22", "emoji": "🔶"},
    "very_high": {"label": "Very High", "color": "#e74c3c", "emoji": "🔴"}
}

FRENCH_AVG_CO2_PER_MEAL = 2.5

APP_VERSION = "2.0.0"
APP_TITLE = "EcoMeal Bot"
APP_ICON = "🌱"

CURRENCIES = ["EUR", "USD", "GBP"]
DEFAULT_CURRENCY = "EUR"
DEFAULT_WEEKLY_BUDGET = 100.0
DEFAULT_HOUSEHOLD_SIZE = 2
DEFAULT_COUNTRY = "France"

MAX_COOKING_TIME_DEFAULT = 60
MAX_RECIPE_HISTORY = 50
MAX_CHAT_HISTORY = 100

FALLBACK_RECIPES_COUNT = 6
