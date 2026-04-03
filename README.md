---
title: EcoMeal Bot
emoji: 🌱
colorFrom: green
colorTo: blue
sdk: streamlit
sdk_version: "1.29.0"
app_file: app.py
pinned: false
license: mit
---

# EcoMeal Bot - Sustainable Recipe Chatbot

A Streamlit chatbot that suggests eco-friendly recipes, tracks CO2 emissions per meal
 and helps users plan sustainable weekly menus.

## Features

- 2000+ real recipes from 20 cuisines
- CO2 emission tracking per ingredient
- User profiles with dietary preferences
- Shopping list generation
- Weekly meal planning
- LLM-powered chat (Hugging Face or LM Studio local)

## Quick Start

### Option A: Hugging Face (Cloud - Recommended)

1. Get your HF API token from https://huggingface.co/settings/tokens
2. Set environment variable: `HF_API_TOKEN=hf_your_token_here`
3. Run:
```bash
pip install -r requirements.txt
streamlit run app.py
```

Or deploy directly to Hugging Face Spaces - the app will use the `HF_API_TOKEN` secret.

### Option B: LM Studio (Local)

1. Install dependencies: `pip install -r requirements.txt`
2. Download LM Studio from https://lmstudio.ai
3. Load model: `llama-3.2-1b-instruct`
4. Start local server on port 1234
5. Set `LLM_PROVIDER=lm_studio` in `.env`
6. Run: `streamlit run app.py`

## Model Selection

**Current model: `meta-llama/Llama-3.2-1B-Instruct`**

The project was originally designed for **Qwen3.5-0.8B**, offering an optimal balance of speed and quality for recipe generation. However, due to deployment constraints on the free Hugging Face Inference Providers tier, we switched to **Llama-3.2-1B-Instruct**:

| Model | Params | Quality | Speed | Free HF Tier |
|-------|--------|---------|-------|--------------|
| Qwen3.5-0.8B | 0.8B | ⭐⭐⭐ | ⚡⚡⚡ | ❌ Not available |
| Qwen2.5-1.5B | 1.5B | ⭐⭐⭐⭐ | ⚡⚡ | ❌ Not available |
| **Llama-3.2-1B** | 1B | ⭐⭐⭐⭐ | ⚡⚡⚡ | ✅ Available |

Llama-3.2-1B provides excellent instruction following and multilingual support (important for French recipes) and is available on the free Hugging Face Inference Providers tier.

## Project Structure

```
ECOMEAL/
  app.py              # Main Streamlit entry
  config.py           # Configuration constants
  run.py              # Pre-flight checks + launcher
  requirements.txt    # Python dependencies
  chat/
    engine.py         # ChatEngine - message processing
    prompts.py        # LLM prompt builders
    parser.py         # Intent classification
    history.py        # Conversation history
    conversation_manager.py
  core/
    co2.py            # CO2 calculations
    ingredients.py    # Ingredient matching
    recipe_search.py  # Recipe database search
    shopping.py       # Shopping list generation
    budget.py         # Budget management
    substitutions.py  # Ingredient substitutions
    carbon_tracker.py # LLM carbon tracking
  profile/
    models.py         # UserProfile dataclass
    manager.py        # Profile load/save
    defaults.py       # Default choices
  ui/
    styles.py         # CSS styling
    sidebar.py        # Sidebar UI
    chat_area.py      # Chat interface
    recipe_card.py    # Recipe display
    shopping_list.py  # Shopping list UI
    welcome_tab.py    # Home tab
    profile_tab.py    # Profile settings
    weekly_tab.py     # Weekly planning
  data/
    aliments.json     # Food CO2 database
    prices.json       # Price data
    seasons.json      # Seasonal availability
    country_co2.json  # Country CO2 multipliers
    emblematic_recipes.json
    recipes/
      recipes_db.json  # 2000+ recipes
    profiles/         # User profiles (auto-created)
    conversations/    # Chat history (auto-created)
```

## Configuration

Edit `config.py` to customize:

- LM Studio URL and model
- CO2 thresholds
- Default budget and currency

## Usage

1. **Select Profile**: Choose or create a profile in the sidebar
2. **Quick Ingredients**: Click ingredient buttons or type your own
3. **Ask for Recipes**: Type requests like "I want a vegetarian pasta recipe"
4. **Modify Recipes**: Ask for changes like "make it vegan" or "add beans"
5. **Get Shopping List**: Request shopping list for current recipe
6. **Weekly Plan**: Generate a full week of meals

## CO2 Data Sources

- ADEME (French Environment Agency)
- Agribalyse database
- Country-specific electricity grids

## License

MIT License - See LICENSE file for details.
