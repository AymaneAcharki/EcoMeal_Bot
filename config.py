from pathlib import Path

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

LM_STUDIO_BASE_URL = "http://localhost:1234/v1"
LM_STUDIO_MODEL = "qwen3.5:0.8b"
LM_STUDIO_TEMPERATURE = 0.3
LM_STUDIO_TOP_K = 40
LM_STUDIO_TOP_P = 0.95
LM_STUDIO_MIN_P = 0.05
LM_STUDIO_REPEAT_PENALTY = 1.1
LM_STUDIO_MAX_TOKENS_RECIPE = 800
LM_STUDIO_MAX_TOKENS_GUIDED = 1500
LM_STUDIO_MAX_TOKENS_CHAT = 1000
LM_STUDIO_THINKING_ENABLED = False

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
