import json
from typing import List, Dict
from datetime import datetime
import config
from core.co2 import load_aliments_db, get_food_by_id
from core.ingredients import IngredientMatcher

# Module-level caches
_prices_db = None
_seasons_db = None
_aliments_db = None


def load_prices_db() -> Dict:
    global _prices_db
    if _prices_db is None:
        with open(config.PRICES_DB, 'r', encoding='utf-8') as f:
            _prices_db = json.load(f)
    return _prices_db


def load_seasons_db() -> Dict:
    global _seasons_db
    if _seasons_db is None:
        with open(config.SEASONS_DB, 'r', encoding='utf-8') as f:
            _seasons_db = json.load(f)
    return _seasons_db


def _get_aliments_db() -> Dict:
    global _aliments_db
    if _aliments_db is None:
        _aliments_db = load_aliments_db()
    return _aliments_db


def estimate_cost(ingredients: List[Dict], prices_db: Dict = None,
                  currency: str = "EUR") -> Dict:
    if prices_db is None:
        prices_db = load_prices_db()

    aliments = _get_aliments_db()
    prices = prices_db.get('prices', {})
    total_cost = 0.0
    items_with_cost = []

    for ingredient in ingredients:
        food_id = ingredient.get('food_id')
        quantity_g = ingredient.get('quantity_g', 100)

        food = get_food_by_id(aliments, food_id) if food_id else None

        if food:
            name = food.get('name', 'Unknown')
            price_per_kg = prices.get(name, 5.0)
            cost = (price_per_kg * quantity_g) / 1000
            total_cost += cost

            items_with_cost.append({
                'name': name,
                'quantity_g': quantity_g,
                'price_per_kg': price_per_kg,
                'cost': round(cost, 2),
                'currency': currency
            })
        elif ingredient.get('name'):
            # Fallback: use ingredient name directly
            name = ingredient['name']
            price_per_kg = prices.get(name, 5.0)
            cost = (price_per_kg * quantity_g) / 1000
            total_cost += cost

            items_with_cost.append({
                'name': name,
                'quantity_g': quantity_g,
                'price_per_kg': price_per_kg,
                'cost': round(cost, 2),
                'currency': currency
            })

    return {
        'total_cost': round(total_cost, 2),
        'currency': currency,
        'items': items_with_cost
    }


def generate_shopping_list(recipe_ingredients: List[Dict], pantry_items: List[str],
                          budget: float = None, currency: str = "EUR") -> Dict:
    """Generate a shopping list from recipe ingredients, excluding pantry items."""
    aliments = _get_aliments_db()
    matcher = IngredientMatcher(aliments)
    missing_items = []

    for ingredient in recipe_ingredients:
        food_id = ingredient.get('food_id')
        quantity_g = ingredient.get('quantity_g', 100)

        food = get_food_by_id(aliments, food_id) if food_id else None

        if not food:
            # Try matching by name
            ing_name = ingredient.get('name', '')
            if ing_name:
                food = matcher.match_ingredient(ing_name)

        if not food:
            continue

        name = food.get('name', 'Unknown')

        is_in_pantry = any(
            pantry_item.lower().strip() in name.lower() or
            name.lower() in pantry_item.lower().strip()
            for pantry_item in (pantry_items or [])
        )

        if not is_in_pantry:
            missing_items.append({
                'name': name,
                'food_id': food.get('id'),
                'quantity_g': quantity_g,
                'category': food.get('category'),
                'co2_kg': food.get('co2_kg')
            })

    cost_info = estimate_cost(missing_items, currency=currency)

    over_budget = False
    excess = 0.0
    if budget and cost_info['total_cost'] > budget:
        over_budget = True
        excess = round(cost_info['total_cost'] - budget, 2)

    current_month = datetime.now().month
    seasonal_info = check_seasonal(missing_items, current_month)

    return {
        'missing_items': missing_items,
        'total_cost': cost_info['total_cost'],
        'currency': currency,
        'items_with_cost': cost_info['items'],
        'seasonal_notes': seasonal_info,
        'over_budget': over_budget,
        'budget': budget,
        'excess': excess
    }


def check_seasonal(items: List[Dict], month: int, seasons_db: Dict = None) -> List[Dict]:
    if seasons_db is None:
        seasons_db = load_seasons_db()

    seasonal_data = seasons_db.get('seasonal', {})
    notes = []

    for item in items:
        name = item.get('name', '')

        for food_name, data in seasonal_data.items():
            if food_name.lower() in name.lower() or name.lower() in food_name.lower():
                peak_months = data.get('peak_months', [])
                available_months = data.get('available_months', [])
                is_imported = data.get('imported', False)

                if month not in available_months and not is_imported:
                    notes.append({
                        'item': name,
                        'status': 'out_of_season',
                        'note': f"{name} is out of season this month"
                    })
                elif month in peak_months:
                    notes.append({
                        'item': name,
                        'status': 'peak_season',
                        'note': f"{name} is at peak season!"
                    })
                elif is_imported:
                    notes.append({
                        'item': name,
                        'status': 'imported',
                        'note': f"{name} is imported (higher CO2)"
                    })
                break

    return notes
