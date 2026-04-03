"""
Recipe search engine - finds real recipes from database by ingredients/cuisine.
Provides fallback mode when LLM is offline.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from random import choice
from datetime import datetime

import config
from core.co2 import load_aliments_db, calculate_meal_co2, get_co2_label, compare_to_average
from core.ingredients import IngredientMatcher
from core.substitutions import suggest_multiple_substitutions

BASE_DIR = Path(__file__).parent.parent / "data"
RECIPES_DB = BASE_DIR / "recipes" / "recipes_db.json"
MEALDB_DB = BASE_DIR / "recipes" / "mealdb_recipes.json"
ALIMENTS_DB = BASE_DIR / "aliments.json"
PRICES_DB = BASE_DIR / "prices.json"
SEASONS_DB = BASE_DIR / "seasons.json"

MEAT_KEYWORDS = {"beef", "lamb", "pork", "chicken", "turkey", "duck", "goose",
                  "bacon", "sausage", "ham", "prosciutto", "chorizo", "meat",
                  "steak", "minced", "shrimp", "salmon", "fish", "tuna",
                  "crab", "lobster", "anchovy", "scallop", "clam"}


class RecipeSearch:
    def __init__(self):
        self.aliments_db = load_aliments_db()
        self._load_db()
        self.matcher = IngredientMatcher(self.aliments_db)
        self._build_search_index()

    def _load_db(self):
        """Load recipes from both local DB and TheMealDB."""
        self.recipes = []
        self.metadata = {}

        # Load local recipes
        if RECIPES_DB.exists():
            with open(RECIPES_DB, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.recipes.extend(data.get("recipes", []))
            self.metadata.update(data.get("metadata", {}))

        # Load TheMealDB recipes (higher quality)
        if MEALDB_DB.exists():
            with open(MEALDB_DB, "r", encoding="utf-8") as f:
                data = json.load(f)
            mealdb_recipes = data.get("recipes", [])
            self.recipes.extend(mealdb_recipes)
            print(f"Loaded {len(mealdb_recipes)} TheMealDB recipes")

        # Separate emblematic recipes
        self.emblematic_recipes = [r for r in self.recipes if r.get("emblematic")]
        self.normal_recipes = [r for r in self.recipes if not r.get("emblematic")]

        self.cuisine_index: Dict[str, List[Dict]] = {}
        self.ingredient_index: Dict[str, List[int]] = {}
        self.tag_index: Dict[str, List[Dict]] = {}
        self.emblematic_by_name: Dict[str, Dict] = {}

        for recipe in self.recipes:
            cuisine = recipe.get("cuisine", "")
            if cuisine not in self.cuisine_index:
                self.cuisine_index[cuisine] = []
            self.cuisine_index[cuisine].append(recipe)

            for tag in recipe.get("tags", []):
                if tag not in self.tag_index:
                    self.tag_index[tag] = []
                self.tag_index[tag].append(recipe)

            for ing in recipe.get("ingredients", []):
                name_lower = ing.get("name", "").lower()
                if name_lower not in self.ingredient_index:
                    self.ingredient_index[name_lower] = []
                self.ingredient_index[name_lower].append(recipe["id"])

            # Index emblematic by name for direct lookup
            if recipe.get("emblematic"):
                self.emblematic_by_name[recipe["name"].lower()] = recipe

    def _build_search_index(self):
        important_words = {
            "chicken", "beef", "pork", "lamb", "turkey", "shrimp", "salmon",
            "fish", "tofu", "tempeh", "lentils", "chickpeas", "beans",
            "rice", "pasta", "bread", "flour", "noodles", "quinoa", "oats",
            "potato", "potatoes", "tomato", "tomatoes", "onion", "onions",
            "garlic", "carrot", "carrots", "pepper", "peppers", "broccoli",
            "spinach", "mushroom", "mushrooms", "celery", "corn", "peas",
            "zucchini", "eggplant", "cabbage", "lettuce", "kale", "ginger",
            "lemon", "lime", "orange", "apple", "apples", "banana", "bananas",
            "avocado", "coconut", "mango", "pineapple", "berries", "strawberries",
            "cheese", "milk", "butter", "cream", "yogurt", "egg", "eggs",
            "sugar", "honey", "oil", "vinegar", "soy sauce", "salsa",
            "cumin", "cinnamon", "turmeric", "paprika", "oregano", "basil",
            "parsley", "cilantro", "mint", "thyme", "rosemary", "dill",
            "salt", "pepper", "nutmeg", "coriander", "bay", "bay leaves",
            "olive", "olives", "caper", "capers", "sesame", "sesame seeds",
            "walnut", "walnuts", "almond", "almonds", "peanut", "peanuts",
            "cashew", "cashews", "pecan", "pecans", "pistachio", "hazelnut",
            "sausage", "bacon", "ham", "prosciutto", "pancetta", "chorizo",
            "crab", "lobster", "scallop", "clam", "mussel", "anchovy",
            "tuna", "cod", "sardine",
        }
        self.keyword_index: Dict[str, List[int]] = {}
        for recipe in self.recipes:
            recipe_id = recipe["id"]
            for ing in recipe.get("ingredients", []):
                ing_name = ing.get("name", "").lower()
                for word in important_words:
                    if word in ing_name:
                        if word not in self.keyword_index:
                            self.keyword_index[word] = []
                        self.keyword_index[word].append(recipe_id)
                        break

    def search_by_ingredients(self, user_ingredients: List[str],
                              cuisine: str = None, limit: int = 5,
                              exclude_ids: List[int] = None) -> List[Dict]:
        results = []
        user_lower = [i.lower() for i in user_ingredients]
        excluded = set(exclude_ids or [])

        candidate_ids: Dict[int, float] = {}
        for word in user_lower:
            matching_ids = set()
            for key, ids in self.keyword_index.items():
                if word in key or key in word:
                    matching_ids.update(ids)
            for rid in matching_ids:
                candidate_ids[rid] = candidate_ids.get(rid, 0) + 1

        if not candidate_ids:
            return []

        for rid, match_count in candidate_ids.items():
            if rid in excluded:
                continue
            recipe = self._get_recipe_by_id(rid)
            if not recipe:
                continue
            if cuisine and recipe.get("cuisine") != cuisine:
                continue
            total_ings = recipe.get("ingredient_count", 1)
            overlap = match_count / max(total_ings, 1)
            co2 = recipe.get("co2_total_kg", 2.5)
            # Eco bonus is a tiebreaker, not the main driver (max 3 pts vs 70 relevance)
            eco_bonus = max(0, 3.0 - co2) / 3.0
            score = (overlap * 70) + (eco_bonus * 3)
            results.append({"recipe": recipe, "score": score})

        results.sort(key=lambda x: -x["score"])
        return [r["recipe"] for r in results[:limit]]

    def search_by_cuisine(self, cuisine: str, limit: int = 10,
                          exclude_ids: List[int] = None) -> List[Dict]:
        recipes = self.cuisine_index.get(cuisine, [])
        if not recipes:
            return []
        excluded = set(exclude_ids or [])
        filtered = [r for r in recipes if r.get("id") not in excluded]

        # Prioritize emblematic recipes
        emblematic = [r for r in filtered if r.get("emblematic")]
        normal = [r for r in filtered if not r.get("emblematic")]

        # Sort emblematic by CO2 (best first), normal by ingredient count
        emblematic_sorted = sorted(emblematic, key=lambda r: r.get("co2_total_kg", 99))
        normal_sorted = sorted(normal, key=lambda r: (
            -r.get("ingredient_count", 0), r.get("co2_total_kg", 99)
        ))

        # Combine: emblematic first, then normal
        results = emblematic_sorted + normal_sorted
        return results[:limit]

    def search_random(self, cuisine: str = None,
                      prefer_low_co2: bool = True,
                      prefer_emblematic: bool = True,
                      exclude_ids: List[int] = None) -> Optional[Dict]:
        pool = self.cuisine_index.get(cuisine, self.recipes) if cuisine else self.recipes
        if not pool:
            pool = self.recipes
        if not pool:
            return None
        excluded = set(exclude_ids or [])
        filtered = [r for r in pool if r.get("id") not in excluded]
        if not filtered:
            filtered = pool  # fallback if all excluded

        # Prefer emblematic with low CO2 if both flags set
        if prefer_emblematic and prefer_low_co2:
            emblematic_low_co2 = sorted(
                [r for r in filtered if r.get("emblematic")],
                key=lambda r: r.get("co2_total_kg", 99)
            )
            if emblematic_low_co2:
                # Pick from top 50% of emblematic
                top_idx = max(1, len(emblematic_low_co2) // 2)
                return choice(emblematic_low_co2[:top_idx])

        if prefer_low_co2:
            # Pick from top 50% (not top 33%) to include meat dishes
            pool_sorted = sorted(filtered, key=lambda r: r.get("co2_total_kg", 99))
            top_idx = max(1, len(pool_sorted) // 2)
            return choice(pool_sorted[:top_idx])
        return choice(filtered)

    def search_emblematic(self, cuisine: str = None, limit: int = 5) -> List[Dict]:
        """Return emblematic recipes, optionally filtered by cuisine."""
        pool = self.emblematic_recipes
        if cuisine:
            pool = [r for r in pool if r.get("cuisine") == cuisine]
        return pool[:limit]

    def search_by_dish_name(self, dish_name: str) -> Optional[Dict]:
        """Find an emblematic recipe by its name."""
        return self.emblematic_by_name.get(dish_name.lower())

    def search_by_dish_type(self, dish_type: str, cuisine: str = None,
                            prefer_low_co2: bool = True, limit: int = 5) -> List[Dict]:
        """Find recipes by dish type (stew, soup, salad, etc.)."""
        # Map dish types to search keywords
        type_keywords = {
            'stew': ['stew', 'ragout', 'casserole', 'pot roast', 'goulash', 'hotpot'],
            'soup': ['soup', 'broth', 'bisque', 'chowder', 'pho', 'ramen', 'miso'],
            'salad': ['salad'],
            'curry': ['curry', 'korma', 'vindaloo', 'tikka', 'masala'],
            'pasta': ['pasta', 'spaghetti', 'penne', 'linguine', 'fettuccine', 'rigatoni', 'carbonara', 'bolognese'],
            'rice': ['risotto', 'pilaf', 'fried rice', 'rice bowl', 'biryani'],
            'sandwich': ['sandwich', 'burger', 'panini'],
            'pizza': ['pizza'],
            'stir_fry': ['stir fry', 'stir-fry', 'wok', 'sautéed'],
            'roast': ['roast', 'roasted', 'baked'],
            'grilled': ['grill', 'grilled', 'bbq', 'barbecue'],
            'fried': ['fried', 'crispy', 'fritter'],
            'steamed': ['steamed', 'steam'],
        }

        keywords = type_keywords.get(dish_type, [dish_type])
        results = []

        # Meat keywords for filtering
        meat_keywords = {'beef', 'chicken', 'pork', 'lamb', 'meat', 'sausage', 'bacon',
                         'turkey', 'duck', 'shrimp', 'salmon', 'fish'}

        # Dessert/breakfast keywords to exclude from savory dishes
        dessert_keywords = {'sugar', 'juice', 'lemon', 'sweet', 'cake', 'cookie', 'dessert',
                            'fruit', 'cream', 'chocolate', 'honey', 'syrup', 'compote'}

        for recipe in self.recipes:
            if cuisine and recipe.get("cuisine") != cuisine:
                continue

            name_lower = recipe.get("name", "").lower()

            # Check if any keyword matches the recipe name
            if any(kw in name_lower for kw in keywords):
                # Skip dessert/breakfast items for savory dish searches
                if dish_type in ['stew', 'soup', 'curry', 'stir_fry', 'roast', 'grilled', 'fried']:
                    if any(dw in name_lower for dw in dessert_keywords):
                        continue  # Skip dessert recipes

                    if recipe.get("ingredient_count", 0) < 3:
                        continue  # Skip recipes with too few ingredients

                co2 = recipe.get("co2_total_kg", 2.5)

                # Check if recipe has meat ingredients
                has_meat = False
                for ing in recipe.get("ingredients", []):
                    ing_name = ing.get("name", "").lower()
                    if any(mk in ing_name for mk in meat_keywords):
                        has_meat = True
                        break

                # Score: prefer lower CO2, but also consider if user wants meat
                score = 100 - co2 * 10
                if has_meat:
                    score += 5  # Slight boost for meat versions
                if recipe.get("emblematic"):
                    score += 10  # Boost emblematic recipes

                results.append({"recipe": recipe, "score": score, "has_meat": has_meat})

        # Sort by score
        results.sort(key=lambda x: -x["score"])

        return [r["recipe"] for r in results[:limit]]

    def get_recipe_by_id(self, recipe_id: int) -> Optional[Dict]:
        return self._get_recipe_by_id(recipe_id)

    def _get_recipe_by_id(self, recipe_id: int) -> Optional[Dict]:
        for recipe in self.recipes:
            if recipe.get("id") == recipe_id:
                return recipe
        return None

    def format_recipe_for_display(self, recipe: Dict, profile=None) -> Dict:
        ingredients_for_co2 = []
        for ing in recipe.get("ingredients", []):
            food_id = ing.get("food_id")
            qty = ing.get("quantity_g", 100)
            if food_id:
                ingredients_for_co2.append({"food_id": food_id, "quantity_g": qty})

        country = getattr(profile, "country", None) if profile else None
        co2_info = calculate_meal_co2(ingredients_for_co2, self.aliments_db, country=country)
        co2_label = get_co2_label(co2_info["total_co2_kg"])
        comparison = compare_to_average(co2_info["total_co2_kg"], country=country)

        formatted_ingredients = []
        for ing in recipe.get("ingredients", []):
            formatted_ingredients.append({
                "name": ing.get("name", "Unknown"),
                "quantity_g": ing.get("quantity_g", 100)
            })

        substitutions = suggest_multiple_substitutions(
            [i.get("name") for i in formatted_ingredients]
        )

        ing_count = recipe.get("ingredient_count", len(formatted_ingredients))
        difficulty = "easy" if ing_count <= 6 else "medium" if ing_count <= 12 else "advanced"
        cooking_time = recipe.get("cooking_time_minutes", min(20 + ing_count * 3, 90))

        # Use real steps from DB if available, otherwise placeholder
        steps = recipe.get("steps", [])
        if not steps:
            steps = [f"Combine all ingredients and cook for approximately {cooking_time} minutes."]

        formatted = {
            "name": recipe.get("name", "Unknown Recipe"),
            "cuisine": recipe.get("cuisine", "unknown"),
            "description": f"A {recipe.get('cuisine', '').title()} recipe with {ing_count} ingredients",
            "ingredients": formatted_ingredients,
            "steps": steps,
            "cooking_time_minutes": cooking_time,
            "difficulty": difficulty,
            "co2_info": co2_info,
            "co2_label": co2_label,
            "comparison": comparison,
            "substitutions": substitutions,
            "sustainability_tip": self._generate_tip(co2_info["total_co2_kg"], recipe.get("cuisine", "")),
            "source": "database",
            "database_id": recipe.get("id")
        }
        return formatted

    def _generate_tip(self, co2_kg: float, cuisine: str) -> str:
        if co2_kg <= 0.5:
            return f"Excellent low-carbon footprint! This {cuisine} dish is well below the French average."
        elif co2_kg <= 1.5:
            return f"Good CO2 score for a {cuisine} meal. Consider seasonal vegetables to reduce further."
        elif co2_kg <= 3.0:
            return f"Average impact. Try replacing some ingredients with plant-based alternatives."
        return f"Higher carbon footprint. Consider swapping meat for lentils or chickpeas."

    def get_stats(self) -> Dict:
        return {
            "total_recipes": len(self.recipes),
            "cuisines": list(self.cuisine_index.keys()),
            "cuisine_counts": {c: len(r) for c, r in self.cuisine_index.items()},
            "avg_co2_by_cuisine": {
                c: round(sum(r.get("co2_total_kg", 0) for r in recipes) / len(recipes), 2)
                for c, recipes in self.cuisine_index.items()
            }
        }
