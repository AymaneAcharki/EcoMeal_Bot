from typing import Dict, List
from core.co2 import load_aliments_db, get_food_by_name


SUBSTITUTIONS_DB = {
    "Beef (steak)": {
        "substitutes": ["Lentils", "Chickpeas", "Tofu", "Tempeh", "Seitan"],
        "reason": "Plant-based proteins have 90-95% lower CO2 emissions",
        "savings_co2": 25.0
    },
    "Lamb": {
        "substitutes": ["Lentils", "Chickpeas", "Tofu"],
        "reason": "Lamb has very high environmental impact",
        "savings_co2": 18.0
    },
    "Pork": {
        "substitutes": ["Tofu", "Tempeh", "Chickpeas"],
        "reason": "Plant proteins reduce CO2 by 70-80%",
        "savings_co2": 6.0
    },
    "Chicken": {
        "substitutes": ["Tofu", "Tempeh", "Seitan"],
        "reason": "Poultry can be replaced with similar-texture plant proteins",
        "savings_co2": 5.0
    },
    "Cheese (hard)": {
        "substitutes": ["Tofu", "Nutritional yeast", "Cashew cheese"],
        "reason": "Dairy alternatives significantly reduce emissions",
        "savings_co2": 12.0
    },
    "Fish (farmed salmon)": {
        "substitutes": ["Tofu", "Tempeh", "Hearts of palm"],
        "reason": "Aquaculture has substantial environmental footprint",
        "savings_co2": 10.0
    },
    "Rice (white)": {
        "substitutes": ["Quinoa", "Potatoes", "Pasta"],
        "reason": "Rice paddies produce methane; alternatives have lower impact",
        "savings_co2": 1.5
    }
}


def get_all_substitutions() -> Dict:
    return SUBSTITUTIONS_DB


def get_substitution_for_ingredient(ingredient_name: str) -> Dict:
    for key, data in SUBSTITUTIONS_DB.items():
        if key.lower() in ingredient_name.lower() or ingredient_name.lower() in key.lower():
            return {
                'original': key,
                'substitutes': data['substitutes'],
                'reason': data['reason'],
                'co2_savings': data['savings_co2']
            }
    return {}


def suggest_multiple_substitutions(ingredients: List[str], max_suggestions: int = 3) -> List[Dict]:
    suggestions = []
    
    for ingredient in ingredients:
        sub = get_substitution_for_ingredient(ingredient)
        if sub:
            db = load_aliments_db()
            food = get_food_by_name(db, ingredient)
            
            if food:
                co2 = food.get('co2_kg', 0)
                suggestions.append({
                    'original': ingredient,
                    'original_co2': co2,
                    'substitutes': sub['substitutes'],
                    'reason': sub['reason'],
                    'potential_savings': sub['co2_savings']
                })
    
    suggestions.sort(key=lambda x: x['potential_savings'], reverse=True)
    
    return suggestions[:max_suggestions]


def calculate_substitution_impact(original_ingredients: List[Dict], 
                                  substitutions: Dict[str, str]) -> Dict:
    db = load_aliments_db()
    original_co2 = 0.0
    new_co2 = 0.0
    
    for ingredient in original_ingredients:
        food_id = ingredient.get('food_id')
        quantity_g = ingredient.get('quantity_g', 100)
        
        food = get_food_by_id(db, food_id)
        if food:
            name = food.get('name')
            co2_contribution = (food.get('co2_kg', 0) * quantity_g) / 1000
            original_co2 += co2_contribution
            
            if name in substitutions:
                substitute_name = substitutions[name]
                substitute_food = get_food_by_name(db, substitute_name)
                if substitute_food:
                    new_co2_contribution = (substitute_food.get('co2_kg', 0) * quantity_g) / 1000
                    new_co2 += new_co2_contribution
                else:
                    new_co2 += co2_contribution
            else:
                new_co2 += co2_contribution
    
    savings = original_co2 - new_co2
    percentage = (savings / original_co2 * 100) if original_co2 > 0 else 0
    
    return {
        'original_co2_kg': round(original_co2, 3),
        'new_co2_kg': round(new_co2, 3),
        'savings_kg': round(savings, 3),
        'savings_percentage': round(percentage, 1)
    }


from core.co2 import get_food_by_id
