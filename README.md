# EcoMeal Bot - Sustainable Recipe Chatbot

A Streamlit chatbot that suggests eco-friendly recipes, tracks CO2 emissions per meal
 and helps users plan sustainable weekly menus.

## Features

- 2000+ real recipes from 20 cuisines
- CO2 emission tracking per ingredient
- User profiles with dietary preferences
- Shopping list generation
- Weekly meal planning
- LLM-powered chat (LM Studio local)

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Start LM Studio

1. Download LM Studio from https://lmstudio.ai
2. Load model: `qwen3.5:0.8b` (or compatible)
3. Start local server on port 1234

### 3. Run the App

```bash
# Option A: Direct launch
python -m streamlit run app.py --server.port 8501

# Option B: With pre-flight checks
python run.py
```

### 4. Open Browser

Navigate to: http://localhost:8501

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
