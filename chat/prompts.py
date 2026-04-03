from typing import Dict, List


# Core system prompt - short and focused for Llama 3.2
SYSTEM_PROMPT = """You are EcoChef, a sustainable cooking assistant.
Help users cook realistic, delicious, low-carbon meals.

RULES:
1. Only answer about: recipes, cooking, food CO2, substitutions, shopping lists.
2. Be practical and concise.
3. For recipes: output ONLY valid JSON, no markdown, no extra text.
4. Create REAL, COOKABLE dishes - not generic or invented combinations.

CO2 DATA (kg CO2 per kg): Beef 27 | Chicken 6.9 | Fish 6-12 | Tofu 2.0 | Lentils 0.9 | Vegetables 0.3-1.5
Target: Keep recipes under 2.0 kg CO2 per serving."""


# Few-shot example for better quality
RECIPE_EXAMPLE = """EXAMPLE OF A GOOD RECIPE:
{
  "name": "Spaghetti Aglio e Olio",
  "description": "Classic Italian pasta with garlic, olive oil, and chili flakes. Simple, fragrant, and ready in 15 minutes.",
  "ingredients": [
    {"name": "spaghetti", "quantity_g": 200},
    {"name": "garlic cloves", "quantity_g": 15},
    {"name": "olive oil", "quantity_g": 45},
    {"name": "red chili flakes", "quantity_g": 3},
    {"name": "fresh parsley", "quantity_g": 10},
    {"name": "salt", "quantity_g": 5}
  ],
  "steps": [
    "Boil spaghetti in salted water for 9 minutes until al dente. Reserve 100ml pasta water.",
    "Slice garlic thinly. Heat olive oil in pan over medium-low heat for 2 minutes.",
    "Add garlic and chili flakes. Cook gently for 3 minutes until golden, not brown.",
    "Drain pasta, add to pan with reserved water. Toss for 2 minutes until coated.",
    "Serve with chopped parsley and a drizzle of olive oil."
  ],
  "cooking_time_minutes": 15,
  "difficulty": "easy",
  "sustainability_tip": "This plant-based pasta has very low CO2 (~0.4kg). Use local garlic for even less."
}"""


# Quality rules to enforce
QUALITY_RULES = """
QUALITY RULES (follow strictly):
- Create a REAL, COOKABLE dish that exists in cuisine.
- Use AUTHENTIC ingredients for the dish type (e.g., carbonara = eggs + pecorino + guanciale, NO cream).
- Do NOT use vague ingredients like "spices", "sauce", "seasoning", "herbs" - be specific.
- Each step MUST include: action + time/temperature + expected result.
- Description MUST mention taste and texture.
- Add one practical chef_tip.
- If traditional dish, preserve its identity - do not modify core ingredients.
- Output ONLY valid JSON, nothing else."""


# Format reminder (shorter)
RECIPE_FORMAT = """OUTPUT FORMAT (JSON only):
{
  "name": "Dish Name",
  "description": "Taste and texture in 1-2 sentences.",
  "ingredients": [{"name": "specific ingredient", "quantity_g": 100}],
  "steps": ["Action + time/temp + result.", "..."],
  "cooking_time_minutes": 30,
  "difficulty": "easy|medium|hard",
  "sustainability_tip": "One specific tip."
}"""


def build_recipe_prompt(ingredients: List[str], profile: Dict,
                        constraints: Dict = None,
                        focus_mode: str = "co2") -> str:
    """Build a recipe generation prompt optimized for Llama 3.2."""
    diet = profile.get("diet_type", "omnivore")
    allergies = profile.get("allergies", [])
    max_time = profile.get("max_cooking_time", 60)
    skill = profile.get("skill_level", "beginner")
    household = profile.get("household_size", 2)
    cuisines = profile.get("cuisine_preferences", [])

    # Build context
    prompt = f"Create a recipe using: {', '.join(ingredients)}\n\n"
    prompt += f"USER:\n"
    prompt += f"- Diet: {diet}\n"
    prompt += f"- Servings: {household}\n"
    prompt += f"- Skill: {skill}\n"
    prompt += f"- Max time: {max_time} min\n"

    if allergies:
        prompt += f"- ALLERGIES (avoid): {', '.join(allergies)}\n"

    if cuisines:
        prompt += f"- Preferred cuisines: {', '.join(cuisines)}\n"

    # Focus mode - but respect user's ingredient choices
    has_meat = any(ing.lower() in ['chicken', 'beef', 'pork', 'lamb', 'turkey', 'duck', 'fish', 'salmon', 'shrimp', 'bacon', 'sausage'] for ing in ingredients)

    if focus_mode == "co2" and not has_meat:
        prompt += "\nFOCUS: Minimize CO2. Use local seasonal ingredients where possible.\n"
    elif focus_mode == "nutri":
        prompt += "\nFOCUS: Maximize nutrition. Include protein, fiber, vitamins.\n"
    elif focus_mode == "eco":
        prompt += "\nFOCUS: Budget-friendly. Use affordable ingredients.\n"

    # If user explicitly wants meat, acknowledge it
    if has_meat:
        prompt += "\nNOTE: User requested meat. Include it as requested. You can suggest a smaller portion for sustainability.\n"

    # Add quality rules
    prompt += QUALITY_RULES

    # Add format
    prompt += "\n" + RECIPE_FORMAT

    # Add few-shot example
    prompt += "\n\n" + RECIPE_EXAMPLE

    # Final instruction
    prompt += "\n\nNow generate the recipe (JSON only):"

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
