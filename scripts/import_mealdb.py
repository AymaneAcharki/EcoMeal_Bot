"""
Import recipes from TheMealDB API.
Free public API key: "1"
Covers 17 countries with authentic recipes.
"""
import requests
import json
import time
from pathlib import Path

MEALDB_KEY = "1"
BASE = f"https://www.themealdb.com/api/json/v1/{MEALDB_KEY}"

# Countries we want to import
COUNTRIES = [
    'French', 'Italian', 'Spanish', 'Greek', 'British', 'Irish',
    'Moroccan', 'Indian', 'Chinese', 'Japanese', 'Thai', 'Vietnamese',
    'Mexican', 'American', 'Jamaican', 'Filipino', 'Russian'
]

def parse_measure(measure_str):
    """Parse measure string to extract quantity in grams."""
    if not measure_str:
        return 100

    measure_str = measure_str.lower().strip()

    # Common conversions
    conversions = {
        'cup': 240, 'cups': 240,
        'tablespoon': 15, 'tablespoons': 15, 'tbsp': 15,
        'teaspoon': 5, 'teaspoons': 5, 'tsp': 5,
        'ounce': 28, 'ounces': 28, 'oz': 28,
        'pound': 454, 'pounds': 454, 'lb': 454, 'lbs': 454,
        'kg': 1000, 'kilogram': 1000,
        'g': 1, 'gram': 1, 'grams': 1,
        'ml': 1, 'milliliter': 1,
        'l': 1000, 'liter': 1000, 'litre': 1000,
        'clove': 5, 'cloves': 5,
        'slice': 30, 'slices': 30,
        'piece': 50, 'pieces': 50,
        'whole': 100,
        'large': 150, 'medium': 100, 'small': 50,
    }

    # Try to extract number and unit
    import re
    numbers = re.findall(r'[\d.]+', measure_str)

    if not numbers:
        return 100

    qty = float(numbers[0])

    # Find unit
    for unit, grams in conversions.items():
        if unit in measure_str:
            return int(qty * grams)

    # Default: assume grams if just a number
    return int(qty) if qty > 10 else 100


def fetch_recipes_for_area(area, max_count=20):
    """Fetch recipes for a specific country/area."""
    print(f"Fetching {area}...")

    try:
        # Get list of meals for this area
        response = requests.get(f"{BASE}/filter.php?a={area}", timeout=30)
        meals = response.json().get('meals', [])

        if not meals:
            print(f"  No meals found for {area}")
            return []

        results = []
        for meal in meals[:max_count]:
            meal_id = meal['idMeal']

            # Get full details
            detail_resp = requests.get(f"{BASE}/lookup.php?i={meal_id}", timeout=30)
            detail_data = detail_resp.json()

            if not detail_data.get('meals'):
                continue

            detail = detail_data['meals'][0]

            # Parse ingredients
            ingredients = []
            for i in range(1, 21):
                name = detail.get(f'strIngredient{i}', '')
                measure = detail.get(f'strMeasure{i}', '')

                if name and name.strip():
                    ingredients.append({
                        "name": name.strip(),
                        "quantity_g": parse_measure(measure)
                    })

            # Parse instructions into steps
            instructions = detail.get('strInstructions', '')
            steps = [s.strip() for s in instructions.split('\r\n') if s.strip()]
            if not steps:
                steps = [s.strip() for s in instructions.split('\n') if s.strip()]
            if not steps:
                steps = [instructions]

            recipe = {
                "id": f"mealdb_{meal_id}",
                "name": detail['strMeal'],
                "cuisine": area.lower(),
                "category": detail.get('strCategory', ''),
                "ingredients": ingredients,
                "steps": steps,
                "image_url": detail.get('strMealThumb', ''),
                "source": "themealdb",
                "emblematic": True
            }

            results.append(recipe)
            time.sleep(0.3)  # Rate limiting

        print(f"  Got {len(results)} recipes")
        return results

    except Exception as e:
        print(f"  Error: {e}")
        return []


def main():
    """Import all recipes and save to JSON."""
    all_recipes = []

    for country in COUNTRIES:
        recipes = fetch_recipes_for_area(country, max_count=15)
        all_recipes.extend(recipes)
        time.sleep(0.5)

    # Save to file
    output_path = Path(__file__).parent.parent / "data" / "recipes" / "mealdb_recipes.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({
            "recipes": all_recipes,
            "total": len(all_recipes),
            "source": "themealdb",
            "countries": COUNTRIES
        }, f, indent=2, ensure_ascii=False)

    print(f"\nTotal: {len(all_recipes)} recipes saved to {output_path}")

    # Print stats
    by_country = {}
    for r in all_recipes:
        c = r['cuisine']
        by_country[c] = by_country.get(c, 0) + 1

    print("\nBy country:")
    for c, count in sorted(by_country.items()):
        print(f"  {c}: {count}")


if __name__ == "__main__":
    main()
