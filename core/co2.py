import json
from typing import Dict, List, Tuple
import config

# Module-level cache for country data
_country_data = None


def load_aliments_db() -> Dict:
    with open(config.ALIMENTS_DB, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_country_co2() -> Dict:
    """Load country-specific CO2 multipliers."""
    global _country_data
    if _country_data is None:
        country_path = config.DATA_DIR / "country_co2.json"
        with open(country_path, 'r', encoding='utf-8') as f:
            _country_data = json.load(f)
    return _country_data


def get_country_multiplier(country: str) -> float:
    """Get the CO2 multiplier for a given country (1.0 = France baseline)."""
    data = load_country_co2()
    countries = data.get("countries", {})
    if country in countries:
        return countries[country].get("multiplier", 1.0)
    return 1.0


def get_country_avg_meal_co2(country: str) -> float:
    """Get the average CO2 per meal for a given country."""
    data = load_country_co2()
    countries = data.get("countries", {})
    if country in countries:
        return countries[country].get("avg_co2_meal_kg", 2.5)
    return 2.5


def get_food_by_id(db: Dict, food_id: int) -> Dict:
    for food in db.get('foods', []):
        if food.get('id') == food_id:
            return food
    return {}


def get_food_by_name(db: Dict, name: str) -> Dict:
    name_lower = name.lower()
    for food in db.get('foods', []):
        if name_lower in food.get('name', '').lower():
            return food
    return {}


def calculate_meal_co2(ingredients: List[Dict], db: Dict = None,
                       country: str = None) -> Dict:
    """Calculate meal CO2 with optional country multiplier."""
    if db is None:
        db = load_aliments_db()

    multiplier = get_country_multiplier(country) if country else 1.0

    total_co2 = 0.0
    breakdown = []

    for ingredient in ingredients:
        food_id = ingredient.get('food_id')
        quantity_g = ingredient.get('quantity_g', 100)

        food = get_food_by_id(db, food_id)
        if food:
            co2_per_kg = food.get('co2_kg', 0)
            co2_for_item = (co2_per_kg * quantity_g) / 1000
            co2_adjusted = co2_for_item * multiplier
            total_co2 += co2_adjusted

            breakdown.append({
                'name': food.get('name'),
                'quantity_g': quantity_g,
                'co2_kg': round(co2_adjusted, 3),
                'co2_base_kg': round(co2_for_item, 3),
                'category': food.get('category')
            })

    return {
        'total_co2_kg': round(total_co2, 3),
        'country': country,
        'country_multiplier': multiplier,
        'breakdown': breakdown
    }


def get_co2_label(co2_kg: float) -> Dict:
    if co2_kg <= config.CO2_THRESHOLDS['excellent']:
        return config.CO2_LABELS['excellent']
    elif co2_kg <= config.CO2_THRESHOLDS['low']:
        return config.CO2_LABELS['low']
    elif co2_kg <= config.CO2_THRESHOLDS['medium']:
        return config.CO2_LABELS['medium']
    elif co2_kg <= config.CO2_THRESHOLDS['high']:
        return config.CO2_LABELS['high']
    else:
        return config.CO2_LABELS['very_high']


def get_substitution(ingredient_name: str, db: Dict = None) -> Dict:
    if db is None:
        db = load_aliments_db()
    
    food = get_food_by_name(db, ingredient_name)
    if not food:
        return {}
    
    category = food.get('category')
    current_co2 = food.get('co2_kg', 0)
    
    substitutions = {
        'meat': ['Tofu', 'Tempeh', 'Lentils', 'Chickpeas', 'Seitan'],
        'fish': ['Tofu', 'Tempeh', 'Chickpeas'],
        'dairy': ['Tofu', 'Tempeh']
    }
    
    if category in substitutions:
        for sub_name in substitutions[category]:
            sub_food = get_food_by_name(db, sub_name)
            if sub_food and sub_food.get('co2_kg', float('inf')) < current_co2:
                reduction = current_co2 - sub_food.get('co2_kg', 0)
                return {
                    'original': food.get('name'),
                    'substitute': sub_food.get('name'),
                    'co2_original': current_co2,
                    'co2_substitute': sub_food.get('co2_kg'),
                    'reduction_kg': round(reduction, 2),
                    'reduction_pct': round((reduction / current_co2) * 100, 1)
                }
    
    return {}


def compare_to_average(co2_kg: float, country: str = None) -> Dict:
    if country:
        avg = get_country_avg_meal_co2(country)
    else:
        avg = config.FRENCH_AVG_CO2_PER_MEAL

    difference = co2_kg - avg
    percentage = ((co2_kg - avg) / avg) * 100 if avg > 0 else 0

    return {
        'average': avg,
        'your_meal': co2_kg,
        'difference_kg': round(difference, 3),
        'percentage': round(percentage, 1),
        'status': 'below' if co2_kg < avg else 'above',
        'country': country
    }
