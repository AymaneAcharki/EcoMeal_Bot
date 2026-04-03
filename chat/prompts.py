from typing import Dict, List


# Core system prompt - optimized for small models (1B params)
SYSTEM_PROMPT_CORE = """You are EcoChef, a sustainable cooking assistant (UN SDG 12).
Help users cook delicious, low-carbon meals.

STRICT RULES:
1. ONLY answer about: recipes, cooking, food CO2, nutrition
2. Off-topic -> "I specialize in sustainable cooking. Ask me about recipes or food."
3. Be concise (max 200 words per response)
4. For recipes: output ONLY valid JSON, no markdown, no extra text

CO2 DATA (kg CO2 per kg of food):
- Beef: 27.0 | Lamb: 20.0 | Pork: 7.6 | Chicken: 6.9 | Fish: 6-12
- Eggs: 4.8 | Cheese: 13.5 | Tofu: 2.0 | Lentils: 0.9 | Chickpeas: 0.8
- Vegetables: 0.3-1.5 | Rice: 2.7 | Pasta: 1.5 | Potatoes: 0.2

TARGET: Keep recipes under 2.0 kg CO2 per serving."""

# Recipe format reminder - injected in user message for better attention
RECIPE_FORMAT_REMINDER = """OUTPUT ONLY THIS JSON STRUCTURE, NOTHING ELSE:
{
  "name": "Recipe Name",
  "description": "1-2 sentences.",
  "ingredients": [{"name": "Item", "quantity_g": 150}],
  "steps": ["Step 1: ...", "Step 2: ..."],
  "cooking_time_minutes": 30,
  "difficulty": "easy",
  "sustainability_tip": "One sentence."
}
RULES: Max 12 ingredients. Quantities in grams. 4-8 steps. No markdown. No explanation."""

# For backward compatibility
SYSTEM_PROMPT = SYSTEM_PROMPT_CORE


def build_recipe_prompt(ingredients: List[str], profile: Dict,
                        constraints: Dict = None,
                        focus_mode: str = "co2") -> str:
    """Build a recipe generation prompt with user context."""
    diet = profile.get("diet_type", "omnivore")
    allergies = profile.get("allergies", [])
    max_time = profile.get("max_cooking_time", 60)
    skill = profile.get("skill_level", "beginner")
    household = profile.get("household_size", 2)
    cuisines = profile.get("cuisine_preferences", [])

    prompt = f"Generate a recipe using these ingredients: {', '.join(ingredients)}.\n\n"
    prompt += f"USER PROFILE:\n"
    prompt += f"- Diet: {diet}\n"
    prompt += f"- Household size: {household} people\n"
    prompt += f"- Skill level: {skill}\n"
    prompt += f"- Max cooking time: {max_time} minutes\n"

    if allergies:
        prompt += f"- ALLERGIES (strictly avoid): {', '.join(allergies)}\n"

    if cuisines:
        prompt += f"- Cuisine preferences: {', '.join(cuisines)}\n"

    if constraints:
        if "max_co2" in constraints:
            prompt += f"- Maximum CO2 per serving: {constraints['max_co2']} kg\n"
        if "appliances" in constraints:
            prompt += f"- Available appliances: {', '.join(constraints['appliances'])}\n"
        if "difficulty" in constraints:
            prompt += f"- Difficulty level: {constraints['difficulty']}\n"

    focus_hints = {
        "co2": "FOCUS: Minimize CO2 footprint. Prefer plant-based proteins, local ingredients.\n",
        "nutri": "FOCUS: Maximize nutritional value. Include protein, fiber, vitamins.\n",
        "eco": "FOCUS: Budget-friendly and sustainable. Use affordable, seasonal ingredients.\n"
    }
    if focus_mode in focus_hints:
        prompt += focus_hints[focus_mode]

    # Inject format reminder at the end of user message (better attention for small models)
    prompt += f"\n{RECIPE_FORMAT_REMINDER}"
    return prompt


def build_recipe_suggestion_prompt(ingredients: List[str],
                                   matched_recipes: List[Dict],
                                   profile: Dict) -> str:
    """Prompt for LLM to present database recipes nicely."""
    prompt = f"The user has these ingredients: {', '.join(ingredients)}.\n\n"
    prompt += "I found these matching recipes from the database:\n\n"

    for i, r in enumerate(matched_recipes[:3], 1):
        name = r.get("name", "Unknown")
        cuisine = r.get("cuisine", "unknown")
        co2 = r.get("co2_total_kg", 2.5)
        ing_count = r.get("ingredient_count", 0)
        prompt += f"{i}. {name} ({cuisine}, {co2:.2f} kg CO2, {ing_count} ingredients)\n"

    prompt += "\nSelect the best match and present it as a complete recipe in JSON format."
    prompt += " Adjust ingredient quantities for the user's household size."
    prompt += f"\n\n{RECIPE_FORMAT_REMINDER}"
    return prompt


def build_shopping_list_prompt(recipe_ingredients: List[Dict],
                               pantry_items: List[str],
                               focus_items: List[str] = None) -> str:
    """Prompt for generating a focused shopping list."""
    recipe_items = [i.get("name", "Unknown") for i in recipe_ingredients]

    prompt = "Generate a shopping list comparing recipe needs with pantry.\n\n"
    prompt += f"Recipe needs: {', '.join(recipe_items)}\n"
    prompt += f"Already in pantry: {', '.join(pantry_items) if pantry_items else 'Nothing listed'}\n"

    if focus_items:
        prompt += f"\nFOCUS ON: {', '.join(focus_items)} (prioritize these categories)\n"

    prompt += "\nRespond in JSON format ONLY:\n"
    prompt += "{\n"
    prompt += '  "missing_items": [{"name": "item", "quantity": "100g", "category": "vegetables"}],\n'
    prompt += '  "estimated_cost_eur": 0.0,\n'
    prompt += '  "eco_tips": ["Buy seasonal", "Choose local"]\n'
    prompt += "}"
    return prompt


def build_follow_up_prompt(previous_recipe: Dict, modification: str,
                          focus_mode: str = "co2") -> str:
    """Prompt for modifying an existing recipe."""
    prompt = f"The user wants to modify the previous recipe.\n\n"
    prompt += f"Previous recipe: {previous_recipe.get('name', 'Unknown')}\n"
    prompt += f"Modification request: {modification}\n\n"

    if focus_mode == "co2":
        prompt += "When modifying, try to reduce CO2 footprint if possible.\n"
    elif focus_mode == "nutri":
        prompt += "When modifying, try to improve nutritional value.\n"
    elif focus_mode == "eco":
        prompt += "When modifying, try to keep it budget-friendly.\n"

    prompt += f"Generate an updated recipe in JSON format.\n"
    prompt += f"{RECIPE_FORMAT_REMINDER}"
    return prompt


def build_intent_classify_prompt(user_message: str) -> str:
    """Prompt for intent classification - forces single word response."""
    return f"""Task: classify the intent. Reply with EXACTLY one word from the list below, nothing else.

Message: "{user_message}"

Valid intents: recipe_request, modification, shopping_list, question, greeting, weekly_plan

Your answer (one word only):"""


def build_weekly_plan_prompt(profile: Dict, pantry_items: List[str],
                            focus_mode: str = "co2") -> str:
    """Prompt for generating a weekly meal plan."""
    diet = profile.get("diet_type", "omnivore")
    max_time = profile.get("max_cooking_time", 60)
    budget = profile.get("weekly_budget", 100)
    household = profile.get("household_size", 2)
    cuisines = profile.get("cuisine_preferences", [])

    prompt = "Generate a 7-day meal plan.\n\n"
    prompt += f"USER PROFILE:\n"
    prompt += f"- Diet: {diet}\n"
    prompt += f"- Max cooking time per meal: {max_time} minutes\n"
    prompt += f"- Weekly budget: {budget} EUR\n"
    prompt += f"- Household size: {household} people\n"

    if cuisines:
        prompt += f"- Cuisine preferences: {', '.join(cuisines)}\n"

    if pantry_items:
        prompt += f"- Available ingredients: {', '.join(pantry_items)}\n"

    focus_hints = {
        "co2": "FOCUS: Minimize weekly CO2 footprint.\n",
        "nutri": "FOCUS: Balanced nutrition throughout the week.\n",
        "eco": "FOCUS: Stay within budget, use affordable ingredients.\n"
    }
    if focus_mode in focus_hints:
        prompt += focus_hints[focus_mode]

    # Complete JSON structure (not truncated)
    prompt += "\nRespond in JSON format ONLY:\n"
    prompt += "{\n"
    prompt += '  "days": [\n'
    prompt += '    {"day": "Monday", "meal": "Recipe name", "co2_kg": 1.5, "ingredients": ["list"]},\n'
    prompt += '    {"day": "Tuesday", "meal": "...", "co2_kg": 1.2, "ingredients": [...]},\n'
    prompt += '    {"day": "Wednesday", "meal": "...", "co2_kg": 1.0, "ingredients": [...]},\n'
    prompt += '    {"day": "Thursday", "meal": "...", "co2_kg": 1.3, "ingredients": [...]},\n'
    prompt += '    {"day": "Friday", "meal": "...", "co2_kg": 1.1, "ingredients": [...]},\n'
    prompt += '    {"day": "Saturday", "meal": "...", "co2_kg": 1.4, "ingredients": [...]},\n'
    prompt += '    {"day": "Sunday", "meal": "...", "co2_kg": 1.2, "ingredients": [...]}\n'
    prompt += '  ],\n'
    prompt += '  "total_estimated_cost_eur": 0.0,\n'
    prompt += '  "total_estimated_co2_kg": 0.0\n'
    prompt += "}"
    return prompt
