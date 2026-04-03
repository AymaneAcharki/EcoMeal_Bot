import json
import re
from typing import Dict, Optional, List
from pathlib import Path

# Load emblematic dish names at module level
_EMBLEMATIC_NAMES: Dict[str, str] = {}  # lowercase name -> cuisine

def _load_emblematic_names():
    """Load emblematic recipe names for dish detection."""
    global _EMBLEMATIC_NAMES
    if _EMBLEMATIC_NAMES:
        return  # Already loaded

    emblematic_path = Path(__file__).parent.parent / "data" / "emblematic_recipes.json"
    if emblematic_path.exists():
        try:
            with open(emblematic_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            for recipe in data.get("recipes", []):
                name = recipe.get("name", "")
                cuisine = recipe.get("cuisine", "unknown")
                if name:
                    _EMBLEMATIC_NAMES[name.lower()] = cuisine
        except Exception:
            pass

_load_emblematic_names()


def detect_dish_name(text: str) -> Optional[str]:
    """Detect if text contains an emblematic dish name or dish type.

    Returns the matched dish name (original case) or None.
    """
    if not text:
        return None

    text_lower = text.lower()

    # Detect cuisine in text to prioritize matching dishes from that cuisine
    detected_cuisine = None
    cuisine_aliases = {
        'italian': 'italian', 'italy': 'italian',
        'french': 'french', 'france': 'french',
        'indian': 'indian', 'india': 'indian',
        'chinese': 'chinese', 'china': 'chinese',
        'japanese': 'japanese', 'japan': 'japanese',
        'thai': 'thai', 'thailand': 'thai',
        'mexican': 'mexican', 'mexico': 'mexican',
        'korean': 'korean', 'korea': 'korean',
        'greek': 'greek', 'greece': 'greek',
        'spanish': 'spanish', 'spain': 'spanish',
        'vietnamese': 'vietnamese', 'vietnam': 'vietnamese',
        'moroccan': 'moroccan', 'morocco': 'moroccan',
        'brazilian': 'brazilian', 'brazil': 'brazilian',
        'british': 'british', 'uk': 'british',
        'jamaican': 'jamaican', 'jamaica': 'jamaican',
        'filipino': 'filipino', 'philippines': 'filipino',
    }
    for alias, cuisine in cuisine_aliases.items():
        if alias in text_lower:
            detected_cuisine = cuisine
            break

    # Check for emblematic dish names if loaded
    if _EMBLEMATIC_NAMES:
        # Check for exact matches first
        for name_lower, cuisine in _EMBLEMATIC_NAMES.items():
            if name_lower in text_lower:
                # If cuisine detected, only return dishes from that cuisine
                if detected_cuisine and cuisine != detected_cuisine:
                    continue
                return name_lower.title()

        # Check for key dish words (last word of dish name, usually the main identifier)
        # BUT exclude overly generic words
        generic_words = {'rice', 'chicken', 'beef', 'pork', 'soup', 'salad', 'pasta', 'curry', 'noodles', 'bread'}

        dish_keywords = {}
        for name_lower, cuisine in _EMBLEMATIC_NAMES.items():
            words = name_lower.split()
            if words:
                key_word = words[-1]  # Last word is usually the dish type
                # Skip generic words that cause false positives
                if key_word in generic_words:
                    continue
                if key_word not in dish_keywords:
                    dish_keywords[key_word] = []
                dish_keywords[key_word].append((name_lower, cuisine))

        # Check text for dish keywords
        text_words = set(text_lower.split())
        for keyword, dishes in dish_keywords.items():
            if keyword in text_words:
                # If cuisine detected, prioritize dishes from that cuisine
                if detected_cuisine:
                    for name_lower, cuisine in dishes:
                        if cuisine == detected_cuisine:
                            return name_lower.title()
                # Otherwise return first match
                return dishes[0][0].title()

        # Check for partial matches (dish name without cuisine prefix)
        for name_lower, cuisine in _EMBLEMATIC_NAMES.items():
            # If cuisine detected, only consider dishes from that cuisine
            if detected_cuisine and cuisine != detected_cuisine:
                continue

            name_words = name_lower.split()
            if len(name_words) >= 2:
                # For multi-word dishes, check if main words appear
                main_words = [w for w in name_words if len(w) > 3 and w not in generic_words]
                if main_words:
                    matches = sum(1 for w in main_words if w in text_lower)
                    if matches >= len(main_words) * 0.6:
                        return name_lower.title()

    return None


def detect_dish_type(text: str) -> Optional[str]:
    """Detect if text contains a dish type (stew, soup, salad, etc.).

    Returns the dish type or None.
    """
    if not text:
        return None

    text_lower = text.lower()

    # Dish types with variations
    dish_types = {
        'stew': ['stew', 'stewed'],
        'soup': ['soup', 'broth', 'bisque', 'chowder'],
        'salad': ['salad'],
        'curry': ['curry'],
        'pasta': ['pasta', 'spaghetti', 'penne', 'linguine', 'fettuccine', 'rigatoni'],
        'rice': ['risotto', 'pilaf', 'fried rice', 'rice bowl'],
        'sandwich': ['sandwich', 'burger', 'sub', 'panini'],
        'pizza': ['pizza'],
        'stir_fry': ['stir fry', 'stir-fry', 'wok'],
        'roast': ['roast', 'roasted'],
        'grilled': ['grill', 'grilled', 'bbq', 'barbecue'],
        'baked': ['bake', 'baked', 'casserole', 'gratin'],
        'fried': ['fried', 'deep fried', 'crispy'],
        'steamed': ['steamed', 'steam'],
        'raw': ['raw', 'tartare', 'carpaccio'],
    }

    for dish_type, keywords in dish_types.items():
        for kw in keywords:
            if kw in text_lower:
                return dish_type

    return None


def get_dish_cuisine(dish_name: str) -> Optional[str]:
    """Get the cuisine for a dish name."""
    if not dish_name or not _EMBLEMATIC_NAMES:
        return None
    return _EMBLEMATIC_NAMES.get(dish_name.lower())


def extract_json(text: str) -> Optional[Dict]:
    if not text:
        return None
    
    brace_depth = 0
    json_start = -1
    
    for i, char in enumerate(text):
        if char == '{':
            if brace_depth == 0:
                json_start = i
            brace_depth += 1
        elif char == '}':
            brace_depth -= 1
            if brace_depth == 0 and json_start != -1:
                json_str = text[json_start:i+1]
                try:
                    return json.loads(json_str)
                except json.JSONDecodeError:
                    continue
    
    return None


def parse_recipe(json_data: Dict) -> Dict:
    if not json_data:
        return get_fallback_recipe()
    
    required_fields = ['name', 'ingredients', 'steps']
    
    for field in required_fields:
        if field not in json_data:
            return get_fallback_recipe()
    
    ingredients = json_data.get('ingredients', [])
    validated_ingredients = []
    
    for ing in ingredients:
        if isinstance(ing, dict):
            validated_ingredients.append({
                'name': ing.get('name', 'Unknown ingredient'),
                'quantity_g': ing.get('quantity_g', ing.get('quantity', 100))
            })
        elif isinstance(ing, str):
            validated_ingredients.append({
                'name': ing,
                'quantity_g': 100
            })
    
    steps = json_data.get('steps', [])
    if not steps or not isinstance(steps, list):
        steps = ["Prepare ingredients", "Cook according to recipe", "Serve and enjoy"]
    
    recipe = {
        'name': json_data.get('name', 'Unnamed Recipe'),
        'description': json_data.get('description', ''),
        'ingredients': validated_ingredients,
        'steps': steps,
        'cooking_time_minutes': json_data.get('cooking_time_minutes', 30),
        'difficulty': json_data.get('difficulty', 'medium'),
        'sustainability_tip': json_data.get('sustainability_tip', 'Choose local, seasonal ingredients when possible')
    }
    
    return recipe


def parse_shopping_list(json_data: Dict) -> Dict:
    if not json_data:
        return {'missing_items': [], 'tips': []}
    
    return {
        'missing_items': json_data.get('missing_items', []),
        'tips': json_data.get('tips', [])
    }


def parse_intent(text: str) -> str:
    if not text:
        return 'unknown'

    text_lower = text.lower().strip()

    # Check for emblematic dish names first
    if detect_dish_name(text):
        return 'recipe_request'

    # Common food ingredients
    food_words = [
        'chicken', 'beef', 'pork', 'lamb', 'fish', 'salmon', 'shrimp', 'tofu',
        'rice', 'pasta', 'noodles', 'bread', 'potato', 'potatoes', 'quinoa',
        'tomato', 'tomatoes', 'onion', 'onions', 'garlic', 'carrot', 'carrots',
        'broccoli', 'spinach', 'mushroom', 'mushrooms', 'peppers', 'zucchini',
        'egg', 'eggs', 'cheese', 'milk', 'butter', 'cream',
        'beans', 'lentils', 'chickpeas', 'peas',
        'apple', 'banana', 'lemon', 'lime', 'orange',
        'olive', 'olives', 'avocado', 'coconut',
        'curry', 'soup', 'salad', 'stew', 'stir', 'fry', 'roast', 'bake',
        'sandwich', 'taco', 'burrito', 'pizza', 'pasta', 'risotto',
        'sushi', 'ramen', 'curry', 'stew', 'bowl'
    ]

    # Cuisine types
    cuisine_words = [
        'italian', 'french', 'moroccan', 'thai', 'chinese', 'japanese',
        'indian', 'mexican', 'korean', 'greek', 'spanish', 'vietnamese',
        'brazilian', 'british', 'irish', 'russian', 'jamaican', 'filipino',
        'cajun', 'creole', 'southern', 'american', 'asian', 'mediterranean'
    ]

    intent_patterns = {
        'modification': [
            r'\b(make it|change|modify|instead|replace|swap|adjust)\b',
            r'\bwithout\b',
            r'\bcan you\b.*\b(different|another|alternative)\b',
            r'\bturn it into\b',
            r'\badd\b.*\bto\b.*\b(recipe|it)\b',
            r'\b(more|less)\b.*\b(meat|cheese|spice|salt|sugar|sauce|cream)\b',
            r'\b(as a|in a|like a)\b\s*(sandwich|salad|soup|stew|bowl|wrap|pasta|curry)',
            r'\bwith (meat|chicken|beef|fish|shrimp|tofu|cheese)\b',
            r'\b(without|no|skip)\b.*\b(meat|cheese|dairy|gluten|nuts)\b',
            r'\b(same|similar|like)\b.*\b(but|however|just)\b',
            r'\b(healthier|lighter|heavier|bigger|smaller|spicier|milder)\b',
        ],
        'shopping_list': [
            r'\bshopping\b',
            r'\bbuy\b',
            r'\bneed\b.*\b(get|buy|store)\b',
            r'\bgroceries\b',
            r'\bwhat do i need\b'
        ],
        'weekly_plan': [
            r'\bweek\b.*\b(plan|menu|schedule)\b',
            r'\bweekly\b',
            r'\b7\s*day\b',
            r'\bmeal prep\b',
            r'\bplan.*\bmeals?\b',
            r'\bplan\s+my\s+week\b',
            r'\bweekly\s+menu\b',
            r'\bmenu\s+for\s+the\s+week\b',
            r'\bplan\s+my\s+meals\b',
            r'\bmeal\s*plan\b',
            r'\bdays?\s+meal\s*plan\b',
            r'\bweekly\s+meal\b',
            r'\bplan\s+for\s+\d+\s+days?\b',
            r'\bgive\s+me\s+a\s+weekly\b',
            r'\bcreate\s+a\s+meal\s*plan\b'
        ],
        'question': [
            r'\bhow\b.*\b(to|do|can|should|long|much|many)\b',
            r'\bwhat\b.*\b(is|are|does|if)\b',
            r'\bwhy\b',
            r'\bwhen\b.*\b(should|do)\b',
            r'\bwhich\b.*\b(is|are)\b',
            r'\bexplain\b',
            r'\btell me about\b',
            r'\bcan\s+i\b',
            r'\bshould\s+i\b',
            r'\bwhat\s+happens\b'
        ],
        'greeting': [
            r'^(hi|hello|hey|good morning|good evening|bonjour|hola|salut)',
            r'\bhow are you\b',
            r'\bnice to meet\b'
        ]
    }

    # Follow-up patterns: short phrases that refer to previous recipe context
    followup_patterns = [
        r'^(a|an|the)?\s*(sandwich|salad|soup|stew|bowl|wrap|curry|pasta|pizza|taco|burrito)',
        r'^(as a|in a|like a|make it a)\b',
        r'^(another|other|different|new|next)\b',
        r'^(with|add|plus|more|extra|include)\b',
        r'^(without|no|skip|minus|less|remove)\b',
        r'^(also|and|but|or|try|maybe)\b.*\b(with|add|include)\b',
        r'\?$',
    ]

    # Check for recipe request patterns FIRST (complete sentences are new requests)
    recipe_patterns = [
        # English
        r'\b(recipe|cook|prepare|dish|meal|dinner|lunch|breakfast|supper)\b',
        r'\bi (want|need|would like|feel like)\b.*\b(food|eat|something)\b',
        r'\bwhat can i\b.*\b(make|cook|eat)\b',
        r'\bi have\b.*\b(ingredients|in the fridge|at home)\b',
        r'\bsuggest\b',
        r'\bgive me\b',
        r'\brecipe with\b',
        r'\bsomething with\b',
        r'\bdish with\b',
        # French
        r'\b(recette|recettes|cuisiner|preparer|plat|repas|diner|dejeuner)\b',
        r'\bje (veux|veut|voudrais|souhaite|cherche|recherche)\b.*\b(recette|plat|repas)\b',
        r'\bquelle recette\b',
        r'\bavec des?\b.*\bje peux\b',
        r'\bdonne moi\b',
        r'\bpropose\b.*\brecette\b',
        r'\bun menu\b',
        r'\bprepare moi\b',
        # Portuguese
        r'\b(receita|receitas|cozinhar|preparar|prato|refeicao|jantar|almoco)\b',
        r'\bquero\b.*\b(receita|prato)\b',
        r'\bpreciso\b.*\b(receita|prato)\b',
        r'\bme de\b.*\b(receita|prato)\b',
        # Spanish
        r'\b(receta|recetas|cocinar|preparar|plato|comida|cena|almuerzo)\b',
        r'\bquiero\b.*\b(receta|plato)\b',
        r'\bnecesito\b.*\b(receta|plato)\b',
        r'\bdame\b.*\b(receta|plato)\b',
    ]

    # Short follow-ups (< 8 words starting with specific prefixes) skip recipe check
    word_count = len(text_lower.split())
    is_short_followup = word_count <= 7 and any(
        text_lower.startswith(p) for p in [
            'a ', 'an ', 'as ', 'in ', 'make it', 'change', 'with ',
            'without', 'no ', 'try ', 'same ', 'another', 'the ',
            'other', 'more ', 'less ', 'healthier', 'lighter', 'heavier',
            'bigger', 'smaller', 'spicier', 'milder', 'also ',
        ]
    )

    # Check weekly_plan FIRST (before recipe_request to avoid conflicts)
    for pattern in intent_patterns.get('weekly_plan', []):
        if re.search(pattern, text_lower):
            return 'weekly_plan'

    if not is_short_followup:
        for pattern in recipe_patterns:
            if re.search(pattern, text_lower):
                return 'recipe_request'

    # Then check specific intents (modification, shopping_list, etc.) - except weekly_plan already checked
    for intent, patterns in intent_patterns.items():
        if intent == 'weekly_plan':
            continue  # Already checked above
        for pattern in patterns:
            if re.search(pattern, text_lower):
                return intent

    for pattern in recipe_patterns:
        if re.search(pattern, text_lower):
            return 'recipe_request'

    # Check follow-up patterns BEFORE food words
    # These are short phrases that modify a previous recipe
    for pattern in followup_patterns:
        if re.search(pattern, text_lower):
            return 'modification'

    # Check if text contains food words (likely a recipe request)
    for word in food_words:
        if word in text_lower:
            return 'recipe_request'

    # Check if text contains cuisine words (likely a recipe request)
    for word in cuisine_words:
        if word in text_lower:
            return 'recipe_request'

    return 'unknown'


def get_fallback_recipe() -> Dict:
    return {
        'name': 'Simple Vegetable Stir-Fry',
        'description': 'A quick and sustainable vegetable stir-fry',
        'ingredients': [
            {'name': 'Broccoli', 'quantity_g': 150},
            {'name': 'Carrots', 'quantity_g': 100},
            {'name': 'Onions', 'quantity_g': 50},
            {'name': 'Tofu', 'quantity_g': 100}
        ],
        'steps': [
            'Cut vegetables into bite-sized pieces',
            'Heat oil in a wok or large pan over high heat',
            'Add tofu and cook until golden, about 3-4 minutes',
            'Add vegetables and stir-fry for 5-7 minutes',
            'Season with soy sauce and serve over rice'
        ],
        'cooking_time_minutes': 20,
        'difficulty': 'easy',
        'sustainability_tip': 'Use seasonal vegetables for lowest CO2 impact'
    }


def safe_response(raw_llm_response: str, expected_type: str = 'recipe') -> Dict:
    json_data = extract_json(raw_llm_response)
    
    if expected_type == 'recipe':
        return parse_recipe(json_data) if json_data else get_fallback_recipe()
    elif expected_type == 'shopping_list':
        return parse_shopping_list(json_data) if json_data else {'missing_items': [], 'tips': []}
    elif expected_type == 'weekly_plan':
        return json_data if json_data else {'days': [], 'total_estimated_cost': 0, 'total_estimated_co2': 0}
    
    return json_data or {}
