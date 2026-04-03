import json
from typing import Dict, List, Optional
from datetime import datetime
import requests
from openai import OpenAI

from profile.models import UserProfile
from chat.prompts import (
    SYSTEM_PROMPT, build_recipe_prompt, build_shopping_list_prompt,
    build_follow_up_prompt, build_intent_classify_prompt, build_weekly_plan_prompt
)
from chat.parser import extract_json, parse_recipe, parse_intent, safe_response, get_fallback_recipe, detect_dish_name, get_dish_cuisine, detect_dish_type
from chat.history import ConversationHistory
from core.co2 import load_aliments_db, calculate_meal_co2, get_co2_label, compare_to_average
from core.ingredients import IngredientMatcher
from core.shopping import generate_shopping_list, estimate_cost
from core.budget import BudgetManager
from core.substitutions import suggest_multiple_substitutions
from core.recipe_search import RecipeSearch
from core.carbon_tracker import CarbonTracker
import config


class ChatEngine:
    def __init__(self, profile: UserProfile):
        self.profile = profile
        self.history = ConversationHistory()
        self.co2_db = load_aliments_db()
        self.ingredient_matcher = IngredientMatcher(self.co2_db)
        self.budget_manager = BudgetManager(
            weekly_budget=profile.weekly_budget,
            currency=profile.currency
        )

        # Load real recipe database
        try:
            self.recipe_search = RecipeSearch()
        except Exception:
            self.recipe_search = None

        # Carbon tracker for LLM inference emissions
        country = getattr(profile, 'country', 'France')
        self.carbon_tracker = CarbonTracker(
            country=country,
            hardware="RTX 4060 Laptop",
            ram_gb=16
        )

        self.client = OpenAI(
            base_url=config.LM_STUDIO_BASE_URL,
            api_key="not-needed"
        )
        self.thinking_enabled = config.LM_STUDIO_THINKING_ENABLED
        self.llm_params = {
            "temperature": config.LM_STUDIO_TEMPERATURE,
            "top_p": config.LM_STUDIO_TOP_P,
        }
        self.llm_extra = {
            "top_k": config.LM_STUDIO_TOP_K,
            "min_p": config.LM_STUDIO_MIN_P,
            "repeat_penalty": config.LM_STUDIO_REPEAT_PENALTY,
        }
        self.llm_available = self._test_connection()

    def _call_llm(self, messages: List[Dict], max_tokens: int,
                  temperature: float = None) -> str:
        """Unified LLM call with all parameters synced to LM Studio settings."""
        params = {
            "model": config.LM_STUDIO_MODEL,
            "messages": messages,
            "max_tokens": max_tokens,
        }
        if temperature is not None:
            params["temperature"] = temperature
        else:
            params.update(self.llm_params)
        params["extra_body"] = dict(self.llm_extra)

        if self.thinking_enabled:
            params["extra_body"]["enable_thinking"] = True

        # Track carbon emissions for this LLM call
        start_time = self.carbon_tracker.start_call()

        response = self.client.chat.completions.create(**params)
        content = response.choices[0].message.content or ""

        # Record emissions
        tokens = getattr(response.usage, 'completion_tokens', 0) if response.usage else 0
        self.carbon_tracker.end_call(start_time, tokens_generated=tokens)

        # Strip thinking blocks from output if present
        if self.thinking_enabled:
            content = self._strip_thinking(content)

        return content

    def _strip_thinking(self, text: str) -> str:
        """Remove <think|...> or <thinking>...</thinking> blocks from LLM output."""
        import re
        text = re.sub(r'<think\b[^>]*>.*?</think\s*>', '', text, flags=re.DOTALL)
        text = re.sub(r'<thinking\b[^>]*>.*?</thinking\s*>', '', text, flags=re.DOTALL)
        return text.strip()

    def _test_connection(self) -> bool:
        try:
            response = self.client.chat.completions.create(
                model=config.LM_STUDIO_MODEL,
                messages=[{"role": "user", "content": "test"}],
                max_tokens=10
            )
            return True
        except:
            return False

    def process_message(self, user_text: str, pantry_items: List[str] = None,
                       constraints: Dict = None) -> Dict:
        self.history.add_message('user', user_text)

        intent = parse_intent(user_text)

        pantry = pantry_items or []

        # Track total request processing (DB search + LLM if used)
        start_time = self.carbon_tracker.start_call()

        if intent == 'greeting':
            response = self._handle_greeting()
        elif intent == 'recipe_request':
            response = self._handle_recipe_request(user_text, pantry, constraints)
        elif intent == 'modification':
            response = self._handle_modification(user_text, constraints)
        elif intent == 'shopping_list':
            response = self._handle_shopping_list_request(pantry, constraints)
        elif intent == 'weekly_plan':
            response = self._handle_weekly_plan(pantry, constraints)
        elif intent == 'question':
            response = self._handle_question(user_text)
        else:
            response = self._handle_unknown(user_text)

        # Record processing emissions (covers DB search + any LLM calls)
        self.carbon_tracker.end_call(start_time, tokens_generated=0, call_type=intent)

        self.history.add_message('assistant', response.get('message', ''), response)

        return response

    def _handle_greeting(self) -> Dict:
        message = "Hello! I'm EcoChef, your sustainable cooking assistant.\n\n"
        message += "I can help you:\n"
        message += "- Generate eco-friendly recipes based on your ingredients\n"
        message += "- Create shopping lists with seasonal tips\n"
        message += "- Plan your weekly meals within budget\n"
        message += "- Suggest sustainable ingredient swaps\n\n"

        if self.recipe_search:
            stats = self.recipe_search.get_stats()
            db_recipes = stats["total_recipes"]
            cuisines = ", ".join(stats["cuisines"][:6])
            message += f"I have {db_recipes} real recipes from {len(stats['cuisines'])} cuisines ({cuisines}...) ready to suggest!\n\n"

        message += "Select your ingredients and preferences, then tell me what you'd like to cook!"
        return {'message': message, 'type': 'greeting'}

    def _handle_recipe_request(self, user_text: str, pantry_items: List[str],
                               constraints: Dict = None) -> Dict:
        # Check for pure search mode
        pure_search = constraints.get("pure_search", False) if constraints else False

        # Check for Fridge Waste Reducing mode - when OFF, prefer emblematic recipes
        prefer_emblematic = constraints.get("prefer_emblematic", False) if constraints else False

        # Check for specific dish name first
        dish_name = detect_dish_name(user_text)

        # Only use pantry items if Fridge Waste Reducing is ON
        effective_pantry = pantry_items if not prefer_emblematic else []

        ingredients = self.ingredient_matcher.extract_ingredients_from_text(user_text)

        if not ingredients and effective_pantry:
            ingredients = self.ingredient_matcher.extract_ingredients_from_text(' '.join(effective_pantry))

        ingredient_names = [i.get('name') for i in ingredients] if ingredients else []
        if not ingredient_names and effective_pantry:
            ingredient_names = effective_pantry

        focus_mode = "co2"
        if constraints:
            focus_mode = constraints.get("focus_mode", "co2")

        # Detect if user explicitly wants meat -> don't force low CO2
        meat_keywords = {"chicken", "beef", "pork", "lamb", "turkey", "duck",
                         "steak", "meat", "shrimp", "salmon", "fish", "tuna",
                         "bacon", "sausage", "ham", "shrimp"}
        text_lower = user_text.lower()
        user_wants_meat = any(kw in text_lower for kw in meat_keywords)

        # Detect if user wants NO meat (vegetarian)
        vegetarian_keywords = {"vegetarian", "no meat", "without meat", "meat-free",
                               "meat free", "meatless", "plant-based", "veggie"}
        user_wants_vegetarian = any(kw in text_lower for kw in vegetarian_keywords)

        # Detect if user wants vegan
        vegan_keywords = {"vegan", "plant-based", "dairy-free", "no animal"}
        user_wants_vegan = any(kw in text_lower for kw in vegan_keywords)

        prefer_low_co2 = (focus_mode == "co2") and not user_wants_meat

        # Extract cuisine - in pure search mode, only detect from text, not profile
        # Skip profile cuisine when user mentions ANY ingredient or pantry item
        has_any_ingredients = len(ingredients) >= 1 or len(pantry_items) >= 1
        if pure_search or has_any_ingredients:
            cuisine = self._detect_cuisine_from_text_only(user_text)
        else:
            cuisine = self._detect_cuisine(user_text, constraints)

        # Get already-shown recipe IDs to avoid duplicates
        exclude_ids = self.history.get_shown_recipe_ids()

        # === PRIORITY 0: DISH TYPE MATCH (stew, soup, etc.) ===
        # First check UI constraint, then detect from text
        dish_type = constraints.get("dish_type") if constraints else None
        if not dish_type:
            dish_type = detect_dish_type(user_text)
        if dish_type and self.recipe_search:
            db_recipes = self.recipe_search.search_by_dish_type(dish_type, cuisine=cuisine, limit=10)
            if db_recipes:
                # Check if user wants meat
                wants_meat = any(mk in text_lower for mk in ['meat', 'beef', 'chicken', 'pork', 'lamb', 'sausage', 'bacon'])

                # Filter recipes that match the meat preference
                good_match = None
                for recipe in db_recipes:
                    # Check if recipe has meat ingredients
                    recipe_has_meat = False
                    for ing in recipe.get("ingredients", []):
                        ing_name = ing.get("name", "").lower()
                        if any(mk in ing_name for mk in ['beef', 'chicken', 'pork', 'lamb', 'meat', 'sausage', 'bacon', 'turkey', 'duck', 'shrimp', 'salmon', 'fish']):
                            recipe_has_meat = True
                            break

                    # If user wants meat and recipe has meat, OR user doesn't want meat and recipe doesn't have meat
                    if wants_meat == recipe_has_meat:
                        good_match = recipe
                        break

                # If no perfect match, take the first one anyway (user might be flexible)
                if not good_match:
                    good_match = db_recipes[0]

                formatted = self.recipe_search.format_recipe_for_display(good_match, self.profile)
                formatted['source'] = 'database'
                formatted['database_id'] = good_match.get('id')
                self.history.set_current_recipe(formatted)
                return {
                    'message': f"Here's a recipe for **{formatted['name']}**!",
                    'type': 'recipe',
                    'recipe': formatted
                }

        # === PRIORITY 1: DIRECT DISH NAME MATCH ===
        if dish_name and self.recipe_search:
            db_recipe = self.recipe_search.search_by_dish_name(dish_name)
            if db_recipe:
                formatted = self.recipe_search.format_recipe_for_display(db_recipe, self.profile)
                formatted['source'] = 'database'
                formatted['database_id'] = db_recipe.get('id')
                self.history.set_current_recipe(formatted)
                return {
                    'message': f"Here's the recipe for **{formatted['name']}**!",
                    'type': 'recipe',
                    'recipe': formatted
                }

        # === PRIORITY 2: DATABASE ===
        db_recipe = None
        if self.recipe_search:
            if ingredient_names:
                # In pure search, search across ALL cuisines
                results = self.recipe_search.search_by_ingredients(
                    ingredient_names, cuisine=cuisine, limit=10,
                    exclude_ids=exclude_ids
                )
                # Filter for vegetarian/vegan if requested
                if user_wants_vegetarian or user_wants_vegan:
                    results = [r for r in results if self._is_recipe_vegetarian(r, user_wants_vegan)]
                if results:
                    db_recipe = self.recipe_search.format_recipe_for_display(
                        results[0], self.profile
                    )
                    db_recipe['source'] = 'database'
                    db_recipe['database_id'] = results[0].get('id')

            if not db_recipe:
                # Try multiple times to find a vegetarian/vegan recipe
                max_attempts = 5 if (user_wants_vegetarian or user_wants_vegan) else 1
                # When Fridge Waste Reducing is OFF (prefer_emblematic=True), prioritize emblematic recipes
                emblematic_priority = prefer_emblematic
                for attempt in range(max_attempts):
                    random_recipe = self.recipe_search.search_random(
                        cuisine=cuisine, prefer_low_co2=prefer_low_co2,
                        prefer_emblematic=emblematic_priority,
                        exclude_ids=exclude_ids
                    )
                    if random_recipe:
                        if user_wants_vegetarian or user_wants_vegan:
                            if self._is_recipe_vegetarian(random_recipe, user_wants_vegan):
                                db_recipe = self.recipe_search.format_recipe_for_display(
                                    random_recipe, self.profile
                                )
                                db_recipe['source'] = 'database'
                                db_recipe['database_id'] = random_recipe.get('id')
                                break
                            else:
                                exclude_ids.append(random_recipe.get('id'))
                        else:
                            db_recipe = self.recipe_search.format_recipe_for_display(
                                random_recipe, self.profile
                            )
                            db_recipe['source'] = 'database'
                            db_recipe['database_id'] = random_recipe.get('id')
                            break

        # DB found -> return immediately
        if db_recipe:
            self.history.set_current_recipe(db_recipe)
            return {
                'message': f"Here's a recipe for you: **{db_recipe['name']}**",
                'type': 'recipe',
                'recipe': db_recipe
            }

        # === PRIORITY 2: LLM (only if DB found nothing) ===
        if self.llm_available:
            try:
                prompt = build_recipe_prompt(
                    ingredient_names,
                    self.profile.to_dict(),
                    constraints=constraints,
                    focus_mode=focus_mode
                )
                raw = self._call_llm(
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=config.LM_STUDIO_MAX_TOKENS_RECIPE
                )
                recipe_data = safe_response(raw, 'recipe')
                recipe = parse_recipe(recipe_data)

                # Calculate CO2 for LLM recipe
                ingredients_for_co2 = []
                for ing in recipe.get('ingredients', []):
                    food = self.ingredient_matcher.match_ingredient(ing.get('name', ''))
                    if food:
                        ingredients_for_co2.append({
                            'food_id': food.get('id'),
                            'quantity_g': ing.get('quantity_g', 100)
                        })

                co2_info = calculate_meal_co2(ingredients_for_co2, self.co2_db, country=self.profile.country)
                recipe['co2_info'] = co2_info
                recipe['co2_label'] = get_co2_label(co2_info['total_co2_kg'])
                recipe['comparison'] = compare_to_average(co2_info['total_co2_kg'], country=self.profile.country)

                substitutions = suggest_multiple_substitutions(
                    [i.get('name') for i in recipe.get('ingredients', [])]
                )
                recipe['substitutions'] = substitutions

                self.history.set_current_recipe(recipe)

                return {
                    'message': f"Here's a recipe for you: **{recipe['name']}**",
                    'type': 'recipe',
                    'recipe': recipe
                }
            except:
                pass

        # === PRIORITY 3: Generic fallback ===
        recipe = get_fallback_recipe()
        recipe['source'] = 'fallback'
        self.history.set_current_recipe(recipe)
        return {
            'message': f"Here's a recipe for you: **{recipe['name']}**",
            'type': 'recipe',
            'recipe': recipe
        }

    def _is_recipe_vegetarian(self, recipe: Dict, vegan: bool = False) -> bool:
        """Check if a recipe is vegetarian (or vegan if vegan=True)."""
        ingredients = recipe.get("ingredients", [])
        ingredients_text = " ".join([i.get("name", "").lower() for i in ingredients])

        meat_words = ["chicken", "beef", "pork", "lamb", "turkey", "duck", "goose",
                     "steak", "meat", "shrimp", "salmon", "fish", "tuna", "cod",
                     "bacon", "sausage", "ham", "prosciutto", "pancetta", "chorizo",
                     "crab", "lobster", "anchovy", "scallop", "clam", "mussel"]

        # Check tags first
        tags = recipe.get("tags", [])
        if vegan and "vegan" in tags:
            return True
        if not vegan and "vegetarian" in tags:
            return True

        # Check ingredients
        for meat in meat_words:
            if meat in ingredients_text:
                return False

        # If vegan, also check for animal products
        if vegan:
            animal_words = ["cheese", "milk", "butter", "cream", "yogurt", "egg",
                           "honey", "whey", "ghee"]
            for animal in animal_words:
                if animal in ingredients_text:
                    return False

        return True

    def _detect_cuisine(self, user_text: str, constraints: Dict = None) -> Optional[str]:
        """Detect cuisine from user text, constraints, or profile."""
        if not self.recipe_search:
            return None

        text_lower = user_text.lower()

        # Check constraints first
        if constraints and constraints.get("cuisine"):
            c = constraints["cuisine"]
            if c in self.recipe_search.cuisine_index:
                return c

        # Extract cuisine from user text
        cuisine_aliases = {
            "moroccan": "moroccan", "morrocan": "moroccan",
            "italian": "italian", "italy": "italian",
            "french": "french", "france": "french",
            "indian": "indian", "india": "indian",
            "chinese": "chinese", "china": "chinese",
            "japanese": "japanese", "japan": "japanese",
            "thai": "thai", "thailand": "thai",
            "mexican": "mexican", "mexico": "mexican",
            "korean": "korean", "korea": "korean",
            "greek": "greek", "greece": "greek",
            "spanish": "spanish", "spain": "spanish",
            "vietnamese": "vietnamese", "vietnam": "vietnamese",
            "cajun": "cajun_creole", "creole": "cajun_creole",
            "southern": "southern_us", "american": "southern_us",
            "brazilian": "brazilian", "brazil": "brazilian",
            "british": "british", "english": "british", "uk": "british",
            "irish": "irish", "ireland": "irish",
            "russian": "russian", "russia": "russian",
            "jamaican": "jamaican", "jamaica": "jamaican",
            "filipino": "filipino", "philippines": "filipino",
            "mediterranean": "greek",
            "asian": None,
        }

        for alias, cuisine in cuisine_aliases.items():
            if alias in text_lower and cuisine in self.recipe_search.cuisine_index:
                return cuisine

        # Fall back to profile preference (if not pure search)
        prefs = getattr(self.profile, 'cuisine_preferences', [])
        if prefs and prefs[0] in self.recipe_search.cuisine_index:
            return prefs[0]

        return None

    def _detect_cuisine_from_text_only(self, user_text: str) -> Optional[str]:
        """Detect cuisine ONLY from user text - used in pure search mode."""
        if not self.recipe_search:
            return None

        text_lower = user_text.lower()

        cuisine_aliases = {
            "moroccan": "moroccan", "morrocan": "moroccan",
            "italian": "italian", "italy": "italian",
            "french": "french", "france": "french",
            "indian": "indian", "india": "indian",
            "chinese": "chinese", "china": "chinese",
            "japanese": "japanese", "japan": "japanese",
            "thai": "thai", "thailand": "thai",
            "mexican": "mexican", "mexico": "mexican",
            "korean": "korean", "korea": "korean",
            "greek": "greek", "greece": "greek",
            "spanish": "spanish", "spain": "spanish",
            "vietnamese": "vietnamese", "vietnam": "vietnamese",
            "cajun": "cajun_creole", "creole": "cajun_creole",
            "southern": "southern_us", "american": "southern_us",
            "brazilian": "brazilian", "brazil": "brazilian",
            "british": "british", "english": "british", "uk": "british",
            "irish": "irish", "ireland": "irish",
            "russian": "russian", "russia": "russian",
            "jamaican": "jamaican", "jamaica": "jamaican",
            "filipino": "filipino", "philippines": "filipino",
            "mediterranean": "greek",
            "asian": None,
        }

        for alias, cuisine in cuisine_aliases.items():
            if alias in text_lower and cuisine in self.recipe_search.cuisine_index:
                return cuisine

        # No profile fallback - pure text detection only
        return None

    def _handle_modification(self, user_text: str, constraints: Dict = None) -> Dict:
        last_recipe = self.history.get_last_recipe()

        if not last_recipe:
            return {
                'message': "I don't have a previous recipe to modify. Please ask for a recipe first!",
                'type': 'error'
            }

        focus_mode = "co2"
        if constraints:
            focus_mode = constraints.get("focus_mode", "co2")

        text_lower = user_text.lower()

        # Detect vegetarian/vegan modification requests
        vegetarian_keywords = {"vegetarian", "no meat", "without meat", "meat-free", "meat free", "meatless"}
        user_wants_vegetarian = any(kw in text_lower for kw in vegetarian_keywords)
        vegan_keywords = {"vegan", "plant-based", "dairy-free", "no animal"}
        user_wants_vegan = any(kw in text_lower for kw in vegan_keywords)

        exclude_ids = self.history.get_shown_recipe_ids()
        mod_ingredients = self._extract_modification_ingredients(user_text, last_recipe)
        mod_cuisine = self._detect_cuisine(user_text, constraints)

        # === PRIORITY 1: DB search with modified ingredients ===
        db_recipe = None
        if self.recipe_search:
            # Try with modified ingredients
            if mod_ingredients:
                results = self.recipe_search.search_by_ingredients(
                    mod_ingredients, cuisine=mod_cuisine, limit=10,
                    exclude_ids=exclude_ids
                )
                # Filter for vegetarian/vegan if requested
                if user_wants_vegetarian or user_wants_vegan:
                    results = [r for r in results if self._is_recipe_vegetarian(r, user_wants_vegan)]

                if results:
                    db_recipe = self.recipe_search.format_recipe_for_display(
                        results[0], self.profile
                    )
                    db_recipe['source'] = 'database'
                    db_recipe['database_id'] = results[0].get('id')

            # Try with original recipe ingredients
            if not db_recipe:
                orig_names = [ing.get('name', '') for ing in last_recipe.get('ingredients', [])]
                if orig_names:
                    results = self.recipe_search.search_by_ingredients(
                        orig_names, cuisine=mod_cuisine, limit=10,
                        exclude_ids=exclude_ids
                    )
                    # Filter for vegetarian/vegan if requested
                    if user_wants_vegetarian or user_wants_vegan:
                        results = [r for r in results if self._is_recipe_vegetarian(r, user_wants_vegan)]

                    if results:
                        db_recipe = self.recipe_search.format_recipe_for_display(
                            results[0], self.profile
                        )
                        db_recipe['source'] = 'database'
                        db_recipe['database_id'] = results[0].get('id')

            # Random in cuisine if specified - try multiple times for vegetarian
            if not db_recipe:
                max_attempts = 10 if (user_wants_vegetarian or user_wants_vegan) else 1
                for attempt in range(max_attempts):
                    random_recipe = self.recipe_search.search_random(
                        cuisine=mod_cuisine,
                        prefer_low_co2=(focus_mode == "co2"),
                        exclude_ids=exclude_ids
                    )
                    if random_recipe:
                        if user_wants_vegetarian or user_wants_vegan:
                            if self._is_recipe_vegetarian(random_recipe, user_wants_vegan):
                                db_recipe = self.recipe_search.format_recipe_for_display(
                                    random_recipe, self.profile
                                )
                                db_recipe['source'] = 'database'
                                db_recipe['database_id'] = random_recipe.get('id')
                                break
                            else:
                                exclude_ids.append(random_recipe.get('id'))
                        else:
                            db_recipe = self.recipe_search.format_recipe_for_display(
                                random_recipe, self.profile
                            )
                            db_recipe['source'] = 'database'
                            db_recipe['database_id'] = random_recipe.get('id')
                            break

        if db_recipe:
            self.history.set_current_recipe(db_recipe)
            return {
                'message': f"Here's an alternative: **{db_recipe['name']}**",
                'type': 'recipe',
                'recipe': db_recipe
            }

        # === PRIORITY 2: LLM fallback ===
        if self.llm_available:
            try:
                prompt = build_follow_up_prompt(last_recipe, user_text, focus_mode=focus_mode)
                raw = self._call_llm(
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        *self.history.get_context_for_llm(5),
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=config.LM_STUDIO_MAX_TOKENS_RECIPE
                )
                recipe_data = safe_response(raw, 'recipe')
            except:
                recipe_data = get_fallback_recipe()
        else:
            recipe_data = get_fallback_recipe()

        recipe = parse_recipe(recipe_data)

        ingredients_for_co2 = []
        for ing in recipe.get('ingredients', []):
            food = self.ingredient_matcher.match_ingredient(ing.get('name', ''))
            if food:
                ingredients_for_co2.append({
                    'food_id': food.get('id'),
                    'quantity_g': ing.get('quantity_g', 100)
                })

        co2_info = calculate_meal_co2(ingredients_for_co2, self.co2_db, country=self.profile.country)
        recipe['co2_info'] = co2_info
        recipe['co2_label'] = get_co2_label(co2_info['total_co2_kg'])
        recipe['comparison'] = compare_to_average(co2_info['total_co2_kg'], country=self.profile.country)

        self.history.set_current_recipe(recipe)

        return {
            'message': f"Updated recipe: **{recipe['name']}**",
            'type': 'recipe',
            'recipe': recipe
        }

    def _extract_modification_ingredients(self, user_text: str, last_recipe: Dict) -> List[str]:
        """Extract ingredient modifications from follow-up text."""
        import re
        lower = user_text.lower()
        orig_ingredients = [ing.get('name', '') for ing in last_recipe.get('ingredients', [])]
        result = list(orig_ingredients)

        # Form modifiers: "as a sandwich", "in a bowl"
        form_map = {
            'sandwich': ['bread', 'sandwich bread'],
            'wrap': ['tortilla', 'wrap'],
            'bowl': ['rice'],
            'salad': ['lettuce', 'spinach'],
            'soup': ['broth', 'stock'],
            'curry': ['curry paste', 'coconut milk'],
            'pasta': ['pasta', 'spaghetti'],
        }
        for form_key, additions in form_map.items():
            if form_key in lower:
                for item in additions:
                    if item not in [i.lower() for i in result]:
                        result.append(item)

        # "with X" pattern
        with_match = re.search(r'\bwith\s+(\w+)', lower)
        if with_match:
            new_ing = with_match.group(1)
            if new_ing not in [i.lower() for i in result]:
                result.append(new_ing)

        # "without X" pattern
        without_match = re.search(r'\bwithout\s+(\w+)', lower)
        if without_match:
            remove_ing = without_match.group(1)
            result = [i for i in result if remove_ing not in i.lower()]

        # "with meat" -> add chicken if no specific meat mentioned
        if 'meat' in lower and not any(w in lower for w in ['chicken', 'beef', 'pork', 'lamb', 'turkey', 'fish', 'shrimp']):
            result.append('chicken')

        # "vegetarian" -> remove meat
        if 'vegetarian' in lower:
            meat_words = ['chicken', 'beef', 'pork', 'lamb', 'turkey', 'shrimp', 'salmon', 'fish', 'bacon', 'sausage']
            result = [i for i in result if not any(m in i.lower() for m in meat_words)]

        # "vegan" -> remove all animal products
        if 'vegan' in lower:
            animal_words = ['chicken', 'beef', 'pork', 'lamb', 'turkey', 'shrimp', 'salmon', 'fish',
                           'bacon', 'sausage', 'cheese', 'milk', 'butter', 'cream', 'egg', 'yogurt', 'honey']
            result = [i for i in result if not any(m in i.lower() for m in animal_words)]

        return result

    def _handle_shopping_list_request(self, pantry_items: List[str],
                                      constraints: Dict = None) -> Dict:
        last_recipe = self.history.get_last_recipe()

        if not last_recipe:
            return {
                'message': "Please generate a recipe first, then I can create a shopping list!",
                'type': 'error'
            }

        ingredients = []
        for ing in last_recipe.get('ingredients', []):
            food = self.ingredient_matcher.match_ingredient(ing.get('name', ''))
            if food:
                ingredients.append({
                    'food_id': food.get('id'),
                    'quantity_g': ing.get('quantity_g', 100)
                })

        budget = self.profile.weekly_budget if hasattr(self.profile, 'weekly_budget') else 100
        currency = self.profile.currency if hasattr(self.profile, 'currency') else "EUR"

        shopping_list = generate_shopping_list(
            ingredients,
            pantry_items,
            budget=budget,
            currency=currency
        )

        # Filter by focus categories if specified
        if constraints and constraints.get("shopping_categories"):
            allowed_cats = constraints["shopping_categories"]
            filtered = [
                item for item in shopping_list.get("missing_items", [])
                if item.get("category") in allowed_cats
            ]
            if filtered:
                shopping_list["missing_items"] = filtered
                shopping_list["items_with_cost"] = [
                    item for item in shopping_list.get("items_with_cost", [])
                    if any(m["name"] == item["name"] for m in filtered)
                ]
                shopping_list["total_cost"] = sum(
                    item.get("cost", 0) for item in shopping_list["items_with_cost"]
                )

        return {
            'message': "Here's your shopping list:",
            'type': 'shopping_list',
            'shopping_list': shopping_list
        }

    def _handle_weekly_plan(self, pantry_items: List[str], constraints: Dict = None) -> Dict:
        focus_mode = "co2"
        weekly_budget = self.profile.weekly_budget if hasattr(self.profile, 'weekly_budget') else 100
        household_size = 2

        if constraints:
            focus_mode = constraints.get("focus_mode", "co2")
            weekly_budget = constraints.get("weekly_budget", weekly_budget)
            household_size = constraints.get("household_size", household_size)

        # Try DB-based weekly plan first
        if self.recipe_search:
            days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            plan_days = []
            total_co2 = 0.0
            all_ingredients = {}  # Consolidated ingredients with quantities

            cuisine = None
            if constraints and constraints.get("cuisine"):
                cuisine = constraints["cuisine"]
            elif hasattr(self.profile, 'cuisine_preferences') and self.profile.cuisine_preferences:
                cuisine = self.profile.cuisine_preferences[0]

            used_ids = list(self.history.get_shown_recipe_ids())
            for day in days:
                recipe = self.recipe_search.search_random(
                    cuisine=cuisine,
                    prefer_low_co2=(focus_mode == "co2"),
                    prefer_emblematic=True,
                    exclude_ids=used_ids
                )
                if recipe:
                    used_ids.append(recipe["id"])
                    formatted = self.recipe_search.format_recipe_for_display(recipe, self.profile)
                    plan_days.append({
                        "day": day,
                        "meal": formatted["name"],
                        "cuisine": formatted.get("cuisine", "unknown"),
                        "ingredients": formatted["ingredients"],
                        "co2_kg": formatted["co2_info"]["total_co2_kg"]
                    })
                    total_co2 += formatted["co2_info"]["total_co2_kg"]

                    # Consolidate ingredients for shopping list
                    for ing in formatted.get("ingredients", []):
                        name = ing.get("name", "").lower()
                        qty = ing.get("quantity_g", 100)
                        if name in all_ingredients:
                            all_ingredients[name] += qty
                        else:
                            all_ingredients[name] = qty

            if plan_days:
                # Generate consolidated shopping list
                from core.shopping import generate_shopping_list
                from datetime import datetime

                # Convert to format expected by shopping list generator
                recipe_ingredients = [
                    {"name": name, "quantity_g": qty}
                    for name, qty in all_ingredients.items()
                ]

                shopping_result = generate_shopping_list(
                    recipe_ingredients,
                    pantry_items,
                    budget=weekly_budget,
                    currency="EUR"
                )

                # Calculate seasonal score (how many seasonal ingredients)
                month = datetime.now().month
                seasonal_ingredients = self._get_seasonal_ingredients(month)
                seasonal_matches = sum(1 for ing in all_ingredients.keys() if any(s in ing for s in seasonal_ingredients))
                seasonal_score = round(seasonal_matches / max(len(all_ingredients), 1) * 100, 1)

                # Calculate CO2 comparison
                french_avg_weekly = 2.5 * 7 * 2  # 2.5 kg/meal * 7 days * 2 meals
                co2_saved = round(french_avg_weekly - total_co2, 2)
                co2_saved_pct = round((co2_saved / french_avg_weekly) * 100, 1) if total_co2 < french_avg_weekly else 0

                # Generate recommendation
                if co2_saved > 0:
                    recommendation = f"Great choice! This plan saves {co2_saved} kg CO2 compared to the French average ({co2_saved_pct}% reduction)."
                elif total_co2 < french_avg_weekly:
                    recommendation = f"This plan is {round((french_avg_weekly - total_co2) / french_avg_weekly * 100, 1)}% below the French weekly average."
                else:
                    recommendation = "Consider swapping some meat dishes for plant-based alternatives to reduce CO2."

                if seasonal_score > 50:
                    recommendation += f" {seasonal_score}% of ingredients are in season this month!"

                weekly_plan = {
                    "days": plan_days,
                    "total_estimated_co2": round(total_co2, 2),
                    "french_avg_weekly_co2": french_avg_weekly,
                    "co2_saved_kg": max(0, co2_saved),
                    "co2_saved_percent": co2_saved_pct,
                    "seasonal_score_percent": seasonal_score,
                    "shopping_list": {
                        "items": shopping_result.get("missing_items", []),
                        "total_items": len(shopping_result.get("missing_items", [])),
                        "total_cost": shopping_result.get("total_cost", 0),
                        "currency": "EUR"
                    },
                    "recommendation": recommendation
                }
                return {
                    'message': "Here's your weekly meal plan with shopping list and CO2 analysis:",
                    'type': 'weekly_plan',
                    'weekly_plan': weekly_plan
                }

        # Fallback to LLM
        if self.llm_available:
            try:
                prompt = build_weekly_plan_prompt(self.profile.to_dict(), pantry_items, focus_mode=focus_mode)
                raw = self._call_llm(
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=config.LM_STUDIO_MAX_TOKENS_GUIDED
                )
                plan_data = safe_response(raw, 'weekly_plan')
            except:
                plan_data = {'days': [], 'total_estimated_cost': 0, 'total_estimated_co2': 0}
        else:
            plan_data = {'days': [], 'total_estimated_cost': 0, 'total_estimated_co2': 0}

        return {
            'message': "Here's your weekly meal plan:",
            'type': 'weekly_plan',
            'weekly_plan': plan_data
        }

    def _get_seasonal_ingredients(self, month: int) -> List[str]:
        """Get seasonal ingredients for a given month."""
        seasonal_by_month = {
            1: ["cabbage", "carrot", "leek", "onion", "potato", "spinach", "kale"],
            2: ["cabbage", "carrot", "leek", "onion", "potato", "spinach", "kale"],
            3: ["asparagus", "carrot", "leek", "lettuce", "spinach", "peas"],
            4: ["asparagus", "lettuce", "peas", "radish", "spinach", "strawberries"],
            5: ["asparagus", "lettuce", "peas", "strawberries", "tomatoes", "zucchini"],
            6: ["beans", "cucumber", "lettuce", "peas", "strawberries", "tomatoes", "zucchini"],
            7: ["beans", "berries", "cucumber", "tomatoes", "zucchini", "peppers", "eggplant"],
            8: ["beans", "berries", "cucumber", "tomatoes", "zucchini", "peppers", "eggplant", "melon"],
            9: ["apples", "beans", "mushrooms", "pears", "plums", "tomatoes", "zucchini"],
            10: ["apples", "mushrooms", "pears", "pumpkin", "squash", "grapes"],
            11: ["cabbage", "carrot", "mushrooms", "onion", "potato", "pumpkin", "squash"],
            12: ["cabbage", "carrot", "leek", "onion", "potato", "kale", "citrus"]
        }
        return seasonal_by_month.get(month, [])

    def _handle_question(self, user_text: str) -> Dict:
        if self.llm_available:
            try:
                answer = self._call_llm(
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        *self.history.get_context_for_llm(5),
                        {"role": "user", "content": user_text}
                    ],
                    max_tokens=config.LM_STUDIO_MAX_TOKENS_CHAT,
                    temperature=0.5
                )
            except:
                answer = self._get_offline_answer(user_text)
        else:
            answer = self._get_offline_answer(user_text)

        return {
            'message': answer,
            'type': 'answer'
        }

    def _get_offline_answer(self, user_text: str) -> str:
        text_lower = user_text.lower()

        if self.recipe_search:
            stats = self.recipe_search.get_stats()
            if "how many" in text_lower and "recipe" in text_lower:
                return f"I have {stats['total_recipes']} recipes from {len(stats['cuisines'])} cuisines in my database."

            if "cuisine" in text_lower:
                return f"Available cuisines: {', '.join(stats['cuisines'])}."

            if "co2" in text_lower or "carbon" in text_lower:
                return "Beef produces 27 kg CO2/kg, while lentils only 0.9 kg. Swap meat for plant proteins to reduce your carbon footprint!"

        return "I'm currently offline. Start LM Studio for full chat features, or ask me for a recipe using your ingredients!"

    def _handle_unknown(self, user_text: str) -> Dict:
        return {
            'message': "I'm not sure what you'd like. You can ask me for:\n"
                      "- A recipe (tell me your ingredients)\n"
                      "- A shopping list\n"
                      "- A weekly meal plan\n"
                      "- Sustainability tips\n"
                      "What would you like?",
            'type': 'clarification'
        }

    def get_history_stats(self) -> Dict:
        return self.history.get_stats()
